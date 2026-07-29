"""Shared pytest configuration — load local.settings.json into the environment."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


def _load_local_settings() -> None:
    settings_path = Path(__file__).resolve().parents[1] / "local.settings.json"
    if not settings_path.exists():
        return
    raw = settings_path.read_text(encoding="utf-8-sig").strip()
    if not raw:
        return
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return
    values = payload.get("Values", {})
    for key, value in values.items():
        if key not in os.environ and isinstance(value, str) and value:
            os.environ[key] = value


_load_local_settings()


class FakeFunctionContext:
    """Minimal Azure Functions context for in-process API tests."""

    invocation_id = "test-invocation-id"


@pytest.fixture
def function_context() -> FakeFunctionContext:
    return FakeFunctionContext()
