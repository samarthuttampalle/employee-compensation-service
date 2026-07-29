"""Reporting HTTP blueprint — thin controllers for Part B read-only endpoints."""

from __future__ import annotations

import azure.functions as func

from ecs.api.http_utils import handle_errors, json_response
from ecs.domain.reports import (
    BonusPercentageRow,
    BonusRankingRow,
    DepartmentOverAverageRow,
    EmployeeWithoutBonusRow,
)
from ecs.schemas.report_schemas import (
    BonusPercentageItem,
    BonusPercentageResponse,
    BonusRankingItem,
    BonusRankingResponse,
    DepartmentOverAverageItem,
    DepartmentsOverAverageResponse,
    EmployeesWithoutBonusResponse,
    EmployeeWithoutBonusItem,
    HighestCompensationResponse,
    HighestSalaryEmployee,
    HighestTotalCompensationEmployee,
    TotalBonusResponse,
)
from ecs.services.reporting_service import ReportingService

reports_bp = func.Blueprint()  # type: ignore[no-untyped-call]
_reporting_service: ReportingService | None = None


def init_reporting_api(service: ReportingService) -> None:
    """Bind the reporting service used by blueprint route handlers."""
    global _reporting_service
    _reporting_service = service


def _service() -> ReportingService:
    if _reporting_service is None:
        raise RuntimeError("Reporting API has not been initialized.")
    return _reporting_service


def _employee_without_bonus_item(row: EmployeeWithoutBonusRow) -> EmployeeWithoutBonusItem:
    return EmployeeWithoutBonusItem.model_validate(
        {
            "employeeId": row.employee_id,
            "firstName": row.first_name,
            "lastName": row.last_name,
        }
    )


def _bonus_percentage_item(row: BonusPercentageRow) -> BonusPercentageItem:
    return BonusPercentageItem.model_validate(
        {
            "employeeId": row.employee_id,
            "firstName": row.first_name,
            "lastName": row.last_name,
            "bonusPercentage": row.bonus_percentage,
        }
    )


def _department_over_average_item(row: DepartmentOverAverageRow) -> DepartmentOverAverageItem:
    return DepartmentOverAverageItem.model_validate(
        {
            "departmentId": row.department_id,
            "departmentName": row.department_name,
            "totalBonusPaid": row.total_bonus_paid,
            "averageSalary": row.average_salary,
        }
    )


def _bonus_ranking_item(row: BonusRankingRow) -> BonusRankingItem:
    return BonusRankingItem.model_validate(
        {
            "rank": row.rank,
            "employeeId": row.employee_id,
            "firstName": row.first_name,
            "lastName": row.last_name,
            "bonus": row.bonus,
        }
    )


@reports_bp.route(route="api/reports/total-bonus", methods=["GET"])
@handle_errors
def get_total_bonus(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    """GET /api/reports/total-bonus — B1."""
    total = _service().get_total_bonus_paid()
    return json_response(TotalBonusResponse.model_validate({"totalBonusPaid": total}))


@reports_bp.route(route="api/reports/employees-without-bonus", methods=["GET"])
@handle_errors
def get_employees_without_bonus(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    """GET /api/reports/employees-without-bonus — B2."""
    result = _service().get_employees_without_bonus()
    response = EmployeesWithoutBonusResponse(
        items=[_employee_without_bonus_item(item) for item in result.items],
        count=result.count,
    )
    return json_response(response)


@reports_bp.route(route="api/reports/bonus-percentage", methods=["GET"])
@handle_errors
def get_bonus_percentage(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    """GET /api/reports/bonus-percentage — B3."""
    items = _service().get_bonus_percentages()
    response = BonusPercentageResponse(items=[_bonus_percentage_item(item) for item in items])
    return json_response(response)


@reports_bp.route(route="api/reports/departments-over-average", methods=["GET"])
@handle_errors
def get_departments_over_average(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    """GET /api/reports/departments-over-average — B4."""
    items = _service().get_departments_over_average()
    response = DepartmentsOverAverageResponse(
        items=[_department_over_average_item(item) for item in items]
    )
    return json_response(response)


@reports_bp.route(route="api/reports/bonus-ranking", methods=["GET"])
@handle_errors
def get_bonus_ranking(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    """GET /api/reports/bonus-ranking — B5."""
    items = _service().get_bonus_ranking()
    response = BonusRankingResponse(items=[_bonus_ranking_item(item) for item in items])
    return json_response(response)


@reports_bp.route(route="api/reports/highest-compensation", methods=["GET"])
@handle_errors
def get_highest_compensation(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    """GET /api/reports/highest-compensation — B6."""
    result = _service().get_highest_compensation()
    response = HighestCompensationResponse.model_validate(
        {
            "highestSalaryEmployee": HighestSalaryEmployee.model_validate(
                {
                    "employeeId": result.highest_salary_employee.employee_id,
                    "firstName": result.highest_salary_employee.first_name,
                    "lastName": result.highest_salary_employee.last_name,
                    "salary": result.highest_salary_employee.salary,
                }
            ),
            "isAlsoHighestTotalCompensation": result.is_also_highest_total_compensation,
            "highestTotalCompensationEmployee": HighestTotalCompensationEmployee.model_validate(
                {
                    "employeeId": result.highest_total_compensation_employee.employee_id,
                    "firstName": result.highest_total_compensation_employee.first_name,
                    "lastName": result.highest_total_compensation_employee.last_name,
                    "totalCompensation": (
                        result.highest_total_compensation_employee.total_compensation
                    ),
                }
            ),
        }
    )
    return json_response(response)
