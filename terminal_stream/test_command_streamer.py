import time
import unittest

import pytest

from terminal_stream.command_streamer import CommandStreamer, TerminatedProcessError

@pytest.fixture(params=[
        ("ls dog", "ls: dog: No such file or directory\n"),
        ("cd dog", "/bin/bash: line 1: cd: dog: No such file or directory\n"),
        ("vim dog", "Vim: Warning: Output is not to a terminal\nVim: Warning: Input is not from a terminal\n"),
    ])
def error_commands(request):
    yield request.param

class TestCommandStreamer:
    @pytest.fixture(autouse=True)
    def streamer(self):
        self.streamer = CommandStreamer()

    def test_stream_nonblocking(self):
        self.streamer.send_command("echo Hello")

        output = self.streamer.read_nonblocking()

        assert output[0] == "Hello\n"  # newline is part of echo command

    def test_stream_nonblocking_sleeping_command(self):
        self.streamer.send_command("sleep 1 && echo Hello")

        output = self.streamer.read_nonblocking(1.5)

        assert output[0] == "Hello\n"

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

    def test_read_with_intput_response(self):
        self.streamer.send_command('read -p "Please enter your name: " user_name')
        self.streamer.send_command('dog')

        with pytest.raises(TimeoutError):
            self.streamer.read_nonblocking(0.1)

        self.streamer.send_command('echo $user_name')
        output_result = self.streamer.read_nonblocking(0.1)

        assert output_result[0] == 'dog\n'

    def test_read_std_err(self, error_commands):
        command, expect_output =error_commands
        self.streamer.send_command(command)

        output = self.streamer.read_nonblocking()

        assert output[1] == expect_output

