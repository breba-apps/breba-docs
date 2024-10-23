import json

from breba_docs.analyzer.reporter import Reporter
from breba_docs.services.agent import Agent
from breba_docs.services.goal_report import GoalReport, DocumentReport
from breba_docs.services.openai_agent import OpenAIAgent
from breba_docs.services.output_analyzer_result import CommandReport
from breba_docs.socket_server.client import Client


class DocumentAnalyzer:
    def __init__(self):
        self.agent: Agent = OpenAIAgent()

    def get_input_message(self, text: str):
        instruction = self.agent.provide_input(text)
        if instruction == "breba-noop":
            return None
        elif instruction:
            return json.dumps({"input": instruction})

    def collect_response(self, response: str, command_executor: Client):
        """
        Collect a response from the command executor and any additional responses that come back based on if the AI
        thinks that the command is waiting for input or not. If AI thinks it is waiting for input, then we send in the
        input and await the additional response. If AI does not think it is waiting for input, we just return the
        response.

        Args:
            response (str): The initial response from the command executor.
            command_executor (Client): The client to send messages to and receive responses from.

        Returns:
            str: The full response including any additional responses due to input.
        """
        if response:
            input_message = self.get_input_message(response)
            input_response = ""
            if input_message:
                input_response = command_executor.send_message(input_message)
            # TODO: This additional response covers for cases where at the first attempt the response comes back empty
            #  Due to a timeout. But really it is just a slow executing command and this works as backup
            #  Should probably introduce a max wait time and loop over at some interval to double check response
            additional_response = self.collect_response(command_executor.read_response(), command_executor)
            return response + input_response + additional_response

        return ''

    def execute_command_and_collect_response(self, command, command_executor: Client):
        # when response comes back we want to check if AI thinks it is waiting for input.
        # if it is, then we send in input
        # if it is not, we keep reading the response
        response = command_executor.send_message(json.dumps(command))
        response = self.collect_response(response, command_executor)

        return response

    def execute_commands(self, commands) -> list[CommandReport]:
        report = []
        with Client() as commands_client:
            for command in commands:
                command = {"command": command}
                response = self.execute_command_and_collect_response(command, commands_client)
                agent_output = self.agent.analyze_output(response)
                report.append(agent_output)
        return report

    def analyze(self, doc: str):
        goals = self.agent.fetch_goals(doc)
        goal_reports: list[GoalReport] = []
        for goal in goals:
            commands = self.agent.fetch_commands(doc, json.dumps(goal))
            command_reports = self.execute_commands(commands)
            goal_report = GoalReport(goal["name"], goal["description"], command_reports)
            goal_reports.append(goal_report)
        document_report: DocumentReport = DocumentReport("Some Document", goal_reports)
        Reporter(document_report).print_report()