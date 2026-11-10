"""Tests for Ctrl-C while run_command waits for a child command."""

import os
import select
import signal
import subprocess
import sys
import unittest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# The parent runs the child given as its first argument, reports the child's return code, and keeps running.
PARENT = """
import sys, time, ultraclick
result = ultraclick.output.run_command([sys.executable, '-c', sys.argv[1]], error_handling=False)
print('parent after child', result.returncode, flush=True)
time.sleep(30)
"""


@unittest.skipIf(os.name == 'nt', 'process groups and SIGINT are Unix-only')
class TestRunCommandInterrupt(unittest.TestCase):

    def start_parent(self, child, colors):
        # A new session gives parent and child their own process group, as a terminal's foreground job has.
        process = subprocess.Popen([sys.executable, '-c', PARENT, child], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   cwd=PROJECT_ROOT, start_new_session=True,
                                   env=dict(os.environ, ULTRACLICK_PLAIN='1', ULTRACLICK_COLORS=colors))
        self.addCleanup(self.stop_group, process)
        return process

    def stop_group(self, process):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            # Every process of the group has already exited.
            pass
        process.communicate()

    def read_until(self, process, text):
        output = b''
        while text.encode() not in output:
            self.assertTrue(select.select([process.stdout], [], [], 10)[0], f'No {text!r} in {output!r}')
            chunk = os.read(process.stdout.fileno(), 1024)
            self.assertTrue(chunk, f'Output ended without {text!r}: {output!r}')
            output += chunk

    def ctrl_c(self, process):
        # The terminal sends Ctrl-C to its whole foreground process group.
        os.killpg(process.pid, signal.SIGINT)

    def test_first_ctrl_c_ends_child_and_parent_continues(self):
        for colors in ('0', '1'):
            with self.subTest(colors=colors):
                process = self.start_parent("import time; print('ready', flush=True); time.sleep(30)", colors)
                self.read_until(process, 'ready')
                self.ctrl_c(process)
                self.read_until(process, 'parent after child')

    def test_second_ctrl_c_interrupts_parent_while_child_keeps_running(self):
        child = ("import signal, time; signal.signal(signal.SIGINT, lambda signum, frame: print('child handled ctrl-c', flush=True)); "
                 "print('ready', flush=True); time.sleep(30)")
        for colors in ('0', '1'):
            with self.subTest(colors=colors):
                process = self.start_parent(child, colors)
                self.read_until(process, 'ready')
                self.ctrl_c(process)
                self.read_until(process, 'child handled ctrl-c')
                self.assertIsNone(process.poll())
                self.ctrl_c(process)
                self.assertNotEqual(process.wait(timeout=10), 0)

    def test_ctrl_c_interrupts_parent_after_child_exits(self):
        for colors in ('0', '1'):
            with self.subTest(colors=colors):
                process = self.start_parent('pass', colors)
                self.read_until(process, 'parent after child 0')
                self.ctrl_c(process)
                self.assertNotEqual(process.wait(timeout=10), 0)


if __name__ == '__main__':
    unittest.main()
