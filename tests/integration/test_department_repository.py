"""Integration tests for SqlAlchemyDepartmentRepository against local SQL Server."""

from __future__ import annotations

import pytest

from ecs.core.exceptions import ConflictError
from ecs.repositories.department_repository import SqlAlchemyDepartmentRepository
from ecs.repositories.employee_repository import SqlAlchemyEmployeeRepository


def test_get_by_id_returns_seeded_department(
    department_repository: SqlAlchemyDepartmentRepository,
) -> None:
    department = department_repository.get_by_id(1)
    assert department is not None
    assert department.department_name == "Engineering"
    assert department.location == "Bengaluru"


def test_list_departments_includes_empty_department(
    department_repository: SqlAlchemyDepartmentRepository,
) -> None:
    items, total = department_repository.list_departments()
    assert total == 5
    legal = next(item for item in items if item.department_name == "Legal")
    assert legal.department_id == 5


def test_insert_and_update_department(
    department_repository: SqlAlchemyDepartmentRepository,
) -> None:
    created = department_repository.insert(department_name="Marketing", location="Delhi")
    assert created.department_id > 0

    updated = department_repository.update(created.department_id, {"location": None})
    assert updated is not None
    assert updated.location is None
    assert updated.department_name == "Marketing"


def test_insert_duplicate_department_name_raises_conflict(
    department_repository: SqlAlchemyDepartmentRepository,
) -> None:
    with pytest.raises(ConflictError):
        department_repository.insert(department_name="Engineering", location=None)


def test_count_and_unassign_employees(
    department_repository: SqlAlchemyDepartmentRepository,
    employee_repository: SqlAlchemyEmployeeRepository,
) -> None:
    assert department_repository.count_employees(1) == 3
    unassigned = department_repository.unassign_employees(1)
    assert unassigned == 3
    assert department_repository.count_employees(1) == 0

    employee = employee_repository.get_by_id(1)
    assert employee is not None
    assert employee.department_id is None


def test_delete_department_with_set_null_behavior(
    department_repository: SqlAlchemyDepartmentRepository,
    employee_repository: SqlAlchemyEmployeeRepository,
) -> None:
    assert department_repository.delete(4) is True
    employee = employee_repository.get_by_id(7)
    assert employee is not None
    assert employee.department_id is None


def test_delete_missing_department_returns_false(
    department_repository: SqlAlchemyDepartmentRepository,
) -> None:
    assert department_repository.delete(99999) is False
