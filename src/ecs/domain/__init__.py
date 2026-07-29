"""Domain types — engine-agnostic dataclasses."""

from ecs.domain.department import Department
from ecs.domain.employee import Employee
from ecs.domain.reports import (
    BonusPercentageRow,
    BonusRankingRow,
    DepartmentOverAverageRow,
    EmployeeWithoutBonusRow,
    HighestSalaryRow,
    HighestTotalCompensationRow,
)

__all__ = [
    "Employee",
    "Department",
    "EmployeeWithoutBonusRow",
    "BonusPercentageRow",
    "DepartmentOverAverageRow",
    "BonusRankingRow",
    "HighestSalaryRow",
    "HighestTotalCompensationRow",
]
