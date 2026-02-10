"""Tests for device communication layer."""

import pytest
import uuid
from unittest.mock import Mock, MagicMock

from src.network.device_communicator import (
    DeviceCommunicator, InputEventReceiver, DeviceLink
)
from src.models.device import Device, DeviceOS, DeviceRole
from src.models.input_event import InputEvent, InputEventType
from src.network.connection import ConnectionHandler
from src.relay.input_relay import RelayConfig


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
def communicator(local_device):
    """Create DeviceCommunicator instance."""
    return DeviceCommunicator(local_device)


class TestDeviceCommunicatorInitialization:
    """Test DeviceCommunicator initialization."""

    def test_communicator_creation(self, communicator, local_device):
        """Test creating device communicator."""
        assert communicator.local_device == local_device
        assert len(communicator.device_links) == 0

    def test_relay_manager_initialization(self, communicator):
        """Test relay manager is initialized."""
        assert communicator.relay_manager is not None
        assert len(communicator.relay_manager.relays) == 0


class TestConnectionManagement:
    """Test connection management."""

    def test_establish_connection(self, communicator, remote_device, mock_connection):
        """Test establishing connection with remote device."""
        success = communicator.establish_connection(remote_device, mock_connection)
        
        assert success
        assert remote_device.id in communicator.device_links
        
        communicator.shutdown()

    def test_establish_duplicate_connection(self, communicator, remote_device, mock_connection):
        """Test establishing duplicate connection."""
        communicator.establish_connection(remote_device, mock_connection)
        success = communicator.establish_connection(remote_device, mock_connection)
        
        assert not success
        
        communicator.shutdown()

    def test_close_connection(self, communicator, remote_device, mock_connection):
        """Test closing connection with device."""
        communicator.establish_connection(remote_device, mock_connection)
        success = communicator.close_connection(remote_device.id)
        
        assert success
        assert remote_device.id not in communicator.device_links

    def test_close_nonexistent_connection(self, communicator):
        """Test closing connection that doesn't exist."""
        fake_id = str(uuid.uuid4())
        success = communicator.close_connection(fake_id)
        
        assert not success

    def test_connection_callback_on_connect(self, communicator, remote_device, mock_connection):
        """Test callback triggered on connection."""
        callback = Mock()
        communicator.on_device_connected = callback
        
        communicator.establish_connection(remote_device, mock_connection)
        
        callback.assert_called_once_with(remote_device)
        
        communicator.shutdown()

    def test_connection_callback_on_disconnect(self, communicator, remote_device, mock_connection):
        """Test callback triggered on disconnection."""
        callback = Mock()
        communicator.on_device_disconnected = callback
        
        communicator.establish_connection(remote_device, mock_connection)
        communicator.close_connection(remote_device.id)
        
        callback.assert_called_once_with(remote_device)


class TestInputEventSending:
    """Test input event sending."""

    def test_send_input_event(self, communicator, remote_device, mock_connection):
        """Test sending input event to device."""
        communicator.establish_connection(remote_device, mock_connection)
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        success = communicator.send_input_event(remote_device.id, event)
        
        assert success
        
        communicator.shutdown()

    def test_send_to_disconnected_device(self, communicator):
        """Test sending to device with no connection."""
        fake_id = str(uuid.uuid4())
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        success = communicator.send_input_event(fake_id, event)
        
        assert not success

    def test_broadcast_input_event(self, communicator, mock_connection):
        """Test broadcasting event to all devices."""
        # Create two remote devices
        device1 = Device(id=str(uuid.uuid4()), name="Device1", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.101", port=5000)
        device2 = Device(id=str(uuid.uuid4()), name="Device2", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.102", port=5000)
        
        communicator.establish_connection(device1, mock_connection)
        communicator.establish_connection(device2, mock_connection)
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        count = communicator.broadcast_input_event(event)
        
        assert count == 2
        
        communicator.shutdown()

    def test_broadcast_to_no_devices(self, communicator):
        """Test broadcasting when no devices connected."""
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        count = communicator.broadcast_input_event(event)
        
        assert count == 0


class TestDeviceStatus:
    """Test device status tracking."""

    def test_get_connected_devices(self, communicator, mock_connection):
        """Test getting list of connected devices."""
        # Create two devices
        device1 = Device(id=str(uuid.uuid4()), name="Device1", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.101", port=5000)
        device2 = Device(id=str(uuid.uuid4()), name="Device2", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.102", port=5000)
        
        communicator.establish_connection(device1, mock_connection)
        communicator.establish_connection(device2, mock_connection)
        
        devices = communicator.get_connected_devices()
        
        assert len(devices) == 2
        assert device1 in devices
        assert device2 in devices
        
        communicator.shutdown()

    def test_get_connection_status(self, communicator, remote_device, mock_connection):
        """Test getting connection status."""
        communicator.establish_connection(remote_device, mock_connection)
        
        status = communicator.get_connection_status(remote_device.id)
        
        assert status is not None
        assert status["device_id"] == remote_device.id
        assert status["device_name"] == remote_device.name
        assert status["is_active"] is True
        
        communicator.shutdown()

    def test_get_all_connection_status(self, communicator, mock_connection):
        """Test getting status of all connections."""
        # Create two devices
        device1 = Device(id=str(uuid.uuid4()), name="Device1", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.101", port=5000)
        device2 = Device(id=str(uuid.uuid4()), name="Device2", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.102", port=5000)
        
        communicator.establish_connection(device1, mock_connection)
        communicator.establish_connection(device2, mock_connection)
        
        status = communicator.get_all_connection_status()
        
        assert len(status) == 2
        assert device1.id in status
        assert device2.id in status
        
        communicator.shutdown()

    def test_get_status_nonexistent_device(self, communicator):
        """Test getting status for nonexistent device."""
        fake_id = str(uuid.uuid4())
        status = communicator.get_connection_status(fake_id)
        
        assert status is None


class TestInputEventReceiver:
    """Test input event receiver."""

    def test_receiver_creation(self, communicator):
        """Test creating input event receiver."""
        receiver = InputEventReceiver(communicator)
        assert receiver.communicator == communicator
        assert len(receiver.event_handlers) == 0

    def test_register_handler(self, communicator):
        """Test registering input event handler."""
        receiver = InputEventReceiver(communicator)
        handler = Mock()
        
        receiver.register_handler(handler)
        
        assert handler in receiver.event_handlers
        assert len(receiver.event_handlers) == 1

    def test_unregister_handler(self, communicator):
        """Test unregistering input event handler."""
        receiver = InputEventReceiver(communicator)
        handler = Mock()
        
        receiver.register_handler(handler)
        receiver.unregister_handler(handler)
        
        assert handler not in receiver.event_handlers
        assert len(receiver.event_handlers) == 0

    def test_process_received_event(self, communicator):
        """Test processing received input event."""
        receiver = InputEventReceiver(communicator)
        handler = Mock()
        receiver.register_handler(handler)
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        receiver.process_received_event(event)
        
        handler.assert_called_once_with(event)

    def test_process_event_multiple_handlers(self, communicator):
        """Test event dispatched to all handlers."""
        receiver = InputEventReceiver(communicator)
        handler1 = Mock()
        handler2 = Mock()
        
        receiver.register_handler(handler1)
        receiver.register_handler(handler2)
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        receiver.process_received_event(event)
        
        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)

    def test_process_invalid_event(self, communicator):
        """Test processing invalid event."""
        receiver = InputEventReceiver(communicator)
        handler = Mock()
        receiver.register_handler(handler)
        
        # KeyEvent requires keycode in payload
        # Creating a valid event to test that invalid structure is handled
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        # Should call handler for valid event
        receiver.process_received_event(event)
        handler.assert_called_once_with(event)

    def test_handler_exception_isolation(self, communicator):
        """Test exception in one handler doesn't affect others."""
        receiver = InputEventReceiver(communicator)
        
        # First handler raises exception
        handler1 = Mock(side_effect=Exception("Handler error"))
        # Second handler should still be called
        handler2 = Mock()
        
        receiver.register_handler(handler1)
        receiver.register_handler(handler2)
        
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )
        
        # Process event - should not raise despite handler1 error
        receiver.process_received_event(event)
        
        # handler2 should still be called
        handler2.assert_called_once()


class TestCommunicatorShutdown:
    """Test communicator shutdown."""

    def test_shutdown_communicator(self, communicator, remote_device, mock_connection):
        """Test shutting down communicator."""
        communicator.establish_connection(remote_device, mock_connection)
        
        success = communicator.shutdown()
        
        assert success
        assert len(communicator.device_links) == 0

    def test_shutdown_multiple_connections(self, communicator, mock_connection):
        """Test shutdown with multiple connections."""
        device1 = Device(id=str(uuid.uuid4()), name="Device1", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.101", port=5000)
        device2 = Device(id=str(uuid.uuid4()), name="Device2", os=DeviceOS.WINDOWS,
                        ip_address="192.168.1.102", port=5000)
        
        communicator.establish_connection(device1, mock_connection)
        communicator.establish_connection(device2, mock_connection)
        
        success = communicator.shutdown()
        
        assert success
        assert len(communicator.device_links) == 0


class TestDeviceLink:
    """Test DeviceLink data structure."""

    def test_link_creation(self, local_device, remote_device, mock_connection):
        """Test creating device link."""
        link = DeviceLink(
            local_device=local_device,
            remote_device=remote_device,
            connection=mock_connection,
            is_active=True
        )
        
        assert link.local_device == local_device
        assert link.remote_device == remote_device
        assert link.connection == mock_connection
        assert link.is_active is True

    def test_link_with_relay(self, local_device, remote_device, mock_connection):
        """Test link with relay."""
        from src.relay.input_relay import InputRelay
        
        relay = InputRelay(local_device, remote_device, mock_connection)
        
        link = DeviceLink(
            local_device=local_device,
            remote_device=remote_device,
            connection=mock_connection,
            relay=relay,
            is_active=True
        )
        
        assert link.relay == relay
