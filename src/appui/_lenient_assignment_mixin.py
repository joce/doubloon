"""Shared helpers for configuration models."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, ClassVar, Self

if TYPE_CHECKING:
    from collections.abc import Generator


class LenientAssignmentMixin:
    """Enable per-model control over lenient validation during construction."""

    _allow_fallback_flag: ClassVar[ContextVar[bool]] = ContextVar(
        "_allow_fallback_flag", default=False
    )

    def __init__(
        self,
        **data: Any,  # noqa: ANN401 - Required to match Pydantic signature
    ) -> None:
        with self._allow_fallback():
            super().__init__(**data)

    @classmethod
    def model_validate(  # noqa: PLR0913 - Required to match Pydantic signature
        cls,
        obj: Any,  # noqa: ANN401 - Required to match Pydantic signature
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
        by_alias: bool | None = None,
        by_name: bool | None = None,
    ) -> Self:
        """Validate ``obj`` into a configuration instance.

        Args:
            obj: The object to validate.
            strict: Flag to enable strict validation.
            from_attributes: Whether to pull values from attributes.
            context: Additional validation context.
            by_alias: Whether to look up fields by their aliases.
            by_name: Whether to look up fields by their field names.

        Returns:
            Any: The validated configuration instance.
        """
        with cls._allow_fallback():
            return super().model_validate(  # type: ignore[misc]
                obj,
                strict=strict,
                from_attributes=from_attributes,
                context=context,
                by_alias=by_alias,
                by_name=by_name,
            )

    @classmethod
    @contextmanager
    def _allow_fallback(cls) -> Generator[None, None, None]:
        """Context manager enabling lenient validation for the active context.

        Yields:
            Generator[None, None, None]: Nothing. Just used for context management.
        """

        token = cls._allow_fallback_flag.set(True)
        try:
            yield
        finally:
            cls._allow_fallback_flag.reset(token)

    @classmethod
    def _fallback_enabled(cls) -> bool:
        """Return whether lenient fallback is active for the current context.

        Returns:
            bool: True if lenient fallback is enabled, False otherwise.
        """

        return cls._allow_fallback_flag.get()
