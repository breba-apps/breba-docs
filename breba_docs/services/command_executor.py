import abc
import contextlib
import json
import os
import shlex
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
    def __init__(self, agent: Agent):
        self.agent = agent
        self.socket_client = None

    @classmethod
    @contextlib.contextmanager
    def executor_and_new_container(cls, agent: Agent):
        execution_container = None
        try:
            execution_container = container_setup(agent)
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

    def collect_response(self, response: str, socket_client: Client):
        """
        Collect a response from the command executor and any additional responses that come back based on if the AI
        thinks that the command is waiting for input or not. If AI thinks it is waiting for input, then we send in the
        input and await the additional response. If AI does not think it is waiting for input, we just return the
        response.

        Args:
            response (str): The initial response from the command executor.
            socket_client (Client): The client to send messages to and receive responses from.

        Returns:
            str: The full response including any additional responses due to input.
        """
        if response:
            input_message = self.get_input_message(response)
            input_response = ""
            if input_message:
                input_response = socket_client.send_message(input_message)
            # TODO: This additional response covers for cases where at the first attempt the response comes back empty
            #  Due to a timeout. But really it is just a slow executing command and this works as backup
            #  Should probably introduce a max wait time and loop over at some interval to double check response
            additional_response = self.collect_response(socket_client.read_response(), socket_client)
            return response + input_response + additional_response

        return ''

    def execute_command(self, command: [str]) -> str:
        # If not yet part of a session, execute command in using session
        if not self.socket_client:
            with self.session() as session:
                return session.execute_command(command)
        else:
            command_directive = {"command": command}
            response = self.socket_client.send_message(json.dumps(command_directive))
            response = self.collect_response(response, self.socket_client)
            return response

    def execute_commands_sync(self, commands) -> list[CommandReport]:
        command_reports = []
        execution_container = None
        try:
            execution_container = container_setup()
            time.sleep(0.5)

            with self.session() as session:
                for command in commands:
                    command_report = session.execute_command(command)
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
