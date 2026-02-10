"""Device entity representing a connected keyboard-mouse-share instance."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid


class DeviceRole(str, Enum):
    """Device role in the network."""
    MASTER = "MASTER"        # Sends input events
    CLIENT = "CLIENT"        # Receives input events
    UNASSIGNED = "UNASSIGNED"  # Not yet assigned a role


class DeviceOS(str, Enum):
    """Supported operating systems."""
    WINDOWS = "Windows"
    MACOS = "Darwin"


@dataclass
class Device:
    """
    Represents a keyboard-mouse-share device on the network.
    
    Attributes:
        id: Unique identifier (UUID v4)
        mac_address: Hardware address (format: AA:BB:CC:DD:EE:FF)
        name: Human-readable device name (max 50 chars)
        os: Operating system (Windows or Darwin/macOS)
        role: Device role in network (MASTER, CLIENT, UNASSIGNED)
        ip_address: IPv4 or IPv6 address (None until discovered on mDNS)
        port: Network port (default 19999)
        version: Application version (semantic: "1.0.0")
        is_registered: True if currently on mDNS
        created_at: Timestamp when device record created
        last_seen: Timestamp when last seen on mDNS
    
    Constraints:
        - id must be valid UUID v4
        - mac_address must be unique
        - name max 50 characters
        - port in range 1024–65535
        - role must be MASTER, CLIENT, or UNASSIGNED
        - os must be Windows or Darwin
    """
    
    # Required fields
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mac_address: str = ""  # Will be fetched from ARP/ifconfig
    name: str = ""
    os: DeviceOS = DeviceOS.WINDOWS
    role: DeviceRole = DeviceRole.UNASSIGNED
    
    # Network fields
    ip_address: Optional[str] = None  # "192.168.1.100" or None
    port: int = 19999
    version: str = "1.0.0"
    
    # Registration fields
    is_registered: bool = False  # On mDNS right now?
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Validate fields after dataclass initialization."""
        from ..utils.validators import (
            validate_uuid, validate_mac_address, validate_device_name,
            validate_port, validate_ip_address, validate_os_type
        )
        
        if not validate_uuid(self.id):
            raise ValueError(f"Invalid UUID: {self.id}")
        
        if self.mac_address and not validate_mac_address(self.mac_address):
            raise ValueError(f"Invalid MAC address: {self.mac_address}")
        
        if not validate_device_name(self.name):
            raise ValueError(f"Invalid device name: {self.name}")
        
        if not validate_port(self.port):
            raise ValueError(f"Invalid port: {self.port}")
        
        if self.ip_address and not validate_ip_address(self.ip_address):
            raise ValueError(f"Invalid IP address: {self.ip_address}")
        
        if not validate_os_type(str(self.os.value)):
            raise ValueError(f"Invalid OS: {self.os}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "mac_address": self.mac_address,
            "name": self.name,
            "os": self.os.value,
            "role": self.role.value,
            "ip_address": self.ip_address,
            "port": self.port,
            "version": self.version,
            "is_registered": self.is_registered,
            "created_at": self.created_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Device":
        """Create Device from dictionary."""
        return cls(
            id=data["id"],
            mac_address=data["mac_address"],
            name=data["name"],
            os=DeviceOS(data["os"]),
            role=DeviceRole(data["role"]),
            ip_address=data.get("ip_address"),
            port=data.get("port", 19999),
            version=data.get("version", "1.0.0"),
            is_registered=data.get("is_registered", False),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
        )
