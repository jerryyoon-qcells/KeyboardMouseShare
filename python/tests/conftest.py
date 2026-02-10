"""Test fixtures and configuration."""

import pytest


@pytest.fixture
def mock_config():
    """Fixture providing a mock configuration object."""
    from src.config import Config

    config = Config()
    return config


@pytest.fixture
def mock_logger():
    """Fixture providing a mock logger."""
    from src.logger import setup_logging
    import logging

    logger = setup_logging(log_level=logging.DEBUG)
    return logger


@pytest.fixture
def sample_device_data():
    """Fixture providing sample device data."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "mac_address": "A1:B2:C3:D4:E5:F6",
        "name": "Test Device",
        "os": "Windows",
        "role": "MASTER",
        "ip_address": "192.168.1.100",
        "port": 19999,
        "version": "1.0.0",
    }


@pytest.fixture
def sample_layout_data():
    """Fixture providing sample layout configuration."""
    return {
        "device_id": "550e8400-e29b-41d4-a716-446655440000",
        "x": 0,
        "y": 0,
        "width": 1920,
        "height": 1080,
        "dpi_scale": 1.0,
        "orientation": "LANDSCAPE",
    }
