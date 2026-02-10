"""Tests for InputEvent entity."""

import pytest
from src.models.input_event import InputEvent, InputEventType
import uuid


class TestInputEventCreation:
    """Test InputEvent entity creation and validation."""
    
    def test_create_key_press_event(self):
        """Test creating a key press event."""
        source_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        
        event = InputEvent(
            event_type=InputEventType.KEY_PRESS,
            source_device_id=source_id,
            target_device_id=target_id,
            payload={"keycode": "A"}
        )
        
        assert event.event_type == InputEventType.KEY_PRESS
        assert event.payload["keycode"] == "A"
        assert event.is_encrypted is True
    
    def test_create_mouse_move_event(self):
        """Test creating a mouse move event."""
        source_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        
        event = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=source_id,
            target_device_id=target_id,
            payload={"x": 1024, "y": 768}
        )
        
        assert event.event_type == InputEventType.MOUSE_MOVE
        assert event.payload["x"] == 1024
        assert event.payload["y"] == 768
    
    def test_create_mouse_click_event(self):
        """Test creating a mouse click event."""
        source_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        
        event = InputEvent(
            event_type=InputEventType.MOUSE_CLICK,
            source_device_id=source_id,
            target_device_id=target_id,
            payload={"button": "left"}
        )
        
        assert event.payload["button"] == "left"
    
    def test_create_mouse_scroll_event(self):
        """Test creating a mouse scroll event."""
        source_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        
        event = InputEvent(
            event_type=InputEventType.MOUSE_SCROLL,
            source_device_id=source_id,
            target_device_id=target_id,
            payload={"scroll_delta": 5}
        )
        
        assert event.payload["scroll_delta"] == 5
    
    def test_event_auto_generates_id(self):
        """Test that event generates unique ID."""
        source_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        
        event1 = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=source_id,
            target_device_id=target_id,
            payload={"x": 0, "y": 0}
        )
        event2 = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=source_id,
            target_device_id=target_id,
            payload={"x": 0, "y": 0}
        )
        
        assert event1.id != event2.id
    
    def test_event_creates_timestamp(self):
        """Test that event gets UTC timestamp."""
        source_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        
        event = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=source_id,
            target_device_id=target_id,
            payload={"x": 0, "y": 0}
        )
        
        assert event.timestamp is not None


class TestInputEventValidation:
    """Test InputEvent payload validation."""
    
    def test_key_press_missing_keycode_raises(self):
        """Test that KEY_PRESS without keycode raises ValueError."""
        source_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="keycode"):
            InputEvent(
                event_type=InputEventType.KEY_PRESS,
                source_device_id=source_id,
                target_device_id=target_id,
                payload={}  # Missing keycode
            )
    
    def test_mouse_move_missing_coordinates_raises(self):
        """Test that MOUSE_MOVE without x/y raises ValueError."""
        source_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="x/y"):
            InputEvent(
                event_type=InputEventType.MOUSE_MOVE,
                source_device_id=source_id,
                target_device_id=target_id,
                payload={"x": 100}  # Missing y
            )
    
    def test_mouse_click_missing_button_raises(self):
        """Test that MOUSE_CLICK without button raises ValueError."""
        source_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="button"):
            InputEvent(
                event_type=InputEventType.MOUSE_CLICK,
                source_device_id=source_id,
                target_device_id=target_id,
                payload={}  # Missing button
            )
    
    def test_invalid_source_device_id_raises(self):
        """Test that invalid source device ID raises ValueError."""
        target_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="Invalid source"):
            InputEvent(
                event_type=InputEventType.MOUSE_MOVE,
                source_device_id="invalid",
                target_device_id=target_id,
                payload={"x": 0, "y": 0}
            )
    
    def test_invalid_target_device_id_raises(self):
        """Test that invalid target device ID raises ValueError."""
        source_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="Invalid target"):
            InputEvent(
                event_type=InputEventType.MOUSE_MOVE,
                source_device_id=source_id,
                target_device_id="invalid",
                payload={"x": 0, "y": 0}
            )


class TestInputEventToDict:
    """Test InputEvent serialization."""
    
    def test_to_dict_includes_all_fields(self):
        """Test that to_dict includes all fields."""
        source_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        
        event = InputEvent(
            event_type=InputEventType.KEY_PRESS,
            source_device_id=source_id,
            target_device_id=target_id,
            payload={"keycode": "Return"},
            is_encrypted=True
        )
        d = event.to_dict()
        
        assert d["event_type"] == "KEY_PRESS"
        assert d["source_device_id"] == source_id
        assert d["target_device_id"] == target_id
        assert d["payload"]["keycode"] == "Return"
        assert d["is_encrypted"] is True


class TestInputEventFromDict:
    """Test InputEvent deserialization."""
    
    def test_from_dict_round_trip(self):
        """Test that to_dict -> from_dict preserves data."""
        source_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        
        event1 = InputEvent(
            event_type=InputEventType.MOUSE_SCROLL,
            source_device_id=source_id,
            target_device_id=target_id,
            payload={"scroll_delta": -3}
        )
        d = event1.to_dict()
        event2 = InputEvent.from_dict(d)
        
        assert event2.event_type == event1.event_type
        assert event2.source_device_id == event1.source_device_id
        assert event2.target_device_id == event1.target_device_id
        assert event2.payload == event1.payload


class TestAllEventTypes:
    """Test all event types."""
    
    def test_all_event_types_valid(self):
        """Test that all defined event types work."""
        source_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        
        payloads = {
            InputEventType.KEY_PRESS: {"keycode": "A"},
            InputEventType.KEY_RELEASE: {"keycode": "A"},
            InputEventType.MOUSE_MOVE: {"x": 0, "y": 0},
            InputEventType.MOUSE_CLICK: {"button": "left"},
            InputEventType.MOUSE_RELEASE: {"button": "left"},
            InputEventType.MOUSE_SCROLL: {"scroll_delta": 5},
        }
        
        for event_type, payload in payloads.items():
            event = InputEvent(
                event_type=event_type,
                source_device_id=source_id,
                target_device_id=target_id,
                payload=payload
            )
            assert event.event_type == event_type
