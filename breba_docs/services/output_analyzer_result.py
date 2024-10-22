import json
from dataclasses import dataclass


@dataclass
class CommandReport:
    command: str
    success: bool
    insights: str

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
