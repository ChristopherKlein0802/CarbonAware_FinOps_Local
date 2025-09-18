"""
Structured Logging Configuration for Carbon-Aware FinOps Dashboard
Centralized logging setup with performance metrics and structured output

This module provides a standardized logging configuration across all
dashboard components with academic-grade transparency and debugging capabilities.
"""

import logging
import logging.config
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging output

    Provides consistent, machine-readable log format with
    academic transparency and debugging information.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add custom fields if present
        if hasattr(record, 'performance_metrics'):
            log_entry["performance"] = record.performance_metrics

        if hasattr(record, 'api_operation'):
            log_entry["api_operation"] = record.api_operation

        if hasattr(record, 'carbon_data'):
            log_entry["carbon_data"] = record.carbon_data

        if hasattr(record, 'cost_data'):
            log_entry["cost_data"] = record.cost_data

        return json.dumps(log_entry, ensure_ascii=False)


class PerformanceFilter(logging.Filter):
    """Filter to add performance metrics to log records"""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add performance context to all log records"""
        # Add dashboard context
        record.dashboard_version = "1.0.0"
        record.academic_mode = True

        return True


def setup_logging(
    log_level: str = "INFO",
    enable_structured: bool = True,
    log_file: str = None
) -> None:
    """
    Configure structured logging for the entire application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_structured: Use JSON structured logging format
        log_file: Optional log file path for persistent logging
    """

    # Clear any existing handlers
    logging.getLogger().handlers.clear()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)

    if enable_structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        # Simple format for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)

    console_handler.addFilter(PerformanceFilter())
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(StructuredFormatter())
        file_handler.addFilter(PerformanceFilter())
        root_logger.addHandler(file_handler)

    # Set specific logger levels for external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def get_performance_logger(module_name: str) -> logging.Logger:
    """
    Get a logger configured for performance monitoring

    Args:
        module_name: Name of the module requesting the logger

    Returns:
        Configured logger with performance tracking capabilities
    """
    logger = logging.getLogger(f"carbon_finops.{module_name}")
    return logger


def log_performance_metric(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    success: bool = True,
    **kwargs
) -> None:
    """
    Log performance metrics in structured format

    Args:
        logger: Logger instance to use
        operation: Name of the operation being measured
        duration_ms: Duration in milliseconds
        success: Whether the operation succeeded
        **kwargs: Additional context data
    """

    performance_data = {
        "operation": operation,
        "duration_ms": round(duration_ms, 2),
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Add any additional context
    performance_data.update(kwargs)

    # Create log record with performance data
    if success:
        logger.info(
            f"✅ {operation} completed in {duration_ms:.2f}ms",
            extra={"performance_metrics": performance_data}
        )
    else:
        logger.warning(
            f"⚠️ {operation} failed after {duration_ms:.2f}ms",
            extra={"performance_metrics": performance_data}
        )


def log_api_operation(
    logger: logging.Logger,
    api_name: str,
    operation: str,
    response_time_ms: float,
    status_code: int = None,
    success: bool = True,
    **kwargs
) -> None:
    """
    Log API operations with structured data

    Args:
        logger: Logger instance to use
        api_name: Name of the API (e.g., "ElectricityMaps", "Boavizta")
        operation: Operation being performed
        response_time_ms: API response time in milliseconds
        status_code: HTTP status code if applicable
        success: Whether the operation succeeded
        **kwargs: Additional API context
    """

    api_data = {
        "api_name": api_name,
        "operation": operation,
        "response_time_ms": round(response_time_ms, 2),
        "success": success,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    if status_code:
        api_data["status_code"] = status_code

    # Add any additional context
    api_data.update(kwargs)

    if success:
        logger.info(
            f"🌐 {api_name} {operation} succeeded ({response_time_ms:.2f}ms)",
            extra={"api_operation": api_data}
        )
    else:
        logger.error(
            f"❌ {api_name} {operation} failed ({response_time_ms:.2f}ms)",
            extra={"api_operation": api_data}
        )


def log_carbon_data(
    logger: logging.Logger,
    region: str,
    carbon_intensity: float,
    source: str,
    confidence: str = "medium"
) -> None:
    """
    Log carbon intensity data with academic transparency

    Args:
        logger: Logger instance to use
        region: AWS region or ElectricityMaps zone
        carbon_intensity: Carbon intensity in g CO2/kWh
        source: Data source (e.g., "ElectricityMaps", "cache", "self_collected")
        confidence: Data confidence level
    """

    carbon_data = {
        "region": region,
        "carbon_intensity_g_co2_kwh": carbon_intensity,
        "source": source,
        "confidence": confidence,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    logger.info(
        f"🌱 Carbon data: {carbon_intensity:.1f}g CO₂/kWh ({region}, {source})",
        extra={"carbon_data": carbon_data}
    )


# Default configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "()": StructuredFormatter,
        },
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "structured",
            "stream": "ext://sys.stdout"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    },
    "loggers": {
        "carbon_finops": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        }
    }
}
