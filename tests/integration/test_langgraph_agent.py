import pytest
from dotenv import load_dotenv

from breba_docs.agent.graph_agent import GraphAgent


@pytest.fixture
def agent():
    load_dotenv()
    return GraphAgent()


@pytest.fixture
def doc():
    with open('./tests/integration/fixtures/doc.md', 'r') as file:
        return file.read()


@pytest.mark.integration
def test_fetch_goals(mocker, agent, doc):
    goals = agent.fetch_goals(doc)
    getting_started_goal = next((goal for goal in goals if goal["name"] == "getting started"), None)
    assert getting_started_goal, "No goal with the name 'getting started' was found in the fetched goals."


