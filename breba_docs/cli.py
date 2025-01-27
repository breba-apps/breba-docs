import argparse
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from urllib.parse import urlparse

from git import Repo

from breba_docs import config
from breba_docs.analyzer.document_analyzer import create_document_report
from breba_docs.analyzer.reporter import Reporter
from breba_docs.container import container_setup
from breba_docs.services.document import Document


def is_valid_url(url):
    # TODO: check if md file
    parsed_url = urlparse(url)

    return all([parsed_url.scheme, parsed_url.netloc])


def parse_arguments():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Breba CLI")
    parser.add_argument("--debug-server", action="store_true", help="Enable logging from the server.")
    parser.add_argument(
        "project",
        nargs="?",
        default=".",
        help="Specify the project path (use '.' for the current folder or provide a folder path)."
    )
    return parser.parse_args()


def clean_data():
    data_dir = Path("data")

    if data_dir.exists() and data_dir.is_dir():
        shutil.rmtree(data_dir)

    data_dir.mkdir(parents=True, exist_ok=True)


def get_document(retries=3):
    print(f"\nCurrent working directory is: {os.getcwd()}")

    if retries == 0:
        return None

    location = input(f"Provide URL to git repo or an path to file:")

    if Path(location).is_file():
        clean_data()
        with open(location, "r") as file:
            # We will now copy this file into the data folder
            filepath = Path("data") / Path(location).name
            document = Document(file.read(), filepath)
            document.persist()

            return document
    elif is_valid_url(location):
        clean_data()
        # TODO: log errors
        repo: Repo = Repo.clone_from(location, "data")
        filepath = Path(repo.working_dir) / "README.md"
        with open(filepath, "r") as file:
            return Document(file.read(), filepath)
    else:
        print(f"Not a valid URL or local file path. {retries - 1} retries remaining.")
        return get_document(retries - 1)


def setup_project(project_path):
    if not os.path.exists(project_path):
        # Create the directory if it does not exist
        os.makedirs(project_path)
        print(f"Directory '{project_path}' created.")

    os.chdir(project_path)


def run_analyzer(document: Document):
    if document:
        report = create_document_report(document)
        Reporter(report).print_report()
    else:
        print("No document provided. Exiting...")



def start_cli(project_path: str):
    load_dotenv()
    # TODO: currently get_document implicitly depends on setup_project
    #  But we should have a project class that can persist document
    setup_project(project_path)
    document = get_document()
    run_analyzer(document)


def run():
    args = parse_arguments()
    config.initialize(args)
    start_cli(config.project_path)


if __name__ == "__main__":
    run()
