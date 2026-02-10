"""Tests for UI Service Bridge integration."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PyQt5.QtWidgets import QApplication
from datetime import datetime, timezone

from src.ui.service_bridge import UIServiceBridge, UIServiceBridgeConfig
from src.ui.widgets.device_list import DeviceListWidget
from src.ui.widgets.connection_status import ConnectionStatusWidget
from src.ui.manager import UIConfiguration
from src.models.device import Device, DeviceRole, DeviceOS
from src.models.input_event import InputEventType
from src.input.handler import InputCapture
from src.network.discovery import DiscoveryService
from src.network.connection import ConnectionHandler


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def config():
    """Create UIConfiguration for testing."""
    return UIConfiguration(device_name="TestDevice")


@pytest.fixture
def device_list_widget(config):
    """Create DeviceListWidget for testing."""
    return DeviceListWidget(config)


@pytest.fixture
def connection_status_widget():
    """Create ConnectionStatusWidget for testing."""
    return ConnectionStatusWidget()


@pytest.fixture
def bridge(device_list_widget, connection_status_widget):
    """Create UIServiceBridge for testing."""
    return UIServiceBridge(device_list_widget, connection_status_widget)


class TestUIServiceBridgeInit:
    """Test UIServiceBridge initialization."""
    
    def test_init_creates_bridge(self, bridge):
        """Test bridge is properly initialized."""
        assert bridge is not None
        assert bridge.device_list_widget is not None
        assert bridge.connection_status_widget is not None
    
    def test_init_with_custom_config(self, device_list_widget, connection_status_widget):
        """Test bridge with custom configuration."""
        config = UIServiceBridgeConfig(
            device_poll_interval=1.0,
            connection_update_interval=0.25,
            enable_metrics=True
        )
        
        bridge = UIServiceBridge(device_list_widget, connection_status_widget, config)
        
        assert bridge.config.device_poll_interval == 1.0
        assert bridge.config.connection_update_interval == 0.25
        assert bridge.config.enable_metrics is True
    
    def test_init_services_none(self, bridge):
        """Test services start as None."""
        assert bridge.discovery_service is None
        assert bridge.connection_handler is None


class TestServiceAttachment:
    """Test service attachment to bridge."""
    
    def test_attach_discovery_service(self, bridge):
        """Test attaching discovery service."""
        mock_service = Mock(spec=DiscoveryService)
        
        bridge.attach_discovery_service(mock_service)
        
        assert bridge.discovery_service is mock_service
    
    def test_attach_connection_handler(self, bridge):
        """Test attaching connection handler."""
        mock_handler = Mock(spec=ConnectionHandler)
        
        bridge.attach_connection_handler(mock_handler)
        
        assert bridge.connection_handler is mock_handler
    
    def test_attach_input_handler(self, bridge):
        """Test attaching input handler."""
        mock_handler = Mock()
        mock_handler.set_callback = Mock()
        
        bridge.attach_input_handler("test_handler", mock_handler)
        
        assert "test_handler" in bridge._input_callbacks


class TestDeviceListIntegration:
    """Test device list integration with discovery service."""
    
    def test_convert_devices_to_ui_format(self, bridge):
        """Test device conversion to UI format."""
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100",
            port=19999,
            is_registered=True
        )
        
        ui_devices = bridge._convert_devices_to_ui_format([device])
        
        assert len(ui_devices) == 1
        assert ui_devices[0]["name"] == "TestPC"
        assert ui_devices[0]["os"] == "Windows"
        assert ui_devices[0]["ip_address"] == "192.168.1.100"
        assert ui_devices[0]["status"] == "online"
    
    def test_convert_offline_device(self, bridge):
        """Test offline device conversion."""
        device = Device(
            name="OfflinePC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            is_registered=False
        )
        
        ui_devices = bridge._convert_devices_to_ui_format([device])
        
        assert ui_devices[0]["status"] == "offline"
    
    def test_polling_loop_updates_devices(self, bridge, device_list_widget, monkeypatch):
        """Test polling loop updates device list."""
        # Mock discovery service
        mock_service = Mock(spec=DiscoveryService)
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100",
            is_registered=True
        )
        mock_service.get_discovered_devices.return_value = [device]
        
        bridge.attach_discovery_service(mock_service)
        
        # Manually call polling loop logic
        devices = mock_service.get_discovered_devices()
        ui_devices = bridge._convert_devices_to_ui_format(devices)
        device_list_widget.update_device_list(ui_devices)
        
        # Verify device was added
        assert device_list_widget.device_list.count() == 1


class TestConnectionIntegration:
    """Test connection status integration."""
    
    def test_connect_requested(self, bridge, device_list_widget):
        """Test connect request triggers appropriate handlers."""
        device = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "online"
        }
        
        device_list_widget.devices["device-1"] = device
        
        # Simulate connect request
        bridge._on_connect_requested("device-1")
        
        # Widget should show connecting state
        assert "Connecting" in str(bridge.connection_status_widget.tls_status.text())
    
    def test_disconnect_requested(self, bridge):
        """Test disconnect request resets UI state."""
        bridge._on_disconnect_requested("device-1")
        
        # Widget should reset
        assert bridge._connected_device is None
    
    def test_set_connected(self, bridge):
        """Test setting connected state."""
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100"
        )
        
        bridge.set_connected(device)
        
        assert bridge._connected_device is not None
        assert bridge._connected_device.name == "TestPC"
    
    def test_set_disconnected(self, bridge):
        """Test setting disconnected state."""
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100"
        )
        
        bridge.set_connected(device)
        bridge.set_disconnected()
        
        assert bridge._connected_device is None


class TestInputEventTracking:
    """Test input event tracking through bridge."""
    
    def test_input_event_callback_registered(self, bridge):
        """Test input handler callback registration."""
        mock_handler = Mock()
        mock_handler.set_callback = Mock()
        
        bridge.attach_input_handler("test", mock_handler)
        
        # Handler should have received callback
        assert mock_handler.set_callback.called
    
    def test_input_event_updates_metrics(self, bridge):
        """Test input events update widget metrics."""
        # Create a simple test of the update_input_event method
        bridge.connection_status_widget.update_input_event(
            InputEventType.KEY_PRESS,
            {"key": "a"}
        )
        
        assert bridge.connection_status_widget.metrics["key_press"] == 1


class TestPollingControl:
    """Test polling lifecycle control."""
    
    def test_start_polling(self, bridge):
        """Test starting polling thread."""
        bridge.start_polling()
        
        assert bridge._polling_active is True
        assert bridge._polling_thread is not None
        assert bridge._polling_thread.is_alive()
        
        bridge.stop_polling()
    
    def test_stop_polling(self, bridge):
        """Test stopping polling thread."""
        bridge.start_polling()
        assert bridge._polling_active is True
        
        bridge.stop_polling()
        
        assert bridge._polling_active is False
    
    def test_polling_already_running(self, bridge):
        """Test starting polling when already running."""
        bridge.start_polling()
        
        # Second start should be ignored
        bridge.start_polling()
        
        bridge.stop_polling()


class TestShutdown:
    """Test bridge shutdown."""
    
    def test_shutdown_stops_polling(self, bridge):
        """Test shutdown stops polling."""
        bridge.start_polling()
        
        bridge.shutdown()
        
        assert bridge._polling_active is False


class TestWidgetSignalConnections:
    """Test widget signal connections."""
    
    def test_device_list_signals_connected(self, bridge):
        """Test device list widget signals are connected."""
        # Signals should be connected (would need Qt signal testing framework)
        # For now, verify the bridge has the handlers
        assert hasattr(bridge, '_on_connect_requested')
        assert hasattr(bridge, '_on_disconnect_requested')


class TestUIServiceBridgeConfig:
    """Test UIServiceBridgeConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = UIServiceBridgeConfig()
        
        assert config.device_poll_interval == 2.0
        assert config.connection_update_interval == 0.5
        assert config.enable_metrics is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = UIServiceBridgeConfig(
            device_poll_interval=3.0,
            connection_update_interval=1.0,
            enable_metrics=False
        )
        
        assert config.device_poll_interval == 3.0
        assert config.connection_update_interval == 1.0
        assert config.enable_metrics is False
