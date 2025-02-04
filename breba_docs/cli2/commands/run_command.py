import os
from pathlib import Path

import yaml

from cleo.commands.command import Command
from cleo.helpers import argument


class RunCommand(Command):
    """
    Run the breba-docs project.

    run
        {project_path? : path to the project to run. Defaults to the current directory.}
    """
    name = "run"
    description = "Run the breba-docs project in the current directory."

    arguments = [
        argument(
            "project_path",
            description="path to the project to run. Defaults to the current directory.",
            optional=True
        )
    ]

    def handle(self):
        project_name = self.argument("project_path")
        if project_name:
            project_root = Path(os.getcwd()) / project_name
        else:
            project_root = Path(os.getcwd())

        config_path = project_root / "config.yaml"

        # Ensure we are in a valid breba-docs project directory
        if not config_path.exists():
            self.line(
                "<error>No configuration file found. Are you sure you are in a breba-docs project directory?</error>")
            return

        # Load the configuration file
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            self.line(f"<error>Error reading configuration file: {e}</error>")
            return

        # For demonstration, simply display the configuration details
        self.line("<info>Running the breba-docs project...</info>")
        self.line(f"Project Name: {config.get('project_name', 'Unknown')}")
        self.line("Configured Models:")

        models = config.get("models", {})
        if models:
            for model_id, model_details in models.items():
                self.line(f" - {model_id}: {model_details}")
        else:
            self.line(" <comment>No models configured.</comment>")
