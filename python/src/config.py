"""
Configuration management for Keyboard Mouse Share.

Handles loading and managing application configuration from JSON files,
environment variables, and defaults.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class Config:
    """Application configuration manager."""

    DEFAULT_CONFIG_DIR = Path.home() / ".keyboard-mouse-share"
    DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
    DEFAULT_LOG_DIR = DEFAULT_CONFIG_DIR / "logs"

    # Default configuration values
    DEFAULTS: Dict[str, Any] = {
        "device_name": f"Device-{Path.home().name}",
        "device_role": "unassigned",
        "port": 19999,
        "discovery_timeout": 60,
        "connection_timeout": 30,
        "passphrase_length": 6,
        "max_passphrase_attempts": 3,
        "passphrase_lockout_duration": 300,  # 5 minutes in seconds
        "log_level": "INFO",
        "audit_logging_enabled": True,
        "audit_log_retention_days": 7,
    }

    def __init__(self, config_file: Optional[Path] = None) -> None:
        """
        Initialize configuration manager.

        Args:
            config_file: Optional path to configuration file. If not provided,
                        uses DEFAULT_CONFIG_FILE.
        """
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self._config: Dict[str, Any] = self.DEFAULTS.copy()
        self.log_dir = self.DEFAULT_LOG_DIR

        # Create config directory if it doesn't exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Load configuration from file if it exists
        if self.config_file.exists():
            self._load_from_file()
        else:
            logger.info(f"No configuration file found at {self.config_file}")
            logger.info(f"Using default configuration")

    def _load_from_file(self) -> None:
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, "r") as f:
                file_config = json.load(f)
            self._config.update(file_config)
            logger.info(f"Configuration loaded from {self.config_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse configuration file: {e}")
            logger.warning("Using default configuration")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            logger.warning("Using default configuration")

    def save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self._config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value

    def __getitem__(self, key: str) -> Any:
        """Get configuration value using dict-like syntax."""
        return self._config[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set configuration value using dict-like syntax."""
        self._config[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()

    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"Config(file={self.config_file}, keys={len(self._config)})"
