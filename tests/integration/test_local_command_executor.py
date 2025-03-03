import re
from typing import Generator

import pytest
from dotenv import load_dotenv

from breba_docs.agent.openai_agent import OpenAIAgent
from breba_docs.services.command_executor import LocalCommandExecutor
from breba_docs.services.input_provider import AgentInputProvider, InputProvider


@pytest.fixture
def input_provider() -> Generator[InputProvider, None, None]:
    # TODO: need a fake input provider for tests, but own tests for Input Provider
    load_dotenv()
    with OpenAIAgent() as agent:
        provider = AgentInputProvider(agent)
        yield provider


@pytest.mark.integration
def test_session(input_provider: InputProvider):
    with LocalCommandExecutor(input_provider).session() as executor:
        output = executor.execute_command("""read -p "Please enter today's date (YYYY-MM-DD): " user_date""")
        assert """$ read -p "Please enter today\'s date (YYYY-MM-DD): " user_date\n""" in output
        assert "\nPlease enter today\'s date (YYYY-MM-DD): 2023-10-05" in output
        assert not re.search(r"Completed .*", output)
        output = executor.execute_command("echo Hello there $user_date")
        assert "$ echo Hello there $user_date\nHello there 2023-10-05" in output
        assert "\n\n" not in output  # Tests that end marker is removed along with corresponding newline
