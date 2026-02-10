"""Tests for Connection entity."""

import pytest
from src.models.connection import Connection, ConnectionStatus
import uuid


class TestConnectionCreation:
    """Test Connection entity creation and validation."""
    
    def test_create_connection(self):
        """Test creating a connection with valid device IDs."""
        master_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        conn = Connection(master_device_id=master_id, client_device_id=client_id)
        
        assert conn.master_device_id == master_id
        assert conn.client_device_id == client_id
        assert conn.status == ConnectionStatus.CONNECTING
        assert conn.input_event_counter == 0
    
    def test_connection_auto_generates_id(self):
        """Test that connection generates unique ID."""
        master_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        
        conn1 = Connection(master_device_id=master_id, client_device_id=client_id)
        conn2 = Connection(master_device_id=master_id, client_device_id=client_id)
        
        assert conn1.id != conn2.id
    
    def test_connection_same_device_raises(self):
        """Test that master == client raises ValueError."""
        device_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="must be different"):
            Connection(master_device_id=device_id, client_device_id=device_id)
    
    def test_connection_invalid_master_uuid_raises(self):
        """Test that invalid master UUID raises ValueError."""
        with pytest.raises(ValueError, match="Invalid master"):
            Connection(
                master_device_id="invalid",
                client_device_id=str(uuid.uuid4())
            )
    
    def test_connection_invalid_client_uuid_raises(self):
        """Test that invalid client UUID raises ValueError."""
        with pytest.raises(ValueError, match="Invalid client"):
            Connection(
                master_device_id=str(uuid.uuid4()),
                client_device_id="invalid"
            )
    
    def test_connection_with_status(self):
        """Test creating connection with specific status."""
        master_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        
        conn = Connection(
            master_device_id=master_id,
            client_device_id=client_id,
            status=ConnectionStatus.CONNECTED
        )
        assert conn.status == ConnectionStatus.CONNECTED
    
    def test_connection_creates_timestamps(self):
        """Test that created_at and last_heartbeat are set."""
        master_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        
        conn = Connection(master_device_id=master_id, client_device_id=client_id)
        
        assert conn.created_at is not None
        assert conn.last_heartbeat is not None


class TestConnectionToDict:
    """Test Connection serialization to dictionary."""
    
    def test_to_dict_includes_all_fields(self):
        """Test that to_dict includes all connection fields."""
        master_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        
        conn = Connection(
            master_device_id=master_id,
            client_device_id=client_id,
            status=ConnectionStatus.CONNECTED
        )
        d = conn.to_dict()
        
        assert d["master_device_id"] == master_id
        assert d["client_device_id"] == client_id
        assert d["status"] == "CONNECTED"
        assert "created_at" in d
    
    def test_to_dict_with_certificate(self):
        """Test serialization with TLS certificate."""
        master_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        cert = "-----BEGIN CERTIFICATE-----\nMIIC..."
        
        conn = Connection(
            master_device_id=master_id,
            client_device_id=client_id,
            tls_certificate=cert
        )
        d = conn.to_dict()
        
        assert d["tls_certificate"] == cert


class TestConnectionFromDict:
    """Test Connection deserialization from dictionary."""
    
    def test_from_dict_round_trip(self):
        """Test that to_dict -> from_dict preserves all data."""
        master_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        
        conn1 = Connection(
            master_device_id=master_id,
            client_device_id=client_id,
            status=ConnectionStatus.CONNECTED,
            input_event_counter=42
        )
        d = conn1.to_dict()
        conn2 = Connection.from_dict(d)
        
        assert conn2.master_device_id == conn1.master_device_id
        assert conn2.client_device_id == conn1.client_device_id
        assert conn2.status == conn1.status
        assert conn2.input_event_counter == 42


class TestConnectionStatuses:
    """Test various connection status values."""
    
    def test_all_connection_statuses(self):
        """Test all valid connection statuses."""
        master_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        
        for status in ConnectionStatus:
            conn = Connection(
                master_device_id=master_id,
                client_device_id=client_id,
                status=status
            )
            assert conn.status == status
