"""API tests for reporting HTTP endpoints with mocked services."""

from __future__ import annotations

import json
from decimal import Decimal
from unittest.mock import Mock

import azure.functions as func
import pytest

from ecs.api.reports_functions import (
    get_bonus_percentage,
    get_bonus_ranking,
    get_departments_over_average,
    get_employees_without_bonus,
    get_highest_compensation,
    get_total_bonus,
    init_reporting_api,
)
from ecs.core.exceptions import NotFoundError
from ecs.domain.reports import (
    BonusPercentageRow,
    BonusRankingRow,
    DepartmentOverAverageRow,
    EmployeeWithoutBonusRow,
    HighestSalaryRow,
    HighestTotalCompensationRow,
)
from ecs.services.reporting_service import (
    EmployeesWithoutBonusResult,
    HighestCompensationResult,
    ReportingService,
)


@pytest.fixture
def reporting_service() -> Mock:
    return Mock(spec=ReportingService)


@pytest.fixture(autouse=True)
def bind_reporting_api(reporting_service: Mock) -> None:
    init_reporting_api(reporting_service)


def test_get_total_bonus_returns_200(reporting_service: Mock, function_context) -> None:
    reporting_service.get_total_bonus_paid.return_value = Decimal("102000.00")
    req = func.HttpRequest(method="GET", url="/api/reports/total-bonus", body=b"")

    resp = get_total_bonus(req, function_context)  # type: ignore[arg-type]

    assert resp.status_code == 200
    body = json.loads(resp.get_body())
    assert body["totalBonusPaid"] == "102000.00"


def test_get_employees_without_bonus_returns_items_and_count(
    reporting_service: Mock,
    function_context,
) -> None:
    rows = [
        EmployeeWithoutBonusRow(employee_id=2, first_name="Ben", last_name="Carter"),
        EmployeeWithoutBonusRow(employee_id=4, first_name="Dana", last_name="Fox"),
    ]
    reporting_service.get_employees_without_bonus.return_value = EmployeesWithoutBonusResult(
        items=rows,
        count=2,
    )
    req = func.HttpRequest(
        method="GET",
        url="/api/reports/employees-without-bonus",
        body=b"",
    )

    resp = get_employees_without_bonus(req, function_context)  # type: ignore[arg-type]

    assert resp.status_code == 200
    body = json.loads(resp.get_body())
    assert body["count"] == 2
    assert len(body["items"]) == 2
    assert body["items"][0]["employeeId"] == 2


def test_get_bonus_percentage_returns_items(reporting_service: Mock, function_context) -> None:
    rows = [
        BonusPercentageRow(
            employee_id=1,
            first_name="Aarav",
            last_name="Mehta",
            bonus_percentage=Decimal("8.33"),
        )
    ]
    reporting_service.get_bonus_percentages.return_value = rows
    req = func.HttpRequest(method="GET", url="/api/reports/bonus-percentage", body=b"")

    resp = get_bonus_percentage(req, function_context)  # type: ignore[arg-type]

    assert resp.status_code == 200
    body = json.loads(resp.get_body())
    assert body["items"][0]["bonusPercentage"] == "8.33"


def test_get_departments_over_average_returns_items(
    reporting_service: Mock,
    function_context,
) -> None:
    rows = [
        DepartmentOverAverageRow(
            department_id=1,
            department_name="Engineering",
            total_bonus_paid=Decimal("45000.00"),
            average_salary=Decimal("40000.00"),
        )
    ]
    reporting_service.get_departments_over_average.return_value = rows
    req = func.HttpRequest(
        method="GET",
        url="/api/reports/departments-over-average",
        body=b"",
    )

    resp = get_departments_over_average(req, function_context)  # type: ignore[arg-type]

    assert resp.status_code == 200
    body = json.loads(resp.get_body())
    assert body["items"][0]["departmentName"] == "Engineering"


def test_get_bonus_ranking_returns_items(reporting_service: Mock, function_context) -> None:
    rows = [
        BonusRankingRow(
            rank=1,
            employee_id=10,
            first_name="Vikram",
            last_name="Singh",
            bonus=Decimal("30000.00"),
        )
    ]
    reporting_service.get_bonus_ranking.return_value = rows
    req = func.HttpRequest(method="GET", url="/api/reports/bonus-ranking", body=b"")

    resp = get_bonus_ranking(req, function_context)  # type: ignore[arg-type]

    assert resp.status_code == 200
    body = json.loads(resp.get_body())
    assert body["items"][0]["rank"] == 1
    assert body["items"][0]["bonus"] == "30000.00"


def test_get_highest_compensation_returns_comparison(
    reporting_service: Mock,
    function_context,
) -> None:
    reporting_service.get_highest_compensation.return_value = HighestCompensationResult(
        highest_salary_employee=HighestSalaryRow(
            employee_id=9,
            first_name="Priya",
            last_name="Nair",
            salary=Decimal("200000.00"),
        ),
        is_also_highest_total_compensation=True,
        highest_total_compensation_employee=HighestTotalCompensationRow(
            employee_id=9,
            first_name="Priya",
            last_name="Nair",
            total_compensation=Decimal("202000.00"),
        ),
    )
    req = func.HttpRequest(
        method="GET",
        url="/api/reports/highest-compensation",
        body=b"",
    )

    resp = get_highest_compensation(req, function_context)  # type: ignore[arg-type]

    assert resp.status_code == 200
    body = json.loads(resp.get_body())
    assert body["isAlsoHighestTotalCompensation"] is True
    assert body["highestSalaryEmployee"]["employeeId"] == 9
    assert body["highestTotalCompensationEmployee"]["totalCompensation"] == "202000.00"


def test_get_highest_compensation_returns_404_when_no_employees(
    reporting_service: Mock,
    function_context,
) -> None:
    reporting_service.get_highest_compensation.side_effect = NotFoundError(
        "No employees found.",
        code="NO_EMPLOYEES_FOUND",
    )
    req = func.HttpRequest(
        method="GET",
        url="/api/reports/highest-compensation",
        body=b"",
    )

    resp = get_highest_compensation(req, function_context)  # type: ignore[arg-type]

    assert resp.status_code == 404
    body = json.loads(resp.get_body())
    assert body["error"]["code"] == "NO_EMPLOYEES_FOUND"
