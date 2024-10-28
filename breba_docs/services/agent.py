from abc import ABC, abstractmethod

from breba_docs.services.reports import CommandReport


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
        pass

    @abstractmethod
    def fetch_modify_file_commands(self, filepath: str, command_report: CommandReport) -> list[str]:
        """
        Given a command report, and the text of a document, come up with terminal commands to modify a file at the
        given filepath. The commands should be able to be run in sequence to modify the file.

        Args: filepath (str): The path to the file to modify. command_report (CommandReport): A command report
        containing information about the command that was run and the output of that command. document (str): The
        text of the document from which we are fetching commands.

        Returns:
            list[str]: A list of terminal commands to modify the file at the given filepath.
        """
        pass
