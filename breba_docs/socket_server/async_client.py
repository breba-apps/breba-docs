import asyncio
import json
import time
from typing import Tuple

from breba_docs.socket_server.listener import PORT


class AsyncClient:
    def __init__(self, server_address: Tuple[str, int] = ("127.0.0.1", PORT)):
        self.server_address = server_address
        self.reader = None
        self.writer = None

    async def connect(self):
        """Establish a connection to the server."""
        try:
            self.reader, self.writer = await asyncio.open_connection(self.server_address[0], self.server_address[1])
        except Exception as e:
            print(f"Error during connection: {e}")
            self.writer = None

    async def disconnect(self):
        """Close the connection to the server."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            print("Disconnected from server")
            self.writer = None

    async def stream_response(self, timeout=2):
        """Read data from the server every 2 seconds until no more data is received."""
        while True:
            try:
                data = await asyncio.wait_for(self.reader.read(1024), timeout)
                if data:
                    yield data.decode()
                else:
                    break
            except asyncio.TimeoutError:
                break

    async def send_message(self, message):
        """Send a message to the server."""
        if self.writer:
            try:
                print(f"Sending: {message}")
                payload = message.encode()
                header = len(payload).to_bytes(4)
                print(f"Message with Header: {header + payload}")
                self.writer.write(header + payload)
                await self.writer.drain()

                return True
            except Exception as e:
                print(f"Error sending message: {e}")
                return False
        else:
            raise Exception("No connected to server. Cannot send message.")

    async def __aenter__(self):
        """Called when entering the 'with' block."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Called when exiting the 'with' block."""
        await self.disconnect()


async def main():
    address = ("127.0.0.1", PORT)

    async with AsyncClient(address) as server:
        command = {"command": 'pip install pexpect'}
        await server.send_message(json.dumps(command))
        time.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())