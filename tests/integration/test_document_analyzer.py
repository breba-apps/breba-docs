from pathlib import Path

import pytest

from breba_docs.analyzer.document_analyzer import DocumentAnalyzer
from breba_docs.container import container_setup
from breba_docs.services.document import Document

from dotenv import load_dotenv


@pytest.fixture
def container():
    # To Run the container from terminal from breba_docs package dir
    # docker run -d -it \
    #   -v $(pwd)/breba_docs/socket_server:/usr/src/socket_server \
    #   -w /usr/src \
    #   -p 44440:44440 \
    #   python:3 \
    #   /bin/bash
    started_container = container_setup(dev=True)

    yield started_container
    started_container.stop()
    started_container.remove()


@pytest.fixture(autouse=True)
def load_env():
    load_dotenv()


@pytest.mark.integration
def test_document_basic(mocker, container):
    location = Path("tests/integration/fixtures/typo_doc.md")
    with open(location, "r") as file:
        # We will now copy this file into the data folder
        data_folder_path = Path("tests/integration/data")
        filepath = data_folder_path / Path(location).name
        document = Document(file.read(), filepath)
        document.persist()

    analyzer = DocumentAnalyzer()
    report = analyzer.analyze(document)
    assert report.file == "Some Document"

    getting_started_goal = next(
        (goal_report for goal_report in report.goal_reports if goal_report.goal_name == "getting started"), None)
    assert getting_started_goal, f"Could not find the getting started goal in the report. Report: {report}"

    goal_with_typo = None
    for goal_report in report.goal_reports:
        for command_report in goal_report.command_reports:
            # check that the typo is preserved
            if command_report.command == "nodestream run simple -v":
                goal_with_typo = goal_report
                # since this is a typo doc, the last command will fail because of a typo
                assert command_report.success is False
                break

    # First check the typo is found in a command
    assert goal_with_typo, f"Should have found a goal with typo in command: {report}"

    # Then check that the expected number of commands is found. (this includes setup and execute commands)
    assert len(goal_with_typo.command_reports) == 3

    # Makes sure that the typo command is the last one
    assert goal_with_typo.command_reports[2].command == "nodestream run simple -v", (
        f"'nodestream run simple -v' is not found in the expected order. Report: {report}")
