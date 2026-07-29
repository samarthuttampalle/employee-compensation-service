"""Department domain type — engine-agnostic, no framework dependencies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Department:
    """Persisted department aggregate root."""

    department_id: int
    department_name: str
    location: str | None
