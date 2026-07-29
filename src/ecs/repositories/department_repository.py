"""Department aggregate persistence using SQLAlchemy Core."""

from __future__ import annotations

import logging
from collections.abc import Mapping

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.engine import Engine

from ecs.domain.department import Department
from ecs.repositories.base import (
    department_table,
    employee_table,
    map_department_row,
    translate_db_errors,
)

logger = logging.getLogger(__name__)

_DEPARTMENT_UPDATE_COLUMNS = {
    "department_name": department_table.c.DepartmentName,
    "location": department_table.c.Location,
}


class SqlAlchemyDepartmentRepository:
    """CRUD repository for Department rows."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_by_id(self, department_id: int) -> Department | None:
        """Return a department by primary key, or None if missing."""
        stmt = select(department_table).where(department_table.c.DepartmentID == department_id)
        with translate_db_errors(), self._engine.connect() as connection:
            row = connection.execute(stmt).mappings().first()
        if row is None:
            return None
        return map_department_row(row)

    def list_departments(self) -> tuple[list[Department], int]:
        """Return all departments ordered by ID, plus total count."""
        list_stmt = select(department_table).order_by(department_table.c.DepartmentID.asc())
        count_stmt = select(func.count()).select_from(department_table)
        with translate_db_errors(), self._engine.connect() as connection:
            rows = connection.execute(list_stmt).mappings().all()
            total = int(connection.execute(count_stmt).scalar_one())
        return [map_department_row(row) for row in rows], total

    def insert(self, *, department_name: str, location: str | None) -> Department:
        """Insert a new department and return the persisted row."""
        stmt = (
            insert(department_table)
            .values(DepartmentName=department_name, Location=location)
            .returning(department_table)
        )
        with translate_db_errors(), self._engine.begin() as connection:
            row = connection.execute(stmt).mappings().one()
        department = map_department_row(row)
        logger.info("Department created", extra={"department_id": department.department_id})
        return department

    def update(self, department_id: int, updates: Mapping[str, object]) -> Department | None:
        """Apply a partial update. Keys must be snake_case domain field names."""
        if not updates:
            return self.get_by_id(department_id)

        values: dict[object, object] = {}
        for field_name, value in updates.items():
            column = _DEPARTMENT_UPDATE_COLUMNS.get(field_name)
            if column is None:
                raise ValueError(f"Unsupported department update field: {field_name}")
            values[column] = value

        stmt = (
            update(department_table)
            .where(department_table.c.DepartmentID == department_id)
            .values(values)
            .returning(department_table)
        )
        with translate_db_errors(), self._engine.begin() as connection:
            row = connection.execute(stmt).mappings().first()
        if row is None:
            return None
        department = map_department_row(row)
        logger.info("Department updated", extra={"department_id": department.department_id})
        return department

    def delete(self, department_id: int) -> bool:
        """Delete a department. Returns True if a row was deleted."""
        stmt = delete(department_table).where(department_table.c.DepartmentID == department_id)
        with translate_db_errors(), self._engine.begin() as connection:
            result = connection.execute(stmt)
        deleted = result.rowcount > 0
        if deleted:
            logger.info("Department deleted", extra={"department_id": department_id})
        return deleted

    def count_employees(self, department_id: int) -> int:
        """Count employees currently assigned to a department."""
        stmt = (
            select(func.count())
            .select_from(employee_table)
            .where(employee_table.c.DepartmentID == department_id)
        )
        with translate_db_errors(), self._engine.connect() as connection:
            return int(connection.execute(stmt).scalar_one())

    def unassign_employees(self, department_id: int) -> int:
        """Set DepartmentID = NULL for all employees in a department."""
        stmt = (
            update(employee_table)
            .where(employee_table.c.DepartmentID == department_id)
            .values(DepartmentID=None)
        )
        with translate_db_errors(), self._engine.begin() as connection:
            result = connection.execute(stmt)
        count = int(result.rowcount)
        logger.info(
            "Employees unassigned from department",
            extra={"department_id": department_id, "unassigned_employees": count},
        )
        return count
