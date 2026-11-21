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

A minimal application, saved as `app.py`:

```python
import ultraclick as click


@click.main_group(name="app")
class App:
    """Minimal UltraClick application."""

    @click.command()
    def version(self):
        """Show the version."""
        return "app 1.0"


if __name__ == "__main__":
    App()
```

```console
$ python app.py version
app 1.0
```

The included [demo.py](./demo.py) is a larger example demonstrating global options, nested commands, aliases, and a
`--json` option.

## Help Output

**ultraclick** leverages RichClick to produce beautiful help screens automatically.

```
$ ./demo.py

 Usage: demo.py [OPTIONS] [COMMAND] [ARGS]...

 Main demo application showcasing ultraclick's features.

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --verbose                                    Enable verbose output                                                   │
│ --json                                       Print results as JSON                                                   │
│ --profile  TEXT                              Configuration profile to use [default: default]                         │
│ --env      [development|staging|production]  Environment to run in [default: development]                            │
│ --version                                    Show the version and exit.                                              │
│ --help                                       Show this message and exit.                                             │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ask          Run a child command that reads a line from the keyboard.                                                │
│ config       Configuration commands for the application. Demonstrates context sharing between subcommands.           │
│ echo         Print the given text.                                                                                   │
│ error        Test error message design                                                                               │
│ resource     Resource management commands. Demonstrates parameter handling and nested command structure.             │
│ status       Show application status.                                                                                │
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
- `click.output.image(path)`

`click.output.image(path)` shows a PNG file inline in terminals that support the Kitty graphics protocol. Plain text
output prints the path instead.

`click.output.silence()` hides formatter messages inside a `with` block. Pass a condition to silence only when it is true:

```python
with click.output.silence(not verbose):
    click.output.info("Loading configuration")
```

UltraClick chooses the output style from the caller's terminal. In an interactive terminal, formatter methods use the
formatted, colorized terminal view. When stdout or stderr is not a TTY, when `TERM=dumb`, or when `NO_COLOR` is present,
UltraClick switches to plain text output so agents, scripts, and redirected commands receive simple text.

`ULTRACLICK_PLAIN=1` forces plain text output. `ULTRACLICK_COLORS=1` forces color output.

`click.output.plain` is `True` in plain text output, so CLI code can adapt its own output, for example skip a progress
display.

`click.output.result(value)` prints a command's return value to stdout: a list one item per line, a dict as `key: value`
lines, anything else as text. `click.JsonOutputFormatter` prints it as JSON instead and its messages as plain text.
`click.use_formatter(cls)` replaces `click.output` with a new instance of `cls`, for example for a `--json` option:

```python
@click.option("--json", "json_output", is_flag=True, help="Print results as JSON")
def __init__(self, json_output):
    if json_output:
        click.use_formatter(click.JsonOutputFormatter)
```

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
