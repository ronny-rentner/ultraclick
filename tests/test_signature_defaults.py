import os
import subprocess
import sys
import unittest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPT = os.path.join(PROJECT_ROOT, 'tests', 'signature_defaults.py')


class TestSignatureDefaults(unittest.TestCase):
    def run_command(self, args):
        return subprocess.run(
            [sys.executable, SCRIPT] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT,
        )

    def assert_output(self, args, stdout):
        result = self.run_command(args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, stdout)
        self.assertEqual(result.stderr, "")

    def test_signature_defaults_apply_when_options_are_omitted(self):
        self.assert_output(['show'], "env=development dry_run=True zone=eu\n")

    def test_given_options_override_signature_defaults(self):
        for args in (['-e', 'prod', '--no-dry-run', '--region', 'us'], ['--env', 'prod', '--no-dry-run', '--region', 'us']):
            with self.subTest(args=args):
                self.assert_output(args + ['show'], "env=prod dry_run=False zone=us\n")

    def test_help_shows_signature_defaults(self):
        result = self.run_command(['--help'])
        self.assertEqual(result.returncode, 0, result.stderr)
        for default in ('[default: development]', '[default: dry-run]', '[default: eu]'):
            self.assertIn(default, result.stdout)

    def test_uppercase_argument_uses_signature_default(self):
        for args, stdout in ((['greet'], "Hello world\n"), (['greet', 'Ada'], "Hello Ada\n")):
            with self.subTest(args=args):
                self.assert_output(args, stdout)


if __name__ == '__main__':
    unittest.main()
