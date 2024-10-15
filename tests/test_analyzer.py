import json
import pytest

from breba_docs.analyzer.service import analyze
from breba_docs.services.agent import Agent
from breba_docs.socket_server.client import Client


@pytest.fixture
def mock_agent(mocker):
    mock_agent = mocker.MagicMock(spec=Agent)
    mock_agent.fetch_commands.return_value = ['command1', 'command2']
    mock_agent.analyze_output.return_value = "Analyzed output"
    mock_agent.provide_input.return_value = "breba-noop"
    return mock_agent


@pytest.fixture
def mock_client(mocker):
    mock_client = mocker.MagicMock(spec=Client)
    mock_client.send_message.side_effect = ['response1', 'response2']
    mock_client.read_response.side_effect = ['', '']
    return mock_client


def test_analyze(mocker, mock_agent, mock_client):
    # Mocking the Client class to return the mock_client
    mocker.patch('breba_docs.analyzer.service.Client', return_value=mock_client)

    doc = "first run echo 'command1', then run echo 'command2'"
    analyze(mock_agent, doc)

    # Check that send_message was called with the correct JSON commands
    expected_command1 = json.dumps({"command": "command1"})
    expected_command2 = json.dumps({"command": "command2"})

    mock_client.send_message.assert_any_call(expected_command1)
    mock_client.send_message.assert_any_call(expected_command2)

    # Check that analyze_output was called with the final response
    mock_agent.analyze_output.assert_called_once_with('response2')

    # Check that the Client context was used
    mock_client.__enter__.assert_called_once()
    mock_client.__exit__.assert_called_once()
