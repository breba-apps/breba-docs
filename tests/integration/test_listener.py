import asyncio
import json
from asyncio import StreamReader, StreamWriter
from unittest.mock import MagicMock

import pytest_asyncio

import pytest

from breba_docs.socket_server.async_client import AsyncClient
from breba_docs.socket_server.client2 import Client2
from breba_docs.socket_server.listener import start_server, stop_server


@pytest_asyncio.fixture
async def real_server_connection(mocker) -> (MagicMock, StreamReader, StreamWriter):
    reader, writer = await asyncio.open_connection("127.0.0.1", 44440)
    try:
        yield reader, writer
    finally:
        writer.close()
        await writer.wait_closed()


@pytest_asyncio.fixture
async def server():
    async_server = asyncio.create_task(start_server())
    await asyncio.sleep(1)
    yield
    await stop_server()
    async_server.cancel()


@pytest.fixture
def client():
    with Client2() as client:
        yield client

@pytest_asyncio.fixture
async def aclient():
    async with AsyncClient() as aclient:
        yield aclient

@pytest.mark.asyncio
@pytest.mark.integration
async def test_echo_command(server, client):
    payload = json.dumps({"command": "echo Hello", "command_id": "test"})
    client.send_message(payload)
    await asyncio.sleep(0.1)  # server is running in parallel so we need to wait for it

    data = ""
    for chunk in client.stream_response(timeout=0.1):
        data += chunk
        await asyncio.sleep(0.1)  # server is running in parallel, it will not produce new output without async sleep

    assert data == '$ echo Hello\nHello\nCompleted test\n'

@pytest.mark.asyncio
@pytest.mark.integration
async def test_async_echo_command(server, aclient):
    payload = json.dumps({"command": "echo Hello", "command_id": "test"})
    await aclient.send_message(payload)

    data = ""
    async for chunk in aclient.stream_response(timeout=0.1):
        data += chunk

    assert data == '$ echo Hello\nHello\nCompleted test\n'

@pytest.mark.asyncio
@pytest.mark.integration
async def test_echo_variable(server, client):
    payload = json.dumps({"command": "export MY=Hello", "command_id": "test1"})
    client.send_message(payload)

    payload = json.dumps({"command": "echo $MY", "command_id": "test2"})
    client.send_message(payload)

    await asyncio.sleep(0.1)  # server is running in parallel so we need to wait for it

    data = ""
    for chunk in client.stream_response(timeout=0.1):
        data += chunk
        await asyncio.sleep(0.1)

    # We collected all the output from the two commands
    assert data == '$ export MY=Hello\nCompleted test1\n$ echo $MY\nHello\nCompleted test2\n'

@pytest.mark.asyncio
@pytest.mark.integration
async def test_async_echo_variable(server, aclient):
    payload = json.dumps({"command": "export MY=Hello", "command_id": "test1"})
    await aclient.send_message(payload)

    payload = json.dumps({"command": "echo $MY", "command_id": "test2"})
    await aclient.send_message(payload)

    data = ""
    async for chunk in aclient.stream_response(timeout=0.1):
        data += chunk
        # await asyncio.sleep(0.1) # server is running in parallel so we need to wait for it

    # We collected all the output from the two commands
    assert data == '$ export MY=Hello\nCompleted test1\n$ echo $MY\nHello\nCompleted test2\n'