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
        if self.process.poll() is not None:
            raise TerminatedProcessError(f"Process is terminated with return code {self.process.returncode}")
        stdout, _, _ = select([self.process.stdout], [], [], timeout)
        while stdout:
            output = self.process.stdout.peek()
            yield output.decode()
            self.process.stdout.read(len(output))
            stdout, _, _ = select([self.process.stdout], [], [], timeout)
        raise TimeoutError(f"No data read before reaching timout of {timeout}s")



    def close(self):
        self.process.stdin.close()
        self.process.stdout.close()
        self.process.stderr.close()
        self.process.wait(1)
        self.process.terminate()