"""SQLAlchemy engine factory and connectivity helpers."""

from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from ecs.core.config import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create and cache a SQLAlchemy engine for Azure SQL/SQL Server."""
    settings = get_settings()
    odbc_connection_string = settings.sql_connection_string.get_secret_value()
    connection_url = f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_connection_string)}"
    return create_engine(
        connection_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True,
    )


def verify_database_connection() -> bool:
    """Run a lightweight query to confirm DB connectivity."""
    engine = get_engine()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
