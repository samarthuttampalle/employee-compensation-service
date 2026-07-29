"""Unit tests for ReportingService with mocked repository."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import Mock

import pytest

from ecs.core.exceptions import NotFoundError
from ecs.domain.reports import (
    BonusPercentageRow,
    BonusRankingRow,
    DepartmentOverAverageRow,
    EmployeeWithoutBonusRow,
    HighestSalaryRow,
    HighestTotalCompensationRow,
)
from ecs.services.reporting_service import ReportingService


@pytest.fixture
def reporting_repository() -> Mock:
    return Mock()


@pytest.fixture
def reporting_service(reporting_repository: Mock) -> ReportingService:
    return ReportingService(reporting_repository)


def test_get_total_bonus_paid_delegates_to_repository(
    reporting_service: ReportingService,
    reporting_repository: Mock,
) -> None:
    reporting_repository.fetch_total_bonus_paid.return_value = Decimal("102000.00")

    total = reporting_service.get_total_bonus_paid()

    assert total == Decimal("102000.00")
    reporting_repository.fetch_total_bonus_paid.assert_called_once_with()


def test_get_employees_without_bonus_returns_items_and_count(
    reporting_service: ReportingService,
    reporting_repository: Mock,
) -> None:
    rows = [
        EmployeeWithoutBonusRow(employee_id=2, first_name="Ben", last_name="Carter"),
        EmployeeWithoutBonusRow(employee_id=4, first_name="Dana", last_name="Fox"),
    ]
    reporting_repository.fetch_employees_without_bonus.return_value = rows

    result = reporting_service.get_employees_without_bonus()

    assert result.items == rows
    assert result.count == 2


def test_get_bonus_percentages_delegates_to_repository(
    reporting_service: ReportingService,
    reporting_repository: Mock,
) -> None:
    rows = [
        BonusPercentageRow(
            employee_id=1,
            first_name="Aarav",
            last_name="Mehta",
            bonus_percentage=Decimal("8.33"),
        )
    ]
    reporting_repository.fetch_bonus_percentages.return_value = rows

    result = reporting_service.get_bonus_percentages()

    assert result == rows


def test_get_departments_over_average_delegates_to_repository(
    reporting_service: ReportingService,
    reporting_repository: Mock,
) -> None:
    rows = [
        DepartmentOverAverageRow(
            department_id=1,
            department_name="Engineering",
            total_bonus_paid=Decimal("45000.00"),
            average_salary=Decimal("40000.00"),
        )
    ]
    reporting_repository.fetch_departments_over_average.return_value = rows

    result = reporting_service.get_departments_over_average()

    assert result == rows


def test_get_bonus_ranking_delegates_to_repository(
    reporting_service: ReportingService,
    reporting_repository: Mock,
) -> None:
    rows = [
        BonusRankingRow(
            rank=1,
            employee_id=10,
            first_name="Vikram",
            last_name="Singh",
            bonus=Decimal("30000.00"),
        )
    ]
    reporting_repository.fetch_bonus_ranking.return_value = rows

    result = reporting_service.get_bonus_ranking()

    assert result == rows


def test_get_highest_compensation_marks_same_employee(
    reporting_service: ReportingService,
    reporting_repository: Mock,
) -> None:
    salary_row = HighestSalaryRow(
        employee_id=9,
        first_name="Priya",
        last_name="Nair",
        salary=Decimal("200000.00"),
    )
    total_row = HighestTotalCompensationRow(
        employee_id=9,
        first_name="Priya",
        last_name="Nair",
        total_compensation=Decimal("202000.00"),
    )
    reporting_repository.fetch_highest_salary.return_value = salary_row
    reporting_repository.fetch_highest_total_compensation.return_value = total_row

    result = reporting_service.get_highest_compensation()

    assert result.highest_salary_employee == salary_row
    assert result.highest_total_compensation_employee == total_row
    assert result.is_also_highest_total_compensation is True


def test_get_highest_compensation_marks_different_employees(
    reporting_service: ReportingService,
    reporting_repository: Mock,
) -> None:
    salary_row = HighestSalaryRow(
        employee_id=11,
        first_name="High",
        last_name="Salary",
        salary=Decimal("250000.00"),
    )
    total_row = HighestTotalCompensationRow(
        employee_id=12,
        first_name="High",
        last_name="Total",
        total_compensation=Decimal("270000.00"),
    )
    reporting_repository.fetch_highest_salary.return_value = salary_row
    reporting_repository.fetch_highest_total_compensation.return_value = total_row

    result = reporting_service.get_highest_compensation()

    assert result.is_also_highest_total_compensation is False


def test_get_highest_compensation_raises_when_no_employees(
    reporting_service: ReportingService,
    reporting_repository: Mock,
) -> None:
    reporting_repository.fetch_highest_salary.return_value = None
    reporting_repository.fetch_highest_total_compensation.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        reporting_service.get_highest_compensation()

    assert exc_info.value.code == "NO_EMPLOYEES_FOUND"
