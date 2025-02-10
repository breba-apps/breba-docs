import pytest
from pty_server import AsyncPtyClient

from breba_docs.services.command_executor import ContainerCommandExecutor
from breba_docs.services.input_provider import InputProvider


@pytest.fixture
def mock_input_provider(mocker):
    return mocker.MagicMock(spec=InputProvider)

@pytest.fixture
def mock_pty_client(mocker):
    return mocker.MagicMock(spec=AsyncPtyClient)

@pytest.mark.asyncio
async def test_should_return_none_when_input_message_is_none(mocker, mock_input_provider, mock_pty_client):
    mock_input_provider.get_input = mocker.MagicMock(return_value=None)

    executor = ContainerCommandExecutor(mock_input_provider, mock_pty_client)
    provide_input = executor.create_provide_input()

    assert await provide_input(["Hello World"]) is None

@pytest.mark.asyncio
async def test_should_return_true_when_input_message_is_string(mocker, mock_input_provider, mock_pty_client):
    mock_input_provider.get_input = mocker.MagicMock(return_value="Hello World")
    mock_pty_client.send_input = mocker.AsyncMock(return_value=True)

    executor = ContainerCommandExecutor(mock_input_provider, mock_pty_client)
    provide_input = executor.create_provide_input()

    input_text = await provide_input(["Hello World"])
    assert input_text is True

@pytest.mark.asyncio
async def test_should_return_false_when_send_message_fails(mocker, mock_input_provider, mock_pty_client):
    mock_input_provider.get_input = mocker.MagicMock(return_value="Hello World")
    mock_pty_client.send_input = mocker.AsyncMock(return_value=False)

    executor = ContainerCommandExecutor(mock_input_provider, mock_pty_client)
    provide_input = executor.create_provide_input()

    assert await provide_input(["Hello World"]) is False