"""UI Manager - Lifecycle and QApplication management."""

import logging
from typing import Optional, Callable
from pathlib import Path
import json
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer, QObject, pyqtSignal


logger = logging.getLogger(__name__)


class UIConfiguration:
    """UI and application configuration."""
    
    def __init__(self, device_name: str = "KeyboardMouseShare", role: str = "master"):
        """
        Initialize UI configuration.
        
        Args:
            device_name: Name of this device
            role: "master" (sends input) or "client" (receives input)
        """
        self.device_name = device_name
        self._role = role  # master or client
        self.auto_connect = False
        self.keyboard_enabled = True
        self.mouse_enabled = True
        self.config_file = Path.home() / ".keyboards-mouse-share" / "config.json"
        
        self._validate()
    
    @property
    def role(self) -> str:
        """Get device role."""
        return self._role
    
    @role.setter
    def role(self, value: str) -> None:
        """Set device role with validation."""
        if value not in ("master", "client"):
            raise ValueError("role must be 'master' or 'client'")
        self._role = value
    
    def _validate(self):
        """Validate configuration values."""
        if not isinstance(self.device_name, str) or len(self.device_name) < 1:
            raise ValueError("device_name must be non-empty string")
        
        if self._role not in ("master", "client"):
            raise ValueError("role must be 'master' or 'client'")
    
    def save(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_dict = {
                "device_name": self.device_name,
                "role": self._role,
                "auto_connect": self.auto_connect,
                "keyboard_enabled": self.keyboard_enabled,
                "mouse_enabled": self.mouse_enabled,
            }
            
            with open(self.config_file, "w") as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    @classmethod
    def load(cls) -> "UIConfiguration":
        """
        Load configuration from file.
        
        Returns:
            UIConfiguration instance (uses defaults if file missing)
        """
        config_file = Path.home() / ".keyboards-mouse-share" / "config.json"
        
        if not config_file.exists():
            logger.info("No saved configuration found, using defaults")
            return cls()
        
        try:
            with open(config_file, "r") as f:
                config_dict = json.load(f)
            
            config = cls(
                device_name=config_dict.get("device_name", "KeyboardMouseShare"),
                role=config_dict.get("role", "master")
            )
            config.auto_connect = config_dict.get("auto_connect", False)
            config.keyboard_enabled = config_dict.get("keyboard_enabled", True)
            config.mouse_enabled = config_dict.get("mouse_enabled", True)
            
            logger.info(f"Configuration loaded from {config_file}")
            return config
        
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}, using defaults")
            return cls()


class UIManager(QObject):
    """
    Manages PyQt5 application lifecycle and UI coordination.
    
    Responsibilities:
    1. Create and manage QApplication
    2. Create main window and widgets
    3. Connect Phase 2 services to UI components
    4. Handle application lifecycle (startup, shutdown, cleanup)
    """
    
    # Signals
    startup_complete = pyqtSignal()
    shutdown_requested = pyqtSignal()
    
    def __init__(self, config: Optional[UIConfiguration] = None):
        """
        Initialize UI manager.
        
        Args:
            config: UIConfiguration instance (loads defaults if None)
        """
        super().__init__()
        
        self.config = config or UIConfiguration.load()
        self.app: Optional[QApplication] = None
        self.main_window: Optional[QMainWindow] = None
        self.service_bridge: Optional['UIServiceBridge'] = None
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._on_refresh_tick)
    
    def create_application(self) -> bool:
        """
        Create QApplication instance.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.app is not None:
                logger.warning("QApplication already exists")
                return False
            
            self.app = QApplication.instance()
            if self.app is None:
                self.app = QApplication([])
            
            logger.info("QApplication created successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create QApplication: {e}")
            return False
    
    def create_main_window(self) -> bool:
        """
        Create and display main window.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.app is None:
                logger.error("QApplication not initialized")
                return False
            
            # Lazy import to avoid circular dependency
            from src.ui.main_window import MainWindow
            
            self.main_window = MainWindow(self.config)
            self.main_window.show()
            
            logger.info("Main window created and displayed")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create main window: {e}")
            return False
    
    def create_service_bridge(self) -> bool:
        """
        Create UI service bridge for connecting Phase 2 services.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.main_window is None:
                logger.error("Main window not created")
                return False
            
            # Lazy import to avoid circular dependency
            from src.ui.service_bridge import UIServiceBridge
            
            self.service_bridge = UIServiceBridge(
                device_list_widget=self.main_window.device_list_widget,
                connection_status_widget=self.main_window.connection_status_widget
            )
            
            logger.info("UI service bridge created")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create service bridge: {e}")
            return False
    
    def attach_discovery_service(self, service) -> bool:
        """
        Attach discovery service to UI bridge.
        
        Args:
            service: DiscoveryService instance
        
        Returns:
            True if attached successfully
        """
        try:
            if self.service_bridge is None:
                logger.error("Service bridge not initialized")
                return False
            
            self.service_bridge.attach_discovery_service(service)
            logger.info("DiscoveryService attached to UI")
            return True
        
        except Exception as e:
            logger.error(f"Failed to attach discovery service: {e}")
            return False
    
    def attach_connection_handler(self, handler) -> bool:
        """
        Attach connection handler to UI bridge.
        
        Args:
            handler: ConnectionHandler instance
        
        Returns:
            True if attached successfully
        """
        try:
            if self.service_bridge is None:
                logger.error("Service bridge not initialized")
                return False
            
            self.service_bridge.attach_connection_handler(handler)
            logger.info("ConnectionHandler attached to UI")
            return True
        
        except Exception as e:
            logger.error(f"Failed to attach connection handler: {e}")
            return False
    
    def attach_input_handler(self, handler_id: str, handler) -> bool:
        """
        Attach input handler to UI bridge for metrics tracking.
        
        Args:
            handler_id: Identifier for handler (e.g., "windows")
            handler: Input handler instance
        
        Returns:
            True if attached successfully
        """
        try:
            if self.service_bridge is None:
                logger.error("Service bridge not initialized")
                return False
            
            self.service_bridge.attach_input_handler(handler_id, handler)
            logger.info(f"Input handler '{handler_id}' attached to UI")
            return True
        
        except Exception as e:
            logger.error(f"Failed to attach input handler: {e}")
            return False
    
    def start_refresh_timer(self, interval_ms: int = 5000) -> bool:
        """
        Start periodic refresh timer for device list updates.
        
        Args:
            interval_ms: Refresh interval in milliseconds (default 5s)
        
        Returns:
            True if started successfully
        """
        try:
            self._refresh_timer.setInterval(interval_ms)
            self._refresh_timer.start()
            logger.info(f"Refresh timer started (interval={interval_ms}ms)")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start refresh timer: {e}")
            return False
    
    def stop_refresh_timer(self) -> bool:
        """
        Stop periodic refresh timer.
        
        Returns:
            True if stopped successfully
        """
        try:
            self._refresh_timer.stop()
            logger.info("Refresh timer stopped")
            return True
        
        except Exception as e:
            logger.error(f"Failed to stop refresh timer: {e}")
            return False
    
    def _on_refresh_tick(self) -> None:
        """Handle refresh timer tick (trigger device list update)."""
        if self.main_window:
            # This will be implemented in MainWindow
            pass
    
    def run(self) -> int:
        """
        Run the UI application event loop.
        
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            if self.app is None:
                logger.error("QApplication not initialized")
                return 1
            
            if self.main_window is None:
                logger.error("Main window not created")
                return 1
            
            # Start service bridge polling if available
            if self.service_bridge:
                self.service_bridge.start_polling()
            
            self.start_refresh_timer()
            self.startup_complete.emit()
            
            exit_code = self.app.exec_()
            
            self.stop_refresh_timer()
            
            # Stop service bridge polling
            if self.service_bridge:
                self.service_bridge.stop_polling()
            
            self.shutdown_requested.emit()
            
            return exit_code
        
        except Exception as e:
            logger.error(f"Error running application: {e}")
            return 1
    
    def shutdown(self) -> bool:
        """
        Shutdown the application cleanly.
        
        Returns:
            True if shutdown successful
        """
        try:
            self.stop_refresh_timer()
            
            # Shutdown service bridge
            if self.service_bridge:
                self.service_bridge.shutdown()
            
            if self.main_window:
                self.main_window.close()
            
            if self.app:
                self.app.quit()
            
            logger.info("Application shutdown complete")
            return True
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            return False
