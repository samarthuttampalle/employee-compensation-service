"""Unit tests for DepartmentService with mocked repositories."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from ecs.core.exceptions import ConflictError, NotFoundError, ValidationError
from ecs.domain.department import Department
from ecs.schemas.department_schemas import CreateDepartmentRequest, UpdateDepartmentRequest
from ecs.services.department_service import DepartmentService


@pytest.fixture
def department_repository() -> Mock:
    return Mock()


@pytest.fixture
def department_service(department_repository: Mock) -> DepartmentService:
    return DepartmentService(department_repository)


def _sample_department(**overrides: object) -> Department:
    defaults: dict[str, object] = {
        "department_id": 1,
        "department_name": "Engineering",
        "location": "Bengaluru",
    }
    defaults.update(overrides)
    return Department(**defaults)  # type: ignore[arg-type]


def test_create_department_delegates_to_repository(
    department_service: DepartmentService,
    department_repository: Mock,
) -> None:
    created = _sample_department()
    department_repository.insert.return_value = created
    request = CreateDepartmentRequest.model_validate(
        {"departmentName": "Engineering", "location": "Bengaluru"}
    )

    result = department_service.create_department(request)

    assert result == created
    department_repository.insert.assert_called_once_with(
        department_name="Engineering",
        location="Bengaluru",
    )


def test_get_department_raises_not_found(
    department_service: DepartmentService,
    department_repository: Mock,
) -> None:
    department_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        department_service.get_department(42)

    assert exc_info.value.code == "DEPARTMENT_NOT_FOUND"


def test_update_department_rejects_empty_body(
    department_service: DepartmentService,
) -> None:
    request = UpdateDepartmentRequest.model_validate({})

    with pytest.raises(ValidationError):
        department_service.update_department(1, request)


def test_update_department_applies_partial_changes(
    department_service: DepartmentService,
    department_repository: Mock,
) -> None:
    department_repository.get_by_id.return_value = _sample_department()
    department_repository.update.return_value = _sample_department(location=None)
    request = UpdateDepartmentRequest.model_validate({"location": None})

    result = department_service.update_department(1, request)

    assert result.location is None
    department_repository.update.assert_called_once_with(1, {"location": None})


def test_delete_department_raises_conflict_when_employees_assigned(
    department_service: DepartmentService,
    department_repository: Mock,
) -> None:
    department_repository.get_by_id.return_value = _sample_department()
    department_repository.count_employees.return_value = 4

    with pytest.raises(ConflictError) as exc_info:
        department_service.delete_department(1, force=False)

    assert exc_info.value.code == "DEPARTMENT_HAS_EMPLOYEES"
    department_repository.delete.assert_not_called()


def test_delete_department_with_force_unassigns_employees(
    department_service: DepartmentService,
    department_repository: Mock,
) -> None:
    department_repository.get_by_id.return_value = _sample_department()
    department_repository.count_employees.return_value = 4
    department_repository.unassign_employees.return_value = 4
    department_repository.delete.return_value = True

    result = department_service.delete_department(1, force=True)

    assert result.department_id == 1
    assert result.unassigned_employees == 4
    department_repository.unassign_employees.assert_called_once_with(1)
    department_repository.delete.assert_called_once_with(1)


def test_delete_department_raises_not_found(
    department_service: DepartmentService,
    department_repository: Mock,
) -> None:
    department_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        department_service.delete_department(99)
