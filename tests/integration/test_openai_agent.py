from pathlib import Path

import pytest

from breba_docs.services.reports import CommandReport
from breba_docs.agent.openai_agent import OpenAIAgent
from dotenv import load_dotenv


@pytest.fixture
def openai_agent():
    load_dotenv()
    with OpenAIAgent() as agent:
        yield agent


@pytest.fixture
def command_output():
    with open('./tests/integration/fixtures/command_output_pass.txt', 'r') as file:
        return file.read()


@pytest.fixture
def command_output_fail():
    with open('./tests/integration/fixtures/command_output_fail.txt', 'r') as file:
        return file.read()


@pytest.fixture
def doc():
    with open('./tests/integration/fixtures/doc.md', 'r') as file:
        return file.read()


@pytest.mark.integration
def test_analyzer_output_pass(mocker, openai_agent, command_output):
    analysis = openai_agent.analyze_output(command_output)
    assert analysis.success, f"Analyzer is expect to produce error in this case, but got {analysis}"


@pytest.mark.integration
def test_analyzer_output_fail(mocker, openai_agent, command_output_fail):
    analysis = openai_agent.analyze_output(command_output_fail)
    assert not analysis.success, f"Analyzer is expect to produce error in this case, but got {analysis}"


@pytest.mark.integration
def test_fetch_goals(mocker, openai_agent, doc):
    goals = openai_agent.fetch_goals(doc)
    getting_started_goal = next((goal for goal in goals if goal["name"] == "getting started"), None)
    assert getting_started_goal, "No goal with the name 'getting started' was found in the fetched goals."


@pytest.mark.integration
def test_fetch_commands(mocker, openai_agent, doc):
    goal = {'description': 'As a user, I would like to get started with the nodestream software',
            'name': 'getting started'}
    commands = openai_agent.fetch_commands(doc, goal)
    expected_commands = [
        'pip install nodestream',
        'nodestream new --database neo4j my_project && cd my_project',
        'nodestream run sample -v'
    ]
    assert commands == expected_commands


@pytest.mark.integration
def test_fetch_modify_file_commands(mocker, openai_agent):
    report = CommandReport(command="nodestream run simple -v",
                           success=False,
                           insights="The command failed because there is no pipeline named 'simple' found in the "
                                    "project. A suggestion was provided to check if 'sample' was intended instead.")
    filepath = Path('./tests/integration/fixtures/typo_doc.md')
    commands = openai_agent.fetch_modify_file_commands(filepath, report)
    expected_command = "sed -i '' 's/nodestream run simple -v/nodestream run sample -v/' tests/integration/fixtures/typo_doc.md"
    assert commands[0] == expected_command


@pytest.mark.integration
def test_input_required(mocker, openai_agent):
    output = """(.venv) pip uninstall nodestream
(.venv) (.venv)
Found existing installation: nodestream 0.13.2

Uninstalling nodestream-0.13.2:

Would remove:

/usr/src/.venv/bin/nodestream
/usr/src/.venv/lib/python3.12/site-packages/nodestream-0.13.2.dist-info/*
/usr/src/.venv/lib/python3.12/site-packages/nodestream/*

Proceed (Y/n)?"""
    command_input = openai_agent.provide_input(output)
    assert command_input == "Y"


@pytest.mark.integration
def test_input_already_provided(mocker, openai_agent):
    output = """(.venv) pip uninstall nodestream
(.venv) (.venv)
Found existing installation: nodestream 0.13.2

Uninstalling nodestream-0.13.2:

Would remove:

/usr/src/.venv/bin/nodestream
/usr/src/.venv/lib/python3.12/site-packages/nodestream-0.13.2.dist-info/*
/usr/src/.venv/lib/python3.12/site-packages/nodestream/*

Proceed (Y/n)?
Completed 91b16e7e-8ebd-49cc-8bc3-566f28429ae9
"""

    command_input = openai_agent.provide_input(output)
    assert command_input == "breba-noop"


@pytest.mark.integration
def test_input_in_the_middle(mocker, openai_agent):
    output = """(.venv) pip uninstall nodestream
(.venv) (.venv)
Found existing installation: nodestream 0.13.2

Uninstalling nodestream-0.13.2:

Would remove:

/usr/src/.venv/bin/nodestream
/usr/src/.venv/lib/python3.12/site-packages/nodestream-0.13.2.dist-info/*
/usr/src/.venv/lib/python3.12/site-packages/nodestream/*

Proceed (Y/n)?
Requirement already satisfied: nodestream in ./.venv/lib/python3.12/site-packages (0.13.2)
Requirement already satisfied: Jinja2<4,>=3 in ./.venv/lib/python3.12/site-packages (from nodestream) (3.1.4)
Requirement already satisfied: boto3<2.0.0,>=1.34.127 in ./.venv/lib/python3.12/site-packages (from nodestream) (1.35.50)
"""
    command_input = openai_agent.provide_input(output)
    assert command_input == "breba-noop"
