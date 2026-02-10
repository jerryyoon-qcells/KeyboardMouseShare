"""Unit tests for validators module."""

import pytest

from src.utils.validators import (
    validate_coordinate,
    validate_device_count,
    validate_device_name,
    validate_device_role,
    validate_dpi_scale,
    validate_ip_address,
    validate_mac_address,
    validate_os_type,
    validate_passphrase,
    validate_port,
    validate_resolution,
    validate_uuid,
)


class TestIPValidation:
    """Tests for IP address validation."""

    def test_valid_ipv4(self) -> None:
        """Test valid IPv4 addresses."""
        assert validate_ip_address("192.168.1.1") is True
        assert validate_ip_address("10.0.0.1") is True
        assert validate_ip_address("255.255.255.255") is True
        assert validate_ip_address("0.0.0.0") is True

    def test_invalid_ipv4(self) -> None:
        """Test invalid IPv4 addresses."""
        assert validate_ip_address("256.1.1.1") is False
        assert validate_ip_address("192.168.1") is False
        assert validate_ip_address("192.168.1.1.1") is False
        assert validate_ip_address("abc.def.ghi.jkl") is False


class TestPortValidation:
    """Tests for port number validation."""

    def test_valid_ports(self) -> None:
        """Test valid port numbers."""
        assert validate_port(1) is True
        assert validate_port(80) is True
        assert validate_port(443) is True
        assert validate_port(19999) is True
        assert validate_port(65535) is True

    def test_invalid_ports(self) -> None:
        """Test invalid port numbers."""
        assert validate_port(0) is False
        assert validate_port(-1) is False
        assert validate_port(65536) is False
        assert validate_port(100000) is False


class TestPassphraseValidation:
    """Tests for passphrase validation."""

    def test_valid_passphrase(self) -> None:
        """Test valid passphrases."""
        assert validate_passphrase("ABC123") is True
        assert validate_passphrase("abc!@#") is True
        assert validate_passphrase("123456") is True

    def test_invalid_passphrase_length(self) -> None:
        """Test passphrases with invalid length."""
        assert validate_passphrase("ABC12") is False  # Too short
        assert validate_passphrase("ABC1234") is False  # Too long
        assert validate_passphrase("") is False

    def test_invalid_passphrase_characters(self) -> None:
        """Test passphrases with invalid characters."""
        assert validate_passphrase("ABC éàü") is False  # Non-ASCII


class TestDeviceNameValidation:
    """Tests for device name validation."""

    def test_valid_device_names(self) -> None:
        """Test valid device names."""
        assert validate_device_name("My MacBook") is True
        assert validate_device_name("Windows-PC") is True
        assert validate_device_name("Test Device 123") is True
        assert validate_device_name("Jerry's Device") is True

    def test_invalid_device_names(self) -> None:
        """Test invalid device names."""
        assert validate_device_name("") is False
        assert validate_device_name("x" * 51) is False  # Too long
        assert validate_device_name("Device@#$%") is False  # Invalid characters


class TestMACAddressValidation:
    """Tests for MAC address validation."""

    def test_valid_mac_addresses(self) -> None:
        """Test valid MAC addresses."""
        assert validate_mac_address("A1:B2:C3:D4:E5:F6") is True
        assert validate_mac_address("00:00:00:00:00:00") is True
        assert validate_mac_address("FF:FF:FF:FF:FF:FF") is True
        assert validate_mac_address("A1-B2-C3-D4-E5-F6") is True  # Dashes

    def test_invalid_mac_addresses(self) -> None:
        """Test invalid MAC addresses."""
        assert validate_mac_address("A1:B2:C3:D4:E5") is False  # Too short
        assert validate_mac_address("A1:B2:C3:D4:E5:F6:F7") is False  # Too long
        assert validate_mac_address("ZZ:ZZ:ZZ:ZZ:ZZ:ZZ") is False  # Invalid hex


class TestUUIDValidation:
    """Tests for UUID validation."""

    def test_valid_uuids(self) -> None:
        """Test valid UUIDs."""
        assert validate_uuid("550e8400-e29b-41d4-a716-446655440000") is True
        assert validate_uuid("00000000-0000-0000-0000-000000000000") is True

    def test_invalid_uuids(self) -> None:
        """Test invalid UUIDs."""
        assert validate_uuid("550e8400-e29b-41d4-a716-44665544000") is False  # Too short
        assert validate_uuid("not-a-uuid") is False
        assert validate_uuid("") is False


class TestDeviceRoleValidation:
    """Tests for device role validation."""

    def test_valid_roles(self) -> None:
        """Test valid device roles."""
        assert validate_device_role("MASTER") is True
        assert validate_device_role("CLIENT") is True
        assert validate_device_role("UNASSIGNED") is True

    def test_invalid_roles(self) -> None:
        """Test invalid device roles."""
        assert validate_device_role("Master") is False  # Case-sensitive
        assert validate_device_role("UNKNOWN") is False
        assert validate_device_role("") is False


class TestOSTypeValidation:
    """Tests for OS type validation."""

    def test_valid_os_types(self) -> None:
        """Test valid OS types."""
        assert validate_os_type("Windows") is True
        assert validate_os_type("Darwin") is True

    def test_invalid_os_types(self) -> None:
        """Test invalid OS types."""
        assert validate_os_type("windows") is False  # Case-sensitive
        assert validate_os_type("macOS") is False
        assert validate_os_type("Linux") is False


class TestCoordinateValidation:
    """Tests for coordinate validation."""

    def test_valid_coordinates(self) -> None:
        """Test valid coordinates."""
        assert validate_coordinate(0, 0) is True
        assert validate_coordinate(1920, 1080) is True
        assert validate_coordinate(4096, 4096) is True

    def test_invalid_coordinates(self) -> None:
        """Test invalid coordinates."""
        assert validate_coordinate(-1, 0) is False
        assert validate_coordinate(0, -1) is False
        assert validate_coordinate(4097, 4096) is False


class TestResolutionValidation:
    """Tests for resolution validation."""

    def test_valid_resolutions(self) -> None:
        """Test valid screen resolutions."""
        assert validate_resolution(800, 600) is True
        assert validate_resolution(1920, 1080) is True
        assert validate_resolution(2560, 1440) is True
        assert validate_resolution(7680, 4320) is True  # 8K

    def test_invalid_resolutions(self) -> None:
        """Test invalid screen resolutions."""
        assert validate_resolution(479, 480) is False  # Too small (width)
        assert validate_resolution(480, 479) is False  # Too small (height)
        assert validate_resolution(7681, 4320) is False  # Out of bounds
        assert validate_resolution(0, 0) is False


class TestDPIScaleValidation:
    """Tests for DPI scale validation."""

    def test_valid_dpi_scales(self) -> None:
        """Test valid DPI scales."""
        assert validate_dpi_scale(0.5) is True
        assert validate_dpi_scale(1.0) is True
        assert validate_dpi_scale(1.5) is True
        assert validate_dpi_scale(2.0) is True
        assert validate_dpi_scale(4.0) is True

    def test_invalid_dpi_scales(self) -> None:
        """Test invalid DPI scales."""
        assert validate_dpi_scale(0.25) is False  # Too small
        assert validate_dpi_scale(5.0) is False  # Too large
        assert validate_dpi_scale(-1.0) is False
