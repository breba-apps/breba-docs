import pytest

from breba_docs.agent.openai_agent import OpenAIAgent
from breba_docs.services.command_executor import ContainerCommandExecutor

@pytest.fixture
def mock_agent(mocker):
    return mocker.MagicMock(spec=OpenAIAgent)

def test_should_not_restart_retries_when_input_message_is_none(mocker, mock_agent):
    mocker.patch('breba_docs.services.command_executor.ContainerCommandExecutor.get_input_message', return_value=None)
    socket = mocker.MagicMock(send_message=mocker.Mock(return_value=True))

    executor = ContainerCommandExecutor(mock_agent, socket)
    should_restart_retries = executor.create_should_restart_retries()

    assert should_restart_retries(["Hello World"]) is False


def test_should_restart_retries_when_input_message_is_string(mocker, mock_agent):
    mocker.patch('breba_docs.services.command_executor.ContainerCommandExecutor.get_input_message', return_value="Hello World")
    socket = mocker.MagicMock(send_message=mocker.Mock(return_value=True))

    executor = ContainerCommandExecutor(mock_agent, socket)
    should_restart_retries = executor.create_should_restart_retries()

    assert should_restart_retries(["Hello World"]) is True

def test_should_not_restart_retries_when_send_message_fails(mocker, mock_agent):
    mocker.patch('breba_docs.services.command_executor.ContainerCommandExecutor.get_input_message', return_value="Hello World")
    socket = mocker.MagicMock(send_message=mocker.Mock(return_value=False))

    executor = ContainerCommandExecutor(mock_agent, socket)
    should_restart_retries = executor.create_should_restart_retries()

    assert should_restart_retries(["Hello World"]) is False