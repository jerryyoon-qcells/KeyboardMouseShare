"""Connection entity representing a TLS connection between two devices."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid


class ConnectionStatus(str, Enum):
    """Connection lifecycle states."""
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    FAILED = "FAILED"


@dataclass
class Connection:
    """
    Represents a TLS connection between a master and client device.
    
    Attributes:
        id: Unique identifier for this connection pair
        master_device_id: UUID of master device
        client_device_id: UUID of client device
        status: Connection state (CONNECTING, CONNECTED, DISCONNECTED, FAILED)
        tls_certificate: PEM-encoded X.509 certificate (for peer validation)
        auth_token: Token for session resumption / reconnection
        input_event_counter: Number of input events sent (audit/monitoring)
        created_at: When connection established
        last_heartbeat: When last heartbeat received
    
    Constraints:
        - Both device IDs must be valid UUIDs
        - They must be different (master ≠ client)
        - status must be one of the enum values
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    master_device_id: str = ""
    client_device_id: str = ""
    
    status: ConnectionStatus = ConnectionStatus.CONNECTING
    
    tls_certificate: Optional[str] = None  # PEM format
    auth_token: Optional[str] = None
    input_event_counter: int = 0
    
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Validate connection setup."""
        from ..utils.validators import validate_uuid
        
        if not validate_uuid(self.master_device_id):
            raise ValueError(f"Invalid master device ID: {self.master_device_id}")
        
        if not validate_uuid(self.client_device_id):
            raise ValueError(f"Invalid client device ID: {self.client_device_id}")
        
        if self.master_device_id == self.client_device_id:
            raise ValueError("Master and client must be different devices")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "master_device_id": self.master_device_id,
            "client_device_id": self.client_device_id,
            "status": self.status.value,
            "tls_certificate": self.tls_certificate,
            "auth_token": self.auth_token,
            "input_event_counter": self.input_event_counter,
            "created_at": self.created_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Connection":
        """Create Connection from dictionary."""
        return cls(
            id=data["id"],
            master_device_id=data["master_device_id"],
            client_device_id=data["client_device_id"],
            status=ConnectionStatus(data["status"]),
            tls_certificate=data.get("tls_certificate"),
            auth_token=data.get("auth_token"),
            input_event_counter=data.get("input_event_counter", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_heartbeat=datetime.fromisoformat(data["last_heartbeat"]),
        )
