import json
import socket
import time
import uuid
from typing import Tuple, Callable

from breba_docs.socket_server.listener import PORT

class EndOfStream(Exception):
    pass

class SocketClosedError(Exception):
    pass

class Client:
    def __init__(self, server_address: Tuple[str, int] = ("127.0.0.1", PORT)):
        self.server_address = server_address
        self.client_socket = None

    def connect(self):
        """Establish a connection to the server."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect(self.server_address)
            print(f"Connected to server at {self.server_address}")
        except socket.error as e:
            print(f"Error during connection: {e}")
            self.client_socket = None

    def disconnect(self):
        """Close the connection to the server."""
        if self.client_socket:
            try:
                self.client_socket.close()
                print("Disconnected from server")
            except socket.error as e:
                print(f"Error closing socket: {e}")
            self.client_socket = None

    def accumulate_response(self, message_id):
        # This is trying to tie message_id to
        def stream_functional(timeout):
            self.client_socket.settimeout(timeout)  # Set a timeout for the socket
            try:
                while True:
                    data = self.client_socket.recv(16384).decode()
                    if f"Completed {message_id}" in data:
                        yield data.replace(f"Completed {message_id}", "")  # Remove the command end marker and keep the rest of the data
                        break
                    if data:
                        yield data
                    else:
                        raise SocketClosedError("Streaming ended due to no data received, likely socket is closed")
            except socket.timeout as e:
                raise EndOfStream("Streaming ended due to socket timeout") from e

        def accumulate_output(timeout=2.0):
            data = ""
            try:
                for chunk in stream_functional(timeout):
                    data += chunk
            except (EndOfStream, SocketClosedError):
                print("End of stream reached. Will return accumulated data.")
            return data

        return accumulate_output

    def stream_response(self, timeout=2):
        """Read data from the server every 2 seconds until no more data is received."""
        self.client_socket.settimeout(timeout)  # Set a timeout for the socket
        try:
            while True:
                data = self.client_socket.recv(16384)
                if data:
                    yield data.decode()
                else:
                    # If no data is received, break the loop.
                    break
        except socket.timeout:
            return ""

    def send_message(self, message):
        """Send a message to the server."""
        if self.client_socket:
            try:
                print(f"Sending: {message}")
                payload = message.encode()
                header = len(payload).to_bytes(4)
                print(f"Message with Header: {header + payload}")
                self.client_socket.sendall(header + payload)
                return True
            except socket.error as e:
                print(f"Error sending message: {e}")
                return False
        else:
            print("No connection to server. Cannot send message.")
            raise Exception("No connection to server. Cannot send message.")

    def send_command(self, command: str) -> Callable[[float], str | None] | None:
        command_id = str(uuid.uuid4())
        command_directive = {"command": command, "command_id": command_id}
        if self.send_message(json.dumps(command_directive)):
            return self.accumulate_response(command_id)
        else:
            return None

    def __enter__(self):
        """Called when entering the 'with' block."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Called when exiting the 'with' block."""
        self.disconnect()


if __name__ == "__main__":
    address = ("127.0.0.1", PORT)

    with Client(address) as server:
        command = {"command": 'pip install pexpect'}
        server.send_message(json.dumps(command))
        time.sleep(2)
