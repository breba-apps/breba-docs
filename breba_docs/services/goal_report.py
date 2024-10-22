from dataclasses import dataclass

from breba_docs.services.output_analyzer_result import CommandReport


@dataclass
class GoalReport:
    goal_name: str
    goal_description: str
    command_reports: list[CommandReport]


@dataclass
class DocumentReport:
    file: str
    goal_reports: list[GoalReport]


@dataclass
class ProjectReport:
    project: str
    file_reports: list[DocumentReport]