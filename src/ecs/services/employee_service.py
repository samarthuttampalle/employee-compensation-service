"""Employee business logic — CRUD orchestration and default-bonus policy."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ecs.core.exceptions import NotFoundError, ValidationError
from ecs.domain.employee import Employee
from ecs.repositories.base import DepartmentRepositoryProtocol, EmployeeRepositoryProtocol
from ecs.schemas.employee_schemas import CreateEmployeeRequest, UpdateEmployeeRequest


@dataclass(frozen=True, slots=True)
class EmployeeReadResult:
    """Employee read result with optional read-time default bonus metadata."""

    employee: Employee
    effective_bonus: Decimal | None = None
    bonus_is_defaulted: bool = False


@dataclass(frozen=True, slots=True)
class EmployeeListResult:
    """Paginated employee list returned by the service layer."""

    items: list[Employee]
    total: int
    top: int
    skip: int


class EmployeeService:
    """Business rules for employee CRUD operations."""

    def __init__(
        self,
        employee_repository: EmployeeRepositoryProtocol,
        department_repository: DepartmentRepositoryProtocol,
        *,
        default_bonus_rate: Decimal = Decimal("0.05"),
        max_page_size: int = 200,
    ) -> None:
        self._employee_repository = employee_repository
        self._department_repository = department_repository
        self._default_bonus_rate = default_bonus_rate
        self._max_page_size = max_page_size

    def create_employee(self, request: CreateEmployeeRequest) -> Employee:
        """Create a new employee after validating department references."""
        if request.department_id is not None:
            self._ensure_department_exists(request.department_id)

        return self._employee_repository.insert(
            first_name=request.first_name,
            last_name=request.last_name,
            department_id=request.department_id,
            salary=request.salary,
            bonus=request.bonus,
            hire_date=request.hire_date,
        )

    def get_employee(
        self,
        employee_id: int,
        *,
        apply_default_bonus: bool = False,
    ) -> EmployeeReadResult:
        """Return an employee, optionally computing a read-time default bonus."""
        employee = self._employee_repository.get_by_id(employee_id)
        if employee is None:
            raise NotFoundError.for_resource("Employee", employee_id)

        effective_bonus: Decimal | None = None
        bonus_is_defaulted = False
        if apply_default_bonus and employee.bonus is None:
            effective_bonus = employee.salary * self._default_bonus_rate
            bonus_is_defaulted = True

        return EmployeeReadResult(
            employee=employee,
            effective_bonus=effective_bonus,
            bonus_is_defaulted=bonus_is_defaulted,
        )

    def list_employees(
        self,
        *,
        department_id: int | None = None,
        top: int = 50,
        skip: int = 0,
    ) -> EmployeeListResult:
        """List employees with server-side pagination clamping."""
        if top < 0 or skip < 0:
            raise ValidationError("top and skip must be non-negative.")

        clamped_top = min(top, self._max_page_size)
        items, total = self._employee_repository.list_employees(
            department_id=department_id,
            top=clamped_top,
            skip=skip,
        )
        return EmployeeListResult(items=items, total=total, top=clamped_top, skip=skip)

    def update_employee(self, employee_id: int, request: UpdateEmployeeRequest) -> Employee:
        """Apply a partial employee update."""
        if not request.has_updates():
            raise ValidationError("At least one field must be provided for update.")

        if not self._employee_repository.get_by_id(employee_id):
            raise NotFoundError.for_resource("Employee", employee_id)

        updates = self._build_update_payload(request)
        if request.is_set("department_id") and request.department_id is not None:
            self._ensure_department_exists(request.department_id)

        updated = self._employee_repository.update(employee_id, updates)
        if updated is None:
            raise NotFoundError.for_resource("Employee", employee_id)
        return updated

    def delete_employee(self, employee_id: int) -> None:
        """Delete an employee by ID."""
        deleted = self._employee_repository.delete(employee_id)
        if not deleted:
            raise NotFoundError.for_resource("Employee", employee_id)

    def _ensure_department_exists(self, department_id: int) -> None:
        department = self._department_repository.get_by_id(department_id)
        if department is None:
            raise NotFoundError.for_resource("Department", department_id)

    @staticmethod
    def _build_update_payload(request: UpdateEmployeeRequest) -> dict[str, object]:
        updates: dict[str, object] = {}
        if request.is_set("first_name"):
            updates["first_name"] = request.first_name
        if request.is_set("last_name"):
            updates["last_name"] = request.last_name
        if request.is_set("department_id"):
            updates["department_id"] = request.department_id
        if request.is_set("salary"):
            updates["salary"] = request.salary
        if request.is_set("bonus"):
            updates["bonus"] = request.bonus
        if request.is_set("hire_date"):
            updates["hire_date"] = request.hire_date
        return updates
