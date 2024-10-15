from breba_docs.services.agent import Agent


class MockAgent(Agent):
    def fetch_commands(self, text: str) -> list[str]:
        return [
            "pip install nodestream",
            "nodestream new --database neo4j my_project",
            "cd my_project",
            "nodestream run sample -v",
        ]

    def analyze_output(self, text: str) -> str:
        return ("Found some errors. Looks like cd my_project is failing to execute with the following error: cd "
                "command not found")

    def provide_input(self, text: str) -> str:
        return "Y"
