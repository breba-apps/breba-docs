from abc import ABC, abstractmethod

from breba_docs.services.output_analyzer_result import CommandReport


class Agent(ABC):
    @abstractmethod
    def fetch_commands(self, text: str, goal: str) -> list[str]:
        """
        Fetch commands from the given text.

        Args:
            goal: the goal for which we are fetching the commands
            text (str): Input text from which commands are to be extracted.

        Returns:
            list[str]: A list of shell commands extracted from the text."""
        pass

    @abstractmethod
    def fetch_goals(self, doc: str) -> list[dict]:
        """
        Fetch goals from the given text.

        Args:
            doc (str): Input text from which goals are to be extracted.

        Returns:
            list[str]: A list of goals extracted from the text."""
        pass

    @abstractmethod
    def analyze_output(self, text: str) -> CommandReport:
        """ Analyze the given text. And provide explanation for the analysis
        Args:
            text (str): The output text to analyze for errors or information.

        Returns:
            str: A string message describing the result of the analysis.
        """
        pass

    @abstractmethod
    def provide_input(self, text: str) -> str:
        """ Ask agent for input
        Args
            text: string to check for potential prompts
        return:
            str: input for a prompt or empty string if no input is expected
        """
