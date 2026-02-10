"""Tests for repository implementations."""

import pytest
import tempfile
import uuid
from pathlib import Path
from datetime import datetime

from src.models.schema import Database
from src.models.repositories import (
    DeviceRepository, ConnectionRepository, LayoutRepository, InputEventRepository
)
from src.models.device import Device, DeviceRole, DeviceOS
from src.models.connection import Connection, ConnectionStatus
from src.models.layout import Layout, Orientation
from src.models.input_event import InputEvent, InputEventType


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path=db_path)
        db.connect()
        db.migrate()
        yield db
        db.close()


class TestDeviceRepository:
    """Test DeviceRepository CRUD operations."""
    
    def test_create_device(self, temp_db):
        """Test creating a device."""
        repo = DeviceRepository(temp_db)
        device = Device(name="Test", mac_address="aa:bb:cc:dd:ee:ff")
        
        created = repo.create(device)
        
        assert created.id == device.id
        assert created.name == device.name
    
    def test_read_device(self, temp_db):
        """Test reading a device by ID."""
        repo = DeviceRepository(temp_db)
        device = Device(name="Test", mac_address="aa:bb:cc:dd:ee:ff")
        repo.create(device)
        
        read = repo.read(device.id)
        
        assert read is not None
        assert read.name == device.name
        assert read.mac_address == device.mac_address
    
    def test_read_nonexistent_device_returns_none(self, temp_db):
        """Test that reading nonexistent device returns None."""
        repo = DeviceRepository(temp_db)
        
        result = repo.read("nonexistent-id")
        
        assert result is None
    
    def test_list_all_devices(self, temp_db):
        """Test listing all devices."""
        repo = DeviceRepository(temp_db)
        
        dev1 = Device(name="Device1", mac_address="aa:bb:cc:dd:ee:01")
        dev2 = Device(name="Device2", mac_address="aa:bb:cc:dd:ee:02")
        
        repo.create(dev1)
        repo.create(dev2)
        
        all_devices = repo.list_all()
        
        assert len(all_devices) == 2
        assert any(d.name == "Device1" for d in all_devices)
        assert any(d.name == "Device2" for d in all_devices)
    
    def test_list_registered_devices(self, temp_db):
        """Test listing only registered devices."""
        repo = DeviceRepository(temp_db)
        
        dev1 = Device(name="Device1", mac_address="aa:bb:cc:dd:ee:01", is_registered=True)
        dev2 = Device(name="Device2", mac_address="aa:bb:cc:dd:ee:02", is_registered=False)
        
        repo.create(dev1)
        repo.create(dev2)
        
        registered = repo.list_registered()
        
        assert len(registered) == 1
        assert registered[0].name == "Device1"
    
    def test_update_device(self, temp_db):
        """Test updating a device."""
        repo = DeviceRepository(temp_db)
        device = Device(name="Test", mac_address="aa:bb:cc:dd:ee:ff")
        repo.create(device)
        
        device.name = "Updated"
        device.role = DeviceRole.MASTER
        updated = repo.update(device)
        
        read = repo.read(device.id)
        assert read.name == "Updated"
        assert read.role == DeviceRole.MASTER
    
    def test_delete_device(self, temp_db):
        """Test deleting a device."""
        repo = DeviceRepository(temp_db)
        device = Device(name="Test", mac_address="aa:bb:cc:dd:ee:ff")
        repo.create(device)
        
        deleted = repo.delete(device.id)
        
        assert deleted is True
        assert repo.read(device.id) is None
    
    def test_device_round_trip(self, temp_db):
        """Test creating, reading, and verifying device equality."""
        repo = DeviceRepository(temp_db)
        device = Device(
            name="Test",
            mac_address="aa:bb:cc:dd:ee:ff",
            role=DeviceRole.MASTER,
            os=DeviceOS.MACOS,
            ip_address="192.168.1.100"
        )
        repo.create(device)
        
        read = repo.read(device.id)
        
        assert read.name == device.name
        assert read.role == device.role
        assert read.os == device.os
        assert read.ip_address == device.ip_address


class TestConnectionRepository:
    """Test ConnectionRepository CRUD operations."""
    
    def test_create_connection(self, temp_db):
        """Test creating a connection."""
        repo = ConnectionRepository(temp_db)
        device_repo = DeviceRepository(temp_db)
        
        # Create two devices first
        master = Device(name="Master", mac_address="aa:bb:cc:dd:ee:01")
        client = Device(name="Client", mac_address="aa:bb:cc:dd:ee:02")
        device_repo.create(master)
        device_repo.create(client)
        
        # Create connection
        conn = Connection(
            master_device_id=master.id,
            client_device_id=client.id
        )
        created = repo.create(conn)
        
        assert created.id == conn.id
    
    def test_read_connection(self, temp_db):
        """Test reading a connection."""
        repo = ConnectionRepository(temp_db)
        device_repo = DeviceRepository(temp_db)
        
        master = Device(name="Master", mac_address="aa:bb:cc:dd:ee:01")
        client = Device(name="Client", mac_address="aa:bb:cc:dd:ee:02")
        device_repo.create(master)
        device_repo.create(client)
        
        conn = Connection(
            master_device_id=master.id,
            client_device_id=client.id,
            status=ConnectionStatus.CONNECTED
        )
        repo.create(conn)
        
        read = repo.read(conn.id)
        
        assert read is not None
        assert read.status == ConnectionStatus.CONNECTED
    
    def test_list_active_connections(self, temp_db):
        """Test listing only active connections."""
        repo = ConnectionRepository(temp_db)
        device_repo = DeviceRepository(temp_db)
        
        master = Device(name="Master", mac_address="aa:bb:cc:dd:ee:01")
        client = Device(name="Client", mac_address="aa:bb:cc:dd:ee:02")
        device_repo.create(master)
        device_repo.create(client)
        
        conn1 = Connection(
            master_device_id=master.id,
            client_device_id=client.id,
            status=ConnectionStatus.CONNECTED
        )
        conn2 = Connection(
            master_device_id=master.id,
            client_device_id=client.id.replace('a', 'b'),  # Different client
            status=ConnectionStatus.DISCONNECTED
        )
        
        # Need second client for second connection
        client2 = Device(name="Client2", mac_address="aa:bb:cc:dd:ee:03")
        device_repo.create(client2)
        conn2.client_device_id = client2.id
        
        repo.create(conn1)
        repo.create(conn2)
        
        active = repo.list_active()
        
        assert len(active) == 1
        assert active[0].status == ConnectionStatus.CONNECTED
    
    def test_update_connection(self, temp_db):
        """Test updating a connection."""
        repo = ConnectionRepository(temp_db)
        device_repo = DeviceRepository(temp_db)
        
        master = Device(name="Master", mac_address="aa:bb:cc:dd:ee:01")
        client = Device(name="Client", mac_address="aa:bb:cc:dd:ee:02")
        device_repo.create(master)
        device_repo.create(client)
        
        conn = Connection(
            master_device_id=master.id,
            client_device_id=client.id,
            status=ConnectionStatus.CONNECTING
        )
        repo.create(conn)
        
        conn.status = ConnectionStatus.CONNECTED
        conn.input_event_counter = 42
        updated = repo.update(conn)
        
        read = repo.read(conn.id)
        assert read.status == ConnectionStatus.CONNECTED
        assert read.input_event_counter == 42


class TestLayoutRepository:
    """Test LayoutRepository CRUD operations."""
    
    def test_create_layout(self, temp_db):
        """Test creating a layout."""
        repo = LayoutRepository(temp_db)
        device_repo = DeviceRepository(temp_db)
        
        device = Device(name="Test", mac_address="aa:bb:cc:dd:ee:ff")
        device_repo.create(device)
        
        layout = Layout(device_id=device.id, width=1920, height=1080)
        created = repo.create(layout)
        
        assert created.device_id == device.id
        assert created.width == 1920
    
    def test_read_layout(self, temp_db):
        """Test reading a layout."""
        repo = LayoutRepository(temp_db)
        device_repo = DeviceRepository(temp_db)
        
        device = Device(name="Test", mac_address="aa:bb:cc:dd:ee:ff")
        device_repo.create(device)
        
        layout = Layout(device_id=device.id)
        repo.create(layout)
        
        read = repo.read(layout.id)
        
        assert read is not None
        assert read.device_id == device.id
    
    def test_read_layout_by_device(self, temp_db):
        """Test reading layout by device ID."""
        repo = LayoutRepository(temp_db)
        device_repo = DeviceRepository(temp_db)
        
        device = Device(name="Test", mac_address="aa:bb:cc:dd:ee:ff")
        device_repo.create(device)
        
        layout = Layout(device_id=device.id)
        repo.create(layout)
        
        read = repo.read_by_device(device.id)
        
        assert read is not None
        assert read.device_id == device.id
    
    def test_update_layout(self, temp_db):
        """Test updating a layout."""
        repo = LayoutRepository(temp_db)
        device_repo = DeviceRepository(temp_db)
        
        device = Device(name="Test", mac_address="aa:bb:cc:dd:ee:ff")
        device_repo.create(device)
        
        layout = Layout(device_id=device.id, dpi_scale=1.0)
        repo.create(layout)
        
        layout.dpi_scale = 2.0
        layout.width = 2560
        updated = repo.update(layout)
        
        read = repo.read(layout.id)
        assert read.dpi_scale == 2.0
        assert read.width == 2560


class TestInputEventRepository:
    """Test InputEventRepository CRUD operations."""
    
    def test_create_event(self, temp_db):
        """Test creating an input event."""
        repo = InputEventRepository(temp_db)
        device_repo = DeviceRepository(temp_db)
        
        source = Device(name="Source", mac_address="aa:bb:cc:dd:ee:01")
        target = Device(name="Target", mac_address="aa:bb:cc:dd:ee:02")
        device_repo.create(source)
        device_repo.create(target)
        
        event = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=source.id,
            target_device_id=target.id,
            payload={"x": 100, "y": 200}
        )
        created = repo.create(event)
        
        assert created.id == event.id
    
    def test_read_event(self, temp_db):
        """Test reading an event."""
        repo = InputEventRepository(temp_db)
        device_repo = DeviceRepository(temp_db)
        
        source = Device(name="Source", mac_address="aa:bb:cc:dd:ee:01")
        target = Device(name="Target", mac_address="aa:bb:cc:dd:ee:02")
        device_repo.create(source)
        device_repo.create(target)
        
        event = InputEvent(
            event_type=InputEventType.KEY_PRESS,
            source_device_id=source.id,
            target_device_id=target.id,
            payload={"keycode": "A"}
        )
        repo.create(event)
        
        read = repo.read(event.id)
        
        assert read is not None
        assert read.event_type == InputEventType.KEY_PRESS
        assert read.payload["keycode"] == "A"
    
    def test_list_by_connection(self, temp_db):
        """Test listing events by connection pair."""
        repo = InputEventRepository(temp_db)
        device_repo = DeviceRepository(temp_db)
        
        source = Device(name="Source", mac_address="aa:bb:cc:dd:ee:01")
        target = Device(name="Target", mac_address="aa:bb:cc:dd:ee:02")
        device_repo.create(source)
        device_repo.create(target)
        
        event1 = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=source.id,
            target_device_id=target.id,
            payload={"x": 0, "y": 0}
        )
        event2 = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=source.id,
            target_device_id=target.id,
            payload={"x": 100, "y": 100}
        )
        
        repo.create(event1)
        repo.create(event2)
        
        events = repo.list_by_connection(source.id, target.id)
        
        assert len(events) == 2
    
    def test_delete_event(self, temp_db):
        """Test deleting an event."""
        repo = InputEventRepository(temp_db)
        device_repo = DeviceRepository(temp_db)
        
        source = Device(name="Source", mac_address="aa:bb:cc:dd:ee:01")
        target = Device(name="Target", mac_address="aa:bb:cc:dd:ee:02")
        device_repo.create(source)
        device_repo.create(target)
        
        event = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            source_device_id=source.id,
            target_device_id=target.id,
            payload={"x": 0, "y": 0}
        )
        repo.create(event)
        
        deleted = repo.delete(event.id)
        
        assert deleted is True
        assert repo.read(event.id) is None
