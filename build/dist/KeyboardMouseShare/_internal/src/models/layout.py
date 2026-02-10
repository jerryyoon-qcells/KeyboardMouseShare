"""Layout entity representing device physical arrangement and display properties."""

from dataclasses import dataclass
from enum import Enum
import uuid


class Orientation(str, Enum):
    """Display orientation."""
    LANDSCAPE = "LANDSCAPE"
    PORTRAIT = "PORTRAIT"


@dataclass
class Layout:
    """
    Represents the physical layout and display properties of a device.
    
    Attributes:
        id: Unique identifier
        device_id: UUID of associated device
        x: X-coordinate of top-left corner (pixels)
        y: Y-coordinate of top-left corner (pixels)
        width: Display width (pixels)
        height: Display height (pixels)
        dpi_scale: DPI scaling factor (1.0 = 96 DPI, 2.0 = 192 DPI)
        orientation: LANDSCAPE or PORTRAIT
    
    Constraints:
        - x, y must be non-negative
        - width, height must be > 0
        - dpi_scale must be 0.5–4.0
    
    Example:
        # 1080p monitor at (0, 0) with 1x scale
        layout = Layout(
            device_id=my_device.id,
            x=0, y=0,
            width=1920, height=1080,
            dpi_scale=1.0,
            orientation=Orientation.LANDSCAPE
        )
    """
    
    id: str = ""
    device_id: str = ""
    
    x: int = 0
    y: int = 0
    width: int = 1920
    height: int = 1080
    
    dpi_scale: float = 1.0
    orientation: Orientation = Orientation.LANDSCAPE
    
    def __post_init__(self):
        """Validate layout dimensions."""
        from ..utils.validators import validate_coordinate, validate_resolution, validate_dpi_scale
        
        if not validate_coordinate(self.x, self.y):
            raise ValueError(f"Invalid coordinates: ({self.x}, {self.y})")
        
        if not validate_resolution(self.width, self.height):
            raise ValueError(f"Invalid resolution: {self.width}x{self.height}")
        
        if not validate_dpi_scale(self.dpi_scale):
            raise ValueError(f"Invalid DPI scale: {self.dpi_scale}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "dpi_scale": self.dpi_scale,
            "orientation": self.orientation.value,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Layout":
        """Create Layout from dictionary."""
        return cls(
            id=data.get("id", ""),
            device_id=data.get("device_id", ""),
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 1920),
            height=data.get("height", 1080),
            dpi_scale=data.get("dpi_scale", 1.0),
            orientation=Orientation(data.get("orientation", "LANDSCAPE")),
        )
