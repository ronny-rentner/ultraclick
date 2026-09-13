# Working with UltraClick

## Repository Layout

- `src/ultraclick/__init__.py` contains the public API and framework implementation.
- `demo.py` is the runnable reference CLI.
- `tests/` contains the test suite.
- `pyproject.toml` defines package metadata and dependencies.

Read [readme.md](./readme.md) for library usage and [llms.md](./llms.md) for detailed behavior.

## Python Environment

Use `venv/bin/python` for Python commands from the repository root. The repository has a local `venv`; shell activation is not required.

Installation instructions are in [readme.md](./readme.md#installation).

## Code Changes

Keep runtime changes in `src/ultraclick/__init__.py`, alongside the existing `RichCommand`, `RichGroup`, and decorator helpers. Extend the existing Click and RichClick implementation instead of introducing a second implementation or scattering small modules.

Read each file fully before editing and follow its existing style. Use 4-space indentation, module-level imports, `snake_case` for functions and variables, and `CamelCase` for classes. Keep decorators next to the methods they configure. Do not introduce a formatter or reformat unrelated code.

Keep `demo.py` aligned with the library's behavior.

## Behavior to Preserve

- `__init__` receives options and performs setup.
- `__run__` runs only when no subcommand is provided. Without it, the group shows help.
- Usage includes `COMMAND [ARGS]...` only when subcommands exist.
- Class docstrings can supply help text. Empty descriptions stay empty.

## Tests

Run from the repository root:

```bash
./venv/bin/python -m unittest
```

Add or update `unittest` coverage for every behavior change. Prefer CLI tests that check exit codes, stdout, and stderr; `tests/test_demo.py` provides examples. Name tests `test_<behavior>` and keep fixtures lightweight.

For parsing and help fixes, cover the direct command and supported abbreviated or reordered forms.

## Documentation

- `readme.md` explains installation and library usage to users.
- `llms.md` states precise behavior needed to generate code using UltraClick.
- `AGENTS.md` explains how to work with this repository, including running tests and making changes.

Keep information in the document that serves its audience. Link to existing instructions instead of duplicating them.

Explain UltraClick's behavior directly. Preserve established README wording when it is more precise. Use short examples to clarify initialization, default actions, and help generation. Present `__run__` primarily as the default-action hook for short scripts without subcommands.

## Commits and Pull Requests

Use short, capitalized, imperative commit titles. In pull requests, explain the user-visible change and report the tests run. Include output examples when command output or help text changes.
