import os
from pathlib import Path

import pytest
import yaml
from cleo.testers.command_tester import CommandTester

from breba_docs.cli.commands.new_command import NewCommand
from breba_docs.cli.commands.run_command import RunCommand


@pytest.fixture(autouse=True)
def temp_project(tmp_path, monkeypatch):
    """
    Change the current working directory to a temporary directory.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path

@pytest.fixture
def new_project_path(temp_project):
    project_name = "TestProject"
    inputs = "openai\ngpt-4\ndummy_api_key\nNo\nbreba-image\n"

    new_command_tester = CommandTester(NewCommand())
    exit_code = new_command_tester.execute(args=project_name, inputs=inputs, interactive=True)
    assert exit_code == 0, "Failed to create config file"
    return Path(temp_project) / project_name


def test_new_command_with_option(new_project_path):
    """
    Test the 'new' command
    """
    # Verify that the expected directories and config file were created.
    project_root = new_project_path
    data_dir = project_root / "data"
    prompts_dir = project_root / "prompts"
    config_file = project_root / "config.yaml"

    assert data_dir.exists() and data_dir.is_dir(), "Missing data directory"
    assert prompts_dir.exists() and prompts_dir.is_dir(), "Missing prompts directory"
    assert config_file.exists() and config_file.is_file(), "Missing config.yaml file"

    # Load and verify the content of config.yaml.
    with config_file.open("r") as f:
        config = yaml.safe_load(f)

    assert config["project_name"] == "TestProject"
    assert config["container_image"] == "breba-image"
    models = config["models"]
    model_id = "openai-gpt-4-1"
    assert model_id in models
    model_details = models[model_id]
    assert model_details["type"] == "openai"
    assert model_details["name"] == "gpt-4"
    assert model_details["api_key"] == "dummy_api_key"
    assert model_details["temperature"] == 0.0


def test_run_command(mocker, new_project_path):
    """
    Test the 'run' command
    """
    mocker.patch("breba_docs.cli.commands.run_command.get_document", return_value=None)
    mocker.patch("breba_docs.cli.commands.run_command.run_analyzer", return_value=None)

    # Create an instance of RunCommand and wrap it with CommandTester.
    command = RunCommand()
    tester = CommandTester(command)

    # Testing with default path parameter, which will test in current directory
    exit_code = tester.execute(args=str(new_project_path), interactive=False)
    assert exit_code == 0

    # Verify that the expected output was printed.
    output = tester.io.fetch_output()
    assert "Running the breba-docs project..." in output
    assert "Project Name: TestProject" in output
    assert "Container Image: breba-image" in output
    assert "openai-gpt-4-1" in output
    assert "dummy_api_key" in output
    assert os.environ["OPENAI_API_KEY"] == "dummy_api_key"
    assert os.environ["BREBA_IMAGE"] == "breba-image"


def test_run_command_in_current_directory(mocker, new_project_path):
    """
    Test the 'run' command when in current directory
    """
    mocker.patch("breba_docs.cli.commands.run_command.get_document", return_value=None)
    mocker.patch("breba_docs.cli.commands.run_command.run_analyzer", return_value=None)

    os.chdir(new_project_path)

    # Create an instance of RunCommand and wrap it with CommandTester.
    command = RunCommand()
    tester = CommandTester(command)

    # Testing with default path parameter, which will test in current directory
    exit_code = tester.execute(interactive=False)
    assert exit_code == 0

    # Verify that the expected output was printed.
    output = tester.io.fetch_output()
    assert "Running the breba-docs project..." in output
    assert "Project Name: TestProject" in output
    assert "openai-gpt-4-1" in output
    assert "dummy_api_key" in output
