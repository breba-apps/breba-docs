import asyncio
import json
from asyncio import StreamReader, StreamWriter
from unittest.mock import MagicMock, patch

import pytest_asyncio

import pytest

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


@pytest.mark.asyncio
@pytest.mark.integration
async def test_echo_command(server, real_server_connection):
    reader, writer = real_server_connection
    payload = json.dumps({"command": "echo Hello", "command_id": "test"}).encode()
    header = len(payload).to_bytes(4)
    writer.write(header + payload)
    await writer.drain()

    data = b""
    while True:
        try:
            data += await asyncio.wait_for(reader.read(1024), 0.5)
            if not data:
                break
        except asyncio.TimeoutError:
            break

    assert data == b'$ echo Hello\nHello\nCompleted test\n'

@pytest.mark.asyncio
@pytest.mark.integration
async def test_echo_variable(server, real_server_connection):
    reader, writer = real_server_connection

    payload = json.dumps({"command": "export MY=Hello", "command_id": "test1"}).encode()
    header = len(payload).to_bytes(4)
    writer.write(header + payload)
    await writer.drain()

    payload = json.dumps({"command": "echo $MY", "command_id": "test2"}).encode()
    header = len(payload).to_bytes(4)
    writer.write(header + payload)
    await writer.drain()

    data = b""
    while True:
        try:
            data += await asyncio.wait_for(reader.read(1024), 0.5)
            if not data:
                break
        except asyncio.TimeoutError:
            break

    # We collected all the output from the two commands
    assert data.decode() == '$ export MY=Hello\nCompleted test1\n$ echo $MY\nHello\nCompleted test2\n'