"""Reporting business logic — thin orchestration over reporting queries."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ecs.core.exceptions import NotFoundError
from ecs.domain.reports import (
    BonusPercentageRow,
    BonusRankingRow,
    DepartmentOverAverageRow,
    EmployeeWithoutBonusRow,
    HighestSalaryRow,
    HighestTotalCompensationRow,
)
from ecs.repositories.base import ReportingRepositoryProtocol


@dataclass(frozen=True, slots=True)
class EmployeesWithoutBonusResult:
    """B2 result envelope."""

    items: list[EmployeeWithoutBonusRow]
    count: int


@dataclass(frozen=True, slots=True)
class HighestCompensationResult:
    """B6 comparison result assembled in the service layer."""

    highest_salary_employee: HighestSalaryRow
    is_also_highest_total_compensation: bool
    highest_total_compensation_employee: HighestTotalCompensationRow


class ReportingService:
    """Read-only reporting orchestration for Part B endpoints."""

    def __init__(self, reporting_repository: ReportingRepositoryProtocol) -> None:
        self._reporting_repository = reporting_repository

    def get_total_bonus_paid(self) -> Decimal:
        """Return B1 — company-wide total bonus paid."""
        return self._reporting_repository.fetch_total_bonus_paid()

    def get_employees_without_bonus(self) -> EmployeesWithoutBonusResult:
        """Return B2 — employees who never received a bonus."""
        items = self._reporting_repository.fetch_employees_without_bonus()
        return EmployeesWithoutBonusResult(items=items, count=len(items))

    def get_bonus_percentages(self) -> list[BonusPercentageRow]:
        """Return B3 — bonus as a percentage of salary."""
        return self._reporting_repository.fetch_bonus_percentages()

    def get_departments_over_average(self) -> list[DepartmentOverAverageRow]:
        """Return B4 — departments where total bonus exceeds average salary."""
        return self._reporting_repository.fetch_departments_over_average()

    def get_bonus_ranking(self) -> list[BonusRankingRow]:
        """Return B5 — employees ranked by bonus amount."""
        return self._reporting_repository.fetch_bonus_ranking()

    def get_highest_compensation(self) -> HighestCompensationResult:
        """Return B6 — highest salary vs highest total compensation comparison."""
        highest_salary = self._reporting_repository.fetch_highest_salary()
        highest_total = self._reporting_repository.fetch_highest_total_compensation()
        if highest_salary is None or highest_total is None:
            raise NotFoundError("No employees found.", code="NO_EMPLOYEES_FOUND")

        return HighestCompensationResult(
            highest_salary_employee=highest_salary,
            is_also_highest_total_compensation=(
                highest_salary.employee_id == highest_total.employee_id
            ),
            highest_total_compensation_employee=highest_total,
        )
