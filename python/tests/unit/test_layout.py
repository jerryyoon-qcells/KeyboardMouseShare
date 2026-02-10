"""Tests for Layout entity."""

import pytest
from src.models.layout import Layout, Orientation


class TestLayoutCreation:
    """Test Layout entity creation and validation."""
    
    def test_create_layout_with_defaults(self):
        """Test creating layout with default values."""
        layout = Layout(device_id="abc123")
        
        assert layout.device_id == "abc123"
        assert layout.x == 0
        assert layout.y == 0
        assert layout.width == 1920
        assert layout.height == 1080
        assert layout.dpi_scale == 1.0
        assert layout.orientation == Orientation.LANDSCAPE
    
    def test_create_landscape_1080p(self):
        """Test creating a 1080p landscape layout."""
        layout = Layout(
            device_id="dev-id",
            width=1920, height=1080,
            orientation=Orientation.LANDSCAPE
        )
        assert layout.width == 1920
        assert layout.height == 1080
        assert layout.orientation == Orientation.LANDSCAPE
    
    def test_create_portrait_layout(self):
        """Test creating a portrait layout."""
        layout = Layout(
            device_id="dev-id",
            width=1080, height=1920,
            orientation=Orientation.PORTRAIT
        )
        assert layout.orientation == Orientation.PORTRAIT
    
    def test_create_layout_with_offset(self):
        """Test creating layout at non-zero coordinates."""
        layout = Layout(
            device_id="dev-id",
            x=1920, y=0,
            width=1920, height=1080
        )
        assert layout.x == 1920
        assert layout.y == 0
    
    def test_create_layout_with_dpi_scaling(self):
        """Test creating layout with Retina/4K scaling."""
        layout = Layout(
            device_id="dev-id",
            dpi_scale=2.0  # Retina macOS
        )
        assert layout.dpi_scale == 2.0
    
    def test_layout_invalid_negative_coordinates(self):
        """Test that negative coordinates raise ValueError."""
        with pytest.raises(ValueError, match="Invalid coordinates"):
            Layout(device_id="dev-id", x=-100, y=0)
    
    def test_layout_invalid_resolution_too_small(self):
        """Test that resolution < 480 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid resolution"):
            Layout(device_id="dev-id", width=320, height=240)
    
    def test_layout_invalid_dpi_too_low(self):
        """Test that DPI scale < 0.5 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid DPI scale"):
            Layout(device_id="dev-id", dpi_scale=0.25)
    
    def test_layout_invalid_dpi_too_high(self):
        """Test that DPI scale > 4.0 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid DPI scale"):
            Layout(device_id="dev-id", dpi_scale=5.0)
    
    def test_layout_valid_dpi_boundaries(self):
        """Test valid DPI scale boundaries."""
        layout_low = Layout(device_id="dev-id", dpi_scale=0.5)
        assert layout_low.dpi_scale == 0.5
        
        layout_high = Layout(device_id="dev-id", dpi_scale=4.0)
        assert layout_high.dpi_scale == 4.0


class TestLayoutToDict:
    """Test Layout serialization."""
    
    def test_to_dict_includes_all_fields(self):
        """Test that to_dict includes all fields."""
        layout = Layout(
            device_id="dev-id",
            x=100, y=200,
            width=1920, height=1080,
            dpi_scale=1.5
        )
        d = layout.to_dict()
        
        assert d["device_id"] == "dev-id"
        assert d["x"] == 100
        assert d["y"] == 200
        assert d["width"] == 1920
        assert d["height"] == 1080
        assert d["dpi_scale"] == 1.5
        assert d["orientation"] == "LANDSCAPE"


class TestLayoutFromDict:
    """Test Layout deserialization."""
    
    def test_from_dict_round_trip(self):
        """Test that to_dict -> from_dict preserves data."""
        layout1 = Layout(
            device_id="dev-id",
            x=100, y=200,
            width=2560, height=1440,
            dpi_scale=2.0
        )
        d = layout1.to_dict()
        layout2 = Layout.from_dict(d)
        
        assert layout2.device_id == layout1.device_id
        assert layout2.x == layout1.x
        assert layout2.y == layout1.y
        assert layout2.width == layout1.width
        assert layout2.height == layout1.height
        assert layout2.dpi_scale == layout1.dpi_scale


class TestLayoutOrientations:
    """Test layout orientations."""
    
    def test_all_orientations(self):
        """Test both landscape and portrait."""
        for orientation in Orientation:
            layout = Layout(device_id="dev-id", orientation=orientation)
            assert layout.orientation == orientation
