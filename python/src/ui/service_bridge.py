"""UI Service Integration Bridge."""

import logging
import asyncio
import threading
from typing import Optional, Callable, Dict
from dataclasses import dataclass

from src.network.discovery import DiscoveryService
from src.network.connection import ConnectionHandler
from src.models.device import Device
from src.models.input_event import InputEventType
from src.input.handler import InputCapture
from src.ui.widgets.device_list import DeviceListWidget
from src.ui.widgets.connection_status import ConnectionStatusWidget


logger = logging.getLogger(__name__)


@dataclass
class UIServiceBridgeConfig:
    """Configuration for UI service bridge."""
    device_poll_interval: float = 2.0  # Poll discovery service every 2 seconds
    connection_update_interval: float = 0.5  # Update connection status every 500ms
    enable_metrics: bool = True  # Track input event metrics


class UIServiceBridge:
    """
    Bridge connecting Phase 2 network services to Phase 3 UI widgets.
    
    Coordinates:
    - DiscoveryService -> DeviceListWidget
    - ConnectionHandler -> ConnectionStatusWidget
    - InputHandlers -> ConnectionStatusWidget (metrics)
    """
    
    def __init__(
        self,
        device_list_widget: DeviceListWidget,
        connection_status_widget: ConnectionStatusWidget,
        config: UIServiceBridgeConfig = None
    ):
        """
        Initialize service bridge.
        
        Args:
            device_list_widget: Widget for device discovery display
            connection_status_widget: Widget for connection status display
            config: Bridge configuration
        """
        self.device_list_widget = device_list_widget
        self.connection_status_widget = connection_status_widget
        self.config = config or UIServiceBridgeConfig()
        
        # Services (set via attach methods)
        self.discovery_service: Optional[DiscoveryService] = None
        self.connection_handler: Optional[ConnectionHandler] = None
        
        # Internal state
        self._polling_thread: Optional[threading.Thread] = None
        self._polling_active = False
        self._connected_device: Optional[Device] = None
        self._input_callbacks: Dict[str, Callable] = {}
        
        # Connect widget signals to handlers
        self._setup_widget_connections()
        
        logger.info("UIServiceBridge initialized")
    
    def _setup_widget_connections(self) -> None:
        """Setup signal connections from widgets to bridge."""
        # Device list widget signals
        self.device_list_widget.connect_requested.connect(self._on_connect_requested)
        self.device_list_widget.disconnect_requested.connect(self._on_disconnect_requested)
        
        logger.debug("Widget connections established")
    
    def attach_discovery_service(self, service: DiscoveryService) -> None:
        """
        Attach discovery service for device polling.
        
        Args:
            service: DiscoveryService instance
        """
        self.discovery_service = service
        logger.info("DiscoveryService attached to bridge")
    
    def attach_connection_handler(self, handler: ConnectionHandler) -> None:
        """
        Attach connection handler for status tracking.
        
        Args:
            handler: ConnectionHandler instance
        """
        self.connection_handler = handler
        logger.info("ConnectionHandler attached to bridge")
    
    def attach_input_handler(self, handler_id: str, handler) -> None:
        """
        Attach input handler for event tracking.
        
        Args:
            handler_id: Identifier for this handler (e.g., "windows", "macos")
            handler: Input handler instance with input_callback support
        """
        def input_callback(event: InputCapture) -> None:
            """Forward input events to UI."""
            if self.config.enable_metrics:
                self.connection_status_widget.update_input_event(
                    event.event_type,
                    event.payload
                )
        
        self._input_callbacks[handler_id] = input_callback
        
        # If handler supports callbacks, attach ours
        if hasattr(handler, 'set_callback'):
            handler.set_callback(input_callback)
        
        logger.info(f"Input handler '{handler_id}' attached to bridge")
    
    def start_polling(self) -> None:
        """Start polling discovery service for device updates."""
        if self._polling_active:
            logger.warning("Polling already active")
            return
        
        self._polling_active = True
        self._polling_thread = threading.Thread(
            target=self._polling_loop,
            daemon=True,
            name="UIServiceBridge-Polling"
        )
        self._polling_thread.start()
        logger.info("Device polling started")
    
    def stop_polling(self) -> None:
        """Stop polling discovery service."""
        self._polling_active = False
        if self._polling_thread:
            self._polling_thread.join(timeout=5.0)
        logger.info("Device polling stopped")
    
    def _polling_loop(self) -> None:
        """Background thread polling discovery service."""
        try:
            while self._polling_active:
                if self.discovery_service:
                    try:
                        # Get discovered devices
                        devices = self.discovery_service.get_discovered_devices()
                        
                        # Convert to UI format
                        ui_devices = self._convert_devices_to_ui_format(devices)
                        
                        # Update widget
                        self.device_list_widget.update_device_list(ui_devices)
                        
                    except Exception as e:
                        logger.error(f"Error polling discovery service: {e}")
                
                # Sleep before next poll
                threading.Event().wait(self.config.device_poll_interval)
        
        except Exception as e:
            logger.error(f"Polling loop error: {e}")
    
    def _convert_devices_to_ui_format(self, devices: list) -> list:
        """
        Convert Device objects to UI format.
        
        Args:
            devices: List of Device objects from discovery service
        
        Returns:
            List of device dicts for UI display
        """
        ui_devices = []
        
        for device in devices:
            # Determine online/offline status
            status = "online" if device.is_registered else "offline"
            
            ui_device = {
                "id": device.id,
                "name": device.name,
                "os": device.os.value if hasattr(device.os, 'value') else str(device.os),
                "ip_address": device.ip_address or "Unknown",
                "status": status,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None
            }
            
            ui_devices.append(ui_device)
        
        return ui_devices
    
    def _on_connect_requested(self, device_id: str) -> None:
        """
        Handle connect request from device list widget.
        
        Args:
            device_id: ID of device to connect
        """
        try:
            logger.info(f"Connect requested for device: {device_id}")
            
            # Get device from widget's device dict
            if device_id not in self.device_list_widget.devices:
                logger.error(f"Device not found: {device_id}")
                return
            
            device_data = self.device_list_widget.devices[device_id]
            device_name = device_data.get("name", "Unknown")
            
            # Update UI to connecting state
            self.connection_status_widget.set_connecting(device_name)
            
            # Initiate connection with ConnectionHandler
            if self.connection_handler:
                # This would trigger actual connection in real implementation
                logger.info(f"Initiating connection to {device_name}")
                # TODO: Call connection_handler.connect(device_data)
            
        except Exception as e:
            logger.error(f"Error handling connect request: {e}")
    
    def _on_disconnect_requested(self, device_id: str) -> None:
        """
        Handle disconnect request from device list widget.
        
        Args:
            device_id: ID of device to disconnect
        """
        try:
            logger.info(f"Disconnect requested for device: {device_id}")
            
            # Update UI to disconnected state
            self.connection_status_widget.set_disconnected()
            
            # Close connection with ConnectionHandler
            if self.connection_handler:
                logger.info("Closing connection")
                # TODO: Call connection_handler.close()
            
            self._connected_device = None
        
        except Exception as e:
            logger.error(f"Error handling disconnect request: {e}")
    
    def set_connected(self, device: Device) -> None:
        """
        Update UI when connection established.
        
        Args:
            device: Connected device
        """
        try:
            self._connected_device = device
            self.connection_status_widget.set_connected(device)
            logger.info(f"Connection established: {device.name}")
        
        except Exception as e:
            logger.error(f"Error setting connected state: {e}")
    
    def set_disconnected(self) -> None:
        """Update UI when connection closed."""
        try:
            self._connected_device = None
            self.connection_status_widget.set_disconnected()
            logger.info("Connection closed")
        
        except Exception as e:
            logger.error(f"Error setting disconnected state: {e}")
    
    def shutdown(self) -> None:
        """Shutdown bridge and cleanup resources."""
        try:
            self.stop_polling()
            logger.info("UIServiceBridge shutdown complete")
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
