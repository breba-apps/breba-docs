import json

from breba_docs.analyzer.reporter import Reporter
from breba_docs.services.agent import Agent
from breba_docs.services.command_executor import ContainerCommandExecutor, LocalCommandExecutor
from breba_docs.services.document import Document
from breba_docs.services.reports import GoalReport, DocumentReport
from breba_docs.services.openai_agent import OpenAIAgent


class DocumentAnalyzer:
    def __init__(self):
        self.agent: Agent = OpenAIAgent()

    def analyze(self, doc: Document):
        goals = self.agent.fetch_goals(doc.content)
        goal_reports: list[GoalReport] = []
        # TODO: extract function that is inside the loop called analyze goal
        for goal in goals:
            commands = self.agent.fetch_commands(doc.content, json.dumps(goal))
            # create new command executor for each goal in order to run all commands in single terminal session
            command_reports = ContainerCommandExecutor(self.agent).execute_commands_sync(commands)
            goal_report = GoalReport(goal["name"], goal["description"], command_reports)
            goal_reports.append(goal_report)
        #     TODO: give document name other than Some Document
        document_report: DocumentReport = DocumentReport("Some Document", goal_reports)
        Reporter(document_report).print_report()

        # TODO: post processing should be done outside of document analyzer and in a new module called workflow
        for goal in goal_reports:
            self.post_process_goal(goal, doc)
        return document_report

    def post_process_goal(self, goal_report: GoalReport, doc: Document):
        """
        Post processing a goal can be used for follow up actions such as fixing documentation for commands that failed
        :param goal_report:
        :param doc:
        :return:
        """
        command_executor = LocalCommandExecutor(self.agent)
        for command_report in goal_report.command_reports:
            if not command_report.success:
                modify_commands = self.agent.fetch_modify_file_commands(doc.filepath, command_report)
                modify_report = command_executor.execute_commands_sync(modify_commands)
                print(modify_report)
