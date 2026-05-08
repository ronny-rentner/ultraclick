import os
import subprocess
import sys
import unittest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPT = os.path.join(PROJECT_ROOT, 'tests', 'logging_capture.py')


class TestLoggingCapture(unittest.TestCase):
    def run_command(self, env=None):
        command_env = os.environ.copy()
        if env:
            command_env.update(env)
        return subprocess.run(
            [sys.executable, SCRIPT, "warn"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT,
            env=command_env,
        )

    def test_main_group_captures_logs_by_default(self):
        result = self.run_command()
        self.assertEqual(result.returncode, 0)
        self.assertIn("done", result.stdout)
        self.assertIn("WARNING: fixture | library warning", result.stderr)

    def test_main_group_can_disable_log_capture(self):
        result = self.run_command({"ULTRACLICK_TEST_CAPTURE_LOGS": "0"})
        self.assertEqual(result.returncode, 0)
        self.assertIn("done", result.stdout)
        self.assertNotIn("fixture | library warning", result.stderr)


if __name__ == '__main__':
    unittest.main()
