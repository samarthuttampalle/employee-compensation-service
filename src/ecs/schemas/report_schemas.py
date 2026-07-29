"""Pydantic wire contracts for reporting endpoints (B1-B6)."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Money = Annotated[Decimal, Field(max_digits=12, decimal_places=2)]
Percentage = Annotated[Decimal, Field(max_digits=12, decimal_places=2)]


class TotalBonusResponse(BaseModel):
    """B1 — company-wide total bonus paid."""

    model_config = ConfigDict(populate_by_name=True)

    total_bonus_paid: Money = Field(alias="totalBonusPaid")


class EmployeeWithoutBonusItem(BaseModel):
    """Single row for B2 — employees who never received a bonus."""

    model_config = ConfigDict(populate_by_name=True)

    employee_id: int = Field(alias="employeeId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")


class EmployeesWithoutBonusResponse(BaseModel):
    """B2 response envelope."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[EmployeeWithoutBonusItem]
    count: int


class BonusPercentageItem(BaseModel):
    """Single row for B3 — bonus as % of salary."""

    model_config = ConfigDict(populate_by_name=True)

    employee_id: int = Field(alias="employeeId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    bonus_percentage: Percentage = Field(alias="bonusPercentage")


class BonusPercentageResponse(BaseModel):
    """B3 response envelope."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[BonusPercentageItem]


class DepartmentOverAverageItem(BaseModel):
    """Single row for B4 — departments where total bonus exceeds average salary."""

    model_config = ConfigDict(populate_by_name=True)

    department_id: int = Field(alias="departmentId")
    department_name: str = Field(alias="departmentName")
    total_bonus_paid: Money = Field(alias="totalBonusPaid")
    average_salary: Money = Field(alias="averageSalary")


class DepartmentsOverAverageResponse(BaseModel):
    """B4 response envelope."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[DepartmentOverAverageItem]


class BonusRankingItem(BaseModel):
    """Single row for B5 — employees ranked by bonus (NULL last)."""

    model_config = ConfigDict(populate_by_name=True)

    rank: int
    employee_id: int = Field(alias="employeeId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    bonus: Money | None


class BonusRankingResponse(BaseModel):
    """B5 response envelope."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[BonusRankingItem]


class HighestSalaryEmployee(BaseModel):
    """Highest base-salary employee summary for B6."""

    model_config = ConfigDict(populate_by_name=True)

    employee_id: int = Field(alias="employeeId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    salary: Money


class HighestTotalCompensationEmployee(BaseModel):
    """Highest total-compensation employee summary for B6."""

    model_config = ConfigDict(populate_by_name=True)

    employee_id: int = Field(alias="employeeId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    total_compensation: Money = Field(alias="totalCompensation")


class HighestCompensationResponse(BaseModel):
    """B6 — highest salary vs highest total compensation comparison."""

    model_config = ConfigDict(populate_by_name=True)

    highest_salary_employee: HighestSalaryEmployee = Field(alias="highestSalaryEmployee")
    is_also_highest_total_compensation: bool = Field(alias="isAlsoHighestTotalCompensation")
    highest_total_compensation_employee: HighestTotalCompensationEmployee = Field(
        alias="highestTotalCompensationEmployee"
    )
