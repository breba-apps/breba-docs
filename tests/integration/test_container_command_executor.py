from unittest.mock import patch

import pytest
from dotenv import load_dotenv

from breba_docs.container import container_setup
from breba_docs.services.command_executor import ContainerCommandExecutor
from breba_docs.agent.openai_agent import OpenAIAgent

@pytest.fixture()
def mock_container_setup():
    with patch("breba_docs.services.command_executor.container_setup") as mocked_container_setup:  # Replace `my_module` with the actual module name
        mocked_container_setup.side_effect = lambda debug=True, dev=True: container_setup(debug=debug, dev=dev)
        yield mocked_container_setup


@pytest.fixture
def openai_agent():
    load_dotenv()
    with OpenAIAgent() as agent:
        yield agent


@pytest.mark.integration
def test_container_command_executor(mocker, openai_agent, mock_container_setup):
    executor = ContainerCommandExecutor(openai_agent)
    command_reports = executor.execute_commands_sync(
        ["""read -p "Please enter today's date (YYYY-MM-DD): " user_date""",
         "echo Hello there $user_date"]
    )
    assert command_reports[0].success

