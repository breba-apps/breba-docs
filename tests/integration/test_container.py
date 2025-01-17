import json
import time

import pytest

from breba_docs.container import container_setup
from breba_docs.socket_server.client import Client
from breba_docs.socket_server.listener import PORT


@pytest.fixture(scope="module")
def container():
    # To Run the container from terminal from breba_docs package dir
    # docker run -d -it \
    #   -v $(pwd)/breba_docs/socket_server:/usr/src/socket_server \
    #   -w /usr/src \
    #   -p 44440:44440 \
    #   python:3 \
    #   /bin/bash
    started_container = container_setup(dev=True)
    time.sleep(2)
    yield started_container
    started_container.stop()
    started_container.remove()


@pytest.mark.integration
def test_execute_command(container):
    with Client(("127.0.0.1", PORT)) as  client:
        response_install_fn = client.send_command('pip install pexpect')
        response_install = response_install_fn(0.2)
        response_install = client.send_command('pip uninstall pexpect')
        response = response_install(0.2)
        command = {"input": 'Y'}
        client.send_message(json.dumps(command))
        response = ''.join([response, response_install(2)])  # This will exit as soon as command completes

    assert "Proceed (Y/n)" in response
    assert "Successfully uninstalled" in response


@pytest.mark.integration
def test_execute_ampersand_command(container):
    with Client(("127.0.0.1", PORT)) as client:
        command = 'mkdir test && cd test && pwd && echo "more testing is needed"'
        response_accumulator = client.send_command(command)
        response = response_accumulator(0.01)
    assert "/usr/src/test" in response
    assert "No such file or directory" not in response


@pytest.mark.integration
def test_multiple_connections(container):
    with Client(("127.0.0.1", PORT)) as client:
        command = 'mkdir test2 && cd test2 && pwd && echo "more testing is needed"'
        response_accumulator = client.send_command(command)
        response = response_accumulator(0.01)

    assert "/usr/src/test" in response
    assert "No such file or directory" not in response

    with Client(("127.0.0.1", PORT)) as client:
        command = 'mkdir test3 && cd test3 && pwd && echo "more testing is needed"'
        response_accumulator = client.send_command(command)
        response = response_accumulator(0.01)
    assert "/usr/src/test3" in response
    assert "No such file or directory" not in response
