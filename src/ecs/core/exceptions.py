"""Domain-specific exception hierarchy for API error mapping."""

from __future__ import annotations


class ECSError(Exception):
    """Base class for all domain-level service exceptions."""

    code = "ECS_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class ValidationError(ECSError):
    """Raised for request or domain validation failures."""

    code = "VALIDATION_ERROR"


class NotFoundError(ECSError):
    """Raised when an expected entity does not exist."""

    code = "NOT_FOUND"

    @classmethod
    def for_resource(cls, resource_name: str, resource_id: int) -> NotFoundError:
        """Build a not-found error with a resource-specific error code."""
        normalized = resource_name.strip().upper().replace(" ", "_")
        return cls(
            f"{resource_name} with ID {resource_id} was not found.",
            code=f"{normalized}_NOT_FOUND",
        )


class ConflictError(ECSError):
    """Raised when an operation violates a business rule."""

    code = "CONFLICT"


class DependencyError(ECSError):
    """Raised when an external dependency is unavailable."""

    code = "DEPENDENCY_UNAVAILABLE"
