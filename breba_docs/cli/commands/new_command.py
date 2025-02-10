import os
from pathlib import Path

import docker
import yaml

from cleo.commands.command import Command
from cleo.helpers import argument
from docker.models.images import Image


def create_project_structure(project_root):
    data_dir = project_root / "data"
    prompts_dir = project_root / "prompts"
    data_dir.mkdir(parents=False, exist_ok=False)
    prompts_dir.mkdir(parents=False, exist_ok=False)


def create_docker_image(name, command):
    command.line("Creating docker image...")
    client = docker.from_env()

    # Step 1: Run a container from the python:3 image to perform the setup.
    setup_command = (
        "bash -c '"
        "python -m venv /usr/src/.venv "
        "&& . /usr/src/.venv/bin/activate "
        "&& pip install pty-server'"
    )

    command.line("Starting a sample container...")
    setup_container = client.containers.run(
        image="python:3",
        command=setup_command,
        working_dir="/usr/src",
        detach=True,
        tty=True
    )

    setup_container.wait()
    command.line("Creating a new image...")

    cmd_instruction = (
        'CMD ["/bin/bash", "-c", "VIRTUAL_ENV_DISABLE_PROMPT=1 . .venv/bin/activate && pty-server"]'
    )
    new_image: Image = setup_container.commit(
        repository=name,
        tag="latest",
        changes=[cmd_instruction]
    )
    command.line(f"Docker image created.{new_image.tags}")


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

    def handle(self):
        # Retrieve project name from option or prompt for it.
        project_name = self.argument("name")
        if not project_name:
            project_name = self.ask("Project name:")

        project_root = Path.cwd() / project_name

        try:
            # Interactively ask for model configuration.
            self.line("Configure your model:")
            # Currently, the only available model type is "openai".
            model_type = self.choice("Model type:", ["openai"], default=0)
            model_name = self.ask("Model name:")
            api_key = self.ask("API key:")
            create_docker = self.confirm(
                "Do you need to create a docker image for command execution?",
                default=True
            )

            if create_docker:
                container_image = self.ask("How would you like to name the new docker image:")
                create_docker_image(container_image, self)
            else:
                container_image = self.ask("What container image would you like to use for executing commands:")

            # Generate a model_id using the combination of type, name, and a counter (starting at 1).
            model_id = f"{model_type}-{model_name}-1"

            os.makedirs(project_root, exist_ok=False)
            create_project_structure(project_root)

            # Build the configuration data.
            config_data = {
                "project_name": project_name,
                "container_image": container_image,
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
