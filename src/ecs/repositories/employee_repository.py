"""Employee aggregate persistence using SQLAlchemy Core."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.engine import Engine

from ecs.domain.employee import Employee
from ecs.repositories.base import (
    employee_table,
    map_employee_row,
    translate_db_errors,
)

logger = logging.getLogger(__name__)

_EMPLOYEE_UPDATE_COLUMNS = {
    "first_name": employee_table.c.FirstName,
    "last_name": employee_table.c.LastName,
    "department_id": employee_table.c.DepartmentID,
    "salary": employee_table.c.Salary,
    "bonus": employee_table.c.Bonus,
    "hire_date": employee_table.c.HireDate,
}


class SqlAlchemyEmployeeRepository:
    """CRUD repository for Employee rows."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_by_id(self, employee_id: int) -> Employee | None:
        """Return an employee by primary key, or None if missing."""
        stmt = select(employee_table).where(employee_table.c.EmployeeID == employee_id)
        with translate_db_errors(), self._engine.connect() as connection:
            row = connection.execute(stmt).mappings().first()
        if row is None:
            return None
        return map_employee_row(row)

    def list_employees(
        self,
        *,
        department_id: int | None,
        top: int,
        skip: int,
    ) -> tuple[list[Employee], int]:
        """List employees with optional department filter and pagination."""
        filters = []
        if department_id is not None:
            filters.append(employee_table.c.DepartmentID == department_id)

        list_stmt = (
            select(employee_table)
            .where(*filters)
            .order_by(employee_table.c.EmployeeID.asc())
            .offset(skip)
            .limit(top)
        )
        count_stmt = select(func.count()).select_from(employee_table).where(*filters)

        with translate_db_errors(), self._engine.connect() as connection:
            rows = connection.execute(list_stmt).mappings().all()
            total = int(connection.execute(count_stmt).scalar_one())

        employees = [map_employee_row(row) for row in rows]
        logger.debug(
            "Listed employees",
            extra={"department_id": department_id, "top": top, "skip": skip, "total": total},
        )
        return employees, total

    def insert(
        self,
        *,
        first_name: str,
        last_name: str,
        department_id: int | None,
        salary: Decimal,
        bonus: Decimal | None,
        hire_date: date | None,
    ) -> Employee:
        """Insert a new employee and return the persisted row."""
        stmt = (
            insert(employee_table)
            .values(
                FirstName=first_name,
                LastName=last_name,
                DepartmentID=department_id,
                Salary=salary,
                Bonus=bonus,
                HireDate=hire_date,
            )
            .returning(employee_table)
        )
        with translate_db_errors(), self._engine.begin() as connection:
            row = connection.execute(stmt).mappings().one()
        employee = map_employee_row(row)
        logger.info("Employee created", extra={"employee_id": employee.employee_id})
        return employee

    def update(self, employee_id: int, updates: Mapping[str, object]) -> Employee | None:
        """Apply a partial update. Keys must be snake_case domain field names."""
        if not updates:
            return self.get_by_id(employee_id)

        values: dict[object, object] = {}
        for field_name, value in updates.items():
            column = _EMPLOYEE_UPDATE_COLUMNS.get(field_name)
            if column is None:
                raise ValueError(f"Unsupported employee update field: {field_name}")
            values[column] = value

        stmt = (
            update(employee_table)
            .where(employee_table.c.EmployeeID == employee_id)
            .values(values)
            .returning(employee_table)
        )
        with translate_db_errors(), self._engine.begin() as connection:
            row = connection.execute(stmt).mappings().first()
        if row is None:
            return None
        employee = map_employee_row(row)
        logger.info("Employee updated", extra={"employee_id": employee.employee_id})
        return employee

    def delete(self, employee_id: int) -> bool:
        """Delete an employee. Returns True if a row was deleted."""
        stmt = delete(employee_table).where(employee_table.c.EmployeeID == employee_id)
        with translate_db_errors(), self._engine.begin() as connection:
            result = connection.execute(stmt)
        deleted = result.rowcount > 0
        if deleted:
            logger.info("Employee deleted", extra={"employee_id": employee_id})
        return deleted
