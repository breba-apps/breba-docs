import pytest
from dotenv import load_dotenv

from breba_docs.container import container_setup
from breba_docs.services.command_executor import ContainerCommandExecutor
from breba_docs.agent.openai_agent import OpenAIAgent

@pytest.fixture
def container():
    # To Run the container from terminal from breba_docs package dir
    # docker run -d -it \
    #   -v $(pwd)/breba_docs/socket_server:/usr/src/socket_server \
    #   -w /usr/src \
    #   -p 44440:44440 \
    #   python:3 \
    #   /bin/bash
    started_container = container_setup(dev=True)

    yield started_container
    started_container.stop()
    started_container.remove()


@pytest.fixture
def openai_agent():
    load_dotenv()
    with OpenAIAgent() as agent:
        yield agent


@pytest.mark.integration
def test_container_command_executor(mocker, openai_agent):
    executor = ContainerCommandExecutor(openai_agent)
    command_reports = executor.execute_commands_sync(
        ["""read -p "Please enter today's date (YYYY-MM-DD): " user_date""",
         "echo Hello there $user_date"]
    )
    assert command_reports[0].success

