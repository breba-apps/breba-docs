# Use the Python 3 base image
FROM python:3

# Set the working directory in the container
WORKDIR /usr/src

# Install pexpect and clone the repository
RUN pip install pexpect \
    && git clone https://github.com/breba-apps/breba-docs.git

# Run the listener script in detached mode
CMD ["python", "breba-docs/breba_docs/socket_server/listener.py"]