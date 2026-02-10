"""macOS-specific input capture handler using PyObjC."""

import logging
from typing import Callable
from datetime import datetime, timezone
import uuid

from src.input.handler import InputHandler
from src.models.input_event import InputEvent, InputEventType


logger = logging.getLogger(__name__)


class MacOSInputHandler(InputHandler):
    """
    macOS input handler using PyObjC framework.
    
    Captures:
    - Keyboard events (KEY_PRESS, KEY_RELEASE)
    - Mouse events (MOUSE_MOVE, MOUSE_CLICK)
    
    Note: Requires PyObjC and macOS Accessibility permissions
    """
    
    def __init__(self, device_id: str, listener_callback: Callable[[InputEvent], None]):
        """
        Initialize macOS input handler.
        
        Args:
            device_id: Unique identifier for this device
            listener_callback: Function to call when input is captured
        """
        super().__init__(device_id, listener_callback)
        
        self.observer = None
        self._pyobjc_available = False
        self._check_pyobjc_availability()
    
    def _check_pyobjc_availability(self) -> None:
        """Check if PyObjC is available."""
        try:
            import Quartz
            self._pyobjc_available = True
        except ImportError:
            self._pyobjc_available = False
            logger.warning("PyObjC not available - macOS input handler will not work")
    
    def start(self) -> bool:
        """
        Start monitoring keyboard and mouse events on macOS.
        
        Returns:
            True if monitoring started successfully, False otherwise
        """
        try:
            if not self._pyobjc_available:
                logger.error("PyObjC not available")
                return False
            
            logger.info("Starting macOS input handler")
            
            import Quartz
            from Foundation import NSMutableArray
            
            # Create event listener using Quartz event tap
            self.observer = Quartz.CGEventTapCreate(
                Quartz.kCGSessionEventTap,
                Quartz.kCGHeadInsertEventTap,
                Quartz.kCGEventTapOptionDefault,
                Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown) |
                Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp) |
                Quartz.CGEventMaskBit(Quartz.kCGEventMouseMoved) |
                Quartz.CGEventMaskBit(Quartz.kCGEventLeftMouseDown) |
                Quartz.CGEventMaskBit(Quartz.kCGEventLeftMouseUp) |
                Quartz.CGEventMaskBit(Quartz.kCGEventRightMouseDown) |
                Quartz.CGEventMaskBit(Quartz.kCGEventRightMouseUp) |
                Quartz.CGEventMaskBit(Quartz.kCGEventScrollWheel),
                self._event_callback,
                None
            )
            
            if not self.observer:
                logger.error("Failed to create Quartz event tap")
                return False
            
            self.is_running = True
            logger.info("macOS input handler started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start macOS input handler: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop monitoring input events on macOS.
        
        Returns:
            True if monitoring stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping macOS input handler")
            
            if self.observer:
                import Quartz
                Quartz.CGEventTapEnable(self.observer, False)
                self.observer = None
            
            self.is_running = False
            logger.info("macOS input handler stopped successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping macOS input handler: {e}")
            return False
    
    def is_active(self) -> bool:
        """
        Check if macOS input handler is actively monitoring.
        
        Returns:
            True if handler is running and observer is active
        """
        return self.is_running and self.observer is not None
    
    def _event_callback(self, proxy, event_type, event, refcon):
        """
        Callback for Quartz events.
        
        Args:
            proxy: Event tap proxy
            event_type: Type of event from Quartz
            event: Event object from Quartz
            refcon: Reference context (unused)
        """
        try:
            import Quartz
            
            if event_type == Quartz.kCGEventKeyDown:
                self._handle_key_press(event)
            elif event_type == Quartz.kCGEventKeyUp:
                self._handle_key_release(event)
            elif event_type == Quartz.kCGEventMouseMoved:
                self._handle_mouse_move(event)
            elif event_type in (Quartz.kCGEventLeftMouseDown, Quartz.kCGEventRightMouseDown):
                self._handle_mouse_press(event, event_type)
            elif event_type in (Quartz.kCGEventLeftMouseUp, Quartz.kCGEventRightMouseUp):
                self._handle_mouse_release(event, event_type)
            elif event_type == Quartz.kCGEventScrollWheel:
                self._handle_scroll(event)
        
        except Exception as e:
            logger.error(f"Error in event callback: {e}")
        
        return event
    
    def _handle_key_press(self, event) -> None:
        """Handle keyboard press event."""
        try:
            keycode = self._get_key_code(event)
            event_obj = InputEvent(
                event_type=InputEventType.KEY_PRESS,
                source_device_id=self.device_id,
                target_device_id=str(uuid.uuid4()),
                payload={"keycode": keycode},
                timestamp=datetime.now(timezone.utc)
            )
            self.on_input_event(event_obj)
        except Exception as e:
            logger.error(f"Error handling key press: {e}")
    
    def _handle_key_release(self, event) -> None:
        """Handle keyboard release event."""
        try:
            keycode = self._get_key_code(event)
            event_obj = InputEvent(
                event_type=InputEventType.KEY_RELEASE,
                source_device_id=self.device_id,
                target_device_id=str(uuid.uuid4()),
                payload={"keycode": keycode},
                timestamp=datetime.now(timezone.utc)
            )
            self.on_input_event(event_obj)
        except Exception as e:
            logger.error(f"Error handling key release: {e}")
    
    def _handle_mouse_move(self, event) -> None:
        """Handle mouse move event."""
        try:
            import Quartz
            location = Quartz.CGEventGetLocation(event)
            event_obj = InputEvent(
                event_type=InputEventType.MOUSE_MOVE,
                source_device_id=self.device_id,
                target_device_id=str(uuid.uuid4()),
                payload={"x": int(location.x), "y": int(location.y)},
                timestamp=datetime.now(timezone.utc)
            )
            self.on_input_event(event_obj)
        except Exception as e:
            logger.error(f"Error handling mouse move: {e}")
    
    def _handle_mouse_press(self, event, event_type) -> None:
        """Handle mouse press event."""
        try:
            import Quartz
            location = Quartz.CGEventGetLocation(event)
            button_name = "left" if event_type == Quartz.kCGEventLeftMouseDown else "right"
            event_obj = InputEvent(
                event_type=InputEventType.MOUSE_CLICK,
                source_device_id=self.device_id,
                target_device_id=str(uuid.uuid4()),
                payload={"button": button_name, "x": int(location.x), "y": int(location.y)},
                timestamp=datetime.now(timezone.utc)
            )
            self.on_input_event(event_obj)
        except Exception as e:
            logger.error(f"Error handling mouse press: {e}")
    
    def _handle_mouse_release(self, event, event_type) -> None:
        """Handle mouse release event."""
        try:
            import Quartz
            location = Quartz.CGEventGetLocation(event)
            button_name = "left" if event_type == Quartz.kCGEventLeftMouseUp else "right"
            event_obj = InputEvent(
                event_type=InputEventType.MOUSE_RELEASE,
                source_device_id=self.device_id,
                target_device_id=str(uuid.uuid4()),
                payload={"button": button_name, "x": int(location.x), "y": int(location.y)},
                timestamp=datetime.now(timezone.utc)
            )
            self.on_input_event(event_obj)
        except Exception as e:
            logger.error(f"Error handling mouse release: {e}")
    
    def _handle_scroll(self, event) -> None:
        """Handle mouse scroll event."""
        try:
            import Quartz
            location = Quartz.CGEventGetLocation(event)
            scroll_y = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGScrollWheelEventDeltaAxis1)
            event_obj = InputEvent(
                event_type=InputEventType.MOUSE_SCROLL,
                source_device_id=self.device_id,
                target_device_id=str(uuid.uuid4()),
                payload={"scroll_delta": scroll_y, "x": int(location.x), "y": int(location.y)},
                timestamp=datetime.now(timezone.utc)
            )
            self.on_input_event(event_obj)
        except Exception as e:
            logger.error(f"Error handling scroll: {e}")
    
    @staticmethod
    def _get_key_code(event) -> str:
        """Extract key code from Quartz event."""
        try:
            import Quartz
            keycode = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
            return str(keycode)
        except Exception:
            return "unknown"
