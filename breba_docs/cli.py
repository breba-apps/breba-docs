import argparse
import os
import threading
import time
from pathlib import Path

import docker
import requests

from breba_docs.analyzer.service import analyze
from breba_docs.services.openai_agent import OpenAIAgent
from dotenv import load_dotenv
from urllib.parse import urlparse

from breba_docs.socket_server.listener import PORT

DEFAULT_LOCATION = ("https://gist.githubusercontent.com/yasonk/16990780a6b6e46163d1caf743f38e8f/raw"
                    "/6d5fbb7e7053642f45cb449ace1adb4eea38e6de/gistfile1.txt")


def is_valid_url(url):
    # TODO: check if md file
    parsed_url = urlparse(url)

    return all([parsed_url.scheme, parsed_url.netloc])


def is_file_path(file_path):
    path = Path(file_path)
    return path.is_file()


def container_setup():
    client = docker.from_env()
    breba_image = os.environ.get("BREBA_IMAGE", "breba-image")
    print(f"Setting up the container with image: {breba_image}")
    container = client.containers.run(
        breba_image,
        stdin_open=True,
        tty=True,
        detach=True,
        working_dir="/usr/src",
        ports={f'{PORT}/tcp': PORT},
    )
    return container


def get_container_logs(container):
    # Get the logs from the container one time
    logs = container.logs(stream=True)
    for log in logs:
        print(log.decode('utf-8'), end="")


def start_logs_thread(container):
    # Create and start a thread to print logs
    logs_thread = threading.Thread(target=get_container_logs, args=(container,))
    logs_thread.start()
    return logs_thread


def parse_arguments():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Breba CLI")
    parser.add_argument("--debug-server", action="store_true", help="Enable logging from the server.")
    return parser.parse_args()


def run(debug_server=False):
    load_dotenv()
    # TODO: Start container only when special argument is provided
    started_container = container_setup()

    if debug_server:
        start_logs_thread(started_container)  # no need to join because it should just run to the end of the process
        time.sleep(0.5)

    try:
        cwd = os.getcwd()
        print(f"Current working directory is: {cwd}")
        doc_location = input("Provide url to doc file or an absolute path:") or DEFAULT_LOCATION

        errors = []
        # TODO: allow several retries to specify a file
        if is_file_path(doc_location):
            with open(doc_location, "r") as file:
                document = file.read()
        elif is_valid_url(doc_location):
            response = requests.get(doc_location)
            # TODO: if response is not md file produce error message
            document = response.text
        else:
            document = None
            errors.append("Not a valid url or local file path")

        if errors:
            for error in errors:
                print(error)
        elif document:
            ai_agent = OpenAIAgent()
            analyze(ai_agent, document)
        else:
            print("Document text is empty, but no errors were found")
    finally:
        started_container.stop()
        started_container.remove()


if __name__ == "__main__":
    args = parse_arguments()
    run(args.debug_server)
