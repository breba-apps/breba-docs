import pytest
from unittest.mock import mock_open
import requests
from breba_docs.cli import run


@pytest.fixture
def mock_docker(mocker):
    # Mocking docker client and container
    mock_client = mocker.MagicMock()
    mock_container = mocker.MagicMock()
    mock_container.exec_run.return_value = (None, "some output".encode())
    mock_client.containers.run.return_value = mock_container

    # Patching docker.from_env() to return the mock client
    mocker.patch('breba_docs.cli.docker.from_env', return_value=mock_client)
    return mock_container


@pytest.fixture
def mock_requests(mocker):
    # Patching requests.get to return a mock response
    mock_response = mocker.MagicMock(spec=requests.Response)
    mock_response.text = "Mock document content"
    mock_requests = mocker.patch('breba_docs.cli.requests')
    mock_requests.get.return_value = mock_response
    return mock_requests


@pytest.fixture
def mock_analyze(mocker):
    return mocker.patch('breba_docs.cli.analyze')


@pytest.fixture
def mock_openai_agent(mocker):
    # Patching the OpenAIAgent class to prevent real interactions
    mocker.patch('breba_docs.cli.OpenAIAgent')


def test_run_with_valid_url(mock_docker, mock_requests, mock_analyze, mock_openai_agent, mocker):
    # Test case where the user provides a valid URL

    mocker.patch('builtins.input', return_value="https://valid.url/to/document.md")
    mocker.patch('breba_docs.cli.is_valid_url', return_value=True)
    mocker.patch('breba_docs.cli.is_file_path', return_value=False)

    run()

    # Check that requests.get was called to fetch the document
    mock_requests.get.assert_called_once_with("https://valid.url/to/document.md")

    # Assert that the analyze function was called with the correct arguments
    mock_analyze.assert_called_once()


def test_run_with_valid_file_path(mocker, mock_docker, mock_analyze, mock_openai_agent):
    # Test case where the user provides a valid local file path

    mocker.patch('builtins.input', return_value="/valid/path/to/document.md")
    mocker.patch('breba_docs.cli.is_file_path', return_value=True)
    mocker.patch('breba_docs.cli.is_valid_url', return_value=False)

    # Mock the open function to simulate reading a file
    open_mock = mocker.patch('builtins.open', mock_open(read_data="Mock document content"))

    # Run the program
    run()

    # Assert that the file was opened and read
    open_mock.assert_any_call("/valid/path/to/document.md", "r")

    mock_analyze.assert_called_once()


def test_run_with_invalid_input(mocker, mock_docker):
    # Test case where the user provides invalid input

    mocker.patch('builtins.input', return_value="invalid_input")
    mocker.patch('breba_docs.cli.is_file_path', return_value=False)
    mocker.patch('breba_docs.cli.is_valid_url', return_value=False)
    print_mock = mocker.patch('builtins.print')

    # Run the program
    run()

    print_mock.assert_any_call("Not a valid URL or local file path. 1 retries remaining.")
    print_mock.assert_any_call("No document provided. Exiting...")

    mocker.patch('breba_docs.cli.analyze').assert_not_called()
