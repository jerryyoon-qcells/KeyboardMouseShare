# Phase 2: Foundational Implementation Specifications

**Phase**: Phase 2 - Foundational (Blocking Prerequisites)  
**Duration**: 2 weeks (~10 working days)  
**Tasks**: T017–T046 (30 tasks)  
**Status**: SPECIFICATION READY

---

## Overview

Phase 2 implements the core data models, network discovery, and encryption infrastructure that all subsequent phases depend on. This phase is **blocking** — no User Story implementation (Phases 3–7) can begin until Phase 2 completes.

### Phase 2 Deliverables

| Component | Scope | Tasks | Files |
|-----------|-------|-------|-------|
| **Data Models** | Device, Connection, Layout, InputEvent | T017–T026 | `src/models/*.py` (4 modules) |
| **Network Discovery** | mDNS service registration + browsing | T027–T035 | `src/network/discovery.py` |
| **Network Connection** | TLS 1.3 encrypted communication | T036–T042 | `src/network/connection.py` |
| **Input Abstraction** | Cross-platform InputHandler base + tests | T043–T046 | `src/input/handler.py` + stubs |

---

## Implementation Order

### Week 1: Data Models + Discovery

```
Day 1-2: Data Models (T017–T026)
  └─ Device, Connection, Layout, InputEvent entities
  └─ SQLite schema + migrations
  └─ Repository/DAO layer for persistence

Day 3-4: mDNS Discovery (T027–T035)
  └─ DiscoveryService class
  └─ Service registration (broadcast)
  └─ Service browsing (listen)
  └─ Callback handlers
  └─ Unit + integration tests

Day 5: Code Review + Cleanup
  └─ Refine models based on test feedback
  └─ Update documentation
```

### Week 2: Network + Input

```
Day 6-8: TLS Connection (T036–T042)
  └─ ConnectionHandler class
  └─ TLS 1.3 setup + certificate exchange
  └─ Message send/receive with encryption
  └─ Error handling + reconnection logic

Day 9-10: Input Abstraction (T043–T046)
  └─ InputHandler abstract base class
  └─ Platform stub implementations
  └─ Unit tests (mock implementations)
  └─ Integration with input hook libraries
```

---

## Detailed Task Specifications

### SECTION 1: DATA MODELS (T017–T026)

#### T017: Device Entity & Repository

**Objective**: Implement Device dataclass and persistence layer

**Specification**:
```python
# src/models/device.py

@dataclass
class Device:
    """Represents a machine running Keyboard Mouse Share."""
    
    id: str                      # UUID, unique across all time
    mac_address: str             # MAC address (immutable, unique per network)
    name: str                    # User-friendly name (max 50 chars)
    os: Enum[WINDOWS, MACOS]     # Operating system
    role: Enum[MASTER, CLIENT, UNASSIGNED]  # Device role
    ip_address: str              # Current IP on network (mutable)
    port: int                    # Listening port (default 19999)
    version: str                 # App version (e.g., "1.0.0")
    discovery_timestamp: datetime
    last_seen: datetime
    is_registered: bool          # True after user confirms pairing
    created_at: datetime
    updated_at: datetime
```

**Files to Create**:
- `src/models/device.py` (Device dataclass + validators + to_dict/from_dict)
- `src/models/device_repository.py` (DeviceRepository for SQLite operations)

**Tests**:
- Unit: Device creation, validation, serialization (test_device.py)
- Unit: Repository CRUD operations (test_device_repository.py)

**Dependencies**: SQLite3, dataclasses, datetime, uuid

**Acceptance Criteria**:
- ✅ Device can be created and validated
- ✅ Device persists to SQLite
- ✅ Device can be retrieved by ID or MAC address
- ✅ Multiple devices can be stored and queried

---

#### T018: Connection Entity & Repository

**Objective**: Implement Connection dataclass for master↔client links

**Specification**:
```python
# src/models/connection.py

@dataclass
class Connection:
    """Represents a TLS link between master and client."""
    
    id: str                                    # Format: "{master_id}-{client_id}"
    master_device_id: str                      # FK to Device
    client_device_id: str                      # FK to Device
    encryption_key: bytes                      # TLS certificate (PEM)
    encryption_key_hash: str                   # SHA256 hash for integrity
    status: Enum[CONNECTING, CONNECTED, DISCONNECTED, FAILED]
    auth_token: str                            # For reconnect without re-pair
    established_timestamp: datetime
    disconnected_timestamp: Optional[datetime]
    input_event_counter: int                   # Audit: events sent
    input_event_last_timestamp: Optional[datetime]
    failures_count: int                        # Auth failures (triggers backoff)
    created_at: datetime
    updated_at: datetime
```

**Files to Create**:
- `src/models/connection.py` (Connection dataclass)
- `src/models/connection_repository.py` (ConnectionRepository)

**Tests**:
- Unit: Connection lifecycle (CONNECTING → CONNECTED → DISCONNECTED)
- Unit: Repository operations (create, update status, etc.)

**Constraints**:
- One Connection per (master, client) pair
- Cannot transition backwards (DISCONNECTED → CONNECTED requires new record)

---

#### T019: Layout Entity & Repository

**Objective**: Store screen configuration for cursor mapping

**Specification**:
```python
# src/models/layout.py

@dataclass
class Layout:
    """Represents spatial positioning of a device."""
    
    device_id: str               # FK to Device
    x: int                       # Pixel offset X from origin
    y: int                       # Pixel offset Y from origin
    width: int                   # Screen width (physical pixels)
    height: int                  # Screen height (physical pixels)
    dpi_scale: float             # DPI factor (1.0 = 96 DPI baseline)
    orientation: Enum[LANDSCAPE, PORTRAIT]
    created_at: datetime
    updated_at: datetime
```

**Files to Create**:
- `src/models/layout.py`
- `src/models/layout_repository.py`

**Validation**:
- Width/height: 480–7680 pixels
- DPI scale: 0.5–4.0
- x/y: must be non-negative

---

#### T020: InputEvent Entity & Repository

**Objective**: Define event structure for keyboard/mouse transmission

**Specification**:
```python
# src/models/input_event.py

class InputEventType(Enum):
    KEY_PRESS = "KEY_PRESS"
    KEY_RELEASE = "KEY_RELEASE"
    MOUSE_MOVE = "MOUSE_MOVE"
    MOUSE_CLICK = "MOUSE_CLICK"
    MOUSE_SCROLL = "MOUSE_SCROLL"

@dataclass
class InputEvent:
    """Represents a single keyboard or mouse event."""
    
    id: str                      # UUID
    event_type: InputEventType
    source_device_id: str        # Device originating the event
    target_device_id: str        # Device receiving the event
    
    # Payload (varies by type)
    keycode: Optional[int]       # For KEY_PRESS/KEY_RELEASE
    modifiers: List[str]         # ["CTRL", "ALT", "SHIFT"]
    button: Optional[str]        # For MOUSE_CLICK (LEFT, RIGHT, MIDDLE)
    x: Optional[int]             # For MOUSE_MOVE
    y: Optional[int]             # For MOUSE_MOVE
    scroll_delta: Optional[int]  # For MOUSE_SCROLL
    
    timestamp: datetime
    is_encrypted: bool
    created_at: datetime
```

**Files to Create**:
- `src/models/input_event.py`
- Event serialization to JSON (for network transmission)

---

#### T021: SQLite Schema & Migrations

**Objective**: Create database schema and migration framework

**Files to Create**:
- `src/models/schema.py` (SQLite CREATE TABLE statements)
- `src/models/migrations.py` (Migration system: 001_initial.sql, etc.)
- `tests/test_schema.py` (verification that schema is correct)

**Schema**:
```sql
CREATE TABLE devices (
    id TEXT PRIMARY KEY,
    mac_address TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    os TEXT NOT NULL,
    role TEXT NOT NULL,
    ip_address TEXT,
    port INTEGER DEFAULT 19999,
    version TEXT NOT NULL,
    discovery_timestamp TEXT,
    last_seen TEXT,
    is_registered BOOLEAN DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE connections (
    id TEXT PRIMARY KEY,
    master_device_id TEXT NOT NULL,
    client_device_id TEXT NOT NULL,
    status TEXT NOT NULL,
    ...
    FOREIGN KEY(master_device_id) REFERENCES devices(id),
    FOREIGN KEY(client_device_id) REFERENCES devices(id)
);

CREATE TABLE layouts (
    device_id TEXT PRIMARY KEY,
    x INTEGER, y INTEGER,
    width INTEGER, height INTEGER,
    dpi_scale REAL,
    orientation TEXT,
    ...
    FOREIGN KEY(device_id) REFERENCES devices(id)
);

CREATE TABLE input_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    source_device_id TEXT,
    ...
    created_at TEXT
);
```

---

#### T022–T026: Repository Implementation & Tests

**T022**: DeviceRepository full CRUD (create, read, update, delete, query by MAC)
**T023**: ConnectionRepository (lifetime management, status transitions)
**T024**: LayoutRepository (save/load per device)
**T025**: InputEventRepository (audit logging, retention policy)
**T026**: Integration tests for all repositories (transactions, foreign keys, etc.)

**Files**:
- `src/models/repositories.py` (all repository classes)
- `tests/test_repositories.py` (comprehensive test suite)

---

### SECTION 2: NETWORK DISCOVERY (T027–T035)

#### T027: DiscoveryService Architecture

**Objective**: Implement mDNS service for device discovery

**Design**:
```python
# src/network/discovery.py

class DiscoveryService:
    """Manages mDNS service registration and discovery."""
    
    def __init__(self, device: Device, config: Config):
        """Initialize discovery service."""
        self.device = device
        self.config = config
        self.service_type = "_kms._tcp.local."
        self.discovered_devices: List[Device] = []
        self.zeroconf = None
        self.service_info = None
    
    def start_registration(self):
        """Register this device as mDNS service."""
        # Create ServiceInfo with device metadata in TXT record:
        # version, model, os, device_id, port
        
    def start_browsing(self):
        """Start listening for other devices on network."""
        # Create ServiceBrowser to listen for _kms._tcp.local.
        # Call callbacks when devices appear/disappear
    
    def add_listener(self, callback):
        """Register callback for device add/remove events."""
        
    def handle_service_added(self, service_name: str):
        """Callback when new service detected."""
        # Parse service info
        # Create Device object
        # Add to discovered_devices list
        # Call listeners
        
    def handle_service_removed(self, service_name: str):
        """Callback when service goes offline."""
        # Mark device as offline
        # Update last_seen
        
    def get_discovered_devices(self) -> List[Device]:
        """Return list of discovered devices."""
        
    def stop(self):
        """Stop discovery (cleanup)."""
```

**Files to Create**:
- `src/network/discovery.py` (DiscoveryService class)
- `tests/test_discovery.py` (unit + integration tests)

**Dependencies**: zeroconf library

**Acceptance Criteria**:
- ✅ Device registers itself as mDNS service
- ✅ Device discovers other services within 5 seconds
- ✅ Callback fired when service appears/disappears
- ✅ Service info includes version, OS, device_id, port

---

#### T028–T035: Discovery Implementation & Testing

**T028**: ServiceBrowser integration (listening logic)
**T029**: Service info parsing (extract metadata from TXT record)
**T030**: Offline detection (mark offline if not heard from in 60s)
**T031**: Callback system (listeners for add/remove events)
**T032**: Error handling (network failures, timeout handling)
**T033**: Unit tests (mock zeroconf, test state machine)
**T034**: Integration tests (real mDNS on local network)
**T035**: Documentation (API docs, usage examples)

---

### SECTION 3: NETWORK CONNECTION (T036–T042)

#### T036: TLS ConnectionHandler Architecture

**Objective**: Establish encrypted connections between devices

**Design**:
```python
# src/network/connection.py

class ConnectionHandler:
    """Manages TLS 1.3 connections between devices."""
    
    def __init__(self, 
                 local_device: Device,
                 remote_device: Device,
                 config: Config):
        """Initialize connection."""
        self.local_device = local_device
        self.remote_device = remote_device
        self.status = ConnectionStatus.DISCONNECTED
        self.ssl_context = None
        self.socket = None
        
    def initiate_connection(self) -> bool:
        """Initiate TLS connection as client."""
        # Create SSL context (TLS 1.3)
        # Connect to remote IP:port
        # Verify certificate
        # Return success/failure
        
    def accept_connection(self, raw_socket) -> bool:
        """Accept incoming TLS connection as server."""
        # Wrap socket with SSL
        # Perform handshake
        
    def send_message(self, msg_type: str, payload: dict) -> bool:
        """Send encrypted JSON message."""
        # Serialize to JSON
        # Encrypt with TLS
        # Send over socket
        
    def receive_message(self, timeout: float = 30) -> Optional[dict]:
        """Receive and decrypt JSON message."""
        # Read from socket
        # Decrypt
        # Parse JSON
        # Return payload
        
    def close(self):
        """Close connection gracefully."""
```

**Files to Create**:
- `src/network/connection.py` (ConnectionHandler)
- `src/network/message_types.py` (Message protocol definitions)

---

#### T037–T042: Connection Implementation & Testing

**T037**: TLS setup (SSL context with TLS 1.3 config)
**T038**: Certificate exchange protocol (during pairing)
**T039**: Message serialization/deserialization (JSON format)
**T040**: Error handling & reconnection logic
**T041**: Unit tests (mock sockets, TLS simulation)
**T042**: Integration tests (real TLS handshake between two processes)

---

### SECTION 4: INPUT ABSTRACTION (T043–T046)

#### T043: InputHandler Abstract Base Class

**Objective**: Define cross-platform input interface

**Design**:
```python
# src/input/handler.py

from abc import ABC, abstractmethod

class InputHandler(ABC):
    """Abstract base for platform-specific input handling."""
    
    @abstractmethod
    def setup(self) -> bool:
        """Initialize input hooks (may require permissions)."""
        
    @abstractmethod
    def hook_keyboard(self, callback) -> bool:
        """Start listening for keyboard events."""
        
    @abstractmethod
    def hook_mouse(self, callback) -> bool:
        """Start listening for mouse events."""
        
    @abstractmethod
    def send_keyboard_event(self, keycode: int, modifiers: List[str], is_press: bool) -> bool:
        """Simulate keyboard event."""
        
    @abstractmethod
    def send_mouse_event(self, x: int, y: int, button: str = None, is_click: bool = False) -> bool:
        """Simulate mouse event."""
        
    @abstractmethod
    def set_mouse_position(self, x: int, y: int) -> bool:
        """Move mouse cursor to position."""
        
    @abstractmethod
    def unhook(self) -> bool:
        """Stop listening (cleanup)."""
```

**Files to Create**:
- `src/input/handler.py` (Abstract base class)
- `src/input/windows_handler.py` (Stub)
- `src/input/macos_handler.py` (Stub)

---

#### T044–T046: Platform Implementations & Tests

**T044**: WindowsInputHandler (using pynput, Win32 API stubs)
**T045**: MacOSInputHandler (using pynput, PyObjC stubs)
**T046**: Unit tests (mock implementations for cross-platform testing)

**Note**: Full implementation of Windows/macOS hooks deferred to Phases 3–7 when actually sending input. Phase 2 creates the abstraction and stubs.

---

## File Structure After Phase 2

```
src/
├── models/
│   ├── __init__.py
│   ├── device.py          # Device entity + validators
│   ├── connection.py      # Connection entity
│   ├── layout.py          # Layout entity
│   ├── input_event.py     # InputEvent entity
│   ├── repositories.py    # All repository classes
│   ├── schema.py          # SQLite schema
│   └── migrations.py      # Migration system
├── network/
│   ├── __init__.py
│   ├── discovery.py       # DiscoveryService (mDNS)
│   ├── connection.py      # ConnectionHandler (TLS)
│   └── message_types.py   # Protocol definitions
├── input/
│   ├── __init__.py
│   ├── handler.py         # InputHandler ABC
│   ├── windows_handler.py # Windows stub
│   └── macos_handler.py   # macOS stub
├── ...existing files...

tests/
├── test_device.py
├── test_repositories.py
├── test_discovery.py
├── test_connection.py
├── test_input_handler.py
└── ...existing tests...
```

---

## Testing Strategy

### Phase 2 Test Coverage Target: 75%+ (higher than Phase 1's 70%)

**Unit Tests** (Mocked dependencies):
- Device/Connection/Layout creation, validation, serialization
- Repository CRUD operations
- DiscoveryService state machine (mock zeroconf)
- ConnectionHandler message send/receive (mock sockets)
- InputHandler abstract methods (verify interface)

**Integration Tests** (Real dependencies):
- Full mDNS discovery on local network (if available)
- TLS handshake between two test processes
- Database transactions with foreign keys
- Input hook initialization (without actual input simulation)

**Property-Based Tests**:
- Device IDs are unique (UUID generation)
- Connections are unidirectional (master→client only)
- Layout coordinates never negative
- DPI scales between 0.5–4.0

---

## Dependencies

### New External Libraries (Beyond Phase 1)

- `zeroconf>=0.68.0` — mDNS discovery (already in requirements.txt)
- `cryptography>=41.0.0` — TLS certificate handling (already in requirements.txt)
- `pynput>=1.7.6` — Cross-platform input hooks (already in requirements.txt)

### New Internal Modules

- Models package (`src/models/`)
- Network package (`src/network/`)
- Input package (`src/input/`)

---

## Quality Gates for Phase 2 Completion

Before Phase 3 begins:

- [ ] All 30 tasks (T017–T046) complete and merged
- [ ] Test coverage ≥ 75% (up from 70%)
- [ ] All unit tests pass
- [ ] All integration tests pass (mDNS + TLS on local network)
- [ ] Code review completed (linting, type hints, docstrings)
- [ ] ARCHITECTURE.md updated with module diagrams
- [ ] README.md has quick-start examples for Phase 2 features

---

## Risk Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| mDNS blocking on corporate networks | Low | Document as known limitation; fallback to manual IP entry |
| TLS certificate generation issues | Low | Pre-generate test certs; use cryptography library |
| Input hook permission issues (macOS) | Low | Test early on real hardware; document setup steps |
| Database schema migration complexity | Medium | Start simple; add migrations as needed; test transactions |

---

## Next Steps After Phase 2

Once Phase 2 is complete:

1. **Phase 3 (US1: Discovery)** — T047–T065
   - Integrate DiscoveryService into UI
   - Device list UI
   - Registration flow

2. **Phase 4 (US2: Roles)** — T066–T080
   - Master/Client role configuration
   - Role validation (single master constraint)
   - Persistent role storage

3. **Phase 5 (US3: Input Sharing)** — T081–T105
   - Hook keyboard/mouse from master
   - Transmit events through ConnectionHandler
   - Simulate events on client (InputHandler)
   - MVP complete at end of Phase 5

---

**Phase 2 is the foundation. Everything else depends on it working reliably.**

Ready to start implementation? 🚀
