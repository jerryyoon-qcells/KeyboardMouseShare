"""Unit tests for main module."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from src.main import main


class TestMainEntry:
    """Tests for main entry point."""

    def test_main_version_flag(self) -> None:
        """Test main with --version flag."""
        with pytest.raises(SystemExit) as exc_info:
            with patch.object(sys, "argv", ["prog", "--version"]):
                main()
        # SystemExit(0) for --version is OK
        assert exc_info.value.code == 0

    def test_main_with_role_argument(self) -> None:
        """Test main with --role argument."""
        with patch.object(sys, "argv", ["prog", "--role", "master"]):
            with patch("src.main.Config"):
                with patch("src.main.setup_logging"):
                    result = main()
        assert result == 0

    def test_main_with_device_name(self) -> None:
        """Test main with --device-name argument."""
        with patch.object(sys, "argv", ["prog", "--device-name", "My Device"]):
            with patch("src.main.Config"):
                with patch("src.main.setup_logging"):
                    result = main()
        assert result == 0

    def test_main_with_discover_flag(self) -> None:
        """Test main with --discover flag."""
        with patch.object(sys, "argv", ["prog", "--discover"]):
            with patch("src.main.Config"):
                with patch("src.main.setup_logging"):
                    result = main()
        assert result == 0

    def test_main_with_debug_flag(self) -> None:
        """Test main with --debug flag."""
        with patch.object(sys, "argv", ["prog", "--debug"]):
            with patch("src.main.Config"):
                with patch("src.main.setup_logging"):
                    result = main()
        assert result == 0

    def test_main_keyboard_interrupt(self) -> None:
        """Test main handles KeyboardInterrupt gracefully."""
        with patch.object(sys, "argv", ["prog"]):
            with patch("src.main.Config", side_effect=KeyboardInterrupt):
                with patch("src.main.setup_logging"):
                    result = main()
        assert result == 0

    def test_main_exception_handling(self) -> None:
        """Test main handles exceptions gracefully."""
        with patch.object(sys, "argv", ["prog"]):
            with patch("src.main.Config", side_effect=RuntimeError("Test error")):
                with patch("src.main.setup_logging"):
                    result = main()
        assert result == 1
