"""Unit tests for central HTTP error mapping (§10.2)."""

from __future__ import annotations

import json

import azure.functions as func
import pytest

from ecs.api.http_utils import error_response, handle_errors, json_response
from ecs.core.exceptions import (
    ConflictError,
    DependencyError,
    ECSError,
    NotFoundError,
    ValidationError,
)


class _FakeContext:
    invocation_id = "test-invocation-id"


@handle_errors
def _ok_handler(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    return json_response({"status": "ok"})


@handle_errors
def _validation_handler(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    raise ValidationError("Invalid input.")


@handle_errors
def _not_found_handler(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    raise NotFoundError.for_resource("Employee", 99)


@handle_errors
def _conflict_handler(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    raise ConflictError("Department has employees.", code="DEPARTMENT_HAS_EMPLOYEES")


@handle_errors
def _dependency_handler(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    raise DependencyError("Database temporarily unavailable.")


@handle_errors
def _domain_error_handler(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    raise ECSError("Unexpected domain failure.", code="ECS_FAILURE")


@handle_errors
def _unexpected_handler(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    raise RuntimeError("boom")


@pytest.fixture
def http_request() -> func.HttpRequest:
    return func.HttpRequest(method="GET", url="/api/test", body=b"")


@pytest.fixture
def context() -> _FakeContext:
    return _FakeContext()


def test_handle_errors_returns_success_response(
    http_request: func.HttpRequest,
    context: _FakeContext,
) -> None:
    response = _ok_handler(http_request, context)  # type: ignore[arg-type]

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("handler", "status_code", "error_code"),
    [
        (_validation_handler, 400, "VALIDATION_ERROR"),
        (_not_found_handler, 404, "EMPLOYEE_NOT_FOUND"),
        (_conflict_handler, 409, "DEPARTMENT_HAS_EMPLOYEES"),
        (_dependency_handler, 503, "DEPENDENCY_UNAVAILABLE"),
        (_domain_error_handler, 500, "ECS_FAILURE"),
        (_unexpected_handler, 500, "INTERNAL_ERROR"),
    ],
)
def test_handle_errors_maps_exceptions_to_http(
    http_request: func.HttpRequest,
    context: _FakeContext,
    handler: object,
    status_code: int,
    error_code: str,
) -> None:
    response = handler(http_request, context)  # type: ignore[operator]

    assert response.status_code == status_code
    body = json.loads(response.get_body())
    assert body["error"]["code"] == error_code
    assert body["error"]["correlationId"] == context.invocation_id


def test_handle_errors_hides_internal_details_for_unexpected_errors(
    http_request: func.HttpRequest,
    context: _FakeContext,
) -> None:
    response = _unexpected_handler(http_request, context)  # type: ignore[arg-type]
    body = json.loads(response.get_body())

    assert body["error"]["message"] == "An unexpected error occurred."
    assert "boom" not in body["error"]["message"]


def test_error_response_includes_correlation_id_when_provided() -> None:
    response = error_response(
        404,
        "NOT_FOUND",
        "Missing.",
        correlation_id="abc-123",
    )
    body = json.loads(response.get_body())

    assert body["error"]["correlationId"] == "abc-123"
