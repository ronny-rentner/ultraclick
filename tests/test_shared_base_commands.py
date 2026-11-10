import os
import subprocess
import sys
import unittest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPT = os.path.join(PROJECT_ROOT, 'tests', 'shared_base_commands.py')


class TestSharedBaseCommands(unittest.TestCase):
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

    def test_each_group_runs_inherited_command_on_its_own_instance(self):
        # The class name in the output shows which instance ran the command.
        for group, class_name in (('api', 'Api'), ('service', 'Service'), ('web', 'Web')):
            with self.subTest(group=group):
                self.assert_output([group, '--host', 'example', 'status'], f"{class_name} on example\n")

    def test_inherited_alias_runs_its_own_groups_command(self):
        for group, class_name in (('api', 'Api'), ('service', 'Service'), ('web', 'Web')):
            with self.subTest(group=group):
                self.assert_output([group, 'check'], f"{class_name} on localhost\n")

    def test_overrides_replace_inherited_command_and_options(self):
        self.assert_output(['db', '--port', '1', 'status'], "Db on port 1\n")
        result = self.run_command(['db', '--help'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--port', result.stdout)
        self.assertNotIn('--host', result.stdout)

    def test_inherited_options_are_listed_once(self):
        for group in ('api', 'service', 'web'):
            with self.subTest(group=group):
                result = self.run_command([group, '--help'])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.count('--host'), 1)


if __name__ == '__main__':
    unittest.main()
