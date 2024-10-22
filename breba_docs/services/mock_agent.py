from breba_docs.services.agent import Agent
from breba_docs.services.output_analyzer_result import OutputAnalyzerResult


class MockAgent(Agent):
    def fetch_goals(self, doc: str) -> list[str]:
        return ["Install nodestream", "Run sample"]

    def fetch_commands(self, text: str, goal: str) -> list[str]:
        return [
            "pip install nodestream",
            "nodestream new --database neo4j my_project",
            "cd my_project",
            "nodestream run sample -v",
        ]

    def analyze_output(self, text: str) -> OutputAnalyzerResult:
        return OutputAnalyzerResult.from_string("Found some errors. Looks like cd my_project is failing to execute "
                                                "with the following error: cd command not found")

    def provide_input(self, text: str) -> str:
        return "Y"
