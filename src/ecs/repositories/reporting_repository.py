"""Reporting queries — hand-written parameterized T-SQL for B1–B6."""

from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.engine import Engine

from ecs.domain.reports import (
    BonusPercentageRow,
    BonusRankingRow,
    DepartmentOverAverageRow,
    EmployeeWithoutBonusRow,
    HighestSalaryRow,
    HighestTotalCompensationRow,
)
from ecs.repositories.base import translate_db_errors

logger = logging.getLogger(__name__)

_B1_TOTAL_BONUS = text(
    """
    SELECT COALESCE(SUM(COALESCE(Bonus, 0)), 0) AS TotalBonusPaid
    FROM dbo.Employee
    """
)

_B2_EMPLOYEES_WITHOUT_BONUS = text(
    """
    SELECT EmployeeID, FirstName, LastName
    FROM dbo.Employee
    WHERE Bonus IS NULL
    ORDER BY EmployeeID ASC
    """
)

_B3_BONUS_PERCENTAGE = text(
    """
    SELECT
        EmployeeID,
        FirstName,
        LastName,
        ROUND(Bonus / Salary * 100, 2) AS BonusPercentage
    FROM dbo.Employee
    WHERE Bonus IS NOT NULL
    ORDER BY EmployeeID ASC
    """
)

_B4_DEPARTMENTS_OVER_AVERAGE = text(
    """
    SELECT
        d.DepartmentID,
        d.DepartmentName,
        SUM(COALESCE(e.Bonus, 0)) AS TotalBonusPaid,
        AVG(e.Salary) AS AverageSalary
    FROM dbo.Department d
    INNER JOIN dbo.Employee e ON e.DepartmentID = d.DepartmentID
    GROUP BY d.DepartmentID, d.DepartmentName
    HAVING SUM(COALESCE(e.Bonus, 0)) > AVG(e.Salary)
    ORDER BY d.DepartmentID ASC
    """
)

_B5_BONUS_RANKING = text(
    """
    SELECT
        EmployeeID,
        FirstName,
        LastName,
        Bonus,
        RANK() OVER (
            ORDER BY CASE WHEN Bonus IS NULL THEN 1 ELSE 0 END ASC,
                     Bonus DESC
        ) AS BonusRank
    FROM dbo.Employee
    ORDER BY BonusRank ASC, EmployeeID ASC
    """
)

_B6_HIGHEST_SALARY = text(
    """
    SELECT TOP 1 EmployeeID, FirstName, LastName, Salary
    FROM dbo.Employee
    ORDER BY Salary DESC, EmployeeID ASC
    """
)

_B6_HIGHEST_TOTAL_COMPENSATION = text(
    """
    SELECT TOP 1
        EmployeeID,
        FirstName,
        LastName,
        (Salary + COALESCE(Bonus, 0)) AS TotalCompensation
    FROM dbo.Employee
    ORDER BY (Salary + COALESCE(Bonus, 0)) DESC, EmployeeID ASC
    """
)


class SqlAlchemyReportingRepository:
    """Read-only repository for compensation reporting queries."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def fetch_total_bonus_paid(self) -> Decimal:
        """Implements B1: company-wide total bonus with NULL treated as zero."""
        with translate_db_errors(), self._engine.connect() as connection:
            value = connection.execute(_B1_TOTAL_BONUS).scalar_one()
        total = Decimal(str(value))
        logger.debug("Fetched total bonus paid", extra={"total_bonus_paid": total})
        return total

    def fetch_employees_without_bonus(self) -> list[EmployeeWithoutBonusRow]:
        """Implements B2: employees who never received a bonus."""
        with translate_db_errors(), self._engine.connect() as connection:
            rows = connection.execute(_B2_EMPLOYEES_WITHOUT_BONUS).mappings().all()
        return [
            EmployeeWithoutBonusRow(
                employee_id=int(row["EmployeeID"]),
                first_name=str(row["FirstName"]),
                last_name=str(row["LastName"]),
            )
            for row in rows
        ]

    def fetch_bonus_percentages(self) -> list[BonusPercentageRow]:
        """Implements B3: bonus as percentage of salary for employees with a bonus."""
        with translate_db_errors(), self._engine.connect() as connection:
            rows = connection.execute(_B3_BONUS_PERCENTAGE).mappings().all()
        return [
            BonusPercentageRow(
                employee_id=int(row["EmployeeID"]),
                first_name=str(row["FirstName"]),
                last_name=str(row["LastName"]),
                bonus_percentage=Decimal(str(row["BonusPercentage"])),
            )
            for row in rows
        ]

    def fetch_departments_over_average(self) -> list[DepartmentOverAverageRow]:
        """Implements B4: departments where total bonus exceeds average salary."""
        with translate_db_errors(), self._engine.connect() as connection:
            rows = connection.execute(_B4_DEPARTMENTS_OVER_AVERAGE).mappings().all()
        return [
            DepartmentOverAverageRow(
                department_id=int(row["DepartmentID"]),
                department_name=str(row["DepartmentName"]),
                total_bonus_paid=Decimal(str(row["TotalBonusPaid"])),
                average_salary=Decimal(str(row["AverageSalary"])),
            )
            for row in rows
        ]

    def fetch_bonus_ranking(self) -> list[BonusRankingRow]:
        """Implements B5: employees ranked by bonus with NULL bonuses ranked last."""
        with translate_db_errors(), self._engine.connect() as connection:
            rows = connection.execute(_B5_BONUS_RANKING).mappings().all()
        return [
            BonusRankingRow(
                rank=int(row["BonusRank"]),
                employee_id=int(row["EmployeeID"]),
                first_name=str(row["FirstName"]),
                last_name=str(row["LastName"]),
                bonus=Decimal(str(row["Bonus"])) if row["Bonus"] is not None else None,
            )
            for row in rows
        ]

    def fetch_highest_salary(self) -> HighestSalaryRow | None:
        """Implements B6 (part 1): employee with the highest base salary."""
        with translate_db_errors(), self._engine.connect() as connection:
            row = connection.execute(_B6_HIGHEST_SALARY).mappings().first()
        if row is None:
            return None
        return HighestSalaryRow(
            employee_id=int(row["EmployeeID"]),
            first_name=str(row["FirstName"]),
            last_name=str(row["LastName"]),
            salary=Decimal(str(row["Salary"])),
        )

    def fetch_highest_total_compensation(self) -> HighestTotalCompensationRow | None:
        """Implements B6 (part 2): employee with the highest total compensation."""
        with translate_db_errors(), self._engine.connect() as connection:
            row = connection.execute(_B6_HIGHEST_TOTAL_COMPENSATION).mappings().first()
        if row is None:
            return None
        return HighestTotalCompensationRow(
            employee_id=int(row["EmployeeID"]),
            first_name=str(row["FirstName"]),
            last_name=str(row["LastName"]),
            total_compensation=Decimal(str(row["TotalCompensation"])),
        )
