"""Pylint plugin to mute warnings about missing docstrings on overridden methods."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, no_type_check

from astroid import MANAGER  # type: ignore[import-untyped]
from astroid.nodes import (  # type: ignore[import-untyped]
    AsyncFunctionDef,
    Const,
    FunctionDef,
    NodeNG,
    Yield,
)

if TYPE_CHECKING:
    from pylint.lint import PyLinter


DISABLING_DECORATORS = {"typing.override", "typing_extensions.override"}


def register(_: PyLinter) -> None:
    """Auto registers the transformer during initialization."""


def has_func_in_hierarchy(node: NodeNG) -> bool:
    """Check if the node has a function in its hierarchy.

    Args:
        node: The node to check.

    Returns:
        True if the node has a function ancestor, False otherwise.
    """

    if not node.parent:
        return False

    return node.parent.is_function or has_func_in_hierarchy(node.parent)


def is_yielding(node: NodeNG) -> bool:
    """Check if the node contains a yield statement.

    Args:
        node: The node to check.

    Returns:
        True if the node contains a yield statement, False otherwise.
    """

    for child in node.get_children():
        if isinstance(child, Yield) or is_yielding(child):
            return True
    return False


def should_add_docstring(func: FunctionDef) -> bool:
    """Check if the function should have a docstring.

    Args:
        func: The function to check.

    Returns:
        True if the function does not have a docstring but should have one,
        False otherwise.
    """

    return not func.doc_node and (
        # Does this have a decorator for which we don't want to generate a docstring?
        any(decorator in func.decoratornames() for decorator in DISABLING_DECORATORS)
        # Is this a local function?
        or has_func_in_hierarchy(func)
    )


# disabling for `type: ignore[attr-defined]`, which is needed in several places for the
# function to work
@no_type_check
def generate_dummy_docstring(func: FunctionDef) -> str:
    """Generate a dummy docstring for the function in order to suppress the warning.

    Args:
        func: The function to generate a docstring for.

    Returns:
        The docstring for the function.
    """

    res = f"This is a documentation for {func.name}.\n"

    if func.args:
        res += "\nArgs:\n"
        cnt = 1
        for arg in func.args.args:
            res += f"    {arg.name}: the arg number {cnt}.\n"
            cnt += 1

    if is_yielding(func):
        res += "\nYields:\n Some value.\n"

    # Add a return value for the function if it's not None (and it's not a generator)
    elif func.returns and not (
        isinstance(func.returns, Const) and func.returns.value is None
    ):
        res += "\nReturns:\n    "
        if hasattr(func.returns, "name"):
            res += f"\
                {func.returns.name}: Some value.\n"
        elif hasattr(func.returns, "value") and hasattr(func.returns.value, "name"):
            res += f"\
                {func.returns.value.name}: Some value.\n"

    return res


def transform(
    node: FunctionDef,
    infer_function: Any = None,  # noqa: ARG001, ANN401
) -> FunctionDef:
    """Transform the function to add a docstring.

    Args:
        node: The function to transform.
        infer_function: Unused inference function parameter.

    Returns:
        The potentially modified FunctionDef node.
    """

    if should_add_docstring(node):
        docstring_content = generate_dummy_docstring(node)
        # Create a new Const node for the docstring
        docstring_node = Const(value=docstring_content)
        docstring_node.parent = node

        # Set the doc_node attribute directly
        node.doc_node = docstring_node

    return node


MANAGER.register_transform(FunctionDef, transform)
MANAGER.register_transform(AsyncFunctionDef, transform)
