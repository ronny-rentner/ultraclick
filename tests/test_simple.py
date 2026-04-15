import os
import subprocess
import sys
import unittest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SIMPLE_SCRIPT = os.path.join(PROJECT_ROOT, 'simple.py')


class TestSimpleCLI(unittest.TestCase):
    def run_command(self, args):
        return subprocess.run(
            [sys.executable, SIMPLE_SCRIPT] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT,
        )

    def test_help_does_not_claim_missing_subcommands(self):
        result = self.run_command(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: simple.py [OPTIONS]", result.stdout)
        self.assertNotIn("COMMAND [ARGS]", result.stdout)


if __name__ == '__main__':
    unittest.main()
