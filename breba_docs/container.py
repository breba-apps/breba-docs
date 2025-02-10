import contextlib
import os
import threading
import time
from io import BytesIO
import tarfile
from pathlib import Path

import docker
from docker.models.containers import Container

from breba_docs import config


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


def container_setup(debug=False, dev=False) -> Container:
    debug = debug or config.debug_server

    client = docker.from_env()
    breba_image = os.environ.get("BREBA_IMAGE", "breba-image")
    print(f"Setting up the container with image: {breba_image}")
    kwargs = {}
    if dev:
        # We will run pty-server from the local .venv folder which needs to resolve to a local path with develop option
        # For example in pyproject.toml: pty-server = { path = "../pty-server", develop = true }
        local_venv = Path(os.getcwd()) / Path("../pty-server")
        kwargs['volumes'] = {
            local_venv: {'bind': '/usr/src/pty-server', 'mode': 'rw'},
        }
        kwargs['command'] = [
            "bash",
            "-c",
            """
            export VIRTUAL_ENV_DISABLE_PROMPT=1 && \
            source .venv/bin/activate && \
            pip install ./pty-server/
            pty-server
            """
        ]

    # TODO: make the port configurable
    port = 44440
    container = client.containers.run(
        breba_image,
        stdin_open=True,
        tty=True,
        detach=True,
        working_dir="/usr/src",
        ports={f'{port}/tcp': port},
        **kwargs
    )

    # Block until the container is running, or exited
    while container.status == 'created':
        time.sleep(0.1)
        container.reload()

    if container.status != 'running':
        print(f"Container status: {container.status}")
        print(container.logs().decode('utf-8'))
        raise Exception("Container failed to start")

    if debug:
        start_logs_thread(container)  # no need to join because it should just run to the end of the process
        time.sleep(0.5)

    return container


@contextlib.contextmanager
def new_container(**kwargs):
    execution_container = None
    try:
        execution_container = container_setup(**kwargs)
        yield execution_container
    finally:
        if execution_container:
            execution_container.stop()
            execution_container.remove()


def write_document_to_container(container: Container, document: str) -> None:
    # Create a tar archive in memory containing the document content
    tar_stream = BytesIO()
    tarinfo = tarfile.TarInfo(name="README.md")
    tarinfo.size = len(document.encode('utf-8'))

    # Create tarball in memory
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        tar.addfile(tarinfo, BytesIO(document.encode('utf-8')))

    tar_stream.seek(0)  # Rewind the stream to the beginning

    # Use put_archive to copy the tarball into the container's /usr/src directory
    container.put_archive(path="/usr/src", data=tar_stream)