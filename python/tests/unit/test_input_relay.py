"""Tests for input relay service."""

import pytest
import time
import uuid
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timezone

from src.relay.input_relay import InputRelay, RelayManager, RelayConfig, RelayMetrics
from src.models.device import Device, DeviceOS, DeviceRole
from src.models.input_event import InputEvent, InputEventType
from src.network.connection import ConnectionHandler


@pytest.fixture
def local_device():
    """Create local device."""
    return Device(
        id=str(uuid.uuid4()),
        name="LocalDevice",
        os=DeviceOS.WINDOWS,
        ip_address="192.168.1.100",
        port=5000,
        role=DeviceRole.MASTER
    )


@pytest.fixture
def remote_device():
    """Create remote device."""
    return Device(
        id=str(uuid.uuid4()),
        name="RemoteDevice",
        os=DeviceOS.WINDOWS,
        ip_address="192.168.1.101",
        port=5000,
        role=DeviceRole.CLIENT
    )


@pytest.fixture
def mock_connection():
    """Create mock connection."""
    conn = Mock(spec=ConnectionHandler)
    conn.send_message = Mock(return_value=True)
    return conn


@pytest.fixture
def relay_config():
    """Create relay configuration."""
    return RelayConfig(
        max_queue_size=100,
        max_retries=2,
        retry_delay_ms=10,
        batch_size=5,
        batch_timeout_ms=50
    )


@pytest.fixture
def input_relay(local_device, remote_device, mock_connection, relay_config):
    """Create InputRelay instance."""
    return InputRelay(
        local_device,
        remote_device,
        mock_connection,
        relay_config
    )


class TestInputRelayInitialization:
    """Test InputRelay initialization."""

    def test_relay_creation(self, input_relay, local_device, remote_device):
        """Test creating a relay."""
        assert input_relay.local_device == local_device
        assert input_relay.remote_device == remote_device
        assert not input_relay.is_running

    def test_relay_with_default_config(self, local_device, remote_device, mock_connection):
        """Test relay with default configuration."""
        relay = InputRelay(local_device, remote_device, mock_connection)
        assert relay.config is not None
        assert relay.config.max_queue_size == 1000
        assert relay.config.batch_size == 10

    def test_relay_metrics_initialization(self, input_relay):
        """Test metrics are initialized."""
        metrics = input_relay.get_metrics()
        assert metrics.events_received == 0
        assert metrics.events_forwarded == 0
        assert metrics.events_failed == 0


class TestRelayLifecycle:
    """Test relay start/stop lifecycle."""

    def test_start_relay(self, input_relay):
        """Test starting relay."""
        success = input_relay.start()
        assert success
        assert input_relay.is_running
        input_relay.stop()

    def test_start_already_running(self, input_relay):
        """Test starting relay that's already running."""
        input_relay.start()
        success = input_relay.start()
        assert not success
        input_relay.stop()

    def test_stop_relay(self, input_relay):
        """Test stopping relay."""
        input_relay.start()
        assert input_relay.is_running
        success = input_relay.stop()
        assert success
        assert not input_relay.is_running

    def test_stop_when_not_running(self, input_relay):
        """Test stopping relay that's not running."""
        success = input_relay.stop()
        assert not success

    def test_relay_thread_creation(self, input_relay):
        """Test relay thread is created on start."""
        input_relay.start()
        assert input_relay.relay_thread is not None
        assert input_relay.relay_thread.is_alive()
        input_relay.stop()

    def test_relay_cleanup_on_stop(self, input_relay):
        """Test relay cleans up properly on stop."""
        input_relay.start()
        
        # Add event to queue
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        input_relay.queue_event(event)
        
        # Stop relay
        input_relay.stop()
        
        # Verify cleanup
        assert not input_relay.is_running
        assert input_relay.relay_thread is not None


class TestEventQueueing:
    """Test event queueing functionality."""

    def test_queue_event(self, input_relay):
        """Test queueing an event."""
        input_relay.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        success = input_relay.queue_event(event)
        assert success
        assert input_relay.get_metrics().events_received == 1
        
        input_relay.stop()

    def test_queue_when_not_running(self, input_relay):
        """Test queueing when relay not running."""
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        success = input_relay.queue_event(event)
        assert not success

    def test_queue_full(self, local_device, remote_device, mock_connection):
        """Test queueing when queue is full."""
        config = RelayConfig(max_queue_size=2)
        relay = InputRelay(local_device, remote_device, mock_connection, config)
        relay.start()
        
        # Fill queue
        for i in range(2):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=str(uuid.uuid4()),
                target_device_id=str(uuid.uuid4()),
                payload={"keycode": "A"}
            )
            relay.queue_event(event)
        
        # Try to exceed capacity
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        success = relay.queue_event(event)
        assert not success
        assert relay.get_metrics().events_failed == 1
        
        relay.stop()

    def test_queue_keyboard_event(self, input_relay):
        """Test queueing keyboard event."""
        input_relay.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_RELEASE,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "SHIFT"}
        )
        
        success = input_relay.queue_event(event)
        assert success
        
        input_relay.stop()

    def test_queue_mouse_event(self, input_relay):
        """Test queueing mouse event."""
        input_relay.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"x": 100, "y": 200}
        )
        
        success = input_relay.queue_event(event)
        assert success
        
        input_relay.stop()


class TestEventForwarding:
    """Test event forwarding functionality."""

    def test_forward_single_event(self, input_relay, mock_connection):
        """Test forwarding a single event."""
        input_relay.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        input_relay.queue_event(event)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify send was called
        assert mock_connection.send_message.called
        
        input_relay.stop()

    def test_forward_multiple_events(self, input_relay, mock_connection):
        """Test forwarding multiple events."""
        input_relay.start()
        
        events = []
        for i in range(3):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=str(uuid.uuid4()),
                target_device_id=str(uuid.uuid4()),
                payload={"keycode": chr(65 + i)}  # A, B, C
            )
            events.append(event)
            input_relay.queue_event(event)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Verify sends occurred
        assert mock_connection.send_message.call_count >= 1
        
        input_relay.stop()

    def test_no_forward_when_disconnected(self, local_device, remote_device):
        """Test events not forwarded when connection is None."""
        relay = InputRelay(local_device, remote_device, None)
        relay.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        relay.queue_event(event)
        time.sleep(0.1)
        
        metrics = relay.get_metrics()
        assert metrics.events_failed > 0
        
        relay.stop()


class TestBatching:
    """Test event batching functionality."""

    def test_batch_accumulation(self, input_relay, mock_connection):
        """Test events accumulate in batch."""
        input_relay.start()
        
        # Queue events
        for i in range(3):
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=str(uuid.uuid4()),
                target_device_id=str(uuid.uuid4()),
                payload={"keycode": chr(65 + i)}
            )
            input_relay.queue_event(event)
        
        # Verify batch is accumulating
        assert len(input_relay.batch_buffer) <= 3
        
        input_relay.stop()

    def test_batch_flush_on_size(self, input_relay, mock_connection):
        """Test batch flushed when size reached."""
        input_relay.start()
        
        # Queue events equal to batch size
        for i in range(5):  # batch_size = 5
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=InputEventType.KEY_PRESS,
                source_device_id=str(uuid.uuid4()),
                target_device_id=str(uuid.uuid4()),
                payload={"keycode": chr(65 + i)}
            )
            input_relay.queue_event(event)
        
        time.sleep(0.1)
        
        # Batch should be flushed
        assert len(input_relay.batch_buffer) == 0
        
        input_relay.stop()

    def test_batch_flush_on_timeout(self, input_relay, mock_connection):
        """Test batch flushed on timeout."""
        input_relay.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        input_relay.queue_event(event)
        
        # Wait for batch timeout (config has 50ms timeout)
        time.sleep(0.15)
        
        # Batch should be flushed
        assert len(input_relay.batch_buffer) == 0
        
        input_relay.stop()


class TestMetrics:
    """Test metrics tracking."""

    def test_metrics_event_received(self, input_relay):
        """Test metrics track received events."""
        input_relay.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        input_relay.queue_event(event)
        
        metrics = input_relay.get_metrics()
        assert metrics.events_received == 1
        
        input_relay.stop()

    def test_metrics_event_forwarded(self, input_relay, mock_connection):
        """Test metrics track forwarded events."""
        input_relay.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        input_relay.queue_event(event)
        time.sleep(0.2)
        
        metrics = input_relay.get_metrics()
        assert metrics.events_forwarded >= 1
        
        input_relay.stop()

    def test_metrics_bytes_sent(self, input_relay, mock_connection):
        """Test metrics track bytes sent."""
        input_relay.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        input_relay.queue_event(event)
        time.sleep(0.2)
        
        metrics = input_relay.get_metrics()
        assert metrics.bytes_sent > 0
        
        input_relay.stop()

    def test_metrics_latency_calculation(self, input_relay, mock_connection):
        """Test metrics calculate latency."""
        input_relay.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        input_relay.queue_event(event)
        time.sleep(0.2)
        
        metrics = input_relay.get_metrics()
        assert metrics.avg_latency_ms >= 0
        
        input_relay.stop()

    def test_metrics_reset(self, input_relay):
        """Test metrics can be reset."""
        input_relay.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        input_relay.queue_event(event)
        
        # Reset metrics
        input_relay.reset_metrics()
        
        metrics = input_relay.get_metrics()
        assert metrics.events_received == 0
        assert metrics.events_forwarded == 0
        
        input_relay.stop()


class TestErrorHandling:
    """Test error handling and retries."""

    def test_retry_on_forward_failure(self, local_device, remote_device):
        """Test retries on forward failure."""
        mock_conn = Mock(spec=ConnectionHandler)
        mock_conn.send_message = Mock(side_effect=[
            Exception("Network error"),
            Exception("Network error"),
            None  # Success on third try
        ])
        
        config = RelayConfig(max_retries=3, retry_delay_ms=10)
        relay = InputRelay(local_device, remote_device, mock_conn, config)
        relay.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        relay.queue_event(event)
        time.sleep(0.3)
        
        # Should have retried
        assert mock_conn.send_message.call_count >= 1
        
        relay.stop()

    def test_max_retries_exceeded(self, local_device, remote_device):
        """Test event fails after max retries."""
        mock_conn = Mock(spec=ConnectionHandler)
        mock_conn.send_message = Mock(side_effect=Exception("Network error"))
        
        config = RelayConfig(max_retries=2, retry_delay_ms=10)
        relay = InputRelay(local_device, remote_device, mock_conn, config)
        relay.start()
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        relay.queue_event(event)
        time.sleep(0.2)
        
        metrics = relay.get_metrics()
        assert metrics.events_failed >= 1
        
        relay.stop()


class TestRelayManager:
    """Test RelayManager for managing multiple relays."""

    def test_manager_creation(self, local_device):
        """Test creating relay manager."""
        manager = RelayManager(local_device)
        assert manager.local_device == local_device
        assert len(manager.relays) == 0

    def test_add_relay(self, local_device, remote_device, mock_connection):
        """Test adding relay to manager."""
        manager = RelayManager(local_device)
        
        relay = manager.add_relay(remote_device, mock_connection)
        
        assert relay is not None
        assert remote_device.id in manager.relays
        assert relay.is_running
        
        manager.shutdown()

    def test_add_duplicate_relay(self, local_device, remote_device, mock_connection):
        """Test adding duplicate relay returns existing."""
        manager = RelayManager(local_device)
        
        relay1 = manager.add_relay(remote_device, mock_connection)
        relay2 = manager.add_relay(remote_device, mock_connection)
        
        assert relay1 == relay2
        assert len(manager.relays) == 1
        
        manager.shutdown()

    def test_remove_relay(self, local_device, remote_device, mock_connection):
        """Test removing relay from manager."""
        manager = RelayManager(local_device)
        
        manager.add_relay(remote_device, mock_connection)
        success = manager.remove_relay(remote_device.id)
        
        assert success
        assert remote_device.id not in manager.relays

    def test_broadcast_event(self, local_device, remote_device, mock_connection):
        """Test broadcasting event to all relays."""
        manager = RelayManager(local_device)
        
        # Add multiple relays
        device1 = Device(id=str(uuid.uuid4()), name="Device1", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.101", port=5000)
        device2 = Device(id=str(uuid.uuid4()), name="Device2", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.102", port=5000)
        
        manager.add_relay(device1, mock_connection)
        manager.add_relay(device2, mock_connection)
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        count = manager.broadcast_event(event)
        assert count == 2
        
        manager.shutdown()

    def test_get_metrics_summary(self, local_device, remote_device, mock_connection):
        """Test getting metrics summary from manager."""
        manager = RelayManager(local_device)
        
        relay = manager.add_relay(remote_device, mock_connection)
        relay.queue_event(InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        ))
        
        metrics = manager.get_metrics_summary()
        
        assert remote_device.id in metrics
        assert metrics[remote_device.id].events_received >= 1
        
        manager.shutdown()

    def test_shutdown_manager(self, local_device, remote_device, mock_connection):
        """Test shutting down manager."""
        manager = RelayManager(local_device)
        
        manager.add_relay(remote_device, mock_connection)
        success = manager.shutdown()
        
        assert success
        assert len(manager.relays) == 0


class TestRelayConfiguration:
    """Test relay configuration options."""

    def test_default_config(self):
        """Test default relay configuration."""
        config = RelayConfig()
        assert config.max_queue_size == 1000
        assert config.max_retries == 3
        assert config.batch_size == 10
        assert config.log_events is True

    def test_custom_config(self):
        """Test custom relay configuration."""
        config = RelayConfig(
            max_queue_size=500,
            max_retries=5,
            batch_size=20
        )
        assert config.max_queue_size == 500
        assert config.max_retries == 5
        assert config.batch_size == 20

    def test_metrics_initialization(self):
        """Test RelayMetrics initialization."""
        metrics = RelayMetrics()
        assert metrics.events_received == 0
        assert metrics.events_forwarded == 0
        assert metrics.events_failed == 0

    def test_metrics_reset(self):
        """Test RelayMetrics reset."""
        metrics = RelayMetrics()
        metrics.events_received = 10
        metrics.events_forwarded = 8
        metrics.events_failed = 2
        
        metrics.reset()
        
        assert metrics.events_received == 0
        assert metrics.events_forwarded == 0
        assert metrics.events_failed == 0
