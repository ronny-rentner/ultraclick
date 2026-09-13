"""Tests for live, combined subprocess output in plain mode."""

import io
import os
import select
import subprocess
import sys
import unittest
from unittest import mock

import ultraclick


class TestRunCommandPlain(unittest.TestCase):

    def setUp(self):
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        # Register cleanup explicitly so these tests also run on Python 3.9 and 3.10.
        for patch in (mock.patch.object(ultraclick, 'PLAIN_TEXT_MODE', True),
                      mock.patch.object(sys, 'stdout', self.stdout), mock.patch.object(sys, 'stderr', self.stderr)):
            patch.start()
            self.addCleanup(patch.stop)
        self.formatter = ultraclick.PlainOutputFormatter()

    @unittest.skipIf(os.name == 'nt', 'select on subprocess pipes is Unix-only')
    def test_streams_partial_lines_before_child_exits(self):
        # Each acknowledgement releases the next child write. Buffered capture or
        # newline-based forwarding cannot deliver the first prompt before timeout.
        child = "import os, sys; os.write(1, b'ready'); input(); os.write(2, b'warning'); input()"
        wrapper = (
            "import sys, ultraclick; "
            f"result = ultraclick.output.run_command([sys.executable, '-c', {child!r}]); "
            "assert result.stdout == 'readywarning'; assert result.stderr == ''; "
            "assert result.returncode == 0"
        )
        env = dict(os.environ, TERM='dumb', ULTRACLICK_COLORS='0')
        with subprocess.Popen([sys.executable, '-c', wrapper], stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env) as process:
            try:
                for expected in (b'ready', b'warning'):
                    self.assertTrue(select.select([process.stdout], [], [], 5)[0], 'Output withheld before exit')
                    self.assertEqual(os.read(process.stdout.fileno(), len(expected)), expected)
                    self.assertIsNone(process.poll())
                    process.stdin.write(b'\n')
                    process.stdin.flush()
                stdout, stderr = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 0, stderr)
                self.assertEqual(stdout, b'')
            finally:
                # Closing stdin releases a waiting child even when an assertion fails.
                if process.poll() is None:
                    process.communicate(timeout=5)

    def test_combined_capture_and_error_handling(self):
        # Silent and suppressed calls still capture both streams; only silent
        # calls also disable the existing nonzero-exit exception behavior.
        command = [sys.executable, '-c', "import os; os.write(1, b'out'); os.write(2, b'err'); exit(7)"]
        for kwargs in ({'error_handling': False}, {'silent': True}, {'suppress': True, 'error_handling': False}):
            with self.subTest(kwargs=kwargs):
                self.stdout.seek(0)
                self.stdout.truncate()
                result = self.formatter.run_command(command, **kwargs)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (7, 'outerr', ''))
                self.assertEqual(self.stdout.getvalue(), 'outerr' if kwargs == {'error_handling': False} else '')
        with self.assertRaises(SystemExit) as raised:
            self.formatter.run_command(command, suppress=True)
        self.assertEqual(raised.exception.code, 7)

    def test_json_stays_separate_and_plain_environment_is_preserved(self):
        # Stderr must never enter the JSON decoder, even though ordinary plain
        # commands combine it with stdout. Child color settings remain plain.
        command = [sys.executable, '-c',
                   "import json, os, sys; sys.stderr.write('warning'); "
                   "print(json.dumps([os.environ['TERM'], os.environ['NO_COLOR'], os.environ['CLICOLOR']]))"]
        result = self.formatter.run_command(command, silent=True, parse_json=True)
        self.assertEqual(result, ['dumb', '1', '0'])
        self.assertEqual(self.stdout.getvalue(), '')
        self.assertEqual(self.stderr.getvalue(), '')

    def test_list_arguments_reach_child_unchanged(self):
        # Shell operators and variable references in list elements are literal
        # arguments, even when cmd.exe and the child each parse the command.
        arguments = ['', 'two words', 'a"b', "a'b", 'a&b|c<d>e', '%PATH%', '!PATH!', '$PATH', '^', 'path with space\\']
        command = [sys.executable, '-c', 'import json, sys; print(json.dumps(sys.argv[1:]))'] + arguments
        result = self.formatter.run_command(command, silent=True, parse_json=True)
        self.assertEqual(result, arguments)


if __name__ == '__main__':
    unittest.main()
