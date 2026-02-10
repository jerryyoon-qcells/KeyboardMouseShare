"""Main Application Window."""

import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTabWidget, QStatusBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal

from src.ui.manager import UIConfiguration
from src.ui.widgets.device_list import DeviceListWidget
from src.ui.widgets.connection_status import ConnectionStatusWidget
from src.ui.dialogs import ConnectDeviceDialog, SettingsDialog


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window containing discovery, connection, and relay UI.
    
    Layout:
    ┌─ Menu Bar ──────────────────────────┐
    │ File | View | Help                  │
    ├─ Toolbar ──────────────────────────┤
    │ [⟳ Refresh] [⚙️ Settings] [?Help]   │
    ├─ Tab Widget ──────────────────────┤
    │ ┌─ Discovery ─┐ ┌─ Status ──┐     │
    │ │             │ │           │     │
    │ │ Device List │ │ Connection│     │
    │ │ (10 devices)│ │ Status    │     │
    │ │             │ │           │     │
    │ └─────────────┘ └───────────┘     │
    └─ Status Bar ──────────────────────┘
    """
    
    def __init__(self, config: UIConfiguration):
        """
        Initialize main window.
        
        Args:
            config: UI configuration instance
        """
        super().__init__()
        
        self.config = config
        self.device_list_widget: DeviceListWidget = None
        self.connection_status_widget: ConnectionStatusWidget = None
        
        self._setup_ui()
        self._setup_status_bar()
        self._setup_menu_bar()
    
    def _setup_ui(self) -> None:
        """Setup main UI layout and widgets."""
        self.setWindowTitle(f"Keyboard & Mouse Share - {self.config.device_name}")
        self.setGeometry(100, 100, 1024, 768)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Tab widget for Discovery and Status
        self.tabs = QTabWidget()
        
        # Discovery tab
        self.device_list_widget = DeviceListWidget(self.config)
        self.tabs.addTab(self.device_list_widget, "🔍 Device Discovery")
        
        # Connection status tab
        self.connection_status_widget = ConnectionStatusWidget()
        self.tabs.addTab(self.connection_status_widget, "📱 Connection Status")
        
        main_layout.addWidget(self.tabs)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("⟳ Refresh Devices")
        refresh_btn.clicked.connect(self.on_refresh_devices)
        toolbar_layout.addWidget(refresh_btn)
        
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.clicked.connect(self.on_open_settings)
        toolbar_layout.addWidget(settings_btn)
        
        toolbar_layout.addStretch()
        
        help_btn = QPushButton("? Help")
        help_btn.clicked.connect(self.on_open_help)
        toolbar_layout.addWidget(help_btn)
        
        main_layout.insertLayout(0, toolbar_layout)
        
        logger.info("Main window UI setup complete")
    
    def _setup_status_bar(self) -> None:
        """Setup status bar."""
        status_bar = self.statusBar()
        status_bar.showMessage("Ready")
        logger.info("Status bar created")
    
    def _setup_menu_bar(self) -> None:
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("&Quit", self.close)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction("&Refresh", self.on_refresh_devices)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&About", self.on_open_help)
        
        logger.info("Menu bar created")
    
    def on_refresh_devices(self) -> None:
        """Handle refresh devices button click."""
        try:
            self.statusBar().showMessage("Refreshing device list...")
            if self.device_list_widget:
                self.device_list_widget.refresh_devices()
            self.statusBar().showMessage("Device list refreshed")
        except Exception as e:
            logger.error(f"Error refreshing devices: {e}")
            self.statusBar().showMessage(f"Error: {e}")
    
    def on_open_settings(self) -> None:
        """Handle open settings button click."""
        try:
            dialog = SettingsDialog(self.config, self)
            dialog.settings_changed.connect(self._on_settings_changed)
            dialog.exec_()
            logger.info("Settings dialog closed")
        except Exception as e:
            logger.error(f"Error opening settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open settings: {e}")
    
    def on_open_help(self) -> None:
        """Handle open help button click."""
        try:
            help_text = """
            Keyboard & Mouse Share - Help
            
            Device Discovery:
            - Devices on the network are automatically discovered via mDNS
            - Online devices show with a green indicator
            - Click a device to select it
            
            Connecting:
            - Select a device and click "Connect"
            - Choose your device's role (master or client)
            - Connection progress is shown in the Connection Status tab
            
            Settings:
            - Configure device name and role
            - Enable/disable keyboard and mouse capture
            - Set auto-connect preferences
            
            Input Metrics:
            - View real-time counts of input events
            - Key presses, mouse moves, clicks, and scrolling
            - Resets when connection is closed
            """
            QMessageBox.information(self, "Help", help_text)
            logger.info("Help dialog displayed")
        except Exception as e:
            logger.error(f"Error opening help: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open help: {e}")
    
    def _on_settings_changed(self, settings: dict) -> None:
        """
        Handle settings changed signal.
        
        Args:
            settings: Dict with new settings
        """
        try:
            self.statusBar().showMessage("Settings updated successfully")
            logger.info(f"Settings updated: {settings}")
        except Exception as e:
            logger.error(f"Error handling settings change: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        logger.info("Main window closing")
        self.config.save()
        event.accept()
