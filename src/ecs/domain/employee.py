"""Employee domain type — engine-agnostic, no framework dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Employee:
    """Persisted employee aggregate root."""

    employee_id: int
    first_name: str
    last_name: str
    department_id: int | None
    salary: Decimal
    bonus: Decimal | None
    hire_date: date | None
