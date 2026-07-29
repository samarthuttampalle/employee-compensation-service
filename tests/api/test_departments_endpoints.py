"""API tests for department HTTP endpoints with mocked services."""

from __future__ import annotations

import json
from unittest.mock import Mock

import azure.functions as func
import pytest

from ecs.api.departments_functions import (
    create_department,
    delete_department,
    get_department,
    init_department_api,
    list_departments,
    update_department,
)
from ecs.core.exceptions import ConflictError, NotFoundError
from ecs.domain.department import Department
from ecs.services.department_service import (
    DepartmentDeleteResult,
    DepartmentListResult,
    DepartmentService,
)


@pytest.fixture
def department_service() -> Mock:
    return Mock(spec=DepartmentService)


@pytest.fixture(autouse=True)
def bind_department_api(department_service: Mock) -> None:
    init_department_api(department_service)


def _sample_department() -> Department:
    return Department(department_id=1, department_name="Engineering", location="Bengaluru")


def test_create_department_returns_201(department_service: Mock, function_context) -> None:
    department_service.create_department.return_value = _sample_department()
    req = func.HttpRequest(
        method="POST",
        url="/api/departments",
        body=json.dumps({"departmentName": "Engineering", "location": "Bengaluru"}).encode(),
        headers={"Content-Type": "application/json"},
    )

    resp = create_department(req, function_context)  # type: ignore[arg-type]

    assert resp.status_code == 201
    body = json.loads(resp.get_body())
    assert body["departmentName"] == "Engineering"


def test_get_department_returns_404_when_missing(
    department_service: Mock,
    function_context,
) -> None:
    department_service.get_department.side_effect = NotFoundError.for_resource("Department", 9)
    req = func.HttpRequest(
        method="GET",
        url="/api/departments/9",
        body=b"",
        route_params={"departmentId": "9"},
    )

    resp = get_department(req, function_context)  # type: ignore[arg-type]

    assert resp.status_code == 404
    body = json.loads(resp.get_body())
    assert body["error"]["code"] == "DEPARTMENT_NOT_FOUND"


def test_list_departments_returns_items(department_service: Mock, function_context) -> None:
    department_service.list_departments.return_value = DepartmentListResult(
        items=[_sample_department()],
        total=1,
    )
    req = func.HttpRequest(method="GET", url="/api/departments", body=b"")

    resp = list_departments(req, function_context)  # type: ignore[arg-type]

    assert resp.status_code == 200
    body = json.loads(resp.get_body())
    assert body["total"] == 1


def test_update_department_returns_updated_resource(
    department_service: Mock,
    function_context,
) -> None:
    department_service.update_department.return_value = Department(1, "Engineering", None)
    req = func.HttpRequest(
        method="PATCH",
        url="/api/departments/1",
        route_params={"departmentId": "1"},
        body=json.dumps({"location": None}).encode(),
        headers={"Content-Type": "application/json"},
    )

    resp = update_department(req, function_context)  # type: ignore[arg-type]

    assert resp.status_code == 200
    body = json.loads(resp.get_body())
    assert body["location"] is None


def test_delete_department_without_force_returns_409(
    department_service: Mock,
    function_context,
) -> None:
    department_service.delete_department.side_effect = ConflictError(
        "Department has assigned employees.",
        code="DEPARTMENT_HAS_EMPLOYEES",
    )
    req = func.HttpRequest(
        method="DELETE",
        url="/api/departments/1",
        body=b"",
        route_params={"departmentId": "1"},
    )

    resp = delete_department(req, function_context)  # type: ignore[arg-type]

    assert resp.status_code == 409
    body = json.loads(resp.get_body())
    assert body["error"]["code"] == "DEPARTMENT_HAS_EMPLOYEES"


def test_delete_department_with_force_returns_unassigned_count(
    department_service: Mock,
    function_context,
) -> None:
    department_service.delete_department.return_value = DepartmentDeleteResult(
        department_id=1,
        unassigned_employees=4,
    )
    req = func.HttpRequest(
        method="DELETE",
        url="/api/departments/1?force=true",
        body=b"",
        route_params={"departmentId": "1"},
        params={"force": "true"},
    )

    resp = delete_department(req, function_context)  # type: ignore[arg-type]

    assert resp.status_code == 200
    body = json.loads(resp.get_body())
    assert body["unassignedEmployees"] == 4


def test_delete_empty_department_returns_204(department_service: Mock, function_context) -> None:
    department_service.delete_department.return_value = DepartmentDeleteResult(
        department_id=1,
        unassigned_employees=0,
    )
    req = func.HttpRequest(
        method="DELETE",
        url="/api/departments/1",
        body=b"",
        route_params={"departmentId": "1"},
    )

    resp = delete_department(req, function_context)  # type: ignore[arg-type]

    assert resp.status_code == 204
