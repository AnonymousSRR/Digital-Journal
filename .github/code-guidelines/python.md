# Python Code Generation Guidelines

## Project Structure

- Organize all projects in a clear and logical folder structure:

  ```
  project-root/
  ├── README.md
  ├── requirements.txt or pyproject.toml
  ├── src/
  │   └── mypackage/
  │       ├── __init__.py
  │       ├── module1.py
  │       └── module2.py
  ├── scripts/
  │   └── run_analysis.py
  └── tests/
      ├── __init__.py
      ├── test_module1.py
      └── test_module2.py
  ```

- Keep metadata and configuration (README, requirements, license, etc.) at the root.
- Source code must be in a dedicated package directory (like `src/mypackage/`).
- Place standalone scripts in a separate `scripts/` directory. Use `if __name__ == "__main__":` for script entry points.
- Put all tests in a parallel `tests/` directory, mirroring the code structure. Name all test files and test functions with the prefix `test_`.

## Python Code Style

- Follow PEP 8 for code style, indentation, and line lengths.
- Use auto-formatting (e.g., Black) and linting (e.g., flake8/pylint/ruff).
- **Never use a lot of comments.** Only add comments for truly non-obvious logic. Write code to be self-explanatory with clear names.
- Use snake_case for module and function names, CapWords for classes, UPPER_SNAKE_CASE for constants.
- Always use explicit and descriptive names for variables, functions, arguments, and return values.
- All import statements go at the top, grouped: standard library, third-party, then local modules, with blank lines in between. Use absolute paths and avoid wildcard imports.
- Write docstrings for all public modules, classes, functions, and methods. Prefer code clarity over excessive comments.

## Function and Parameter Practices

- **Never use mutable default arguments** (like lists or dicts). Use only `None` as a default, and create the object inside the function if needed.
- **Do not use blank strings, blank lists, or similar empty defaults** in parameters or variables.
- **Do not use `.get()` for dict access.** Always access required keys directly (e.g., `d[key]`), so missing keys raise errors.
- If a key or value is truly optional, check explicitly for `None` or absence.

## Error Handling

- Handle exceptions clearly and explicitly.
- Never use bare `except:`; always catch specific exception types.
- Log or re-raise errors as needed.
- Use `logging` (not `print()`) for any runtime output or error messages.
- Example logging pattern:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.info("Starting process")
  ```

## Formatting and Readability

- Use an auto-formatter and linter as part of your workflow and CI.
- Write small, focused functions that do one thing.
- Prefer comprehensions or built-in functions for clarity.
- Avoid deep nesting by breaking logic into helpers.
- Functions and classes must follow Single Responsibility Principle.
- Name everything clearly so the code is self-documenting.
- Use type hints where practical to clarify input and output types.

## Dependency and Configuration

- All dependencies must be listed (pinned versions) in `requirements.txt` or `pyproject.toml`.
- Always use a virtual environment.
- Use environment variables or config files for secrets or paths. Never hard-code credentials.
- Exclude all venvs, caches, and non-source artifacts via `.gitignore`.

## Testing

- Use pytest for all testing.
- Place all tests in the `tests` directory, using `test_`-prefixed files and functions.
- Name tests clearly by scenario or behavior.
- Use pytest fixtures to share setup or data, avoid duplication.
- Never mix tests with production code.
- Write both happy path and edge case tests, with clear assertions and exception checks.
- Review and maintain tests for clarity and reliability.

## General Best Practices

- Prefer Python’s standard library; only add third-party packages for clear benefit.
- Always validate and sanitize inputs. Avoid silent failures.
- Use context managers to manage resources (e.g., files).
- Write clear, meaningful commit messages and follow a team branching strategy.
- Keep project documentation and READMEs current.
- **Minimize comments**—the code itself must be clear.
- **Never use unexplained empty defaults or fallback dict access methods.**

This set of guidelines must be strictly followed for all code generation tasks. No exceptions.
