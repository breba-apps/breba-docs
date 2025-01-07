import subprocess
import time
from select import select

class TerminatedProcessError(Exception):
    pass

class CommandStreamer:
    def __init__(self):
        self.process = subprocess.Popen('/bin/bash', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def send_command(self, command):
        command = f"{command}\n"
        self.process.stdin.write(command.encode())
        self.process.stdin.flush()

    def get_readable_fd(self, timeout):
        """
        This will return the first readable file descriptor
        :param timeout: how long to wait for a file descriptor to become readable
        :return: the first readable file descriptor
        """
        readable, _, _ = select([self.process.stdout, self.process.stderr], [], [], timeout)
        if not readable:
            raise TimeoutError(f"No data read before reaching timout of {timeout}s")
        return readable[0]

    def read_nonblocking(self, timeout=0.1):
        """
        Reads from stdout.

        :param timeout:
        :return: string output from the process stdout
        :raise TimeoutError: if no data is read before timeout
        """
        return next(self.stream_nonblocking(timeout))

    def stream_nonblocking(self, timeout=0.1):
        # TODO: what happens if there is an error
        # TODO: test for process ending inside the while loop
        if self.process.poll() is not None:
            raise TerminatedProcessError(f"Process is terminated with return code {self.process.returncode}")
        readable = self.get_readable_fd(timeout)

        while readable:
            output = readable.peek()
            yield output.decode()
            readable.read(len(output))
            readable = self.get_readable_fd(timeout)


    def close(self):
        self.process.stdin.close()
        self.process.stdout.close()
        self.process.stderr.close()
        self.process.wait(1)
        self.process.terminate()