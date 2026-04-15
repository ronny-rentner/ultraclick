import os
import subprocess
import sys
import unittest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPT = os.path.join(PROJECT_ROOT, 'tests', 'help_with_required_init_args.py')


class TestHelpWithRequiredInitArgs(unittest.TestCase):
    def run_command(self, args):
        return subprocess.run(
            [sys.executable, SCRIPT] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT,
        )

    def test_help_does_not_require_init_arguments(self):
        # This command shape matches class-based groups whose __init__ declares required arguments.
        result = self.run_command(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)
        self.assertIn("[OPTIONS] INPUT_DIR [SLUG]", result.stdout)
        self.assertNotIn("Missing argument 'INPUT_DIR'", result.stdout)
        self.assertEqual(result.stderr, "")


if __name__ == '__main__':
    unittest.main()
