# UltraClick for LLMs

## Rules

1. Read `readme.md` fully as basis of this file. This file provides information beyond `readme.md`.

## Generation Guidance

- Import UltraClick as `click`.
- Prefer the shortest class structure that matches the CLI shape.
- Use one class per command group.
- Use nested classes for subcommand groups instead of manual registration code.
- Put group-level options on `__init__`.
- Put command-local options and arguments on the command method.
- Decorate command methods with `@click.command()`.
- Use `@click.main_group` for normal CLIs.
- Use `click.group_from_class(...)` with `__run__` only for very small scripts with no subcommands.

## State And Context

- Keep group-local state on `self`.
- Use `click.ctx.meta` only for state that must cross group boundaries.
- Prefer `click.ctx` over `click.get_current_context()` when generated code needs current context data.

## Output

- Prefer returning values from commands instead of printing manually.
- Use `click.output.*(...)` only when styled terminal output is required.
- Use `click.output.run_command(...)` for external commands so UltraClick handles command echoing and output capture.
- `click.output.run_command(...)` is synchronous. It waits for the child process to finish and is not a background-job API.

## `__init__` And `__run__`

- `__init__` receives options and performs setup.
- `__run__` is called only when no subcommand was provided.
- If `__run__` is absent, the group shows help instead.
- Use `__run__` for true default actions, not as a substitute for a clear subcommand structure.

## No-Command Customization

- If a group has subcommands but should do something custom when called directly, check `click.ctx.invoked_subcommand`.
- In that case, set `click.ctx.meta["show_help_on_no_command"] = False` before running the custom action.

## Output Mode Overrides

- `ULTRACLICK_PLAIN=1` forces plain output.
- `ULTRACLICK_COLORS=1` forces Rich output and overrides plain-mode detection, including `ULTRACLICK_PLAIN`.
- In plain mode, `click.output.run_command(...)` uses the non-PTY subprocess path and passes plain-output environment settings to child commands.

## Efficiency Checklist

1. Read `readme.md` fully.
2. Build the command tree directly as classes and nested classes.
3. Put setup in `__init__`.
4. Return values directly for simple output.
5. Use `click.ctx.meta` only when state must cross group boundaries.
6. Use `click.output.run_command(...)` for external commands.
7. Add `__run__` only when the no-subcommand case should execute code.
