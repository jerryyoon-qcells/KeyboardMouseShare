"""Connection and Device Dialogs."""

import logging
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QComboBox, QGroupBox, QFormLayout,
    QMessageBox, QProgressBar, QSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal

from src.models.device import DeviceRole


logger = logging.getLogger(__name__)


class ConnectDeviceDialog(QDialog):
    """Dialog for initiating connection to a device."""
    
    connection_initiated = pyqtSignal(str)  # Emits device ID
    
    def __init__(self, device_info: dict, parent=None):
        """
        Initialize connection dialog.
        
        Args:
            device_info: Dict with device details (id, name, ip, os)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.device_info = device_info
        self.setWindowTitle(f"Connect to {device_info.get('name', 'Device')}")
        self.setGeometry(400, 300, 500, 300)
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup dialog layout."""
        layout = QVBoxLayout(self)
        
        # Device info section
        info_group = QGroupBox("Device Information")
        info_layout = QFormLayout(info_group)
        
        device_name = self.device_info.get("name", "Unknown")
        device_os = self.device_info.get("os", "Unknown")
        device_ip = self.device_info.get("ip_address", "Unknown")
        
        info_layout.addRow("Device:", QLabel(device_name))
        info_layout.addRow("OS:", QLabel(device_os))
        info_layout.addRow("IP Address:", QLabel(device_ip))
        
        layout.addWidget(info_group)
        
        # Connection settings section
        settings_group = QGroupBox("Connection Settings")
        settings_layout = QFormLayout(settings_group)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems([DeviceRole.MASTER.value, DeviceRole.CLIENT.value])
        settings_layout.addRow("This Device Role:", self.role_combo)
        
        self.port_spin = QSpinBox()
        self.port_spin.setMinimum(1024)
        self.port_spin.setMaximum(65535)
        self.port_spin.setValue(19999)
        settings_layout.addRow("Port:", self.port_spin)
        
        layout.addWidget(settings_group)
        
        # Progress section (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to connect")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        button_layout.addWidget(self.connect_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _on_connect_clicked(self) -> None:
        """Handle connect button click."""
        try:
            device_id = self.device_info.get("id")
            if not device_id:
                QMessageBox.critical(self, "Error", "Device ID not found")
                return
            
            self.connect_btn.setEnabled(False)
            self.status_label.setText("Connecting...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            self.connection_initiated.emit(device_id)
            
            logger.info(f"Connection initiated to device: {device_id}")
        
        except Exception as e:
            logger.error(f"Error initiating connection: {e}")
            QMessageBox.critical(self, "Error", f"Connection failed: {e}")
            self.connect_btn.setEnabled(True)
    
    def update_progress(self, value: int, status: str) -> None:
        """
        Update connection progress.
        
        Args:
            value: Progress value (0-100)
            status: Status message
        """
        self.progress_bar.setValue(value)
        self.status_label.setText(status)
    
    def connection_successful(self) -> None:
        """Mark connection as successful."""
        self.status_label.setText("Connected successfully!")
        self.progress_bar.setValue(100)
        self.accept()
    
    def connection_failed(self, error: str) -> None:
        """
        Mark connection as failed.
        
        Args:
            error: Error message
        """
        self.status_label.setText(f"Connection failed: {error}")
        self.connect_btn.setEnabled(True)
        QMessageBox.critical(self, "Connection Failed", error)


class SettingsDialog(QDialog):
    """Dialog for application settings."""
    
    settings_changed = pyqtSignal(dict)  # Emits settings dict
    
    def __init__(self, config, parent=None):
        """
        Initialize settings dialog.
        
        Args:
            config: UIConfiguration instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.config = config
        self.setWindowTitle("Settings")
        self.setGeometry(400, 300, 500, 400)
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup dialog layout."""
        layout = QVBoxLayout(self)
        
        # Device settings
        device_group = QGroupBox("Device Settings")
        device_layout = QFormLayout(device_group)
        
        self.device_name_input = QLineEdit()
        self.device_name_input.setText(self.config.device_name)
        device_layout.addRow("Device Name:", self.device_name_input)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["master", "client"])
        self.role_combo.setCurrentText(self.config.role)
        device_layout.addRow("Device Role:", self.role_combo)
        
        layout.addWidget(device_group)
        
        # Connection settings
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QFormLayout(conn_group)
        
        self.auto_connect_combo = QComboBox()
        self.auto_connect_combo.addItems(["Yes", "No"])
        current = "Yes" if self.config.auto_connect else "No"
        self.auto_connect_combo.setCurrentText(current)
        conn_layout.addRow("Auto-connect on startup:", self.auto_connect_combo)
        
        layout.addWidget(conn_group)
        
        # Input settings
        input_group = QGroupBox("Input Settings")
        input_layout = QFormLayout(input_group)
        
        self.keyboard_combo = QComboBox()
        self.keyboard_combo.addItems(["Enabled", "Disabled"])
        current = "Enabled" if self.config.keyboard_enabled else "Disabled"
        self.keyboard_combo.setCurrentText(current)
        input_layout.addRow("Keyboard capture:", self.keyboard_combo)
        
        self.mouse_combo = QComboBox()
        self.mouse_combo.addItems(["Enabled", "Disabled"])
        current = "Enabled" if self.config.mouse_enabled else "Disabled"
        self.mouse_combo.setCurrentText(current)
        input_layout.addRow("Mouse capture:", self.mouse_combo)
        
        layout.addWidget(input_group)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        try:
            # Update config
            self.config.device_name = self.device_name_input.text()
            self.config.role = self.role_combo.currentText()
            self.config.auto_connect = self.auto_connect_combo.currentText() == "Yes"
            self.config.keyboard_enabled = self.keyboard_combo.currentText() == "Enabled"
            self.config.mouse_enabled = self.mouse_combo.currentText() == "Enabled"
            
            # Emit signal
            settings = {
                "device_name": self.config.device_name,
                "role": self.config.role,
                "auto_connect": self.config.auto_connect,
                "keyboard_enabled": self.config.keyboard_enabled,
                "mouse_enabled": self.config.mouse_enabled,
            }
            self.settings_changed.emit(settings)
            
            # Save to file
            self.config.save()
            
            logger.info("Settings saved successfully")
            self.accept()
        
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
