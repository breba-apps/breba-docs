import json
import os
import time

import docker
import pytest

from breba_docs.analyzer.service import execute_detach, execute_command
from breba_docs.socket_server.client import Client
from breba_docs.socket_server.listener import PORT


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
    output = execute_detach(command, container)
    # TODO: Needs to work without sleep anywhere in this code. Here We wait for listener to start up.
    #  Connect to server should wait for server to come up
    time.sleep(2)
    client = Client(("127.0.0.1", PORT))
    with client:
        command = {"command": 'pip uninstall pexpect'}
        client.send_message(json.dumps(command))
        # TODO: Need to avoid this sleep. Here we wait for reading the first command to finish. Otherwise it won't
        #  parse json correctly. Can be fixed if wait for a response before sending another command
        time.sleep(2)
        command = {"input": 'Y'}
        client.send_message(json.dumps(command))
        time.sleep(1)
        command = {"command": 'quit'}
        client.send_message(json.dumps(command))

    # TODO: get rid of this sleep. Here we are waiting because the listener.py never exists on quit command.
    #  It needs to throw an exception within the task in order to stop all tasks and quit. T
    #  hen we can use `for line in output`
    time.sleep(3)
    output_text = next(iter(output))
    output_text = output_text.decode("utf-8")
    assert "Server Closed" in output_text
