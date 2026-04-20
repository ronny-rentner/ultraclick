import errno
import inspect
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
from functools import partial, wraps
from types import SimpleNamespace

# Explicit UltraClick overrides win over terminal heuristics.
FORCE_COLORS = os.environ.get('ULTRACLICK_COLORS', '').lower() in {'1', 'true', 'yes', 'on'}
FORCE_PLAIN_TEXT = os.environ.get('ULTRACLICK_PLAIN', '').lower() in {'1', 'true', 'yes', 'on'}

# Plain mode follows the same broad style many CLIs use unless colors are explicitly forced.
PLAIN_TEXT_MODE = not FORCE_COLORS and (
    FORCE_PLAIN_TEXT
    or 'NO_COLOR' in os.environ
    or os.environ.get('TERM') == 'dumb'
    or not sys.stdout.isatty()
    or not sys.stderr.isatty()
)

if PLAIN_TEXT_MODE:
    import click
    # Plain mode keeps the rest of the module uniform by mapping Rich class names
    # back to stock Click classes when rich_click is not in use.
    click.RichCommand = click.Command
    click.RichGroup = click.Group
else:
    import rich
    import rich.console
    import rich.panel
    import rich_click as click
from click import *

import codecs

# Only import pty on platforms that support it (Unix-like systems)
if os.name != 'nt':  # Not Windows
    import pty
    import termios


class PlainTextConsole:
    """
    Minimal console adapter for plain formatter output.
    It accepts the `Console.print()` parameters used in this file and writes plain text.
    """

    def __init__(self, file):
        self.file = file

    def print(self, *objects, sep=' ', end='\n', **kwargs):
        # Formatter methods keep calling `self.console.print(...)` unchanged.
        print(*objects, sep=sep, end=end, file=self.file)


class ClickContextProxy:
    """
    A magic proxy to Click's current context.
    Allows you to write `ctx.meta["env"]` or `ctx.params["target"]`
    without manually calling `click.get_current_context()` every time.
    """

    def __getattr__(self, attr):
        ctx = click.get_current_context()
        return getattr(ctx, attr)

    def __getitem__(self, key):
        ctx = click.get_current_context()
        return ctx[key]

    # TODO: This method crashes because click.Context is not callable.
    #       Keeping it commented out for now to verify no downstream usage relies on it.
    # def __call__(self, *args, **kwargs):
    #     ctx = click.get_current_context()
    #     return ctx(*args, **kwargs)

    def __repr__(self):
        ctx = click.get_current_context()
        return repr(ctx)

ctx = ClickContextProxy()

class RichCommand(click.RichCommand):
    """
    Custom Command class that automatically prints the return value of the command function.
    """

    def __init__(self, *args, alias=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.alias = alias

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
    source_class = None
    instance_key = None
    group_kwargs = None

    def collect_usage_pieces(self, ctx):
        pieces = click.Command.collect_usage_pieces(self, ctx)
        if self.list_commands(ctx):
            pieces.append(self.subcommand_metavar)
        return pieces

    def parse_args(self, ctx, args):
        #output.info(f"BEF RichGroup.parse_args(group={self.name}) ctx.params={ctx.params} args={args}")
        try:
            rv = super().parse_args(ctx, args)
        except click.UsageError:
            # Deferred help marks the context first so nested `--help target` forms keep working.
            # Required __init__ arguments must not win over that explicit help request.
            if ctx.meta.get('ultraclick_help_requested'):
                click.echo(self.get_help(ctx))
                ctx.exit(0)
            raise
        #output.info(f"AFT RichGroup.parse_args(group={self.name}) ctx.params={ctx.params} ctx.meta={ctx.meta}")
        
        if self.source_class and self.instance_key and self.instance_key not in ctx.meta:
            # Instantiate the class with parsed options
            instance = self.source_class(**ctx.params)
            ctx.meta[self.instance_key] = instance
            self._discover()
            
        return rv

    def _discover(self):
        #output.info(f"RichGroup._discover(group={self.name}, source_class={self.source_class} context_settings={self.context_settings})")
        if not self.source_class:
            return

        # Add commands dynamically
        for attr_name in dir(self.source_class):
            attr = getattr(self.source_class, attr_name)
            if isinstance(attr, click.Command):
                # Avoid redundant adding
                cmd_name = getattr(attr, 'name', attr_name)
                if cmd_name in self.commands:
                    continue

                # Wrap the command function with context
                command_fn = attr.callback
                #TODO: Is it an error if it's not callable?
                if callable(command_fn):
                    wrapped_callback = wrap_command_with_context(command_fn, instance_key=self.instance_key)
                    attr.callback = wrapped_callback

                #if attr_name != command_fn.__name__:
                if attr.alias:
                    #print('alias: ', attr, attr_name, getattr(attr, 'name', attr_name), command_fn.__name__)
                    #alias_cmd = alias_command(attr_name, attr)
                    self.add_command(attr, name=attr_name)
                    continue
                else:
                    #print('add_command: ', attr, '1', attr_name, '2', getattr(attr, 'name', ''), '3', command_fn.__name__)
                    # name parameter has priority, otherwise take the command function name
                    self.add_command(attr, name=getattr(attr, 'name', attr_name))

            # Handle nested groups
            if isinstance(attr, type) and issubclass(attr, object) and not attr_name.startswith("_"):
                # Nested group class
                cmd_name = attr_name.lower()
                if cmd_name not in self.commands:
                    nested_group = group_from_class(attr, name=cmd_name, parent_key=self.instance_key, **(self.group_kwargs or {}))
                    self.add_command(nested_group)

    def get_help_option(self, ctx):
        help_options = self.get_help_option_names(ctx)
        if not help_options or not self.add_help_option:
            return None

        if self._help_option is None:
            # Use help_option decorator to create the option with our custom callback
            from click.decorators import help_option
            
            # Apply decorator to self (Command) which adds the param to self.params
            help_option(*help_options, callback=deferred_help_callback)(self)
            
            # Retrieve the last added parameter (which is our help option) and remove it
            # because get_help_option is supposed to return it, not register it permanently
            # (although click core does caching, we just need the object here)
            self._help_option = self.params.pop()

        return self._help_option

    def get_command(self, ctx, cmd_name):
        #output.info(f"get_command {cmd_name} ctx.params={ctx.params}")
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])

        click.echo(f'\n\n"{cmd_name}" is not unique: {", ".join(matches)}\n')
        return super().get_command(ctx, cmd_name)

    def resolve_command(self, ctx, args):
        #output.info(f"resolve_command1 - args: {args} ctx.params={ctx.params}")
        # always return the full command name
        _, cmd, args = super().resolve_command(ctx, args)
        #output.info(f"resolve_command2 -  {_} {cmd} {args}")
        if not cmd:
            return _, cmd, args
        return cmd.name, cmd, args

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
            
            # If help was explicitly requested, suppress the error and exit cleanly
            if ctx.meta.get('ultraclick_help_requested'):
                ctx.exit(0)

            raise exc

def wrap_command_with_context(command_fn, instance_key=None):
    """
    Wrap a command function to inject the corresponding group instance `self`
    into the first argument.

    Uses ClickContextProxy instead of passing ctx as a second parameter.
    """
    @wraps(command_fn)
    @click.pass_context
    def wrapped_fn(ctx, *args, **kwargs):
        # Check if help was requested for a single command (no group)
        if ctx.meta.get('ultraclick_help_requested'):
            click.echo(ctx.get_help())
            ctx.exit()

        instance = ctx.meta.get(instance_key)
        if not instance:
            raise ValueError(f"Instance for key '{instance_key}' not found in context.")

        # Unwrap Click's @pass_context wrapper to avoid injecting ctx twice
        actual_fn = getattr(command_fn, "__wrapped__", command_fn)
        return actual_fn(instance, *args, **kwargs)

    return wrapped_fn

def alias_command(alias_name, target_command, alias_help=None):
    # Copy all parameters from the target command to the alias
    params = target_command.params

    @click.command(name=alias_name, params=params, hidden=True, cls=RichCommand)
    @click.pass_context
    def _alias(ctx, *args, **kwargs):
        return ctx.forward(target_command)

    _alias.callback.__name__ = alias_name

    return _alias

def alias(cmd):
    @click.command(params=cmd.params, hidden=True, cls=RichCommand, alias=True)
    @click.pass_context
    def _alias(self, *args, **kwargs):
        return click.get_current_context().forward(cmd)
    return _alias

def deferred_help_callback(ctx, param, value):
    if value and not ctx.resilient_parsing:
        ctx.meta['ultraclick_help_requested'] = True

def main_group(*args, **kwargs):
    """
    Convenience class decorator for creating a command group from a class.

    Accepts the same parameters as group_from_class() but can be used as a decorator.
    """
    def decorator(cls):
        return group_from_class(cls, *args, **kwargs)
    return decorator

def group_from_class(cls, name=None, help=None, parent_key=None, initial_ctx_meta=None, **kwargs):
    """
    Dynamically create a Click command group from a class.

    Args:
        cls: The class to convert into a Click group
        name: The name of the command (defaults to lowercase class name)
        help: Help text for the command (defaults to class docstring)
        parent_key: Key to use for parent command in context metadata
        context_settings: Dict with context settings like 'meta', 'allow_interspersed_args', etc.
    """
    if name is None:
        name = cls.__name__.lower()
    if help is None:
        help = inspect.getdoc(cls) or ""

    # Construct the instance key
    instance_key = f"{parent_key}.{name}" if parent_key else name

    # Adjust some default group settings
    kwargs.setdefault('invoke_without_command',  True)

    context_settings = kwargs.setdefault('context_settings', {})
    context_settings.setdefault('allow_interspersed_args', True)

    # TODO: It's strange that we have to set these two options and they seem
    #       to not do what they say but merely make `allow_interspersed_args` actually work
    context_settings.setdefault('ignore_unknown_options',  True)
    context_settings.setdefault('allow_extra_args',        True)

    @click.group(name=name, help=help, cls=RichGroup, **kwargs)
    @click.pass_context
    @wraps(cls.__init__)
    def group_cmd(ctx, *args, **kwargs):
        if instance_key in ctx.meta:
            instance = ctx.meta[instance_key]
        else:
            if not ctx.meta and initial_ctx_meta:
                ctx.meta.update(initial_ctx_meta)

            # Set a flag in the context that we'll use to decide whether to show help
            ctx.meta['show_help_on_no_command'] = True

            # Instantiate the class and store it in the context using the instance key
            instance = cls(*args, **kwargs)
            ctx.meta[instance_key] = instance

        # Handle execution if no subcommand was invoked
        if ctx.invoked_subcommand is None:
            if hasattr(instance, "__run__") and not ctx.meta.get('ultraclick_help_requested'):
                return instance.__run__()

            if ctx.meta.get('show_help_on_no_command', True) or ctx.meta.get('ultraclick_help_requested'):
                click.echo(ctx.get_help())

    # Attach metadata for early initialization and discovery
    group_cmd.source_class = cls
    group_cmd.instance_key = instance_key
    group_cmd.group_kwargs = kwargs

    # Perform initial discovery
    group_cmd._discover()

    return group_cmd

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
            self.lines = int(os.environ["LINES"])
        else:
            self.lines = shutil.get_terminal_size().lines

        if 'COLUMNS' in os.environ:
            self.columns = int(os.environ["COLUMNS"])
        else:
            self.columns = shutil.get_terminal_size().columns

        self.console = rich.console.Console(highlight=False, file=sys.stderr)
        self._original_console_file = self.console.file
        self._silenced = False
        self.shell = self._find_shell()

    def _find_shell(self):
        """Find a suitable shell, preferring bash over sh for better proctitle support."""
        for s in ['/bin/bash', '/usr/bin/bash', '/bin/sh']:
            if os.path.exists(s):
                return s
        return '/bin/sh'

    def title(self, title, project_name):
        self.console.print(f"{title}: [bold magenta]{project_name}[/bold magenta]")

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

    def warning(self, message):
        self.console.print(f"[bold yellow]✖[/bold yellow] {message}")

    def success(self, message):
        self.console.print(f"[bold green]{message}[/bold green]")

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
        Simulate a TTY to preserve colored output and interactive behaviors on Unix systems.
        Use a simpler approach on Windows.
        """
        # Accept argv-style input so callers can describe command boundaries directly and let
        # UltraClick assemble the shell string in one place before handing it to the PTY runner.
        if isinstance(command, (list, tuple)):
            command = shlex.join([str(part) for part in command])

        # Keep string input working exactly as before so existing callers can continue passing
        # prebuilt shell commands without any behavior change.
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
        env['LINES'] = str(self.lines)
        env['COLUMNS'] = str(self.columns)
        if PLAIN_TEXT_MODE:
            # Plain mode should propagate the same terminal expectations to child processes.
            env['TERM'] = 'dumb'
            env['NO_COLOR'] = '1'
            env['CLICOLOR'] = '0'
            env.pop('CLICOLOR_FORCE', None)
        #env["FORCE_COLOR"] = "1"  # Enable forced color output for commands that respect it
        #env["COMPOSE_PROGRESS"] = "plain"

        # Plain mode avoids PTYs so subprocesses behave like non-interactive plain-text tools.
        if PLAIN_TEXT_MODE or os.name == 'nt':
            result = subprocess.run(command, shell=True, text=True, capture_output=True, env=env)
            if not suppress:
                print(result.stdout, end="")
                print(result.stderr, end="", file=sys.stderr)
            # Handle return code
            if result.returncode != 0:
                if not suppress and error_handling:
                    self.failure(f"Command failed with return code {result.returncode}.")
                if error_handling:
                    sys.exit(result.returncode)

            # Handle JSON parsing if requested
            if parse_json:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    if not suppress:
                        self.error(f"JSON decode error: {e.msg} at line {e.lineno} column {e.colno}")
                    return {}

            return SimpleNamespace(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr
            )

        # Use PTY on Unix systems
        stdout_bytes = bytearray()

        try:
            # Open a pseudo-terminal
            master_fd, slave_fd = pty.openpty()

            # Start the subprocess
            process = subprocess.Popen(
                command,
                shell=True,
                executable=self.shell,
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
                    # Send Ctrl-C to the PTY instead of the process
                    # This ensures the signal reaches the foreground process group
                    os.write(master_fd, b'\x03')

            signal.signal(signal.SIGINT, forward_signal)

            decoder = codecs.getincrementaldecoder("utf-8")()
            buffer = bytearray()

            # Read from the master PTY in real-time
            try:
                while True:
                    chunk = os.read(master_fd, 1024)  # Read up to 1024 bytes
                    if not chunk:
                        break
                    stdout_bytes.extend(chunk)
                    text = decoder.decode(chunk)
                    if not suppress:
                        print(text, end="")
                        #print(chunk.decode("utf-8", errors="replace"), end="")  # Decode and print
            except OSError as e:
                if e.errno != errno.EIO:  # EIO means EOF
                    raise
            finally:
                if not suppress:
                    print(decoder.decode(b"", final=True), end="")
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


class PlainOutputFormatter(OutputFormatter):
    """
    Plain text formatter for LLM and machine-oriented script output.
    It keeps the same public API as OutputFormatter while rendering only simple text.
    """

    def __init__(self):
        if 'LINES' in os.environ:
            self.lines = int(os.environ["LINES"])
        else:
            self.lines = shutil.get_terminal_size().lines

        if 'COLUMNS' in os.environ:
            self.columns = int(os.environ["COLUMNS"])
        else:
            self.columns = shutil.get_terminal_size().columns

        # Plain mode must not touch Rich imports, so it initializes its own console directly.
        self.console = PlainTextConsole(sys.stderr)
        self._original_console_file = self.console.file
        self._silenced = False
        self.shell = self._find_shell()

    def title(self, title, project_name):
        self.console.print(f"{title}: {project_name}")

    def main_operation(self, operation_name):
        self.console.print(f"== {operation_name} ==")

    def environment(self, env_name, script_path, venv_path):
        self.headline('Setup')
        self.console.print(f"Environment: {env_name}")
        self.console.print(f"Python venv: {venv_path}")

    def headline(self, message, icon="#"):
        self.console.print("")
        self.console.print(f"{icon} {message}")

    def error(self, message):
        self.console.print(f"ERROR: {message}")

    def warning(self, message):
        self.console.print(f"WARNING: {message}")

    def success(self, message):
        self.console.print(f"OK: {message}")

    def failure(self, message):
        self.console.print(f"ERROR: {message}")



@wraps(click.option)
def option(*param_decls, **kwargs):
    """
    A drop-in replacement for `click.option` that injects default values from the
    function signature if not explicitly provided.
    """
    def decorator(func):
        # UltraClick keeps option help honest by showing defaults whenever a default
        # exists and the caller did not make an explicit show_default choice.
        # This applies both to defaults declared in the decorator itself and to
        # defaults inferred from the Python signature below.
        if "default" in kwargs and "show_default" not in kwargs:
            kwargs["show_default"] = True

        # Retrieve the function's signature
        sig = inspect.signature(func)
        param_name = param_decls[0].lstrip('-').replace('-', '_')  # Normalize parameter name

        # Find the parameter in the signature and check for a default
        param = sig.parameters.get(param_name)
        if param and param.default != inspect.Parameter.empty and "default" not in kwargs:
            kwargs["default"] = param.default
            if "show_default" not in kwargs:
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

command = partial(click.command, cls=RichCommand)
output = PlainOutputFormatter() if PLAIN_TEXT_MODE else OutputFormatter()

# Short alias
run = output.run_command_and_print_output
