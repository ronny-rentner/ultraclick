import errno
import inspect
import json
import os
import pty
import signal
import subprocess
from functools import partial, wraps
import sys
from types import SimpleNamespace


from click import shell_completion
import rich
import rich.console
import rich_click as click
from click import *

# -------------------------------
# Custom Command and Group Classes
# -------------------------------

class RichCommand(click.RichCommand):
    """
    Custom Command class that:
    1. Automatically prints the return value of the command function.
    """
    def invoke(self, ctx):
        # Execute the original invoke method and capture the return value
        result = super().invoke(ctx)

        if result is not None:
            if isinstance(result, list):
                for item in result:
                    click.echo(item)
            elif isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, list):
                        value = ", ".join(map(str, value))
                    click.echo(f"{key}: {value}")
            else:
                click.echo(result)

        return result

class RichGroup(click.RichGroup):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])

        output.info(f'\n\n"{cmd_name}" is not unique: {", ".join(matches)}\n')
        return super().get_command(ctx, cmd_name)

    def resolve_command(self, ctx, args):
        # always return the full command name
        _, cmd, args = super().resolve_command(ctx, args)
        if not cmd:
            return _, cmd, args
        return cmd.name, cmd, args

    def main(self, *args, **kwargs):
        try:
            return super().main(*args, **kwargs)
        # No exceptions are being thrown :(
        except Exception as exc:
            print(exc)
            raise

    def invoke(self, ctx):
        try:
            return super().invoke(ctx)
        except (click.UsageError, click.BadOptionUsage) as exc:
            if not getattr(exc, 'dying_and_help_printed', None):
                if ctx.invoked_subcommand:
                    subcommand = self.get_command(ctx, ctx.invoked_subcommand)
                    click.echo(subcommand.get_help(exc.ctx or ctx))
                else:
                    click.echo(self.get_help(ctx))
                exc.dying_and_help_printed = True
                # Prevent the duplicate 'usage' help because we already print it
                exc.ctx = None
            raise exc

# -------------------------------
# Decorator for Wrapping Commands with Context
# -------------------------------

def wrap_command_with_context(command_fn, instance_key=None):
    """
    Wrap a command function to inject the corresponding group instance `self` into the first argument.
    """
    @wraps(command_fn)
    @click.pass_context
    def wrapped_fn(ctx, *args, **kwargs):
        instance = ctx.meta.get(instance_key)
        if not instance:
            raise ValueError(f"Instance for key '{instance_key}' not found in context.")
        return command_fn(instance, ctx, *args, **kwargs)

    return wrapped_fn

# -------------------------------
# Group Creation Function
# -------------------------------

def group_from_class(cls, name=None, help=None, parent_key=None):
    """
    Dynamically create a Click group from a class.
    Utilizes the AutoPrintGroup to enable automatic printing of command return values.
    """
    if name is None:
        name = cls.__name__.lower()
    if help is None:
        help = cls.__doc__ or f"Commands for {cls.__name__}"

    # Construct the instance key
    instance_key = f"{parent_key}.{name}" if parent_key else name

    @click.group(name=name, help=help, cls=RichGroup)
    @click.pass_context
    @wraps(cls.__init__)
    def group_cmd(ctx, *args, **kwargs):
        # Instantiate the class and store it in the context using the instance key
        instance = cls(ctx, *args, **kwargs)
        ctx.meta[instance_key] = instance

    # Add commands dynamically
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if isinstance(attr, click.Command):
            # Wrap the command function with context
            command_fn = attr.callback
            if callable(command_fn):
                wrapped_callback = wrap_command_with_context(command_fn, instance_key=instance_key)
                attr.callback = wrapped_callback
            group_cmd.add_command(attr)

        # Handle nested groups
        if isinstance(attr, type) and issubclass(attr, object) and not attr_name.startswith("_"):
            # Nested group class
            nested_group = group_from_class(attr, name=attr_name.lower(), parent_key=instance_key)
            group_cmd.add_command(nested_group)

    return group_cmd

# -------------------------------
# Output Formatter Class
# -------------------------------

class OutputFormatter:
    """
    Handles all output formatting.
    - Only this class accesses rich.console.Console for printing.
    - No markup highlighting for commands to avoid path highlighting.
    - Consistent naming for methods: title, main_operation, environment, headline, command, error, failure, success, info, prompt.
    """

    lines = 25
    columns = 80

    def __init__(self):
        # Rich console should pick up those env variables
        if 'LINES' in os.environ:
            self.lines = os.environ["LINES"]
        else:
            self.lines = subprocess.run(['tput', 'lines'], capture_output = True, text = True).stdout.strip()
        if 'COLUMNS' in os.environ:
            self.columns = os.environ["COLUMNS"]
        else:
            self.columns = subprocess.run(['tput', 'cols'], capture_output = True, text = True).stdout.strip()

        self.console = rich.console.Console(highlight=False, file=sys.stderr)
        self._original_console_file = self.console.file
        self._silenced = False

    def title(self, project_name):
        self.console.print(f"Docker Manager: [bold magenta]{project_name}[/bold magenta]")

    def main_operation(self, operation_name):
        panel = rich.panel.Panel(
            f"{operation_name}",
            style="bold white",
            border_style="blue",
            box=rich.box.HEAVY,
            expand=False
        )
        self.console.print(panel)

    def environment(self, env_name, script_path, venv_path):
        self.headline('Setup', icon='⚙')
        self.console.print(f"Environment: {env_name}")
        self.console.print(f"Python venv: {venv_path}")

    def headline(self, message, icon="→"):
        self.console.print("")
        self.console.print(f"[bold white underline]{icon} {message}[/bold white underline]")

    def command(self, cmd):
        # Indent the command by two spaces and disable markup
        self.console.print(f"{cmd}", markup=False)

    def error(self, message):
        self.console.print(f"[bold red]✖[/bold red] {message}")

    def success(self, message):
        self.console.print(f"{message}")

    def failure(self, message):
        self.console.print(f"[bold red]✖[/bold red] {message}")

    def info(self, message):
        self.console.print(message)

    def echo(self, message):
        self.console.print(message)

    def prompt(self, message):
        # Print without newline for user input
        self.console.print(message, end='')

    def silence(self):
        """
        Context manager to temporarily silence the console output.
        """
        class SilenceContext:
            def __init__(inner_self, formatter):
                inner_self.formatter = formatter

            def __enter__(inner_self):
                if not self._silenced:
                    self._silenced = True
                    self.console.file = open(os.devnull, "w")

            def __exit__(inner_self, exc_type, exc_value, traceback):
                if self._silenced:
                    self._silenced = False
                    self.console.file.close()
                    self.console.file = self._original_console_file

        return SilenceContext(self)

    def run_command(self, command, headline=None, suppress=False, error_handling=True, parse_json=False, silent=False):
        """
        Run a shell command and capture its output, optionally streaming it.
        Simulate a TTY to preserve colored output and interactive behaviors.
        """
        command = command.strip()

        if headline:
            self.headline(headline)

        if not silent:
            self.command(command)
        else:
            suppress = True
            error_handling = False

        # Prepare the environment with color support
        env = os.environ.copy()
        env['LINES'] = self.lines
        env['COLUMNS'] = self.columns
        #env["FORCE_COLOR"] = "1"  # Enable forced color output for commands that respect it
        #env["COMPOSE_PROGRESS"] = "plain"


        stdout_bytes = bytearray()

        try:
            # Open a pseudo-terminal
            master_fd, slave_fd = pty.openpty()

            # Start the subprocess
            process = subprocess.Popen(
                command,
                shell=True,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                text=False,  # Disable text mode; we will decode bytes manually
                env=env
            )

            # Close the slave descriptor in the parent
            os.close(slave_fd)


            # Register signal handler to forward `Ctrl-C`
            def forward_signal(signum, frame):
                if process.poll() is None:  # If the process is still running
                    process.send_signal(signum)

            signal.signal(signal.SIGINT, forward_signal)

            # Read from the master PTY in real-time
            try:
                while True:
                    chunk = os.read(master_fd, 1024)  # Read up to 1024 bytes
                    if not chunk:
                        break
                    stdout_bytes.extend(chunk)
                    if not suppress:
                        print(chunk.decode("utf-8", errors="replace"), end="")  # Decode and print
            except OSError as e:
                if e.errno != errno.EIO:  # EIO means EOF
                    raise
            finally:
                os.close(master_fd)  # Ensure the fd is closed

            # Wait for the process to complete
            process.wait()

            # Handle return code
            if process.returncode != 0:
                if not suppress and error_handling:
                    self.failure(f"Command failed with return code {process.returncode}.")
                if error_handling:
                    sys.exit(process.returncode)

            # Handle JSON parsing if requested
            if parse_json:
                try:
                    return json.loads(stdout_bytes.decode("utf-8"))
                except json.JSONDecodeError as e:
                    if not suppress:
                        self.error(f"JSON decode error: {e.msg} at line {e.lineno} column {e.colno}")
                    return {}

            # Return result as a simple namespace for compatibility
            return SimpleNamespace(
                returncode=process.returncode,
                stdout=stdout_bytes.decode("utf-8", errors="replace"),  # Decode captured output
                stderr=""  # stderr is combined with stdout in PTY
            )

        except subprocess.CalledProcessError as e:
            self.error(f"Command failed with return code {e.returncode}.")
            if error_handling:
                sys.exit(1)
            return e

    def run_command_and_print_output(self, command, headline=None, error_handling=True):
        return self.run_command(command, headline, suppress=False, error_handling=error_handling)

    def run_command_and_parse_json(self, command, headline=None, error_handling=True):
        return self.run_command(command, headline, suppress=True, error_handling=error_handling, parse_json=True)



@wraps(click.option)
def option(*param_decls, **kwargs):
    """
    A drop-in replacement for `click.option` that injects default values from the
    function signature if not explicitly provided.
    """
    def decorator(func):
        # Retrieve the function's signature
        sig = inspect.signature(func)
        param_name = param_decls[0].lstrip('-').replace('-', '_')  # Normalize parameter name

        # Find the parameter in the signature and check for a default
        param = sig.parameters.get(param_name)
        if param and param.default != inspect.Parameter.empty and "default" not in kwargs:
            kwargs["default"] = param.default
            kwargs["show_default"] = True

        # Delegate to the original click.option
        return click.option(*param_decls, **kwargs)(func)

    return decorator

@wraps(click.argument)
def argument(*param_decls, **kwargs):
    """
    A drop-in replacement for `click.argument` that injects default values
    from the function signature if not explicitly provided.
    It does NOT alter 'nargs' or 'required'—you (the CLI author) must set them
    if you want an argument to accept an optional value.
    """
    def decorator(func):
        sig = inspect.signature(func)
        param_name = param_decls[0].lstrip('-').replace('-', '_')

        param = sig.parameters.get(param_name)
        if param and param.default != inspect.Parameter.empty:
            # Only set default if the user didn't already specify it
            if "default" not in kwargs:
                kwargs["default"] = param.default

            # Enable showing the default in help text
            #if "show_default" not in kwargs:
            #    kwargs["show_default"] = True

        return click.argument(*param_decls, **kwargs)(func)

    return decorator

# Create a partial function for the click.command decorator
#command = partial(click.command, cls=Command)

command = partial(click.command, cls=RichCommand)
output = OutputFormatter()
