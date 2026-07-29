"""Unit tests for employee Pydantic schemas — especially PATCH omitted vs null (§9.4)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from ecs.domain.employee import Employee
from ecs.schemas.employee_schemas import (
    CreateEmployeeRequest,
    EmployeeResponse,
    UpdateEmployeeRequest,
)


def test_create_employee_request_accepts_valid_payload() -> None:
    req = CreateEmployeeRequest.model_validate(
        {
            "firstName": "Ada",
            "lastName": "Lovelace",
            "departmentId": 3,
            "salary": 95000.00,
            "bonus": None,
            "hireDate": "2023-06-01",
        }
    )
    assert req.first_name == "Ada"
    assert req.salary == Decimal("95000.00")
    assert req.bonus is None
    assert req.hire_date == date(2023, 6, 1)


def test_create_employee_request_rejects_non_positive_salary() -> None:
    with pytest.raises(ValidationError):
        CreateEmployeeRequest.model_validate(
            {
                "firstName": "Ada",
                "lastName": "Lovelace",
                "salary": 0,
            }
        )


def test_create_employee_request_rejects_negative_bonus() -> None:
    with pytest.raises(ValidationError):
        CreateEmployeeRequest.model_validate(
            {
                "firstName": "Ada",
                "lastName": "Lovelace",
                "salary": 1000,
                "bonus": -1,
            }
        )


def test_create_employee_request_rejects_future_hire_date() -> None:
    future = date.today() + timedelta(days=1)
    with pytest.raises(ValidationError):
        CreateEmployeeRequest.model_validate(
            {
                "firstName": "Ada",
                "lastName": "Lovelace",
                "salary": 1000,
                "hireDate": future.isoformat(),
            }
        )


def test_update_omitted_fields_are_not_in_fields_set() -> None:
    req = UpdateEmployeeRequest.model_validate({"bonus": 1500})
    assert req.is_set("bonus") is True
    assert req.is_set("first_name") is False
    assert req.is_set("salary") is False
    assert req.bonus == Decimal("1500")
    assert req.has_updates() is True


def test_update_explicit_null_bonus_is_distinguished_from_omission() -> None:
    clear_bonus = UpdateEmployeeRequest.model_validate({"bonus": None})
    assert clear_bonus.is_set("bonus") is True
    assert clear_bonus.bonus is None

    omit_bonus = UpdateEmployeeRequest.model_validate({"firstName": "Ada"})
    assert omit_bonus.is_set("bonus") is False
    assert omit_bonus.bonus is None


def test_update_explicit_null_department_id_is_allowed() -> None:
    req = UpdateEmployeeRequest.model_validate({"departmentId": None})
    assert req.is_set("department_id") is True
    assert req.department_id is None


def test_update_rejects_explicit_null_salary() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UpdateEmployeeRequest.model_validate({"salary": None})
    assert "salary cannot be null" in str(exc_info.value)


def test_update_rejects_explicit_null_first_name() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UpdateEmployeeRequest.model_validate({"firstName": None})
    assert "firstName cannot be null" in str(exc_info.value)


def test_update_rejects_explicit_null_last_name() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UpdateEmployeeRequest.model_validate({"lastName": None})
    assert "lastName cannot be null" in str(exc_info.value)


def test_update_empty_body_has_no_updates() -> None:
    req = UpdateEmployeeRequest.model_validate({})
    assert req.has_updates() is False
    assert req.model_fields_set == set()


def test_employee_response_from_domain_with_default_bonus_fields() -> None:
    employee = Employee(
        employee_id=1,
        first_name="Ada",
        last_name="Lovelace",
        department_id=3,
        salary=Decimal("95000.00"),
        bonus=None,
        hire_date=date(2023, 6, 1),
    )
    response = EmployeeResponse.from_domain(
        employee,
        effective_bonus=Decimal("4750.00"),
        bonus_is_defaulted=True,
    )
    payload = response.model_dump(by_alias=True)
    assert payload["employeeId"] == 1
    assert payload["bonus"] is None
    assert payload["effectiveBonus"] == Decimal("4750.00")
    assert payload["bonusIsDefaulted"] is True
