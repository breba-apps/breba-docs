import pytest
from dotenv import load_dotenv

from breba_docs.agent.graph_agent import GraphAgent
from breba_docs.container import container_setup


@pytest.fixture
def agent(doc):
    load_dotenv()
    return GraphAgent(doc)


@pytest.fixture
def doc():
    with open('./tests/integration/fixtures/doc.md', 'r') as file:
        return file.read()

@pytest.fixture(autouse=True)
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


@pytest.mark.integration
def test_invoke_graph(mocker, agent, doc):
    graph = GraphAgent(doc)
    state = graph.invoke()
    goals = state['goal_reports']
    getting_started_goal = next((goal for goal in goals if goal.goal_name == "getting started"), None)
    # TODO: test commands list as well as command execution success
    assert getting_started_goal, "No goal with the name 'getting started' was found in the fetched goals."


