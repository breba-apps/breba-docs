import json
from dataclasses import dataclass


@dataclass
class CommandReport:
    command: str
    success: bool | None
    insights: str | None

    @classmethod
    def from_string(cls, message: str) -> "CommandReport":
        data = json.loads(message)
        return cls(data["command"], data["success"], data["insights"])

    @classmethod
    def example_str(cls) -> str:
        return json.dumps({
            "command": "git clone https://github.com/Nodestream/nodestream.git",
            "success": True,
            "insights": "The cloning process completed successfully with all objects received and deltas resolved."
        })


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
