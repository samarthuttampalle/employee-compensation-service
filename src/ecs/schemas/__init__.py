"""Pydantic request/response schemas."""

from ecs.schemas.department_schemas import (
    CreateDepartmentRequest,
    DepartmentListResponse,
    DepartmentResponse,
    ForceDeleteDepartmentResponse,
    UpdateDepartmentRequest,
)
from ecs.schemas.employee_schemas import (
    CreateEmployeeRequest,
    EmployeeListResponse,
    EmployeeResponse,
    UpdateEmployeeRequest,
)
from ecs.schemas.report_schemas import (
    BonusPercentageResponse,
    BonusRankingResponse,
    DepartmentsOverAverageResponse,
    EmployeesWithoutBonusResponse,
    HighestCompensationResponse,
    TotalBonusResponse,
)

__all__ = [
    "CreateEmployeeRequest",
    "UpdateEmployeeRequest",
    "EmployeeResponse",
    "EmployeeListResponse",
    "CreateDepartmentRequest",
    "UpdateDepartmentRequest",
    "DepartmentResponse",
    "DepartmentListResponse",
    "ForceDeleteDepartmentResponse",
    "TotalBonusResponse",
    "EmployeesWithoutBonusResponse",
    "BonusPercentageResponse",
    "DepartmentsOverAverageResponse",
    "BonusRankingResponse",
    "HighestCompensationResponse",
]
