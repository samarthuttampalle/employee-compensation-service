"""Integration tests for SqlAlchemyReportingRepository against local SQL Server."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from ecs.repositories.department_repository import SqlAlchemyDepartmentRepository
from ecs.repositories.employee_repository import SqlAlchemyEmployeeRepository
from ecs.repositories.reporting_repository import SqlAlchemyReportingRepository


@pytest.fixture
def reporting_repository(engine: Engine) -> SqlAlchemyReportingRepository:
    return SqlAlchemyReportingRepository(engine)


def test_total_bonus_treats_null_as_zero(
    reporting_repository: SqlAlchemyReportingRepository,
) -> None:
    total = reporting_repository.fetch_total_bonus_paid()
    assert total == Decimal("102000.00")


def test_employees_without_bonus_returns_null_bonus_rows(
    reporting_repository: SqlAlchemyReportingRepository,
) -> None:
    rows = reporting_repository.fetch_employees_without_bonus()
    employee_ids = {row.employee_id for row in rows}
    assert employee_ids == {2, 4, 8}
    assert len(rows) == 3


def test_bonus_percentage_excludes_null_bonus_employees(
    reporting_repository: SqlAlchemyReportingRepository,
) -> None:
    rows = reporting_repository.fetch_bonus_percentages()
    employee_ids = {row.employee_id for row in rows}
    assert 2 not in employee_ids
    assert 4 not in employee_ids
    assert 8 not in employee_ids
    assert len(rows) == 7

    aarav = next(row for row in rows if row.employee_id == 1)
    assert aarav.bonus_percentage == Decimal("8.33")


def test_departments_over_average_excludes_department_with_no_employees(
    reporting_repository: SqlAlchemyReportingRepository,
    engine: Engine,
) -> None:
    rows = reporting_repository.fetch_departments_over_average()
    department_ids = {row.department_id for row in rows}
    assert 5 not in department_ids


def test_departments_over_average_includes_matching_department(
    reporting_repository: SqlAlchemyReportingRepository,
    department_repository: SqlAlchemyDepartmentRepository,
    employee_repository: SqlAlchemyEmployeeRepository,
) -> None:
    department = department_repository.insert(
        department_name="Bonus Heavy",
        location="Remote",
    )
    employee_repository.insert(
        first_name="Alex",
        last_name="Stone",
        department_id=department.department_id,
        salary=Decimal("50000.00"),
        bonus=Decimal("60000.00"),
        hire_date=date(2024, 1, 1),
    )

    rows = reporting_repository.fetch_departments_over_average()
    match = next(row for row in rows if row.department_id == department.department_id)
    assert match.total_bonus_paid == Decimal("60000.00")
    assert match.average_salary == Decimal("50000.00")


def test_bonus_ranking_places_null_bonus_last(
    reporting_repository: SqlAlchemyReportingRepository,
) -> None:
    rows = reporting_repository.fetch_bonus_ranking()
    assert len(rows) == 10

    null_bonus_rows = [row for row in rows if row.bonus is None]
    non_null_bonus_rows = [row for row in rows if row.bonus is not None]
    assert {row.employee_id for row in null_bonus_rows} == {2, 4, 8}

    max_non_null_rank = max(row.rank for row in non_null_bonus_rows)
    min_null_rank = min(row.rank for row in null_bonus_rows)
    assert min_null_rank > max_non_null_rank

    vikram = next(row for row in rows if row.employee_id == 10)
    assert vikram.rank == 1
    assert vikram.bonus == Decimal("30000.00")


def test_bonus_ranking_assigns_same_rank_to_tied_bonuses(
    reporting_repository: SqlAlchemyReportingRepository,
) -> None:
    rows = reporting_repository.fetch_bonus_ranking()
    tied = [row for row in rows if row.bonus == Decimal("15000.00")]
    assert len(tied) == 2
    assert tied[0].rank == tied[1].rank == 3


def test_highest_salary_from_seed_data(reporting_repository: SqlAlchemyReportingRepository) -> None:
    highest = reporting_repository.fetch_highest_salary()
    assert highest is not None
    assert highest.employee_id == 9
    assert highest.salary == Decimal("200000.00")


def test_highest_total_compensation_from_seed_data(
    reporting_repository: SqlAlchemyReportingRepository,
) -> None:
    highest = reporting_repository.fetch_highest_total_compensation()
    assert highest is not None
    assert highest.employee_id == 9
    assert highest.total_compensation == Decimal("202000.00")


def test_highest_salary_vs_highest_total_compensation_can_differ(
    reporting_repository: SqlAlchemyReportingRepository,
    employee_repository: SqlAlchemyEmployeeRepository,
    department_repository: SqlAlchemyDepartmentRepository,
) -> None:
    department = department_repository.insert(department_name="Comp Test", location=None)
    high_salary = employee_repository.insert(
        first_name="High",
        last_name="Salary",
        department_id=department.department_id,
        salary=Decimal("250000.00"),
        bonus=None,
        hire_date=date(2024, 2, 1),
    )
    high_total = employee_repository.insert(
        first_name="High",
        last_name="Total",
        department_id=department.department_id,
        salary=Decimal("200000.00"),
        bonus=Decimal("70000.00"),
        hire_date=date(2024, 2, 1),
    )

    highest_salary = reporting_repository.fetch_highest_salary()
    highest_total = reporting_repository.fetch_highest_total_compensation()

    assert highest_salary is not None
    assert highest_total is not None
    assert highest_salary.employee_id == high_salary.employee_id
    assert highest_total.employee_id == high_total.employee_id
    assert highest_salary.employee_id != highest_total.employee_id


def test_reporting_queries_return_empty_results_when_no_employees(
    engine: Engine,
) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM dbo.Employee"))

    repository = SqlAlchemyReportingRepository(engine)
    assert repository.fetch_total_bonus_paid() == Decimal("0")
    assert repository.fetch_employees_without_bonus() == []
    assert repository.fetch_bonus_percentages() == []
    assert repository.fetch_departments_over_average() == []
    assert repository.fetch_bonus_ranking() == []
    assert repository.fetch_highest_salary() is None
    assert repository.fetch_highest_total_compensation() is None
