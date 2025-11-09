"""
Logging configuration for Kajabi import system.

Provides structured logging with correlation IDs for tracing.
"""
import logging
import sys
from typing import Optional
import structlog


def setup_logging(log_level: str = "INFO", environment: str = "development"):
    """
    Configure structured logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Environment name (development, production)
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Choose processors based on environment
    if environment == "production":
        # Production: JSON output for log aggregation
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Human-readable output with colors
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str, trace_id: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a logger instance with optional trace ID.

    Args:
        name: Logger name (usually module name)
        trace_id: Optional correlation ID for request tracing

    Returns:
        Configured logger instance
    """
    logger = structlog.get_logger(name)
    if trace_id:
        logger = logger.bind(trace_id=trace_id)
    return logger
