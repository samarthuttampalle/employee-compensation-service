"""Azure Functions runtime shim — the host requires function_app.py at the project root."""

from ecs.function_app import app  # noqa: F401
