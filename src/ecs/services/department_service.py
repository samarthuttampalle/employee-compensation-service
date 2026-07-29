"""Department business logic — CRUD orchestration and delete-guard rules."""

from __future__ import annotations

from dataclasses import dataclass

from ecs.core.exceptions import ConflictError, NotFoundError, ValidationError
from ecs.domain.department import Department
from ecs.repositories.base import DepartmentRepositoryProtocol
from ecs.schemas.department_schemas import CreateDepartmentRequest, UpdateDepartmentRequest


@dataclass(frozen=True, slots=True)
class DepartmentListResult:
    """Department list returned by the service layer."""

    items: list[Department]
    total: int


@dataclass(frozen=True, slots=True)
class DepartmentDeleteResult:
    """Result of a department delete operation."""

    department_id: int
    unassigned_employees: int


class DepartmentService:
    """Business rules for department CRUD operations."""

    def __init__(self, department_repository: DepartmentRepositoryProtocol) -> None:
        self._department_repository = department_repository

    def create_department(self, request: CreateDepartmentRequest) -> Department:
        """Create a new department."""
        return self._department_repository.insert(
            department_name=request.department_name,
            location=request.location,
        )

    def get_department(self, department_id: int) -> Department:
        """Return a department by ID."""
        department = self._department_repository.get_by_id(department_id)
        if department is None:
            raise NotFoundError.for_resource("Department", department_id)
        return department

    def list_departments(self) -> DepartmentListResult:
        """Return all departments."""
        items, total = self._department_repository.list_departments()
        return DepartmentListResult(items=items, total=total)

    def update_department(self, department_id: int, request: UpdateDepartmentRequest) -> Department:
        """Apply a partial department update."""
        if not request.has_updates():
            raise ValidationError("At least one field must be provided for update.")

        if not self._department_repository.get_by_id(department_id):
            raise NotFoundError.for_resource("Department", department_id)

        updates = self._build_update_payload(request)
        updated = self._department_repository.update(department_id, updates)
        if updated is None:
            raise NotFoundError.for_resource("Department", department_id)
        return updated

    def delete_department(
        self,
        department_id: int,
        *,
        force: bool = False,
    ) -> DepartmentDeleteResult:
        """Delete a department, optionally unassigning employees first."""
        department = self._department_repository.get_by_id(department_id)
        if department is None:
            raise NotFoundError.for_resource("Department", department_id)

        employee_count = self._department_repository.count_employees(department_id)
        if employee_count > 0 and not force:
            raise ConflictError(
                "Department has assigned employees. Use force=true to delete and unassign them.",
                code="DEPARTMENT_HAS_EMPLOYEES",
            )

        unassigned = 0
        if employee_count > 0 and force:
            unassigned = self._department_repository.unassign_employees(department_id)

        deleted = self._department_repository.delete(department_id)
        if not deleted:
            raise NotFoundError.for_resource("Department", department_id)

        return DepartmentDeleteResult(
            department_id=department_id,
            unassigned_employees=unassigned,
        )

    @staticmethod
    def _build_update_payload(request: UpdateDepartmentRequest) -> dict[str, object]:
        updates: dict[str, object] = {}
        if request.is_set("department_name"):
            updates["department_name"] = request.department_name
        if request.is_set("location"):
            updates["location"] = request.location
        return updates
