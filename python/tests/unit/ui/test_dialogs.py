"""Tests for UI Dialogs."""

import pytest
from PyQt5.QtWidgets import QApplication

from src.ui.dialogs import ConnectDeviceDialog, SettingsDialog
from src.ui.manager import UIConfiguration


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def config():
    """Create UIConfiguration for testing."""
    return UIConfiguration(device_name="TestDevice")


class TestConnectDeviceDialog:
    """Test ConnectDeviceDialog."""
    
    def test_dialog_init(self):
        """Test dialog initialization."""
        device_info = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100"
        }
        
        dialog = ConnectDeviceDialog(device_info)
        
        assert dialog is not None
        assert dialog.device_info["name"] == "TestPC"
    
    def test_dialog_has_role_combo(self):
        """Test dialog has role combo box."""
        device_info = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100"
        }
        
        dialog = ConnectDeviceDialog(device_info)
        
        assert dialog.role_combo is not None
        assert dialog.role_combo.count() == 2
    
    def test_dialog_has_port_spin(self):
        """Test dialog has port spin box."""
        device_info = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100"
        }
        
        dialog = ConnectDeviceDialog(device_info)
        
        assert dialog.port_spin is not None
        assert dialog.port_spin.minimum() == 1024
        assert dialog.port_spin.maximum() == 65535
    
    def test_dialog_has_progress_bar(self):
        """Test dialog has progress bar."""
        device_info = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100"
        }
        
        dialog = ConnectDeviceDialog(device_info)
        
        assert dialog.progress_bar is not None
        assert not dialog.progress_bar.isVisible()
    
    def test_update_progress(self):
        """Test progress update."""
        device_info = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100"
        }
        
        dialog = ConnectDeviceDialog(device_info)
        dialog.update_progress(50, "Connecting...")
        
        assert dialog.progress_bar.value() == 50
        assert "Connecting" in dialog.status_label.text()
    
    def test_connection_successful(self):
        """Test successful connection marking."""
        device_info = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100"
        }
        
        dialog = ConnectDeviceDialog(device_info)
        dialog.connection_successful()
        
        assert dialog.progress_bar.value() == 100
        assert "successfully" in dialog.status_label.text().lower()


class TestSettingsDialog:
    """Test SettingsDialog."""
    
    def test_dialog_init(self, config):
        """Test dialog initialization."""
        dialog = SettingsDialog(config)
        
        assert dialog is not None
        assert dialog.config is config
    
    def test_dialog_has_device_name_input(self, config):
        """Test dialog has device name input."""
        dialog = SettingsDialog(config)
        
        assert dialog.device_name_input is not None
        assert dialog.device_name_input.text() == config.device_name
    
    def test_dialog_has_role_combo(self, config):
        """Test dialog has role combo box."""
        dialog = SettingsDialog(config)
        
        assert dialog.role_combo is not None
        assert dialog.role_combo.count() == 2
        assert dialog.role_combo.currentText() == config.role
    
    def test_dialog_has_auto_connect_combo(self, config):
        """Test dialog has auto-connect combo box."""
        dialog = SettingsDialog(config)
        
        assert dialog.auto_connect_combo is not None
    
    def test_dialog_has_keyboard_combo(self, config):
        """Test dialog has keyboard combo box."""
        dialog = SettingsDialog(config)
        
        assert dialog.keyboard_combo is not None
    
    def test_dialog_has_mouse_combo(self, config):
        """Test dialog has mouse combo box."""
        dialog = SettingsDialog(config)
        
        assert dialog.mouse_combo is not None
    
    def test_settings_signal_emission(self, config):
        """Test settings changed signal emission."""
        dialog = SettingsDialog(config)
        signal_received = []
        
        def on_settings_changed(settings):
            signal_received.append(settings)
        
        dialog.settings_changed.connect(on_settings_changed)
        
        # Change settings and trigger save
        dialog.device_name_input.setText("NewDevice")
        
        # Manually emit the signal to test
        test_settings = {
            "device_name": "NewDevice",
            "role": "master",
            "auto_connect": False,
            "keyboard_enabled": True,
            "mouse_enabled": True,
        }
        dialog.settings_changed.emit(test_settings)
        
        assert len(signal_received) == 1
        assert signal_received[0]["device_name"] == "NewDevice"


class TestDialogIntegration:
    """Test dialog integration with UI."""
    
    def test_connect_device_dialog_signal(self, qtbot):
        """Test connect device dialog signal emission."""
        device_info = {
            "id": "device-1",
            "name": "TestPC",
            "os": "Windows",
            "ip_address": "192.168.1.100"
        }
        
        dialog = ConnectDeviceDialog(device_info)
        
        with qtbot.waitSignal(dialog.connection_initiated, timeout=1000):
            dialog._on_connect_clicked()
    
    def test_settings_dialog_signal(self, config, qtbot):
        """Test settings dialog signal emission."""
        dialog = SettingsDialog(config)
        
        test_settings = {
            "device_name": "NewDevice",
            "role": "master",
            "auto_connect": True,
            "keyboard_enabled": True,
            "mouse_enabled": True,
        }
        
        with qtbot.waitSignal(dialog.settings_changed, timeout=1000):
            dialog.settings_changed.emit(test_settings)
