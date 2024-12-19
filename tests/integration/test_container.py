import json
import socket
import time
import shlex

import pytest

from breba_docs.container import container_setup
from breba_docs.socket_server.client import Client
from breba_docs.socket_server.listener import PORT


def execute_detach(command, container):
    # this command will be able to run any command regardless of quote use
    docker_command = f"/bin/bash -c {shlex.quote(command.strip())}"

    exit_code, output = container.exec_run(
        docker_command,
        stdout=True,
        stderr=True,
        tty=True,
        stream=True,
    )

    return output


def execute_command(command, container):
    # this command will be able to run any command regardless of quote use
    docker_command = f"/bin/bash -c {shlex.quote(command.strip())}"

    exit_code, output = container.exec_run(
        docker_command,
        stdout=True,
        stderr=True,
        tty=True,
        stream=True,
    )

    output_text = ""

    for line in output:
        line_text = line.decode("utf-8")
        print(line_text.strip())
        output_text += line_text

    return output_text


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

def collect_response(client):
    data = []
    try:
        for response in client.stream_response(timeout=0.5):
            data += [response]
    finally:
        return ''.join(data)


@pytest.mark.integration
def test_execute_command(container):
    # TODO: Needs to work without sleep anywhere in this code. Here We wait for listener to start up.
    #  Connect to server should wait for server to come up
    time.sleep(2)
    with Client(("127.0.0.1", PORT)) as  client:
        command = {"command": 'pip uninstall pexpect', "command_id": "uninstall123"}
        client.send_message(json.dumps(command))
        response = collect_response(client)
        command = {"input": 'Y'}
        client.send_message(json.dumps(command))
        response = ''.join([response, collect_response(client)])
        command = {"command": 'quit'}
        client.send_message(json.dumps(command))
        response = ''.join([response, collect_response(client)])
    assert "Quit command received" in response
    assert "Proceed (Y/n)" in response
    assert "Successfully uninstalled" in response


@pytest.mark.integration
def test_execute_ampersand_command(container):
    # TODO: Needs to work without sleep anywhere in this code. Here We wait for listener to start up.
    #  Connect to server should wait for server to come up
    time.sleep(2)
    with Client(("127.0.0.1", PORT)) as client:
        command = {"command": 'mkdir test && cd test && pwd && echo "more testing is needed"'}
        client.send_message(json.dumps(command))
        response = collect_response(client)
    assert "/usr/src/test" in response
    assert "No such file or directory" not in response


@pytest.mark.integration
def test_multiple_connections(container):
    time.sleep(2)
    with Client(("127.0.0.1", PORT)) as client:
        command = {"command": 'mkdir test && cd test && pwd && echo "more testing is needed"'}
        client.send_message(json.dumps(command))
        response = collect_response(client)

    assert "/usr/src/test" in response
    assert "No such file or directory" not in response

    with Client(("127.0.0.1", PORT)) as client:
        command = {"command": 'mkdir test2 && cd test2 && pwd && echo "more testing is needed"'}
        client.send_message(json.dumps(command))
        response = collect_response(client)
    assert "/usr/src/test2" in response
    assert "No such file or directory" not in response
