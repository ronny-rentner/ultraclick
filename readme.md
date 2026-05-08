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
    @click.option("--config-dir", type=pathlib.Path, help="Configuration directory")
    def __init__(self, config_dir="./config"):
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
                  help="Type of resource to manage")
    def __init__(self, resource_type="server"):
        self.resource_type = resource_type

        # Access shared data from parent command
        self.profile = click.ctx.meta["profile"]

    @click.command()
    @click.argument("name")
    @click.option("--size", help="Resource size (small, medium, large)")
    @click.option("--region", help="Deployment region")
    def create(self, name, size="medium", region="us-east"):
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
    @click.option("--profile", help="Configuration profile to use")
    @click.option("--env",
                 type=click.Choice(['development', 'staging', 'production']),
                 help="Environment to run in")
    @click.version_option(version="1.0")
    def __init__(self, verbose, profile="default", env="development"):
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

Plain text output is selected automatically when stdout or stderr is not a TTY, when `TERM=dumb`, or when `NO_COLOR`
is present. Set `ULTRACLICK_PLAIN=1` to force plain Click-style output even in an interactive terminal. Set
`ULTRACLICK_COLORS=1` to force Rich output and override plain-mode detection, including `ULTRACLICK_PLAIN`.

Option defaults are shown in help output when an option has a default value, whether that default was declared in the
decorator or inferred from the Python signature. If you need different behavior, pass Click's `show_default=...`
explicitly on that option.

The preferred UltraClick style is to put defaults on the Python function signature and keep `@click.option(...)`
focused on option names, types, and help text. Decorator defaults still work, but signature defaults keep the Python
call shape and CLI help output driven by the same source.

### Main Help
```
 Usage: demo [OPTIONS] COMMAND [ARGS]...                                     
                                                                                
 Main demo application showcasing ultraclick's features.                        
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --verbose                                    Enable verbose output           │
│ --profile  TEXT                              Configuration profile to use    │
│                                               [default: default]            │
│ --env      [development|staging|production]  Environment to run in          │
│                                               [default: development]        │
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

## Usage

Some ultraclick usage patterns.

### Group Initialization And Default Actions

In ultraclick, the optional methods `__init__` and `__run__` serve different roles:
 * `__init__` receives options and does setup steps. 
 * `__run__` is called only when no subcommand is provided.
 * If `__run__` is absent, the group shows help instead.

```python
@click.main_group(name="simple")
class SimpleApp:
    @click.option("--profile")
    def __init__(self, profile):
        self.profile = profile

    def __run__(self):
        return f"Running with profile {self.profile}"
```

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

When plain mode is active, `click.output` switches to the plain formatter and `click.output.run_command(...)` uses the
non-PTY subprocess path. UltraClick also passes `TERM=dumb`, `NO_COLOR=1`, and `CLICOLOR=0` to child commands so
downstream tools produce plain output too.

## Tips

### Flexible Parameter Ordering
By default, **ultraclick** allows global options to be placed after subcommands (e.g., `./demo.py status --verbose`). It includes robust logic to ensure `--help` flags are correctly routed to the target command even when deep in the hierarchy.

### Defaults In Help
By default, option help shows the effective default value. The preferred pattern is to put that default on the Python
function signature, for example `def __init__(self, profile="default")`, and let UltraClick's `@click.option(...)`
wrapper expose it in the CLI. Explicit decorator defaults still work when you need them.

### Shell Completion
Generate a shell completion script by setting the command's completion environment variable to `<shell>_source`.

```bash
_DEMO_PY_COMPLETE=bash_source ./demo.py
_DEMO_PY_COMPLETE=zsh_source ./demo.py
_DEMO_PY_COMPLETE=fish_source ./demo.py
```

The variable name is `_<COMMAND>_COMPLETE`, with the command name uppercased and dashes or dots changed to underscores.
For a command named `my-tool`, use `_MY_TOOL_COMPLETE`.

## Development

### Setup
1.  Clone the repository.
2.  Install dependencies: `pip install -e .`

### Testing
Run the included unit tests through the project's unittest entrypoint:
```bash
python -m tests
```

### Release
Releases are tag-driven through the GitHub Actions release workflow.

The workflow runs only when a Git tag matching `v*` is pushed.

1.  Bump the package version in `pyproject.toml`.
2.  Commit and push that change to `main`.
3.  Create a matching tag such as `v0.2.4`.
4.  Push the tag.
5.  Verify the GitHub Actions `Release` workflow run and wait for it to finish.

```bash
git tag v0.2.4
git push origin v0.2.4
gh run list -L 10
gh run watch <run-id> --exit-status
```

## License

GPLv3
