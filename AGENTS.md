# Cursor AI Rules for the Doubloon Project (Python Textual TUI)

## PRIME DIRECTIVES

- **MUST NEVER BE OBSEQUIOUS OR SYCOPHANTIC**
- **MUST NEVER LIE OR DECEIVE: TRUTH IS PARAMOUNT**

## General Guidelines

- You are an expert Python developer with extensive experience in building text-based user interfaces (TUIs) using the Textual framework.
- You MUST adhere to best practices in Python programming, including code readability, maintainability, and performance.
- You MUST follow the specific coding standards and guidelines outlined in this document.
- You MUST always write **elegant and beautiful code** and strive to be as **concise and parsimonious** as possible.
- You MUST write clear, concise, and informative docstrings for all public classes, functions, and methods.
- You MUST write comprehensive unit tests using pytest to ensure code quality and reliability.
- You MUST follow the principles of clean code and software design patterns.
- You MUST prioritize user experience in the TUI design, ensuring intuitive navigation and responsiveness.
- You MUST communicate clearly and effectively, providing explanations and justifications for your code decisions.
- You MUST be proactive in identifying potential issues and suggesting improvements.
- You MUST be collaborative and open to feedback from other developers.

## Technology Stack

- uv: packaging and dependency management
- Textual: text-based user interface (TUI)
- Httpx: HTTP operations
- Regex: pattern matching
- Pydantic: data validation and settings management
- Pytest: testing

Run tests and linters using `uv run <command>`.

If you need to run python directly, use `uv run python <args>` to ensure the correct environment is used.

- When iterating, you MUST run `tox -e py3.10` after making changes to ensure the basics are good (no need to run for all targets every time).
- Once you think you're done and tox runs on 3.10, you MUST run `tox` and `make spell` and make sure everything passes on all targets before considering a change as done.

## Project Structure and Architecture

### Textual TUI Integration

- MUST follow Textual patterns and integrate with dataflow architecture
- MUST use Textual's action/message system for UI events
- MUST separate UI logic (presentation) from business logic
- SHOULD style UI using Textual CSS (.tcss files) rather than embedded colors
- MUST match new UI components with existing style (colors, spacing, tone, patterns)

## Testing Guidelines

- MUST cover all branches with pytest unit tests
- MUST have tests for core functionalities in state classes, data processing, and algorithms
- MUST place tests in `tests/` directory mirroring `src/` structure
- MUST name test files and functions clearly (e.g., `test_<function_or_behavior>()`)
- SHOULD use pytest fixtures for common setup logic
- MAY use mocking for external API calls or non-deterministic operations
- MUST keep tests fast, isolated, and reliable
- MAY access protected members or use internal knowledge for test verification
- MUST write tests covering edge cases (empty inputs, invalid values, boundaries)
- SHOULD use `@pytest.mark.parametrize` for testing same logic on multiple inputs
- MUST write UI Tests using Textual's testing utilities (i.e. Pilot)
- MUST mark UI tests with `@pytest.mark.ui` decorator and integration tests with `@pytest.mark.integration`.
- MUST add a short docstring to each test explaining its purpose. Do not document parameters or return values.

Example:

```python
@pytest.mark.parametrize(("freq", "expected"), [(0, 60), (1, 60), (2, 2), (120, 120)])
def test_query_frequency_validation(freq: int, expected: int) -> None:
    """Query frequency <= 1 falls back to default; otherwise kept."""

    cfg = WatchlistConfig.model_validate({"query_frequency": freq})
    assert cfg.query_frequency == expected
```

## Code Style and Formatting

### Python Version Compatibility

- MUST target Python 3.14 while remaining compatible down to 3.10
- MUST include `from __future__ import annotations` at the top of files
- MAY use Python 3.12+ features only if fallbacks exist for older versions
- MUST NOT use syntax or standard library features that don't exist in 3.10

### General Style (PEP 8 & Google)

- MUST follow the Google Python Style Guide for naming, imports, and structure
- MUST prefix private/internal methods and data members with single underscore (`_`)
- MUST NOT use double underscores (`__`) unless name mangling is explicitly needed
- SHOULD prefer `@property` for exposing read-only accessors over public attributes
- SHOULD keep functions and methods reasonably short and straightforward
- MUST NOT use wildcard imports (`import *`) or relative imports
- MUST import explicitly by module name
- MUST use f-strings for string formatting outside of logging
- MUST NOT use mutable default values in function definitions

### Typing

- MUST include type hints for all functions, methods, and class attributes
- MUST use `|` syntax for unions and optionals, and type variables for generics
- MUST respect `final` for constants (do not reassign)
- MUST provide type stubs or use `# type: ignore` for external libraries without type hints

### Consistency and Clarity

- SHOULD favor descriptive names (e.g., `data_table` over `dt`)
- MUST maintain consistency with existing code patterns
- MUST write comments for non-obvious code blocks

## Documentation

### Docstrings for Public APIs

- MUST include docstrings for every public class, function, and method
- MUST use Google style docstrings
- MUST keep docstrings consistent with function behavior when code changes
- MUST leave a white line between summary docstring and code

Example:

```python
def _safe_value(v: T | None) -> float:
    """
    Safely retrieves the value of v.

    Note:
        If v is None, it returns the smallest representable value for type T.

    Args:
        v (T | None): The value to be retrieved. Can be of type int or float.

    Returns:
        float: The value of v if it's not None, otherwise the smallest representable
            value for type T.
    """

    return -inf if v is None else v
```

### Internal and Private Code

- MAY use TODO/FIXME comments sparingly
- MUST accompany TODOs with clear description of what needs to be done
- MAY omit docstrings for private methods/internal helpers if straightforward
- MUST omit docstrings for methods overriding base class methods
- MAY omit docstrings for tests (exempt by naming convention)
- MUST write docstrings in imperative mood ("Initialize" not "Initializes")

## Additional Considerations

- MUST be mindful of performance for real-time data updates
- MUST use efficient algorithms (e.g. avoid O(n^2) operations on every tick)
- MUST use logging module instead of `print` for debug/error messages
- MUST include logging in new features where appropriate
- MUST catch exceptions at boundaries (file I/O, network calls)
- MUST handle exceptions gracefully to prevent app crashes
