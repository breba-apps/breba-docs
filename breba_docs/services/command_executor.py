import abc
import asyncio
import contextlib
import json
import os
import shlex
import time
import uuid
from collections.abc import Coroutine

import pexpect
from tenacity import retry, stop_after_delay, wait_fixed

from breba_docs.agent.agent import Agent
from breba_docs.container import container_setup
from breba_docs.services.reports import CommandReport
from pty_server import AsyncPtyClient
from pty_server.async_client import PtyServerResponse


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
    def __init__(self, agent, socket_client=None):
        self.agent = agent
        self.socket_client = socket_client
        # Used for async bridging
        self.loop = asyncio.new_event_loop()

    def _run_in_own_loop(self, fut: asyncio.Future | Coroutine):
        """
        Ensure that this executor's dedicated loop is set as the current loop
        in the current thread. This is crucial if the code ends up running
        in a different thread than where it was created.
        """
        asyncio.set_event_loop(self.loop)
        return self.loop.run_until_complete(fut)

    @classmethod
    @contextlib.contextmanager
    def executor_and_new_container(cls, agent: Agent, **kwargs):
        execution_container = None
        try:
            execution_container = container_setup(**kwargs)
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

    def create_provide_input(self):
        response_length = 0

        def maybe_get_input(response: list[str]) -> str | None:
            nonlocal response_length
            # Only try to get input if new data was received
            if response and len(response) != response_length:
                response_length = len(response)
                return self.get_input_message(response[-1])

            return None

        async def provide_input(response: list[str]) -> str | None:
            input_message = maybe_get_input(response)

            if input_message:
                return await self.socket_client.send_message(input_message)

            return None

        return provide_input

    async def read_response(self, response: PtyServerResponse, timeout=0.5, max_retries=2):
        """Read data from the server with custom retry logic."""
        retries = 0
        data_received = []
        provide_input = self.create_provide_input()
        while True:
            async for data in response.stream(timeout):
                print(f"Data from Socket Client: {data}")
                data_received.append(data)
                retries = 0  # Every time we have a successful read, we want to reset retries

            if response.completed():
                return ''.join(data_received)
            if response.timedout():
                print(f"No new Data received in {timeout} seconds (attempt {retries}/{max_retries})")
                if await provide_input(data_received):
                    print(f"Provided input, restarting retries")
                    retries = 0
                else:
                    retries += 1

                if retries >= max_retries:
                    print("Max retries reached.")
                    return ''.join(data_received)


    async def do_execute(self, command: str):
        response = await self.socket_client.send_command(command)
        if response:
            response_text = await self.read_response(response)
        else:
            response_text = "Error occurred due to socket error. See log for details"
        return response_text

    def execute_command(self, command: str) -> str:
        # If not yet part of a session, execute command in using session
        if not self.socket_client:
            with self.session() as session:
                return session.execute_command(command)
        else:

            return self._run_in_own_loop(self.do_execute(command))

    async def execute_command_async(self, command: str) -> str:
        # If not yet part of a session, execute command in using session
        if not self.socket_client:
            with self.session() as session:
                return session.execute_command(command)
        else:
            return await self.do_execute(command)

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

    @retry(stop=stop_after_delay(15), wait=wait_fixed(0.2))
    async def try_connect(self):
        client = AsyncPtyClient()
        await client.connect()  # if this raises, it will retry
        return client

    @contextlib.contextmanager
    def session(self):
        self.socket_client = self._run_in_own_loop(self.try_connect())
        try:
            yield self
        finally:
            self._run_in_own_loop(self.socket_client.disconnect())
            self.socket_client = None

    @contextlib.asynccontextmanager
    async def async_session(self) -> CommandExecutor:
        """Using the with executor.session will run all commands in the same session"""
        self.socket_client = await self.try_connect()
        yield self
        await self.socket_client.disconnect()
        self.socket_client = None