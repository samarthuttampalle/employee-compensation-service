"""Data access layer."""

from ecs.repositories.base import (
    DepartmentRepositoryProtocol,
    EmployeeRepositoryProtocol,
    department_table,
    employee_table,
    map_department_row,
    map_employee_row,
    translate_db_errors,
)
from ecs.repositories.department_repository import SqlAlchemyDepartmentRepository
from ecs.repositories.employee_repository import SqlAlchemyEmployeeRepository
from ecs.repositories.reporting_repository import SqlAlchemyReportingRepository

__all__ = [
    "EmployeeRepositoryProtocol",
    "DepartmentRepositoryProtocol",
    "ReportingRepositoryProtocol",
    "SqlAlchemyEmployeeRepository",
    "SqlAlchemyDepartmentRepository",
    "SqlAlchemyReportingRepository",
    "employee_table",
    "department_table",
    "map_employee_row",
    "map_department_row",
    "translate_db_errors",
]
