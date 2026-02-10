"""Unit tests for configuration module."""

import json
import tempfile
from pathlib import Path

import pytest

from src.config import Config


class TestConfigInitialization:
    """Tests for Config initialization."""

    def test_default_initialization(self) -> None:
        """Test Config initialization with defaults."""
        config = Config()
        assert config.get("device_name") is not None
        assert config["device_role"] == "unassigned"
        assert config["port"] == 19999

    def test_custom_config_file(self) -> None:
        """Test Config initialization with custom file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "custom_config.json"
            config = Config(config_file=config_file)
            assert config.config_file == config_file

    def test_load_from_file(self) -> None:
        """Test loading configuration from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_data = {"device_name": "Test Device", "port": 20000}

            # Create config file
            with open(config_file, "w") as f:
                json.dump(config_data, f)

            # Load config
            config = Config(config_file=config_file)
            assert config["device_name"] == "Test Device"
            assert config["port"] == 20000


class TestConfigGetSet:
    """Tests for Config get/set operations."""

    def test_get_existing_key(self) -> None:
        """Test getting existing configuration key."""
        config = Config()
        assert config.get("port") == 19999

    def test_get_missing_key(self) -> None:
        """Test getting missing configuration key."""
        config = Config()
        assert config.get("nonexistent") is None
        assert config.get("nonexistent", "default") == "default"

    def test_set_value(self) -> None:
        """Test setting configuration value."""
        config = Config()
        config.set("device_name", "New Device")
        assert config.get("device_name") == "New Device"

    def test_dict_like_access(self) -> None:
        """Test dict-like access to configuration."""
        config = Config()
        assert config["port"] == 19999
        config["port"] = 20000
        assert config["port"] == 20000


class TestConfigSave:
    """Tests for Config save functionality."""

    def test_save_to_file(self) -> None:
        """Test saving configuration to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config = Config(config_file=config_file)

            config["device_name"] = "Saved Device"
            config.save()

            # Verify file was created
            assert config_file.exists()

            # Load and verify
            with open(config_file, "r") as f:
                data = json.load(f)
            assert data["device_name"] == "Saved Device"


class TestConfigToDict:
    """Tests for Config.to_dict()."""

    def test_to_dict_returns_copy(self) -> None:
        """Test that to_dict returns a copy."""
        config = Config()
        config_dict = config.to_dict()

        # Modify returned dict
        config_dict["port"] = 30000

        # Original should not be modified
        assert config["port"] == 19999


class TestConfigRepr:
    """Tests for Config string representation."""

    def test_repr_format(self) -> None:
        """Test Config __repr__ format."""
        config = Config()
        repr_str = repr(config)
        assert "Config" in repr_str
        assert "keys=" in repr_str
