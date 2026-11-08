"""Tests for conditional console silencing."""

import io
import sys
import unittest
from unittest import mock

import ultraclick


class TestOutputSilence(unittest.TestCase):

    def setUp(self):
        self.stderr = io.StringIO()
        patch = mock.patch.object(sys, 'stderr', self.stderr)
        patch.start()
        self.addCleanup(patch.stop)
        self.formatter = ultraclick.PlainOutputFormatter()

    def test_condition_selects_silencing(self):
        # Output after the block shows that silencing ends with it.
        for args, expected in (((), 'after\n'), ((True,), 'after\n'), ((False,), 'inside\nafter\n')):
            with self.subTest(args=args):
                self.stderr.seek(0)
                self.stderr.truncate()
                with self.formatter.silence(*args):
                    self.formatter.info('inside')
                self.formatter.info('after')
                self.assertEqual(self.stderr.getvalue(), expected)

    def test_nested_silence_lasts_until_outermost_exit(self):
        with self.formatter.silence():
            with self.formatter.silence():
                pass
            self.formatter.info('inside')
        self.formatter.info('after')
        self.assertEqual(self.stderr.getvalue(), 'after\n')

    def test_disabled_silence_keeps_enclosing_silence(self):
        with self.formatter.silence():
            with self.formatter.silence(False):
                pass
            self.formatter.info('inside')
        self.assertEqual(self.stderr.getvalue(), '')


if __name__ == '__main__':
    unittest.main()
