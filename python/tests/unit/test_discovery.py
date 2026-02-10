"""Unit tests for Discovery Service (mocked zeroconf)."""

import pytest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock, patch, call
from src.models.device import Device, DeviceRole, DeviceOS
from src.models.schema import Database
from src.network.discovery import DiscoveryService
import tempfile
import os


@pytest.fixture
def temp_db():
    """Create temporary database for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = Database(db_path)
        db.migrate()
        yield db
        db.close()


@pytest.fixture
def local_device():
    """Create a local device for testing."""
    return Device(
        id=str(uuid.uuid4()),
        mac_address="AA:BB:CC:DD:EE:FF",
        name="TestMaster",
        os=DeviceOS.WINDOWS,
        role=DeviceRole.MASTER,
        ip_address="192.168.1.100",
        port=19999,
        version="1.0.0",
        is_registered=False,
    )


@pytest.fixture
def discovery_service(local_device, temp_db):
    """Create DiscoveryService instance."""
    with patch("src.network.discovery.Zeroconf"):
        service = DiscoveryService(local_device, temp_db)
    return service


class TestDiscoveryServiceInitialization:
    """Test DiscoveryService setup and initialization."""
    
    def test_init_creates_service(self, local_device, temp_db):
        """Test discovery service initialization."""
        with patch("src.network.discovery.Zeroconf"):
            service = DiscoveryService(local_device, temp_db)
        
        assert service.local_device == local_device
        assert service.db == temp_db
        assert service.running == False
        assert len(service.discovered_devices) == 0
        assert len(service.listeners) == 0
    
    def test_service_type_constant(self, discovery_service):
        """Test that SERVICE_TYPE is correct."""
        assert discovery_service.SERVICE_TYPE == "_kms._tcp.local."
    
    def test_offline_threshold_constant(self, discovery_service):
        """Test that OFFLINE_THRESHOLD is 60 seconds."""
        assert discovery_service.OFFLINE_THRESHOLD == 60


class TestServiceRegistration:
    """Test service registration on mDNS."""
    
    @patch("src.network.discovery.ServiceInfo")
    @patch("src.network.discovery.Zeroconf")
    def test_register_service(self, mock_zeroconf_class, mock_service_info_class, 
                              local_device, temp_db):
        """Test service registration on mDNS."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        mock_service_info = MagicMock()
        mock_service_info_class.return_value = mock_service_info
        
        service = DiscoveryService(local_device, temp_db)
        service.zeroconf = mock_zc
        
        service.register_service()
        
        # Verify ServiceInfo was created with correct params
        mock_service_info_class.assert_called_once()
        call_args = mock_service_info_class.call_args
        
        assert call_args[0][0] == "_kms._tcp.local."  # SERVICE_TYPE
        assert "TestMaster._kms._tcp.local." in call_args[1]["name"]
        assert call_args[1]["port"] == 19999
        
        # Verify properties/TXT records
        properties = call_args[1]["properties"]
        assert properties["device_id"] == local_device.id
        assert properties["os"] == "Windows"
        assert properties["version"] == "1.0.0"
        assert properties["role"] == "MASTER"
        
        # Verify zeroconf.register_service was called
        mock_zc.register_service.assert_called_once_with(mock_service_info)
        
        # Verify local device marked as registered
        assert local_device.is_registered == True


class TestDiscoveryServiceLifecycle:
    """Test start/stop lifecycle."""
    
    @patch("src.network.discovery.ServiceBrowser")
    @patch("src.network.discovery.Zeroconf")
    def test_start_service(self, mock_zeroconf_class, mock_browser_class,
                          local_device, temp_db):
        """Test starting discovery service."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        service = DiscoveryService(local_device, temp_db)
        
        with patch.object(service, "register_service"):
            with patch.object(service, "start_browsing"):
                service.start()
        
        assert service.running == True
        assert service.zeroconf == mock_zc
    
    @patch("src.network.discovery.ServiceInfo")
    @patch("src.network.discovery.Zeroconf")
    def test_stop_service(self, mock_zeroconf_class, mock_service_info_class,
                         local_device, temp_db):
        """Test stopping discovery service."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        mock_service_info = MagicMock()
        mock_service_info_class.return_value = mock_service_info
        
        service = DiscoveryService(local_device, temp_db)
        service.zeroconf = mock_zc
        service.running = True
        service.browser = MagicMock()
        
        service.stop()
        
        assert service.running == False
        service.browser.cancel.assert_called_once()
        mock_zc.unregister_service.assert_called_once()
        mock_zc.close.assert_called_once()


class TestDeviceDiscoveryCallbacks:
    """Test device discovery via mDNS callbacks."""
    
    @patch("src.network.discovery.ServiceStateChange")
    @patch("src.network.discovery.Zeroconf")
    def test_on_device_added(self, mock_zeroconf_class, mock_state_change,
                            local_device, temp_db):
        """Test handling device added on mDNS."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        remote_device_id = str(uuid.uuid4())
        
        # Mock service info for discovered device
        mock_service_info = MagicMock()
        mock_service_info.port = 19999
        mock_service_info.parsed_addresses.return_value = ["192.168.1.101"]
        mock_service_info.properties = {
            b"device_id": remote_device_id.encode(),
            b"os": b"Darwin",
            b"version": b"1.0.0",
            b"role": b"CLIENT",
        }
        
        mock_zc.get_service_info.return_value = mock_service_info
        
        service = DiscoveryService(local_device, temp_db)
        service.zeroconf = mock_zc
        
        # Call the callback
        service._on_device_added(mock_zc, "RemoteDevice._kms._tcp.local.")
        
        # Verify device was discovered and stored
        assert remote_device_id in service.discovered_devices
        discovered = service.discovered_devices[remote_device_id]
        assert discovered.name == "RemoteDevice"
        assert discovered.ip_address == "192.168.1.101"
        assert discovered.port == 19999
        assert discovered.is_registered == True
    
    @patch("src.network.discovery.Zeroconf")
    def test_on_device_removed(self, mock_zeroconf_class, local_device, temp_db):
        """Test handling device removed from mDNS."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        service = DiscoveryService(local_device, temp_db)
        
        # Add a device first
        removed_device = Device(
            id=str(uuid.uuid4()),
            name="RemoveMe",
            mac_address="AA:BB:CC:DD:EE:00",
            os=DeviceOS.WINDOWS,
            port=19999,
            is_registered=True,
        )
        service.discovered_devices[removed_device.id] = removed_device
        
        # Remove it
        service._on_device_removed(mock_zc, "RemoveMe._kms._tcp.local.")
        
        # Verify device was removed from discovered_devices
        assert removed_device.id not in service.discovered_devices
        # Verify it's marked as offline in DB
        assert removed_device.is_registered == False
    
    @patch("src.network.discovery.Zeroconf")
    def test_on_device_updated(self, mock_zeroconf_class, local_device, temp_db):
        """Test handling device update on mDNS."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        service = DiscoveryService(local_device, temp_db)
        
        removed_mock = MagicMock()
        added_mock = MagicMock()
        
        service._on_device_removed = removed_mock
        service._on_device_added = added_mock
        
        service._on_device_updated(mock_zc, "SomeDevice._kms._tcp.local.")
        
        removed_mock.assert_called_once()
        added_mock.assert_called_once()


class TestListenerCallbacks:
    """Test listener notification system."""
    
    @patch("src.network.discovery.Zeroconf")
    def test_add_listener(self, mock_zeroconf_class, local_device, temp_db):
        """Test adding listeners."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        service = DiscoveryService(local_device, temp_db)
        callback = Mock()
        
        service.add_listener(callback)
        
        assert callback in service.listeners
    
    @patch("src.network.discovery.Zeroconf")
    def test_listener_called_on_device_added(self, mock_zeroconf_class,
                                            local_device, temp_db):
        """Test listener is notified when device added."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        callback = Mock()
        
        remote_device_id = str(uuid.uuid4())
        mock_service_info = MagicMock()
        mock_service_info.port = 19999
        mock_service_info.parsed_addresses.return_value = ["192.168.1.101"]
        mock_service_info.properties = {
            b"device_id": remote_device_id.encode(),
            b"os": b"Windows",
            b"version": b"1.0.0",
            b"role": b"CLIENT",
        }
        
        mock_zc.get_service_info.return_value = mock_service_info
        
        service = DiscoveryService(local_device, temp_db)
        service.zeroconf = mock_zc
        service.add_listener(callback)
        
        service._on_device_added(mock_zc, "SomeDevice._kms._tcp.local.")
        
        # Verify callback was called with correct args
        callback.assert_called_once()
        event_type, device = callback.call_args[0]
        assert event_type == "device_added"
        assert device.id == remote_device_id


class TestOfflineDetection:
    """Test offline device detection."""
    
    @patch("src.network.discovery.Zeroconf")
    def test_get_discovered_devices(self, mock_zeroconf_class, local_device, temp_db):
        """Test retrieving discovered devices list."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        service = DiscoveryService(local_device, temp_db)
        
        # Add some devices
        dev1 = Device(
            id=str(uuid.uuid4()),
            name="Device1",
            mac_address="AA:BB:CC:DD:EE:01",
            os=DeviceOS.WINDOWS,
            port=19999,
        )
        dev2 = Device(
            id=str(uuid.uuid4()),
            name="Device2",
            mac_address="AA:BB:CC:DD:EE:02",
            os=DeviceOS.MACOS,
            port=19999,
        )
        service.discovered_devices[dev1.id] = dev1
        service.discovered_devices[dev2.id] = dev2
        
        discovered = service.get_discovered()
        
        assert len(discovered) == 2
        assert dev1 in discovered
        assert dev2 in discovered
    
    @patch("src.network.discovery.Zeroconf")
    def test_ignores_own_device(self, mock_zeroconf_class, local_device, temp_db):
        """Test that service ignores its own mDNS broadcast."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        local_device_id = str(uuid.uuid4())
        local_device.id = local_device_id
        
        mock_service_info = MagicMock()
        mock_service_info.port = 19999
        mock_service_info.parsed_addresses.return_value = ["192.168.1.100"]
        mock_service_info.properties = {
            b"device_id": local_device_id.encode(),
            b"os": b"Windows",
            b"version": b"1.0.0",
            b"role": b"MASTER",
        }
        
        mock_zc.get_service_info.return_value = mock_service_info
        
        service = DiscoveryService(local_device, temp_db)
        service.zeroconf = mock_zc
        
        service._on_device_added(mock_zc, "TestMaster._kms._tcp.local.")
        
        # Verify local device was NOT added to discovered_devices
        assert local_device_id not in service.discovered_devices


class TestErrorHandling:
    """Test error handling in discovery."""
    
    @patch("src.network.discovery.Zeroconf")
    def test_handles_missing_service_info(self, mock_zeroconf_class,
                                         local_device, temp_db):
        """Test graceful handling of missing service info."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        mock_zc.get_service_info.return_value = None  # Service info not found
        
        service = DiscoveryService(local_device, temp_db)
        service.zeroconf = mock_zc
        
        # Should not raise, just log warning
        service._on_device_added(mock_zc, "MissingDevice._kms._tcp.local.")
        
        # Device should not be added
        assert len(service.discovered_devices) == 0
    
    @patch("src.network.discovery.Zeroconf")
    def test_handles_malformed_device_id(self, mock_zeroconf_class,
                                        local_device, temp_db):
        """Test handling malformed device ID from TXT records."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        mock_service_info = MagicMock()
        mock_service_info.port = 19999
        mock_service_info.parsed_addresses.return_value = ["192.168.1.101"]
        mock_service_info.properties = {
            b"device_id": b"not-a-uuid",  # Invalid UUID format
            b"os": b"Windows",
            b"version": b"1.0.0",
            b"role": b"CLIENT",
        }
        
        mock_zc.get_service_info.return_value = mock_service_info
        
        service = DiscoveryService(local_device, temp_db)
        service.zeroconf = mock_zc
        
        # Should handle gracefully - Device validation will reject malformed UUID
        service._on_device_added(mock_zc, "Device._kms._tcp.local.")
        
        # Device should NOT be added (validation fails)
        assert len(service.discovered_devices) == 0


class TestConcurrency:
    """Test thread-safety of discovery service."""
    
    @patch("src.network.discovery.Zeroconf")
    def test_multiple_listeners(self, mock_zeroconf_class, local_device, temp_db):
        """Test that multiple listeners are all notified."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()
        
        service = DiscoveryService(local_device, temp_db)
        service.add_listener(callback1)
        service.add_listener(callback2)
        service.add_listener(callback3)
        
        remote_id = str(uuid.uuid4())
        mock_service_info = MagicMock()
        mock_service_info.port = 19999
        mock_service_info.parsed_addresses.return_value = ["192.168.1.50"]
        mock_service_info.properties = {
            b"device_id": remote_id.encode(),
            b"os": b"Windows",
            b"version": b"1.0.0",
            b"role": b"CLIENT",
        }
        
        mock_zc.get_service_info.return_value = mock_service_info
        service.zeroconf = mock_zc
        
        service._on_device_added(mock_zc, "SomeDevice._kms._tcp.local.")
        
        # All callbacks should be called
        assert callback1.call_count == 1
        assert callback2.call_count == 1
        assert callback3.call_count == 1


class TestServiceBrowsingAndRegistration:
    """Test service browsing and registration details."""
    
    @patch("src.network.discovery.ServiceBrowser")
    @patch("src.network.discovery.Zeroconf")
    def test_start_browsing_registers_handler(self, mock_zeroconf_class, mock_browser_class,
                                             local_device, temp_db):
        """Test that start_browsing creates ServiceBrowser with callback."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        service = DiscoveryService(local_device, temp_db)
        service.zeroconf = mock_zc
        
        service.start_browsing()
        
        # Verify ServiceBrowser was created with correct params
        mock_browser_class.assert_called_once()
        call_args = mock_browser_class.call_args
        assert call_args[0][0] == mock_zc
        assert call_args[0][1] == "_kms._tcp.local."
        assert "handlers" in call_args[1]
    
    @patch("src.network.discovery.ServiceInfo")
    @patch("src.network.discovery.Zeroconf")
    def test_register_service_sets_local_device_registered(self, mock_zeroconf_class,
                                                          mock_service_info_class,
                                                          local_device, temp_db):
        """Test that register_service updates local device in DB."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        mock_service_info = MagicMock()
        mock_service_info_class.return_value = mock_service_info
        
        assert local_device.is_registered == False
        
        service = DiscoveryService(local_device, temp_db)
        service.zeroconf = mock_zc
        service.register_service()
        
        assert local_device.is_registered == True
    
    @patch("src.network.discovery.Zeroconf")
    def test_listener_exception_doesnt_block_others(self, mock_zeroconf_class,
                                                   local_device, temp_db):
        """Test that exception in one listener doesn't block others."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        callback_good1 = Mock()
        callback_bad = Mock(side_effect=Exception("Listener error"))
        callback_good2 = Mock()
        
        remote_id = str(uuid.uuid4())
        mock_service_info = MagicMock()
        mock_service_info.port = 19999
        mock_service_info.parsed_addresses.return_value = ["192.168.1.60"]
        mock_service_info.properties = {
            b"device_id": remote_id.encode(),
            b"os": b"Windows",
            b"version": b"1.0.0",
            b"role": b"CLIENT",
        }
        
        mock_zc.get_service_info.return_value = mock_service_info
        
        service = DiscoveryService(local_device, temp_db)
        service.zeroconf = mock_zc
        service.add_listener(callback_good1)
        service.add_listener(callback_bad)
        service.add_listener(callback_good2)
        
        # Should not raise even though callback_bad fails
        service._on_device_added(mock_zc, "Device._kms._tcp.local.")
        
        # Both good callbacks should be called
        assert callback_good1.call_count == 1
        assert callback_good2.call_count == 1


class TestDeviceUpdates:
    """Test device update scenarios."""
    
    @patch("src.network.discovery.Zeroconf")
    def test_update_existing_device_ip(self, mock_zeroconf_class, local_device, temp_db):
        """Test updating existing device with new IP address."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        # Pre-populate device with old IP
        service = DiscoveryService(local_device, temp_db)
        old_device = Device(
            id=str(uuid.uuid4()),
            name="UpdateMe",
            mac_address="AA:BB:CC:DD:EE:01",
            os=DeviceOS.WINDOWS,
            port=19999,
            ip_address="192.168.1.1",
            is_registered=True,
        )
        service.device_repo.create(old_device)
        
        # Now mDNS reports new IP
        new_ip = "192.168.1.200"
        mock_service_info = MagicMock()
        mock_service_info.port = 19999
        mock_service_info.parsed_addresses.return_value = [new_ip]
        mock_service_info.properties = {
            b"device_id": old_device.id.encode(),
            b"os": b"Windows",
            b"version": b"1.0.0",
            b"role": b"CLIENT",
        }
        
        mock_zc.get_service_info.return_value = mock_service_info
        service.zeroconf = mock_zc
        
        service._on_device_added(mock_zc, "UpdateMe._kms._tcp.local.")
        
        # Device should be updated with new IP
        updated = service.discovered_devices[old_device.id]
        assert updated.ip_address == new_ip
    
    @patch("src.network.discovery.Zeroconf")
    def test_device_last_seen_updated_on_discovery(self, mock_zeroconf_class,
                                                   local_device, temp_db):
        """Test that last_seen timestamp is updated when device seen."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        service = DiscoveryService(local_device, temp_db)
        
        remote_id = str(uuid.uuid4())
        old_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        # Pre-create device with old last_seen
        device = Device(
            id=remote_id,
            name="TestDevice",
            mac_address="AA:BB:CC:DD:EE:02",
            os=DeviceOS.WINDOWS,
            port=19999,
            is_registered=True,
            last_seen=old_time,
        )
        service.device_repo.create(device)
        service.discovered_devices[remote_id] = device
        
        # Now discover it again
        mock_service_info = MagicMock()
        mock_service_info.port = 19999
        mock_service_info.parsed_addresses.return_value = ["192.168.1.100"]
        mock_service_info.properties = {
            b"device_id": remote_id.encode(),
            b"os": b"Windows",
            b"version": b"1.0.0",
            b"role": b"CLIENT",
        }
        
        mock_zc.get_service_info.return_value = mock_service_info
        service.zeroconf = mock_zc
        
        service._on_device_added(mock_zc, "TestDevice._kms._tcp.local.")
        
        # last_seen should be updated to recent time
        updated = service.discovered_devices[remote_id]
        assert (datetime.now(timezone.utc) - updated.last_seen).total_seconds() < 5


class TestInvalidEnumHandling:
    """Test handling of invalid enum values from mDNS."""
    
    @patch("src.network.discovery.Zeroconf")
    def test_invalid_os_defaults_to_windows(self, mock_zeroconf_class, local_device, temp_db):
        """Test that invalid OS value defaults to Windows."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        remote_id = str(uuid.uuid4())
        mock_service_info = MagicMock()
        mock_service_info.port = 19999
        mock_service_info.parsed_addresses.return_value = ["192.168.1.100"]
        mock_service_info.properties = {
            b"device_id": remote_id.encode(),
            b"os": b"UnknownOS",  # Invalid
            b"version": b"1.0.0",
            b"role": b"CLIENT",
        }
        
        mock_zc.get_service_info.return_value = mock_service_info
        
        service = DiscoveryService(local_device, temp_db)
        service.zeroconf = mock_zc
        
        service._on_device_added(mock_zc, "Device._kms._tcp.local.")
        
        device = service.discovered_devices[remote_id]
        assert device.os == DeviceOS.WINDOWS
    
    @patch("src.network.discovery.Zeroconf")
    def test_invalid_role_defaults_to_unassigned(self, mock_zeroconf_class,
                                                local_device, temp_db):
        """Test that invalid role defaults to UNASSIGNED."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        remote_id = str(uuid.uuid4())
        mock_service_info = MagicMock()
        mock_service_info.port = 19999
        mock_service_info.parsed_addresses.return_value = ["192.168.1.100"]
        mock_service_info.properties = {
            b"device_id": remote_id.encode(),
            b"os": b"Windows",
            b"version": b"1.0.0",
            b"role": b"UnknownRole",  # Invalid
        }
        
        mock_zc.get_service_info.return_value = mock_service_info
        
        service = DiscoveryService(local_device, temp_db)
        service.zeroconf = mock_zc
        
        service._on_device_added(mock_zc, "Device._kms._tcp.local.")
        
        device = service.discovered_devices[remote_id]
        assert device.role == DeviceRole.UNASSIGNED


class TestNetworkProperties:
    """Test extraction of network properties from mDNS."""
    
    @patch("src.network.discovery.Zeroconf")
    def test_ipv6_address_handling(self, mock_zeroconf_class, local_device, temp_db):
        """Test handling of IPv6 addresses from mDNS."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        remote_id = str(uuid.uuid4())
        ipv6_addr = "2001:db8::1"
        mock_service_info = MagicMock()
        mock_service_info.port = 19999
        mock_service_info.parsed_addresses.return_value = [ipv6_addr]
        mock_service_info.properties = {
            b"device_id": remote_id.encode(),
            b"os": b"Darwin",
            b"version": b"1.0.0",
            b"role": b"CLIENT",
        }
        
        mock_zc.get_service_info.return_value = mock_service_info
        
        service = DiscoveryService(local_device, temp_db)
        service.zeroconf = mock_zc
        
        service._on_device_added(mock_zc, "Device._kms._tcp.local.")
        
        device = service.discovered_devices[remote_id]
        assert device.ip_address == ipv6_addr
    
    @patch("src.network.discovery.Zeroconf")
    def test_missing_addresses_handled(self, mock_zeroconf_class, local_device, temp_db):
        """Test handling of device with no addresses."""
        mock_zc = MagicMock()
        mock_zeroconf_class.return_value = mock_zc
        
        remote_id = str(uuid.uuid4())
        mock_service_info = MagicMock()
        mock_service_info.port = 19999
        mock_service_info.parsed_addresses.return_value = []  # No addresses
        mock_service_info.properties = {
            b"device_id": remote_id.encode(),
            b"os": b"Windows",
            b"version": b"1.0.0",
            b"role": b"CLIENT",
        }
        
        mock_zc.get_service_info.return_value = mock_service_info
        
        service = DiscoveryService(local_device, temp_db)
        service.zeroconf = mock_zc
        
        service._on_device_added(mock_zc, "Device._kms._tcp.local.")
        
        device = service.discovered_devices[remote_id]
        assert device.ip_address is None
