# Repository Guidelines

## Project Structure & Module Organization
Core library code lives under `src/ultraclick/__init__.py`. The public API and most framework behavior are defined there, so keep new runtime code close to the existing `RichCommand`, `RichGroup`, and decorator helpers instead of scattering small modules. `demo.py` is the runnable reference CLI and should stay aligned with real behavior. Tests live in `tests/`, with `tests/test_demo.py` exercising the demo through subprocess calls. Project metadata and dependencies are defined in `pyproject.toml`.

## Build, Test, and Development Commands
Create an editable environment with `pip install -e .` and include test helpers with `pip install -e .[test]`. Run the demo locally with `python demo.py --help` or a concrete command such as `python demo.py status`. Run the test suite with `python -m unittest discover -s tests -v`. For packaged-install checks, use `python -m pip install .` in a clean virtualenv.

## Coding Style & Naming Conventions
Follow the existing Python style: 4-space indentation, module-level imports, and descriptive `snake_case` names for functions, methods, and variables. Use `CamelCase` for command/group classes such as `MainApp` and `ResourceCommand`. Keep decorators adjacent to the method they configure, and extend the current Click and RichClick patterns instead of introducing parallel abstractions. There is no formatter or linter config in the repository, so make formatting match nearby code and keep lines readable.

## Documentation Roles
Do treat each top-level doc as serving a different audience. [`readme.md`](./readme.md) is the user-facing explanation of the library and should read like upstream product documentation. [`llms.md`](./llms.md) is the precise behavioral companion for code generation and should make implicit contracts explicit. [`AGENTS.md`](./AGENTS.md) is the repository working agreement for contributors and agents and should capture repo-specific editing, testing, and documentation expectations.

## UltraClick Semantics To Preserve
Do document ultraclick from the library's own perspective. In ultraclick, the optional methods `__init__` and `__run__` serve different roles: `__init__` receives options and does setup steps, `__run__` is called only when no subcommand is provided, and if `__run__` is absent, the group shows help instead. Do present `__run__` primarily as the default-action hook for very short scripts that have no subcommands. Do keep help text exact: usage lines should only advertise `COMMAND [ARGS]...` when subcommands actually exist, class docstrings are valid help text, and empty descriptions should stay empty instead of being replaced with placeholder prose.

## Documentation Style
Do prefer the wording already established in [`readme.md`](./readme.md) when it states a feature more exactly than a rewrite would. Do explain features directly instead of introducing extra categories that ultraclick itself does not have. Do add short concrete examples when behavior is easy to misunderstand, especially around group initialization, default actions, and help generation.

## Testing Guidelines
Add or update `unittest` coverage for every behavior change. Prefer end-to-end CLI assertions that run `demo.py` and verify exit codes, stdout, and stderr, matching the current test style. Name new tests `test_<behavior>` and keep fixtures lightweight. When fixing parsing or help behavior, include both the direct command form and the abbreviated or reordered argument form if supported.

## Commit & Pull Request Guidelines
Recent commits use short imperative subjects such as `Implement dynamic command discovery and __run__ hook` and `Fix ImportError by using help_option decorator`. Keep commit titles concise, capitalized, and action-first. Pull requests should explain the user-visible CLI change, list added or updated tests, and include terminal output snippets when help text or command output changes.
