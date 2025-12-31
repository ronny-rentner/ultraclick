import unittest
import subprocess
import os
import sys

# Get the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DEMO_SCRIPT = os.path.join(PROJECT_ROOT, 'demo.py')

class TestDemoCLI(unittest.TestCase):
    """Test the demo CLI by actually running it as a subprocess"""
    
    def run_command(self, args):
        """Run the demo CLI with the given arguments and return stdout and stderr"""
        # Use Python to run the script to ensure it works cross-platform
        cmd = [sys.executable, DEMO_SCRIPT] + args
        
        # Run the command and capture stdout and stderr
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        # Print full output details for better debugging
        print(f"\nCommand: python demo.py {' '.join(args)}")
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        return result
    
    def test_version_option(self):
        """Test the --version option returns expected output"""
        result = self.run_command(["--version"])
        self.assertEqual(result.returncode, 0)
        # Just check that version output contains "demo" and "version" without hardcoding the version number
        self.assertIn("demo", result.stdout.lower())
        self.assertIn("version", result.stdout.lower())
    
    def test_status_command(self):
        """Test the status command returns expected output"""
        result = self.run_command(["status"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Status: Running", result.stdout)
        self.assertIn("Environment: development", result.stdout)
        self.assertIn("Profile: default", result.stdout)
    
    def test_config_show_command(self):
        """Test the config show command returns expected output"""
        result = self.run_command(["config", "show"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Active Profile: default", result.stdout)
        self.assertIn("Config Directory: ./config", result.stdout)
    
    def test_config_set_command(self):
        """Test the config set command works correctly"""
        result = self.run_command(["config", "set", "debug", "true"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Setting debug=true in profile 'default'", result.stdout)
    
    def test_config_alias_command(self):
        """Test that command aliases work correctly"""
        result = self.run_command(["config", "update", "debug", "false"])
        try:
            self.assertEqual(result.returncode, 0)
            self.assertIn("Setting debug=false in profile 'default'", result.stdout)
        except AssertionError:
            print(f"Command failed with stderr: {result.stderr}")
            raise
    
    def test_resource_list_command(self):
        """Test the resource list command works correctly"""
        result = self.run_command(["resource", "list"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Listing all servers (Profile: default)", result.stdout)
    
    def test_resource_create_command(self):
        """Test the resource create command with options"""
        cmd = ["resource", "--resource-type", "database", "create", 
               "mydb", "--size", "large", "--region", "eu-west"]
        result = self.run_command(cmd)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Creating database 'mydb'", result.stdout)
        self.assertIn("Size: large", result.stdout)
        self.assertIn("Region: eu-west", result.stdout)
    
    def test_command_abbreviation(self):
        """Test that command abbreviations work correctly"""
        # This should resolve to 'resource list'
        result = self.run_command(["r", "l"])
        try:
            self.assertEqual(result.returncode, 0)
            self.assertIn("Listing all servers (Profile: default)", result.stdout)
        except AssertionError:
            print(f"Command failed with stderr: {result.stderr}")
            raise
    
    def test_global_options(self):
        """Test that global options affect all commands"""
        result = self.run_command(["--profile", "production", "status"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Profile: production", result.stdout)
    
    def test_allow_interspersed_args(self):
        """Test that options can be specified after commands"""
        # Test options before command (traditional style)
        result_before = self.run_command(["--verbose", "status"])
        self.assertEqual(result_before.returncode, 0)
        self.assertIn("Verbose: True", result_before.stdout)
        self.assertIn("Verbose mode enabled", result_before.stderr)
        
        # Test options after command (requires allow_interspersed_args=True)
        result_after = self.run_command(["status", "--verbose"])
        self.assertEqual(result_after.returncode, 0)
        self.assertIn("Verbose: True", result_after.stdout)
        self.assertIn("Verbose mode enabled", result_after.stderr)

    def test_subcommand_help_end(self):
        """Test help at the end of a subcommand"""
        result = self.run_command(["resource", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: demo.py resource", result.stdout)
        self.assertIn("Commands", result.stdout)

    def test_subcommand_help_start(self):
        """Test help before a subcommand (look-ahead)"""
        result = self.run_command(["--help", "resource"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: demo.py resource", result.stdout)

    def test_deep_subcommand_help_end(self):
        """Test help for a deep subcommand with required arguments"""
        result = self.run_command(["resource", "create", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: demo.py resource create", result.stdout)
        # Should NOT fail with missing argument error
        self.assertNotIn("Missing argument", result.stdout)

    def test_deep_subcommand_help_start(self):
        """Test help before a deep subcommand"""
        result = self.run_command(["--help", "resource", "create"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: demo.py resource create", result.stdout)
        self.assertNotIn("Missing argument", result.stdout)

    def test_leaf_command_help(self):
        """Test help for a leaf command"""
        result = self.run_command(["status", "--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: demo.py status", result.stdout)
        self.assertNotIn("Status: Running", result.stdout)

    def test_leaf_command_help_start(self):
        """Test help before a leaf command"""
        result = self.run_command(["--help", "status"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: demo.py status", result.stdout)
        self.assertNotIn("Status: Running", result.stdout)

if __name__ == '__main__':
    unittest.main()