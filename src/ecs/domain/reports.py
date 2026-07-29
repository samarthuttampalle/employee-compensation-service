"""Domain types for reporting query results."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class EmployeeWithoutBonusRow:
    """B2 row — employee who never received a bonus."""

    employee_id: int
    first_name: str
    last_name: str


@dataclass(frozen=True, slots=True)
class BonusPercentageRow:
    """B3 row — bonus as a percentage of salary."""

    employee_id: int
    first_name: str
    last_name: str
    bonus_percentage: Decimal


@dataclass(frozen=True, slots=True)
class DepartmentOverAverageRow:
    """B4 row — department where total bonus exceeds average salary."""

    department_id: int
    department_name: str
    total_bonus_paid: Decimal
    average_salary: Decimal


@dataclass(frozen=True, slots=True)
class BonusRankingRow:
    """B5 row — employee ranked by bonus amount."""

    rank: int
    employee_id: int
    first_name: str
    last_name: str
    bonus: Decimal | None


@dataclass(frozen=True, slots=True)
class HighestSalaryRow:
    """B6 row — employee with the highest base salary."""

    employee_id: int
    first_name: str
    last_name: str
    salary: Decimal


@dataclass(frozen=True, slots=True)
class HighestTotalCompensationRow:
    """B6 row — employee with the highest total compensation."""

    employee_id: int
    first_name: str
    last_name: str
    total_compensation: Decimal
