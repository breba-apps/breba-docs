import os
import shutil
from pathlib import Path
from urllib.parse import urlparse

import yaml
from cleo.commands.command import Command
from cleo.helpers import argument
from git import Repo

from breba_docs.analyzer.document_analyzer import create_document_report
from breba_docs.analyzer.reporter import Reporter
from breba_docs.services.document import Document


def is_valid_url(url):
    # TODO: check if md file
    parsed_url = urlparse(url)

    return all([parsed_url.scheme, parsed_url.netloc])


def clean_data():
    data_dir = Path("data")

    if data_dir.exists() and data_dir.is_dir():
        shutil.rmtree(data_dir)

    data_dir.mkdir(parents=True, exist_ok=True)


def get_document(project_root: Path, retries=3):
    print(f"\nProject root is: {project_root}")
    data_dir = project_root / "data"

    if retries == 0:
        return None

    location = input(f"Provide URL to git repo or an path to file:")

    if Path(location).is_file():
        clean_data()
        with open(location, "r") as file:
            # We will now copy this file into the data folder
            filepath = data_dir / Path(location).name
            document = Document(file.read(), filepath)
            # This is a new document, so we need to persist it to write to filepath
            document.persist()

            return document
    elif is_valid_url(location):
        clean_data()
        # TODO: log errors
        repo: Repo = Repo.clone_from(location, data_dir)
        filepath = Path(repo.working_dir) / "README.md"
        with open(filepath, "r") as file:
            return Document(file.read(), filepath)
    else:
        print(f"Not a valid URL or local file path. {retries - 1} retries remaining.")
        return get_document(project_root, retries - 1)


def run_analyzer(document: Document):
    if document:
        report = create_document_report(document)
        Reporter(report).print_report()
    else:
        print("No document provided. Exiting...")


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
        # TODO: This is actually project path, need to handle path instead of name
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
        self.line(f"Container Image: {config.get('container_image', 'Unknown')}")
        self.line("Configured Models:")

        models = config.get("models", {})
        if models:
            for model_id, model_details in models.items():
                self.line(f" - {model_id}: {model_details}")
        else:
            self.line(" <comment>No models configured.</comment>")

        # TODO: Use named model
        first_model_id = next(iter(config['models']))
        first_model = config['models'][first_model_id]
        # TODO: create a config singleton module
        os.environ["OPENAI_API_KEY"] = first_model["api_key"]
        os.environ["BREBA_IMAGE"] = config["container_image"]
        document = get_document(project_root)
        run_analyzer(document)
