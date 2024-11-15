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
    assert len(report.goal_reports) == 2
    # since this is a typo doc, the last command will fail because of a typo
    assert report.goal_reports[0].command_reports[2].command == "nodestream run simple -v"
    assert report.goal_reports[0].command_reports[2].success is False
