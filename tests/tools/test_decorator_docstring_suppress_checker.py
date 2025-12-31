"""Test the decorator docstring suppression plugin."""

# pylint: disable=missing-return-doc

from __future__ import annotations

import astroid  # type: ignore[import-untyped]

from tools.pylint_plugins.decorator_docstring_suppress_checker import (
    generate_dummy_docstring,  # pyright: ignore[reportUnknownVariableType]
)


def test_generate_dummy_docstring_includes_union_return() -> None:
    """Include return info when annotations use union syntax."""

    module = astroid.parse("def f() -> bool | None:\n    return True\n")
    func = module.body[0]

    docstring = generate_dummy_docstring(func)

    assert "Returns:" in docstring
    assert "bool | None: Some value." in docstring


def test_generate_dummy_docstring_skips_none_return() -> None:
    """Avoid adding return docs when annotation is None."""

    module = astroid.parse("def f() -> None:\n    return None\n")
    func = module.body[0]

    docstring = generate_dummy_docstring(func)

    assert "Returns:" not in docstring


def test_generate_dummy_docstring_skips_private_params() -> None:
    """Skip documenting parameters prefixed with underscores."""

    module = astroid.parse(
        "def f(_ignored: int, value: int) -> None:\n    return None\n"
    )
    func = module.body[0]

    docstring = generate_dummy_docstring(func)

    assert "Args:" in docstring
    assert "_ignored" not in docstring
    assert "value: the arg number 1." in docstring
