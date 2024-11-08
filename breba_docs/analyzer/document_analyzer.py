import json

from breba_docs.analyzer.reporter import Reporter
from breba_docs.services.agent import Agent
from breba_docs.services.command_executor import ContainerCommandExecutor
from breba_docs.services.reports import GoalReport, DocumentReport, CommandReport
from breba_docs.services.openai_agent import OpenAIAgent


class DocumentAnalyzer:
    def __init__(self):
        self.agent: Agent = OpenAIAgent()

    def analyze(self, doc: str):
        goals = self.agent.fetch_goals(doc)
        goal_reports: list[GoalReport] = []
        for goal in goals:
            commands = self.agent.fetch_commands(doc, json.dumps(goal))
            # create new command executor for each goal in order to run all commands in single terminal session
            command_reports = ContainerCommandExecutor(self.agent).execute_commands_sync(commands)
            goal_report = GoalReport(goal["name"], goal["description"], command_reports)
            goal_reports.append(goal_report)
        document_report: DocumentReport = DocumentReport("Some Document", goal_reports)
        Reporter(document_report).print_report()