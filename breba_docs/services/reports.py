import json
from dataclasses import dataclass, field


@dataclass
class Goal:
    name: str
    description: str

@dataclass
class CommandReport:
    command: str
    improved_command: str | None
    success: bool | None
    insights: str | None

    @classmethod
    def from_string(cls, message: str) -> "CommandReport":
        data = json.loads(message)
        return cls(data["command"], data["improved_command"], data["success"], data["insights"])

    @classmethod
    def example_str(cls) -> str:
        return json.dumps({
            "command": "git clone https://github.com/Nodestream/nodestream.git",
            "improved_command": None,
            "success": True,
            "insights": "The cloning process completed successfully with all objects received and deltas resolved."
        })


@dataclass
class GoalReport:
    goal: Goal
    command_reports: list[CommandReport]
    modify_command_reports: list[CommandReport] = field(default_factory=list)


@dataclass
class DocumentReport:
    file: str
    goal_reports: list[GoalReport]


@dataclass
class ProjectReport:
    project: str
    file_reports: list[DocumentReport]
