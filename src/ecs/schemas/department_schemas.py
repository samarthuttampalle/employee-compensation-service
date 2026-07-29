"""Pydantic wire contracts for department endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ecs.domain.department import Department


class CreateDepartmentRequest(BaseModel):
    """Inbound body for POST /api/departments."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    department_name: str = Field(alias="departmentName", min_length=1, max_length=100)
    location: str | None = Field(default=None, max_length=100)


class UpdateDepartmentRequest(BaseModel):
    """Inbound body for PATCH /api/departments/{id} — omitted vs explicit null."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    department_name: str | None = Field(
        default=None, alias="departmentName", min_length=1, max_length=100
    )
    location: str | None = Field(default=None, max_length=100)

    @model_validator(mode="before")
    @classmethod
    def reject_null_for_required_columns(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "departmentName" in data and data["departmentName"] is None:
            raise ValueError("departmentName cannot be null")
        return data

    def has_updates(self) -> bool:
        """Return True when at least one field was present in the request body."""
        return bool(self.model_fields_set)

    def is_set(self, field_name: str) -> bool:
        """Return True when the field was present in the JSON body (including explicit null)."""
        return field_name in self.model_fields_set


class DepartmentResponse(BaseModel):
    """Outbound department representation."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    department_id: int = Field(alias="departmentId")
    department_name: str = Field(alias="departmentName")
    location: str | None

    @classmethod
    def from_domain(cls, department: Department) -> DepartmentResponse:
        """Map a domain Department to the wire response model."""
        return cls.model_validate(
            {
                "departmentId": department.department_id,
                "departmentName": department.department_name,
                "location": department.location,
            }
        )


class DepartmentListResponse(BaseModel):
    """Department list response."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[DepartmentResponse]
    total: int


class ForceDeleteDepartmentResponse(BaseModel):
    """Response body when a department is deleted with force=true."""

    model_config = ConfigDict(populate_by_name=True)

    department_id: int = Field(alias="departmentId")
    unassigned_employees: int = Field(alias="unassignedEmployees")
