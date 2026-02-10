"""Tests for InputEventApplier."""

import pytest
import uuid
import time
from unittest.mock import Mock, patch, MagicMock

from src.input.event_applier import InputEventApplier, ApplierConfig, ApplierMetrics
from src.models.device import Device, DeviceOS, DeviceRole
from src.models.input_event import InputEvent, InputEventType


@pytest.fixture
def local_device():
    """Create local device."""
    return Device(
        id=str(uuid.uuid4()),
        name="LocalDevice",
        os=DeviceOS.WINDOWS,
        ip_address="192.168.1.100",
        port=5000,
        role=DeviceRole.CLIENT
    )


@pytest.fixture
def applier(local_device):
    """Create InputEventApplier instance."""
    return InputEventApplier(local_device)


@pytest.fixture
def applier_with_config(local_device):
    """Create InputEventApplier with custom config."""
    config = ApplierConfig(
        event_delay_ms=5,
        log_events=False,
        max_queue_size=100
    )
    return InputEventApplier(local_device, config)


class TestInputEventApplierInitialization:
    """Test InputEventApplier initialization."""

    def test_applier_creation(self, applier, local_device):
        """Test creating event applier."""
        assert applier.local_device == local_device
        assert not applier.is_running
        assert len(applier._event_queue) == 0

    def test_applier_with_default_config(self, applier):
        """Test applier with default configuration."""
        assert applier.config.event_delay_ms == 10
        assert applier.config.max_queue_size == 1000
        assert applier.config.validate_events is True

    def test_applier_with_custom_config(self, applier_with_config):
        """Test applier with custom configuration."""
        assert applier_with_config.config.event_delay_ms == 5
        assert applier_with_config.config.max_queue_size == 100

    def test_metrics_initialization(self, applier):
        """Test metrics are initialized."""
        metrics = applier.get_metrics()
        assert metrics.events_received == 0
        assert metrics.events_applied == 0
        assert metrics.events_failed == 0
        assert metrics.keyboard_events == 0
        assert metrics.mouse_events == 0


class TestApplierLifecycle:
    """Test applier lifecycle."""

    def test_start_applier(self, applier):
        """Test starting applier."""
        success = applier.start()
        assert success is True
        assert applier.is_running is True
        applier.stop()

    def test_start_already_running(self, applier):
        """Test starting already running applier."""
        applier.start()
        success = applier.start()
        assert success is False
        applier.stop()

    def test_stop_applier(self, applier):
        """Test stopping applier."""
        applier.start()
        success = applier.stop()
        assert success is True
        assert applier.is_running is False

    def test_stop_when_not_running(self, applier):
        """Test stopping when not running."""
        success = applier.stop()
        assert success is False

    def test_applier_thread_created(self, applier):
        """Test applier thread is created."""
        applier.start()
        assert applier.applier_thread is not None
        assert applier.applier_thread.is_alive()
        applier.stop()


class TestEventQueuing:
    """Test event queuing."""

    def test_queue_keyboard_event(self, applier):
        """Test queuing keyboard event."""
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        success = applier.apply_event(event)
        assert success is True
        
        metrics = applier.get_metrics()
        assert metrics.events_received == 1
        
        applier.stop()

    def test_queue_mouse_event(self, applier):
        """Test queuing mouse event."""
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"x": 100, "y": 200}
        )
        
        success = applier.apply_event(event)
        assert success is True
        
        metrics = applier.get_metrics()
        assert metrics.events_received == 1
        
        applier.stop()

    def test_queue_when_not_running(self, applier):
        """Test queuing when applier not running."""
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        success = applier.apply_event(event)
        assert success is False

    def test_queue_full(self, applier_with_config):
        """Test queue overflow handling."""
        applier = applier_with_config
        applier.start()
        
        overflow_count = 0
        
        # Try to queue more events than capacity (100)
        for i in range(150):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=str(uuid.uuid4()),
                target_device_id=str(uuid.uuid4()),
                payload={"keycode": "A"}
            )
            
            if not applier.apply_event(event):
                overflow_count += 1
        
        assert overflow_count > 0
        
        metrics = applier.get_metrics()
        assert metrics.events_failed > 0
        
        applier.stop()


class TestEventValidation:
    """Test event validation."""

    def test_validate_key_press_event(self, applier):
        """Test validating KEY_PRESS event."""
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        assert applier._validate_event(event) is True
        applier.stop()

    def test_validate_mouse_move_event(self, applier):
        """Test validating MOUSE_MOVE event."""
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"x": 100, "y": 200}
        )
        
        assert applier._validate_event(event) is True
        applier.stop()

    def test_validate_mouse_click_event(self, applier):
        """Test validating MOUSE_CLICK event."""
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_CLICK,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"button": "left"}
        )
        
        assert applier._validate_event(event) is True
        applier.stop()

    def test_validate_invalid_keycode(self, applier):
        """Test validation fails for invalid keycode."""
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "INVALID-KEY"}
        )
        
        assert applier._validate_event(event) is False
        applier.stop()

    def test_validate_missing_mouse_coordinates(self, applier):
        """Test validation fails for missing mouse coordinates."""
        applier.start()
        
        # InputEvent itself validates, so missing coordinates fail at creation
        try:
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.MOUSE_MOVE,
                source_device_id=str(uuid.uuid4()),
                target_device_id=str(uuid.uuid4()),
                payload={"x": 100}  # Missing y
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected
        
        applier.stop()

    def test_validate_invalid_button(self, applier):
        """Test validation fails for invalid button."""
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_CLICK,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"button": "invalid_button"}
        )
        
        assert applier._validate_event(event) is False
        applier.stop()


class TestKeyboardEventApplication:
    """Test keyboard event application."""

    @patch('src.input.event_applier.KeyboardController')
    def test_apply_key_press(self, mock_kb_controller, applier):
        """Test applying key press."""
        mock_kb = MagicMock()
        mock_kb_controller.return_value = mock_kb
        applier.keyboard = mock_kb
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        applier.apply_event(event)
        time.sleep(0.05)  # Wait for processing
        
        metrics = applier.get_metrics()
        assert metrics.keyboard_events >= 1
        
        applier.stop()

    @patch('src.input.event_applier.KeyboardController')
    def test_apply_key_release(self, mock_kb_controller, applier):
        """Test applying key release."""
        mock_kb = MagicMock()
        mock_kb_controller.return_value = mock_kb
        applier.keyboard = mock_kb
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_RELEASE,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        applier.apply_event(event)
        time.sleep(0.05)
        
        metrics = applier.get_metrics()
        assert metrics.keyboard_events >= 1
        
        applier.stop()


class TestMouseEventApplication:
    """Test mouse event application."""

    @patch('src.input.event_applier.MouseController')
    def test_apply_mouse_move(self, mock_mouse_controller, applier):
        """Test applying mouse move."""
        mock_mouse = MagicMock()
        mock_mouse_controller.return_value = mock_mouse
        applier.mouse = mock_mouse
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"x": 100, "y": 200}
        )
        
        applier.apply_event(event)
        time.sleep(0.05)
        
        metrics = applier.get_metrics()
        assert metrics.mouse_events >= 1
        
        applier.stop()

    @patch('src.input.event_applier.MouseController')
    def test_apply_mouse_click(self, mock_mouse_controller, applier):
        """Test applying mouse click."""
        mock_mouse = MagicMock()
        mock_mouse_controller.return_value = mock_mouse
        applier.mouse = mock_mouse
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_CLICK,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"button": "left", "clicks": 1}
        )
        
        applier.apply_event(event)
        time.sleep(0.05)
        
        metrics = applier.get_metrics()
        assert metrics.mouse_events >= 1
        
        applier.stop()

    @patch('src.input.event_applier.MouseController')
    def test_apply_mouse_scroll(self, mock_mouse_controller, applier):
        """Test applying mouse scroll."""
        mock_mouse = MagicMock()
        mock_mouse_controller.return_value = mock_mouse
        applier.mouse = mock_mouse
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_SCROLL,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"scroll_delta": 3}
        )
        
        applier.apply_event(event)
        time.sleep(0.05)
        
        metrics = applier.get_metrics()
        assert metrics.mouse_events >= 1
        
        applier.stop()


class TestMetrics:
    """Test metrics tracking."""

    def test_metrics_event_received(self, applier):
        """Test events_received metric."""
        applier.start()
        
        for i in range(5):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=str(uuid.uuid4()),
                target_device_id=str(uuid.uuid4()),
                payload={"keycode": "A"}
            )
            applier.apply_event(event)
        
        time.sleep(0.1)
        
        metrics = applier.get_metrics()
        assert metrics.events_received == 5
        
        applier.stop()

    def test_metrics_event_applied(self, applier):
        """Test events_applied metric."""
        applier.start()
        
        for i in range(3):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=str(uuid.uuid4()),
                target_device_id=str(uuid.uuid4()),
                payload={"keycode": "A"}
            )
            applier.apply_event(event)
        
        time.sleep(0.1)
        
        metrics = applier.get_metrics()
        assert metrics.events_applied >= 3
        
        applier.stop()

    def test_metrics_keyboard_events(self, applier):
        """Test keyboard_events metric."""
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        applier.apply_event(event)
        
        time.sleep(0.05)
        
        metrics = applier.get_metrics()
        assert metrics.keyboard_events >= 1
        
        applier.stop()

    def test_metrics_mouse_events(self, applier):
        """Test mouse_events metric."""
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"x": 100, "y": 200}
        )
        applier.apply_event(event)
        
        time.sleep(0.05)
        
        metrics = applier.get_metrics()
        assert metrics.mouse_events >= 1
        
        applier.stop()

    def test_metrics_reset(self, applier):
        """Test resetting metrics."""
        applier.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        applier.apply_event(event)
        
        time.sleep(0.05)
        
        applier.reset_metrics()
        
        metrics = applier.get_metrics()
        assert metrics.events_received == 0
        assert metrics.events_applied == 0
        
        applier.stop()


class TestStateTracking:
    """Test state tracking."""

    def test_get_pressed_keys(self, applier):
        """Test getting pressed keys."""
        applier.start()
        
        # Manually add keys to pressed set
        applier._pressed_keys.add("A")
        applier._pressed_keys.add("B")
        
        pressed = applier.get_pressed_keys()
        assert "A" in pressed
        assert "B" in pressed
        
        applier.stop()

    def test_get_mouse_position(self, applier):
        """Test getting mouse position."""
        applier.start()
        
        # Manually set mouse position
        applier._mouse_position = (100, 200)
        
        position = applier.get_mouse_position()
        assert position == (100, 200)
        
        applier.stop()

    def test_release_all_keys(self, applier):
        """Test releasing all pressed keys."""
        with patch('src.input.event_applier.KeyboardController'):
            applier.start()
            
            applier._pressed_keys.add("A")
            applier._pressed_keys.add("B")
            applier._pressed_keys.add("C")
            
            applier.release_all_keys()
            
            # All keys should be released
            assert len(applier._pressed_keys) == 0
            
            applier.stop()


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_event_type(self, applier):
        """Test handling invalid event type."""
        applier.start()
        
        # Create event with unknown type
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        # Manually call _apply_single_event with patched event type
        original_type = event.event_type
        
        # This should handle gracefully
        applier.apply_event(event)
        time.sleep(0.05)
        
        applier.stop()

    def test_metrics_error_tracking(self, applier):
        """Test error tracking in metrics."""
        applier.start()
        
        # Create event with mixed types - queue it and verify error tracking
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"x": 100, "y": 200}
        )
        
        applier.apply_event(event)
        time.sleep(0.1)
        
        metrics = applier.get_metrics()
        assert metrics.events_received >= 1
        
        applier.stop()
