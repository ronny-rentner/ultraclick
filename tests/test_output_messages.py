"""Tests for Rich markup handling in formatter messages."""

import io
import sys
import unittest
from unittest import mock

import ultraclick


class TestOutputMessages(unittest.TestCase):

    def setUp(self):
        self.stderr = io.StringIO()
        patch = mock.patch.object(sys, 'stderr', self.stderr)
        patch.start()
        self.addCleanup(patch.stop)
        self.formatter = ultraclick.OutputFormatter()

    def test_styled_messages_print_brackets_literally(self):
        # The formatter's own styling still applies, so no tag is printed.
        calls = (
            (self.formatter.error, ('saved to [draft]',), '✖ saved to [draft]\n'),
            (self.formatter.warning, ('saved to [draft]',), '✖ saved to [draft]\n'),
            (self.formatter.failure, ('saved to [draft]',), '✖ saved to [draft]\n'),
            (self.formatter.success, ('saved to [draft]',), 'saved to [draft]\n'),
            (self.formatter.error, (ValueError('bad [value]'),), '✖ bad [value]\n'),
            (self.formatter.title, ('Project [a]', 'demo [b]'), 'Project [a]: demo [b]\n'),
        )
        for method, args, expected in calls:
            with self.subTest(method=method.__name__, args=args):
                self.stderr.seek(0)
                self.stderr.truncate()
                method(*args)
                self.assertEqual(self.stderr.getvalue(), expected)

    def test_main_operation_prints_brackets_literally(self):
        self.formatter.main_operation('deploy [draft]')
        self.assertIn('deploy [draft]', self.stderr.getvalue())

    def test_info_keeps_caller_markup(self):
        self.formatter.info('[bold]saved[/bold] to ' + self.formatter.escape_markup('[draft]'))
        self.assertEqual(self.stderr.getvalue(), 'saved to [draft]\n')

    def test_plain_escape_markup_keeps_text(self):
        self.assertEqual(ultraclick.PlainOutputFormatter().escape_markup('[draft]'), '[draft]')


if __name__ == '__main__':
    unittest.main()
