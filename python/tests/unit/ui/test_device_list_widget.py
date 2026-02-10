"""Tests for Device List Widget."""

import pytest
from PyQt5.QtWidgets import QApplication, QListWidgetItem
from PyQt5.QtCore import Qt

from src.ui.widgets.device_list import DeviceListWidget
from src.ui.manager import UIConfiguration
from src.models.device import DeviceRole, DeviceOS


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def config(tmp_path):
    """Create UIConfiguration for testing."""
    return UIConfiguration(device_name="TestDevice")


@pytest.fixture
def widget(config):
    """Create DeviceListWidget for testing."""
    return DeviceListWidget(config)


class TestDeviceListWidgetInit:
    """Test DeviceListWidget initialization."""
    
    def test_init_creates_widget(self, widget):
        """Test widget is properly initialized."""
        assert widget is not None
        assert widget.device_list is not None
        assert widget.status_label is not None
    
    def test_init_buttons_disabled(self, widget):
        """Test that action buttons are disabled on init."""
        assert not widget.connect_btn.isEnabled()
        assert not widget.disconnect_btn.isEnabled()
    
    def test_init_empty_devices(self, widget):
        """Test that devices dict is empty on init."""
        assert len(widget.devices) == 0
        assert widget.device_list.count() == 0


class TestDeviceListWidgetLayout:
    """Test DeviceListWidget UI layout."""
    
    def test_has_title_label(self, widget):
        """Test widget has title label."""
        layout = widget.layout()
        assert layout is not None
        # Title should be in layout
    
    def test_has_device_list(self, widget):
        """Test widget has device list."""
        assert widget.device_list is not None
    
    def test_has_action_buttons(self, widget):
        """Test widget has action buttons."""
        assert widget.connect_btn is not None
        assert widget.disconnect_btn is not None
    
    def test_has_status_label(self, widget):
        """Test widget has status label."""
        assert widget.status_label is not None


class TestDeviceListUpdate:
    """Test device list updating."""
    
    def test_update_empty_list(self, widget):
        """Test updating with empty device list."""
        widget.update_device_list([])
        assert widget.device_list.count() == 0
        assert len(widget.devices) == 0
    
    def test_update_single_device(self, widget):
        """Test updating with single device."""
        device = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "online"
        }
        
        widget.update_device_list([device])
        
        assert widget.device_list.count() == 1
        assert len(widget.devices) == 1
        assert "device-1" in widget.devices
    
    def test_update_multiple_devices(self, widget):
        """Test updating with multiple devices."""
        devices = [
            {
                "id": "device-1",
                "name": "PC1",
                "os": "Windows",
                "ip_address": "192.168.1.100",
                "status": "online"
            },
            {
                "id": "device-2",
                "name": "PC2",
                "os": "macOS",
                "ip_address": "192.168.1.101",
                "status": "offline"
            },
            {
                "id": "device-3",
                "name": "Linux",
                "os": "Linux",
                "ip_address": "192.168.1.102",
                "status": "online"
            }
        ]
        
        widget.update_device_list(devices)
        
        assert widget.device_list.count() == 3
        assert len(widget.devices) == 3
        
        for device in devices:
            assert device["id"] in widget.devices
    
    def test_update_clears_previous(self, widget):
        """Test that update clears previous devices."""
        old_devices = [
            {"id": "d1", "name": "D1", "os": "W", "ip_address": "1.1.1.1", "status": "online"},
            {"id": "d2", "name": "D2", "os": "W", "ip_address": "1.1.1.2", "status": "online"}
        ]
        
        widget.update_device_list(old_devices)
        assert widget.device_list.count() == 2
        
        new_devices = [
            {"id": "d3", "name": "D3", "os": "W", "ip_address": "1.1.1.3", "status": "online"}
        ]
        
        widget.update_device_list(new_devices)
        assert widget.device_list.count() == 1
        assert len(widget.devices) == 1


class TestDeviceListSelection:
    """Test device selection behavior."""
    
    def test_device_selection_signal(self, widget, qtbot):
        """Test device selection emits signal."""
        device = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "online"
        }
        
        widget.update_device_list([device])
        
        with qtbot.waitSignal(widget.device_selected, timeout=1000):
            widget.device_list.setCurrentRow(0)
    
    def test_connect_enabled_for_online(self, widget):
        """Test connect button enabled for online device."""
        device = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "online"
        }
        
        widget.update_device_list([device])
        widget.device_list.setCurrentRow(0)
        
        assert widget.connect_btn.isEnabled()
    
    def test_connect_disabled_for_offline(self, widget):
        """Test connect button disabled for offline device."""
        device = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "offline"
        }
        
        widget.update_device_list([device])
        widget.device_list.setCurrentRow(0)
        
        assert not widget.connect_btn.isEnabled()
    
    def test_disconnect_button_status(self, widget):
        """Test disconnect button only enabled for connected devices."""
        device = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "connected"
        }
        
        widget.update_device_list([device])
        widget.device_list.setCurrentRow(0)
        
        assert widget.disconnect_btn.isEnabled()


class TestDeviceListActions:
    """Test device action handling."""
    
    def test_connect_button_clicked(self, widget, qtbot):
        """Test connect button emits signal."""
        device = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "online"
        }
        
        widget.update_device_list([device])
        widget.device_list.setCurrentRow(0)
        
        with qtbot.waitSignal(widget.connect_requested, timeout=1000):
            widget.connect_btn.click()
    
    def test_disconnect_button_clicked(self, widget, qtbot):
        """Test disconnect button emits signal."""
        device = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "connected"
        }
        
        widget.update_device_list([device])
        widget.device_list.setCurrentRow(0)
        
        with qtbot.waitSignal(widget.disconnect_requested, timeout=1000):
            widget.disconnect_btn.click()
    
    def test_no_action_without_selection(self, widget):
        """Test buttons disabled without device selection."""
        assert not widget.connect_btn.isEnabled()
        assert not widget.disconnect_btn.isEnabled()


class TestDeviceListStatusLabel:
    """Test status label updates."""
    
    def test_status_updates_on_refresh(self, widget):
        """Test status label updates when refreshing."""
        widget.refresh_devices()
        # Status should show device count
        assert "device" in widget.status_label.text().lower()
    
    def test_status_shows_device_count(self, widget):
        """Test status label shows device count."""
        devices = [
            {"id": f"d{i}", "name": f"D{i}", "os": "W", "ip_address": f"1.1.1.{i}", "status": "online"}
            for i in range(5)
        ]
        
        widget.update_device_list(devices)
        assert "5" in widget.status_label.text()


class TestDeviceListDisplay:
    """Test device display formatting."""
    
    def test_device_display_includes_name(self, widget):
        """Test displayed device text includes device name."""
        device = {
            "id": "device-1",
            "name": "MyPC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "online"
        }
        
        widget.update_device_list([device])
        item_text = widget.device_list.item(0).text()
        
        assert "MyPC" in item_text
    
    def test_device_display_includes_os(self, widget):
        """Test displayed device text includes OS."""
        device = {
            "id": "device-1",
            "name": "MyPC",
            "os": "macOS",
            "ip_address": "192.168.1.100",
            "status": "online"
        }
        
        widget.update_device_list([device])
        item_text = widget.device_list.item(0).text()
        
        assert "macOS" in item_text
    
    def test_device_display_includes_ip(self, widget):
        """Test displayed device text includes IP address."""
        device = {
            "id": "device-1",
            "name": "MyPC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "online"
        }
        
        widget.update_device_list([device])
        item_text = widget.device_list.item(0).text()
        
        assert "192.168.1.100" in item_text
    
    def test_online_device_shows_green_indicator(self, widget):
        """Test online devices show green indicator."""
        device = {
            "id": "device-1",
            "name": "MyPC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "online"
        }
        
        widget.update_device_list([device])
        item_text = widget.device_list.item(0).text()
        
        assert "🟢" in item_text
    
    def test_offline_device_shows_red_indicator(self, widget):
        """Test offline devices show red indicator."""
        device = {
            "id": "device-1",
            "name": "MyPC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "offline"
        }
        
        widget.update_device_list([device])
        item_text = widget.device_list.item(0).text()
        
        assert "🔴" in item_text


class TestDeviceListDataStorage:
    """Test device data storage."""
    
    def test_device_data_stored_correctly(self, widget):
        """Test device data is stored correctly in dict."""
        device = {
            "id": "device-1",
            "name": "MyPC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "online",
            "last_seen": "2024-02-09T10:30:00"
        }
        
        widget.update_device_list([device])
        
        stored_device = widget.devices["device-1"]
        assert stored_device["name"] == "MyPC"
        assert stored_device["os"] == "Windows"
        assert stored_device["ip_address"] == "192.168.1.100"
    
    def test_device_id_in_list_item(self, widget):
        """Test device ID is stored in list item."""
        device = {
            "id": "device-123",
            "name": "MyPC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "online"
        }
        
        widget.update_device_list([device])
        
        item = widget.device_list.item(0)
        device_id = item.data(Qt.UserRole)
        assert device_id == "device-123"
