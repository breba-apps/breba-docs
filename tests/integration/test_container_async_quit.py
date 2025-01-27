import time

import pytest

from breba_docs.container import container_setup
from pty_server import AsyncPtyClient

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
@pytest.mark.asyncio
async def test_execute_quit_command(container):
    """ This test needs own module because it starts a new container in order to quit it. """
    async with AsyncPtyClient() as client:
        response = await client.send_command('pip install pexpect')
        response_text = await response.text(1)
        assert response.completed()

        response = await client.send_command('pip uninstall pexpect')
        response_text = await response.text(1)
        assert response.timedout()
        assert "Proceed (Y/n)" in response_text

        response = await client.send_command('quit')
        response_text = await response.text(0.5)
        assert response_text == "Server will shut down now."

