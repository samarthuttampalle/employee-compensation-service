"""Department HTTP blueprint — thin controllers for supporting CRUD."""

from __future__ import annotations

import azure.functions as func

from ecs.api.http_utils import (
    handle_errors,
    json_response,
    no_content_response,
    parse_bool_query,
    parse_json_body,
    parse_positive_int,
)
from ecs.schemas.department_schemas import (
    CreateDepartmentRequest,
    DepartmentListResponse,
    DepartmentResponse,
    ForceDeleteDepartmentResponse,
    UpdateDepartmentRequest,
)
from ecs.services.department_service import DepartmentService

departments_bp = func.Blueprint()  # type: ignore[no-untyped-call]
_department_service: DepartmentService | None = None


def init_department_api(service: DepartmentService) -> None:
    """Bind the department service used by blueprint route handlers."""
    global _department_service
    _department_service = service


def _service() -> DepartmentService:
    if _department_service is None:
        raise RuntimeError("Department API has not been initialized.")
    return _department_service


@departments_bp.route(route="api/departments", methods=["POST"])
@handle_errors
def create_department(
    req: func.HttpRequest,
    context: func.Context,
) -> func.HttpResponse:
    """POST /api/departments — create a new department."""
    request = parse_json_body(req, CreateDepartmentRequest)
    department = _service().create_department(request)
    response = DepartmentResponse.from_domain(department)
    return json_response(
        response,
        201,
        headers={"Location": f"/api/departments/{department.department_id}"},
    )


@departments_bp.route(route="api/departments/{departmentId}", methods=["GET"])
@handle_errors
def get_department(
    req: func.HttpRequest,
    context: func.Context,
) -> func.HttpResponse:
    """GET /api/departments/{departmentId} — retrieve one department."""
    department_id = parse_positive_int(req.route_params.get("departmentId"), "departmentId")
    department = _service().get_department(department_id)
    return json_response(DepartmentResponse.from_domain(department))


@departments_bp.route(route="api/departments", methods=["GET"])
@handle_errors
def list_departments(
    req: func.HttpRequest,
    context: func.Context,
) -> func.HttpResponse:
    """GET /api/departments — list all departments."""
    result = _service().list_departments()
    response = DepartmentListResponse(
        items=[DepartmentResponse.from_domain(item) for item in result.items],
        total=result.total,
    )
    return json_response(response)


@departments_bp.route(route="api/departments/{departmentId}", methods=["PATCH"])
@handle_errors
def update_department(
    req: func.HttpRequest,
    context: func.Context,
) -> func.HttpResponse:
    """PATCH /api/departments/{departmentId} — partial department update."""
    department_id = parse_positive_int(req.route_params.get("departmentId"), "departmentId")
    request = parse_json_body(req, UpdateDepartmentRequest)
    department = _service().update_department(department_id, request)
    return json_response(DepartmentResponse.from_domain(department))


@departments_bp.route(route="api/departments/{departmentId}", methods=["DELETE"])
@handle_errors
def delete_department(
    req: func.HttpRequest,
    context: func.Context,
) -> func.HttpResponse:
    """DELETE /api/departments/{departmentId} — delete a department."""
    department_id = parse_positive_int(req.route_params.get("departmentId"), "departmentId")
    force = parse_bool_query(req.params.get("force"))
    result = _service().delete_department(department_id, force=force)
    if result.unassigned_employees > 0:
        return json_response(
            ForceDeleteDepartmentResponse.model_validate(
                {
                    "departmentId": result.department_id,
                    "unassignedEmployees": result.unassigned_employees,
                }
            )
        )
    return no_content_response()
