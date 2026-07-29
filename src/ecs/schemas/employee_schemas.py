"""Pydantic wire contracts for employee endpoints."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from ecs.domain.employee import Employee

Money = Annotated[Decimal, Field(max_digits=12, decimal_places=2)]


class CreateEmployeeRequest(BaseModel):
    """Inbound body for POST /api/employees."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    first_name: str = Field(alias="firstName", min_length=1, max_length=50)
    last_name: str = Field(alias="lastName", min_length=1, max_length=50)
    department_id: int | None = Field(default=None, alias="departmentId")
    salary: Money = Field(gt=0)
    bonus: Money | None = Field(default=None, ge=0)
    hire_date: date | None = Field(default=None, alias="hireDate")

    @field_validator("hire_date")
    @classmethod
    def hire_date_not_in_future(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("hireDate cannot be in the future")
        return value


class UpdateEmployeeRequest(BaseModel):
    """Inbound body for PATCH /api/employees/{id} — omitted vs explicit null."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    first_name: str | None = Field(default=None, alias="firstName", min_length=1, max_length=50)
    last_name: str | None = Field(default=None, alias="lastName", min_length=1, max_length=50)
    department_id: int | None = Field(default=None, alias="departmentId")
    salary: Money | None = Field(default=None, gt=0)
    bonus: Money | None = Field(default=None, ge=0)
    hire_date: date | None = Field(default=None, alias="hireDate")

    @model_validator(mode="before")
    @classmethod
    def reject_null_for_required_columns(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        non_nullable = {
            "firstName": "firstName cannot be null",
            "lastName": "lastName cannot be null",
            "salary": "salary cannot be null",
            "hireDate": "hireDate cannot be null when provided; omit to leave unchanged",
        }
        for field, message in non_nullable.items():
            if field in data and data[field] is None:
                raise ValueError(message)
        return data

    @field_validator("hire_date")
    @classmethod
    def hire_date_not_in_future(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("hireDate cannot be in the future")
        return value

    def has_updates(self) -> bool:
        """Return True when at least one field was present in the request body."""
        return bool(self.model_fields_set)

    def is_set(self, field_name: str) -> bool:
        """Return True when the field was present in the JSON body (including explicit null)."""
        return field_name in self.model_fields_set


class EmployeeResponse(BaseModel):
    """Outbound employee representation."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    employee_id: int = Field(alias="employeeId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    department_id: int | None = Field(alias="departmentId")
    salary: Money
    bonus: Money | None
    hire_date: date | None = Field(alias="hireDate")
    effective_bonus: Money | None = Field(default=None, alias="effectiveBonus")
    bonus_is_defaulted: bool | None = Field(default=None, alias="bonusIsDefaulted")

    @classmethod
    def from_domain(
        cls,
        employee: Employee,
        *,
        effective_bonus: Decimal | None = None,
        bonus_is_defaulted: bool | None = None,
    ) -> EmployeeResponse:
        """Map a domain Employee to the wire response model."""
        return cls.model_validate(
            {
                "employeeId": employee.employee_id,
                "firstName": employee.first_name,
                "lastName": employee.last_name,
                "departmentId": employee.department_id,
                "salary": employee.salary,
                "bonus": employee.bonus,
                "hireDate": employee.hire_date,
                "effectiveBonus": effective_bonus,
                "bonusIsDefaulted": bonus_is_defaulted,
            }
        )


class EmployeeListResponse(BaseModel):
    """Paginated employee list response."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[EmployeeResponse]
    total: int
    top: int
    skip: int
