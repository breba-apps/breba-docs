import json
import socket
import time
from contextlib import contextmanager

from breba_docs.socket_server.listener import PORT


@contextmanager
def connect_to_server(server_address):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(server_address)
        yield client_socket  # This passes control to the block inside the 'with' statement
    except socket.error as e:
        print(f"Error during socket operation: {e}")
    finally:
        try:
            client_socket.close()
        except socket.error as e:
            print(f"Error closing socket: {e}")


def send_message_to_server(client_socket, message):
    try:
        print(f"Sending: {message}")
        client_socket.sendall(message.encode())
    except socket.error as e:
        print(f"Error sending message: {e}")


if __name__ == "__main__":
    address = ("127.0.0.1", PORT)
    with connect_to_server(address) as server:
        command = {"command": 'pip install nodestream'}
        send_message_to_server(server, json.dumps(command))
        time.sleep(2)
        # command = {"input": 'Y'}
        # send_message_to_server(server, json.dumps(command))
        # time.sleep(1)
        # command = {"command": 'quit'}
        # send_message_to_server(server, json.dumps(command))
