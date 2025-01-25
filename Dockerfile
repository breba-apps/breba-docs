# Use the Python 3 base image
FROM python:3

# Set the working directory in the container
WORKDIR /usr/src

# Install pty-server
RUN python -m venv .venv \
    && . .venv/bin/activate \
    && pip install pty-server

CMD ["/bin/bash", "-c", "VIRTUAL_ENV_DISABLE_PROMPT=1 . .venv/bin/activate && pty-server"]
