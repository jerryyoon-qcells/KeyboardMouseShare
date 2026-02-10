"""Integration tests for Discovery Service (minimal - real mDNS is environment-dependent)."""

import pytest
import uuid
from src.models.device import Device, DeviceRole, DeviceOS
from src.models.schema import Database
from src.network.discovery import DiscoveryService
import tempfile
import os
from unittest.mock import patch


@pytest.fixture
def temp_db_integration():
    """Create temporary database for integration tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "integration_test.db")
        db = Database(db_path)
        db.migrate()
        yield db
        db.close()


class TestDiscoveryServiceIntegration:
    """Integration tests for discovery service."""
    
    @patch("src.network.discovery.ServiceInfo")
    def test_service_lifecycle_no_network(self, mock_service_info_class, temp_db_integration):
        """Test discovery service lifecycle without actual network."""
        local_device = Device(
            id=str(uuid.uuid4()),
            mac_address="AA:BB:CC:DD:EE:FF",
            name="TestDevice",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="127.0.0.1",
            port=19999,
        )
        
        service = DiscoveryService(local_device, temp_db_integration)
        
        assert service.running == False
        assert len(service.discovered_devices) == 0
        assert service.zeroconf is None
        
        with patch("src.network.discovery.Zeroconf"):
            with patch("src.network.discovery.ServiceBrowser"):
                service.start()
        
        assert service.running == True
        assert service.zeroconf is not None
        assert service.browser is not None
    
    def test_listener_registration_and_callback(self, temp_db_integration):
        """Test listener registration."""
        local_device = Device(
            id=str(uuid.uuid4()),
            mac_address="AA:BB:CC:DD:EE:FF",
            name="TestMaster",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            port=19999,
        )
        
        service = DiscoveryService(local_device, temp_db_integration)
        
        # Track callback invocations
        callbacks_received = []
        
        def my_listener(event_type, device):
            callbacks_received.append((event_type, device.name))
        
        service.add_listener(my_listener)
        
        assert len(service.listeners) == 1
        assert my_listener in service.listeners
    
    def test_database_persistence(self, temp_db_integration):
        """Test that discovered devices persist in database."""
        local_device = Device(
            id=str(uuid.uuid4()),
            mac_address="AA:BB:CC:DD:EE:FF",
            name="TestMaster",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            port=19999,
        )
        
        service = DiscoveryService(local_device, temp_db_integration)
        
        # Manually add a device to discovered list (simulating discovery)
        remote_device = Device(
            id=str(uuid.uuid4()),
            mac_address="FF:EE:DD:CC:BB:AA",
            name="RemoteDevice",
            os=DeviceOS.MACOS,
            role=DeviceRole.CLIENT,
            ip_address="192.168.1.100",
            port=19999,
            is_registered=True,
        )
        
        service.device_repo.create(remote_device)
        service.discovered_devices[remote_device.id] = remote_device
        
        # Verify it's in the database
        retrieved = service.device_repo.read(remote_device.id)
        assert retrieved is not None
        assert retrieved.name == "RemoteDevice"
        assert retrieved.ip_address == "192.168.1.100"
    
    def test_get_discovered_returns_current_list(self, temp_db_integration):
        """Test that get_discovered returns the discovery snapshot."""
        local_device = Device(
            id=str(uuid.uuid4()),
            mac_address="AA:BB:CC:DD:EE:FF",
            name="TestMaster",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            port=19999,
        )
        
        service = DiscoveryService(local_device, temp_db_integration)
        
        # Initially empty
        assert len(service.get_discovered()) == 0
        
        # Add some devices
        for i in range(3):
            device = Device(
                id=str(uuid.uuid4()),
                mac_address=f"AA:BB:CC:DD:EE:{i:02X}",
                name=f"Device{i}",
                os=DeviceOS.WINDOWS,
                port=19999,
            )
            service.discovered_devices[device.id] = device
        
        # Should have 3 discovered devices
        discovered = service.get_discovered()
        assert len(discovered) == 3
        assert all(isinstance(d, Device) for d in discovered)


class TestOfflineDetectionIntegration:
    """Integration tests for offline detection."""
    
    @patch("src.network.discovery.ServiceInfo")
    def test_offline_thread_starts(self, mock_service_info_class, temp_db_integration):
        """Test that offline detection thread starts correctly."""
        import time
        
        local_device = Device(
            id=str(uuid.uuid4()),
            mac_address="AA:BB:CC:DD:EE:FF",
            name="TestMaster",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            port=19999,
        )
        
        service = DiscoveryService(local_device, temp_db_integration)
        
        with patch("src.network.discovery.Zeroconf"):
            with patch("src.network.discovery.ServiceBrowser"):
                service.start()
        
        # Thread should be running
        assert service._offline_thread is not None
        assert service._offline_thread.is_alive()
        
        # Cleanup
        service.stop()
        time.sleep(0.1)  # Let thread shutdown
        assert service.running == False


class TestThreadSafety:
    """Test thread safety of discovery service."""
    
    def test_concurrent_device_access(self, temp_db_integration):
        """Test that concurrent access doesn't corrupt state."""
        import threading
        
        local_device = Device(
            id=str(uuid.uuid4()),
            mac_address="AA:BB:CC:DD:EE:FF",
            name="TestMaster",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            port=19999,
        )
        
        service = DiscoveryService(local_device, temp_db_integration)
        
        errors = []
        
        def add_device():
            try:
                for i in range(5):
                    device = Device(
                        id=str(uuid.uuid4()),
                        mac_address=f"AA:BB:CC:DD:EE:{i:02X}",
                        name=f"Device{i}",
                        os=DeviceOS.WINDOWS,
                        port=19999,
                    )
                    service.discovered_devices[device.id] = device
            except Exception as e:
                errors.append(str(e))
        
        def get_devices():
            try:
                for _ in range(5):
                    devices = service.get_discovered()
                    assert isinstance(devices, list)
            except Exception as e:
                errors.append(str(e))
        
        # Run concurrent operations
        threads = [
            threading.Thread(target=add_device),
            threading.Thread(target=add_device),
            threading.Thread(target=get_devices),
            threading.Thread(target=get_devices),
        ]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # Should have no errors
        assert len(errors) == 0
