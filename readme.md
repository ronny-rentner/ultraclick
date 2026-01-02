# ultraclick: Object-Oriented CLI Framework for Python

[![PyPI Package](https://img.shields.io/pypi/v/ultraclick.svg)](https://pypi.org/project/ultraclick)
[![Run Tests](https://github.com/ronny-rentner/ultraclick/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/ronny-rentner/ultraclick/actions/workflows/tests.yml)
[![Python >=3.9](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**ultraclick** is a powerful, class-based wrapper around the popular [Click](https://click.palletsprojects.com/) library and [RichClick](https://github.com/ewels/rich-click). It empowers developers to build complex, structured, and beautiful Command Line Interfaces (CLIs) using modern Python object-oriented patterns.

Say goodbye to massive files filled with decorated functions. **ultraclick** lets you organize your CLI commands into clean classes, share state naturally via instance attributes, and enjoy beautiful output formatting out of the box.

## Features

- **Class-Based CLI Architecture**: Define your command-line interface using clean Python classes.
- **Full Compatibility**: 100% compatible with all **Click** and **RichClick** features, decorators, and parameter types.
- **Natural State Management**: Share context (config, API clients, flags) between commands naturally via `self` and class instance attributes.
- **Smart Parameter Handling**: Robust handling of global and local command-line options and arguments, even when interspersed.
- **Context Proxy**: Access the Click context globally via `click.ctx` without messy parameter passing.
- **Deeply Nested Groups**: Create hierarchical command structures (e.g., `app resource create`) by simply nesting classes.
- **Rich Integration**: Beautiful, colorful terminal output and enhanced help text formatting out of the box.
- **Command Aliases & Abbreviations**: Support for command aliases (`status` -> `info`) and partial command matching (`conf s` -> `config show`).
- **Automatic Output**: Simply return values (strings, dicts, lists) from command methods, and they are automatically formatted and printed nicely.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Help Output](#help-output)
- [Advanced Usage](#advanced-usage)
- [Tips](#tips)
- [Development](#development)

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
source venv/bin/activate

# Install the package in development mode
pip install -e .
```

## Quick Start

Here is a complete, runnable example demonstrating how to build a structured CLI with global options, nested commands, and aliases. This code corresponds to the included `demo.py`.

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
        # Store parameters as instance variables for sub-commands in this class
        self.config_dir = config_dir

        # Access shared data from global context
        self.profile = click.ctx.meta["profile"]

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

    # Command alias demonstration
    update = click.alias(set)

    @click.command()
    @click.argument("name")
    def get(self, name):
        """Get a configuration value."""
        return f"Getting '{name}' from profile '{self.profile}'"

    # Another command alias
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

    @click.command()
    @click.argument("name")
    @click.option("--size", default="medium", help="Resource size (small, medium, large)")
    @click.option("--region", default="us-east", help="Deployment region")
    def create(self, name, size, region):
        """Create a new resource."""
        # Use the profile from instance state instead of context
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
        # Use instance state for profile
        if not names:
            return f"Listing all {self.resource_type}s (Profile: {self.profile})"
        else:
            return f"Filtered {self.resource_type} list: {', '.join(names)} (Profile: {self.profile})"


@click.main_group(name="demo")
class MainApp:
    """
    Main demo application showcasing ultraclick's features.
    """
    # Define nested command groups
    config = ConfigCommand
    resource = ResourceCommand

    @click.option("--verbose", is_flag=True, is_eager=True, help="Enable verbose output")
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

        # Store settings in global state
        click.ctx.meta["verbose"] = verbose
        click.ctx.meta["profile"] = profile
        click.ctx.meta["env"] = env

        if verbose:
            click.output.success(f"Verbose mode enabled in {env} environment")

    @click.option("--test", is_flag=True, help="Test option")
    @click.command()
    def status(self, test):
        """Show application status."""

        click.output.headline(f'Demo Status')

        return (
            f"Status: Running\n"
            f"Environment: {self.env}\n"
            f"Verbose: {self.verbose}\n"
            f"Profile: {self.profile}"
        )

    # 'info' is an alias for the 'status' command
    info=click.alias(status)

if __name__ == "__main__":
    MainApp()
```

### Running the Example

```console
$ python demo.py --verbose status
Verbose mode enabled in development environment

→ Demo Status
Status: Running
Environment: development
Verbose: True
Profile: default

$ python demo.py config show
Active Profile: default
Config Directory: ./config

$ python demo.py --profile production resource create mydb --size large
Creating server 'mydb'
Size: large
Region: us-east
Using profile: production
```

## Help Output

**ultraclick** leverages RichClick to produce beautiful help screens automatically.

### Main Help
```
 Usage: demo [OPTIONS] COMMAND [ARGS]...                                     
                                                                                
 Main demo application showcasing ultraclick's features.                        
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --verbose                                    Enable verbose output           │
│ --profile  TEXT                              Configuration profile to use    │
│ --env      [development|staging|production]  Environment to run in           │
│ --version                                    Show the version and exit.      │
│ --help                                       Show this message and exit.     │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ config      Configuration commands for the application. Demonstrates context │
│             sharing between subcommands.                                     │
│ resource    Resource management commands. Demonstrates parameter handling and │
│             nested command structure.                                        │
│ status      Show application status.                                         │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Advanced Usage

### Context Proxy (`click.ctx`)
**ultraclick** provides a `click.ctx` proxy that forwards attributes to `click.get_current_context()`. This allows you to access context data globally without passing it as a parameter.

```python
# Store global state in the main group
click.ctx.meta["db_client"] = Database()

# Access it in any subcommand
db = click.ctx.meta["db_client"]
current_cmd = click.ctx.invoked_subcommand
```

### Output Formatter (`click.output`)
Access styled output methods directly:
- `click.output.success(msg)`
- `click.output.error(msg)`
- `click.output.warning(msg)`
- `click.output.info(msg)`
- `click.output.headline(msg)`

#### Running Shell Commands
Ultraclick includes a powerful command runner that preserves colors and interactivity (via PTY on Unix):

```python
# Simple command execution
click.output.run_command("ls -la")

# Run and capture output
result = click.output.run_command("git status", silent=True)
if result.returncode == 0:
    print(result.stdout)

# Run and parse JSON output automatically
data = click.output.run_command_and_parse_json("kubectl get pods -o json")
print(f"Found {len(data['items'])} pods")
```

## Tips

### Flexible Parameter Ordering
By default, **ultraclick** allows global options to be placed after subcommands (e.g., `./demo.py status --verbose`). It includes robust logic to ensure `--help` flags are correctly routed to the target command even when deep in the hierarchy.

## Development

### Setup
1.  Clone the repository.
2.  Install dependencies: `pip install -e .`

### Testing
Run the included unit tests using the standard Python `unittest` module:
```bash
python -m unittest discover tests
```

## License

GPLv3