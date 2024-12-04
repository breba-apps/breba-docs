import json
from unittest.mock import Mock, patch, MagicMock

import pytest
from langgraph.constants import END

from breba_docs.agent.graph_agent import GraphAgent, AgentState
from breba_docs.services.reports import CommandReport, GoalReport


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

    result = graph_agent.identify_goals(AgentState(messages=[], goals=[], goal_reports=[]))

    # Assertions
    assert result["goals"] == [{"name": "Goal 1", "description": "Desc 1"}]
    graph_agent.model.invoke.assert_called_once()


def test_maybe_start_next_goal_commands_succeeded():
    # Create CommandReports and a GoalReport
    command_reports = [
        CommandReport(command="echo Hello", success=True, insights=None),
        CommandReport(command="ls -la", success=True, insights=None),
    ]
    goal_report = GoalReport(
        goal_name="Sample Goal",
        goal_description="Test goal for identify_commands",
        command_reports=command_reports,
    )

    state = AgentState(
        messages=[],
        goals=[{"name": "Sample Goal", "description": "Test goal for identify_commands"}],
        goal_reports=[goal_report],
    )

    mock_doc = Mock(content="Sample document content")

    graph_agent = GraphAgent(doc=mock_doc)

    result = graph_agent.maybe_start_next_goal(state)

    assert result == "identify_commands"

def test_maybe_start_next_goal_commands_failed():
    command_reports = [
        CommandReport(command="echo Hello", success=True, insights=None),
        CommandReport(command="ls -la", success=False, insights=None),
    ]
    goal_report = GoalReport(
        goal_name="Sample Goal",
        goal_description="Test goal for identify_commands",
        command_reports=command_reports,
    )

    state = AgentState(
        messages=[],
        goals=[{"name": "Sample Goal", "description": "Test goal for identify_commands"}],
        goal_reports=[goal_report],
    )

    mock_doc = Mock(content="Sample document content")

    graph_agent = GraphAgent(doc=mock_doc)

    result = graph_agent.maybe_start_next_goal(state)

    assert result == "execute_mutator_commands"


def test_maybe_start_next_goal_no_more_goals():
    command_reports = [
        CommandReport(command="echo Hello", success=True, insights=None),
        CommandReport(command="ls -la", success=True, insights=None),
    ]
    goal_report = GoalReport(
        goal_name="Sample Goal",
        goal_description="Test goal for identify_commands",
        command_reports=command_reports,
    )

    state = AgentState(
        messages=[],
        goals=[],
        goal_reports=[goal_report],
    )

    mock_doc = Mock(content="Sample document content")

    graph_agent = GraphAgent(doc=mock_doc)

    result = graph_agent.maybe_start_next_goal(state)

    assert result == END