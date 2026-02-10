"""End-to-end integration tests for Phase 4 - Input Relay and Device Communication."""

import pytest
import uuid
import time
from unittest.mock import Mock, MagicMock, patch

from src.models.device import Device, DeviceOS, DeviceRole
from src.models.input_event import InputEvent, InputEventType
from src.network.device_communicator import DeviceCommunicator, InputEventReceiver
from src.relay.input_relay import InputRelay, RelayManager, RelayConfig
from src.network.connection import ConnectionHandler


@pytest.fixture
def master_device():
    """Create master (local) device."""
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
    """Create client (remote) device."""
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
    conn = Mock(spec=ConnectionHandler)
    conn.send_message = Mock(return_value=True)
    conn.is_connected = Mock(return_value=True)
    return conn


class TestInputRelayE2E:
    """End-to-end tests for input relay."""

    def test_single_keyboard_event_relay(self, master_device, client_device, mock_connection):
        """Test relaying single keyboard event from master to client."""
        relay = InputRelay(master_device, client_device, mock_connection)
        relay.start()
        
        # Queue keyboard event
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=master_device.id,
            target_device_id=client_device.id,
            payload={"keycode": "A"}
        )
        
        assert relay.queue_event(event)
        
        # Wait for relay to process
        time.sleep(0.1)
        
        # Verify metrics
        metrics = relay.get_metrics()
        assert metrics.events_received == 1
        assert metrics.events_forwarded >= 1
        
        relay.stop()

    def test_multiple_events_batching(self, master_device, client_device, mock_connection):
        """Test batching of multiple events."""
        config = RelayConfig(batch_size=5, batch_timeout_ms=100)
        relay = InputRelay(master_device, client_device, mock_connection, config)
        relay.start()
        
        # Queue 5 keyboard events
        for i in range(5):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=master_device.id,
                target_device_id=client_device.id,
                payload={"keycode": f"KEY_{i}"}
            )
            assert relay.queue_event(event)
        
        # Wait for processing
        time.sleep(0.2)
        
        metrics = relay.get_metrics()
        assert metrics.events_received == 5
        assert metrics.events_forwarded >= 5
        
        relay.stop()

    def test_mixed_input_events(self, master_device, client_device, mock_connection):
        """Test relaying mixed keyboard and mouse events."""
        relay = InputRelay(master_device, client_device, mock_connection)
        relay.start()
        
        # Queue keyboard event
        kb_event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=master_device.id,
            target_device_id=client_device.id,
            payload={"keycode": "A"}
        )
        assert relay.queue_event(kb_event)
        
        # Queue mouse event
        mouse_event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=master_device.id,
            target_device_id=client_device.id,
            payload={"x": 100, "y": 200}
        )
        assert relay.queue_event(mouse_event)
        
        time.sleep(0.1)
        
        metrics = relay.get_metrics()
        assert metrics.events_received == 2
        assert metrics.events_forwarded >= 2
        
        relay.stop()

    def test_relay_error_recovery(self, master_device, client_device, mock_connection):
        """Test relay recovery from connection errors."""
        # First call fails, then succeeds
        mock_connection.send_message = Mock(side_effect=[False, True, True])
        
        config = RelayConfig(max_retries=2, retry_delay_ms=10)
        relay = InputRelay(master_device, client_device, mock_connection, config)
        relay.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=master_device.id,
            target_device_id=client_device.id,
            payload={"keycode": "A"}
        )
        
        assert relay.queue_event(event)
        time.sleep(0.2)
        
        metrics = relay.get_metrics()
        # Should have retried and eventually succeeded
        assert metrics.events_received >= 1
        
        relay.stop()


class TestMultiDeviceRelayE2E:
    """End-to-end tests for multi-device relay scenarios."""

    def test_relay_to_two_devices(self, master_device, mock_connection):
        """Test broadcasting relay to multiple client devices."""
        client1 = Device(id=str(uuid.uuid4()), name="Client1", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.101", port=5000)
        client2 = Device(id=str(uuid.uuid4()), name="Client2", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.102", port=5000)
        
        manager = RelayManager(master_device)
        
        relay1 = manager.add_relay(client1, mock_connection)
        relay2 = manager.add_relay(client2, mock_connection)
        
        assert relay1 is not None
        assert relay2 is not None
        
        # Start both relays
        relay1.start()
        relay2.start()
        
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
        
        time.sleep(0.1)
        
        # Verify both relays processed the event
        metrics1 = relay1.get_metrics()
        metrics2 = relay2.get_metrics()
        
        assert metrics1.events_received == 1
        assert metrics2.events_received == 1
        
        manager.shutdown()

    def test_add_and_remove_relay_dynamically(self, master_device, mock_connection):
        """Test dynamically adding and removing relays."""
        manager = RelayManager(master_device)
        
        device1 = Device(id=str(uuid.uuid4()), name="Device1", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.101", port=5000)
        device2 = Device(id=str(uuid.uuid4()), name="Device2", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.102", port=5000)
        
        # Add first device
        relay1 = manager.add_relay(device1, mock_connection)
        relay1.start()
        assert len(manager.relays) == 1
        
        # Add second device
        relay2 = manager.add_relay(device2, mock_connection)
        relay2.start()
        assert len(manager.relays) == 2
        
        # Broadcast to both
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=master_device.id,
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        count = manager.broadcast_event(event)
        assert count == 2
        
        # Remove first device
        manager.remove_relay(device1.id)
        assert len(manager.relays) == 1
        
        # Broadcast again - only to remaining device
        count = manager.broadcast_event(event)
        assert count == 1
        
        manager.shutdown()


class TestDeviceCommunicatorE2E:
    """End-to-end tests for device communicator."""

    def test_establish_and_communicate(self, master_device, client_device, mock_connection):
        """Test establishing connection and communicating with device."""
        communicator = DeviceCommunicator(master_device)
        
        # Establish connection
        success = communicator.establish_connection(client_device, mock_connection)
        assert success
        
        # Send event
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=master_device.id,
            target_device_id=client_device.id,
            payload={"keycode": "A"}
        )
        
        assert communicator.send_input_event(client_device.id, event)
        
        # Verify connected devices
        devices = communicator.get_connected_devices()
        assert len(devices) == 1
        assert client_device in devices
        
        # Check connection status
        status = communicator.get_connection_status(client_device.id)
        assert status["is_active"] is True
        
        communicator.shutdown()

    def test_event_receiver_callback_flow(self, master_device, client_device, mock_connection):
        """Test complete event receiver callback flow."""
        communicator = DeviceCommunicator(master_device)
        receiver = InputEventReceiver(communicator)
        
        # Register handler
        handler_calls = []
        def handler(event):
            handler_calls.append(event)
        
        receiver.register_handler(handler)
        
        # Process event
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=client_device.id,
            target_device_id=master_device.id,
            payload={"keycode": "A"}
        )
        
        receiver.process_received_event(event)
        
        # Verify handler was called
        assert len(handler_calls) == 1
        assert handler_calls[0] == event

    def test_connection_lifecycle(self, master_device, client_device, mock_connection):
        """Test full connection lifecycle."""
        communicator = DeviceCommunicator(master_device)
        
        # Track callbacks
        callbacks = {
            "connected": [],
            "disconnected": []
        }
        
        communicator.on_device_connected = lambda device: callbacks["connected"].append(device)
        communicator.on_device_disconnected = lambda device: callbacks["disconnected"].append(device)
        
        # Establish connection
        communicator.establish_connection(client_device, mock_connection)
        assert len(callbacks["connected"]) == 1
        
        # Verify connection
        status = communicator.get_connection_status(client_device.id)
        assert status["is_active"] is True
        
        # Close connection
        communicator.close_connection(client_device.id)
        assert len(callbacks["disconnected"]) == 1
        
        # Verify disconnected
        devices = communicator.get_connected_devices()
        assert len(devices) == 0

    def test_broadcast_to_multiple_devices(self, master_device, mock_connection):
        """Test broadcasting to multiple connected devices."""
        communicator = DeviceCommunicator(master_device)
        
        client1 = Device(id=str(uuid.uuid4()), name="Client1", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.101", port=5000)
        client2 = Device(id=str(uuid.uuid4()), name="Client2", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.102", port=5000)
        client3 = Device(id=str(uuid.uuid4()), name="Client3", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.103", port=5000)
        
        # Establish connections
        communicator.establish_connection(client1, mock_connection)
        communicator.establish_connection(client2, mock_connection)
        communicator.establish_connection(client3, mock_connection)
        
        assert len(communicator.get_connected_devices()) == 3
        
        # Broadcast event to all
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=master_device.id,
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "Return"}
        )
        
        count = communicator.broadcast_input_event(event)
        assert count == 3
        
        communicator.shutdown()


class TestReliabilityAndPerformance:
    """Tests for reliability and performance characteristics."""

    def test_high_frequency_events(self, master_device, client_device, mock_connection):
        """Test handling high-frequency input events."""
        relay = InputRelay(master_device, client_device, mock_connection)
        relay.start()
        
        # Queue 50 events rapidly
        event_count = 50
        for i in range(event_count):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.MOUSE_MOVE,
                source_device_id=master_device.id,
                target_device_id=client_device.id,
                payload={"x": i * 10, "y": i * 10}
            )
            assert relay.queue_event(event)
        
        # Wait for processing
        time.sleep(0.5)
        
        metrics = relay.get_metrics()
        assert metrics.events_received == event_count
        assert metrics.events_forwarded >= event_count - 10  # Allow some variation
        
        relay.stop()

    def test_queue_overflow_handling(self, master_device, client_device, mock_connection):
        """Test handling queue overflow gracefully."""
        config = RelayConfig(max_queue_size=10)
        relay = InputRelay(master_device, client_device, mock_connection, config)
        relay.start()
        
        # Try to queue more events than capacity
        overflow_count = 0
        for i in range(20):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=master_device.id,
                target_device_id=client_device.id,
                payload={"keycode": f"K_{i}"}
            )
            
            if not relay.queue_event(event):
                overflow_count += 1
        
        # Some events should have been rejected
        assert overflow_count > 0
        
        metrics = relay.get_metrics()
        assert metrics.events_failed > 0
        
        relay.stop()

    def test_metrics_accuracy(self, master_device, client_device, mock_connection):
        """Test metrics tracking accuracy."""
        relay = InputRelay(master_device, client_device, mock_connection)
        relay.start()
        
        # Queue and forward events
        for i in range(10):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=master_device.id,
                target_device_id=client_device.id,
                payload={"keycode": "A"}
            )
            relay.queue_event(event)
        
        time.sleep(0.2)
        
        metrics = relay.get_metrics()
        
        # Verify metrics consistency
        assert metrics.events_received == 10
        assert metrics.events_forwarded == 10
        assert metrics.events_failed == 0
        assert metrics.bytes_sent > 0
        assert metrics.avg_latency_ms >= 0
        
        relay.stop()

    def test_concurrent_relay_operations(self, master_device, mock_connection):
        """Test multiple relays operating concurrently."""
        client1 = Device(id=str(uuid.uuid4()), name="Client1", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.101", port=5000)
        client2 = Device(id=str(uuid.uuid4()), name="Client2", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.102", port=5000)
        client3 = Device(id=str(uuid.uuid4()), name="Client3", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.103", port=5000)
        
        manager = RelayManager(master_device)
        
        relay1 = manager.add_relay(client1, mock_connection)
        relay2 = manager.add_relay(client2, mock_connection)
        relay3 = manager.add_relay(client3, mock_connection)
        
        # Start all relays
        relay1.start()
        relay2.start()
        relay3.start()
        
        # Send different events to each
        for i in range(10):
            event1 = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=master_device.id,
                target_device_id=client1.id,
                payload={"keycode": f"K_{i}"}
            )
            relay1.queue_event(event1)
            
            event2 = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.MOUSE_MOVE,
                source_device_id=master_device.id,
                target_device_id=client2.id,
                payload={"x": i, "y": i}
            )
            relay2.queue_event(event2)
            
            event3 = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_RELEASE,
                source_device_id=master_device.id,
                target_device_id=client3.id,
                payload={"keycode": f"K_{i}"}
            )
            relay3.queue_event(event3)
        
        time.sleep(0.3)
        
        # Verify all relays processed their events independently
        metrics1 = relay1.get_metrics()
        metrics2 = relay2.get_metrics()
        metrics3 = relay3.get_metrics()
        
        assert metrics1.events_received == 10
        assert metrics2.events_received == 10
        assert metrics3.events_received == 10
        
        manager.shutdown()
