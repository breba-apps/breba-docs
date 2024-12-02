from pathlib import Path

import pytest
from dotenv import load_dotenv

from breba_docs.agent.graph_agent import GraphAgent
from breba_docs.container import container_setup
from breba_docs.services.document import Document


@pytest.fixture
def agent(doc):
    load_dotenv()
    return GraphAgent(doc)


@pytest.fixture
def doc():
    filepath = Path("tests/integration/fixtures/typo_doc.md")
    with open(filepath, 'r') as file:
        content =  file.read()
        return Document(content, filepath)

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
    graph = GraphAgent(doc) # agent(doc)
    state = graph.invoke()
    goals = state['goal_reports']
    getting_started_goal = next((goal for goal in goals if goal.goal_name == "getting started"), None)
    assert getting_started_goal, "No goal with the name 'getting started' was found in the fetched goals."
    assert getting_started_goal.command_reports[0].success
    assert getting_started_goal.command_reports[1].success
    assert not getting_started_goal.command_reports[2].success
    assert getting_started_goal.modify_command_reports[0].command =="sed -i 's/nodestream run simple -v/nodestream run sample -v/' tests/integration/fixtures/typo_doc.md"
