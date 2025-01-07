import time
import unittest

import pytest

from terminal_stream.command_streamer import CommandStreamer, TerminatedProcessError


class TestCommandStreamer(unittest.TestCase):
    def setUp(self):
        self.streamer = CommandStreamer()

    def test_stream_nonblocking(self):
        self.streamer.send_command("echo Hello")

        output = self.streamer.read_nonblocking()

        assert output == "Hello\n"  # newline is part of echo command

    def test_stream_nonblocking_sleeping_command(self):
        self.streamer.send_command("sleep 1 && echo Hello")

        output = self.streamer.read_nonblocking(1.5)

        assert output == "Hello\n"

    def test_stream_nonblocking_sleeping_command_timeout(self):
        self.streamer.send_command("sleep 1 && echo Hello")

        with pytest.raises(TimeoutError):
            self.streamer.read_nonblocking(0.1)

    def test_read_with_process_closed(self):
        self.streamer.send_command("sleep 1 && echo Hello")
        self.streamer.process.kill()
        # wait for process to exit
        while self.streamer.process.poll() is None:
            time.sleep(0.1)

        with pytest.raises(TerminatedProcessError, match="Process is terminated with return code -9"):
            self.streamer.read_nonblocking(0.1)

