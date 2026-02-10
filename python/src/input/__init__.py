"""Input capture abstraction layer."""

from src.input.handler import InputHandler, InputCapture
from src.input.windows import WindowsInputHandler
from src.input.macos import MacOSInputHandler
import platform
from typing import Callable


def get_input_handler(device_id: str, listener_callback: Callable) -> InputHandler:
    """
    Factory function to get the appropriate input handler for the current platform.
    
    Args:
        device_id: Unique identifier for this device
        listener_callback: Function to call when input is captured
    
    Returns:
        Platform-specific InputHandler instance
    
    Raises:
        RuntimeError: If platform is not supported
    """
    system = platform.system()
    
    if system == "Windows":
        return WindowsInputHandler(device_id, listener_callback)
    elif system == "Darwin":
        return MacOSInputHandler(device_id, listener_callback)
    else:
        raise RuntimeError(f"Input handler not supported for platform: {system}")


__all__ = [
    "InputHandler",
    "InputCapture",
    "WindowsInputHandler",
    "MacOSInputHandler",
    "get_input_handler",
]
