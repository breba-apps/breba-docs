import pytest
from dotenv import load_dotenv
from jinja2.ext import debug

from breba_docs.services.command_executor import ContainerCommandExecutor
from breba_docs.agent.openai_agent import OpenAIAgent


@pytest.fixture
def openai_agent():
    load_dotenv()
    with OpenAIAgent() as agent:
        yield agent

@pytest.fixture
def session(openai_agent):
    with ContainerCommandExecutor.executor_and_new_container(openai_agent, dev=True) as executor:
        with executor.session() as session:
            yield session


@pytest.mark.integration
def test_container_command_executor_no_input(mocker, session):
    commands = [("export MY_VAR=Testing", "$ export MY_VAR=Testing"), ("echo $MY_VAR", "$ echo $MY_VAR\nTesting")]

    for command, expected_output in commands:
        output = session.execute_command(command)
        assert expected_output == output.strip()


@pytest.mark.integration
def test_container_command_executor_with_input(mocker, session):
    commands = [("""read -p "Please enter today's date (YYYY-MM-DD): " user_date""", """$ read -p "Please enter today's date (YYYY-MM-DD): " user_date"""),
                ("echo Hello there $user_date", "Hello there ")]
    for command, expected_output in commands:
        output = session.execute_command(command)
        if expected_output:
            assert expected_output == output.strip()

