"""Unit tests for EmployeeService with mocked repositories."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from ecs.core.exceptions import NotFoundError, ValidationError
from ecs.domain.department import Department
from ecs.domain.employee import Employee
from ecs.schemas.employee_schemas import CreateEmployeeRequest, UpdateEmployeeRequest
from ecs.services.employee_service import EmployeeService


@pytest.fixture
def employee_repository() -> Mock:
    return Mock()


@pytest.fixture
def department_repository() -> Mock:
    return Mock()


@pytest.fixture
def employee_service(employee_repository: Mock, department_repository: Mock) -> EmployeeService:
    return EmployeeService(
        employee_repository,
        department_repository,
        default_bonus_rate=Decimal("0.05"),
        max_page_size=200,
    )


def _sample_employee(**overrides: object) -> Employee:
    defaults: dict[str, object] = {
        "employee_id": 1,
        "first_name": "Ada",
        "last_name": "Lovelace",
        "department_id": 3,
        "salary": Decimal("95000.00"),
        "bonus": Decimal("5000.00"),
        "hire_date": date(2023, 6, 1),
    }
    defaults.update(overrides)
    return Employee(**defaults)  # type: ignore[arg-type]


def test_create_employee_validates_department_reference(
    employee_service: EmployeeService,
    employee_repository: Mock,
    department_repository: Mock,
) -> None:
    department_repository.get_by_id.return_value = None
    request = CreateEmployeeRequest.model_validate(
        {
            "firstName": "Ada",
            "lastName": "Lovelace",
            "departmentId": 99,
            "salary": 95000,
        }
    )

    with pytest.raises(NotFoundError) as exc_info:
        employee_service.create_employee(request)

    assert exc_info.value.code == "DEPARTMENT_NOT_FOUND"
    employee_repository.insert.assert_not_called()


def test_create_employee_inserts_when_department_exists(
    employee_service: EmployeeService,
    employee_repository: Mock,
    department_repository: Mock,
) -> None:
    department_repository.get_by_id.return_value = Department(3, "Engineering", "Bengaluru")
    created = _sample_employee()
    employee_repository.insert.return_value = created
    request = CreateEmployeeRequest.model_validate(
        {
            "firstName": "Ada",
            "lastName": "Lovelace",
            "departmentId": 3,
            "salary": 95000,
        }
    )

    result = employee_service.create_employee(request)

    assert result == created
    employee_repository.insert.assert_called_once()


def test_get_employee_raises_not_found(
    employee_service: EmployeeService,
    employee_repository: Mock,
) -> None:
    employee_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        employee_service.get_employee(42)

    assert exc_info.value.code == "EMPLOYEE_NOT_FOUND"


def test_get_employee_applies_default_bonus_when_requested(
    employee_service: EmployeeService,
    employee_repository: Mock,
) -> None:
    employee_repository.get_by_id.return_value = _sample_employee(
        bonus=None,
        salary=Decimal("100000.00"),
    )

    result = employee_service.get_employee(1, apply_default_bonus=True)

    assert result.employee.bonus is None
    assert result.effective_bonus == Decimal("5000.00")
    assert result.bonus_is_defaulted is True


def test_get_employee_does_not_apply_default_bonus_when_bonus_present(
    employee_service: EmployeeService,
    employee_repository: Mock,
) -> None:
    employee_repository.get_by_id.return_value = _sample_employee(bonus=Decimal("1000.00"))

    result = employee_service.get_employee(1, apply_default_bonus=True)

    assert result.effective_bonus is None
    assert result.bonus_is_defaulted is False


def test_list_employees_clamps_top_to_max_page_size(
    employee_service: EmployeeService,
    employee_repository: Mock,
) -> None:
    employee_repository.list_employees.return_value = ([], 0)

    result = employee_service.list_employees(top=500, skip=0)

    employee_repository.list_employees.assert_called_once_with(department_id=None, top=200, skip=0)
    assert result.top == 200


def test_list_employees_rejects_negative_pagination(
    employee_service: EmployeeService,
) -> None:
    with pytest.raises(ValidationError):
        employee_service.list_employees(top=-1, skip=0)


def test_update_employee_rejects_empty_body(
    employee_service: EmployeeService,
) -> None:
    request = UpdateEmployeeRequest.model_validate({})

    with pytest.raises(ValidationError):
        employee_service.update_employee(1, request)


def test_update_employee_clears_bonus_with_explicit_null(
    employee_service: EmployeeService,
    employee_repository: Mock,
) -> None:
    employee_repository.get_by_id.return_value = _sample_employee()
    employee_repository.update.return_value = _sample_employee(bonus=None)
    request = UpdateEmployeeRequest.model_validate({"bonus": None})

    result = employee_service.update_employee(1, request)

    assert result.bonus is None
    employee_repository.update.assert_called_once_with(1, {"bonus": None})


def test_update_employee_validates_department_reference(
    employee_service: EmployeeService,
    employee_repository: Mock,
    department_repository: Mock,
) -> None:
    employee_repository.get_by_id.return_value = _sample_employee()
    department_repository.get_by_id.return_value = None
    request = UpdateEmployeeRequest.model_validate({"departmentId": 99})

    with pytest.raises(NotFoundError):
        employee_service.update_employee(1, request)


def test_delete_employee_raises_not_found(
    employee_service: EmployeeService,
    employee_repository: Mock,
) -> None:
    employee_repository.delete.return_value = False

    with pytest.raises(NotFoundError):
        employee_service.delete_employee(42)
