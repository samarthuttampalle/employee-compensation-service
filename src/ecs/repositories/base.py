"""Repository shared infrastructure — tables, protocols, and error translation."""

from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from typing import Protocol

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError, SQLAlchemyError

from ecs.core.exceptions import ConflictError, DependencyError, ValidationError
from ecs.domain.department import Department
from ecs.domain.employee import Employee
from ecs.domain.reports import (
    BonusPercentageRow,
    BonusRankingRow,
    DepartmentOverAverageRow,
    EmployeeWithoutBonusRow,
    HighestSalaryRow,
    HighestTotalCompensationRow,
)

logger = logging.getLogger(__name__)

metadata = MetaData()

department_table = Table(
    "Department",
    metadata,
    Column("DepartmentID", Integer, primary_key=True, autoincrement=True),
    Column("DepartmentName", String(100), nullable=False),
    Column("Location", String(100), nullable=True),
    UniqueConstraint("DepartmentName", name="UQ_Department_DepartmentName"),
    schema="dbo",
)

employee_table = Table(
    "Employee",
    metadata,
    Column("EmployeeID", Integer, primary_key=True, autoincrement=True),
    Column("FirstName", String(50), nullable=False),
    Column("LastName", String(50), nullable=False),
    Column(
        "DepartmentID",
        Integer,
        ForeignKey("dbo.Department.DepartmentID", ondelete="SET NULL"),
        nullable=True,
    ),
    Column("Salary", Numeric(12, 2), nullable=False),
    Column("Bonus", Numeric(12, 2), nullable=True),
    Column("HireDate", Date, nullable=True),
    CheckConstraint("Salary > 0", name="CK_Employee_Salary_Positive"),
    CheckConstraint("Bonus IS NULL OR Bonus >= 0", name="CK_Employee_Bonus_NonNegative"),
    schema="dbo",
)


def _as_int(value: object) -> int:
    return int(str(value))


def _as_optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(str(value))


def _coerce_hire_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def map_employee_row(row: RowMapping | Mapping[str, object]) -> Employee:
    """Map a database row to an Employee domain object."""
    return Employee(
        employee_id=_as_int(row["EmployeeID"]),
        first_name=str(row["FirstName"]),
        last_name=str(row["LastName"]),
        department_id=_as_optional_int(row["DepartmentID"]),
        salary=Decimal(str(row["Salary"])),
        bonus=Decimal(str(row["Bonus"])) if row["Bonus"] is not None else None,
        hire_date=_coerce_hire_date(row["HireDate"]),
    )


def map_department_row(row: RowMapping | Mapping[str, object]) -> Department:
    """Map a database row to a Department domain object."""
    location = row["Location"]
    return Department(
        department_id=_as_int(row["DepartmentID"]),
        department_name=str(row["DepartmentName"]),
        location=str(location) if location is not None else None,
    )


@contextmanager
def translate_db_errors() -> Iterator[None]:
    """Translate SQLAlchemy/driver exceptions into domain exceptions."""
    try:
        yield
    except IntegrityError as exc:
        message = str(exc.orig) if getattr(exc, "orig", None) is not None else str(exc)
        lowered = message.lower()
        if "uq_department_departmentname" in lowered or "unique" in lowered:
            raise ConflictError(
                "A department with this name already exists.",
                code="DEPARTMENT_NAME_CONFLICT",
            ) from exc
        if "ck_employee_salary" in lowered or "ck_employee_bonus" in lowered or "check" in lowered:
            raise ValidationError("Database constraint validation failed.") from exc
        if "fk_employee_department" in lowered or "foreign key" in lowered:
            raise ValidationError("Referenced department does not exist.") from exc
        raise ValidationError("Database integrity constraint violated.") from exc
    except OperationalError as exc:
        logger.error(
            "Database operational error",
            extra={"exception_type": type(exc).__name__},
        )
        raise DependencyError("Database temporarily unavailable.") from exc
    except DBAPIError as exc:
        if getattr(exc, "connection_invalidated", False):
            logger.error(
                "Database connection invalidated",
                extra={"exception_type": type(exc).__name__},
            )
            raise DependencyError("Database temporarily unavailable.") from exc
        logger.error(
            "Database driver error",
            extra={"exception_type": type(exc).__name__},
        )
        raise DependencyError("Database temporarily unavailable.") from exc
    except SQLAlchemyError as exc:
        logger.error(
            "Database error",
            extra={"exception_type": type(exc).__name__},
        )
        raise DependencyError("Database temporarily unavailable.") from exc


class EmployeeRepositoryProtocol(Protocol):
    """Persistence contract for the Employee aggregate."""

    def get_by_id(self, employee_id: int) -> Employee | None: ...

    def list_employees(
        self,
        *,
        department_id: int | None,
        top: int,
        skip: int,
    ) -> tuple[list[Employee], int]: ...

    def insert(
        self,
        *,
        first_name: str,
        last_name: str,
        department_id: int | None,
        salary: Decimal,
        bonus: Decimal | None,
        hire_date: date | None,
    ) -> Employee: ...

    def update(self, employee_id: int, updates: Mapping[str, object]) -> Employee | None: ...

    def delete(self, employee_id: int) -> bool: ...


class DepartmentRepositoryProtocol(Protocol):
    """Persistence contract for the Department aggregate."""

    def get_by_id(self, department_id: int) -> Department | None: ...

    def list_departments(self) -> tuple[list[Department], int]: ...

    def insert(self, *, department_name: str, location: str | None) -> Department: ...

    def update(self, department_id: int, updates: Mapping[str, object]) -> Department | None: ...

    def delete(self, department_id: int) -> bool: ...

    def count_employees(self, department_id: int) -> int: ...

    def unassign_employees(self, department_id: int) -> int: ...


class ReportingRepositoryProtocol(Protocol):
    """Persistence contract for reporting queries."""

    def fetch_total_bonus_paid(self) -> Decimal: ...

    def fetch_employees_without_bonus(self) -> list[EmployeeWithoutBonusRow]: ...

    def fetch_bonus_percentages(self) -> list[BonusPercentageRow]: ...

    def fetch_departments_over_average(self) -> list[DepartmentOverAverageRow]: ...

    def fetch_bonus_ranking(self) -> list[BonusRankingRow]: ...

    def fetch_highest_salary(self) -> HighestSalaryRow | None: ...

    def fetch_highest_total_compensation(self) -> HighestTotalCompensationRow | None: ...


class EngineFactory(Protocol):
    """Callable that returns a SQLAlchemy Engine."""

    def __call__(self) -> Engine: ...
