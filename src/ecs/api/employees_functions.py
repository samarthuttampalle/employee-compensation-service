"""Employee HTTP blueprint — thin controllers for Part A CRUD."""

from __future__ import annotations

import azure.functions as func

from ecs.api.http_utils import (
    handle_errors,
    json_response,
    no_content_response,
    parse_bool_query,
    parse_json_body,
    parse_non_negative_int,
    parse_optional_positive_int,
    parse_positive_int,
)
from ecs.schemas.employee_schemas import (
    CreateEmployeeRequest,
    EmployeeListResponse,
    EmployeeResponse,
    UpdateEmployeeRequest,
)
from ecs.services.employee_service import EmployeeService

employees_bp = func.Blueprint()  # type: ignore[no-untyped-call]
_employee_service: EmployeeService | None = None


def init_employee_api(service: EmployeeService) -> None:
    """Bind the employee service used by blueprint route handlers."""
    global _employee_service
    _employee_service = service


def _service() -> EmployeeService:
    if _employee_service is None:
        raise RuntimeError("Employee API has not been initialized.")
    return _employee_service


@employees_bp.route(route="api/employees", methods=["POST"])
@handle_errors
def create_employee(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    """POST /api/employees — create a new employee."""
    request = parse_json_body(req, CreateEmployeeRequest)
    employee = _service().create_employee(request)
    response = EmployeeResponse.from_domain(employee)
    return json_response(
        response,
        201,
        headers={"Location": f"/api/employees/{employee.employee_id}"},
    )


@employees_bp.route(route="api/employees/{employeeId}", methods=["GET"])
@handle_errors
def get_employee(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    """GET /api/employees/{employeeId} — retrieve one employee."""
    employee_id = parse_positive_int(req.route_params.get("employeeId"), "employeeId")
    apply_default_bonus = parse_bool_query(req.params.get("applyDefaultBonus"))
    result = _service().get_employee(employee_id, apply_default_bonus=apply_default_bonus)
    response = EmployeeResponse.from_domain(
        result.employee,
        effective_bonus=result.effective_bonus,
        bonus_is_defaulted=result.bonus_is_defaulted if apply_default_bonus else None,
    )
    return json_response(response)


@employees_bp.route(route="api/employees", methods=["GET"])
@handle_errors
def list_employees(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    """GET /api/employees — list employees with optional filters."""
    department_id = parse_optional_positive_int(req.params.get("departmentId"), "departmentId")
    top = parse_non_negative_int(req.params.get("top"), "top", default=50)
    skip = parse_non_negative_int(req.params.get("skip"), "skip", default=0)
    result = _service().list_employees(department_id=department_id, top=top, skip=skip)
    response = EmployeeListResponse(
        items=[EmployeeResponse.from_domain(item) for item in result.items],
        total=result.total,
        top=result.top,
        skip=result.skip,
    )
    return json_response(response)


@employees_bp.route(route="api/employees/{employeeId}", methods=["PATCH"])
@handle_errors
def update_employee(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    """PATCH /api/employees/{employeeId} — partial employee update."""
    employee_id = parse_positive_int(req.route_params.get("employeeId"), "employeeId")
    request = parse_json_body(req, UpdateEmployeeRequest)
    employee = _service().update_employee(employee_id, request)
    return json_response(EmployeeResponse.from_domain(employee))


@employees_bp.route(route="api/employees/{employeeId}", methods=["DELETE"])
@handle_errors
def delete_employee(
    req: func.HttpRequest,
    context: func.Context | None = None,
) -> func.HttpResponse:
    """DELETE /api/employees/{employeeId} — delete an employee."""
    employee_id = parse_positive_int(req.route_params.get("employeeId"), "employeeId")
    _service().delete_employee(employee_id)
    return no_content_response()
