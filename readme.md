# ultraclick: Object-Oriented CLI Framework for Python

[![PyPI version](https://badge.fury.io/py/ultraclick.svg)](https://badge.fury.io/py/ultraclick)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

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

Building a structured CLI with global options and nested commands is straightforward:

```python
import ultraclick as click
import pathlib

@click.main_group(name="myapp")
class MyApp:
    """My Awesome CLI Tool"""
    
    @click.option("--verbose", is_flag=True, help="Enable verbose output")
    @click.option("--config", type=pathlib.Path, default="config.yaml")
    def __init__(self, verbose, config):
        # Initialize global state here
        self.verbose = verbose
        self.config = config
        
        if verbose:
            click.output.info(f"Loading config from {config}")

    @click.command()
    def status(self):
        """Check system status."""
        return f"System is Online (Config: {self.config})"

    # Nested Group: User Management
    class User:
        """Manage users."""
        
        def __init__(self):
            # Access parent state
            self.verbose = click.ctx.meta.get("verbose")

        @click.command()
        @click.argument("username")
        def create(self, username):
            """Create a new user."""
            return f"Created user: {username}"

if __name__ == "__main__":
    MyApp()
```

## Demo Application

The repository includes a comprehensive demo that showcases ultraclick's features. Try the following commands:

```bash
./demo.py --help
./demo.py --profile production --verbose status
./demo.py resource --help
./demo.py --profile staging resource --resource-type storage list
./demo.py r l
```

## Help Output

Sample help outputs from the demo application:

### Main Help
```
 Usage: demo.py [OPTIONS] COMMAND [ARGS]...                                     
                                                                                
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

### Config Command Help
```
 Usage: demo.py config [OPTIONS] COMMAND [ARGS]...                              
                                                                                
 Configuration commands for the application. Demonstrates context sharing       
 between subcommands.                                                           
 This command group shows help when called directly (default behavior).         
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --config-dir  PATH  Configuration directory                                  │
│ --help              Show this message and exit.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ get           Get a configuration value.                                     │
│ set           Set a configuration value.                                     │
│ show          Display current configuration settings.                        │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Advanced Usage

### Context Proxy (`click.ctx`)
**ultraclick** provides a `click.ctx` proxy that forwards attributes to `click.get_current_context()`. This allows you to access context data globally without passing it as a parameter.

```python
# Access anywhere
verbose = click.ctx.meta.get("verbose")
subcommand = click.ctx.invoked_subcommand
```

### Output Formatter (`click.output`)
Access styled output methods directly:
- `click.output.success(msg)`
- `click.output.error(msg)`
- `click.output.warning(msg)`
- `click.output.info(msg)`
- `click.output.headline(msg)`

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
