import os
import subprocess
import sys
import unittest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class TestOutputPlain(unittest.TestCase):
    def output_plain(self, colors):
        # The output style is chosen at import, so each case needs a fresh process; its captured output is no terminal.
        result = subprocess.run(
            [sys.executable, '-c', 'import ultraclick; print(ultraclick.output.plain)'],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=dict(os.environ, PYTHONPATH=os.path.join(PROJECT_ROOT, 'src'), ULTRACLICK_PLAIN='', ULTRACLICK_COLORS=colors),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_plain_without_terminal(self):
        self.assertEqual(self.output_plain(colors=''), "True\n")

    def test_not_plain_with_forced_colors(self):
        self.assertEqual(self.output_plain(colors='1'), "False\n")


if __name__ == '__main__':
    unittest.main()
