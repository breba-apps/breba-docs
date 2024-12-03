import pytest

from breba_docs.agent.agent import Agent
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

