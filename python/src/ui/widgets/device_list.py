"""Device Discovery List Widget."""

import logging
from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal

from src.ui.manager import UIConfiguration


logger = logging.getLogger(__name__)


class DeviceListWidget(QWidget):
    """
    Widget for displaying discovered devices and managing connections.
    
    Features:
    - Shows list of devices discovered via mDNS
    - Displays device name, OS, IP address, status
    - Allows connect/disconnect actions
    - Shows connection status indicators
    """
    
    device_selected = pyqtSignal(str)  # Emits device ID
    connect_requested = pyqtSignal(str)  # Emits device ID
    disconnect_requested = pyqtSignal(str)  # Emits device ID
    
    def __init__(self, config: UIConfiguration):
        """
        Initialize device list widget.
        
        Args:
            config: UI configuration instance
        """
        super().__init__()
        
        self.config = config
        self.devices: dict = {}  # device_id -> device_info
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup UI layout."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("📡 Available Devices")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title)
        
        # Device list
        self.device_list = QListWidget()
        self.device_list.itemSelectionChanged.connect(self._on_device_selected)
        layout.addWidget(self.device_list)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("🔗 Connect")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        self.connect_btn.setEnabled(False)
        button_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("🔌 Disconnect")
        self.disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        self.disconnect_btn.setEnabled(False)
        button_layout.addWidget(self.disconnect_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("No devices found")
        layout.addWidget(self.status_label)
        
        logger.info("Device list widget initialized")
    
    def refresh_devices(self) -> None:
        """
        Refresh device list from discovery service.
        
        Note: In Phase 3 implementation, this will query DiscoveryService
        """
        try:
            logger.debug("Refreshing device list")
            
            # Placeholder: In full implementation, query DiscoveryService
            # device_list = discovery_service.get_discovered_devices()
            # self.update_device_list(device_list)
            
            self.status_label.setText(f"Found {len(self.devices)} device(s)")
        
        except Exception as e:
            logger.error(f"Error refreshing devices: {e}")
            self.status_label.setText(f"Error: {e}")
    
    def update_device_list(self, devices: List[dict]) -> None:
        """
        Update device list display.
        
        Args:
            devices: List of device info dicts
                     {id, name, os, ip_address, status, last_seen}
        """
        try:
            self.device_list.clear()
            self.devices = {}
            
            for device in devices:
                device_id = device.get("id")
                name = device.get("name", "Unknown")
                os_type = device.get("os", "?")
                ip_addr = device.get("ip_address", "?")
                status = device.get("status", "offline")
                
                # Format display text
                status_emoji = "🟢" if status == "online" else "🔴"
                display_text = f"{status_emoji} {name} ({os_type}) - {ip_addr}"
                
                # Add to list
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, device_id)
                self.device_list.addItem(item)
                
                # Store device info
                self.devices[device_id] = device
                
                logger.debug(f"Added device: {name} ({device_id})")
            
            self.status_label.setText(f"Found {len(self.devices)} device(s)")
        
        except Exception as e:
            logger.error(f"Error updating device list: {e}")
            self.status_label.setText(f"Error: {e}")
    
    def _on_device_selected(self) -> None:
        """Handle device selection in list."""
        try:
            selected_items = self.device_list.selectedItems()
            
            if selected_items:
                device_id = selected_items[0].data(Qt.UserRole)
                device = self.devices.get(device_id)
                
                if device:
                    status = device.get("status", "offline")
                    
                    # Enable/disable buttons based on status
                    is_online = status == "online"
                    self.connect_btn.setEnabled(is_online and status != "connected")
                    self.disconnect_btn.setEnabled(status == "connected")
                    
                    self.device_selected.emit(device_id)
                    logger.debug(f"Device selected: {device_id}")
            else:
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(False)
        
        except Exception as e:
            logger.error(f"Error handling device selection: {e}")
    
    def _on_connect_clicked(self) -> None:
        """Handle connect button click."""
        try:
            selected_items = self.device_list.selectedItems()
            
            if selected_items:
                device_id = selected_items[0].data(Qt.UserRole)
                device = self.devices.get(device_id)
                
                if device:
                    self.connect_requested.emit(device_id)
                    logger.info(f"Connect requested for device: {device_id}")
        
        except Exception as e:
            logger.error(f"Error in connect: {e}")
            QMessageBox.critical(self, "Error", f"Connection failed: {e}")
    
    def _on_disconnect_clicked(self) -> None:
        """Handle disconnect button click."""
        try:
            selected_items = self.device_list.selectedItems()
            
            if selected_items:
                device_id = selected_items[0].data(Qt.UserRole)
                device = self.devices.get(device_id)
                
                if device:
                    self.disconnect_requested.emit(device_id)
                    logger.info(f"Disconnect requested for device: {device_id}")
        
        except Exception as e:
            logger.error(f"Error in disconnect: {e}")
            QMessageBox.critical(self, "Error", f"Disconnection failed: {e}")
