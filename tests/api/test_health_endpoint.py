"""Smoke tests for the health-check endpoint."""

import json

import azure.functions as func

from ecs.function_app import health_check


def test_health_check_returns_200() -> None:
    req = func.HttpRequest(method="GET", url="/api/health", body=b"")
    resp = health_check(req)
    assert resp.status_code == 200
    body = json.loads(resp.get_body())
    assert body["status"] == "healthy"
    assert body["service"] == "employee-compensation-service"
