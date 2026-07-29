"""Unit tests for department Pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ecs.domain.department import Department
from ecs.schemas.department_schemas import (
    CreateDepartmentRequest,
    DepartmentResponse,
    UpdateDepartmentRequest,
)


def test_create_department_request_accepts_valid_payload() -> None:
    req = CreateDepartmentRequest.model_validate(
        {"departmentName": "Engineering", "location": "Bengaluru"}
    )
    assert req.department_name == "Engineering"
    assert req.location == "Bengaluru"


def test_update_explicit_null_location_is_allowed() -> None:
    req = UpdateDepartmentRequest.model_validate({"location": None})
    assert req.is_set("location") is True
    assert req.location is None


def test_update_rejects_explicit_null_department_name() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UpdateDepartmentRequest.model_validate({"departmentName": None})
    assert "departmentName cannot be null" in str(exc_info.value)


def test_update_empty_body_has_no_updates() -> None:
    req = UpdateDepartmentRequest.model_validate({})
    assert req.has_updates() is False


def test_department_response_from_domain() -> None:
    department = Department(
        department_id=1,
        department_name="Engineering",
        location=None,
    )
    payload = DepartmentResponse.from_domain(department).model_dump(by_alias=True)
    assert payload == {
        "departmentId": 1,
        "departmentName": "Engineering",
        "location": None,
    }
