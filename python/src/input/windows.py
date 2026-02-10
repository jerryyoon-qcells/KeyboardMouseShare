"""Windows-specific input capture handler using pynput."""

import logging
from typing import Callable
from pynput import mouse, keyboard
from datetime import datetime, timezone
import uuid

from src.input.handler import InputHandler
from src.models.input_event import InputEvent, InputEventType


logger = logging.getLogger(__name__)


class WindowsInputHandler(InputHandler):
    """
    Windows input handler using pynput library.
    
    Captures:
    - Keyboard events (KEY_PRESS, KEY_RELEASE)
    - Mouse events (MOUSE_MOVE, MOUSE_CLICK)
    """
    
    def __init__(self, device_id: str, listener_callback: Callable[[InputEvent], None]):
        """
        Initialize Windows input handler.
        
        Args:
            device_id: Unique identifier for this device
            listener_callback: Function to call when input is captured
        """
        super().__init__(device_id, listener_callback)
        
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.mouse_listener: Optional[mouse.Listener] = None
    
    def start(self) -> bool:
        """
        Start monitoring keyboard and mouse events on Windows.
        
        Returns:
            True if monitoring started successfully, False otherwise
        """
        try:
            logger.info("Starting Windows input handler")
            
            # Create keyboard listener
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.keyboard_listener.start()
            
            # Create mouse listener
            self.mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            self.mouse_listener.start()
            
            self.is_running = True
            logger.info("Windows input handler started successfully")
            return True
        
        except ImportError as e:
            logger.error(f"pynput library not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to start Windows input handler: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop monitoring input events on Windows.
        
        Returns:
            True if monitoring stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping Windows input handler")
            
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
            
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
            
            self.is_running = False
            logger.info("Windows input handler stopped successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping Windows input handler: {e}")
            return False
    
    def is_active(self) -> bool:
        """
        Check if Windows input handler is actively monitoring.
        
        Returns:
            True if handler is running and listeners are active
        """
        if not self.is_running:
            return False
        
        keyboard_active = self.keyboard_listener and self.keyboard_listener.is_alive()
        mouse_active = self.mouse_listener and self.mouse_listener.is_alive()
        
        return keyboard_active and mouse_active
    
    def _on_key_press(self, key) -> None:
        """Handle keyboard press event."""
        try:
            # Extract key code
            if hasattr(key, 'char'):
                keycode = key.char
            elif hasattr(key, 'name'):
                keycode = key.name
            else:
                keycode = str(key)
            
            event = InputEvent(
                event_type=InputEventType.KEY_PRESS,
                source_device_id=self.device_id,
                target_device_id=str(uuid.uuid4()),  # Will be replaced when sending
                payload={"keycode": keycode},
                timestamp=datetime.now(timezone.utc)
            )
            self.on_input_event(event)
        
        except Exception as e:
            logger.error(f"Error processing key press: {e}")
    
    def _on_key_release(self, key) -> None:
        """Handle keyboard release event."""
        try:
            # Extract key code
            if hasattr(key, 'char'):
                keycode = key.char
            elif hasattr(key, 'name'):
                keycode = key.name
            else:
                keycode = str(key)
            
            event = InputEvent(
                event_type=InputEventType.KEY_RELEASE,
                source_device_id=self.device_id,
                target_device_id=str(uuid.uuid4()),
                payload={"keycode": keycode},
                timestamp=datetime.now(timezone.utc)
            )
            self.on_input_event(event)
        
        except Exception as e:
            logger.error(f"Error processing key release: {e}")
    
    def _on_mouse_move(self, x: int, y: int) -> None:
        """Handle mouse move event."""
        try:
            event = InputEvent(
                event_type=InputEventType.MOUSE_MOVE,
                source_device_id=self.device_id,
                target_device_id=str(uuid.uuid4()),
                payload={"x": x, "y": y},
                timestamp=datetime.now(timezone.utc)
            )
            self.on_input_event(event)
        
        except Exception as e:
            logger.error(f"Error processing mouse move: {e}")
    
    def _on_mouse_click(self, x: int, y: int, button, pressed: bool) -> None:
        """Handle mouse click event."""
        try:
            # Determine button name
            if hasattr(button, 'name'):
                button_name = button.name
            else:
                button_name = str(button)
            
            event_type = InputEventType.MOUSE_CLICK if pressed else InputEventType.MOUSE_RELEASE
            
            event = InputEvent(
                event_type=event_type,
                source_device_id=self.device_id,
                target_device_id=str(uuid.uuid4()),
                payload={"button": button_name, "x": x, "y": y},
                timestamp=datetime.now(timezone.utc)
            )
            self.on_input_event(event)
        
        except Exception as e:
            logger.error(f"Error processing mouse click: {e}")
    
    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """Handle mouse scroll event."""
        try:
            event = InputEvent(
                event_type=InputEventType.MOUSE_SCROLL,
                source_device_id=self.device_id,
                target_device_id=str(uuid.uuid4()),
                payload={"scroll_delta": dy, "x": x, "y": y},
                timestamp=datetime.now(timezone.utc)
            )
            self.on_input_event(event)
        
        except Exception as e:
            logger.error(f"Error processing mouse scroll: {e}")
