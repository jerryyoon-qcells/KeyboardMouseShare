"""End-to-end integration tests for Phase 5 - Event Application on Target Device."""

import pytest
import uuid
import time
from unittest.mock import Mock, patch, MagicMock

from src.input.event_applier import InputEventApplier, ApplierConfig
from src.models.device import Device, DeviceOS, DeviceRole
from src.models.input_event import InputEvent, InputEventType
from src.network.device_communicator import DeviceCommunicator, InputEventReceiver
from src.relay.input_relay import InputRelay, RelayManager


@pytest.fixture
def master_device():
    """Create master (remote sender) device."""
    return Device(
        id=str(uuid.uuid4()),
        name="Master",
        os=DeviceOS.WINDOWS,
        ip_address="192.168.1.100",
        port=5000,
        role=DeviceRole.MASTER
    )


@pytest.fixture
def client_device():
    """Create client (local receiver) device."""
    return Device(
        id=str(uuid.uuid4()),
        name="Client",
        os=DeviceOS.WINDOWS,
        ip_address="192.168.1.101",
        port=5000,
        role=DeviceRole.CLIENT
    )


@pytest.fixture
def mock_connection():
    """Create mock connection handler."""
    conn = Mock()
    conn.send_message = Mock(return_value=True)
    conn.is_connected = Mock(return_value=True)
    return conn


@pytest.fixture
def applier(client_device):
    """Create InputEventApplier for client device."""
    return InputEventApplier(client_device)


class TestEventApplicationE2E:
    """End-to-end event application tests."""

    def test_keyboard_input_chain(self, master_device, client_device, applier):
        """Test keyboard input from master to client application."""
        applier.start()
        
        # Simulate keyboard input from master
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=master_device.id,
            target_device_id=client_device.id,
            payload={"keycode": "A"}
        )
        
        # Apply on client side
        assert applier.apply_event(event)
        
        time.sleep(0.05)
        
        metrics = applier.get_metrics()
        assert metrics.events_received == 1
        assert metrics.keyboard_events == 1
        assert metrics.events_applied >= 1
        
        applier.stop()

    def test_mouse_input_chain(self, master_device, client_device, applier):
        """Test mouse input from master to client application."""
        applier.start()
        
        # Simulate mouse movement from master
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=master_device.id,
            target_device_id=client_device.id,
            payload={"x": 500, "y": 300}
        )
        
        # Apply on client side
        assert applier.apply_event(event)
        
        time.sleep(0.05)
        
        metrics = applier.get_metrics()
        assert metrics.events_received == 1
        assert metrics.mouse_events == 1
        assert metrics.events_applied >= 1
        
        # Verify mouse position tracked
        position = applier.get_mouse_position()
        assert position == (500, 300)
        
        applier.stop()

    def test_mixed_keyboard_typing_sequence(self, master_device, client_device, applier):
        """Test typing sequence (multiple key presses/releases)."""
        applier.start()
        
        keys = ["A", "B", "C", "D", "E"]
        
        # Type sequence
        for key in keys:
            # Press
            press_event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=master_device.id,
                target_device_id=client_device.id,
                payload={"keycode": key}
            )
            applier.apply_event(press_event)
            
            # Release
            release_event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_RELEASE,
                source_device_id=master_device.id,
                target_device_id=client_device.id,
                payload={"keycode": key}
            )
            applier.apply_event(release_event)
        
        time.sleep(0.1)
        
        metrics = applier.get_metrics()
        assert metrics.events_received == len(keys) * 2  # Press + Release per key
        assert metrics.keyboard_events >= len(keys) * 2 - 2
        
        applier.stop()

    def test_mouse_click_sequence(self, master_device, client_device, applier):
        """Test mouse click sequence."""
        applier.start()
        
        # Move to position
        move_event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=master_device.id,
            target_device_id=client_device.id,
            payload={"x": 100, "y": 200}
        )
        applier.apply_event(move_event)
        
        # Click left
        click_event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_CLICK,
            source_device_id=master_device.id,
            target_device_id=client_device.id,
            payload={"button": "left", "clicks": 1}
        )
        applier.apply_event(click_event)
        
        time.sleep(0.05)
        
        metrics = applier.get_metrics()
        assert metrics.events_received == 2
        assert metrics.mouse_events >= 2
        
        applier.stop()


class TestEventReceiverIntegration:
    """Test InputEventReceiver integration with event applier."""

    def test_receiver_to_applier_flow(self, client_device, applier):
        """Test event flow from receiver to applier."""
        communicator = DeviceCommunicator(client_device)
        receiver = InputEventReceiver(communicator)
        applier.start()
        
        # Track applied events
        applied_events = []
        
        # Register handler to apply events
        def apply_handler(event):
            applied_events.append(event)
            applier.apply_event(event)
        
        receiver.register_handler(apply_handler)
        
        # Process received event
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=client_device.id,
            payload={"keycode": "A"}
        )
        
        receiver.process_received_event(event)
        time.sleep(0.05)
        
        # Verify event was applied
        assert len(applied_events) == 1
        
        metrics = applier.get_metrics()
        assert metrics.events_received == 1
        
        applier.stop()

    def test_receiver_broadcasts_to_multiple_handlers(self, client_device, applier):
        """Test receiver broadcasting to multiple handlers."""
        communicator = DeviceCommunicator(client_device)
        receiver = InputEventReceiver(communicator)
        applier.start()
        
        # Track calls to multiple handlers
        handler1_calls = []
        handler2_calls = []
        
        def handler1(event):
            handler1_calls.append(event)
            applier.apply_event(event)
        
        def handler2(event):
            handler2_calls.append(event)
        
        receiver.register_handler(handler1)
        receiver.register_handler(handler2)
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=client_device.id,
            payload={"keycode": "A"}
        )
        
        receiver.process_received_event(event)
        
        # Both handlers should be called
        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1
        
        metrics = applier.get_metrics()
        assert metrics.events_received == 1
        
        applier.stop()


class TestRelayToApplicationFlow:
    """Test complete relay to application flow."""

    def test_relay_and_apply_single_event(self, master_device, client_device, mock_connection, applier):
        """Test relay forwarding and application of single event."""
        # Setup relay on master
        relay = InputRelay(master_device, client_device, mock_connection)
        relay.start()
        
        # Setup applier on client
        applier.start()
        
        # Create and queue event on master
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=master_device.id,
            target_device_id=client_device.id,
            payload={"keycode": "A"}
        )
        
        # Relay it
        relay.queue_event(event)
        
        # Then apply on client
        applier.apply_event(event)
        
        time.sleep(0.1)
        
        # Verify both relay and applier processed event
        relay_metrics = relay.get_metrics()
        applier_metrics = applier.get_metrics()
        
        assert relay_metrics.events_received == 1
        assert applier_metrics.events_received == 1
        
        relay.stop()
        applier.stop()

    def test_relay_broadcast_to_multiple_appliers(self, master_device, mock_connection):
        """Test relay broadcasting to multiple client appliers."""
        # Create two client devices
        client1 = Device(id=str(uuid.uuid4()), name="Client1", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.101", port=5000, role=DeviceRole.CLIENT)
        client2 = Device(id=str(uuid.uuid4()), name="Client2", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.102", port=5000, role=DeviceRole.CLIENT)
        
        # Setup relay manager
        manager = RelayManager(master_device)
        relay1 = manager.add_relay(client1, mock_connection)
        relay2 = manager.add_relay(client2, mock_connection)
        
        # Setup appliers
        applier1 = InputEventApplier(client1)
        applier2 = InputEventApplier(client2)
        applier1.start()
        applier2.start()
        
        # Broadcast event
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=master_device.id,
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        count = manager.broadcast_event(event)
        assert count == 2
        
        # Apply on both clients
        applier1.apply_event(event)
        applier2.apply_event(event)
        
        time.sleep(0.1)
        
        metrics1 = applier1.get_metrics()
        metrics2 = applier2.get_metrics()
        
        assert metrics1.events_received == 1
        assert metrics2.events_received == 1
        
        manager.shutdown()
        applier1.stop()
        applier2.stop()


class TestApplicationStateConsistency:
    """Test state consistency during application."""

    def test_pressed_keys_state_tracking(self, client_device, applier):
        """Test tracking of currently pressed keys."""
        applier.start()
        
        # Press multiple keys with valid keycodes
        keys_to_press = ["A", "B", "Return"]
        
        for key in keys_to_press:
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=str(uuid.uuid4()),
                target_device_id=client_device.id,
                payload={"keycode": key}
            )
            applier._apply_key_press(event)
        
        # Check pressed keys
        pressed = applier.get_pressed_keys()
        assert "A" in pressed
        assert "B" in pressed
        assert "RETURN" in pressed
        
        # Release a key
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_RELEASE,
            source_device_id=str(uuid.uuid4()),
            target_device_id=client_device.id,
            payload={"keycode": "A"}
        )
        applier._apply_key_release(event)
        
        # Check pressed keys again
        pressed = applier.get_pressed_keys()
        assert "A" not in pressed
        assert "B" in pressed
        
        applier.stop()

    def test_mouse_position_tracking(self, client_device, applier):
        """Test tracking of current mouse position."""
        applier.start()
        
        # Move to multiple positions
        positions = [(100, 100), (200, 150), (300, 250)]
        
        for x, y in positions:
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.MOUSE_MOVE,
                source_device_id=str(uuid.uuid4()),
                target_device_id=client_device.id,
                payload={"x": x, "y": y}
            )
            applier._apply_mouse_move(event)
            
            # Verify position updated
            current_pos = applier.get_mouse_position()
            assert current_pos == (x, y)
        
        # Final position
        final_pos = applier.get_mouse_position()
        assert final_pos == (300, 250)
        
        applier.stop()


class TestApplicationErrorRecovery:
    """Test error recovery during event application."""

    def test_queue_full_rejection(self, client_device):
        """Test event rejection when queue is full."""
        config = ApplierConfig(max_queue_size=5)
        applier = InputEventApplier(client_device, config)
        applier.start()
        
        # Queue more events than capacity
        rejected_count = 0
        for i in range(10):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=str(uuid.uuid4()),
                target_device_id=client_device.id,
                payload={"keycode": "A"}
            )
            
            if not applier.apply_event(event):
                rejected_count += 1
        
        # Some should be rejected
        assert rejected_count > 0
        
        metrics = applier.get_metrics()
        assert metrics.events_failed > 0
        
        applier.stop()

    def test_validation_rejection(self, client_device):
        """Test validation rejection of invalid events."""
        applier = InputEventApplier(client_device)
        applier.start()
        
        # Try invalid event - InputEvent validation will fail
        # So we test with validation disabled and bad structure
        try:
            # KeyEvent without keycode will fail InputEvent creation
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=str(uuid.uuid4()),
                target_device_id=client_device.id,
                payload={}  # Missing keycode
            )
            assert False, "Should have failed validation"
        except ValueError:
            pass  # Expected
        
        applier.stop()

    def test_continuous_operation_after_error(self, client_device, applier):
        """Test applier continues after handling errors."""
        applier.start()
        
        # Queue valid event
        event1 = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=client_device.id,
            payload={"keycode": "A"}
        )
        applier.apply_event(event1)
        
        # Another valid event
        event2 = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=str(uuid.uuid4()),
            target_device_id=client_device.id,
            payload={"x": 100, "y": 200}
        )
        applier.apply_event(event2)
        
        time.sleep(0.1)
        
        # Verify both events processed
        metrics = applier.get_metrics()
        assert metrics.events_received == 2
        assert metrics.keyboard_events >= 1
        assert metrics.mouse_events >= 1
        
        applier.stop()


class TestPerformanceCharacteristics:
    """Test performance under various conditions."""

    def test_high_frequency_keyboard_events(self, client_device, applier):
        """Test handling high-frequency keyboard events."""
        applier.start()
        
        # Queue 50 rapid keyboard events
        for i in range(50):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=str(uuid.uuid4()),
                target_device_id=client_device.id,
                payload={"keycode": "A"}
            )
            applier.apply_event(event)
        
        time.sleep(0.5)
        
        metrics = applier.get_metrics()
        assert metrics.events_received == 50
        # Most events should be applied successfully
        assert metrics.keyboard_events >= 40
        
        applier.stop()

    def test_mixed_event_sequence(self, client_device, applier):
        """Test mixed keyboard and mouse event sequence."""
        applier.start()
        
        # Alternate keyboard and mouse events with simple keycodes
        keys = ["A", "B", "C", "D", "E"]
        
        for i in range(10):
            # Type key - use valid keycodes
            key = keys[i % len(keys)]
            kb_event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=str(uuid.uuid4()),
                target_device_id=client_device.id,
                payload={"keycode": key}
            )
            applier.apply_event(kb_event)
            
            # Move mouse
            mouse_event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.MOUSE_MOVE,
                source_device_id=str(uuid.uuid4()),
                target_device_id=client_device.id,
                payload={"x": 100 + i * 10, "y": 100 + i * 10}
            )
            applier.apply_event(mouse_event)
        
        time.sleep(0.3)
        
        metrics = applier.get_metrics()
        assert metrics.events_received == 20
        # Most events should be applied
        assert metrics.keyboard_events >= 8
        assert metrics.mouse_events >= 8
        
        applier.stop()

    def test_metrics_accuracy(self, client_device, applier):
        """Test metrics tracking accuracy."""
        applier.start()
        
        # Queue diverse events
        kp_count = 5
        km_count = 5
        mm_count = 5
        
        for i in range(kp_count):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=str(uuid.uuid4()),
                target_device_id=client_device.id,
                payload={"keycode": "A"}
            )
            applier.apply_event(event)
        
        for i in range(km_count):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_RELEASE,
                source_device_id=str(uuid.uuid4()),
                target_device_id=client_device.id,
                payload={"keycode": "A"}
            )
            applier.apply_event(event)
        
        for i in range(mm_count):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.MOUSE_MOVE,
                source_device_id=str(uuid.uuid4()),
                target_device_id=client_device.id,
                payload={"x": i * 50, "y": i * 50}
            )
            applier.apply_event(event)
        
        time.sleep(0.3)
        
        metrics = applier.get_metrics()
        assert metrics.events_received == kp_count + km_count + mm_count
        assert metrics.keyboard_events >= kp_count + km_count - 1
        assert metrics.mouse_events >= mm_count - 1
        
        applier.stop()
