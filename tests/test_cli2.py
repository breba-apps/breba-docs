import yaml
from pathlib import Path

import pytest

from cleo.testers.command_tester import CommandTester
from breba_docs.cli2.commands.new_command import NewCommand
from breba_docs.cli2.commands.run_command import RunCommand


@pytest.fixture
def temp_project(tmp_path, monkeypatch):
    """
    Change the current working directory to a temporary directory.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_new_command_with_option(temp_project):
    """
    Test the 'new' command using the --name option and simulated interactive input for model configuration.
    """
    # Create an instance of NewCommand and wrap it with CommandTester.
    command = NewCommand()
    tester = CommandTester(command)

    # Prepare simulated interactive input as a single string.
    # The expected answers are:
    # 1. Model type (default "openai")
    # 2. Model name
    # 3. API key
    inputs = "openai\ngpt-4\ndummy_api_key\n"

    project_name = "TestProject"
    # Execute the command with the --name option.
    # The command will pick up the provided inputs interactively.
    exit_code = tester.execute(args=project_name, inputs=inputs, interactive=True)
    assert exit_code == 0

    # Verify that the expected directories and config file were created.
    project_root = Path(temp_project) / project_name
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
    models = config["models"]
    model_id = "openai-gpt-4-1"
    assert model_id in models
    model_details = models[model_id]
    assert model_details["type"] == "openai"
    assert model_details["name"] == "gpt-4"
    assert model_details["api_key"] == "dummy_api_key"
    assert model_details["temperature"] == 0.0


def test_run_command(temp_project):
    """
    Test the 'run' command by creating a dummy config.yaml file and checking the output.
    """
    # Create a dummy configuration.
    config = {
        "project_name": "TestProject",
        "models": {
            "openai-gpt-4-1": {
                "type": "openai",
                "name": "gpt-4",
                "api_key": "dummy_api_key",
                "temperature": 0.0
            }
        }
    }
    config_file = temp_project / "config.yaml"
    with config_file.open("w") as f:
        yaml.dump(config, f)

    # Create an instance of RunCommand and wrap it with CommandTester.
    command = RunCommand()
    tester = CommandTester(command)

    # Testing with default path parameter, which will test in current directory
    exit_code = tester.execute(interactive=False)
    assert exit_code == 0

    # Retrieve the output from the command.
    output = tester.io.fetch_output()

    # Check that the output contains the expected information.
    assert "Running the breba-docs project..." in output
    assert "Project Name: TestProject" in output
    assert "openai-gpt-4-1" in output
    assert "dummy_api_key" in output
