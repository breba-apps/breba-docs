from typing import Generator

import pytest
from dotenv import load_dotenv

from breba_docs.agent.openai_agent import OpenAIAgent
from breba_docs.container import new_container
from breba_docs.services.command_executor import ContainerCommandExecutor
from breba_docs.services.input_provider import InputProvider, AgentInputProvider


@pytest.fixture(scope="module")
def input_provider() -> Generator[InputProvider, None, None]:
    load_dotenv()
    with OpenAIAgent() as agent:
        yield AgentInputProvider(agent)


@pytest.fixture(scope="module")
def container_executor():
    with new_container(dev=False) as executor:
        yield executor


@pytest.fixture
def session(container_executor, input_provider):
    # TODO: I wish there was not an implicit dependency on container. Maybe it is time to create a container class and factory
    with ContainerCommandExecutor(input_provider).session() as session:
        yield session


@pytest.mark.integration
def test_container_command_executor_no_input(mocker, session):
    commands = [("export MY_VAR=Testing", "$ export MY_VAR=Testing"), ("echo $MY_VAR", "$ echo $MY_VAR\nTesting")]

    for command, expected_output in commands:
        output = session.execute_command(command)
        assert expected_output in output.strip()


@pytest.mark.integration
def test_container_command_executor_with_input(mocker, session):
    commands = [("""read -p "Please enter October 5, 2023 in this format (YYYY-MM-DD): " user_date""",
                 """$ read -p "Please enter October 5, 2023 in this format (YYYY-MM-DD): " user_date\nPlease enter October 5, 2023 in this format (YYYY-MM-DD): 2023-10-05"""),
                ("echo Hello there $user_date", "$ echo Hello there $user_date\nHello there 2023-10-05")]
    for command, expected_output in commands:
        output = session.execute_command(command)
        if expected_output:
            assert expected_output in output.strip()
