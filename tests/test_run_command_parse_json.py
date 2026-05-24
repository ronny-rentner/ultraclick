"""Tests for OutputFormatter.run_command JSON parsing.

Core invariant: parse_json=True must read JSON from stdout alone, never from
a PTY-merged stream. Subprocess warnings on stderr (Node DEP0169, Python
DeprecationWarning, etc.) must not corrupt json.loads.
"""

import sys
import unittest
from unittest import mock

import ultraclick


@unittest.skipIf(sys.platform.startswith('win'), 'PTY branch is Unix-only')
class TestRunCommandParseJson(unittest.TestCase):

    def setUp(self):
        self.formatter = ultraclick.output

    def _python_inline(self, code):
        return [sys.executable, '-c', code]

    def test_parses_clean_json_even_when_stderr_is_noisy(self):
        # Labels regression: subprocess emits valid JSON to stdout AND a
        # deprecation warning to stderr. PTY-merged streams would corrupt the
        # parse; the fix routes parse_json through the non-PTY branch.
        cmd = self._python_inline(
            "import sys; sys.stderr.write('DeprecationWarning: noisy\\n'); "
            "print('{\"icons\": [1, 2, 3]}')"
        )
        with mock.patch.object(ultraclick, 'PLAIN_TEXT_MODE', False):
            result = self.formatter.run_command(cmd, silent=True, parse_json=True)
        self.assertEqual(result, {'icons': [1, 2, 3]})

    def test_returns_empty_dict_silently_when_stdout_is_not_json(self):
        # silent=True is the caller's silence contract: malformed stdout
        # returns {} with no output and no exception.
        cmd = self._python_inline("print('definitely not json')")
        with mock.patch.object(ultraclick, 'PLAIN_TEXT_MODE', False):
            result = self.formatter.run_command(cmd, silent=True, parse_json=True)
        self.assertEqual(result, {})

    def test_display_path_still_merges_streams_via_pty(self):
        # Without parse_json on Unix, the PTY branch must keep merging stderr
        # into stdout so docker/npm progress bars stay ordered as the user sees
        # them in a terminal. result.stderr stays empty under PTY combine.
        cmd = self._python_inline(
            "import sys; print('on-stdout'); sys.stderr.write('on-stderr\\n')"
        )
        with mock.patch.object(ultraclick, 'PLAIN_TEXT_MODE', False):
            result = self.formatter.run_command(cmd, silent=True)
        self.assertIn('on-stdout', result.stdout)
        self.assertIn('on-stderr', result.stdout)
        self.assertEqual(result.stderr, '')


if __name__ == '__main__':
    unittest.main()
