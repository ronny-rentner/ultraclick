# ultraclick

**Warning: This is an early hack. There are no unit tests, yet. Maybe not stable!**

In contrast to plain version of [click](https://github.com/pallets/click), ultraclick allows you to define your CLI using Python classes. ultraclick is based on rich-click which is adding colors to click.

## Features

- **Class-based CLI structure**: Define your command-line interface using Python classes
- **Nested command groups**: Organize commands in a hierarchical structure
- **Automatic context sharing**: Share context between commands in the same class instance
- **Rich output formatting**: Colored output and better help text formatting via rich-click
- **Command aliases**: Create alternative names for commands (e.g., `greet` and `hello`)
- **Command abbreviations**: Type partial commands like `demo u` instead of `demo update` when unambiguous
- **Automatic return value handling**: Command return values are automatically displayed
- **Full compatibility**: Supports all features of Click and RichClick

## Installation

To install and run the demo after cloning the repository:

```bash
# Clone the repository
git clone https://github.com/ronny-rentner/ultraclick.git
cd ultraclick

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package in development mode (will install dependencies automatically)
pip install -e .

# Run the demo
python demo.py --help
# Using global options
python demo.py --profile production --verbose status  # top-level options affect all commands
# Try different behaviors with command groups
python demo.py config          # shows help by default
python demo.py resource        # executes custom behavior without showing help
# Command-specific options
python demo.py resource --resource-type database create mydb --size large --region eu-west
# Try command aliases
python demo.py config set debug true
python demo.py config update debug false  # alias for 'set'
# Try command abbreviations
python demo.py r l             # shorthand for 'resource list'
# Combine options, aliases, and abbreviations
python demo.py --profile staging r --resource-type storage l
```


## Example
```python
#!/usr/bin/env python
"""
ultraclick Demo Application

This demo systematically showcases ultraclick's main features:
1. Class-based CLI structure
2. Nested command groups
3. Automatic context sharing
4. Command aliases
5. Command abbreviations
6. Automatic return value handling
"""

import pathlib
import os
from typing import Optional, List

import ultraclick as click


class ConfigCommand:
    """
    Configuration commands for the application.
    Demonstrates context sharing between subcommands.
    
    This command group shows help when called directly (default behavior).
    """
    @click.option("--config-dir", type=pathlib.Path, default="./config", help="Configuration directory")
    def __init__(self, ctx, config_dir):
        # Store parameters as instance variables for sharing between commands
        self.config_dir = config_dir
        
        # Get profile from context that was set in the parent MainApp
        self.profile = ctx.meta.get("profile")
        
        # Add config_dir to context.meta for global access
        ctx.meta["config_dir"] = config_dir
        
        # Let the default behavior show help (flag is already True by default)

    @click.command()
    def show(self, ctx):
        """Display current configuration settings."""
        return (
            f"Active Profile: {self.profile}\n"
            f"Config Directory: {self.config_dir}"
        )
    
    @click.command()
    @click.argument("name")
    @click.argument("value")
    def set(self, ctx, name, value):
        """Set a configuration value."""
        return f"Setting {name}={value} in profile '{self.profile}'"
    
    # Command alias demonstration
    update = set
    
    @click.command()
    @click.argument("name")
    def get(self, ctx, name):
        """Get a configuration value."""
        return f"Getting '{name}' from profile '{self.profile}'"
    
    # Another command alias
    fetch = get


class ResourceCommand:
    """
    Resource management commands.
    Demonstrates parameter handling and nested command structure.
    
    This command group performs an action when called directly (no help shown).
    """
    @click.option("--resource-type", type=click.Choice(['server', 'database', 'storage']), 
                  default="server", help="Type of resource to manage")
    def __init__(self, ctx, resource_type):
        self.resource_type = resource_type
        
        # Get profile from context that was set in the parent MainApp
        self.profile = ctx.meta.get("profile")
        
        # Custom behavior when no subcommand is provided
        if ctx.invoked_subcommand is None:
            # Tell the system not to show help
            ctx.meta['show_help_on_no_command'] = False
            
            # Print our custom message instead
            click.echo(
                f"Resource Management Summary:\n"
                f"• Current Resource Type: {self.resource_type}\n"
                f"• Available Types: server, database, storage\n"
                f"• Active Profile: {self.profile}"
            )
        
    @click.command()
    @click.argument("name")
    @click.option("--size", default="medium", help="Resource size (small, medium, large)")
    @click.option("--region", default="us-east", help="Deployment region")
    def create(self, ctx, name, size, region):
        """Create a new resource."""
        return (
            f"Creating {self.resource_type} '{name}'\n"
            f"Size: {size}\n"
            f"Region: {region}\n"
            f"Using profile: {self.profile}"
        )

    @click.command()
    @click.argument("name")
    def delete(self, ctx, name):
        """Delete a resource."""
        return f"Deleting {self.resource_type} '{name}'"
    
    @click.command()
    @click.argument("names", nargs=-1)
    def list(self, ctx, names):
        """List resources, optionally filtered by name."""
        if not names:
            return f"Listing all {self.resource_type}s (Profile: {self.profile})"
        else:
            return f"Filtered {self.resource_type} list: {', '.join(names)} (Profile: {self.profile})"


class MainApp:
    """
    Main demo application showcasing ultraclick's features.
    """
    # Define nested command groups
    config = ConfigCommand
    resource = ResourceCommand
    
    @click.option("--verbose", is_flag=True, help="Enable verbose output")
    @click.option("--profile", default="default", help="Configuration profile to use")
    @click.option("--env", default="development", 
                 type=click.Choice(['development', 'staging', 'production']),
                 help="Environment to run in")
    def __init__(self, ctx, verbose, profile, env):
        self.verbose = verbose
        self.profile = profile
        self.env = env
        
        # Store in context for global access
        ctx.meta["verbose"] = verbose
        ctx.meta["profile"] = profile
        ctx.meta["env"] = env
        
        if verbose:
            click.echo(f"Verbose mode enabled in {env} environment")
    
    @click.command()
    def version(self, ctx):
        """Show application version."""
        return "ultraclick demo v0.0.1"
    
    @click.command()
    def status(self, ctx):
        """Show application status."""
        return (
            f"Status: Running\n"
            f"Environment: {self.env}\n"
            f"Verbose: {self.verbose}\n"
            f"Profile: {ctx.meta.get('profile', 'Not set')}"
        )


if __name__ == "__main__":
    # Create the CLI using MainApp
    click.group_from_class(MainApp, name="demo")(prog_name="demo")
```
