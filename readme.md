# ultraclick: Object-Oriented CLI Framework for Python

[![PyPI Package](https://img.shields.io/pypi/v/ultraclick.svg)](https://pypi.org/project/ultraclick)
[![Run Tests](https://github.com/ronny-rentner/ultraclick/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/ronny-rentner/ultraclick/actions/workflows/tests.yml)
[![Python >=3.10](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**ultraclick** is a powerful, class-based wrapper around the popular [Click](https://click.palletsprojects.com/) library and [RichClick](https://github.com/ewels/rich-click). It empowers developers to build complex, structured, and beautiful Command Line Interfaces (CLIs) using modern Python object-oriented patterns.

## Features

- **Class-Based CLI Architecture**: Define your command-line interface using clean Python classes.
- **Full Compatibility**: Compatible with all **Click** and **RichClick** features, decorators, and parameter types.
- **Natural State Management**: Share context between commands naturally via `self` and class instance attributes.
- **Deeply Nested Groups**: Create hierarchical command structures (e.g., `app resource create`) by simply nesting classes.
- **Rich Integration**: Beautiful, colorful terminal output and enhanced help text formatting out of the box.
- **Command Aliases & Abbreviations**: Support for command aliases (`status` -> `info`) and partial command matching (`conf sh` -> `config show`).
- **Automatic Output**: Simply return values (strings, dicts, lists) from command methods, and they are automatically formatted and printed nicely.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Help Output](#help-output)
- [Advanced Usage](#advanced-usage)
- [Known Issues](#known-issues)
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

The included `demo.py` is a larger example demonstrating global options, nested commands, and aliases.

```python
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
import sys

import ultraclick as click
from ultraclick import ctx


class ConfigCommand:
    """
    Configuration commands for the application.
    Demonstrates context sharing between subcommands.

    This command group shows help when called directly (default behavior).
    """
    @click.option("--config-dir", type=pathlib.Path, help="Configuration directory")
    def __init__(self, config_dir="./config"):
        # UltraClick can infer the CLI default from the Python signature, so the
        # decorator only needs the option metadata.
        # Store parameters as instance variables for sub-commands in this class
        self.config_dir = config_dir

        # Demo configuration lives for this invocation; resource creation reads its default region here.
        self.values = {"region": "us-east"}

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
        self.values[name] = value
        # Read back through the shared configuration so callers receive the stored value.
        return ctx.invoke("config.get", name=name)

    # Command alias demonstration
    update = click.alias(set)

    @click.command()
    @click.argument("name")
    def get(self, name):
        """Get a configuration value."""
        # Return the value itself so other commands can use it through ctx.invoke().
        if name not in self.values:
            raise click.ClickException(f"Unknown configuration value: {name}")
        return self.values[name]

    # Another command alias
    fetch = click.alias(get)


class ResourceCommand:
    """
    Resource management commands.
    Demonstrates parameter handling and nested command structure.

    This command group performs an action when called directly (no help shown).
    """
    @click.option("--resource-type", type=click.Choice(['server', 'database', 'storage']),
                  help="Type of resource to manage")
    def __init__(self, resource_type="server"):
        # The signature carries the default so help output and runtime behavior stay in sync.
        self.resource_type = resource_type

        # Access shared data from parent command
        self.profile = click.ctx.meta["profile"]

    def __run__(self):
        """Show the summary when no resource subcommand is selected."""
        return (
            f"Resource Management Summary:\n"
            f"• Current Resource Type: {self.resource_type}\n"
            f"• Available Types: server, database, storage\n"
            f"• Active Profile: {self.profile}"
        )

    @click.command()
    @click.argument("name")
    @click.option("--size", help="Resource size (small, medium, large)")
    @click.option("--region", help="Deployment region (defaults to config region)")
    def create(self, name, size="medium", region=None):
        """Create a new resource."""
        # Resolve the default through config, initializing that group only when needed.
        if region is None:
            region = ctx.invoke("config.get", name="region")
        # Command defaults live on the method signature for the same reason as group defaults above.
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
    @click.option("--profile", help="Configuration profile to use")
    @click.option("--env",
                 type=click.Choice(['development', 'staging', 'production']),
                 help="Environment to run in")
    @click.version_option(version="1.0")
    def __init__(self, verbose, profile="default", env="development"):
        # The signature is the preferred place for option defaults in UltraClick examples.
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

        # Capture the interpreter version for the report; --verbose also shows the subprocess execution.
        runtime = click.output.run_command([sys.executable, "--version"],
                                           headline="Checking Python version", silent=not self.verbose)

        return (
            f"Status: Running\n"
            f"Environment: {self.env}\n"
            f"Verbose: {self.verbose}\n"
            f"Profile: {self.profile}\n"
            f"Runtime: {runtime.stdout.strip()}"
        )

    # 'info' is an alias for the 'status' command
    info=click.alias(status)

    @click.command()
    def testraise(self):
        click.output.headline(f'Testing Exceptions')
        raise Exception(f'Testing Exceptions')


if __name__ == "__main__":
    MainApp()
```

### Running the Example

```console
$ python demo.py status

→ Demo Status
Status: Running
Environment: development
Verbose: False
Profile: default
Runtime: Python 3.13.5

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
$ ./demo.py

 Usage: demo.py [OPTIONS] [COMMAND] [ARGS]...

 Main demo application showcasing ultraclick's features.

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --verbose                                    Enable verbose output                                                   │
│ --profile  TEXT                              Configuration profile to use [default: default]                         │
│ --env      [development|staging|production]  Environment to run in [default: development]                            │
│ --version                                    Show the version and exit.                                              │
│ --help                                       Show this message and exit.                                             │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ config      Configuration commands for the application. Demonstrates context sharing between subcommands.            │
│ resource    Resource management commands. Demonstrates parameter handling and nested command structure.              │
│ status      Show application status.                                                                                 │
│ testraise                                                                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Advanced Usage

### Context Proxy (`click.ctx`)

**ultraclick** provides easy access to the Click context via `click.ctx`. Import `ctx` directly when you prefer the
shorter name:

```python
import ultraclick as click
from ultraclick import ctx

# Store global state in the main group
click.ctx.meta["profile"] = profile

# Access shared state in another command
profile = click.ctx.meta["profile"]

# Access the Click command object
current_cmd = click.ctx.command

# Click exposes different types here:
# command is a Click command object; invoked_subcommand is a string or None.
current_subcmd = click.ctx.invoked_subcommand

# Invoke another command by its registered path and use its return value.
region = ctx.invoke("config.get", name="region")
```

`ctx.invoke("config.get", name="region")` starts at the root command group, initializes missing command groups through
normal option parsing, and returns the invoked command's value.

### Output Formatter (`click.output`)

`click.output` gives commands a small set of terminal-friendly messages for status lines, section headlines, warnings,
and errors. Use it for output that belongs around the command result, while the command's return value remains the main
result shown at the end.

```python
@click.command()
def status(self):
    """Show application status."""
    click.output.headline("Demo Status")
    return (
        f"Status: Running\n"
        f"Environment: {self.env}\n"
        f"Profile: {self.profile}"
    )
```

The formatter is available as `click.output`:

- `click.output.headline(msg)`
- `click.output.info(msg)`
- `click.output.success(msg)`
- `click.output.warning(msg)`
- `click.output.error(msg)`

`click.output.silence()` hides formatter messages inside a `with` block. Pass a condition to silence only when it is true:

```python
with click.output.silence(not verbose):
    click.output.info("Loading configuration")
```

UltraClick chooses the output style from the caller's terminal. In an interactive terminal, formatter methods use the
formatted, colorized terminal view. When stdout or stderr is not a TTY, when `TERM=dumb`, or when `NO_COLOR` is present,
UltraClick switches to plain text output so agents, scripts, and redirected commands receive simple text.

`ULTRACLICK_PLAIN=1` forces plain text output. `ULTRACLICK_COLORS=1` forces color output.

### Running Shell Commands

Many CLIs are wrappers around existing tools such as `git`, `docker`, or `kubectl`. `click.output.run_command(...)` gives
those subprocesses the same output behavior as the rest of the CLI: the command is shown, output streams while the command
runs, and the completed result is still available to Python code.

```python
# Simple command execution
click.output.run_command("ls -la")

# Capture output without streaming it to the screen
result = click.output.run_command("git status", silent=True)
if result.returncode == 0:
    print(result.stdout)

# Run and parse JSON output automatically
data = click.output.run_command_and_parse_json("kubectl get pods -o json")
print(f"Found {len(data['items'])} pods")
```

Use `suppress=True` to hide child output while still showing the command that is running. Use `silent=True` to make it
completely silent. Both options still capture the output. Silent and suppressed output is captured in plain text mode
unless you pass `force_pty=True`.

For normal command runs, stdout and stderr are combined in `result.stdout`; `result.stderr` is empty. JSON parsing keeps
stdout separate from stderr before parsing so warnings do not corrupt the JSON data.

## Development

### Setup

1.  Clone the repository.
2.  Install dependencies: `pip install -e .`

### Testing

Run the included unit tests using the standard Python `unittest` module:

```bash
python -m unittest
```

## License

GPLv3
