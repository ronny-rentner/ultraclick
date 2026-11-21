import json
import os
import subprocess
import sys
import unittest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPT = os.path.join(PROJECT_ROOT, 'tests', 'json_output.py')


class TestJsonOutput(unittest.TestCase):
    def run_command(self, *args):
        # The captured output is no terminal, so the fixture starts in plain mode.
        result = subprocess.run(
            [sys.executable, SCRIPT, *args],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=dict(os.environ, ULTRACLICK_PLAIN='', ULTRACLICK_COLORS=''),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_json_prints_list_of_dicts_as_one_array(self):
        result = self.run_command("--json", "windows")
        self.assertEqual(json.loads(result.stdout), [{"id": 1, "title": "Editor"}, {"id": 2, "title": None}])

    def test_json_prints_string_as_json_string(self):
        self.assertEqual(self.run_command("--json", "title").stdout, '"Editor"\n')

    def test_json_keeps_messages_on_stderr(self):
        result = self.run_command("--json", "close")
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "OK: closed\n")

    def test_text_forms_without_json(self):
        self.assertEqual(self.run_command("windows").stdout, "{'id': 1, 'title': 'Editor'}\n{'id': 2, 'title': None}\n")
        self.assertEqual(self.run_command("title").stdout, "Editor\n")


if __name__ == '__main__':
    unittest.main()
