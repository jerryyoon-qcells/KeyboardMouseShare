"""
Structured logging setup for Keyboard Mouse Share.

Configures JSON-formatted logging output for both console and file,
with rotation and audit trail capability.
"""

import json
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from src.config import Config


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra") and record.extra:  # type: ignore
            log_data.update(record.extra)  # type: ignore

        return json.dumps(log_data)


def setup_logging(
    log_level: int = logging.INFO,
    config: Optional[Config] = None,
) -> logging.Logger:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (default: INFO)
        config: Optional Config instance for directory paths

    Returns:
        Configured logger instance
    """
    if config is None:
        config = Config()

    logger = logging.getLogger("keyboard_mouse_share")
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    json_formatter = JSONFormatter()
    simple_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (simple format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # File handler (JSON format) with rotation
    log_file = Path(config.log_dir) / "app.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,  # Keep 5 backup files
        )
        file_handler.setLevel(logging.DEBUG)  # File always logs DEBUG
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not setup file logging: {e}")

    logger.info(f"Logging configured (level={logging.getLevelName(log_level)})")

    return logger
