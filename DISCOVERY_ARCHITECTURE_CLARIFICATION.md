# Discovery Architecture Clarification

## How mDNS Discovery Works in This Project

### 1. High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│ YOUR APP STARTS ON DEVICE A (e.g., "Jerry's Laptop")         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
        ┌──────────────────────────────────────┐
        │ Step 1: CREATE Device ENTITY         │
        ├──────────────────────────────────────┤
        │ id = <random UUID>                   │
        │ mac_address = "aa:bb:cc:dd:ee:ff"    │
        │ name = "Jerry's Laptop"              │
        │ os = "Darwin" (macOS)                │
        │ port = 19999                         │
        │ is_registered = False (not yet!)     │
        │ ip_address = None (not yet!)         │
        └──────────────────────────────────────┘
                           │
                           ↓
        ┌──────────────────────────────────────┐
        │ Step 2: REGISTER ON mDNS             │
        ├──────────────────────────────────────┤
        │ Service Name: _kms._tcp.local.       │
        │ Instance: "Jerry's Laptop._kms..."   │
        │ Host: laptop.local                   │
        │ Port: 19999                          │
        │ TXT Records (metadata):              │
        │  - version=1.0.0                     │
        │  - device_id=<UUID>                  │
        │  - os=Darwin                         │
        │  - role=UNASSIGNED (waiting)         │
        └──────────────────────────────────────┘
                           │
                           ↓
        ┌──────────────────────────────────────┐
        │ Step 3: START BROWSING (listen)      │
        ├──────────────────────────────────────┤
        │ Listen for service type: _kms._tcp.  │
        │ mDNS library broadcasts:             │
        │  "Anyone have _kms._tcp. services?"  │
        └──────────────────────────────────────┘
                           │
                           ↓
                    (LAN broadcast)
                           │
        ┌──────────────────────────────────────┐
        │ DEVICE B (e.g., Windows PC)          │
        │ Hears the query, responds:           │
        │  "I have Jerry's Laptop._kms!"       │
        │  IP: 192.168.1.100                   │
        └──────────────────────────────────────┘
                           │
                           ↓
        ┌──────────────────────────────────────┐
        │ Step 4: DEVICE DISCOVERED            │
        ├──────────────────────────────────────┤
        │ App receives callback:                │
        │  on_device_added(                    │
        │    name="Jerry's Laptop",            │
        │    ip="192.168.1.100",               │
        │    port=19999,                       │
        │    txt_records={...}                 │
        │  )                                   │
        │                                      │
        │ Create Device in DB:                 │
        │  Device(                             │
        │    id="<UUID from TXT>",             │
        │    mac_address="<discover somehow>", │
        │    name="Jerry's Laptop",            │
        │    ip_address="192.168.1.100",       │
        │    port=19999                        │
        │  )                                   │
        │  device.is_registered = True ✓       │
        └──────────────────────────────────────┘
                           │
                           ↓
        ┌──────────────────────────────────────┐
        │ Step 5: READY FOR CONNECTION         │
        ├──────────────────────────────────────┤
        │ Now available in UI device list      │
        │ Can initiate TLS connection          │
        └──────────────────────────────────────┘
```

---

## 2. Device Registration On mDNS (T027–T030)

### Architecture

```python
# What zeroconf library does:
from zeroconf import ServiceInfo, Zeroconf

# Register THIS device on mDNS so others can find it
service_info = ServiceInfo(
    "_kms._tcp.local.",                    # Service type (constant)
    name=f"{device_name}._kms._tcp.local.",  # Full service instance name
    hostname="laptop.local",               # Hostname
    port=19999,                            # Network port
    properties={
        "device_id": str(device.id),       # UUID (from Device entity)
        "os": device.os,                   # "Darwin" or "Windows"
        "version": "1.0.0",                # App version (from constants)
        "role": device.role,               # "UNASSIGNED" initially
    }
)

zeroconf = Zeroconf()
zeroconf.register_service(service_info)
# Now broadcast every ~30 seconds:
# "I'm Jerry's Laptop, listen on port 19999"
```

### Database Impact

```
┌───────────────────────────────────────┐
│ devices TABLE (SQLite)                │
├───────────────────────────────────────┤
│ id                 | PRIMARY KEY, UUID │
│ mac_address        | Unique (TBD)      │
│ name               | "Jerry's Laptop"  │
│ os                 | "Darwin"          │
│ role               | "UNASSIGNED"      │
│ ip_address         | NULL (until      │
│                    │ discovered locally)
│ port               | 19999             │
│ version            | "1.0.0"           │
│ is_registered      | True ✓ (THIS ONE) │
│ created_at         | timestamp         │
│ last_seen         | timestamp         │
└───────────────────────────────────────┘

Key: "is_registered" = True means:
  - Device is on mDNS
  - Others can find it
  - Can accept incoming connections
```

**Task Split (T027–T030)**:
- **T027**: DiscoveryService class architecture (empty class skeleton)
- **T028**: `register_service()` — wraps zeroconf.register_service()
- **T029**: Device entity integration (create Device in DB when registering)
- **T030**: Lifecycle management (start/stop, update TXT records)

---

## 3. Device Browsing & Discovery (T031–T033)

### Architecture

```python
# What zeroconf library does:
from zeroconf import ServiceBrowser, Zeroconf

class DiscoveryService:
    def __init__(self):
        self.zeroconf = Zeroconf()
        self.listeners = []  # Callbacks to notify app
        self.discovered_devices = {}  # Device ID → Device object
    
    def add_listener(self, callback):
        """Register callback for device add/remove events."""
        self.listeners.append(callback)
    
    def start_browsing(self):
        """Start listening for _kms._tcp services on LAN."""
        # This ServiceBrowser runs a background thread
        # It calls on_service_state_change() when devices appear/disappear
        self.browser = ServiceBrowser(
            self.zeroconf,
            "_kms._tcp.local.",
            handlers=[self.on_service_state_change]
        )
    
    def on_service_state_change(self, zeroconf, service_type, name, state_change):
        """Callback invoked when mDNS detects device add/remove/update."""
        
        if state_change == ServiceStateChange.Added:
            print(f"Device found: {name}")
            
            # Fetch service details from mDNS
            info = zeroconf.get_service_info(service_type, name)
            
            # Extract TXT records
            device_id = info.properties.get("device_id")
            os = info.properties.get("os")
            role = info.properties.get("role")
            version = info.properties.get("version")
            
            # Get IP address (may have multiple, pick first)
            ip_address = info.parsed_addresses()[0]  # "192.168.1.100"
            port = info.port  # 19999
            
            # Create Device entity
            device = Device(
                id=device_id,
                name=name.split("._kms")[0],  # "Jerry's Laptop"
                os=os,
                role=role,
                ip_address=ip_address,
                port=port,
                version=version,
                is_registered=True  # ✓ Found it on active mDNS
            )
            
            # Persist to database
            device_repo.create(device)
            
            # Notify app UI
            for listener in self.listeners:
                listener("device_added", device)
        
        elif state_change == ServiceStateChange.Removed:
            print(f"Device left network: {name}")
            
            # Device disappeared from mDNS
            # Mark in database with last_seen timestamp
            device_repo.update_last_seen(device_id)
            
            # Notify app UI
            for listener in self.listeners:
                listener("device_removed", device)
        
        elif state_change == ServiceStateChange.Updated:
            # Device updated metadata (e.g., role changed)
            # Just re-fetch and update DB
            pass
```

### How It Integrates With Device Entity

```
┌────────────────────────────────────────────┐
│ App Initialization                         │
└────────────────────────────────────────────┘
           │
           ├─ Create MY Device entity (locally)
           │  db.devices.create(Device(
           │    name="My Laptop",
           │    os="Darwin",
           │    role="UNASSIGNED",
           │    ip_address="127.0.0.1",
           │    is_registered=False (still registering)
           │  ))
           │
           └─ Register on mDNS + update my Device
              my_device.is_registered = True
              db.devices.update(my_device)

Later:
┌────────────────────────────────────────────┐
│ Browse mDNS (background thread)            │
└────────────────────────────────────────────┘
           │
           └─ Callback fires: Device added
              ├─ Create OTHER Device entity
              │  db.devices.create(Device(
              │    name="Friend's PC",
              │    os="Windows",
              │    ip_address="192.168.1.105",
              │    is_registered=True (found on mDNS)
              │  ))
              │
              └─ Notify UI: "Friend's PC is online!"
```

**Task Split (T031–T033)**:
- **T031**: ServiceBrowser integration (listening)
- **T032**: Device discovery callback (create Device in DB)
- **T033**: Error handling + offline detection (see below)

---

## 4. Offline Detection (T034–T035)

### The Problem

```
Real-world scenario:
  - Device A discovers Device B at 14:00
  - Device B appears in UI ("available")
  - User walks away with Device B (no shutdown)
  - WiFi disconnects at 14:03
  - Device B vanishes from mDNS
  
  But: Does app know it's OFFLINE or just DISCONNECTED?
  Answer: Different scenarios need different handling:
  
  ┌─ OFFLINE (not on network)
  │  └─ Mark device.is_registered = False
  │     Remove from "Available Devices" UI list
  │     Reason: mDNS timeout (60+ seconds, no refresh)
  │
  └─ DISCONNECTED (on network but no TLS connection)
     └─ Keep device.is_registered = True
        Show in UI but grayed out
        Reason: TLS connection failed or closed
```

### Implementation Strategy

```python
class DiscoveryService:
    
    OFFLINE_THRESHOLD = 60  # seconds (Task parameter T034)
    
    def start_offline_detection(self):
        """Background thread: periodically check if discovered devices are still alive."""
        
        import threading
        import time
        
        def check_offline():
            while self.running:
                now = time.time()
                
                for device_id, device in self.discovered_devices.items():
                    time_since_last_seen = now - device.last_seen
                    
                    if time_since_last_seen > self.OFFLINE_THRESHOLD:
                        # Not seen on mDNS for 60+ seconds
                        # Assume it's offline
                        print(f"Device {device.name} is OFFLINE (no mDNS refresh for 60s)")
                        
                        # Update database
                        device.is_registered = False
                        device_repo.update(device)
                        
                        # Notify UI
                        for listener in self.listeners:
                            listener("device_offline", device)
                
                time.sleep(10)  # Check every 10 seconds
        
        thread = threading.Thread(target=check_offline, daemon=True)
        thread.start()
```

### Database Integration

```sql
-- devices TABLE (with offline tracking)
CREATE TABLE devices (
    id TEXT PRIMARY KEY,
    mac_address TEXT UNIQUE,
    name TEXT NOT NULL,
    os TEXT NOT NULL,  -- "Windows", "Darwin"
    role TEXT,         -- "MASTER", "CLIENT", "UNASSIGNED"
    ip_address TEXT,   -- 192.168.1.100 (when discovered)
    port INTEGER,
    version TEXT,
    
    is_registered BOOLEAN DEFAULT False,  -- On mDNS right now?
    
    created_at TIMESTAMP,
    last_seen TIMESTAMP,  -- When last heard from mDNS
    
    CONSTRAINT check_role IN ("MASTER", "CLIENT", "UNASSIGNED")
);

-- Query examples:
-- 1. Find all ONLINE devices (registered on mDNS)
SELECT * FROM devices WHERE is_registered = True;

-- 2. Find devices offline for >60 seconds
SELECT * FROM devices 
WHERE is_registered = True 
AND (datetime('now') - datetime(last_seen)) > 60;

-- 3. Detect stale entries (discovered but never connected)
SELECT * FROM devices 
WHERE is_registered = False 
AND (datetime('now') - datetime(created_at)) > 3600;  -- >1 hour
```

---

## 5. Event Callback System (T034)

### How App Receives Notifications

```python
# In main.py or UI module:

def on_device_event(event_type, device):
    """Callback invoked by DiscoveryService."""
    
    if event_type == "device_added":
        print(f"✓ {device.name} appeared on network")
        ui.add_device_to_list(device)
    
    elif event_type == "device_removed":
        print(f"✗ {device.name} left the network")
        ui.remove_device_from_list(device)
    
    elif event_type == "device_offline":
        print(f"⚠ {device.name} is unreachable (offline detection)")
        ui.gray_out_device(device)
    
    elif event_type == "role_changed":
        print(f"→ {device.name} role changed to {device.role}")
        ui.update_device_status(device)

# Register callback:
discovery_service = DiscoveryService()
discovery_service.add_listener(on_device_event)
discovery_service.start_browsing()
discovery_service.start_offline_detection()
```

---

## 6. Task Dependency Chain

```
T017–T020: Device + Layout + Connection + InputEvent entities
           │
           ├─ (must complete first)
           │
T021–T026: Repository layer (CRUD, queries)
           │
           ├─ (DiscoveryService needs Device + DeviceRepository)
           │
T027: DiscoveryService architecture (class skeleton)
  │
  ├─→ T028: register_service() — Zeroconf registration
  │   └─ Depends: Device entity, DeviceRepository
  │
  ├─→ T029: register_device_in_db() — Persist local device
  │   └─ Depends: Device entity, DeviceRepository
  │
  ├─→ T030: Lifecycle (start/stop registration)
  │   └─ Depends: T028, T029
  │
  ├─→ T031: start_browsing() — ServiceBrowser
  │   └─ Depends: Device entity
  │
  ├─→ T032: on_service_state_change() — Device discovery
  │   └─ Depends: T031, DeviceRepository, Device entity
  │
  ├─→ T033: Error handling for mDNS failures
  │   └─ Depends: T032
  │
  ├─→ T034: start_offline_detection() — Background thread
  │   └─ Depends: DeviceRepository
  │
  └─→ T035: Complete tests + documentation
      └─ Depends: All of above
```

---

## 7. Key Design Decisions

| Decision | Why | Impact |
|----------|-----|--------|
| **mDNS for discovery** | Zero configuration, works on LAN without router | Doesn't work cross-internet (acceptable for MVP) |
| **60s offline threshold** | Reasonable balance (not too fast = false positives, not too slow = poor UX) | Users expect feedback within ~1 min |
| **Device.is_registered flag** | Distinguish "on mDNS now" vs "never saw on mDNS" | UI can filter online-only devices |
| **Background offline detection thread** | Catches network drops that mDNS might miss | Adds one daemon thread (negligible CPU) |
| **ServiceBrowser callback** | Async notification when devices appear/disappear | App stays responsive; UI updates automatically |
| **TXT Records for metadata** | Extend service discovery with app-specific data | No extra network round-trips; embedded in mDNS |

---

## 8. Common Pitfalls & How We Avoid Them

| Pitfall | Symptom | Our Solution |
|---------|---------|--------------|
| **Device appears online but unreachable** | IP address stale; mDNS wrong | TLS connection layer validates; Connection timeout triggers device_offline event |
| **MAC address not in mDNS** | Can't track device across reboots | MAC fetched from local ARP table during registration |
| **Dual IPv4 + IPv6 addresses** | ServiceBrowser returns list | Pick first address; log warning if >1 |
| **mDNS loop on startup** | Finds self as new device | Filter by device_id in TXT record (compare to my_device.id) |
| **mDNS blocking on corporate WiFi** | Devices never discovered | Fallback: manual IP entry (Phase 4+) |
| **Race condition: register + browse simultaneously** | ServiceBrowser misses own device | Self-discovery okay; handled by device_id filter |

---

## Next Steps

1. **Confirm this architecture** — Any changes needed?
2. **Create execution checklist** with code templates (Day 4–5 Deep Dive)
3. **Start T017** — Device entity implementation

**Questions?**
