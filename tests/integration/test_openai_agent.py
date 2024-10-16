import pytest

from breba_docs.services.openai_agent import OpenAIAgent
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


@pytest.mark.integration
def test_analyzer_output_pass(mocker, openai_agent, command_output):
    analysis = openai_agent.analyze_output(command_output)
    assert analysis.success, f"Analyzer is expect to produce error in this case, but got {analysis}"


@pytest.mark.integration
def test_analyzer_output_fail(mocker, openai_agent, command_output_fail):
    analysis = openai_agent.analyze_output(command_output_fail)
    assert not analysis.success, f"Analyzer is expect to produce error in this case, but got {analysis}"
