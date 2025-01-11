import abc
import contextlib
import json
import os
import shlex
import socket
import time
import uuid

import pexpect

from breba_docs.agent.agent import Agent
from breba_docs.container import container_setup
from breba_docs.services.reports import CommandReport
from breba_docs.socket_server.client import Client


class CommandExecutor(abc.ABC):
    @abc.abstractmethod
    def execute_commands_sync(self, command: [str]) -> list[CommandReport]:
        pass

    @abc.abstractmethod
    def execute_command(self, command: [str]) -> list[CommandReport]:
        pass


def collect_output(process, command_end_marker: str):
    command_output = ""
    while True:
        try:
            time.sleep(0.5)
            output = process.read_nonblocking(1024, timeout=2)
            command_output += output
            if command_end_marker in output:
                print("Breaking on end marker")
                break
        except pexpect.exceptions.TIMEOUT:
            print("Breaking due to timeout. Need to check if waiting for input.")
            break
        except pexpect.exceptions.EOF as e:
            print("End of process output.")
            break
    return command_output


class LocalCommandExecutor(CommandExecutor):

    def __init__(self, agent: Agent):
        self.agent = agent

    def get_input_text(self, text: str):
        # TODO: should probably throw this out of executor and handle input in the Executor caller
        instruction = self.agent.provide_input(text)
        if instruction == "breba-noop":
            return None
        elif instruction:
            return instruction

    def execute_command(self, command):
        raise Exception("Unimplemented")

    def execute_commands_sync(self, commands: list[str]) -> list[CommandReport]:
        process = pexpect.spawn('/bin/bash', encoding='utf-8', env={"PS1": ""}, echo=False)

        # clear any messages that show up when starting the shell
        process.read_nonblocking(1024, timeout=0.5)
        report = []
        for command in commands:
            # basically echo the command, but have to escape quotes first
            escaped_command = shlex.quote(command)
            process.sendline(f"echo {escaped_command}\n") # TODO: check if can use echo

            command_id = str(uuid.uuid4())
            command_end_marker = f"Completed {command_id}"
            command = f"{command} && echo {command_end_marker}"
            process.sendline(command)

            command_output = ""
            # TODO: need to separate flow between when command times out and when it has actually completed
            while True:
                new_output = collect_output(process, command_end_marker)
                command_output += new_output
                if new_output:
                    input_text = self.get_input_text(new_output)
                    if input_text:
                        command_output += input_text + os.linesep
                        process.sendline(input_text)
                else:
                    break
            command_report = self.agent.analyze_output(command_output)
            report.append(command_report)

        return report


class ContainerCommandExecutor(CommandExecutor):
    def __init__(self, agent: Agent, socket_client: Client = None):
        # TODO: get ride of agent
        self.agent = agent
        self.socket_client = socket_client

    @classmethod
    @contextlib.contextmanager
    def executor_and_new_container(cls, agent: Agent, **kwargs):
        execution_container = None
        try:
            execution_container = container_setup(**kwargs)
            time.sleep(0.5)
            yield ContainerCommandExecutor(agent)
        finally:
            if execution_container:
                execution_container.stop()
                execution_container.remove()

    def get_input_message(self, text: str):
        instruction = self.agent.provide_input(text)
        if instruction == "breba-noop":
            return None
        elif instruction:
            return json.dumps({"input": instruction})


    def create_should_restart_retries(self):
        response_length = 0

        def maybe_get_input(response: list[str]) -> str | None:
            nonlocal response_length
            # Only try to get input if new data was received
            if response and len(response) != response_length:
                response_length = len(response)
                return self.get_input_message(response[-1])

            return None

        def should_restart_retries(response: list[str]):
            input_message = maybe_get_input(response)

            if input_message:
                # We will only restart retries if we have successfully written input to the socket
                return self.socket_client.send_message(input_message)

            return False

        return should_restart_retries

    # TODO: much of the logic dealing with stream response collection should move to stream response.
    #  This could be done by data_received.append(data) moving to stream_response
    def read_response(self, command_id, timeout=0.5, max_retries=2):
        """Read data from the server with custom retry logic."""
        retries = 0
        data_received = []
        should_restart_retries = self.create_should_restart_retries()
        while True:
            try:
                for data in self.socket_client.stream_response(timeout):
                    print(f"Data from Socket Client: {data}")
                    data_received.append(data)
                    if f"Completed {command_id}" in data:
                        data_received[-1] = data_received[-1].replace(f"Completed {command_id}", "")
                        return ''.join(data_received)
                    retries = 0  # Every time we have successful read, we want to reset retries

                # We hit a timeout or stream is exhausted
                print(f"No new Data received in {timeout} seconds (attempt {retries}/{max_retries})")
                if should_restart_retries(data_received):
                    print(f"Restarting retries")
                    retries = 0
                else:
                    retries += 1

                if retries >= max_retries:
                    print("Max retries reached.")
                    return ''.join(data_received)
            except socket.error as e:
                print(f"Socket Client: Error reading from socket: {e}")
                return ''.join(data_received)

    def execute_command(self, command: str) -> str:
        # If not yet part of a session, execute command in using session
        if not self.socket_client:
            with self.session() as session:
                return session.execute_command(command)
        else:
            command_id = str(uuid.uuid4())
            command_directive = {"command": command, "command_id": command_id}
            if self.socket_client.send_message(json.dumps(command_directive)):
                response = self.read_response(command_id)
            else:
                response = "Error occurred due to socket error. See log for details"
            return response

    def execute_commands_sync(self, commands) -> list[CommandReport]:
        command_reports = []
        execution_container = None
        try:
            execution_container = container_setup()
            time.sleep(0.5)

            with self.session() as session:
                for command in commands:
                    response = session.execute_command(command)
                    # TODO: Pass the command to analyze output, otherwise it doesn't know what command we were even trying to execute
                    command_report = self.agent.analyze_output(response)
                    command_reports.append(command_report)
                self.socket_client = None
            return command_reports

        finally:
            if execution_container:
                execution_container.stop()
                execution_container.remove()

    @contextlib.contextmanager
    def session(self) -> CommandExecutor:
        """Using the with executor.session will run all commands in the same session"""
        with Client() as socket_client:
            try:
                self.socket_client = socket_client
                yield self
            finally:
                self.socket_client = None
