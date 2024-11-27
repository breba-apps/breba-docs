import pytest
from dotenv import load_dotenv

from breba_docs.agent.graph_agent import GraphAgent


@pytest.fixture
def agent(doc):
    load_dotenv()
    return GraphAgent(doc)


@pytest.fixture
def doc():
    with open('./tests/integration/fixtures/doc.md', 'r') as file:
        return file.read()


@pytest.mark.integration
def test_invoke_graph(mocker, agent, doc):
    graph = GraphAgent(doc)
    state = graph.graph.invoke({"messages": []})
    goals = state['goals']
    getting_started_goal = next((goal for goal in goals if goal["name"] == "getting started"), None)
    assert getting_started_goal, "No goal with the name 'getting started' was found in the fetched goals."


