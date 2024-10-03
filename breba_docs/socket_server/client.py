import json
import socket
import time
from typing import Tuple

from breba_docs.socket_server.listener import PORT


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

    def read_response(self):
        """Read data from the server every 3 seconds until no more data is received."""
        data_received = []
        # Timeout will be hit when the command finished and is no longer sending messages.
        # Since the server is sending a Completion message, we could finish reading on that.
        self.client_socket.settimeout(2)  # Set a timeout for the socket

        try:
            while True:
                data = self.client_socket.recv(16384)
                if data:
                    # decode breaks when partial utf-8 char is received.
                    # this happens because utf-8 can be uneven number of bytes.
                    # right now the is handled by receiving all the bytes (big chunk)
                    # TODO: need to receive additional bytes if decode fails
                    data_received.append(data.decode())
                    # TODO: need handler
                    print(f"{data.decode()}")
                else:
                    break
        except socket.timeout:
            print("No more data received (socket timeout).")
        except socket.error as e:
            print(f"Error reading from socket: {e}")

        return ''.join(data_received)

    def send_message(self, message):
        """Send a message to the server."""
        if self.client_socket:
            try:
                print(f"Sending: {message}")
                self.client_socket.sendall(message.encode())
                return self.read_response()
            except socket.error as e:
                print(f"Error sending message: {e}")
        else:
            print("No connection to server. Cannot send message.")

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
