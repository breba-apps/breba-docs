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

    def stream_response(self, timeout=2):
        """Read data from the server every 2 seconds until no more data is received."""
        self.client_socket.settimeout(timeout)  # Set a timeout for the socket

        while True:
            data = self.client_socket.recv(16384)
            if data:
                yield data
            else:
                # If no data is received, break the loop.
                break

    def read_response(self, timeout=0.5, should_restart_callback=lambda x: False, max_retries=2):
        """Read data from the server with custom retry logic."""
        retries = 0
        data_received = []
        while True:
            try:
                for data in self.stream_response(timeout):
                    print(data.decode())
                    data_received.append(data.decode())
                    retries = 0  # Every time we have successful read, we want to reset retries

                return ''.join(data_received)
            except socket.timeout:
                # We hit a timeout, decide if we should retry
                retries += 1
                print(f"Socket Client: No new Data received in {timeout} seconds (attempt {retries}/{max_retries})")
                if should_restart_callback(data_received):
                    retries = 0
                if retries >= max_retries:
                    print("Max retries reached.")
                    return ''.join(data_received)
            except socket.error as e:
                print(f"Socket Client: Error reading from socket: {e}")
                return ''.join(data_received)

    def send_message(self, message):
        """Send a message to the server."""
        if self.client_socket:
            try:
                print(f"Sending: {message}")
                self.client_socket.sendall(message.encode())
                return True
            except socket.error as e:
                print(f"Error sending message: {e}")
                return False
        else:
            print("No connection to server. Cannot send message.")
            raise Exception("No connection to server. Cannot send message.")

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
