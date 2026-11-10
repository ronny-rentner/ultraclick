"""Tests for running child commands in a pseudo-terminal or in plain text mode."""

import io
import os
import sys
import unittest
from unittest import mock

import ultraclick


@unittest.skipIf(os.name == 'nt', 'pseudo-terminals are Unix-only')
class TestRunCommandPty(unittest.TestCase):

    # The child reports whether its stdout is a terminal and which TERM it sees.
    COMMAND = [sys.executable, '-c', "import os; print(os.isatty(1), os.environ.get('TERM'))"]

    def setUp(self):
        # Register cleanup explicitly so these tests also run on Python 3.9 and 3.10.
        for patch in (mock.patch.object(sys, 'stdout', io.StringIO()), mock.patch.object(sys, 'stderr', io.StringIO())):
            patch.start()
            self.addCleanup(patch.stop)

    def run_command(self, plain=False, **kwargs):
        with mock.patch.object(ultraclick, 'PLAIN_TEXT_MODE', plain):
            formatter = ultraclick.PlainOutputFormatter() if plain else ultraclick.OutputFormatter()
            return formatter.run_command(self.COMMAND, **kwargs).stdout.split()

    def test_streamed_output_runs_in_a_terminal(self):
        self.assertEqual(self.run_command()[0], 'True')

    def test_silent_and_suppressed_output_is_captured_in_plain_text_mode(self):
        for kwargs in ({'silent': True}, {'suppress': True}):
            with self.subTest(kwargs=kwargs):
                self.assertEqual(self.run_command(**kwargs), ['False', 'dumb'])

    def test_force_pty_keeps_the_terminal_for_silent_and_suppressed_output(self):
        for kwargs in ({'silent': True}, {'suppress': True}):
            with self.subTest(kwargs=kwargs):
                self.assertEqual(self.run_command(force_pty=True, **kwargs)[0], 'True')

    def test_force_pty_does_not_override_plain_text_mode(self):
        self.assertEqual(self.run_command(plain=True, force_pty=True), ['False', 'dumb'])


if __name__ == '__main__':
    unittest.main()
