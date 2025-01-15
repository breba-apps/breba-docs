import time

import pytest

from breba_docs.container import container_setup
from breba_docs.socket_server.client import Client
from breba_docs.socket_server.listener import PORT


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
    time.sleep(2)
    yield started_container
    started_container.stop()
    started_container.remove()


@pytest.mark.integration
def test_execute_quit_command(container):
    """ This test needs own module because it starts a new container in order to quit it. """
    with Client(("127.0.0.1", PORT)) as  client:
        response_fn = client.send_command('pip uninstall pexpect')
        response = response_fn(0.5)
        response = ''.join([response, response_fn(0.5)])
        quit_response_fn = client.send_command('quit')
        response = ''.join([response, quit_response_fn(0.5)])

    assert "Proceed (Y/n)" in response
    assert "Quit command received" in response
