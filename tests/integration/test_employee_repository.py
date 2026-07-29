"""Integration tests for SqlAlchemyEmployeeRepository against local SQL Server."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from ecs.repositories.employee_repository import SqlAlchemyEmployeeRepository


def test_get_by_id_returns_seeded_employee(
    employee_repository: SqlAlchemyEmployeeRepository,
) -> None:
    employee = employee_repository.get_by_id(1)
    assert employee is not None
    assert employee.first_name == "Aarav"
    assert employee.salary == Decimal("120000.00")
    assert employee.bonus == Decimal("10000.00")


def test_get_by_id_returns_none_for_missing(
    employee_repository: SqlAlchemyEmployeeRepository,
) -> None:
    assert employee_repository.get_by_id(99999) is None


def test_list_employees_filters_by_department(
    employee_repository: SqlAlchemyEmployeeRepository,
) -> None:
    items, total = employee_repository.list_employees(department_id=1, top=50, skip=0)
    assert total == 3
    assert all(item.department_id == 1 for item in items)


def test_list_employees_pagination(
    employee_repository: SqlAlchemyEmployeeRepository,
) -> None:
    page, total = employee_repository.list_employees(department_id=None, top=3, skip=0)
    assert total == 10
    assert len(page) == 3

    page2, _ = employee_repository.list_employees(department_id=None, top=3, skip=3)
    assert len(page2) == 3
    assert {item.employee_id for item in page}.isdisjoint({item.employee_id for item in page2})


def test_insert_and_get_employee(
    employee_repository: SqlAlchemyEmployeeRepository,
) -> None:
    created = employee_repository.insert(
        first_name="Grace",
        last_name="Hopper",
        department_id=1,
        salary=Decimal("99000.00"),
        bonus=None,
        hire_date=date(2024, 1, 15),
    )
    assert created.employee_id > 0
    assert created.bonus is None

    fetched = employee_repository.get_by_id(created.employee_id)
    assert fetched is not None
    assert fetched.first_name == "Grace"
    assert fetched.bonus is None


def test_update_clears_bonus_with_explicit_null(
    employee_repository: SqlAlchemyEmployeeRepository,
) -> None:
    updated = employee_repository.update(1, {"bonus": None})
    assert updated is not None
    assert updated.bonus is None


def test_update_partial_fields(
    employee_repository: SqlAlchemyEmployeeRepository,
) -> None:
    updated = employee_repository.update(1, {"salary": Decimal("125000.00")})
    assert updated is not None
    assert updated.salary == Decimal("125000.00")
    assert updated.first_name == "Aarav"


def test_update_missing_employee_returns_none(
    employee_repository: SqlAlchemyEmployeeRepository,
) -> None:
    assert employee_repository.update(99999, {"salary": Decimal("1000.00")}) is None


def test_delete_employee(
    employee_repository: SqlAlchemyEmployeeRepository,
) -> None:
    assert employee_repository.delete(8) is True
    assert employee_repository.get_by_id(8) is None
    assert employee_repository.delete(8) is False
