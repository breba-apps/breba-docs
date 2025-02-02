import json

import pytest

from breba_docs.container import container_setup

from pty_server import AsyncPtyClient
from pty_server.async_client import STATUS_TIMEOUT, STATUS_COMPLETED, PtyServerResponse


@pytest.fixture(scope="module")
def container():
    # To Run the container from terminal from breba_docs package dir
    # docker run -d -it \
    #   -v $(pwd)../pty-server:/usr/src/pty-server \
    #   -w /usr/src \
    #   -p 44440:44440 \
    #   python:3 \
    #   /bin/bash
    started_container = container_setup(dev=True)
    yield started_container
    started_container.stop()
    started_container.remove()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_command(container):
    async with AsyncPtyClient() as client:
        response_install = await client.send_command('pip install pexpect')
        response_text = await response_install.text(2)
        
        assert response_install.status == STATUS_COMPLETED
        assert "Successfully installed pexpect" in response_text

        response_uninstall = await client.send_command('pip uninstall pexpect')
        response_text = await response_uninstall.text(2)
        assert response_uninstall.status == STATUS_TIMEOUT
        assert "Proceed (Y/n)" in response_text

        command = {"input": 'Y'}
        await client.send_message(json.dumps(command))
        response_text = await response_uninstall.text(2)
        assert response_uninstall.status == STATUS_COMPLETED
        assert "Successfully uninstalled" in response_text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_ampersand_command(container):
    async with AsyncPtyClient() as client:
        command = 'mkdir test && cd test && pwd && echo "more testing is needed"'
        response = await client.send_command(command)
        response_text = await response.text(0.01)
    assert "/usr/src/test" in response_text
    assert "No such file or directory" not in response_text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_connections(container):
    async with AsyncPtyClient() as client:
        command = 'mkdir test2 && cd test2 && pwd && echo "more testing is needed"'
        response = await client.send_command(command)
        response_text = await response.text(0.01)

    assert "/usr/src/test" in response_text
    assert "No such file or directory" not in response_text

    async with AsyncPtyClient() as client:
        command = 'mkdir test3 && cd test3 && pwd && echo "more testing is needed"'
        response = await client.send_command(command)
        response_text = await response.text(0.01)
    assert "/usr/src/test3" in response_text
    assert "No such file or directory" not in response_text
