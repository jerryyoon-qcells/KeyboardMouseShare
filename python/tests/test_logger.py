"""Unit tests for logger module."""

import json
import logging
import tempfile
from pathlib import Path

import pytest

from src.config import Config
from src.logger import JSONFormatter, setup_logging


class TestJSONFormatter:
    """Tests for JSONFormatter."""

    def test_format_creates_json(self) -> None:
        """Test that formatter creates valid JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        # Should be valid JSON
        data = json.loads(formatted)
        assert isinstance(data, dict)
        assert "message" in data or "getMessage" in str(data)


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_returns_logger(self) -> None:
        """Test that setup_logging returns a logger."""
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "keyboard_mouse_share"

    def test_setup_logging_with_custom_level(self) -> None:
        """Test setup_logging with custom log level."""
        logger = setup_logging(log_level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_setup_logging_has_console_handler(self) -> None:
        """Test that logger has console handler."""
        logger = setup_logging()
        handlers = logger.handlers
        has_stream_handler = any(
            isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
            for h in handlers
        )
        assert has_stream_handler

    def test_setup_logging_multiple_calls_same_logger(self) -> None:
        """Test that multiple calls return the same logger."""
        logger1 = setup_logging()
        logger2 = setup_logging()
        assert logger1 is logger2
