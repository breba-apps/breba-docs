import asyncio
import json
from asyncio import StreamReader, StreamWriter
from unittest.mock import MagicMock, patch

import pytest_asyncio

import pytest

import breba_docs
from breba_docs.socket_server.listener import start_server, stop_server


@pytest_asyncio.fixture
async def server_connection(request) -> (StreamReader, StreamWriter):
    with patch("breba_docs.socket_server.listener.command_end_marker", return_value=request.param[-1]):
        end_marker = breba_docs.socket_server.listener.command_end_marker()
        mock = MagicMock()
        mock.read_nonblocking.side_effect = ["Hello", end_marker]
        mock.sendline = MagicMock()
        mock.close = MagicMock()
        with patch("breba_docs.socket_server.listener.pexpect.spawn", return_value=mock):
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


command_outputs = ["Hello", "Completed test"]
@pytest.mark.asyncio
@pytest.mark.parametrize("server_connection, expected_outputs", [(command_outputs, command_outputs)], indirect=["server_connection"])
@pytest.mark.integration
async def test_echo_command(server, server_connection, expected_outputs):
    reader, writer = server_connection
    writer.write(json.dumps({"command": "echo Hello"}).encode())
    await writer.drain()

    data = b""
    while True:
        try:
            data += await asyncio.wait_for(reader.read(1024), 0.5)
        except asyncio.TimeoutError:
            break

    for output in expected_outputs:
        assert output in data.decode()
