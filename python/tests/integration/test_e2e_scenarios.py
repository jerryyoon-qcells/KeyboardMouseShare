"""End-to-end integration tests for complete application scenarios."""

import pytest
import uuid
from unittest.mock import Mock

from PyQt5.QtWidgets import QApplication

from src.ui.manager import UIConfiguration
from src.ui.widgets.device_list import DeviceListWidget
from src.ui.widgets.connection_status import ConnectionStatusWidget
from src.models.device import Device, DeviceRole, DeviceOS
from src.models.input_event import InputEvent, InputEventType


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for all E2E tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def ui_config():
    """Create UIConfiguration for E2E testing."""
    return UIConfiguration(device_name="TestMasterDevice", role="master")


@pytest.fixture
def device_list_widget(qapp, ui_config):
    """Create DeviceListWidget for testing."""
    return DeviceListWidget(ui_config)


@pytest.fixture
def connection_status_widget(qapp):
    """Create ConnectionStatusWidget for testing."""
    return ConnectionStatusWidget()


class TestDeviceDiscoveryScenario:
    """Test complete device discovery scenario."""

    def test_discover_single_device(self, device_list_widget):
        """Test discovering a single remote device."""
        test_device = Device(
            id=str(uuid.uuid4()),
            name="RemoteDevice",
            os=DeviceOS.MACOS,
            ip_address="192.168.1.100",
            port=5000
        )

        device_list_widget.update_device_list([test_device.to_dict()])
        assert device_list_widget.device_list.count() == 1

    def test_discover_multiple_devices(self, device_list_widget):
        """Test discovering multiple remote devices."""
        devices = [
            Device(id=str(uuid.uuid4()), name=f"Device{i}", os=DeviceOS.WINDOWS,
                   ip_address=f"192.168.1.{100+i}", port=5000)
            for i in range(3)
        ]

        device_list_widget.update_device_list([d.to_dict() for d in devices])
        assert device_list_widget.device_list.count() == 3

    def test_device_list_refresh(self, device_list_widget):
        """Test refreshing device list display."""
        initial_devices = [
            Device(id=str(uuid.uuid4()), name="Device1", os=DeviceOS.WINDOWS,
                   ip_address="192.168.1.100", port=5000)
        ]
        device_list_widget.update_device_list([d.to_dict() for d in initial_devices])
        assert device_list_widget.device_list.count() == 1

        updated_devices = [
            Device(id=str(uuid.uuid4()), name="Device2", os=DeviceOS.MACOS,
                   ip_address="192.168.1.101", port=5000),
            Device(id=str(uuid.uuid4()), name="Device3", os=DeviceOS.WINDOWS,
                   ip_address="192.168.1.102", port=5000),
        ]
        device_list_widget.update_device_list([d.to_dict() for d in updated_devices])
        assert device_list_widget.device_list.count() == 2

    def test_empty_device_list(self, device_list_widget):
        """Test handling empty device list."""
        device_list_widget.update_device_list([])
        assert device_list_widget.device_list.count() == 0


class TestConnectionScenario:
    """Test complete connection scenario."""

    def test_connection_state_transitions(self, connection_status_widget):
        """Test complete connection state machine."""
        # Initial: disconnected
        connection_status_widget.set_disconnected()
        assert connection_status_widget.current_device is None

        # Transition: disconnected → connecting
        connection_status_widget.set_connecting("RemoteDevice")
        assert connection_status_widget.current_device == "RemoteDevice"

        # Transition: connecting → connected
        connection_status_widget.set_connected("RemoteDevice")
        assert connection_status_widget.current_device == "RemoteDevice"

        # Transition: connected → disconnected
        connection_status_widget.set_disconnected()
        assert connection_status_widget.current_device is None

    def test_multiple_connect_disconnect_cycles(self, connection_status_widget):
        """Test multiple connect/disconnect cycles."""
        devices = ["Device1", "Device2", "Device3"]

        for device_name in devices:
            connection_status_widget.set_connecting(device_name)
            connection_status_widget.set_connected(device_name)
            assert connection_status_widget.current_device == device_name

            connection_status_widget.set_disconnected()
            assert connection_status_widget.current_device is None

    def test_reconnect_to_different_device(self, connection_status_widget):
        """Test reconnecting to a different device."""
        connection_status_widget.set_connecting("Device1")
        connection_status_widget.set_connected("Device1")
        assert connection_status_widget.current_device == "Device1"

        connection_status_widget.set_connecting("Device2")
        connection_status_widget.set_connected("Device2")
        assert connection_status_widget.current_device == "Device2"


class TestInputMetricsScenario:
    """Test complete input event metric tracking scenario."""

    def test_track_single_input_event(self, connection_status_widget):
        """Test tracking a single input event."""
        connection_status_widget.set_connected("RemoteDevice")

        key_event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )

        connection_status_widget.update_input_event(InputEventType.KEY_PRESS, {"keycode": "A"})

    def test_track_mixed_input_events(self, connection_status_widget):
        """Test tracking mixed keyboard and mouse input."""
        connection_status_widget.set_connected("RemoteDevice")

        events = [
            (InputEventType.KEY_PRESS, {"keycode": "ctrl"}),
            (InputEventType.MOUSE_MOVE, {"x": 150, "y": 250}),
            (InputEventType.MOUSE_CLICK, {"button": "left"}),
        ]

        for event_type, event_data in events:
            connection_status_widget.update_input_event(event_type, event_data)

    def test_metrics_reset_on_disconnect(self, connection_status_widget):
        """Test metrics are reset when disconnecting."""
        connection_status_widget.set_connected("RemoteDevice")
        for i in range(5):
            connection_status_widget.update_input_event(InputEventType.KEY_PRESS, {"keycode": "A"})

        connection_status_widget.set_disconnected()
        assert connection_status_widget.current_device is None


class TestSettingsPersistenceScenario:
    """Test configuration settings persistence scenario."""

    def test_device_name_configuration(self, ui_config):
        """Test device name configuration."""
        assert ui_config.device_name == "TestMasterDevice"

        ui_config.device_name = "UpdatedDevice"
        assert ui_config.device_name == "UpdatedDevice"

    def test_role_configuration(self, ui_config):
        """Test role configuration."""
        assert ui_config.role == "master"

        ui_config.role = "client"
        assert ui_config.role == "client"

        ui_config.role = "master"
        assert ui_config.role == "master"

    def test_auto_connect_setting(self, ui_config):
        """Test auto-connect configuration."""
        assert ui_config.auto_connect is False

        ui_config.auto_connect = True
        assert ui_config.auto_connect is True

        ui_config.auto_connect = False
        assert ui_config.auto_connect is False

    def test_input_capture_settings(self, ui_config):
        """Test input capture preferences."""
        assert ui_config.keyboard_enabled is True
        assert ui_config.mouse_enabled is True

        ui_config.keyboard_enabled = False
        assert ui_config.keyboard_enabled is False
        assert ui_config.mouse_enabled is True

        ui_config.mouse_enabled = False
        assert ui_config.keyboard_enabled is False
        assert ui_config.mouse_enabled is False

        ui_config.keyboard_enabled = True
        ui_config.mouse_enabled = True
        assert ui_config.keyboard_enabled is True
        assert ui_config.mouse_enabled is True

    def test_configuration_validation(self):
        """Test configuration validation."""
        config = UIConfiguration(device_name="TestDevice", role="master")
        assert config.device_name == "TestDevice"
        assert config.role == "master"

        with pytest.raises(ValueError):
            UIConfiguration(device_name="TestDevice", role="invalid")

        with pytest.raises(ValueError):
            UIConfiguration(device_name="", role="master")


class TestMultiDeviceScenario:
    """Test multi-device connection scenarios."""

    def test_sequential_device_connections(self, connection_status_widget, device_list_widget):
        """Test connecting to devices sequentially."""
        devices = [
            Device(id=str(uuid.uuid4()), name="Laptop", os=DeviceOS.WINDOWS,
                   ip_address="192.168.1.100", port=5000),
            Device(id=str(uuid.uuid4()), name="Phone", os=DeviceOS.WINDOWS,
                   ip_address="192.168.1.101", port=5000),
            Device(id=str(uuid.uuid4()), name="Tablet", os=DeviceOS.MACOS,
                   ip_address="192.168.1.102", port=5000),
        ]
        device_list_widget.update_device_list([d.to_dict() for d in devices])
        assert device_list_widget.device_list.count() == 3

        for device in devices:
            connection_status_widget.set_connecting(device.name)
            connection_status_widget.set_connected(device.name)
            assert connection_status_widget.current_device == device.name

            connection_status_widget.set_disconnected()

    def test_device_list_updates_during_connection(self, device_list_widget, connection_status_widget):
        """Test device list updates while connected."""
        initial_devices = [
            Device(id=str(uuid.uuid4()), name="Device1", os=DeviceOS.WINDOWS,
                   ip_address="192.168.1.100", port=5000),
            Device(id=str(uuid.uuid4()), name="Device2", os=DeviceOS.WINDOWS,
                   ip_address="192.168.1.101", port=5000),
        ]
        device_list_widget.update_device_list([d.to_dict() for d in initial_devices])

        connection_status_widget.set_connecting("Device1")

        updated_devices = initial_devices + [
            Device(id=str(uuid.uuid4()), name="Device3", os=DeviceOS.MACOS,
                   ip_address="192.168.1.102", port=5000),
        ]
        device_list_widget.update_device_list([d.to_dict() for d in updated_devices])
        assert device_list_widget.device_list.count() == 3

        assert connection_status_widget.current_device == "Device1"


class TestErrorHandlingScenario:
    """Test error handling throughout application."""

    def test_disconnect_when_not_connected(self, connection_status_widget):
        """Test disconnect when not connected."""
        connection_status_widget.set_disconnected()
        assert connection_status_widget.current_device is None

        connection_status_widget.set_disconnected()
        assert connection_status_widget.current_device is None

    def test_invalid_configuration_values(self):
        """Test handling invalid configuration values."""
        config = UIConfiguration(device_name="TestDevice", role="master")

        config.role = "client"
        assert config.role == "client"

        with pytest.raises(ValueError):
            config.role = "invalid"

    def test_empty_device_list_handling(self, device_list_widget):
        """Test handling empty device list."""
        device_list_widget.update_device_list([])
        assert device_list_widget.device_list.count() == 0

        devices = [
            Device(id=str(uuid.uuid4()), name="Device1", os=DeviceOS.WINDOWS,
                   ip_address="192.168.1.100", port=5000)
        ]
        device_list_widget.update_device_list([d.to_dict() for d in devices])
        assert device_list_widget.device_list.count() == 1


class TestPerformanceScenario:
    """Test performance under various loads."""

    def test_handle_many_devices_in_list(self, device_list_widget):
        """Test handling large number of devices."""
        devices = [
            Device(id=str(uuid.uuid4()), name=f"Device{i}", os=DeviceOS.WINDOWS,
                   ip_address=f"192.168.1.{i % 256}", port=5000)
            for i in range(50)
        ]

        device_list_widget.update_device_list([d.to_dict() for d in devices])
        assert device_list_widget.device_list.count() == 50

    def test_handle_high_frequency_input_events(self, connection_status_widget):
        """Test handling many input events rapidly."""
        connection_status_widget.set_connecting("RemoteDevice")

        for i in range(100):
            if i % 2 == 0:
                connection_status_widget.update_input_event(
                    InputEventType.KEY_PRESS,
                    {"keycode": "A"}
                )
            else:
                connection_status_widget.update_input_event(
                    InputEventType.MOUSE_MOVE,
                    {"x": 100, "y": 200}
                )

    def test_rapid_connect_disconnect_cycles(self, connection_status_widget):
        """Test rapid connect/disconnect cycles."""
        for i in range(10):
            device_name = f"Device{i}"
            connection_status_widget.set_connecting(device_name)
            connection_status_widget.set_connected(device_name)
            connection_status_widget.set_disconnected()

    def test_device_list_updates_with_many_devices(self, device_list_widget):
        """Test updating device list with many devices multiple times."""
        for update_num in range(5):
            devices = [
                Device(id=str(uuid.uuid4()), name=f"Device{i}", os=DeviceOS.WINDOWS,
                       ip_address=f"192.168.1.{i % 256}", port=5000)
                for i in range(20)
            ]
            device_list_widget.update_device_list([d.to_dict() for d in devices])
            assert device_list_widget.device_list.count() == 20


class TestApplicationStateManagement:
    """Test application state management across components."""

    def test_device_selection_persistence(self, device_list_widget, connection_status_widget):
        """Test device selection persists across operations."""
        devices = [
            Device(id=str(uuid.uuid4()), name="Device1", os=DeviceOS.WINDOWS,
                   ip_address="192.168.1.100", port=5000),
            Device(id=str(uuid.uuid4()), name="Device2", os=DeviceOS.WINDOWS,
                   ip_address="192.168.1.101", port=5000),
        ]
        device_list_widget.update_device_list([d.to_dict() for d in devices])

        connection_status_widget.set_connecting("Device1")
        assert connection_status_widget.current_device == "Device1"

        updated_devices = devices + [
            Device(id=str(uuid.uuid4()), name="Device3", os=DeviceOS.WINDOWS,
                   ip_address="192.168.1.102", port=5000),
        ]
        device_list_widget.update_device_list(updated_devices)

        assert connection_status_widget.current_device == "Device1"

    def test_configuration_isolation(self, ui_config):
        """Test configuration changes are isolated."""
        config1 = UIConfiguration(device_name="Device1", role="master")
        config2 = UIConfiguration(device_name="Device2", role="client")

        config1.auto_connect = True
        config1.keyboard_enabled = False

        assert config2.auto_connect is False
        assert config2.keyboard_enabled is True

    def test_connection_state_after_multiple_operations(self, connection_status_widget):
        """Test connection state is correct after multiple operations."""
        connection_status_widget.set_connecting("Device1")

        for i in range(10):
            connection_status_widget.update_input_event(
                InputEventType.KEY_PRESS,
                {"keycode": "A"}
            )

        assert connection_status_widget.current_device == "Device1"

        connection_status_widget.set_disconnected()
        assert connection_status_widget.current_device is None


class TestDeviceModelIntegration:
    """Test Device model integration with UI."""

    def test_device_creation_with_all_fields(self):
        """Test creating device with all required fields."""
        device = Device(
            id=str(uuid.uuid4()),
            name="TestDevice",
            os=DeviceOS.WINDOWS,
            ip_address="192.168.1.100",
            port=5000,
            role=DeviceRole.MASTER
        )

        assert device.name == "TestDevice"
        assert device.os == DeviceOS.WINDOWS
        assert device.ip_address == "192.168.1.100"
        assert device.port == 5000

    def test_device_json_serialization(self):
        """Test device can be serialized to JSON."""
        device = Device(
            id=str(uuid.uuid4()),
            name="TestDevice",
            os=DeviceOS.WINDOWS,
            ip_address="192.168.1.100",
            port=5000
        )

        device_dict = device.to_dict()
        assert device_dict["name"] == "TestDevice"
        assert device_dict["ip_address"] == "192.168.1.100"


class TestInputEventIntegration:
    """Test InputEvent model integration with UI."""

    def test_input_event_creation_keyboard(self):
        """Test creating keyboard input event."""
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.KEY_PRESS,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"keycode": "A"}
        )

        assert event.event_type == InputEventType.KEY_PRESS
        assert event.payload["keycode"] == "A"

    def test_input_event_creation_mouse(self):
        """Test creating mouse input event."""
        event = InputEvent(
            id=str(uuid.uuid4()),
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=str(uuid.uuid4()),
            target_device_id=str(uuid.uuid4()),
            payload={"x": 100, "y": 200}
        )

        assert event.event_type == InputEventType.MOUSE_MOVE
        assert event.payload["x"] == 100
        assert event.payload["y"] == 200

    def test_all_input_event_types(self):
        """Test creating all valid input event types."""
        event_configs = [
            (InputEventType.KEY_PRESS, {"keycode": "A"}),
            (InputEventType.KEY_RELEASE, {"keycode": "A"}),
            (InputEventType.MOUSE_MOVE, {"x": 100, "y": 200}),
            (InputEventType.MOUSE_CLICK, {"button": "left"}),
            (InputEventType.MOUSE_SCROLL, {"scroll_delta": 3}),
        ]

        for event_type, payload_dict in event_configs:
            event = InputEvent(
                id=str(uuid.uuid4()),
                event_type=event_type,
                source_device_id=str(uuid.uuid4()),
                target_device_id=str(uuid.uuid4()),
                payload=payload_dict
            )
            assert event.event_type == event_type
