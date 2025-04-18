# ultraclick

A powerful class-based wrapper for building elegant command-line interfaces in Python.

**ultraclick** is a Python library that extends the popular [click](https://github.com/pallets/click) framework, enabling you to create structured CLI applications using object-oriented principles. It integrates [rich-click](https://github.com/ewels/rich-click) for beautiful color formatting and enhanced readability.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Demo Application](#demo-application)
- [Help Output](#help-output)
- [Demo Code](#demo-code)

## Features

**ultraclick** offers significant advantages over function-based CLI frameworks:

- **Class-based CLI structure**: Define your command-line interface using Python classes
- **Nested command groups**: Organize commands in a hierarchical structure
- **Class instance state**: Share data between commands naturally via instance attributes
- **Context Proxy**: Access the Click context directly with `click.ctx` without passing it as a parameter
- **Context sharing**: Share context data between different command levels via `ctx.meta`
- **Rich output formatting**: Colored output and better help text formatting via rich-click
- **Interactive command execution**: Preserves colors, progress bars, and interactive output from subprocesses
- **Cross-platform compatibility**: Works on Unix, macOS, and Windows
- **Command aliases**: Create alternative names for commands (e.g., `info` as an alias for `status` or `add` as an alias for `create`)
- **Command abbreviations**: Type partial commands like `conf s` instead of `config show` when unambiguous
- **Automatic return value handling**: Command return values are automatically displayed
- **Clean, maintainable code**: Group related commands together with proper encapsulation
- **Full compatibility**: Supports all features of Click and RichClick

## Installation

### From PyPI (recommended)

```bash
pip install ultraclick
```

### From Source

```bash
# Clone the repository
git clone https://github.com/ronny-rentner/ultraclick.git
cd ultraclick

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package in development mode (will install dependencies automatically)
pip install -e .
```

## Demo Application

The repository includes a comprehensive demo that showcases ultraclick's features. After installation and activating your virtual environment, try the following commands:

```bash
./demo.py --help
./demo.py --profile production --verbose status
./demo.py config
./demo.py resource
./demo.py resource --resource-type database create mydb --size large --region eu-west
./demo.py config set debug true
./demo.py config update debug false
./demo.py r l
./demo.py --profile staging r --resource-type storage l
```

### Tab Completion

Enable tab completion for the demo application in Bash:

```bash
eval "$(_DEMO_PY_COMPLETE=bash_source python ./demo.py)"
```

Now you can use Tab to complete commands, options, and arguments.

## Help Output

Sample help outputs from the demo application:

### Main Help
```
 Usage: demo [OPTIONS] COMMAND [ARGS]...                                        
                                                                                
 Main demo application showcasing ultraclick's features.                        
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --verbose                                    Enable verbose output           │
│ --profile    TEXT                            Configuration profile to use    │
│ --env        [development|staging|productio  Environment to run in           │
│              n]                                                              │
│ --version                                    Show the version and exit.      │
│ --help                                       Show this message and exit.     │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ config    Configuration commands for the application. Demonstrates context   │
│           sharing between subcommands.                                       │
│ info      Show application status.                                           │
│ resource  Resource management commands. Demonstrates parameter handling and  │
│           nested command structure.                                          │
│ status    Show application status.                                           │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### Config Command Help
```
 Usage: demo config [OPTIONS] COMMAND [ARGS]...                                 
                                                                                
 Configuration commands for the application. Demonstrates context sharing       
 between subcommands.                                                           
 This command group shows help when called directly (default behavior).         
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --config-dir    PATH  Configuration directory                                │
│ --help                Show this message and exit.                            │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ get       Get a configuration value.                                         │
│ set       Set a configuration value.                                         │
│ show      Display current configuration settings.                            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Tips

### Flexible Parameter Ordering

By default, Click only allows `./demo.py --verbose status` but not `./demo.py status --verbose`. 

To enable both patterns, use the `allow_interspersed_args` context setting:

```python
cli = click.group_from_class(MainApp, context_settings={"allow_interspersed_args": True})
```

This is enabled by default in ultraclick.

## Demo Code

Check out [gwctl](https://github.com/ronny-rentner/gwctl) for a real-world application built with ultraclick.

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

import ultraclick as click


class ConfigCommand:
    """
    Configuration commands for the application.
    Demonstrates context sharing between subcommands.

    This command group shows help when called directly (default behavior).
    """
    @click.option("--config-dir", type=pathlib.Path, default="./config", help="Configuration directory")
    def __init__(self, config_dir):
        # Store parameters as instance variables
        self.config_dir = config_dir
        
        # Access shared data from parent command
        self.profile = click.ctx.meta["profile"]
        
        # Share this command's data with child commands
        click.ctx.meta["config_dir"] = config_dir

    @click.command()
    def show(self):
        """Display current configuration settings."""
        path_prefix = './' if not self.config_dir.is_absolute() else ''
        return (
            f"Active Profile: {self.profile}\n"
            f"Config Directory: {path_prefix}{self.config_dir}"
        )

    @click.command()
    @click.argument("name")
    @click.argument("value")
    def set(self, name, value):
        """Set a configuration value."""
        return f"Setting {name}={value} in profile '{self.profile}'"

    # Command alias demonstration - using decorator approach
    update = click.alias(set)

    @click.command()
    @click.argument("name")
    def get(self, name):
        """Get a configuration value."""
        return f"Getting '{name}' from profile '{self.profile}'"

    # Another command alias - using decorator approach
    fetch = click.alias(get)


class ResourceCommand:
    """
    Resource management commands.
    Demonstrates parameter handling and nested command structure.

    This command group performs an action when called directly (no help shown).
    """
    @click.option("--resource-type", type=click.Choice(['server', 'database', 'storage']),
                  default="server", help="Type of resource to manage")
    def __init__(self, resource_type):
        self.resource_type = resource_type
        
        # Access shared data from parent command
        self.profile = click.ctx.meta["profile"]

        # Custom behavior when no subcommand is provided
        if click.ctx.invoked_subcommand is None:
            # Prevent automatic help display
            click.ctx.meta['show_help_on_no_command'] = False
            
            # Show custom summary instead
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
    def create(self, name, size, region):
        """Create a new resource."""
        return (
            f"Creating {self.resource_type} '{name}'\n"
            f"Size: {size}\n"
            f"Region: {region}\n"
            f"Using profile: {self.profile}"
        )

    @click.command()
    @click.argument("name")
    def delete(self, name):
        """Delete a resource."""
        return f"Deleting {self.resource_type} '{name}'"

    @click.command()
    @click.argument("names", nargs=-1)
    def list(self, names):
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
    @click.version_option(version="1.0")
    def __init__(self, verbose, profile, env):
        # Store options as instance variables
        self.verbose = verbose
        self.profile = profile
        self.env = env

        # Share data with child commands
        click.ctx.meta["verbose"] = verbose
        click.ctx.meta["profile"] = profile
        click.ctx.meta["env"] = env

        if verbose:
            click.output.success(f"Verbose mode enabled in {env} environment")

    @click.command()
    def status(self):
        """Show application status."""
        return (
            f"Status: Running\n"
            f"Environment: {self.env}\n"
            f"Verbose: {self.verbose}\n"
            f"Profile: {self.profile}"
        )
    
    # Command alias using the decorator approach
    info=click.alias(status)

if __name__ == "__main__":
    click.group_from_class(MainApp, name="demo")()
```
