"""Azure Functions host entry point — registers blueprints and wires dependencies."""

from __future__ import annotations

import json
import logging

import azure.functions as func

from ecs.api.departments_functions import departments_bp, init_department_api
from ecs.api.employees_functions import employees_bp, init_employee_api
from ecs.api.reports_functions import init_reporting_api, reports_bp
from ecs.core.config import get_settings
from ecs.core.db import get_engine
from ecs.core.logging_config import configure_logging
from ecs.repositories.department_repository import SqlAlchemyDepartmentRepository
from ecs.repositories.employee_repository import SqlAlchemyEmployeeRepository
from ecs.repositories.reporting_repository import SqlAlchemyReportingRepository
from ecs.services.department_service import DepartmentService
from ecs.services.employee_service import EmployeeService
from ecs.services.reporting_service import ReportingService

logger = logging.getLogger(__name__)

configure_logging()

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

_settings = get_settings()
_engine = get_engine()
_employee_repository = SqlAlchemyEmployeeRepository(_engine)
_department_repository = SqlAlchemyDepartmentRepository(_engine)
_reporting_repository = SqlAlchemyReportingRepository(_engine)
_employee_service = EmployeeService(
    _employee_repository,
    _department_repository,
    default_bonus_rate=_settings.default_bonus_rate,
    max_page_size=_settings.max_page_size,
)
_department_service = DepartmentService(_department_repository)
_reporting_service = ReportingService(_reporting_repository)

init_employee_api(_employee_service)
init_department_api(_department_service)
init_reporting_api(_reporting_service)

app.register_blueprint(employees_bp)
app.register_blueprint(departments_bp)
app.register_blueprint(reports_bp)


@app.route(route="api/health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Liveness probe for local development, CI smoke tests, and deployment slots."""
    logger.info("Health check requested")
    body = json.dumps({"status": "healthy", "service": "employee-compensation-service"})
    return func.HttpResponse(body=body, status_code=200, mimetype="application/json")
