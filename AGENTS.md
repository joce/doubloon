# Cursor AI Rules for the Doubloon Project (Python Textual TUI)

## General Guidelines

- **MUST NEVER BE OBSEQUIOUS OR SYCOPHANTIC**

## Technology Stack

- Poetry: packaging and dependency management
- Textual: text-based user interface (TUI)
- Httpx: HTTP operations
- Regex: pattern matching
- Pydantic: data validation and settings management
- Pytest: testing

## Project Structure and Architecture

### Textual TUI Integration

- MUST follow Textual patterns and integrate with dataflow architecture
- MUST use Textual's action/message system for UI events
- MUST avoid long-running tasks in UI thread
- MUST use `@work` decorator for I/O or blocking computations
- MUST separate UI logic (presentation) from business logic
- MUST use locks/synchronization when modifying shared state from background threads
- SHOULD style UI using Textual CSS (.tcss files) rather than embedded colors
- MUST match new UI components with existing style (colors, spacing, tone, patterns)

## Testing Guidelines

- MUST cover all non-UI logic with pytest unit tests
- MUST have tests for core functionalities in state classes, data processing, and algorithms
- MUST place tests in `tests/` directory mirroring `src/` structure
- MUST name test files and functions clearly (e.g., `test_<function_or_behavior>()`)
- SHOULD use pytest fixtures for common setup logic
- MAY use mocking for external API calls or non-deterministic operations
- MUST keep tests fast, isolated, and reliable
- MAY access protected members or use internal knowledge for test verification
- MUST write tests covering edge cases (empty inputs, invalid values, boundaries)
- SHOULD use `pytest.mark.parametrize` for testing same logic on multiple inputs
- MUST NOT attempt UI event simulation tests (no framework setup exists)

## Code Style and Formatting

### Python Version Compatibility

- MUST target Python 3.14 while remaining compatible down to 3.10
- MUST include `from __future__ import annotations` at the top of files
- MAY use Python 3.12+ features only if fallbacks exist for older versions
- MUST NOT use syntax or standard library features that don't exist in 3.10

### General Style (PEP 8 & Google)

- MUST follow the Google Python Style Guide for naming, imports, and structure
- MUST use `PascalCase` for class names
- MUST use `snake_case` for functions, methods, and variables
- MUST use `UPPER_SNAKE_CASE` for constants
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
- MUST use Python 3 style type annotations (`list[str]`, `dict[str, Any]`, etc.)
- MAY use `typing.Optional`, `typing.Union` (or `|` syntax), and type variables for generics
- MUST NOT use `Any` unless absolutely necessary
- MUST NOT have inconsistent return types
- MUST respect `final` for constants (do not reassign)
- MUST handle `None` cases explicitly (use `Optional` and check before dereferencing)
- MUST ensure correct typing when using generics (e.g., functions returning `T` or accepting `Callable`)
- MUST provide type stubs or use `# type: ignore` for external libraries without type hints

### Consistency and Clarity

- MUST write clean, readable code
- SHOULD favor descriptive names (e.g., `data_table` over `dt`)
- MUST maintain consistency with existing code patterns
- MUST avoid deeply nested code
- MUST write comments for non-obvious code blocks

## Documentation

### Docstrings for Public APIs

- MUST include docstrings for every public class, function, and method
- MUST use Google style docstrings
- MUST start with one-sentence summary followed by blank line and details
- MUST use sections **Args:**, **Returns:**, and **Raises:** as appropriate
- MUST keep docstrings consistent with function behavior when code changes

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
- MUST use efficient algorithms (avoid O(n²) operations on every tick)
- MUST use appropriate data structures
- MUST use logging module instead of `print` for debug/error messages
- MUST include logging in new features where appropriate
- MUST catch exceptions at boundaries (file I/O, network calls)
- MUST handle exceptions gracefully to prevent app crashes
