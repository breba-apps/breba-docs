import pytest

from breba_docs.agent.openai_agent import OpenAIAgent
from breba_docs.services.command_executor import ContainerCommandExecutor

@pytest.fixture
def mock_agent(mocker):
    return mocker.MagicMock(spec=OpenAIAgent)

@pytest.mark.asyncio
async def test_should_return_none_when_input_message_is_none(mocker, mock_agent):
    mocker.patch('breba_docs.services.command_executor.ContainerCommandExecutor.get_input_message', return_value=None)
    socket = mocker.MagicMock(send_message=mocker.Mock(return_value=True))

    executor = ContainerCommandExecutor(mock_agent, socket)
    provide_input = executor.create_provide_input()

    assert await provide_input(["Hello World"]) is None

@pytest.mark.asyncio
async def test_should_return_true_when_input_message_is_string(mocker, mock_agent):
    mocker.patch('breba_docs.services.command_executor.ContainerCommandExecutor.get_input_message', return_value="Hello World")
    socket = mocker.MagicMock(send_message=mocker.AsyncMock(return_value=True))

    executor = ContainerCommandExecutor(mock_agent, socket)
    provide_input = executor.create_provide_input()

    assert await provide_input(["Hello World"]) is True

@pytest.mark.asyncio
async def test_should_return_false_when_send_message_fails(mocker, mock_agent):
    mocker.patch('breba_docs.services.command_executor.ContainerCommandExecutor.get_input_message', return_value="Hello World")
    socket = mocker.MagicMock(send_message=mocker.AsyncMock(return_value=False))

    executor = ContainerCommandExecutor(mock_agent, socket)
    provide_input = executor.create_provide_input()

    assert await provide_input(["Hello World"]) is False