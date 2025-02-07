import pytest
from dotenv import load_dotenv

import re
from breba_docs.services.command_executor import LocalCommandExecutor
from breba_docs.agent.openai_agent import OpenAIAgent


@pytest.fixture
def openai_agent():
    load_dotenv()
    with OpenAIAgent() as agent:
        yield agent


@pytest.mark.integration
def test_local_command_executor(mocker, openai_agent):
    with LocalCommandExecutor.session(openai_agent) as executor:
        command_reports = executor.execute_commands_sync(
            ["""read -p "Please enter today's date (YYYY-MM-DD): " user_date""",
             "echo Hello there $user_date"]
        )
    assert command_reports[0].success


@pytest.mark.integration
def test_session(mocker, openai_agent):
    with LocalCommandExecutor.session(openai_agent) as executor:
        output = executor.execute_command("""read -p "Please enter today's date (YYYY-MM-DD): " user_date""")
        assert """$ read -p "Please enter today\'s date (YYYY-MM-DD): " user_date\n""" in output
        assert "Please enter today\'s date (YYYY-MM-DD): 2023-10-05" in output
        assert not re.search(r"Completed .*", output)
        output = executor.execute_command("echo Hello there $user_date")
        assert "$ echo Hello there $user_date\nHello there 2023-10-05" in output
        assert "\n\n" not in output  # Tests that end marker is removed along with corresponding newline
