import abc
import asyncio
import contextlib
import shlex
import uuid
from collections.abc import Coroutine

from interactive_process import InteractiveProcess, TerminatedProcessError, ReadWriteError

from breba_docs.services.input_provider import InputProvider
from breba_docs.services.reports import CommandReport
from pty_server import AsyncPtyClient
from pty_server.async_client import PtyServerResponse


class CommandExecutor(abc.ABC):
    @abc.abstractmethod
    def execute_command(self, command: [str]) -> list[CommandReport]:
        pass


class LocalCommandExecutor(CommandExecutor):
    @contextlib.contextmanager
    def session(self):
        with contextlib.closing(InteractiveProcess()) as process:
            self.process = process
            # clear any messages that show up when starting the shell, they may swallow useful output if shell has issues
            # TODO: This doesn't do what is supposed. It should read data for 0.1 seconds, but instead it reads data
            #  right away only waiting for 0.1 seconds if there is nothing to read.
            self.process.read_nonblocking(timeout=0.1)
            yield self

    def __init__(self, input_provider: InputProvider, process: InteractiveProcess | None = None):
        self.input_provider = input_provider
        self.process = process

    def execute_command(self, command):
        # TODO: move this to InteractiveProcess, so that container command executor can echo the same way
        # Echo the command first (shell-escaped)
        escaped_command = shlex.quote(command)
        echo_text = f"echo $ {escaped_command}\n"
        self.process.send_command(echo_text)

        command_id = str(uuid.uuid4())
        command_end_marker = f"Completed {command_id}"
        command = f"{command} && echo {command_end_marker} || echo {command_end_marker}"
        self.process.send_command(command)

        command_output = ""
        new_output = ""
        while True:
            try:
                new_output = self.process.read_nonblocking(timeout=2)
                command_output += new_output
                if command_end_marker in new_output:
                    command_output = command_output.replace(f"{command_end_marker}\n", "")
                    print("Breaking on end marker")
                    return command_output
            except TimeoutError:
                print("Breaking due to timeout. Need to check if waiting for input.")
                if new_output:
                    input_text = self.input_provider.get_input(new_output)
                    new_output = ""  # reset new_output so that if timeout happens twice in a row, we don't get stuck

                    # TODO: this does an implicit retry, when no input text is provided by get_input_text.
                    #  maybe should have an explicit retry. The else clause is a continue, but should it be?
                    if input_text:
                        command_output += input_text
                        self.process.send_command(input_text)

                else:
                    break
            except (TerminatedProcessError, ReadWriteError) as exc:
                print(f"End of process output: {exc}")
                break
            except Exception as exc:
                print(exc)
                break

        return command_output


class ContainerCommandExecutor(CommandExecutor):
    def __init__(self, input_provider: InputProvider, socket_client: AsyncPtyClient | None = None):
        self.input_provider = input_provider
        self.socket_client : AsyncPtyClient | None = socket_client
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

    def create_provide_input(self):
        response_length = 0

        def maybe_get_input(response: list[str]) -> str | None:
            nonlocal response_length
            # Only try to get input if new data was received
            if response and len(response) != response_length:
                response_length = len(response)
                return self.input_provider.get_input(response[-1])

            return None

        async def provide_input(response: list[str]) -> str | None:
            input_message = maybe_get_input(response)

            if input_message:
                return await self.socket_client.send_input(input_message)

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
        # If not yet part of a session, execute command inside a session
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

    def _connect(self):
        if not self.socket_client:
            self.socket_client = AsyncPtyClient()
            self._run_in_own_loop(self.socket_client.connect(max_wait_time=15))
        else:
            raise Exception("Already connected")

    def _disconnect(self):
        if self.socket_client:
            self._run_in_own_loop(self.socket_client.disconnect())
            self.socket_client = None
        else:
            raise Exception("Not connected")

    @contextlib.contextmanager
    def session(self):
        self._connect()
        try:
            yield self
        finally:
            self._disconnect()

    @contextlib.asynccontextmanager
    async def async_session(self):
        """Using the with executor.session will run all commands in the same session"""
        self.socket_client = AsyncPtyClient()
        await self.socket_client.connect(max_wait_time=15)
        yield self
        await self.socket_client.disconnect()
        self.socket_client = None
