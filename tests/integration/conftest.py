"""Integration test fixtures — local SQL Server (no Docker)."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import quote_plus

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from ecs.repositories.department_repository import SqlAlchemyDepartmentRepository
from ecs.repositories.employee_repository import SqlAlchemyEmployeeRepository
from ecs.repositories.reporting_repository import SqlAlchemyReportingRepository

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql"


def _read_connection_string_from_json(path: Path) -> str | None:
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8-sig").strip()
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    values = payload.get("Values", {})
    connection_string = values.get("SQL_CONNECTION_STRING")
    if isinstance(connection_string, str) and connection_string.strip():
        return connection_string.strip()
    return None


def _load_sql_connection_string() -> str | None:
    env_value = os.environ.get("SQL_CONNECTION_STRING")
    if env_value and env_value.strip():
        return env_value.strip()

    for candidate in (ROOT / "local.settings.json", ROOT / "local.settings.json.example"):
        connection_string = _read_connection_string_from_json(candidate)
        if connection_string and "<your-sql-server>" not in connection_string:
            return connection_string
    return None


def _split_sql_batches(script: str) -> list[str]:
    batches = re.split(r"^\s*GO\s*$", script, flags=re.IGNORECASE | re.MULTILINE)
    return [batch.strip() for batch in batches if batch.strip()]


def _execute_sql_file(engine: Engine, relative_path: str) -> None:
    script = (SQL_DIR / relative_path).read_text(encoding="utf-8")
    with engine.begin() as connection:
        for batch in _split_sql_batches(script):
            connection.execute(text(batch))


@pytest.fixture(scope="session")
def sql_connection_string() -> str:
    connection_string = _load_sql_connection_string()
    if not connection_string:
        pytest.skip(
            "SQL_CONNECTION_STRING not set and local.settings.json has no connection string"
        )
    return connection_string


@pytest.fixture(scope="session")
def engine(sql_connection_string: str) -> Iterator[Engine]:
    """Create a session-scoped engine and ensure schema + seed data exist."""
    url = f"mssql+pyodbc:///?odbc_connect={quote_plus(sql_connection_string)}"
    eng = create_engine(url, pool_pre_ping=True, future=True)
    try:
        with eng.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — surface connectivity issues as skip
        pytest.skip(f"Cannot connect to SQL Server: {exc}")

    _execute_sql_file(eng, "003_drop_schema.sql")
    _execute_sql_file(eng, "001_create_schema.sql")
    _execute_sql_file(eng, "002_seed_data.sql")
    yield eng
    eng.dispose()


@pytest.fixture(autouse=True)
def reset_database(engine: Engine) -> Iterator[None]:
    """Reset schema data before every integration test for isolation."""
    _execute_sql_file(engine, "003_drop_schema.sql")
    _execute_sql_file(engine, "001_create_schema.sql")
    _execute_sql_file(engine, "002_seed_data.sql")
    yield


@pytest.fixture
def employee_repository(engine: Engine) -> SqlAlchemyEmployeeRepository:
    return SqlAlchemyEmployeeRepository(engine)


@pytest.fixture
def department_repository(engine: Engine) -> SqlAlchemyDepartmentRepository:
    return SqlAlchemyDepartmentRepository(engine)


@pytest.fixture
def reporting_repository(engine: Engine) -> SqlAlchemyReportingRepository:
    return SqlAlchemyReportingRepository(engine)
