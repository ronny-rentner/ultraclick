# UltraClick for LLMs

## Overview
UltraClick is a Python library that provides a thin wrapper around `RichClick` (which in turn wraps `Click`) to enable building **Class-Based Command Line Interfaces (CLIs)**. It simplifies CLI development by allowing you to organize commands using Python classes, automatically handles output formatting, and provides a convenient proxy for the Click context.

## Key Features
- **Class-Based Structure**: Define CLI groups and subcommands using Python classes.
- **Context Proxy**: Access `click` context attributes globally via `ultraclick.ctx` without needing `click.get_current_context()`.
- **Automatic Output**: Command functions can simply return values (strings, dicts, lists), which are automatically printed nicely.
- **Nested Groups**: deeply nested subcommands are supported via nested classes.
- **Signature-Based Defaults**: `click.option` and `click.argument` wrappers automatically infer default values from the Python function signature.

## Basic Usage Pattern

### 1. Import
Always import `ultraclick` as `click` to get the enhanced features while retaining standard Click compatibility.
```python
import ultraclick as click
```

### 2. Define the Main Group
Use `@click.main_group` to decorate a class that represents your main entry point. The `__init__` method can handle global options (like `--verbose` or `--config`).

```python
@click.main_group(name="myapp")
class MyApp:
    @click.option("--verbose", is_flag=True)
    def __init__(self, verbose):
        self.verbose = verbose
        # Store in global context for subcommands
        click.ctx.meta["verbose"] = verbose
```

In ultraclick, the optional methods `__init__` and `__run__` serve different roles:
- `__init__` receives options and does setup steps.
- `__run__` is called only when no subcommand is provided.
- If `__run__` is absent, the group shows help instead.

Use `__run__` mainly for very short scripts that have no subcommands.

```python
import ultraclick as click


class SimpleApp:
    def __run__(self):
        click.output.success("Success")


if __name__ == "__main__":
    click.group_from_class(SimpleApp)()
```

With that shape, calling the script runs `__run__`.

### 3. Add Commands
Define methods within the class and decorate them with `@click.command()`.

```python
    @click.command()
    def hello(self):
        """Prints a hello message."""
        return "Hello, World!"  # Automatically printed
```

### 4. Nested Groups
Use nested classes to create subgroups.

```python
    class User:
        """User management commands."""
        
        @click.command()
        @click.argument("name")
        def create(self, name):
            return f"Created user {name}"
```

## Advanced Patterns

### Custom Behavior When No Subcommand Is Provided
By default, UltraClick shows the help message if a group is called without a subcommand. You can override this to show a status summary or perform a default action.

`if click.ctx.invoked_subcommand is None` checks whether the group was called directly without selecting any subcommand.
`click.ctx.meta['show_help_on_no_command'] = False` disables the default help screen for that no-subcommand case so your
custom action can run instead.

```python
    class Resource:
        def __init__(self):
            # Check if a subcommand was actually invoked
            if click.ctx.invoked_subcommand is None:
                # Prevent automatic help display
                click.ctx.meta['show_help_on_no_command'] = False

                # Perform custom action (e.g., print a summary)
                click.echo("Resource Dashboard: 3 active nodes")
```

This pattern is useful when the group still has subcommands, but calling the group by itself should show a summary or
perform some other custom action instead of rendering help.

## Detailed Example

Here is a comprehensive example demonstrating the structure:

```python
import ultraclick as click

@click.main_group(name="tool")
class Tool:
    """My Awesome Tool"""

    @click.option("--debug", is_flag=True)
    def __init__(self, debug):
        self.debug = debug
        click.ctx.meta["debug"] = debug

    @click.command()
    def status(self):
        """Check status"""
        debug_mode = click.ctx.meta["debug"]
        return f"System Online (Debug: {debug_mode})"

    # Nested Group: 'config'
    class Config:
        """Configuration management"""
        
        def __init__(self):
            # You can access parent context data here
            self.debug = click.ctx.meta["debug"]

        @click.command()
        @click.argument("key")
        @click.argument("value")
        def set(self, key, value):
            return f"Setting {key}={value}"
        
        @click.command()
        @click.argument("key")
        def get(self, key):
            return f"Getting value for {key}"

if __name__ == "__main__":
    Tool()
```

## API Reference

### Decorators
- **`@click.main_group`**: Decorator for the main class of the CLI.
- **`@click.command`**: Decorator for command methods.
- **`@click.option`**: Enhanced wrapper for `click.option`. Infers defaults from function signature.
- **`@click.argument`**: Enhanced wrapper for `click.argument`. Infers defaults from function signature.
- **`@click.alias(target)`**: Creates an alias for an existing command method.

### Context
- **`click.ctx`**: A proxy object that forwards attribute access to `click.get_current_context()`.
    - Usage: `click.ctx.meta["key"]`, `click.ctx.params`, `click.ctx.invoked_subcommand`.

### Help Generation
- Use class docstrings as group help text when available.
- If no real help text exists, leave the description blank instead of inventing placeholder text.
- Keep usage lines exact: only advertise `COMMAND [ARGS]...` when subcommands actually exist.

### Output
- **`click.output`**: An instance of `OutputFormatter` providing styled output methods:
    - `click.output.success(msg)`
    - `click.output.error(msg)`
    - `click.output.warning(msg)`
    - `click.output.info(msg)`
    - `click.output.headline(msg)`
    - **`click.output.run_command(cmd, headline=None, error_handling=True)`**:
        - Runs a shell command with PTY support (Unix) or subprocess (Windows).
        - Streams output in real-time while preserving colors/interactive elements.
        - Correctly forwards signals (Ctrl-C) and supports `setproctitle` in subprocesses.

Use `click.output.*(...)` instead of `print()` when you want terminal output. Structure output with methods such as
`headline`, `info`, `success`, `warning`, and `error` so the command line stays consistent. Use `click.run_command()`
or `click.output.run_command()` for external commands so command echoing and subprocess output are handled by
UltraClick instead of being printed manually.

## Best Practices
1.  **State Management**: Use `__init__` methods to initialize state for the group/subgroup.
2.  **Context Sharing**: Use `click.ctx.meta` to pass global flags (like verbose, dry-run, config paths) down to deep subcommands.
3.  **Return Values**: Prefer returning strings or data structures from commands instead of manually calling `print()`. UltraClick handles the display.
4.  **Type Hints**: Use standard Python type hints in function signatures; Click often infers types, and UltraClick leverages signature inspection.

## Library Development

If you are modifying the `ultraclick` library itself:

### Setup
1.  **Clone & Install**:
    ```bash
    git clone https://github.com/ronny-rentner/ultraclick.git
    cd ultraclick
    python -m venv venv
    source venv/bin/activate
    pip install -e .
    ```

### Testing
Run the unit tests to verify changes:
```bash
python -m unittest discover tests
```

### Code Style (Internal)
-   **Formatting**: Follow PEP 8.
-   **Imports**: Group standard library first, then third-party, then local.
-   **Docstrings**: Use triple quotes for classes and public functions.
-   **Naming**: Snake case for functions/variables, CamelCase for classes.
