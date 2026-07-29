"""API (Function) layer — HTTP triggers and response shaping."""

from ecs.api.departments_functions import departments_bp, init_department_api
from ecs.api.employees_functions import employees_bp, init_employee_api
from ecs.api.http_utils import error_response, handle_errors, json_response, no_content_response
from ecs.api.reports_functions import init_reporting_api, reports_bp

__all__ = [
    "employees_bp",
    "departments_bp",
    "reports_bp",
    "init_employee_api",
    "init_department_api",
    "init_reporting_api",
    "handle_errors",
    "json_response",
    "no_content_response",
    "error_response",
]
