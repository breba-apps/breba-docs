import json

import pytest
from dotenv import load_dotenv

from breba_docs.agent.command_exec_agent import CommandAgent
from breba_docs.services.command_executor import ContainerCommandExecutor
from breba_docs.agent.openai_agent import OpenAIAgent
from breba_docs.services.reports import CommandReport


@pytest.fixture
def openai_agent():
    load_dotenv()
    with OpenAIAgent() as agent:
        yield agent


@pytest.mark.integration
def test_container_command_executor(mocker, openai_agent):
    commands = ['python3 -m venv .venv', 'cd .venv',
                'source bin/activote']
    messages = []
    with ContainerCommandExecutor.executor_and_new_container(OpenAIAgent()) as command_executor:
        with command_executor.session() as session:
            agent = CommandAgent(session)
            for command in commands:
                messages = agent.invoke(command)["messages"]
    command_json = json.loads(messages[-1].content)
    command_report = CommandReport(**command_json)
    assert command_report.command == "source bin/activate"

