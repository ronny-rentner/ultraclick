import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from click.testing import CliRunner
import ultraclick as click
from simple import SimpleApp


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SIMPLE_SCRIPT = os.path.join(PROJECT_ROOT, 'simple.py')


class TestSimpleCLI(unittest.TestCase):
    def test_commands_discovered_on_constructed_instance(self):
        class DynamicApp:
            @click.option('--value')
            def __init__(self, value='default'):
                self.value = value

                @click.command()
                def show(self):
                    return self.value

                self.show = show

        cli = click.group_from_class(DynamicApp)
        for args, expected in ((['--value', 'first', 'show'], 'first'),
                               (['sh', '--value', 'second'], 'second')):
            with self.subTest(args=args):
                result = CliRunner().invoke(cli, args)
                self.assertEqual(result.exit_code, 0, result.exception)
                self.assertEqual(result.stdout, expected + '\n')
                self.assertEqual(result.stderr, '')

    def run_command(self, args):
        return subprocess.run(
            [sys.executable, SIMPLE_SCRIPT] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT,
        )

    def test_default_action_prints_return_values(self):
        # Exercise the existing default action with each supported result shape.
        for value, expected in (("Success", "Success\n"),
                                (["one", "two"], "one\ntwo\n"),
                                ({"names": ["one", "two"]}, "names: one, two\n"),
                                (None, ""), (0, "0\n"), (False, "False\n")):
            with self.subTest(value=value), patch.object(SimpleApp, "__run__", return_value=value):
                result = CliRunner().invoke(click.group_from_class(SimpleApp), [], standalone_mode=False)
                self.assertEqual(result.exit_code, 0, result.exception)
                self.assertEqual(result.stdout, expected)
                self.assertEqual(result.stderr, "")
                # Printing must not consume or replace the value returned to the caller.
                self.assertIs(result.return_value, value)

    def test_help_does_not_run_default_action(self):
        # Help must skip the action itself, including any side effects before it returns.
        with patch.object(SimpleApp, "__run__") as action:
            result = CliRunner().invoke(click.group_from_class(SimpleApp), ["--help"])
            self.assertEqual(result.exit_code, 0, result.exception)
            action.assert_not_called()

    def test_help_does_not_claim_missing_subcommands(self):
        result = self.run_command(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: simple.py [OPTIONS]", result.stdout)
        # An optional command placeholder still advertises nonexistent subcommands.
        self.assertNotIn("COMMAND", result.stdout)


if __name__ == '__main__':
    unittest.main()
