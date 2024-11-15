import pytest
from dotenv import load_dotenv

from breba_docs.services.command_executor import LocalCommandExecutor
from breba_docs.services.openai_agent import OpenAIAgent


@pytest.fixture
def openai_agent():
    load_dotenv()
    with OpenAIAgent() as agent:
        yield agent


@pytest.mark.integration
def test_local_command_executor(mocker, openai_agent):
    executor = LocalCommandExecutor(openai_agent)
    # TODO: this periodically fails to identify user prompt. Need to prompt engineer
    command_reports = executor.execute_commands_sync(
        ["""read -p "Please enter today's date (YYYY-MM-DD): " user_date""",
         "echo Hello there $user_date"]
    )
    assert command_reports[0].success

