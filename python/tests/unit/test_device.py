"""Tests for Device entity."""

import pytest
from src.models.device import Device, DeviceRole, DeviceOS
from datetime import datetime, timezone
import uuid


class TestDeviceCreation:
    """Test Device entity creation and validation."""
    
    def test_create_device_with_defaults(self):
        """Test creating a device with minimal required fields."""
        device = Device(name="Test Laptop", mac_address="aa:bb:cc:dd:ee:ff")
        assert device.name == "Test Laptop"
        assert device.role == DeviceRole.UNASSIGNED
        assert device.is_registered is False
        assert device.port == 19999
        assert device.os == DeviceOS.WINDOWS
    
    def test_device_auto_generates_uuid(self):
        """Test that device generates UUID if not provided."""
        device = Device(name="Test", mac_address="aa:bb:cc:dd:ee:ff")
        assert device.id is not None
        assert len(device.id) > 0
        assert device.id != Device(name="Test2", mac_address="aa:bb:cc:dd:ee:ff").id
    
    def test_device_creates_timestamps(self):
        """Test that created_at and last_seen are set."""
        device = Device(name="Test", mac_address="aa:bb:cc:dd:ee:ff")
        assert device.created_at is not None
        assert device.last_seen is not None
        assert isinstance(device.created_at, datetime)
    
    def test_device_invalid_uuid(self):
        """Test that invalid UUID raises ValueError."""
        with pytest.raises(ValueError, match="Invalid UUID"):
            Device(
                id="not-a-uuid",
                name="Test",
                mac_address="aa:bb:cc:dd:ee:ff"
            )
    
    def test_device_invalid_mac_address(self):
        """Test that invalid MAC address raises ValueError."""
        with pytest.raises(ValueError, match="Invalid MAC"):
            Device(
                name="Test",
                mac_address="invalid-mac"
            )
    
    def test_device_invalid_name_too_long(self):
        """Test that name > 50 chars raises ValueError."""
        with pytest.raises(ValueError, match="Invalid device name"):
            Device(
                name="x" * 100,
                mac_address="aa:bb:cc:dd:ee:ff"
            )
    
    def test_device_invalid_port(self):
        """Test that invalid port raises ValueError."""
        with pytest.raises(ValueError, match="Invalid port"):
            Device(
                name="Test",
                mac_address="aa:bb:cc:dd:ee:ff",
                port=70000  # Too high (max 65535)
            )
    
    def test_device_invalid_ip_address(self):
        """Test that invalid IP address raises ValueError."""
        with pytest.raises(ValueError, match="Invalid IP address"):
            Device(
                name="Test",
                mac_address="aa:bb:cc:dd:ee:ff",
                ip_address="999.999.999.999"
            )
    
    def test_device_valid_ipv4_address(self):
        """Test that valid IPv4 address is accepted."""
        device = Device(
            name="Test",
            mac_address="aa:bb:cc:dd:ee:ff",
            ip_address="192.168.1.100"
        )
        assert device.ip_address == "192.168.1.100"
    
    def test_device_with_role(self):
        """Test creating device with specific role."""
        device = Device(
            name="Test",
            mac_address="aa:bb:cc:dd:ee:ff",
            role=DeviceRole.MASTER
        )
        assert device.role == DeviceRole.MASTER
    
    def test_device_with_macos(self):
        """Test creating macOS device."""
        device = Device(
            name="MacBook",
            mac_address="aa:bb:cc:dd:ee:ff",
            os=DeviceOS.MACOS
        )
        assert device.os == DeviceOS.MACOS


class TestDeviceToDict:
    """Test Device serialization to dictionary."""
    
    def test_to_dict_includes_all_fields(self):
        """Test that to_dict includes all device fields."""
        device = Device(name="Test", mac_address="aa:bb:cc:dd:ee:ff")
        d = device.to_dict()
        
        assert d["name"] == "Test"
        assert d["os"] == "Windows"
        assert d["role"] == "UNASSIGNED"
        assert d["is_registered"] is False
        assert "created_at" in d
        assert "id" in d
    
    def test_to_dict_includes_ip_address(self):
        """Test that to_dict includes IP address if present."""
        device = Device(
            name="Test",
            mac_address="aa:bb:cc:dd:ee:ff",
            ip_address="192.168.1.100"
        )
        d = device.to_dict()
        assert d["ip_address"] == "192.168.1.100"
    
    def test_to_dict_timestamps_are_iso_format(self):
        """Test that timestamps are in ISO format."""
        device = Device(name="Test", mac_address="aa:bb:cc:dd:ee:ff")
        d = device.to_dict()
        
        # Should be parseable as ISO datetime
        created = datetime.fromisoformat(d["created_at"])
        assert isinstance(created, datetime)


class TestDeviceFromDict:
    """Test Device deserialization from dictionary."""
    
    def test_from_dict_round_trip(self):
        """Test that to_dict -> from_dict preserves all data."""
        device1 = Device(
            name="Test",
            mac_address="aa:bb:cc:dd:ee:ff",
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100"
        )
        d = device1.to_dict()
        device2 = Device.from_dict(d)
        
        assert device2.name == device1.name
        assert device2.role == device1.role
        assert device2.ip_address == device1.ip_address
    
    def test_from_dict_with_minimal_data(self):
        """Test from_dict with only required fields."""
        d = {
            "id": str(uuid.uuid4()),
            "mac_address": "aa:bb:cc:dd:ee:ff",
            "name": "Test",
            "os": "Windows",
            "role": "UNASSIGNED",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
        device = Device.from_dict(d)
        
        assert device.name == "Test"
        assert device.ip_address is None


class TestDeviceEquality:
    """Test Device comparison and identification."""
    
    def test_device_id_is_unique(self):
        """Test that each device gets unique ID."""
        device1 = Device(name="Test1", mac_address="aa:bb:cc:dd:ee:ff")
        device2 = Device(name="Test2", mac_address="aa:bb:cc:dd:ee:ff")
        assert device1.id != device2.id
    
    def test_device_with_same_id_and_different_name(self):
        """Test creating device with explicit ID."""
        device_id = str(uuid.uuid4())
        device = Device(
            id=device_id,
            name="Test",
            mac_address="aa:bb:cc:dd:ee:ff"
        )
        assert device.id == device_id
