"""Abstract base class for platform-specific input capture handlers."""

from abc import ABC, abstractmethod
from typing import Callable, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from src.models.input_event import InputEvent


@dataclass
class InputCapture:
    """Result of an input capture operation."""
    
    event: InputEvent
    timestamp: datetime
    success: bool
    error: Optional[str] = None
    
    def __post_init__(self):
        """Validate input capture."""
        if not isinstance(self.event, InputEvent):
            raise ValueError("event must be InputEvent instance")
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")


class InputHandler(ABC):
    """
    Abstract base class for platform-specific input capture.
    
    Responsibilities:
    1. Monitor keyboard and mouse events on local device
    2. Convert low-level OS events to InputEvent dataclass
    3. Call listener callback with captured events
    4. Handle platform-specific APIs (Windows, macOS)
    5. Manage handler lifecycle (start, stop, cleanup)
    """
    
    def __init__(self, device_id: str, listener_callback: Callable[[InputEvent], None]):
        """
        Initialize input handler.
        
        Args:
            device_id: Unique identifier for this device
            listener_callback: Function to call when input is captured
                             Signature: callback(event: InputEvent) -> None
        
        Raises:
            TypeError: If listener_callback is not callable
        """
        if not callable(listener_callback):
            raise TypeError("listener_callback must be callable")
        
        self.device_id = device_id
        self.listener_callback = listener_callback
        self.is_running = False
    
    @abstractmethod
    def start(self) -> bool:
        """
        Start monitoring for input events.
        
        Returns:
            True if monitoring started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """
        Stop monitoring for input events.
        
        Returns:
            True if monitoring stopped successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def is_active(self) -> bool:
        """
        Check if input handler is currently active and monitoring.
        
        Returns:
            True if handler is actively monitoring, False otherwise
        """
        pass
    
    def on_input_event(self, event: InputEvent) -> None:
        """
        Process captured input event and notify listener.
        
        Args:
            event: InputEvent from platform-specific handler
        
        Raises:
            ValueError: If event validation fails
        """
        if not isinstance(event, InputEvent):
            raise ValueError("event must be InputEvent instance")
        
        try:
            self.listener_callback(event)
        except Exception as e:
            # Log but don't raise - keep monitoring active
            import logging
            logging.error(f"Error in input listener callback: {e}")
    
    def cleanup(self) -> None:
        """
        Cleanup resources and stop monitoring.
        
        Implementations should override to release platform-specific resources.
        """
        if self.is_running:
            self.stop()
