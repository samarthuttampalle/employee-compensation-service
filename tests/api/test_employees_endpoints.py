"""API tests for employee HTTP endpoints with mocked services."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import azure.functions as func
import pytest

from ecs.api.employees_functions import (
    create_employee,
    delete_employee,
    get_employee,
    init_employee_api,
    list_employees,
    update_employee,
)
from ecs.core.exceptions import NotFoundError, ValidationError
from ecs.domain.employee import Employee
from ecs.services.employee_service import EmployeeListResult, EmployeeReadResult, EmployeeService


@pytest.fixture
def employee_service() -> Mock:
    return Mock(spec=EmployeeService)


@pytest.fixture(autouse=True)
def bind_employee_api(employee_service: Mock) -> None:
    init_employee_api(employee_service)


def _sample_employee(**overrides: object) -> Employee:
    defaults: dict[str, object] = {
        "employee_id": 1,
        "first_name": "Ada",
        "last_name": "Lovelace",
        "department_id": 3,
        "salary": Decimal("95000.00"),
        "bonus": None,
        "hire_date": date(2023, 6, 1),
    }
    defaults.update(overrides)
    return Employee(**defaults)  # type: ignore[arg-type]


def test_create_employee_returns_201(employee_service: Mock) -> None:
    created = _sample_employee()
    employee_service.create_employee.return_value = created
    req = func.HttpRequest(
        method="POST",
        url="/api/employees",
        body=json.dumps(
            {
                "firstName": "Ada",
                "lastName": "Lovelace",
                "departmentId": 3,
                "salary": 95000.00,
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
    )

    resp = create_employee(req)

    assert resp.status_code == 201
    body = json.loads(resp.get_body())
    assert body["employeeId"] == 1
    assert resp.headers.get("Location") == "/api/employees/1"


def test_get_employee_returns_404_when_missing(employee_service: Mock) -> None:
    employee_service.get_employee.side_effect = NotFoundError.for_resource("Employee", 99)
    req = func.HttpRequest(
        method="GET",
        url="/api/employees/99",
        body=b"",
        route_params={"employeeId": "99"},
    )

    resp = get_employee(req)

    assert resp.status_code == 404
    body = json.loads(resp.get_body())
    assert body["error"]["code"] == "EMPLOYEE_NOT_FOUND"


def test_get_employee_invalid_id_returns_400(employee_service: Mock) -> None:
    req = func.HttpRequest(
        method="GET",
        url="/api/employees/abc",
        body=b"",
        route_params={"employeeId": "abc"},
    )

    resp = get_employee(req)

    assert resp.status_code == 400
    employee_service.get_employee.assert_not_called()


def test_get_employee_with_default_bonus(employee_service: Mock) -> None:
    employee = _sample_employee(bonus=None, salary=Decimal("100000.00"))
    employee_service.get_employee.return_value = EmployeeReadResult(
        employee=employee,
        effective_bonus=Decimal("5000.00"),
        bonus_is_defaulted=True,
    )
    req = func.HttpRequest(
        method="GET",
        url="/api/employees/1?applyDefaultBonus=true",
        body=b"",
        route_params={"employeeId": "1"},
        params={"applyDefaultBonus": "true"},
    )

    resp = get_employee(req)

    assert resp.status_code == 200
    body = json.loads(resp.get_body())
    assert Decimal(str(body["effectiveBonus"])) == Decimal("5000.00")
    assert body["bonusIsDefaulted"] is True


def test_list_employees_returns_paginated_payload(employee_service: Mock) -> None:
    employee_service.list_employees.return_value = EmployeeListResult(
        items=[_sample_employee()],
        total=1,
        top=50,
        skip=0,
    )
    req = func.HttpRequest(method="GET", url="/api/employees", body=b"", params={})

    resp = list_employees(req)

    assert resp.status_code == 200
    body = json.loads(resp.get_body())
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_update_employee_empty_body_returns_400(employee_service: Mock) -> None:
    employee_service.update_employee.side_effect = ValidationError(
        "At least one field must be provided."
    )
    req = func.HttpRequest(
        method="PATCH",
        url="/api/employees/1",
        route_params={"employeeId": "1"},
        body=json.dumps({}).encode(),
        headers={"Content-Type": "application/json"},
    )

    resp = update_employee(req)

    assert resp.status_code == 400


def test_delete_employee_returns_204(employee_service: Mock) -> None:
    req = func.HttpRequest(
        method="DELETE",
        url="/api/employees/1",
        body=b"",
        route_params={"employeeId": "1"},
    )

    resp = delete_employee(req)

    assert resp.status_code == 204
    employee_service.delete_employee.assert_called_once_with(1)
