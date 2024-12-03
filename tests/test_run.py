from pathlib import Path

import git
import pytest
from unittest.mock import mock_open, MagicMock

from breba_docs.cli import start_cli
from breba_docs.services.reports import DocumentReport


@pytest.fixture(autouse=True)
def mock_container(mocker):
    mocker.patch('breba_docs.cli.container_setup', return_value=MagicMock())


@pytest.fixture(autouse=True)
def mock_project_setup(mocker):
    mocker.patch('breba_docs.cli.os', return_value=MagicMock())


@pytest.fixture
def mock_repo(mocker):
    # Patching requests.get to return a mock response
    mock_repo = mocker.MagicMock(spec=git.Repo)
    mock_repo.working_dir = '/path/to/mock/repo'
    mock_git_repo = mocker.patch('breba_docs.cli.Repo')
    mock_git_repo.clone_from = mocker.MagicMock(return_value=mock_repo)


@pytest.fixture()
def create_document_report(mocker):
    return mocker.patch('breba_docs.cli.create_document_report', return_value=DocumentReport("Some Document", []))


def test_run_with_valid_url(mock_repo, create_document_report, mocker):
    # Test case where the user provides a valid URL

    mocker.patch('builtins.input', return_value="https://valid.url/to/document.md")
    open_mock = mocker.patch('builtins.open', mock_open(read_data="Mock document content"))

    start_cli("sample_project")

    open_mock.assert_called_with(Path('/path/to/mock/repo/README.md'), "r")

    create_document_report.assert_called_once()


def test_run_with_valid_file_path(mocker, create_document_report):
    # Test case where the user provides a valid local file path
    current_dir = Path(__file__).parent
    real_file_path = str(current_dir / "sample.md")  # use a valid file path
    mocker.patch('builtins.input', return_value=real_file_path)

    # Mock the open function to simulate reading a file
    open_mock = mocker.patch('builtins.open', mock_open(read_data="Mock document content"))

    # Run the program
    start_cli("sample_project")

    # Assert that the file was opened and read
    open_mock.assert_any_call(real_file_path, "r")

    create_document_report.assert_called_once()


def test_run_with_invalid_input(mocker, create_document_report):
    # Test case where the user provides invalid input
    mocker.patch('builtins.input', return_value="invalid_input")
    print_mock = mocker.patch('builtins.print')

    # Run the program
    start_cli("sample_project")

    print_mock.assert_any_call("Not a valid URL or local file path. 1 retries remaining.")
    print_mock.assert_any_call("No document provided. Exiting...")

    create_document_report.assert_not_called()
