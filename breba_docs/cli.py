import argparse
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from urllib.parse import urlparse

from git import Repo

from breba_docs.analyzer.document_analyzer import DocumentAnalyzer
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


def run(debug_server=False):
    started_container = None
    load_dotenv()

    try:
        document = get_document()

        if document:
            # TODO: Start container only when special argument is provided
            started_container = container_setup(debug=debug_server)

            analyzer = DocumentAnalyzer()
            analyzer.analyze(document.content)
        else:
            print("No document provided. Exiting...")
    finally:
        if started_container:
            started_container.stop()
            started_container.remove()


if __name__ == "__main__":
    args = parse_arguments()
    run(args.debug_server)
