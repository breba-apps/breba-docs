import os
import threading
import time

import docker

from breba_docs.socket_server.listener import PORT


def get_container_logs(container):
    log_buffer = b""

    logs = container.logs(stream=True)
    for log in logs:
        # Append new log data to the buffer
        log_buffer += log

        try:
            # Try decoding the buffer
            decoded_log = log_buffer.decode('utf-8')
            print(decoded_log, end="")

            # If successful, clear the buffer
            log_buffer = b""

        except UnicodeDecodeError:
            # If decoding fails, accumulate more log data and retry
            pass


def start_logs_thread(container):
    # Create and start a thread to print logs
    logs_thread = threading.Thread(target=get_container_logs, args=(container,))
    logs_thread.start()
    return logs_thread


def container_setup(debug=False, dev=False):
    client = docker.from_env()
    breba_image = os.environ.get("BREBA_IMAGE", "breba-image")
    print(f"Setting up the container with image: {breba_image}")
    volumes = {}
    if dev:
        cwd = os.getcwd()
        volumes = {
            cwd: {'bind': '/usr/src/breba-docs', 'mode': 'rw'},
        }
    container = client.containers.run(
        breba_image,
        stdin_open=True,
        tty=True,
        detach=True,
        working_dir="/usr/src",
        ports={f'{PORT}/tcp': PORT},
        volumes=volumes
    )
    if debug:
        start_logs_thread(container)  # no need to join because it should just run to the end of the process
        time.sleep(0.5)

    return container
