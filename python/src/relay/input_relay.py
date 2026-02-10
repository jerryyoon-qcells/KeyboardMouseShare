"""Input relay service for forwarding keyboard and mouse events between devices."""

import logging
import threading
import queue
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid
import json

from src.models.input_event import InputEvent, InputEventType
from src.models.device import Device
from src.network.connection import ConnectionHandler

logger = logging.getLogger(__name__)


@dataclass
class RelayConfig:
    """Configuration for input relay."""
    
    max_queue_size: int = 1000
    max_retries: int = 3
    retry_delay_ms: int = 100
    enable_encryption: bool = True
    batch_size: int = 10  # Number of events to batch before sending
    batch_timeout_ms: int = 50  # Max time to wait before sending batch
    log_events: bool = True
    enable_metrics: bool = True


@dataclass
class RelayMetrics:
    """Metrics for relay performance monitoring."""
    
    events_received: int = 0
    events_forwarded: int = 0
    events_failed: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    avg_latency_ms: float = 0.0
    
    def reset(self):
        """Reset all metrics."""
        self.events_received = 0
        self.events_forwarded = 0
        self.events_failed = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.avg_latency_ms = 0.0


class InputRelay:
    """
    Relays input events from master device to client device.
    
    Handles:
    - Receiving input events from local input handlers
    - Queuing events for transmission
    - Batching events for efficiency
    - Forwarding over network connection
    - Metrics tracking
    - Error handling and retries
    """
    
    def __init__(
        self,
        local_device: Device,
        remote_device: Device,
        connection_handler: ConnectionHandler,
        config: Optional[RelayConfig] = None
    ):
        """
        Initialize InputRelay.
        
        Args:
            local_device: This device (sender)
            remote_device: Remote device (receiver)
            connection_handler: Connection to remote device
            config: Relay configuration
        """
        self.local_device = local_device
        self.remote_device = remote_device
        self.connection = connection_handler
        self.config = config or RelayConfig()
        
        # Event queue for incoming events
        self.event_queue: queue.Queue = queue.Queue(maxsize=self.config.max_queue_size)
        
        # Batch buffer
        self.batch_buffer: List[InputEvent] = []
        
        # Control flags
        self.is_running = False
        self.relay_thread: Optional[threading.Thread] = None
        self.event_lock = threading.Lock()
        
        # Metrics
        self.metrics = RelayMetrics()
        self._latencies: List[float] = []
        
        # Callbacks
        self.on_event_forwarded: Optional[Callable[[InputEvent], None]] = None
        self.on_event_failed: Optional[Callable[[InputEvent, Exception], None]] = None
    
    def start(self) -> bool:
        """
        Start the relay service.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("Input relay already running")
            return False
        
        try:
            self.is_running = True
            self.relay_thread = threading.Thread(
                target=self._relay_loop,
                daemon=True,
                name=f"InputRelay-{self.remote_device.name}"
            )
            self.relay_thread.start()
            logger.info(f"Input relay started: {self.local_device.name} -> {self.remote_device.name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start input relay: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Stop the relay service.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.is_running:
            return False
        
        try:
            self.is_running = False
            
            # Flush any pending events
            self._flush_batch()
            
            # Wait for thread to finish
            if self.relay_thread:
                self.relay_thread.join(timeout=2.0)
            
            logger.info(f"Input relay stopped: {self.local_device.name} -> {self.remote_device.name}")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping input relay: {e}")
            return False
    
    def queue_event(self, event: InputEvent) -> bool:
        """
        Queue an input event for relay.
        
        Args:
            event: Input event to relay
            
        Returns:
            True if queued successfully, False if queue is full
        """
        if not self.is_running:
            logger.warning("Relay not running, discarding event")
            return False
        
        try:
            self.event_queue.put_nowait(event)
            self.metrics.events_received += 1
            
            if self.config.log_events:
                logger.debug(f"Event queued: {event.event_type.value}")
            
            return True
        
        except queue.Full:
            logger.warning("Event queue full, dropping event")
            self.metrics.events_failed += 1
            return False
    
    def _relay_loop(self):
        """Main relay loop - processes events and forwards them."""
        while self.is_running:
            try:
                # Wait for event with timeout
                try:
                    event = self.event_queue.get(timeout=self.config.batch_timeout_ms / 1000.0)
                    self._add_to_batch(event)
                
                except queue.Empty:
                    # Timeout reached - flush batch if not empty
                    if self.batch_buffer:
                        self._flush_batch()
                    continue
                
                # Check if batch is full
                if len(self.batch_buffer) >= self.config.batch_size:
                    self._flush_batch()
            
            except Exception as e:
                logger.error(f"Error in relay loop: {e}")
    
    def _add_to_batch(self, event: InputEvent):
        """Add event to batch buffer."""
        with self.event_lock:
            self.batch_buffer.append(event)
    
    def _flush_batch(self):
        """Send batched events over connection."""
        if not self.batch_buffer:
            return
        
        with self.event_lock:
            events_to_send = self.batch_buffer.copy()
            self.batch_buffer.clear()
        
        # Forward events
        for event in events_to_send:
            success = self._forward_event(event)
            
            if success:
                self.metrics.events_forwarded += 1
                
                if self.on_event_forwarded:
                    self.on_event_forwarded(event)
            
            else:
                self.metrics.events_failed += 1
                
                if self.on_event_failed:
                    self.on_event_failed(event, RuntimeError("Failed to forward event"))
    
    def _forward_event(self, event: InputEvent) -> bool:
        """
        Forward single event over network connection.
        
        Args:
            event: Event to forward
            
        Returns:
            True if forwarded successfully, False otherwise
        """
        if not self.connection:
            logger.error("No connection available for relay")
            return False
        
        # Record start time for latency calculation
        start_time = datetime.now(timezone.utc)
        
        for attempt in range(self.config.max_retries):
            try:
                # Serialize event
                event_dict = event.to_dict()
                event_json = json.dumps(event_dict)
                
                # Send over connection
                self.connection.send_message({
                    "type": "INPUT_EVENT",
                    "payload": event_dict
                })
                
                # Record metrics
                self.metrics.bytes_sent += len(event_json.encode())
                
                # Calculate latency
                latency = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                self._latencies.append(latency)
                
                # Update average latency
                if len(self._latencies) > 100:
                    self._latencies.pop(0)
                self.metrics.avg_latency_ms = sum(self._latencies) / len(self._latencies)
                
                if self.config.log_events:
                    logger.debug(f"Event forwarded: {event.event_type.value} ({latency:.1f}ms)")
                
                return True
            
            except Exception as e:
                retry_delay = self.config.retry_delay_ms / 1000.0
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"Failed to forward event (attempt {attempt + 1}), retrying in {retry_delay}s: {e}")
                    threading.Event().wait(retry_delay)
                else:
                    logger.error(f"Failed to forward event after {self.config.max_retries} attempts: {e}")
        
        return False
    
    def get_metrics(self) -> RelayMetrics:
        """
        Get relay metrics.
        
        Returns:
            Current relay metrics
        """
        return self.metrics
    
    def reset_metrics(self):
        """Reset relay metrics."""
        self.metrics.reset()
        self._latencies.clear()
    
    def is_connected(self) -> bool:
        """Check if relay connection is active."""
        return self.is_running and self.connection is not None


class RelayManager:
    """
    Manages multiple input relays for multi-device scenarios.
    
    Handles:
    - Creating relays for each connected device
    - Managing relay lifecycle
    - Coordinating input forwarding
    - Performance monitoring
    """
    
    def __init__(self, local_device: Device):
        """
        Initialize RelayManager.
        
        Args:
            local_device: This device
        """
        self.local_device = local_device
        self.relays: Dict[str, InputRelay] = {}  # device_id -> relay
        self.relay_lock = threading.Lock()
    
    def add_relay(
        self,
        remote_device: Device,
        connection_handler: ConnectionHandler,
        config: Optional[RelayConfig] = None
    ) -> Optional[InputRelay]:
        """
        Add a relay for a remote device.
        
        Args:
            remote_device: Device to relay to
            connection_handler: Connection to device
            config: Relay configuration
            
        Returns:
            Created InputRelay instance, or None if failed
        """
        with self.relay_lock:
            if remote_device.id in self.relays:
                logger.warning(f"Relay already exists for {remote_device.name}")
                return self.relays[remote_device.id]
            
            try:
                relay = InputRelay(
                    self.local_device,
                    remote_device,
                    connection_handler,
                    config
                )
                relay.start()
                self.relays[remote_device.id] = relay
                
                logger.info(f"Relay added for {remote_device.name}")
                return relay
            
            except Exception as e:
                logger.error(f"Failed to create relay for {remote_device.name}: {e}")
                return None
    
    def remove_relay(self, device_id: str) -> bool:
        """
        Remove a relay for a device.
        
        Args:
            device_id: Device ID to remove relay for
            
        Returns:
            True if removed successfully, False otherwise
        """
        with self.relay_lock:
            if device_id not in self.relays:
                return False
            
            try:
                relay = self.relays[device_id]
                relay.stop()
                del self.relays[device_id]
                
                logger.info(f"Relay removed for device {device_id}")
                return True
            
            except Exception as e:
                logger.error(f"Error removing relay: {e}")
                return False
    
    def broadcast_event(self, event: InputEvent) -> int:
        """
        Broadcast input event to all connected relays.
        
        Args:
            event: Event to broadcast
            
        Returns:
            Number of relays that queued the event
        """
        count = 0
        with self.relay_lock:
            for relay in self.relays.values():
                if relay.queue_event(event):
                    count += 1
        
        return count
    
    def get_relay(self, device_id: str) -> Optional[InputRelay]:
        """
        Get relay for a specific device.
        
        Args:
            device_id: Device ID
            
        Returns:
            InputRelay instance or None
        """
        with self.relay_lock:
            return self.relays.get(device_id)
    
    def get_all_relays(self) -> List[InputRelay]:
        """
        Get all active relays.
        
        Returns:
            List of InputRelay instances
        """
        with self.relay_lock:
            return list(self.relays.values())
    
    def get_metrics_summary(self) -> Dict[str, RelayMetrics]:
        """
        Get metrics for all relays.
        
        Returns:
            Dictionary of device_id -> RelayMetrics
        """
        with self.relay_lock:
            return {
                device_id: relay.get_metrics()
                for device_id, relay in self.relays.items()
            }
    
    def shutdown(self) -> bool:
        """
        Shutdown all relays.
        
        Returns:
            True if all relays stopped successfully
        """
        with self.relay_lock:
            success = True
            for relay in self.relays.values():
                try:
                    relay.stop()
                except Exception as e:
                    logger.error(f"Error stopping relay: {e}")
                    success = False
            
            self.relays.clear()
            return success
