"""mDNS-based device discovery service using zeroconf."""

from typing import Callable, List, Optional, Dict
from datetime import datetime, timezone
from zeroconf import ServiceInfo, ServiceBrowser, Zeroconf, ServiceStateChange
import logging
import threading
import time

from ..models.device import Device, DeviceRole, DeviceOS
from ..models.repositories import DeviceRepository
from ..models.schema import Database


logger = logging.getLogger(__name__)


class DiscoveryService:
    """
    Manages device discovery via mDNS (Multicast DNS).
    
    Responsibilities:
    1. Register this device on mDNS so others can find it
    2. Browse for other devices on the LAN
    3. Notify app when devices appear/disappear
    4. Detect offline devices (60+ second timeout)
    """
    
    SERVICE_TYPE = "_kms._tcp.local."
    OFFLINE_THRESHOLD = 60  # seconds
    
    def __init__(self, local_device: Device, db: Database):
        """
        Initialize discovery service.
        
        Args:
            local_device: This device's Device entity (must have id, name, os, port)
            db: Database instance for persisting discovered devices
        """
        self.local_device = local_device
        self.db = db
        self.device_repo = DeviceRepository(db)
        
        self.zeroconf: Optional[Zeroconf] = None
        self.browser: Optional[ServiceBrowser] = None
        self.discovered_devices: Dict[str, Device] = {}
        
        self.listeners: List[Callable] = []
        self.running = False
        
        self._offline_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def add_listener(self, callback: Callable[[str, Device], None]):
        """
        Register a callback for device events.
        
        Callback signature: callback(event_type: str, device: Device)
        Event types: "device_added", "device_removed", "device_offline"
        
        Args:
            callback: Function to call when devices are discovered/removed/offline
        """
        self.listeners.append(callback)
    
    def start(self):
        """Start discovery: register this device + browse for others."""
        logger.info(f"Starting discovery service for {self.local_device.name}")
        
        self.running = True
        self.zeroconf = Zeroconf()
        
        # Step 1: Register this device on mDNS
        self.register_service()
        
        # Step 2: Start browsing for other devices
        self.start_browsing()
        
        # Step 3: Start background thread for offline detection
        self._start_offline_detection()
    
    def register_service(self):
        """Register this device's service on mDNS."""
        logger.debug(f"Registering {self.local_device.name} on mDNS")
        
        service_name = f"{self.local_device.name}._kms._tcp.local."
        
        service_info = ServiceInfo(
            self.SERVICE_TYPE,
            name=service_name,
            port=self.local_device.port,
            properties={
                "device_id": self.local_device.id,
                "os": self.local_device.os.value,
                "version": self.local_device.version,
                "role": self.local_device.role.value,
            }
        )
        
        if self.zeroconf:
            self.zeroconf.register_service(service_info)
        
        # Update local device as registered
        self.local_device.is_registered = True
        self.device_repo.update(self.local_device)
        
        logger.info(f"Registered {self.local_device.name} on mDNS at port {self.local_device.port}")
    
    def start_browsing(self):
        """Start listening for mDNS services."""
        logger.debug("Starting mDNS browser")
        if self.zeroconf:
            self.browser = ServiceBrowser(
                self.zeroconf,
                self.SERVICE_TYPE,
                handlers=[self.on_service_state_change]
            )
    
    def on_service_state_change(self, zeroconf, service_type: str, name: str, state_change):
        """
        Callback invoked when mDNS detects service add/remove/update.
        
        Args:
            zeroconf: Zeroconf instance
            service_type: Service type that changed
            name: Service instance name
            state_change: Type of change (Added, Removed, Updated)
        """
        logger.debug(f"Service state change: {name} -> {state_change}")
        
        if state_change == ServiceStateChange.Added:
            self._on_device_added(zeroconf, name)
        elif state_change == ServiceStateChange.Removed:
            self._on_device_removed(zeroconf, name)
        elif state_change == ServiceStateChange.Updated:
            self._on_device_updated(zeroconf, name)
    
    def _on_device_added(self, zeroconf, name: str):
        """
        Handle device appearance on mDNS.
        
        Args:
            zeroconf: Zeroconf instance
            name: Service instance name (e.g., "Device._kms._tcp.local.")
        """
        logger.debug(f"Device added on mDNS: {name}")
        
        try:
            # Fetch service info from mDNS
            info = zeroconf.get_service_info(self.SERVICE_TYPE, name)
            if not info:
                logger.warning(f"Could not get service info for {name}")
                return
            
            # Extract metadata from TXT records (properties)
            properties = info.properties or {}
            device_id = properties.get(b"device_id", b"").decode()
            os_name = properties.get(b"os", b"Windows").decode()
            version = properties.get(b"version", b"1.0.0").decode()
            role = properties.get(b"role", b"UNASSIGNED").decode()
            
            # Extract IP and port
            addresses = info.parsed_addresses()
            ip_address = str(addresses[0]) if addresses else None
            port = info.port
            
            # Don't track ourselves
            if device_id == self.local_device.id:
                logger.debug(f"Ignoring self-discovery: {name}")
                return
            
            # Create Device entity from mDNS data
            device_name = name.split("._kms")[0] if "._kms" in name else name
            
            # Parse OS enum
            try:
                device_os = DeviceOS[os_name.upper()]
            except (KeyError, ValueError):
                device_os = DeviceOS.WINDOWS
            
            # Parse Role enum
            try:
                device_role = DeviceRole[role.upper()]
            except (KeyError, ValueError):
                device_role = DeviceRole.UNASSIGNED
            
            device = Device(
                id=device_id,
                name=device_name,
                mac_address="",  # TODO: Fetch from ARP table
                os=device_os,
                role=device_role,
                ip_address=ip_address,
                port=port,
                version=version,
                is_registered=True,
                last_seen=datetime.now(timezone.utc)
            )
            
            # Persist to database
            with self._lock:
                existing = self.device_repo.read(device_id)
                if existing:
                    # Update existing device
                    existing.ip_address = ip_address
                    existing.is_registered = True
                    existing.last_seen = datetime.now(timezone.utc)
                    self.device_repo.update(existing)
                    device = existing
                else:
                    # Create new device
                    self.device_repo.create(device)
                
                self.discovered_devices[device_id] = device
            
            # Notify listeners
            for listener in self.listeners:
                try:
                    listener("device_added", device)
                except Exception as e:
                    logger.exception(f"Error in listener callback: {e}")
            
            logger.info(f"Device discovered: {device_name} ({ip_address}:{port})")
        
        except Exception as e:
            logger.exception(f"Error processing device add: {e}")
    
    def _on_device_removed(self, zeroconf, name: str):
        """
        Handle device disappearance from mDNS.
        
        Args:
            zeroconf: Zeroconf instance
            name: Service instance name
        """
        logger.debug(f"Device removed from mDNS: {name}")
        
        try:
            # Find device by name
            device_name = name.split("._kms")[0] if "._kms" in name else name
            
            with self._lock:
                for device_id, device in list(self.discovered_devices.items()):
                    if device.name == device_name:
                        del self.discovered_devices[device_id]
                        
                        # Update DB (mark offline)
                        device.is_registered = False
                        self.device_repo.update(device)
                        
                        # Notify listeners
                        for listener in self.listeners:
                            try:
                                listener("device_removed", device)
                            except Exception as e:
                                logger.exception(f"Error in listener callback: {e}")
                        
                        logger.info(f"Device removed: {device.name}")
                        break
        
        except Exception as e:
            logger.exception(f"Error processing device removal: {e}")
    
    def _on_device_updated(self, zeroconf, name: str):
        """
        Handle device metadata update on mDNS.
        
        Args:
            zeroconf: Zeroconf instance
            name: Service instance name
        """
        logger.debug(f"Device updated on mDNS: {name}")
        # For now, treat as remove + add
        self._on_device_removed(zeroconf, name)
        self._on_device_added(zeroconf, name)
    
    def _start_offline_detection(self):
        """Start background thread for offline detection (60+ second timeout)."""
        def check_offline_loop():
            while self.running:
                try:
                    now = datetime.now(timezone.utc)
                    
                    with self._lock:
                        for device_id, device in list(self.discovered_devices.items()):
                            time_since_seen = (now - device.last_seen).total_seconds()
                            
                            # Mark as offline if not seen for OFFLINE_THRESHOLD seconds
                            if time_since_seen > self.OFFLINE_THRESHOLD and device.is_registered:
                                logger.warning(
                                    f"Device offline (no mDNS for {time_since_seen}s): {device.name}"
                                )
                                
                                device.is_registered = False
                                self.device_repo.update(device)
                                
                                # Notify listeners
                                for listener in self.listeners:
                                    try:
                                        listener("device_offline", device)
                                    except Exception as e:
                                        logger.exception(f"Error in listener callback: {e}")
                
                except Exception as e:
                    logger.exception(f"Error in offline detection loop: {e}")
                
                # Check every 10 seconds
                time.sleep(10)
        
        self._offline_thread = threading.Thread(target=check_offline_loop, daemon=True)
        self._offline_thread.start()
        logger.debug("Offline detection thread started")
    
    def stop(self):
        """Stop discovery service and cleanup resources."""
        logger.info("Stopping discovery service")
        self.running = False
        
        try:
            if self.browser:
                self.browser.cancel()
                logger.debug("Service browser cancelled")
            
            if self.zeroconf:
                # Unregister our service
                try:
                    service_name = f"{self.local_device.name}._kms._tcp.local."
                    service_info = ServiceInfo(
                        self.SERVICE_TYPE,
                        name=service_name,
                        port=self.local_device.port
                    )
                    self.zeroconf.unregister_service(service_info)
                    logger.debug("Service unregistered from mDNS")
                except Exception as e:
                    logger.warning(f"Error unregistering service: {e}")
                
                self.zeroconf.close()
                logger.debug("Zeroconf closed")
            
            # Wait for offline detection thread
            if self._offline_thread and self._offline_thread.is_alive():
                self._offline_thread.join(timeout=5)
                logger.debug("Offline detection thread stopped")
        
        except Exception as e:
            logger.exception(f"Error stopping discovery service: {e}")
    
    def get_discovered(self) -> List[Device]:
        """
        Get list of currently discovered devices.
        
        Returns:
            List of Device objects discovered on mDNS
        """
        with self._lock:
            return list(self.discovered_devices.values())
