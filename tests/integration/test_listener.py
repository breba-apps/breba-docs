import asyncio
import json
import re
from asyncio import StreamReader, StreamWriter
from unittest.mock import MagicMock

import pytest_asyncio

import pytest

from breba_docs.socket_server.async_client import AsyncClient
from breba_docs.socket_server.client import Client, EndOfStream
from breba_docs.socket_server.listener import start_server, stop_server


@pytest_asyncio.fixture
async def server():
    async_server = asyncio.create_task(start_server())
    await asyncio.sleep(1)
    yield
    await stop_server()
    async_server.cancel()


@pytest_asyncio.fixture
async def client():
    with Client() as client:
        await asyncio.sleep(0.1)  # server is running in parallel, it will not produce new output without async sleep
        response_fn = client.send_command('clear')
        await asyncio.sleep(0.1)  # server is running in parallel, it will not produce new output without async sleep
        flushed = response_fn(0.1)
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
    await asyncio.sleep(0.5)  # server is running in parallel so we need to wait for it

    data = ""
    for chunk in client.stream_response(timeout=0.1):
        data += chunk
        await asyncio.sleep(0.1)  # server is running in parallel, it will not produce new output without async sleep

    assert "$ echo Hello\r\n" in data
    assert "Hello\r\n" in data
    assert "Completed test\r\n" in data

@pytest.mark.asyncio
@pytest.mark.integration
async def test_async_echo_command(server, aclient):
    payload = json.dumps({"command": "echo Hello", "command_id": "test"})
    await aclient.send_message(payload)

    data = ""
    async for chunk in aclient.stream_response(timeout=0.1):
        data += chunk

    assert "$ echo Hello\r\n" in data
    assert "Hello\r\n" in data
    assert "Completed test\r\n" in data

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
    assert "$ export MY=Hello\r\n" in data
    assert "Completed test1\r\n" in data
    assert "$ echo $MY\r\n" in data
    assert "Hello\r\n" in data
    assert "Completed test2\r\n" in data

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

    # We collected all the output from the two commands
    assert "$ export MY=Hello\r\n" in data
    assert "Completed test1\r\n" in data
    assert "$ echo $MY\r\n" in data
    assert "Hello\r\n" in data
    assert "Completed test2\r\n" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_command_with_variable(server, client):
    client.send_command("export MY=Hello")
    response_accumulator = client.send_command("echo $MY")

    await asyncio.sleep(0.1)  # server is running in parallel so we need to wait for it

    data = response_accumulator(0.1)
    # We collected all the output from the two commands
    assert "$ export MY=Hello\r\n" in data
    assert "$ echo $MY\r\n" in data
    assert "Hello\r\n" in data
    assert re.search(r"Completed.*\r\n", data, flags=re.MULTILINE)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_send_command_with_timeout_handler(server, client):
    def timeout_handler(error):
        assert isinstance(error, TimeoutError)
        raise EndOfStream("timeout")  # raise error otherwise we get infinite loop

    response_accumulator = client.send_command("read -p 'Press enter to continue'")
    await asyncio.sleep(0.1)  # server is running in parallel so we need to wait for it

    data = response_accumulator(0.01, timeout_handler)
    # We collected all the output from the two commands
    assert "$ read -p 'Press enter to continue'\r\n" in data