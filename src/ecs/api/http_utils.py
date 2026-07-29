"""Shared HTTP response builders and error-handling decorator."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import azure.functions as func
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from ecs.core.exceptions import (
    ConflictError,
    DependencyError,
    ECSError,
    NotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., func.HttpResponse])
TModel = TypeVar("TModel", bound=BaseModel)


def json_response(
    body: BaseModel | dict[str, Any],
    status_code: int = 200,
    *,
    headers: dict[str, str] | None = None,
) -> func.HttpResponse:
    """Serialize a Pydantic model or dict to a JSON HttpResponse."""
    if isinstance(body, BaseModel):
        payload = body.model_dump_json(by_alias=True)
    else:
        payload = json.dumps(body, default=str)
    return func.HttpResponse(
        body=payload,
        status_code=status_code,
        mimetype="application/json",
        headers=headers,
    )


def no_content_response() -> func.HttpResponse:
    """Return a 204 No Content response."""
    return func.HttpResponse(status_code=204)


def error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    correlation_id: str | None = None,
    details: object = None,
) -> func.HttpResponse:
    """Return the standard API error envelope."""
    error_body: dict[str, object] = {
        "code": code,
        "message": message,
        "details": details,
    }
    if correlation_id is not None:
        error_body["correlationId"] = correlation_id
    return json_response({"error": error_body}, status_code)


def parse_json_body(req: func.HttpRequest, model: type[TModel]) -> TModel:
    """Parse and validate a JSON request body with Pydantic."""
    try:
        body = req.get_json()
    except ValueError as exc:
        raise ValidationError("Request body must be valid JSON.") from exc
    if body is None:
        raise ValidationError("Request body is required.")
    try:
        validated: TModel = model.model_validate(body)
        return validated
    except PydanticValidationError as exc:
        first_error = exc.errors()[0]
        message = str(first_error.get("msg", "Validation failed."))
        raise ValidationError(message) from exc


def parse_positive_int(value: str | None, field_name: str) -> int:
    """Parse a positive integer path or query parameter."""
    if value is None or value.strip() == "":
        raise ValidationError(f"{field_name} must be a positive integer.")
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValidationError(f"{field_name} must be a positive integer.") from exc
    if parsed <= 0:
        raise ValidationError(f"{field_name} must be a positive integer.")
    return parsed


def parse_optional_positive_int(value: str | None, field_name: str) -> int | None:
    """Parse an optional positive integer query parameter."""
    if value is None or value.strip() == "":
        return None
    return parse_positive_int(value, field_name)


def parse_non_negative_int(value: str | None, field_name: str, *, default: int) -> int:
    """Parse a non-negative integer query parameter with a default."""
    if value is None or value.strip() == "":
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValidationError(f"{field_name} must be a non-negative integer.") from exc
    if parsed < 0:
        raise ValidationError(f"{field_name} must be a non-negative integer.")
    return parsed


def parse_bool_query(value: str | None) -> bool:
    """Parse a boolean query flag (true/false, case-insensitive)."""
    return value is not None and value.strip().lower() == "true"


def _get_correlation_id(context: func.Context) -> str:
    return context.invocation_id


def _request_log_context(
    req: func.HttpRequest,
    correlation_id: str | None,
) -> dict[str, object]:
    return {
        "invocation_id": correlation_id,
        "method": req.method,
        "route": req.url,
    }


def handle_errors(handler: F) -> F:
    """Map domain exceptions to HTTP responses for Function handlers."""

    @wraps(handler)
    def wrapper(
        req: func.HttpRequest,
        context: func.Context,
    ) -> func.HttpResponse:
        correlation_id = _get_correlation_id(context)
        log_context = _request_log_context(req, correlation_id)
        started_at = time.perf_counter()
        logger.info("Request received", extra=log_context)
        try:
            response = handler(req, context)
        except ValidationError as exc:
            logger.warning(
                "Validation error",
                extra={
                    **log_context,
                    "exception_type": type(exc).__name__,
                    "error_code": exc.code,
                },
            )
            return error_response(
                400,
                exc.code,
                str(exc),
                correlation_id=correlation_id,
            )
        except NotFoundError as exc:
            logger.warning(
                "Resource not found",
                extra={
                    **log_context,
                    "exception_type": type(exc).__name__,
                    "error_code": exc.code,
                },
            )
            return error_response(
                404,
                exc.code,
                str(exc),
                correlation_id=correlation_id,
            )
        except ConflictError as exc:
            logger.warning(
                "Conflict",
                extra={
                    **log_context,
                    "exception_type": type(exc).__name__,
                    "error_code": exc.code,
                },
            )
            return error_response(
                409,
                exc.code,
                str(exc),
                correlation_id=correlation_id,
            )
        except DependencyError as exc:
            logger.error(
                "Dependency unavailable",
                extra={
                    **log_context,
                    "exception_type": type(exc).__name__,
                    "error_code": exc.code,
                },
            )
            return error_response(
                503,
                "DEPENDENCY_UNAVAILABLE",
                "Database temporarily unavailable.",
                correlation_id=correlation_id,
            )
        except ECSError as exc:
            logger.error(
                "Unhandled domain error",
                extra={
                    **log_context,
                    "exception_type": type(exc).__name__,
                    "error_code": exc.code,
                },
            )
            return error_response(
                500,
                exc.code,
                "An unexpected error occurred.",
                correlation_id=correlation_id,
            )
        except Exception as exc:
            logger.exception(
                "Unhandled error",
                extra={
                    **log_context,
                    "exception_type": type(exc).__name__,
                },
            )
            return error_response(
                500,
                "INTERNAL_ERROR",
                "An unexpected error occurred.",
                correlation_id=correlation_id,
            )

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "Request completed",
            extra={
                **log_context,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    return wrapper  # type: ignore[return-value]
