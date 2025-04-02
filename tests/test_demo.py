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
    
    def test_version_command(self):
        """Test the version command returns expected output"""
        result = self.run_command(["version"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("ultraclick demo v0.0.1", result.stdout)
    
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

if __name__ == '__main__':
    unittest.main()