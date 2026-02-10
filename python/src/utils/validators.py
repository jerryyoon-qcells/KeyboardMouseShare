"""
Input validation functions for Keyboard Mouse Share.

Validates configuration values, device attributes, and user inputs
before processing.
"""

import re
from typing import Optional

from src.utils.constants import (
    DEFAULT_PASSPHRASE_LENGTH,
    DEFAULT_PORT,
    MAX_DEVICES,
    MIN_DEVICES,
)


def validate_ip_address(ip: str) -> bool:
    """
    Validate IPv4 or IPv6 address format.

    Args:
        ip: IP address string

    Returns:
        True if valid, False otherwise
    """
    # IPv4 pattern
    ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if re.match(ipv4_pattern, ip):
        parts = ip.split(".")
        return all(0 <= int(part) <= 255 for part in parts)

    # IPv6 pattern (simplified)
    ipv6_pattern = r"^([\da-fA-F]{0,4}:){2,7}[\da-fA-F]{0,4}$"
    return bool(re.match(ipv6_pattern, ip))


def validate_port(port: int) -> bool:
    """
    Validate port number (1-65535).

    Args:
        port: Port number

    Returns:
        True if valid, False otherwise
    """
    return 1 <= port <= 65535


def validate_passphrase(passphrase: str, expected_length: int = DEFAULT_PASSPHRASE_LENGTH) -> bool:
    """
    Validate passphrase format.

    Args:
        passphrase: Passphrase string
        expected_length: Expected length (default: 6)

    Returns:
        True if valid, False otherwise
    """
    if not passphrase:
        return False

    if len(passphrase) != expected_length:
        return False

    # Allow alphanumeric and common symbols
    pattern = r"^[a-zA-Z0-9!@#$%^&*()_+=\-\[\]{}|;:',.<>?/`~]+$"
    return bool(re.match(pattern, passphrase))


def validate_device_name(name: str, max_length: int = 50) -> bool:
    """
    Validate device name format.

    Args:
        name: Device name string
        max_length: Maximum length (default: 50)

    Returns:
        True if valid, False otherwise
    """
    if not name or not isinstance(name, str):
        return False

    if len(name) > max_length:
        return False

    # Allow alphanumeric, spaces, hyphens, apostrophes
    pattern = r"^[a-zA-Z0-9\s\-']+$"
    return bool(re.match(pattern, name))


def validate_mac_address(mac: str) -> bool:
    """
    Validate MAC address format.

    Args:
        mac: MAC address string (format: XX:XX:XX:XX:XX:XX)

    Returns:
        True if valid, False otherwise
    """
    pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
    return bool(re.match(pattern, mac))


def validate_uuid(uuid_str: str) -> bool:
    """
    Validate UUID format (v4).

    Args:
        uuid_str: UUID string

    Returns:
        True if valid, False otherwise
    """
    pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    return bool(re.match(pattern, uuid_str, re.IGNORECASE))


def validate_device_role(role: str) -> bool:
    """
    Validate device role.

    Args:
        role: Device role string

    Returns:
        True if valid, False otherwise
    """
    return role in ["MASTER", "CLIENT", "UNASSIGNED"]


def validate_os_type(os_type: str) -> bool:
    """
    Validate operating system type.

    Args:
        os_type: OS type string

    Returns:
        True if valid, False otherwise
    """
    return os_type in ["Windows", "Darwin"]  # macOS is identified as Darwin


def validate_device_count(count: int) -> bool:
    """
    Validate device count is within supported range.

    Args:
        count: Number of devices

    Returns:
        True if valid, False otherwise
    """
    return MIN_DEVICES <= count <= MAX_DEVICES


def validate_coordinate(x: int, y: int, max_value: int = 4096) -> bool:
    """
    Validate screen coordinate values.

    Args:
        x: X coordinate
        y: Y coordinate
        max_value: Maximum allowed coordinate value

    Returns:
        True if valid, False otherwise
    """
    return 0 <= x <= max_value and 0 <= y <= max_value


def validate_resolution(width: int, height: int) -> bool:
    """
    Validate screen resolution.

    Args:
        width: Screen width in pixels
        height: Screen height in pixels

    Returns:
        True if valid, False otherwise
    """
    min_res = 480  # SVGA minimum (VGA height)
    max_res = 7680  # 8K resolution

    return (min_res <= width <= max_res) and (min_res <= height <= max_res)


def validate_dpi_scale(scale: float) -> bool:
    """
    Validate DPI scale factor.

    Args:
        scale: DPI scale factor (e.g., 1.0, 1.5, 2.0)

    Returns:
        True if valid, False otherwise
    """
    return 0.5 <= scale <= 4.0
