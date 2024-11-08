import abc
import json

from breba_docs.services.agent import Agent
from breba_docs.services.reports import CommandReport
from breba_docs.socket_server.client import Client


class CommandExecutor(abc.ABC):
    @abc.abstractmethod
    def execute_commands_sync(self, command: [str]) -> list[CommandReport]:
        pass


class ContainerCommandExecutor(CommandExecutor):
    def __init__(self, agent: Agent):
        self.agent = agent

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

    def execute_commands_sync(self, commands) -> list[CommandReport]:
        report = []
        # Need to use a single executor because each executor will run in a separate terminal session
        with Client() as socket_client:
            for command in commands:
                command = {"command": command}
                response = socket_client.send_message(json.dumps(command))
                response = self.collect_response(response, socket_client)
                agent_output = self.agent.analyze_output(response)
                report.append(agent_output)
        return report
