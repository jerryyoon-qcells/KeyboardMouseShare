"""Input event applier - simulates keyboard and mouse events on target device."""

import logging
import threading
from typing import Optional, Callable, Dict
from dataclasses import dataclass
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button

from src.models.input_event import InputEvent, InputEventType
from src.models.device import Device

logger = logging.getLogger(__name__)


@dataclass
class ApplierConfig:
    """Configuration for input event applier."""
    
    # Delay between simulated events (ms)
    event_delay_ms: int = 10
    # Enable logging of applied events
    log_events: bool = True
    # Maximum queue size for events
    max_queue_size: int = 1000
    # Enable event validation before application
    validate_events: bool = True
    # Modifier keys state tracking
    track_modifiers: bool = True


@dataclass
class ApplierMetrics:
    """Metrics for applier performance."""
    
    events_received: int = 0
    events_applied: int = 0
    events_failed: int = 0
    keyboard_events: int = 0
    mouse_events: int = 0
    errors: list = None  # List of error messages
    
    def __post_init__(self):
        """Initialize errors list."""
        if self.errors is None:
            self.errors = []
    
    def reset(self):
        """Reset all metrics."""
        self.events_received = 0
        self.events_applied = 0
        self.events_failed = 0
        self.keyboard_events = 0
        self.mouse_events = 0
        self.errors.clear()


class InputEventApplier:
    """
    Applies received input events on the target device.
    
    Simulates:
    - Keyboard events (KEY_PRESS, KEY_RELEASE)
    - Mouse events (MOUSE_MOVE, MOUSE_CLICK, MOUSE_SCROLL)
    
    Features:
    - Thread-safe event queuing
    - Cross-platform support (Windows, macOS, Linux)
    - Event validation
    - Metrics tracking
    - Error handling
    """
    
    # Keycode mappings
    KEYCODE_MAP = {
        "A": "a", "B": "b", "C": "c", "D": "d", "E": "e",
        "F": "f", "G": "g", "H": "h", "I": "i", "J": "j",
        "K": "k", "L": "l", "M": "m", "N": "n", "O": "o",
        "P": "p", "Q": "q", "R": "r", "S": "s", "T": "t",
        "U": "u", "V": "v", "W": "w", "X": "x", "Y": "y",
        "Z": "z", "0": "0", "1": "1", "2": "2", "3": "3",
        "4": "4", "5": "5", "6": "6", "7": "7", "8": "8",
        "9": "9", "Return": Key.enter, "Tab": Key.tab,
        "Escape": Key.esc, "BackSpace": Key.backspace,
        "Delete": Key.delete, "Home": Key.home, "End": Key.end,
        "PageUp": Key.page_up, "PageDown": Key.page_down,
        "Left": Key.left, "Right": Key.right, "Up": Key.up,
        "Down": Key.down, "Insert": Key.insert, "Pause": Key.pause,
        "PrintScreen": Key.print_screen, "CapsLock": Key.caps_lock,
        "NumLock": Key.num_lock, "ScrollLock": Key.scroll_lock,
        "Shift": Key.shift, "Control": Key.ctrl, "Alt": Key.alt,
        "Cmd": Key.cmd, "Space": " ", "!": "!", "@": "@",
        "#": "#", "$": "$", "%": "%", "^": "^", "&": "&",
        "*": "*", "(": "(", ")": ")", "-": "-", "_": "_",
        "=": "=", "+": "+", "[": "[", "]": "]", "{": "{",
        "}": "}", ";": ";", ":": ":", "'": "'", '"': '"',
        ",": ",", "<": "<", ".": ".", ">": ">", "/": "/",
        "?": "?", "\\": "\\", "|": "|", "`": "`", "~": "~"
    }
    
    # Mouse button mappings
    BUTTON_MAP = {
        "left": Button.left,
        "right": Button.right,
        "middle": Button.middle
    }
    
    def __init__(
        self,
        local_device: Device,
        config: Optional[ApplierConfig] = None
    ):
        """
        Initialize InputEventApplier.
        
        Args:
            local_device: Target device for input simulation
            config: Applier configuration
        """
        self.local_device = local_device
        self.config = config or ApplierConfig()
        self.metrics = ApplierMetrics()
        
        # Input controllers
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        
        # Threading
        self.is_running = False
        self.applier_thread = None
        self._event_queue: list = []
        self._queue_lock = threading.Lock()
        self._stop_event = threading.Event()
        
        # State tracking
        self._pressed_keys: set = set()
        self._mouse_position: tuple = (0, 0)
        
        if config and config.log_events:
            logger.info(f"InputEventApplier initialized for {local_device.name}")
    
    def start(self) -> bool:
        """
        Start the applier thread.
        
        Returns:
            True if started successfully, False if already running
        """
        if self.is_running:
            logger.warning("Applier already running")
            return False
        
        self.is_running = True
        self._stop_event.clear()
        self.applier_thread = threading.Thread(
            target=self._apply_loop,
            daemon=True,
            name="InputApplier"
        )
        self.applier_thread.start()
        
        if self.config.log_events:
            logger.info("InputEventApplier started")
        
        return True
    
    def stop(self) -> bool:
        """
        Stop the applier thread.
        
        Returns:
            True if stopped successfully, False if not running
        """
        if not self.is_running:
            logger.warning("Applier not running")
            return False
        
        self.is_running = False
        self._stop_event.set()
        
        # Wait for thread to finish
        if self.applier_thread and self.applier_thread.is_alive():
            self.applier_thread.join(timeout=2.0)
        
        if self.config.log_events:
            logger.info("InputEventApplier stopped")
        
        return True
    
    def apply_event(self, event: InputEvent) -> bool:
        """
        Queue an event for application.
        
        Args:
            event: Event to apply
            
        Returns:
            True if queued successfully, False if queue full
        """
        if not self.is_running:
            logger.warning("Applier not running, rejecting event")
            self.metrics.events_failed += 1
            return False
        
        # Validate event
        if self.config.validate_events:
            if not self._validate_event(event):
                self.metrics.events_failed += 1
                return False
        
        # Check queue size
        with self._queue_lock:
            if len(self._event_queue) >= self.config.max_queue_size:
                logger.error(f"Event queue full ({self.config.max_queue_size})")
                self.metrics.events_failed += 1
                return False
            
            self._event_queue.append(event)
            self.metrics.events_received += 1
        
        if self.config.log_events:
            logger.debug(f"Event queued: {event.event_type.value}")
        
        return True
    
    def _validate_event(self, event: InputEvent) -> bool:
        """
        Validate event structure and content.
        
        Args:
            event: Event to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if event.event_type == InputEventType.KEY_PRESS or \
               event.event_type == InputEventType.KEY_RELEASE:
                if "keycode" not in event.payload:
                    raise ValueError("KEY event missing keycode")
                if "-" in str(event.payload["keycode"]):
                    raise ValueError(f"Invalid keycode format: {event.payload['keycode']}")
            
            elif event.event_type == InputEventType.MOUSE_MOVE:
                if "x" not in event.payload or "y" not in event.payload:
                    raise ValueError("MOUSE_MOVE missing x or y")
                if not isinstance(event.payload["x"], (int, float)):
                    raise ValueError("x coordinate not numeric")
                if not isinstance(event.payload["y"], (int, float)):
                    raise ValueError("y coordinate not numeric")
            
            elif event.event_type == InputEventType.MOUSE_CLICK:
                if "button" not in event.payload:
                    raise ValueError("MOUSE_CLICK missing button")
                if event.payload["button"] not in self.BUTTON_MAP:
                    raise ValueError(f"Unknown button: {event.payload['button']}")
            
            elif event.event_type == InputEventType.MOUSE_SCROLL:
                if "scroll_delta" not in event.payload:
                    raise ValueError("MOUSE_SCROLL missing scroll_delta")
            
            return True
        
        except ValueError as e:
            logger.warning(f"Event validation failed: {e}")
            self.metrics.errors.append(str(e))
            return False
    
    def _apply_loop(self):
        """Main loop for processing and applying events."""
        import time
        
        while self.is_running:
            # Get next event
            event = None
            with self._queue_lock:
                if len(self._event_queue) > 0:
                    event = self._event_queue.pop(0)
            
            if event:
                self._apply_single_event(event)
                time.sleep(self.config.event_delay_ms / 1000.0)
            else:
                # Sleep briefly to avoid busy waiting
                time.sleep(0.002)  # 2ms
    
    def _apply_single_event(self, event: InputEvent):
        """
        Apply a single input event.
        
        Args:
            event: Event to apply
        """
        try:
            if event.event_type == InputEventType.KEY_PRESS:
                self._apply_key_press(event)
                self.metrics.keyboard_events += 1
            
            elif event.event_type == InputEventType.KEY_RELEASE:
                self._apply_key_release(event)
                self.metrics.keyboard_events += 1
            
            elif event.event_type == InputEventType.MOUSE_MOVE:
                self._apply_mouse_move(event)
                self.metrics.mouse_events += 1
            
            elif event.event_type == InputEventType.MOUSE_CLICK:
                self._apply_mouse_click(event)
                self.metrics.mouse_events += 1
            
            elif event.event_type == InputEventType.MOUSE_SCROLL:
                self._apply_mouse_scroll(event)
                self.metrics.mouse_events += 1
            
            else:
                logger.warning(f"Unknown event type: {event.event_type}")
                self.metrics.events_failed += 1
                return
            
            self.metrics.events_applied += 1
            
            if self.config.log_events:
                logger.debug(f"Event applied: {event.event_type.value}")
        
        except Exception as e:
            logger.error(f"Failed to apply event: {e}")
            self.metrics.events_failed += 1
            self.metrics.errors.append(str(e))
    
    def _apply_key_press(self, event: InputEvent):
        """Apply keyboard key press."""
        keycode = event.payload.get("keycode", "")
        
        # Try exact match first (for special keys like "Return", "Shift", etc.)
        key = self.KEYCODE_MAP.get(keycode)
        
        # If not found, try lowercase version
        if not key:
            key = self.KEYCODE_MAP.get(keycode.lower())
        
        # If still not found, try uppercase version
        if not key:
            key = self.KEYCODE_MAP.get(keycode.upper())
        
        # If still not found, use the keycode as-is (might be single char)
        if not key:
            key = keycode.lower()
        
        try:
            self.keyboard.press(key)
            self._pressed_keys.add(keycode.upper())
            
            if self.config.log_events:
                logger.debug(f"Key pressed: {keycode}")
        
        except Exception as e:
            logger.error(f"Failed to press key {keycode}: {e}")
            raise
    
    def _apply_key_release(self, event: InputEvent):
        """Apply keyboard key release."""
        keycode = event.payload.get("keycode", "")
        
        # Try exact match first (for special keys like "Return", "Shift", etc.)
        key = self.KEYCODE_MAP.get(keycode)
        
        # If not found, try lowercase version
        if not key:
            key = self.KEYCODE_MAP.get(keycode.lower())
        
        # If still not found, try uppercase version
        if not key:
            key = self.KEYCODE_MAP.get(keycode.upper())
        
        # If still not found, use the keycode as-is (might be single char)
        if not key:
            key = keycode.lower()
        
        try:
            self.keyboard.release(key)
            self._pressed_keys.discard(keycode.upper())
            
            if self.config.log_events:
                logger.debug(f"Key released: {keycode}")
        
        except Exception as e:
            logger.error(f"Failed to release key {keycode}: {e}")
            raise
    
    def _apply_mouse_move(self, event: InputEvent):
        """Apply mouse movement."""
        x = event.payload.get("x", 0)
        y = event.payload.get("y", 0)
        
        try:
            self.mouse.position = (x, y)
            self._mouse_position = (x, y)
            
            if self.config.log_events:
                logger.debug(f"Mouse moved to ({x}, {y})")
        
        except Exception as e:
            logger.error(f"Failed to move mouse to ({x}, {y}): {e}")
            raise
    
    def _apply_mouse_click(self, event: InputEvent):
        """Apply mouse click."""
        button_name = event.payload.get("button", "left").lower()
        button = self.BUTTON_MAP.get(button_name, Button.left)
        
        # Get optional click count
        clicks = event.payload.get("clicks", 1)
        
        try:
            self.mouse.click(button, clicks)
            
            if self.config.log_events:
                logger.debug(f"Mouse clicked: {button_name} ({clicks}x)")
        
        except Exception as e:
            logger.error(f"Failed to click mouse: {e}")
            raise
    
    def _apply_mouse_scroll(self, event: InputEvent):
        """Apply mouse scroll."""
        scroll_delta = event.payload.get("scroll_delta", 0)
        
        try:
            self.mouse.scroll(0, scroll_delta)  # x=0 (no horizontal), y=scroll_delta
            
            if self.config.log_events:
                logger.debug(f"Mouse scrolled: delta={scroll_delta}")
        
        except Exception as e:
            logger.error(f"Failed to scroll mouse: {e}")
            raise
    
    def get_metrics(self) -> ApplierMetrics:
        """
        Get applier metrics.
        
        Returns:
            Current applier metrics
        """
        return self.metrics
    
    def reset_metrics(self):
        """Reset applier metrics."""
        self.metrics.reset()
    
    def get_pressed_keys(self) -> set:
        """
        Get currently pressed keys.
        
        Returns:
            Set of keycodes for pressed keys
        """
        return self._pressed_keys.copy()
    
    def get_mouse_position(self) -> tuple:
        """
        Get current mouse position.
        
        Returns:
            Tuple of (x, y) coordinates
        """
        return self._mouse_position
    
    def release_all_keys(self):
        """Release all currently pressed keys."""
        for keycode in list(self._pressed_keys):
            try:
                key = self.KEYCODE_MAP.get(keycode, keycode.lower())
                self.keyboard.release(key)
                self._pressed_keys.discard(keycode)
            except Exception as e:
                logger.warning(f"Failed to release {keycode}: {e}")
