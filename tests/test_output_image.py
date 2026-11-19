"""Tests for showing images through the output formatter."""

import base64
import io
import os
import sys
import unittest
from unittest import mock

import ultraclick


class TestOutputImage(unittest.TestCase):

    def setUp(self):
        self.stderr = io.StringIO()
        patch = mock.patch.object(sys, 'stderr', self.stderr)
        patch.start()
        self.addCleanup(patch.stop)

    def test_image_sends_absolute_path_through_kitty_graphics_protocol(self):
        ultraclick.OutputFormatter().image('images/chart.png')
        payload = base64.b64encode(os.path.join(os.getcwd(), 'images', 'chart.png').encode()).decode()
        self.assertEqual(self.stderr.getvalue(), f"\x1b_Gf=100,t=f,a=T;{payload}\x1b\\\n")

    def test_long_image_path_stays_on_one_line(self):
        ultraclick.OutputFormatter().image('x' * 500 + '.png')
        self.assertEqual(self.stderr.getvalue().count('\n'), 1)

    def test_plain_image_prints_path(self):
        ultraclick.PlainOutputFormatter().image('images/chart.png')
        self.assertEqual(self.stderr.getvalue(), "images/chart.png\n")


if __name__ == '__main__':
    unittest.main()
