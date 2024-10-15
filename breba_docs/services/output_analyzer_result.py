from dataclasses import dataclass

PASS = "PASS"
FAIL = "FAIL"
UNKNOWN = "UNKNOWN"


@dataclass
class OutputAnalyzerResult:
    success: bool
    insights: str

    @classmethod
    def from_string(cls, message: str) -> "OutputAnalyzerResult":
        # Split the string into parts
        parts = message.split(", ", 1)

        # Determine the success based on the first part
        success = parts[0] == PASS

        # The rest of the message is the insights
        insights = parts[1] if len(parts) > 1 else ""

        return cls(success, insights)