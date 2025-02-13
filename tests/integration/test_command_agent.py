import pytest
from dotenv import load_dotenv

from breba_docs.agent.command_exec_agent import CommandAgent
from breba_docs.agent.openai_agent import OpenAIAgent
from breba_docs.container import new_container
from breba_docs.services.command_executor import ContainerCommandExecutor
from breba_docs.services.input_provider import AgentInputProvider
from breba_docs.services.reports import CommandReport


@pytest.fixture
def openai_agent():
    load_dotenv()
    with OpenAIAgent() as agent:
        yield agent


@pytest.fixture
def agent(openai_agent):
    input_provider = AgentInputProvider(openai_agent)
    with new_container(dev=True):
        with ContainerCommandExecutor(input_provider).session() as session:
            yield CommandAgent(session)


@pytest.mark.integration
def test_typo_command_with_fix(agent):
    commands = ['python3 -m venv .venv', 'cd .venv',
                'source bin/activote']
    messages = []

    for command in commands:
        messages = agent.invoke(command)["messages"]

    command_report = CommandReport.from_string(messages[-1].content)

    assert command_report.command == "source bin/activote"
    assert command_report.improved_command == "source bin/activate"


@pytest.mark.integration
def test_typo_command_without_fix(agent):
    command = 'source bin/someabitch'
    messages = agent.invoke(command)["messages"]
    command_report = CommandReport.from_string(messages[-1].content)

    assert command_report.command == "source bin/someabitch"
    assert command_report.improved_command is None


@pytest.mark.integration
def test_command_with_missing_setup(agent):
    # TODO: This test fails sometimes because there are multiple correct "improved commands"
    command = 'cd my_project'
    messages = agent.invoke(command)["messages"]
    command_report = CommandReport.from_string(messages[-1].content)

    assert command_report.command == "cd my_project"
    assert command_report.improved_command == "mkdir my_project && cd my_project"
