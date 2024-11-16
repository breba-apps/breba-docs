import json
from pathlib import Path

import pytest

from breba_docs.analyzer.document_analyzer import DocumentAnalyzer
from breba_docs.agent.agent import Agent
from breba_docs.services.document import Document
from breba_docs.socket_server.client import Client

GOALS = [{"name": "Install nodestream", "description": "Install nodestream"},
         {"name": "Install nodestream2", "description": "Install nodestream2"}]


@pytest.fixture
def mock_agent(mocker):
    mock_agent = mocker.MagicMock(spec=Agent)
    mock_agent.fetch_goals.return_value = GOALS
    mock_agent.fetch_commands.return_value = ['command1', 'command2']
    mock_agent.provide_input.return_value = "breba-noop"
    return mock_agent


@pytest.fixture
def mock_client(mocker):
    client = mocker.MagicMock(spec=Client)
    client.send_message.side_effect = ['response1', 'response2', 'response3', 'response4']
    client.read_response.side_effect = ['', '', '', '']  # This means no new data was received when double checking
    client.__enter__.return_value = client  # Ensure the context manager works correctly
    client.__exit__.return_value = None  # Ensure the context manager works correctly
    return client


def test_analyze(mocker, mock_agent, mock_client):
    # Mocking the Client class to return the mock_client
    mocker.patch('breba_docs.services.command_executor.Client', return_value=mock_client)
    mocker.patch('breba_docs.analyzer.document_analyzer.OpenAIAgent', return_value=mock_agent)

    doc = Document("first run echo 'command1', then run echo 'command2'", Path("README.md"))
    analyzer = DocumentAnalyzer()
    analyzer.analyze(doc)

    # Check that send_message was called with the correct JSON commands
    expected_command1 = json.dumps({"command": "command1"})
    expected_command2 = json.dumps({"command": "command2"})

    mock_client.send_message.assert_any_call(expected_command1)
    mock_client.send_message.assert_any_call(expected_command2)

    # Check that analyze_output was called with the final response
    mock_agent.analyze_output.assert_has_calls([
        mocker.call('response1'),
        mocker.call('response2')
    ], any_order=False)

    # We should open new client session for each goal to execute related commands in own terminal session
    assert mock_client.__enter__.call_count == len(GOALS)
    assert mock_client.__exit__.call_count == len(GOALS)
