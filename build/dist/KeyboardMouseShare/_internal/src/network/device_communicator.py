"""Device communication layer for coordinating input sharing between devices."""

import logging
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, asdict

from src.models.device import Device
from src.models.input_event import InputEvent
from src.network.connection import ConnectionHandler
from src.relay.input_relay import InputRelay, RelayManager, RelayConfig

logger = logging.getLogger(__name__)


@dataclass
class DeviceLink:
    """Represents a communication link between two devices."""
    
    local_device: Device
    remote_device: Device
    connection: ConnectionHandler
    relay: Optional[InputRelay] = None
    is_active: bool = False


class DeviceCommunicator:
    """
    Manages communication between multiple devices.
    
    Handles:
    - Establishing connections between devices
    - Creating and managing input relays
    - Sending/receiving input events
    - Managing device relationships
    - Connection state tracking
    """
    
    def __init__(self, local_device: Device):
        """
        Initialize DeviceCommunicator.
        
        Args:
            local_device: This device
        """
        self.local_device = local_device
        self.relay_manager = RelayManager(local_device)
        self.device_links: Dict[str, DeviceLink] = {}  # device_id -> link
        
        # Callbacks
        self.on_device_connected: Optional[Callable[[Device], None]] = None
        self.on_device_disconnected: Optional[Callable[[Device], None]] = None
        self.on_input_event_received: Optional[Callable[[InputEvent], None]] = None
        self.on_device_error: Optional[Callable[[Device, Exception], None]] = None
    
    def establish_connection(
        self,
        remote_device: Device,
        connection_handler: ConnectionHandler,
        relay_config: Optional[RelayConfig] = None
    ) -> bool:
        """
        Establish communication link with a remote device.
        
        Args:
            remote_device: Remote device to connect to
            connection_handler: Connection to remote device
            relay_config: Input relay configuration
            
        Returns:
            True if connection established successfully, False otherwise
        """
        if remote_device.id in self.device_links:
            logger.warning(f"Connection already exists for {remote_device.name}")
            return False
        
        try:
            # Create relay for input forwarding
            relay = self.relay_manager.add_relay(
                remote_device,
                connection_handler,
                relay_config
            )
            
            if relay is None:
                logger.error(f"Failed to create relay for {remote_device.name}")
                return False
            
            # Create device link
            link = DeviceLink(
                local_device=self.local_device,
                remote_device=remote_device,
                connection=connection_handler,
                relay=relay,
                is_active=True
            )
            
            self.device_links[remote_device.id] = link
            
            # Notify listeners
            if self.on_device_connected:
                self.on_device_connected(remote_device)
            
            logger.info(f"Connection established with {remote_device.name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to establish connection with {remote_device.name}: {e}")
            if self.on_device_error:
                self.on_device_error(remote_device, e)
            return False
    
    def close_connection(self, device_id: str) -> bool:
        """
        Close communication link with a device.
        
        Args:
            device_id: ID of device to disconnect from
            
        Returns:
            True if disconnected successfully, False otherwise
        """
        if device_id not in self.device_links:
            return False
        
        try:
            link = self.device_links[device_id]
            
            # Stop relay
            if link.relay:
                link.relay.stop()
            
            # Remove from relay manager
            self.relay_manager.remove_relay(device_id)
            
            # Update link state
            link.is_active = False
            
            # Notify listeners
            if self.on_device_disconnected:
                self.on_device_disconnected(link.remote_device)
            
            # Remove link
            del self.device_links[device_id]
            
            logger.info(f"Connection closed with {link.remote_device.name}")
            return True
        
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
            return False
    
    def send_input_event(self, device_id: str, event: InputEvent) -> bool:
        """
        Send input event to specific device.
        
        Args:
            device_id: Target device ID
            event: Input event to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if device_id not in self.device_links:
            logger.warning(f"No connection to device {device_id}")
            return False
        
        link = self.device_links[device_id]
        if not link.is_active or not link.relay:
            logger.warning(f"Connection not active for {device_id}")
            return False
        
        return link.relay.queue_event(event)
    
    def broadcast_input_event(self, event: InputEvent) -> int:
        """
        Broadcast input event to all connected devices.
        
        Args:
            event: Input event to broadcast
            
        Returns:
            Number of devices that received the event
        """
        return self.relay_manager.broadcast_event(event)
    
    def get_connected_devices(self) -> List[Device]:
        """
        Get list of connected devices.
        
        Returns:
            List of remote Device instances
        """
        return [
            link.remote_device
            for link in self.device_links.values()
            if link.is_active
        ]
    
    def get_connection_status(self, device_id: str) -> Optional[Dict]:
        """
        Get status of connection with a device.
        
        Args:
            device_id: Device ID
            
        Returns:
            Status dict or None if no connection
        """
        if device_id not in self.device_links:
            return None
        
        link = self.device_links[device_id]
        relay = link.relay
        
        # Get metrics as dict if relay exists
        metrics_dict = None
        if relay:
            metrics = relay.get_metrics()
            metrics_dict = asdict(metrics)
        
        return {
            "device_id": device_id,
            "device_name": link.remote_device.name,
            "is_active": link.is_active,
            "relay_running": relay.is_running if relay else False,
            "metrics": metrics_dict
        }
    
    def get_all_connection_status(self) -> Dict[str, Dict]:
        """
        Get status of all connections.
        
        Returns:
            Dictionary of device_id -> status dict
        """
        return {
            device_id: self.get_connection_status(device_id)
            for device_id in self.device_links.keys()
        }
    
    def shutdown(self) -> bool:
        """
        Shutdown all connections.
        
        Returns:
            True if shutdown successfully, False otherwise
        """
        try:
            # Close all connections
            device_ids = list(self.device_links.keys())
            for device_id in device_ids:
                self.close_connection(device_id)
            
            # Shutdown relay manager
            self.relay_manager.shutdown()
            
            logger.info("DeviceCommunicator shutdown complete")
            return True
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            return False


class InputEventReceiver:
    """
    Receives and processes input events from remote devices.
    
    Handles:
    - Receiving input events over network
    - Validating events
    - Broadcasting to local input handlers
    - Error handling
    """
    
    def __init__(self, communicator: DeviceCommunicator):
        """
        Initialize InputEventReceiver.
        
        Args:
            communicator: Device communicator instance
        """
        self.communicator = communicator
        self.event_handlers: List[Callable[[InputEvent], None]] = []
    
    def register_handler(self, handler: Callable[[InputEvent], None]):
        """
        Register handler for received input events.
        
        Args:
            handler: Callback function for input events
        """
        self.event_handlers.append(handler)
        logger.debug(f"Input event handler registered")
    
    def unregister_handler(self, handler: Callable[[InputEvent], None]):
        """
        Unregister input event handler.
        
        Args:
            handler: Handler to remove
        """
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)
            logger.debug("Input event handler unregistered")
    
    def process_received_event(self, event: InputEvent):
        """
        Process received input event from remote device.
        
        Args:
            event: Received input event
        """
        try:
            # Validate event
            if not self._validate_event(event):
                logger.warning(f"Received invalid event: {event}")
                return
            
            # Broadcast to handlers
            for handler in self.event_handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in input event handler: {e}")
        
        except Exception as e:
            logger.error(f"Error processing received event: {e}")
    
    def _validate_event(self, event: InputEvent) -> bool:
        """
        Validate input event structure.
        
        Args:
            event: Event to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check event type
            if not event.event_type:
                return False
            
            # Check device IDs
            if not event.source_device_id or not event.target_device_id:
                return False
            
            # Check payloadstructure matches event type
            if not event.payload:
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating event: {e}")
            return False
