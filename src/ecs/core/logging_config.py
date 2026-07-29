"""Logging bootstrap for local runs and Azure-hosted executions."""

from __future__ import annotations

import logging

from azure.monitor.opentelemetry import configure_azure_monitor

from ecs.core.config import get_settings


def configure_logging() -> None:
    """Configure standard logging and optional App Insights export."""
    settings = get_settings()
    log_level_name = settings.log_level.upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )
    else:
        root_logger.setLevel(log_level)

    if settings.applicationinsights_connection_string:
        configure_azure_monitor(
            connection_string=settings.applicationinsights_connection_string,
        )
