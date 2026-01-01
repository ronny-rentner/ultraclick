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
- [Demo Application](#demo-application)
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

Here is a complete, runnable example demonstrating how to build a structured CLI with global options and nested commands. This code corresponds to a simplified version of the included `demo.py`.

```python
import ultraclick as click
import pathlib

# Nested Group: Configuration
class ConfigCommand:
    """Configuration management."""
    
    @click.option("--config-dir", type=pathlib.Path, default="./config")
    def __init__(self, config_dir):
        # State specific to this group
        self.config_dir = config_dir
        # Access shared global state
        self.profile = click.ctx.meta["profile"]

    @click.command()
    def show(self):
        """Show current configuration."""
        return f"Profile: {self.profile}, Dir: {self.config_dir}"

# Main Application
@click.main_group(name="demo")
class MainApp:
    """Main demo application."""
    
    # Register nested groups as class attributes
    config = ConfigCommand

    @click.option("--verbose", is_flag=True, help="Enable verbose output")
    @click.option("--profile", default="default", help="Configuration profile")
    def __init__(self, verbose, profile):
        # Initialize global state
        self.verbose = verbose
        self.profile = profile
        
        # Share state with subcommands via context metadata
        click.ctx.meta["verbose"] = verbose
        click.ctx.meta["profile"] = profile
        
        if verbose:
            click.output.info(f"Verbose mode enabled (Profile: {profile})")

    @click.command()
    def status(self):
        """Show application status."""
        return f"Status: Running (Profile: {self.profile})"

if __name__ == "__main__":
    MainApp()
```

### Running the Example

```console
$ python demo.py --verbose status
ℹ Verbose mode enabled (Profile: default)
Status: Running (Profile: default)

$ python demo.py config show
Profile: default, Dir: config

$ python demo.py --profile production config --config-dir /etc/app show
Profile: production, Dir: /etc/app
```

## Demo Application

The repository includes a comprehensive `demo.py` that expands on the quick start with more complex features. Try the following commands to explore:

```bash
./demo.py --help
./demo.py resource --help
./demo.py --profile staging resource --resource-type storage list
./demo.py r l  # Command abbreviation!
```

## Help Output

**ultraclick** leverages RichClick to produce beautiful help screens automatically.

### Main Help
```
 Usage: demo [OPTIONS] COMMAND [ARGS]...                                     
                                                                                
 Main demo application.                                                       
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --verbose                                    Enable verbose output           │
│ --profile  TEXT                              Configuration profile           │
│ --help                                       Show this message and exit.     │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ config      Configuration management.                                        │
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