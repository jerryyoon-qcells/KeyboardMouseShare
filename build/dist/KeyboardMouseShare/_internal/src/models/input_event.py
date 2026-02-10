"""InputEvent entity representing a single keyboard or mouse input action."""

from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


class InputEventType(str, Enum):
    """Types of input events."""
    KEY_PRESS = "KEY_PRESS"
    KEY_RELEASE = "KEY_RELEASE"
    MOUSE_MOVE = "MOUSE_MOVE"
    MOUSE_CLICK = "MOUSE_CLICK"
    MOUSE_RELEASE = "MOUSE_RELEASE"
    MOUSE_SCROLL = "MOUSE_SCROLL"


@dataclass
class InputEvent:
    """
    Represents a single keyboard or mouse input event.
    
    Attributes:
        id: Unique event identifier (UUID v4)
        event_type: Type of input (KEY_PRESS, MOUSE_MOVE, etc.)
        source_device_id: UUID of device that generated the event (master)
        target_device_id: UUID of device that receives the event (client)
        payload: Event-specific data (dict)
            For KEY_PRESS/KEY_RELEASE:
                { "keycode": "A", "modifiers": ["ctrl", "shift"] }
            For MOUSE_MOVE:
                { "x": 1024, "y": 768 }
            For MOUSE_CLICK/RELEASE:
                { "button": "left" }  # left, middle, right
            For MOUSE_SCROLL:
                { "scroll_delta": 5 }  # positive = up, negative = down
        timestamp: When event occurred (UTC)
        is_encrypted: True if payload was encrypted in transit
    
    Constraints:
        - Both device IDs must be valid UUIDs
        - payload must match event_type schema
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: InputEventType = InputEventType.MOUSE_MOVE
    
    source_device_id: str = ""
    target_device_id: str = ""
    
    payload: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_encrypted: bool = True
    
    def __post_init__(self):
        """Validate event structure."""
        from ..utils.validators import validate_uuid
        
        if not validate_uuid(self.source_device_id):
            raise ValueError(f"Invalid source device ID: {self.source_device_id}")
        
        if not validate_uuid(self.target_device_id):
            raise ValueError(f"Invalid target device ID: {self.target_device_id}")
        
        # Validate payload matches event type
        self._validate_payload()
    
    def _validate_payload(self):
        """Ensure payload structure matches event_type."""
        if self.event_type in (InputEventType.KEY_PRESS, InputEventType.KEY_RELEASE):
            if "keycode" not in self.payload:
                raise ValueError(f"KEY event missing keycode: {self.payload}")
        
        elif self.event_type == InputEventType.MOUSE_MOVE:
            if "x" not in self.payload or "y" not in self.payload:
                raise ValueError(f"MOUSE_MOVE missing x/y: {self.payload}")
        
        elif self.event_type in (InputEventType.MOUSE_CLICK, InputEventType.MOUSE_RELEASE):
            if "button" not in self.payload:
                raise ValueError(f"MOUSE_CLICK/RELEASE missing button: {self.payload}")
        
        elif self.event_type == InputEventType.MOUSE_SCROLL:
            if "scroll_delta" not in self.payload:
                raise ValueError(f"MOUSE_SCROLL missing scroll_delta: {self.payload}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "source_device_id": self.source_device_id,
            "target_device_id": self.target_device_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "is_encrypted": self.is_encrypted,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "InputEvent":
        """Create InputEvent from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            event_type=InputEventType(data["event_type"]),
            source_device_id=data["source_device_id"],
            target_device_id=data["target_device_id"],
            payload=data["payload"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            is_encrypted=data.get("is_encrypted", True),
        )
