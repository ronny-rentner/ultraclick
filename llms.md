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

### Output
- **`click.output`**: An instance of `OutputFormatter` providing styled output methods:
    - `click.output.success(msg)`
    - `click.output.error(msg)`
    - `click.output.warning(msg)`
    - `click.output.info(msg)`
    - `click.output.headline(msg)`

## Best Practices
1.  **State Management**: Use `__init__` methods to initialize state for the group/subgroup.
2.  **Context Sharing**: Use `click.ctx.meta` to pass global flags (like verbose, dry-run, config paths) down to deep subcommands.
3.  **Return Values**: Prefer returning strings or data structures from commands instead of manually calling `print()`. UltraClick handles the display.
4.  **Type Hints**: Use standard Python type hints in function signatures; Click often infers types, and UltraClick leverages signature inspection.