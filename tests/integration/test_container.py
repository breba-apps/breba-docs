import json
import os
import time
import shlex

import docker
import pytest

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
    client = docker.from_env()
    cwd = os.getcwd()

    listener_dir = os.path.join(cwd, "breba_docs", "socket_server")

    # To Run the container from terminal from breba_docs package dir
    # docker run -d -it \
    #   -v $(pwd)/breba_docs/socket_server:/usr/src/socket_server \
    #   -w /usr/src \
    #   -p 44440:44440 \
    #   python:3 \
    #   /bin/bash
    started_container = client.containers.run(
        "python:3",
        command="/bin/bash",
        volumes={
            listener_dir: {'bind': '/usr/src/socket_server', 'mode': 'rw'}
        },
        stdin_open=True,
        tty=True,
        detach=True,
        working_dir="/usr/src",
        ports={f'{PORT}/tcp': PORT},
    )

    yield started_container
    started_container.stop()
    started_container.remove()


@pytest.mark.integration
def test_execute_command(container):
    execute_command("pip install pexpect", container)
    command = 'python socket_server/listener.py'
    execute_detach(command, container)
    # TODO: Needs to work without sleep anywhere in this code. Here We wait for listener to start up.
    #  Connect to server should wait for server to come up
    time.sleep(2)
    client = Client(("127.0.0.1", PORT))
    response = ""
    with client:
        command = {"command": 'pip uninstall pexpect'}
        response = client.send_message(json.dumps(command))
        command = {"input": 'Y'}
        response = ''.join([response, client.send_message(json.dumps(command))])
        command = {"command": 'quit'}
        response = ''.join([response, client.send_message(json.dumps(command))])
    assert "Server Closed" in response
    assert "Proceed (Y/n)" in response
    assert "Successfully uninstalled" in response
