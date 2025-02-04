import os
from pathlib import Path

import yaml

from cleo.commands.command import Command
from cleo.helpers import argument


class NewCommand(Command):
    """
    Creates a new breba-docs project.

    new
        {name? : The name of the project (if not provided, you will be prompted)}
    """
    name = "new"
    description = "Creates a new breba-docs project."

    arguments = [
        argument(
            "name",
            description="The name of the project (if not provided, you will be prompted)",
            optional=True
        )
    ]

    def create_project_structure(self, project_root):
        data_dir = project_root / "data"
        prompts_dir = project_root / "prompts"
        data_dir.mkdir(parents=False, exist_ok=False)
        prompts_dir.mkdir(parents=False, exist_ok=False)


    def handle(self):
        # Retrieve project name from option or prompt for it.
        project_name = self.argument("name")
        if not project_name:
            project_name = self.ask("Project name:")

        project_root = Path.cwd() / project_name

        try:
            os.makedirs(project_root, exist_ok=False)
            self.create_project_structure(project_root)

            # Interactively ask for model configuration.
            self.line("Configure your model:")
            # Currently, the only available model type is "openai".
            model_type = self.ask("Model type (available: openai):", default="openai")
            model_name = self.ask("Model name:")
            api_key = self.ask("API key:")

            # Generate a model_id using the combination of type, name, and a counter (starting at 1).
            model_id = f"{model_type}-{model_name}-1"

            # Build the configuration data.
            config_data = {
                "project_name": project_name,
                "models": {
                    model_id: {
                        "type": model_type,
                        "name": model_name,
                        "api_key": api_key,
                        "temperature": 0.0
                    }
                }
            }

            config_path = project_root / "config.yaml"
            try:
                with open(config_path, "w") as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            except Exception as e:
                self.line(f"<error>Error writing config file: {e}</error>")
                return

            self.line(f"<info>Project '{project_name}' created successfully!</info>")
        except Exception as e:
            self.line(f"<error>Project could not be created, it probably already exists: {e}</error>")
