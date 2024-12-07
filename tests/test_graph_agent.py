import json
from unittest.mock import Mock, patch, MagicMock

import pytest
from langgraph.constants import END

from breba_docs.agent.graph_agent import GraphAgent, AgentState
from breba_docs.services.reports import CommandReport, GoalReport, Goal


@pytest.fixture(autouse=True)
def mock_model(mocker):
    mocker.patch('breba_docs.agent.graph_agent.ChatOpenAI')

@pytest.fixture(autouse=True)
def mock_openai_agent(mocker):
    mocker.patch('breba_docs.agent.graph_agent.OpenAIAgent')


def test_identify_goals():
    mock_doc = Mock(content="Sample document content")

    graph_agent = GraphAgent(doc=mock_doc)

    mock_response = Mock()
    mock_response.content = json.dumps({"goals": [{"name": "Goal 1", "description": "Desc 1"}]})
    graph_agent.model.invoke.return_value = mock_response

    result = graph_agent.identify_goals(AgentState(messages=[], goals=[], goal_reports=[], current_goal=None))

    assert result["goals"] == [Goal(name="Goal 1", description="Desc 1")]
    graph_agent.model.invoke.assert_called_once()


def test_commands_succeeded():
    # Create CommandReports and a GoalReport
    command_reports = [
        CommandReport(command="echo Hello", success=True, insights=None),
        CommandReport(command="ls -la", success=True, insights=None),
    ]
    goal_report = GoalReport(
        Goal(name="Sample Goal", description="Test goal for identify_commands"),
        command_reports=command_reports,
    )

    state = AgentState(
        messages=[],
        goals=[Goal(name="Sample Goal", description="Test goal for identify_commands")],
        goal_reports=[goal_report],
        current_goal=None
    )

    mock_doc = Mock(content="Sample document content")

    graph_agent = GraphAgent(doc=mock_doc)

    assert graph_agent.commands_succeeded(state)

def test_commands_failed():
    command_reports = [
        CommandReport(command="echo Hello", success=True, insights=None),
        CommandReport(command="ls -la", success=False, insights=None),
    ]
    goal_report = GoalReport(
        Goal(name="Sample Goal", description="Test goal for identify_commands"),
        command_reports=command_reports,
    )

    state = AgentState(
        messages=[],
        goals=[Goal(name="Sample Goal", description="Test goal for identify_commands")],
        goal_reports=[goal_report],
        current_goal=None
    )

    mock_doc = Mock(content="Sample document content")

    graph_agent = GraphAgent(doc=mock_doc)

    assert not graph_agent.commands_succeeded(state)
