"""Unit tests for input handlers."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import uuid
from src.input.handler import InputHandler, InputCapture
from src.input.windows import WindowsInputHandler
from src.input.macos import MacOSInputHandler
from src.input import get_input_handler
from src.models.input_event import InputEvent, InputEventType


class TestInputCapture:
    """Test InputCapture dataclass."""
    
    def test_input_capture_creation_valid(self):
        """Test creating valid InputCapture."""
        device_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        event = InputEvent(
            event_type=InputEventType.KEY_PRESS,
            source_device_id=device_id,
            target_device_id=target_id,
            payload={"keycode": "A"},
            timestamp=datetime.now(timezone.utc)
        )
        capture = InputCapture(
            event=event,
            timestamp=datetime.now(timezone.utc),
            success=True
        )
        
        assert capture.event == event
        assert capture.success == True
        assert capture.error is None
    
    def test_input_capture_with_error(self):
        """Test creating InputCapture with error."""
        device_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        event = InputEvent(
            event_type=InputEventType.KEY_PRESS,
            source_device_id=device_id,
            target_device_id=target_id,
            payload={"keycode": "A"},
            timestamp=datetime.now(timezone.utc)
        )
        capture = InputCapture(
            event=event,
            timestamp=datetime.now(timezone.utc),
            success=False,
            error="Test error"
        )
        
        assert capture.success == False
        assert capture.error == "Test error"
    
    def test_input_capture_invalid_event_type(self):
        """Test that InputCapture rejects non-InputEvent objects."""
        with pytest.raises(ValueError, match="event must be InputEvent instance"):
            InputCapture(
                event="not an event",
                timestamp=datetime.now(timezone.utc),
                success=True
            )
    
    def test_input_capture_requires_timezone_aware(self):
        """Test that InputCapture requires timezone-aware timestamp."""
        device_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        event = InputEvent(
            event_type=InputEventType.KEY_PRESS,
            source_device_id=device_id,
            target_device_id=target_id,
            payload={"keycode": "A"},
            timestamp=datetime.now(timezone.utc)
        )
        
        with pytest.raises(ValueError, match="timezone-aware"):
            InputCapture(
                event=event,
                timestamp=datetime.now(),  # No timezone
                success=True
            )


class TestInputHandlerABC:
    """Test InputHandler abstract base class."""
    
    def test_input_handler_requires_callable_callback(self):
        """Test that InputHandler validates callback is callable."""
        with pytest.raises(TypeError, match="callable"):
            # InputHandler is abstract, so we test via a mock
            handler = MagicMock(spec=InputHandler)
            InputHandler.__init__(handler, "device1", "not callable")
    
    def test_input_handler_initialization(self):
        """Test InputHandler can be initialized via subclass."""
        callback = Mock()
        handler = MagicMock(spec=InputHandler)
        handler.device_id = "device1"
        handler.listener_callback = callback
        handler.is_running = False
        
        assert handler.device_id == "device1"
        assert handler.listener_callback == callback
        assert handler.is_running == False
    
    def test_on_input_event_calls_callback(self):
        """Test that on_input_event calls listener callback."""
        device_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        callback = Mock()
        handler = WindowsInputHandler(device_id, callback)
        
        event = InputEvent(
            event_type=InputEventType.KEY_PRESS,
            source_device_id=device_id,
            target_device_id=target_id,
            payload={"keycode": "A"},
            timestamp=datetime.now(timezone.utc)
        )
        handler.on_input_event(event)
        
        callback.assert_called_once_with(event)
    
    def test_on_input_event_validates_event_type(self):
        """Test that on_input_event validates InputEvent type."""
        device_id = str(uuid.uuid4())
        callback = Mock()
        handler = WindowsInputHandler(device_id, callback)
        
        with pytest.raises(ValueError, match="InputEvent"):
            handler.on_input_event("not an event")
    
    def test_on_input_event_handles_callback_exception(self):
        """Test that on_input_event handles callback exceptions gracefully."""
        device_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        callback = Mock(side_effect=Exception("Test error"))
        handler = WindowsInputHandler(device_id, callback)
        
        event = InputEvent(
            event_type=InputEventType.KEY_PRESS,
            source_device_id=device_id,
            target_device_id=target_id,
            payload={"keycode": "A"},
            timestamp=datetime.now(timezone.utc)
        )
        
        # Should not raise - keeps monitoring active
        handler.on_input_event(event)
        callback.assert_called_once_with(event)


class TestWindowsInputHandler:
    """Test Windows input handler."""
    
    def test_windows_handler_initialization(self):
        """Test WindowsInputHandler initialization."""
        device_id = str(uuid.uuid4())
        callback = Mock()
        handler = WindowsInputHandler(device_id, callback)
        
        assert handler.device_id == device_id
        assert handler.listener_callback == callback
        assert handler.is_running == False
        assert handler.keyboard_listener is None
        assert handler.mouse_listener is None
    
    @patch('pynput.keyboard.Listener')
    @patch('pynput.mouse.Listener')
    def test_windows_start_success(self, mock_mouse_listener, mock_keyboard_listener):
        """Test starting Windows input handler with mocked listeners."""
        device_id = str(uuid.uuid4())
        callback = Mock()
        handler = WindowsInputHandler(device_id, callback)
        
        # Mock the listeners
        mock_kb = MagicMock()
        mock_mouse = MagicMock()
        mock_keyboard_listener.return_value = mock_kb
        mock_mouse_listener.return_value = mock_mouse
        
        result = handler.start()
        
        assert result == True
        assert handler.is_running == True
        mock_kb.start.assert_called_once()
        mock_mouse.start.assert_called_once()
    
    @patch('pynput.keyboard.Listener')
    @patch('pynput.mouse.Listener')
    def test_windows_stop_success(self, mock_mouse_listener, mock_keyboard_listener):
        """Test stopping Windows input handler."""
        device_id = str(uuid.uuid4())
        callback = Mock()
        handler = WindowsInputHandler(device_id, callback)
        
        # Mock the listeners
        mock_kb = MagicMock()
        mock_mouse = MagicMock()
        handler.keyboard_listener = mock_kb
        handler.mouse_listener = mock_mouse
        handler.is_running = True
        
        result = handler.stop()
        
        assert result == True
        assert handler.is_running == False
        mock_kb.stop.assert_called_once()
        mock_mouse.stop.assert_called_once()
    
    @patch('pynput.keyboard.Listener')
    @patch('pynput.mouse.Listener')
    def test_windows_is_active(self, mock_mouse_listener, mock_keyboard_listener):
        """Test checking if Windows handler is active."""
        callback = Mock()
        handler = WindowsInputHandler("device1", callback)
        
        # Initially not active
        assert handler.is_active() == False
        
        # Mock active listeners
        mock_kb = MagicMock()
        mock_mouse = MagicMock()
        mock_kb.is_alive.return_value = True
        mock_mouse.is_alive.return_value = True
        
        handler.keyboard_listener = mock_kb
        handler.mouse_listener = mock_mouse
        handler.is_running = True
        
        assert handler.is_active() == True
    
    def test_windows_handler_start_no_pynput(self):
        """Test Windows handler initialization succeeds."""
        device_id = str(uuid.uuid4())
        callback = Mock()
        handler = WindowsInputHandler(device_id, callback)
        
        # Handler should be in stopped state initially
        assert handler.is_running == False

class TestMacOSInputHandler:
    """Test macOS input handler."""
    
    def test_macos_handler_initialization(self):
        """Test MacOSInputHandler initialization."""
        callback = Mock()
        handler = MacOSInputHandler("device1", callback)
        
        assert handler.device_id == "device1"
        assert handler.listener_callback == callback
        assert handler.is_running == False
        assert handler.observer is None
    
    def test_macos_handler_pyobjc_check(self):
        """Test macOS handler checks for PyObjC availability."""
        callback = Mock()
        
        with patch.dict('sys.modules', {'Quartz': None}):
            handler = MacOSInputHandler("device1", callback)
            assert handler._pyobjc_available == False
    
    def test_macos_start_without_pyobjc(self):
        """Test that macOS handler fails to start without PyObjC."""
        callback = Mock()
        handler = MacOSInputHandler("device1", callback)
        handler._pyobjc_available = False
        
        result = handler.start()
        assert result == False
        assert handler.is_running == False
    
    def test_macos_is_active(self):
        """Test checking if macOS handler is active."""
        callback = Mock()
        handler = MacOSInputHandler("device1", callback)
        
        # Initially not active
        assert handler.is_active() == False
        
        # Set as active
        handler.observer = MagicMock()
        handler.is_running = True
        
        assert handler.is_active() == True


class TestInputHandlerFactory:
    """Test get_input_handler factory function."""
    
    @patch('platform.system', return_value='Windows')
    def test_factory_returns_windows_handler(self, mock_system):
        """Test factory returns Windows handler on Windows platform."""
        device_id = str(uuid.uuid4())
        callback = Mock()
        handler = get_input_handler(device_id, callback)
        
        assert isinstance(handler, WindowsInputHandler)
        assert handler.device_id == device_id
    
    @patch('platform.system', return_value='Darwin')
    def test_factory_returns_macos_handler(self, mock_system):
        """Test factory returns macOS handler on macOS platform."""
        device_id = str(uuid.uuid4())
        callback = Mock()
        handler = get_input_handler(device_id, callback)
        
        assert isinstance(handler, MacOSInputHandler)
        assert handler.device_id == device_id
    
    @patch('platform.system', return_value='Linux')
    def test_factory_raises_on_unsupported_platform(self, mock_system):
        """Test factory raises error on unsupported platform."""
        callback = Mock()
        
        with pytest.raises(RuntimeError, match="not supported"):
            get_input_handler("device1", callback)
    
    def test_factory_passes_callback_correctly(self):
        """Test that factory passes callback correctly to handler."""
        device_id = str(uuid.uuid4())
        callback = Mock()
        
        with patch('platform.system', return_value='Windows'):
            handler = get_input_handler(device_id, callback)
            
            assert handler.listener_callback == callback


class TestWindowsEventHandlers:
    """Test Windows-specific event handler methods."""
    
    def test_on_key_press_with_char_attribute(self):
        """Test handling key press with char attribute."""
        device_id = str(uuid.uuid4())
        callback = Mock()
        handler = WindowsInputHandler(device_id, callback)
        
        # Mock key with char attribute
        mock_key = MagicMock()
        mock_key.char = 'A'
        
        handler._on_key_press(mock_key)
        
        callback.assert_called_once()
        event = callback.call_args[0][0]
        assert event.event_type == InputEventType.KEY_PRESS
        assert event.payload["keycode"] == 'A'
    
    def test_on_key_press_with_name_attribute(self):
        """Test handling key press with name attribute (special keys)."""
        device_id = str(uuid.uuid4())
        callback = Mock()
        handler = WindowsInputHandler(device_id, callback)
        
        # Mock special key with name attribute
        mock_key = MagicMock()
        del mock_key.char  # Remove char attribute
        mock_key.name = 'shift'
        
        handler._on_key_press(mock_key)
        
        callback.assert_called_once()
        event = callback.call_args[0][0]
        assert event.payload["keycode"] == 'shift'
    
    def test_on_mouse_move(self):
        """Test handling mouse move event."""
        device_id = str(uuid.uuid4())
        callback = Mock()
        handler = WindowsInputHandler(device_id, callback)
        
        handler._on_mouse_move(100, 200)
        
        callback.assert_called_once()
        event = callback.call_args[0][0]
        assert event.event_type == InputEventType.MOUSE_MOVE
        assert event.payload["x"] == 100
        assert event.payload["y"] == 200
    
    def test_on_mouse_click(self):
        """Test handling mouse click event."""
        device_id = str(uuid.uuid4())
        callback = Mock()
        handler = WindowsInputHandler(device_id, callback)
        
        # Mock button
        mock_button = MagicMock()
        mock_button.name = "left"
        
        handler._on_mouse_click(100, 200, mock_button, True)
        
        callback.assert_called_once()
        event = callback.call_args[0][0]
        assert event.event_type == InputEventType.MOUSE_CLICK
        assert event.payload["button"] == "left"
        assert event.payload["x"] == 100
        assert event.payload["y"] == 200
    
    def test_on_mouse_scroll(self):
        """Test handling mouse scroll event."""
        device_id = str(uuid.uuid4())
        callback = Mock()
        handler = WindowsInputHandler(device_id, callback)
        
        handler._on_mouse_scroll(100, 200, 0, 5)
        
        callback.assert_called_once()
        event = callback.call_args[0][0]
        assert event.event_type == InputEventType.MOUSE_SCROLL
        assert event.payload["scroll_delta"] == 5
