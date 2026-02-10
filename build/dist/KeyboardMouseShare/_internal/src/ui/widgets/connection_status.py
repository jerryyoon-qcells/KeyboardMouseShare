"""Connection Status Display Widget."""

import logging
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from src.models.device import Device
from src.models.input_event import InputEventType


logger = logging.getLogger(__name__)


class ConnectionStatusWidget(QWidget):
    """
    Widget for displaying connection status and activity metrics.
    
    Features:
    - Shows active connection status
    - Displays TLS connection progress
    - Shows input event metrics (keys, mouse, etc.)
    - Real-time activity indicators
    """
    
    def __init__(self):
        """Initialize connection status widget."""
        super().__init__()
        
        self.current_device: Optional[str] = None
        self.metrics = {
            "key_press": 0,
            "key_release": 0,
            "mouse_move": 0,
            "mouse_click": 0,
            "mouse_scroll": 0,
        }
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup UI layout."""
        main_layout = QVBoxLayout(self)
        
        # Connection status section
        status_box = QVBoxLayout()
        
        status_title = QLabel("🔐 Connection Status")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        status_title.setFont(title_font)
        status_box.addWidget(status_title)
        
        # Device info
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Connected Device:"))
        self.device_label = QLabel("None")
        self.device_label.setStyleSheet("color: gray;")
        device_layout.addWidget(self.device_label)
        device_layout.addStretch()
        status_box.addLayout(device_layout)
        
        # TLS status
        tls_layout = QHBoxLayout()
        tls_layout.addWidget(QLabel("TLS Status:"))
        self.tls_status = QLabel("Not Connected")
        self.tls_status.setStyleSheet("color: #ff6600;")
        tls_layout.addWidget(self.tls_status)
        tls_layout.addStretch()
        status_box.addLayout(tls_layout)
        
        # Connection progress
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("Connection Progress:"))
        self.connection_progress = QProgressBar()
        self.connection_progress.setValue(0)
        progress_layout.addWidget(self.connection_progress)
        status_box.addLayout(progress_layout)
        
        main_layout.addLayout(status_box)
        
        # Metrics section
        metrics_title = QLabel("📊 Input Event Metrics")
        metrics_title.setFont(title_font)
        main_layout.addWidget(metrics_title)
        
        # Metrics table
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Event Type", "Count"])
        self.metrics_table.setMaximumHeight(200)
        
        # Add metric rows
        for i, event_type in enumerate([
            "Key Press",
            "Key Release",
            "Mouse Move",
            "Mouse Click",
            "Mouse Scroll"
        ]):
            self.metrics_table.insertRow(i)
            self.metrics_table.setItem(i, 0, QTableWidgetItem(event_type))
            self.metrics_table.setItem(i, 1, QTableWidgetItem("0"))
        
        main_layout.addWidget(self.metrics_table)
        
        # Activity section
        activity_title = QLabel("⚡ Activity Status")
        activity_title.setFont(title_font)
        main_layout.addWidget(activity_title)
        
        activity_layout = QHBoxLayout()
        activity_layout.addWidget(QLabel("Last Event:"))
        self.last_event_label = QLabel("None")
        self.last_event_label.setStyleSheet("color: gray;")
        activity_layout.addWidget(self.last_event_label)
        activity_layout.addStretch()
        main_layout.addLayout(activity_layout)
        
        main_layout.addStretch()
        
        logger.info("Connection status widget initialized")
    
    def set_connected(self, device_name: str) -> None:
        """
        Update widget to show connected state.
        
        Args:
            device_name: Name of connected device
        """
        try:
            self.current_device = device_name
            self.device_label.setText(device_name)
            self.device_label.setStyleSheet("color: green; font-weight: bold;")
            
            self.tls_status.setText("Connected (TLS 1.3)")
            self.tls_status.setStyleSheet("color: green; font-weight: bold;")
            
            self.connection_progress.setValue(100)
            
            # Reset metrics
            self._reset_metrics()
            
            logger.info(f"Widget updated for connected device: {device_name}")
        
        except Exception as e:
            logger.error(f"Error setting connected state: {e}")
    
    def set_connecting(self, device_name: str) -> None:
        """
        Update widget to show connecting state.
        
        Args:
            device_name: Name of device being connected
        """
        try:
            self.current_device = device_name
            self.device_label.setText(device_name)
            self.device_label.setStyleSheet("color: blue;")
            
            self.tls_status.setText("Connecting... (TLS Handshake)")
            self.tls_status.setStyleSheet("color: #ff6600;")
            
            self.connection_progress.setValue(50)
            
            logger.info(f"Widget updated for connecting: {device_name}")
        
        except Exception as e:
            logger.error(f"Error setting connecting state: {e}")
    
    def set_disconnected(self) -> None:
        """Update widget to show disconnected state."""
        try:
            self.current_device = None
            self.device_label.setText("None")
            self.device_label.setStyleSheet("color: gray;")
            
            self.tls_status.setText("Not Connected")
            self.tls_status.setStyleSheet("color: gray;")
            
            self.connection_progress.setValue(0)
            
            self._reset_metrics()
            
            logger.info("Widget updated for disconnected state")
        
        except Exception as e:
            logger.error(f"Error setting disconnected state: {e}")
    
    def update_input_event(self, event_type: InputEventType, event_data: dict) -> None:
        """
        Update metrics for input event.
        
        Args:
            event_type: Type of input event
            event_data: Event data dict
        """
        try:
            # Map InputEventType to metric key
            type_map = {
                InputEventType.KEY_PRESS: "key_press",
                InputEventType.KEY_RELEASE: "key_release",
                InputEventType.MOUSE_MOVE: "mouse_move",
                InputEventType.MOUSE_CLICK: "mouse_click",
                InputEventType.MOUSE_SCROLL: "mouse_scroll",
            }
            
            metric_key = type_map.get(event_type)
            if metric_key and metric_key in self.metrics:
                self.metrics[metric_key] += 1
                self._update_metrics_display()
                
                # Update last event label
                event_name = event_type.name.replace("_", " ").title()
                self.last_event_label.setText(f"{event_name} - {self.metrics[metric_key]} total")
                self.last_event_label.setStyleSheet("color: black;")
        
        except Exception as e:
            logger.error(f"Error updating input event: {e}")
    
    def _reset_metrics(self) -> None:
        """Reset all metric counters."""
        try:
            for key in self.metrics:
                self.metrics[key] = 0
            
            self._update_metrics_display()
            self.last_event_label.setText("None")
            self.last_event_label.setStyleSheet("color: gray;")
        
        except Exception as e:
            logger.error(f"Error resetting metrics: {e}")
    
    def _update_metrics_display(self) -> None:
        """Update metrics table display."""
        try:
            row_map = {
                "key_press": 0,
                "key_release": 1,
                "mouse_move": 2,
                "mouse_click": 3,
                "mouse_scroll": 4,
            }
            
            for key, row in row_map.items():
                count = self.metrics.get(key, 0)
                item = QTableWidgetItem(str(count))
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.metrics_table.setItem(row, 1, item)
        
        except Exception as e:
            logger.error(f"Error updating metrics display: {e}")
