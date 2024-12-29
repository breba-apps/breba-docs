import pytest
from dotenv import load_dotenv

from breba_docs.services.command_executor import ContainerCommandExecutor
from breba_docs.agent.openai_agent import OpenAIAgent


@pytest.fixture
def openai_agent():
    load_dotenv()
    with OpenAIAgent() as agent:
        yield agent


@pytest.mark.integration
def test_container_command_executor_no_input(mocker, openai_agent):
    commands = [("export MY_VAR=Testing", "export MY_VAR=Testing"), ("echo $MY_VAR", "Testing")]
    with ContainerCommandExecutor.executor_and_new_container(openai_agent) as executor:
        with executor.session() as session:
            for command, expected_output in commands:
                output = session.execute_command(command)
                # TODO: check for exact output when we get rid of (.venv) from output
                assert expected_output in output


@pytest.mark.integration
def test_container_command_executor_with_input(mocker, openai_agent):
    commands = [("""read -p "Please enter today's date (YYYY-MM-DD): " user_date""", ""),
                ("echo Hello there $user_date", "Hello there ")]
    with ContainerCommandExecutor.executor_and_new_container(openai_agent) as executor:
        with executor.session() as session:
            for command, expected_output in commands:
                output = session.execute_command(command)
                if expected_output:
                    assert expected_output in output

