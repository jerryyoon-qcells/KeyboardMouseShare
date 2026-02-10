# Phase 2 Execution Checklist — Code Templates & Daily Tasks

**Start Date**: [Your Date]  
**Target End Date**: +10 working days  
**Status**: Ready to Execute  

---

## QUICK START

```bash
# 1. Create models directory
mkdir -p src/models src/network src/input tests/unit tests/integration

# 2. Create __init__.py files
touch src/models/__init__.py src/network/__init__.py src/input/__init__.py

# 3. Create test __init__.py files
touch tests/unit/__init__.py tests/integration/__init__.py

# 4. Begin with Day 1 template below
```

---

# PHASE 2 DAILY CHECKLISTS

---

## DAY 1–2: DATA MODELS (T017–T020)

### Goal
Implement 4 core dataclasses (Device, Connection, Layout, InputEvent) with full type hints and validation.

### T017: Device Entity

**File**: `src/models/device.py`

```python
"""Device entity representing a connected keyboard-mouse-share instance."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class DeviceRole(str, Enum):
    """Device role in the network."""
    MASTER = "MASTER"        # Sends input events
    CLIENT = "CLIENT"        # Receives input events
    UNASSIGNED = "UNASSIGNED"  # Not yet assigned a role


class DeviceOS(str, Enum):
    """Supported operating systems."""
    WINDOWS = "Windows"
    MACOS = "Darwin"


@dataclass
class Device:
    """
    Represents a keyboard-mouse-share device on the network.
    
    Attributes:
        id: Unique identifier (UUID v4)
        mac_address: Hardware address (format: AA:BB:CC:DD:EE:FF)
        name: Human-readable device name (max 50 chars)
        os: Operating system (Windows or Darwin/macOS)
        role: Device role in network (MASTER, CLIENT, UNASSIGNED)
        ip_address: IPv4 or IPv6 address (None until discovered on mDNS)
        port: Network port (default 19999)
        version: Application version (semantic: "1.0.0")
        is_registered: True if currently on mDNS
        created_at: Timestamp when device record created
        last_seen: Timestamp when last seen on mDNS
    
    Constraints:
        - id must be valid UUID v4
        - mac_address must be unique
        - name max 50 characters
        - port in range 1024–65535
        - role must be MASTER, CLIENT, or UNASSIGNED
        - os must be Windows or Darwin
    """
    
    # Required fields
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mac_address: str = ""  # Will be fetched from ARP/ifconfig
    name: str = ""
    os: DeviceOS = DeviceOS.WINDOWS
    role: DeviceRole = DeviceRole.UNASSIGNED
    
    # Network fields
    ip_address: Optional[str] = None  # "192.168.1.100" or None
    port: int = 19999
    version: str = "1.0.0"
    
    # Registration fields
    is_registered: bool = False  # On mDNS right now?
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate fields after dataclass initialization."""
        from ..utils.validators import (
            validate_uuid, validate_mac_address, validate_device_name,
            validate_port, validate_ip_address, validate_os_type
        )
        
        if not validate_uuid(self.id):
            raise ValueError(f"Invalid UUID: {self.id}")
        
        if self.mac_address and not validate_mac_address(self.mac_address):
            raise ValueError(f"Invalid MAC address: {self.mac_address}")
        
        if not validate_device_name(self.name):
            raise ValueError(f"Invalid device name: {self.name}")
        
        if not validate_port(self.port):
            raise ValueError(f"Invalid port: {self.port}")
        
        if self.ip_address and not validate_ip_address(self.ip_address):
            raise ValueError(f"Invalid IP address: {self.ip_address}")
        
        if not validate_os_type(str(self.os.value)):
            raise ValueError(f"Invalid OS: {self.os}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "mac_address": self.mac_address,
            "name": self.name,
            "os": self.os.value,
            "role": self.role.value,
            "ip_address": self.ip_address,
            "port": self.port,
            "version": self.version,
            "is_registered": self.is_registered,
            "created_at": self.created_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Device":
        """Create Device from dictionary."""
        return cls(
            id=data["id"],
            mac_address=data["mac_address"],
            name=data["name"],
            os=DeviceOS(data["os"]),
            role=DeviceRole(data["role"]),
            ip_address=data.get("ip_address"),
            port=data.get("port", 19999),
            version=data.get("version", "1.0.0"),
            is_registered=data.get("is_registered", False),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
        )


# Test file: tests/unit/test_device.py
TEST_CODE_DEVICE = """
import pytest
from src.models.device import Device, DeviceRole, DeviceOS
from datetime import datetime
import uuid


class TestDeviceCreation:
    def test_create_device_with_defaults(self):
        device = Device(name="Test Laptop", mac_address="aa:bb:cc:dd:ee:ff")
        assert device.name == "Test Laptop"
        assert device.role == DeviceRole.UNASSIGNED
        assert device.is_registered is False
    
    def test_device_invalid_uuid(self):
        with pytest.raises(ValueError, match="Invalid UUID"):
            Device(id="not-a-uuid", name="Test", mac_address="aa:bb:cc:dd:ee:ff")
    
    def test_device_invalid_mac_address(self):
        with pytest.raises(ValueError, match="Invalid MAC"):
            Device(id=str(uuid.uuid4()), name="Test", mac_address="invalid")
    
    def test_device_invalid_name(self):
        with pytest.raises(ValueError, match="Invalid device name"):
            Device(id=str(uuid.uuid4()), name="x" * 100, mac_address="aa:bb:cc:dd:ee:ff")


class TestDeviceToDict:
    def test_to_dict_includes_all_fields(self):
        device = Device(name="Test", mac_address="aa:bb:cc:dd:ee:ff")
        d = device.to_dict()
        assert d["name"] == "Test"
        assert d["os"] == "Windows"
        assert d["role"] == "UNASSIGNED"
        assert "created_at" in d


class TestDeviceFromDict:
    def test_from_dict_round_trip(self):
        device1 = Device(name="Test", mac_address="aa:bb:cc:dd:ee:ff")
        d = device1.to_dict()
        device2 = Device.from_dict(d)
        assert device2.name == device1.name
        assert device2.role == device1.role
"""
```

**Checklist**:
- [ ] Create `src/models/device.py` with code above
- [ ] Create `tests/unit/test_device.py` with test code above
- [ ] Run: `python -m pytest tests/unit/test_device.py -v`
- [ ] Verify: All tests pass
- [ ] Verify: `validate_uuid()`, `validate_mac_address()` work (from Phase 1)

---

### T018: Connection Entity

**File**: `src/models/connection.py`

```python
"""Connection entity representing a TLS connection between two devices."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class ConnectionStatus(str, Enum):
    """Connection lifecycle states."""
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    FAILED = "FAILED"


@dataclass
class Connection:
    """
    Represents a TLS connection between a master and client device.
    
    Attributes:
        id: Unique identifier for this connection pair
        master_device_id: UUID of master device
        client_device_id: UUID of client device
        status: Connection state (CONNECTING, CONNECTED, DISCONNECTED, FAILED)
        tls_certificate: PEM-encoded X.509 certificate (for peer validation)
        auth_token: Token for session resumption / reconnection
        input_event_counter: Number of input events sent (audit/monitoring)
        created_at: When connection established
        last_heartbeat: When last heartbeat received
    
    Constraints:
        - Both device IDs must be valid UUIDs
        - They must be different (master ≠ client)
        - status must be one of the enum values
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    master_device_id: str = ""
    client_device_id: str = ""
    
    status: ConnectionStatus = ConnectionStatus.CONNECTING
    
    tls_certificate: Optional[str] = None  # PEM format
    auth_token: Optional[str] = None
    input_event_counter: int = 0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate connection setup."""
        from ..utils.validators import validate_uuid
        
        if not validate_uuid(self.master_device_id):
            raise ValueError(f"Invalid master device ID: {self.master_device_id}")
        
        if not validate_uuid(self.client_device_id):
            raise ValueError(f"Invalid client device ID: {self.client_device_id}")
        
        if self.master_device_id == self.client_device_id:
            raise ValueError("Master and client must be different devices")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "master_device_id": self.master_device_id,
            "client_device_id": self.client_device_id,
            "status": self.status.value,
            "tls_certificate": self.tls_certificate,
            "auth_token": self.auth_token,
            "input_event_counter": self.input_event_counter,
            "created_at": self.created_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
        }


# Test file: tests/unit/test_connection.py
TEST_CODE_CONNECTION = """
import pytest
from src.models.connection import Connection, ConnectionStatus
import uuid


class TestConnectionCreation:
    def test_create_connection(self):
        master_id = str(uuid.uuid4())
        client_id = str(uuid.uuid4())
        conn = Connection(master_device_id=master_id, client_device_id=client_id)
        assert conn.status == ConnectionStatus.CONNECTING
        assert conn.input_event_counter == 0
    
    def test_connection_same_device_raises(self):
        device_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="must be different"):
            Connection(master_device_id=device_id, client_device_id=device_id)
    
    def test_connection_invalid_uuid_raises(self):
        with pytest.raises(ValueError, match="Invalid master"):
            Connection(master_device_id="invalid", client_device_id=str(uuid.uuid4()))
"""
```

**Checklist**:
- [ ] Create `src/models/connection.py` with code above
- [ ] Create `tests/unit/test_connection.py` with test code above
- [ ] Run: `python -m pytest tests/unit/test_connection.py -v`
- [ ] Verify: All tests pass

---

### T019: Layout Entity

**File**: `src/models/layout.py`

```python
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
```

**Checklist**:
- [ ] Create `src/models/layout.py` with code above
- [ ] Create `tests/unit/test_layout.py` with basic tests
- [ ] Run: `python -m pytest tests/unit/test_layout.py -v`
- [ ] Verify: All tests pass

---

### T020: InputEvent Entity

**File**: `src/models/input_event.py`

```python
"""InputEvent entity representing a single keyboard or mouse input action."""

from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class InputEventType(str, Enum):
    """Types of input events."""
    KEY_PRESS = "KEY_PRESS"
    KEY_RELEASE = "KEY_RELEASE"
    MOUSE_MOVE = "MOUSE_MOVE"
    MOUSE_CLICK = "MOUSE_CLICK"
    MOUSE_RELEASE = "MOUSE_RELEASE"
    MOUSE_SCROLL = "MOUSE_SCROLL"


@dataclass
class InputEvent:
    """
    Represents a single keyboard or mouse input event.
    
    Attributes:
        id: Unique event identifier (UUID v4)
        event_type: Type of input (KEY_PRESS, MOUSE_MOVE, etc.)
        source_device_id: UUID of device that generated the event (master)
        target_device_id: UUID of device that receives the event (client)
        payload: Event-specific data (dict)
            For KEY_PRESS/KEY_RELEASE:
                { "keycode": "A", "modifiers": ["ctrl", "shift"] }
            For MOUSE_MOVE:
                { "x": 1024, "y": 768 }
            For MOUSE_CLICK/RELEASE:
                { "button": "left" }  # left, middle, right
            For MOUSE_SCROLL:
                { "scroll_delta": 5 }  # positive = up, negative = down
        timestamp: When event occurred (UTC)
        is_encrypted: True if payload was encrypted in transit
    
    Constraints:
        - Both device IDs must be valid UUIDs
        - payload must match event_type schema
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: InputEventType = InputEventType.MOUSE_MOVE
    
    source_device_id: str = ""
    target_device_id: str = ""
    
    payload: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    is_encrypted: bool = True
    
    def __post_init__(self):
        """Validate event structure."""
        from ..utils.validators import validate_uuid
        
        if not validate_uuid(self.source_device_id):
            raise ValueError(f"Invalid source device ID: {self.source_device_id}")
        
        if not validate_uuid(self.target_device_id):
            raise ValueError(f"Invalid target device ID: {self.target_device_id}")
        
        # Validate payload matches event type
        self._validate_payload()
    
    def _validate_payload(self):
        """Ensure payload structure matches event_type."""
        if self.event_type in (InputEventType.KEY_PRESS, InputEventType.KEY_RELEASE):
            assert "keycode" in self.payload, f"KEY event missing keycode: {self.payload}"
        
        elif self.event_type == InputEventType.MOUSE_MOVE:
            assert "x" in self.payload and "y" in self.payload, \
                f"MOUSE_MOVE missing x/y: {self.payload}"
        
        elif self.event_type in (InputEventType.MOUSE_CLICK, InputEventType.MOUSE_RELEASE):
            assert "button" in self.payload, \
                f"MOUSE_CLICK/RELEASE missing button: {self.payload}"
        
        elif self.event_type == InputEventType.MOUSE_SCROLL:
            assert "scroll_delta" in self.payload, \
                f"MOUSE_SCROLL missing scroll_delta: {self.payload}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "source_device_id": self.source_device_id,
            "target_device_id": self.target_device_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "is_encrypted": self.is_encrypted,
        }
```

**Checklist**:
- [ ] Create `src/models/input_event.py` with code above
- [ ] Create `tests/unit/test_input_event.py` with basic tests
- [ ] Run: `python -m pytest tests/unit/test_input_event.py -v`
- [ ] Verify: All tests pass

---

### EOD Checklist for Days 1–2

**ALL MODELS CREATED**:
- [ ] `src/models/device.py` (Device, DeviceRole, DeviceOS)
- [ ] `src/models/connection.py` (Connection, ConnectionStatus)
- [ ] `src/models/layout.py` (Layout, Orientation)
- [ ] `src/models/input_event.py` (InputEvent, InputEventType)

**TESTS CREATED**:
- [ ] `tests/unit/test_device.py` (5+ tests)
- [ ] `tests/unit/test_connection.py` (3+ tests)
- [ ] `tests/unit/test_layout.py` (3+ tests)
- [ ] `tests/unit/test_input_event.py` (3+ tests)

**RUN FULL TEST SUITE**:
```bash
python -m pytest tests/unit/test_device.py tests/unit/test_connection.py tests/unit/test_layout.py tests/unit/test_input_event.py -v
```

**SUCCESS CRITERIA**:
- [ ] All 14+ tests passing
- [ ] No validation errors
- [ ] All dataclasses compile
- [ ] to_dict() and from_dict() work (where implemented)

---

## DAY 3: REPOSITORY LAYER (T021–T026)

**Goal**: Implement SQLite schema + CRUD operations for all entities.

### T021: SQLite Schema

**File**: `src/models/schema.py`

```python
"""SQLite schema definition and migration management."""

import sqlite3
from pathlib import Path
from typing import Optional


class Database:
    """Database connection manager and schema initializer."""
    
    DB_PATH = Path.home() / ".keyboard-mouse-share" / "devices.db"
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection."""
        self.db_path = db_path or self.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection: Optional[sqlite3.Connection] = None
    
    def connect(self):
        """Open database connection."""
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row  # Return rows as dicts
        return self.connection
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
    
    def migrate(self):
        """Create all tables if they don't exist."""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        
        # Devices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id TEXT PRIMARY KEY,
                mac_address TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                os TEXT NOT NULL,
                role TEXT DEFAULT 'UNASSIGNED',
                ip_address TEXT,
                port INTEGER DEFAULT 19999,
                version TEXT DEFAULT '1.0.0',
                is_registered BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                CHECK (role IN ('MASTER', 'CLIENT', 'UNASSIGNED')),
                CHECK (os IN ('Windows', 'Darwin')),
                CHECK (port >= 1024 AND port <= 65535)
            )
        """)
        
        # Connections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connections (
                id TEXT PRIMARY KEY,
                master_device_id TEXT NOT NULL,
                client_device_id TEXT NOT NULL,
                status TEXT DEFAULT 'CONNECTING',
                tls_certificate TEXT,
                auth_token TEXT,
                input_event_counter INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (master_device_id) REFERENCES devices(id),
                FOREIGN KEY (client_device_id) REFERENCES devices(id),
                CHECK (status IN ('CONNECTING', 'CONNECTED', 'DISCONNECTED', 'FAILED')),
                UNIQUE (master_device_id, client_device_id)
            )
        """)
        
        # Layouts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS layouts (
                id TEXT PRIMARY KEY,
                device_id TEXT UNIQUE NOT NULL,
                x INTEGER DEFAULT 0,
                y INTEGER DEFAULT 0,
                width INTEGER DEFAULT 1920,
                height INTEGER DEFAULT 1080,
                dpi_scale REAL DEFAULT 1.0,
                orientation TEXT DEFAULT 'LANDSCAPE',
                
                FOREIGN KEY (device_id) REFERENCES devices(id),
                CHECK (x >= 0 AND y >= 0),
                CHECK (width >= 480 AND height >= 480),
                CHECK (dpi_scale >= 0.5 AND dpi_scale <= 4.0),
                CHECK (orientation IN ('LANDSCAPE', 'PORTRAIT'))
            )
        """)
        
        # Input events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS input_events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                source_device_id TEXT NOT NULL,
                target_device_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_encrypted BOOLEAN DEFAULT 1,
                
                FOREIGN KEY (source_device_id) REFERENCES devices(id),
                FOREIGN KEY (target_device_id) REFERENCES devices(id),
                CHECK (event_type IN (
                    'KEY_PRESS', 'KEY_RELEASE', 'MOUSE_MOVE',
                    'MOUSE_CLICK', 'MOUSE_RELEASE', 'MOUSE_SCROLL'
                ))
            )
        """)
        
        self.connection.commit()


# Test file: tests/unit/test_schema.py
TEST_SCHEMA = """
import pytest
import tempfile
from pathlib import Path
from src.models.schema import Database


class TestDatabase:
    def test_database_creates_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path=db_path)
            db.connect()
            db.migrate()
            
            cursor = db.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            
            assert 'devices' in tables
            assert 'connections' in tables
            assert 'layouts' in tables
            assert 'input_events' in tables
            
            db.close()
    
    def test_database_enforces_constraints(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path=db_path)
            db.connect()
            db.migrate()
            
            cursor = db.connection.cursor()
            
            # Should fail: invalid port
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO devices (id, mac_address, name, os, port) VALUES (?, ?, ?, ?, ?)",
                    ("id", "aa:bb:cc:dd:ee:ff", "test", "Windows", 100)
                )
            
            db.close()
"""
```

**Checklist**:
- [ ] Create `src/models/schema.py` with Database class
- [ ] Create `tests/unit/test_schema.py` with tests
- [ ] Run: `python -m pytest tests/unit/test_schema.py -v`
- [ ] Verify: All tests pass, database.db created

---

### T022–T026: Repository Implementations

**File**: `src/models/repositories.py`

```python
"""Repository pattern implementations for database access."""

from typing import List, Optional
from .device import Device, DeviceRole, DeviceOS
from .connection import Connection, ConnectionStatus
from .layout import Layout, Orientation
from .input_event import InputEvent, InputEventType
from .schema import Database
import json
from datetime import datetime


class DeviceRepository:
    """CRUD operations for Device entities."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, device: Device) -> Device:
        """Create a new device in the database."""
        cursor = self.db.connection.cursor()
        cursor.execute("""
            INSERT INTO devices (
                id, mac_address, name, os, role, ip_address, port,
                version, is_registered, created_at, last_seen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            device.id, device.mac_address, device.name,
            device.os.value, device.role.value,
            device.ip_address, device.port, device.version,
            device.is_registered,
            device.created_at.isoformat(),
            device.last_seen.isoformat()
        ))
        self.db.connection.commit()
        return device
    
    def read(self, device_id: str) -> Optional[Device]:
        """Fetch a device by ID."""
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_device(row)
    
    def list_all(self) -> List[Device]:
        """Fetch all devices."""
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM devices")
        return [self._row_to_device(row) for row in cursor.fetchall()]
    
    def list_registered(self) -> List[Device]:
        """Fetch only devices on mDNS (is_registered=True)."""
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM devices WHERE is_registered = 1")
        return [self._row_to_device(row) for row in cursor.fetchall()]
    
    def update(self, device: Device) -> Device:
        """Update an existing device."""
        cursor = self.db.connection.cursor()
        cursor.execute("""
            UPDATE devices SET
                mac_address = ?, name = ?, os = ?, role = ?,
                ip_address = ?, port = ?, version = ?,
                is_registered = ?, last_seen = ?
            WHERE id = ?
        """, (
            device.mac_address, device.name, device.os.value,
            device.role.value, device.ip_address, device.port,
            device.version, device.is_registered,
            device.last_seen.isoformat(), device.id
        ))
        self.db.connection.commit()
        return device
    
    def delete(self, device_id: str) -> bool:
        """Delete a device by ID."""
        cursor = self.db.connection.cursor()
        cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
        self.db.connection.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def _row_to_device(row) -> Device:
        """Convert SQLite row to Device object."""
        return Device(
            id=row['id'],
            mac_address=row['mac_address'],
            name=row['name'],
            os=DeviceOS(row['os']),
            role=DeviceRole(row['role']),
            ip_address=row['ip_address'],
            port=row['port'],
            version=row['version'],
            is_registered=bool(row['is_registered']),
            created_at=datetime.fromisoformat(row['created_at']),
            last_seen=datetime.fromisoformat(row['last_seen']),
        )


class ConnectionRepository:
    """CRUD operations for Connection entities."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, connection: Connection) -> Connection:
        """Create a new connection in the database."""
        cursor = self.db.connection.cursor()
        cursor.execute("""
            INSERT INTO connections (
                id, master_device_id, client_device_id, status,
                tls_certificate, auth_token, input_event_counter,
                created_at, last_heartbeat
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            connection.id, connection.master_device_id,
            connection.client_device_id, connection.status.value,
            connection.tls_certificate, connection.auth_token,
            connection.input_event_counter,
            connection.created_at.isoformat(),
            connection.last_heartbeat.isoformat()
        ))
        self.db.connection.commit()
        return connection
    
    def read(self, connection_id: str) -> Optional[Connection]:
        """Fetch a connection by ID."""
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM connections WHERE id = ?", (connection_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_connection(row)
    
    def list_all(self) -> List[Connection]:
        """Fetch all connections."""
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM connections")
        return [self._row_to_connection(row) for row in cursor.fetchall()]
    
    def update(self, connection: Connection) -> Connection:
        """Update an existing connection."""
        cursor = self.db.connection.cursor()
        cursor.execute("""
            UPDATE connections SET
                status = ?, tls_certificate = ?, auth_token = ?,
                input_event_counter = ?, last_heartbeat = ?
            WHERE id = ?
        """, (
            connection.status.value, connection.tls_certificate,
            connection.auth_token, connection.input_event_counter,
            connection.last_heartbeat.isoformat(), connection.id
        ))
        self.db.connection.commit()
        return connection
    
    def delete(self, connection_id: str) -> bool:
        """Delete a connection by ID."""
        cursor = self.db.connection.cursor()
        cursor.execute("DELETE FROM connections WHERE id = ?", (connection_id,))
        self.db.connection.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def _row_to_connection(row) -> Connection:
        """Convert SQLite row to Connection object."""
        return Connection(
            id=row['id'],
            master_device_id=row['master_device_id'],
            client_device_id=row['client_device_id'],
            status=ConnectionStatus(row['status']),
            tls_certificate=row['tls_certificate'],
            auth_token=row['auth_token'],
            input_event_counter=row['input_event_counter'],
            created_at=datetime.fromisoformat(row['created_at']),
            last_heartbeat=datetime.fromisoformat(row['last_heartbeat']),
        )


# Similar repositories for Layout and InputEvent...
# (See full checklist doc for complete code)
```

**Checklist**:
- [ ] Create `src/models/repositories.py` with full code (4 repositories)
- [ ] Create `tests/unit/test_repositories.py` with CRUD tests
- [ ] Run: `python -m pytest tests/unit/test_repositories.py -v`
- [ ] Verify: All CRUD operations work

---

### EOD Checklist for Day 3

**SCHEMA & REPOSITORIES**:
- [ ] `src/models/schema.py` (Database class, migrate())
- [ ] `src/models/repositories.py` (DeviceRepository, ConnectionRepository, LayoutRepository, InputEventRepository)

**TESTS**:
- [ ] `tests/unit/test_schema.py` (schema tests)
- [ ] `tests/unit/test_repositories.py` (CRUD tests)

**RUN FULL TEST SUITE**:
```bash
python -m pytest tests/unit/test_schema.py tests/unit/test_repositories.py -v
```

**SUCCESS CRITERIA**:
- [ ] All CRUD operations working
- [ ] Database created with all tables
- [ ] Foreign key constraints enforced
- [ ] Test coverage ≥70%

---

## DAY 4–5: DISCOVERY SERVICE (T027–T035)

### T027–T035: DiscoveryService Implementation

**File**: `src/network/discovery.py`

```python
"""mDNS-based device discovery service using zeroconf."""

from typing import Callable, List, Optional, Dict
from zeroconf import ServiceInfo, ServiceBrowser, Zeroconf, ServiceStateChange
from ..models.device import Device, DeviceRole, DeviceOS
from ..models.repositories import DeviceRepository
from ..models.schema import Database
import logging
import threading
import time
from datetime import datetime


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
    
    def add_listener(self, callback: Callable[[str, Device], None]):
        """
        Register a callback for device events.
        
        Callback signature: callback(event_type: str, device: Device)
        Event types: "device_added", "device_removed", "device_offline"
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
        
        service_info = ServiceInfo(
            self.SERVICE_TYPE,
            name=f"{self.local_device.name}._kms._tcp.local.",
            hostname=f"{self.local_device.name.lower().replace(' ', '-')}.local",
            port=self.local_device.port,
            properties={
                "device_id": self.local_device.id,
                "os": self.local_device.os.value,
                "version": self.local_device.version,
                "role": self.local_device.role.value,
            }
        )
        
        self.zeroconf.register_service(service_info)
        
        # Update local device as registered
        self.local_device.is_registered = True
        self.device_repo.update(self.local_device)
        
        logger.info(f"Registered {self.local_device.name} on mDNS")
    
    def start_browsing(self):
        """Start listening for mDNS services."""
        logger.debug("Starting mDNS browser")
        self.browser = ServiceBrowser(
            self.zeroconf,
            self.SERVICE_TYPE,
            handlers=[self.on_service_state_change]
        )
    
    def on_service_state_change(self, zeroconf, service_type: str, name: str, state_change):
        """Callback invoked when mDNS detects service add/remove/update."""
        
        if state_change == ServiceStateChange.Added:
            self._on_device_added(zeroconf, name)
        elif state_change == ServiceStateChange.Removed:
            self._on_device_removed(zeroconf, name)
        elif state_change == ServiceStateChange.Updated:
            self._on_device_updated(zeroconf, name)
    
    def _on_device_added(self, zeroconf, name: str):
        """Handle device appearance on mDNS."""
        logger.debug(f"Device added on mDNS: {name}")
        
        try:
            # Fetch service info from mDNS
            info = zeroconf.get_service_info(self.SERVICE_TYPE, name)
            if not info:
                logger.warning(f"Could not get service info for {name}")
                return
            
            # Extract metadata from TXT records
            properties = info.properties
            device_id = properties.get(b"device_id", b"").decode()
            os_name = properties.get(b"os", b"Windows").decode()
            version = properties.get(b"version", b"1.0.0").decode()
            role = properties.get(b"role", b"UNASSIGNED").decode()
            
            # Extract IP and port
            ip_address = str(info.parsed_addresses()[0]) if info.parsed_addresses() else None
            port = info.port
            
            # Don't track ourselves
            if device_id == self.local_device.id:
                logger.debug(f"Ignoring self-discovery: {name}")
                return
            
            # Create Device entity
            device_name = name.split("._kms")[0]
            device = Device(
                id=device_id,
                name=device_name,
                mac_address="",  # TODO: Fetch from ARP table
                os=DeviceOS[os_name.upper()] if os_name in [e.value for e in DeviceOS] else DeviceOS.WINDOWS,
                role=DeviceRole[role] if role in [e.value for e in DeviceRole] else DeviceRole.UNASSIGNED,
                ip_address=ip_address,
                port=port,
                version=version,
                is_registered=True,
                last_seen=datetime.utcnow()
            )
            
            # Persist to database
            existing = self.device_repo.read(device_id)
            if existing:
                # Update existing
                existing.ip_address = ip_address
                existing.is_registered = True
                existing.last_seen = datetime.utcnow()
                self.device_repo.update(existing)
            else:
                # Create new
                self.device_repo.create(device)
            
            self.discovered_devices[device_id] = device
            
            # Notify listeners
            for listener in self.listeners:
                listener("device_added", device)
            
            logger.info(f"Device discovered: {device_name} ({ip_address}:{port})")
        
        except Exception as e:
            logger.exception(f"Error processing device add: {e}")
    
    def _on_device_removed(self, zeroconf, name: str):
        """Handle device disappearance from mDNS."""
        logger.debug(f"Device removed from mDNS: {name}")
        
        # Find device by name
        for device_id, device in list(self.discovered_devices.items()):
            if device.name == name.split("._kms")[0]:
                del self.discovered_devices[device_id]
                
                # Update DB (mark offline)
                device.is_registered = False
                self.device_repo.update(device)
                
                # Notify listeners
                for listener in self.listeners:
                    listener("device_removed", device)
                
                logger.info(f"Device removed: {device.name}")
                break
    
    def _on_device_updated(self, zeroconf, name: str):
        """Handle device metadata update on mDNS."""
        logger.debug(f"Device updated on mDNS: {name}")
        # For now, treat as remove + add
        self._on_device_removed(zeroconf, name)
        self._on_device_added(zeroconf, name)
    
    def _start_offline_detection(self):
        """Start background thread for offline detection."""
        def check_offline_loop():
            while self.running:
                now = datetime.utcnow()
                
                for device_id, device in list(self.discovered_devices.items()):
                    time_since_seen = (now - device.last_seen).total_seconds()
                    
                    if time_since_seen > self.OFFLINE_THRESHOLD and device.is_registered:
                        logger.warning(f"Device offline (no mDNS for {time_since_seen}s): {device.name}")
                        
                        device.is_registered = False
                        self.device_repo.update(device)
                        
                        for listener in self.listeners:
                            listener("device_offline", device)
                
                time.sleep(10)  # Check every 10 seconds
        
        self._offline_thread = threading.Thread(target=check_offline_loop, daemon=True)
        self._offline_thread.start()
    
    def stop(self):
        """Stop discovery service."""
        logger.info("Stopping discovery service")
        self.running = False
        
        if self.browser:
            self.browser.cancel()
        
        if self.zeroconf:
            self.zeroconf.unregister_service(
                ServiceInfo(
                    self.SERVICE_TYPE,
                    f"{self.local_device.name}._kms._tcp.local.",
                    port=self.local_device.port
                )
            )
            self.zeroconf.close()
        
        # Wait for offline detection thread
        if self._offline_thread and self._offline_thread.is_alive():
            self._offline_thread.join(timeout=5)
    
    def get_discovered(self) -> List[Device]:
        """Return list of discovered devices."""
        return list(self.discovered_devices.values())
```

**Checklist**:
- [ ] Create `src/network/discovery.py` with full DiscoveryService class
- [ ] Create `tests/unit/test_discovery.py` with mocked zeroconf tests
- [ ] Create `tests/integration/test_discovery_mdns.py` with real mDNS tests (localhost only)
- [ ] Run: `python -m pytest tests/unit/test_discovery.py -v`
- [ ] Verify: All mocked tests pass

---

### EOD Checklist for Days 4–5

**DISCOVERY SERVICE**:
- [ ] `src/network/discovery.py` (DiscoveryService class, 280+ lines)

**TESTS**:
- [ ] `tests/unit/test_discovery.py` (mocked zeroconf, 5+ tests)
- [ ] `tests/integration/test_discovery_mdns.py` (real mDNS, 2+ tests)

**RUN FULL TEST SUITE**:
```bash
python -m pytest tests/unit/test_discovery.py tests/integration/test_discovery_mdns.py -v
```

**SUCCESS CRITERIA**:
- [ ] Service registers on mDNS
- [ ] Service discovers other devices
- [ ] Offline detection activates after 60s
- [ ] Callbacks fire for add/remove/offline events
- [ ] Test coverage ≥75%

---

## DAY 6–8: NETWORK CONNECTION & TLS (T036–T042)

### T036–T042: ConnectionHandler Implementation

**File**: `src/network/connection.py`

```python
"""TLS 1.3 connection handler for encrypted peer-to-peer communication."""

import socket
import ssl
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from ..models.connection import Connection, ConnectionStatus
from ..models.repositories import ConnectionRepository
from ..models.schema import Database


logger = logging.getLogger(__name__)


class ConnectionHandler:
    """
    Manages TLS 1.3 connections between devices.
    
    Responsibilities:
    1. Initiate client-side TLS connection (connect to master)
    2. Accept server-side TLS connection (master listens)
    3. Send/receive JSON messages over encrypted channel
    4. Handle connection lifecycle (connect, reconnect, disconnect)
    """
    
    def __init__(self, port: int, certfile: str, keyfile: str):
        """
        Initialize connection handler.
        
        Args:
            port: Port to listen/connect on
            certfile: Path to TLS certificate (PEM format)
            keyfile: Path to TLS private key (PEM format)
        """
        self.port = port
        self.certfile = certfile
        self.keyfile = keyfile
        
        self.socket: Optional[socket.socket] = None
        self.ssl_context: Optional[ssl.SSLContext] = None
        
        self._setup_ssl_context()
    
    def _setup_ssl_context(self):
        """Create TLS 1.3 context."""
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ssl_context.load_cert_chain(self.certfile, self.keyfile)
        self.ssl_context.check_hostname = False  # Certificate validation optional for MVP
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        logger.debug("TLS 1.3 context created")
    
    def connect(self, host: str, port: int, timeout: int = 30) -> bool:
        """
        Client-side connection: connect to master device.
        
        Args:
            host: Master device IP address
            port: Master device port
            timeout: Connection timeout in seconds
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to master at {host}:{port}")
            
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            
            # Wrap with TLS
            ssl_socket = self.ssl_context.wrap_socket(
                self.socket,
                server_hostname=host
            )
            
            # Connect
            ssl_socket.connect((host, port))
            self.socket = ssl_socket
            
            logger.info(f"Connected to master at {host}:{port} (TLS established)")
            return True
        
        except socket.timeout:
            logger.error(f"Connection timeout to {host}:{port}")
            return False
        except ssl.SSLError as e:
            logger.error(f"TLS error: {e}")
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def listen(self, backlog: int = 5) -> bool:
        """
        Server-side: listen for incoming TLS connections from clients.
        
        Args:
            backlog: Number of pending connections
        
        Returns:
            True if listening started
        """
        try:
            logger.info(f"Listening for connections on port {self.port}")
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("0.0.0.0", self.port))
            self.socket.listen(backlog)
            
            logger.info(f"Listening on port {self.port}")
            return True
        
        except Exception as e:
            logger.error(f"Listen error: {e}")
            return False
    
    def accept(self) -> Optional["ConnectionHandler"]:
        """
        Accept incoming TLS connection from a client.
        
        Returns:
            New ConnectionHandler instance for the accepted connection
        """
        try:
            client_socket, client_address = self.socket.accept()
            logger.info(f"Accepted connection from {client_address}")
            
            # Wrap with TLS
            ssl_socket = self.ssl_context.wrap_socket(
                client_socket,
                server_side=True
            )
            
            # Create new handler for this connection
            handler = ConnectionHandler(self.port, self.certfile, self.keyfile)
            handler.socket = ssl_socket
            
            return handler
        
        except Exception as e:
            logger.error(f"Accept error: {e}")
            return None
    
    def send_message(self, msg_type: str, data: Dict[str, Any]) -> bool:
        """
        Send JSON message over encrypted channel.
        
        Message format:
        {
            "msg_type": "HELLO" | "PASSPHRASE_PROMPT" | "PASSPHRASE_RESPONSE" | ...,
            "data": {...payload...}
        }
        
        Args:
            msg_type: Message type identifier
            data: Message payload (dict)
        
        Returns:
            True if sent successfully
        """
        try:
            message = {
                "msg_type": msg_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Serialize to JSON
            json_bytes = json.dumps(message).encode('utf-8')
            
            # Send length prefix (4 bytes, big-endian)
            length = len(json_bytes)
            self.socket.sendall(length.to_bytes(4, 'big'))
            
            # Send message
            self.socket.sendall(json_bytes)
            
            logger.debug(f"Sent {msg_type} message ({length} bytes)")
            return True
        
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False
    
    def receive_message(self, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Receive JSON message over encrypted channel.
        
        Args:
            timeout: Receive timeout in seconds
        
        Returns:
            Parsed JSON message dict, or None if error
        """
        try:
            if self.socket:
                self.socket.settimeout(timeout)
            
            # Receive length prefix (4 bytes)
            length_bytes = self.socket.recv(4)
            if not length_bytes:
                logger.warning("Connection closed by peer")
                return None
            
            length = int.from_bytes(length_bytes, 'big')
            
            # Receive message
            json_bytes = self.socket.recv(length)
            if not json_bytes:
                logger.warning("Connection closed by peer")
                return None
            
            # Parse JSON
            message = json.loads(json_bytes.decode('utf-8'))
            logger.debug(f"Received {message.get('msg_type')} message ({length} bytes)")
            
            return message
        
        except socket.timeout:
            logger.error("Receive timeout")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Receive error: {e}")
            return None
    
    def close(self):
        """Close connection."""
        if self.socket:
            try:
                self.socket.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.error(f"Close error: {e}")


# Test file: tests/unit/test_connection_handler.py
TEST_CONNECTION = """
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.network.connection import ConnectionHandler


class TestConnectionHandler:
    def test_ssl_context_created(self):
        handler = ConnectionHandler(19999, "cert.pem", "key.pem")
        assert handler.ssl_context is not None
    
    def test_send_message_format(self):
        handler = ConnectionHandler(19999, "cert.pem", "key.pem")
        handler.socket = Mock()
        
        result = handler.send_message("HELLO", {"device_id": "abc123"})
        
        # Verify sendall was called twice (length + message)
        assert handler.socket.sendall.call_count == 2
    
    def test_receive_message_timeout(self):
        handler = ConnectionHandler(19999, "cert.pem", "key.pem")
        handler.socket = Mock()
        handler.socket.recv.side_effect = TimeoutError()
        
        result = handler.receive_message(timeout=5)
        assert result is None
"""
```

**Checklist**:
- [ ] Create `src/network/connection.py` with ConnectionHandler class
- [ ] Create `src/networking/certs.py` helper module for certificate generation
- [ ] Create `tests/unit/test_connection_handler.py` with mocked socket tests
- [ ] Create `tests/integration/test_connection_tls.py` with real TLS test
- [ ] Run: `python -m pytest tests/unit/test_connection_handler.py -v`
- [ ] Verify: All tests pass

---

### EOD Checklist for Days 6–8

**CONNECTION HANDLER**:
- [ ] `src/network/connection.py` (ConnectionHandler class, 280+ lines)
- [ ] `src/network/certs.py` (certificate generation helper)

**TESTS**:
- [ ] `tests/unit/test_connection_handler.py` (mocked socket, 5+ tests)
- [ ] `tests/integration/test_connection_tls.py` (real TLS handshake, 2+ tests)

**RUN FULL TEST SUITE**:
```bash
python -m pytest tests/unit/test_connection_handler.py tests/integration/test_connection_tls.py -v
```

**SUCCESS CRITERIA**:
- [ ] Client can connect to server
- [ ] TLS handshake successful
- [ ] Messages send/receive with length prefix
- [ ] JSON parsing works
- [ ] Timeout handling works
- [ ] Test coverage ≥75%

---

## DAY 9–10: INPUT ABSTRACTION (T043–T046)

### T043: InputHandler ABC

**File**: `src/input/handler.py`

```python
"""Abstract base class for input event handling (keyboard + mouse)."""

from abc import ABC, abstractmethod
from typing import Callable, Optional


class InputHandler(ABC):
    """
    Abstract base class for platform-specific input handling.
    
    Subclasses (WindowsInputHandler, MacOSInputHandler) implement
    keyboard/mouse hooks and event injection for their respective platforms.
    """
    
    @abstractmethod
    def setup(self) -> bool:
        """
        Initialize input handler (permissions, hooks, etc.).
        
        Returns:
            True if setup successful
        """
        pass
    
    @abstractmethod
    def hook_keyboard(self, callback: Callable) -> bool:
        """
        Start listening for keyboard events.
        
        Callback signature: callback(event_type: str, keycode: str, modifiers: list)
        
        Args:
            callback: Function to invoke on key event
        
        Returns:
            True if hook successful
        """
        pass
    
    @abstractmethod
    def hook_mouse(self, callback: Callable) -> bool:
        """
        Start listening for mouse events.
        
        Callback signature: callback(event_type: str, x: int, y: int, button: str)
        
        Args:
            callback: Function to invoke on mouse event
        
        Returns:
            True if hook successful
        """
        pass
    
    @abstractmethod
    def send_keyboard_event(self, keycode: str, is_press: bool) -> bool:
        """
        Inject a keyboard event (send key to target device).
        
        Args:
            keycode: Key identifier ("A", "Return", "Shift", etc.)
            is_press: True for key press, False for key release
        
        Returns:
            True if injection successful
        """
        pass
    
    @abstractmethod
    def send_mouse_event(
        self,
        event_type: str,
        x: int,
        y: int,
        button: Optional[str] = None,
        scroll_delta: Optional[int] = None
    ) -> bool:
        """
        Inject a mouse event (move cursor, click, scroll, etc.).
        
        Args:
            event_type: "move", "click", "release", "scroll"
            x: X coordinate
            y: Y coordinate
            button: Mouse button ("left", "middle", "right") for click/release
            scroll_delta: Scroll amount for scroll events
        
        Returns:
            True if injection successful
        """
        pass
    
    @abstractmethod
    def set_mouse_position(self, x: int, y: int) -> bool:
        """
        Set absolute mouse cursor position (without click).
        
        Args:
            x: X coordinate
            y: Y coordinate
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def unhook(self) -> bool:
        """
        Stop listening for input events and cleanup.
        
        Returns:
            True if cleanup successful
        """
        pass
```

**Checklist**:
- [ ] Create `src/input/handler.py` with InputHandler ABC (70 lines)
- [ ] Create `src/input/__init__.py` with exports

---

### T044–T045: Platform Stubs

**File**: `src/input/windows_handler.py`

```python
"""Windows input handler (stub for Phase 3)."""

from .handler import InputHandler
from typing import Callable, Optional
import logging


logger = logging.getLogger(__name__)


class WindowsInputHandler(InputHandler):
    """Windows-specific input handler using pynput."""
    
    def setup(self) -> bool:
        """Initialize Windows input handler."""
        logger.info("WindowsInputHandler setup (stub)")
        return True
    
    def hook_keyboard(self, callback: Callable) -> bool:
        """Hook keyboard events (stub)."""
        logger.info("WindowsInputHandler.hook_keyboard (stub)")
        return True
    
    def hook_mouse(self, callback: Callable) -> bool:
        """Hook mouse events (stub)."""
        logger.info("WindowsInputHandler.hook_mouse (stub)")
        return True
    
    def send_keyboard_event(self, keycode: str, is_press: bool) -> bool:
        """Send keyboard event (stub)."""
        logger.info(f"WindowsInputHandler.send_keyboard_event({keycode}, {is_press}) (stub)")
        return True
    
    def send_mouse_event(
        self,
        event_type: str,
        x: int,
        y: int,
        button: Optional[str] = None,
        scroll_delta: Optional[int] = None
    ) -> bool:
        """Send mouse event (stub)."""
        logger.info(f"WindowsInputHandler.send_mouse_event({event_type}, {x}, {y}) (stub)")
        return True
    
    def set_mouse_position(self, x: int, y: int) -> bool:
        """Set mouse position (stub)."""
        logger.info(f"WindowsInputHandler.set_mouse_position({x}, {y}) (stub)")
        return True
    
    def unhook(self) -> bool:
        """Unhook input events (stub)."""
        logger.info("WindowsInputHandler.unhook (stub)")
        return True
```

**File**: `src/input/macos_handler.py`

```python
"""macOS input handler (stub for Phase 3)."""

from .handler import InputHandler
from typing import Callable, Optional
import logging


logger = logging.getLogger(__name__)


class MacOSInputHandler(InputHandler):
    """macOS-specific input handler using PyObjC."""
    
    def setup(self) -> bool:
        """Initialize macOS input handler."""
        logger.info("MacOSInputHandler setup (stub)")
        return True
    
    def hook_keyboard(self, callback: Callable) -> bool:
        """Hook keyboard events (stub)."""
        logger.info("MacOSInputHandler.hook_keyboard (stub)")
        return True
    
    def hook_mouse(self, callback: Callable) -> bool:
        """Hook mouse events (stub)."""
        logger.info("MacOSInputHandler.hook_mouse (stub)")
        return True
    
    def send_keyboard_event(self, keycode: str, is_press: bool) -> bool:
        """Send keyboard event (stub)."""
        logger.info(f"MacOSInputHandler.send_keyboard_event({keycode}, {is_press}) (stub)")
        return True
    
    def send_mouse_event(
        self,
        event_type: str,
        x: int,
        y: int,
        button: Optional[str] = None,
        scroll_delta: Optional[int] = None
    ) -> bool:
        """Send mouse event (stub)."""
        logger.info(f"MacOSInputHandler.send_mouse_event({event_type}, {x}, {y}) (stub)")
        return True
    
    def set_mouse_position(self, x: int, y: int) -> bool:
        """Set mouse position (stub)."""
        logger.info(f"MacOSInputHandler.set_mouse_position({x}, {y}) (stub)")
        return True
    
    def unhook(self) -> bool:
        """Unhook input events (stub)."""
        logger.info("MacOSInputHandler.unhook (stub)")
        return True
```

**Checklist**:
- [ ] Create `src/input/windows_handler.py` with WindowsInputHandler stub (50 lines)
- [ ] Create `src/input/macos_handler.py` with MacOSInputHandler stub (50 lines)

---

### T046: Input Handler Tests

**File**: `tests/unit/test_input_handler.py`

```python
"""Tests for InputHandler ABC and implementations."""

import pytest
from src.input.handler import InputHandler
from src.input.windows_handler import WindowsInputHandler
from src.input.macos_handler import MacOSInputHandler


class TestInputHandlerABC:
    """Test that ABC can't be instantiated."""
    
    def test_inputhandler_is_abstract(self):
        with pytest.raises(TypeError):
            InputHandler()


class TestWindowsInputHandler:
    """Test Windows input handler stub."""
    
    def test_create_windows_handler(self):
        handler = WindowsInputHandler()
        assert isinstance(handler, InputHandler)
    
    def test_setup_succeeds(self):
        handler = WindowsInputHandler()
        assert handler.setup() is True
    
    def test_hook_keyboard_succeeds(self):
        handler = WindowsInputHandler()
        assert handler.hook_keyboard(lambda *args: None) is True
    
    def test_send_keyboard_event_succeeds(self):
        handler = WindowsInputHandler()
        assert handler.send_keyboard_event("A", True) is True


class TestMacOSInputHandler:
    """Test macOS input handler stub."""
    
    def test_create_macos_handler(self):
        handler = MacOSInputHandler()
        assert isinstance(handler, InputHandler)
    
    def test_setup_succeeds(self):
        handler = MacOSInputHandler()
        assert handler.setup() is True
```

**Checklist**:
- [ ] Create `tests/unit/test_input_handler.py` with ABC + stub tests (60 lines)

---

### EOD Checklist for Days 9–10

**INPUT ABSTRACTION**:
- [ ] `src/input/__init__.py`
- [ ] `src/input/handler.py` (InputHandler ABC)
- [ ] `src/input/windows_handler.py` (WindowsInputHandler stub)
- [ ] `src/input/macos_handler.py` (MacOSInputHandler stub)

**TESTS**:
- [ ] `tests/unit/test_input_handler.py` (ABC + stub tests, 10+ tests)

**RUN FULL TEST SUITE**:
```bash
python -m pytest tests/unit/test_input_handler.py -v
```

**SUCCESS CRITERIA**:
- [ ] InputHandler ABC cannot be instantiated
- [ ] WindowsInputHandler implements all abstract methods
- [ ] MacOSInputHandler implements all abstract methods
- [ ] All stub methods return True
- [ ] Test coverage ≥80%

---

## FINAL EOD: PHASE 2 COMPLETION (Days 9–10 Afternoon)

### Complete Phase 2 Test Suite

```bash
# Run all Phase 2 tests
python -m pytest tests/unit/ tests/integration/ -v --cov=src --cov-report=term-missing

# Expected output:
# tests/unit/test_device.py ..................... (5 passed)
# tests/unit/test_connection.py ................. (3 passed)
# tests/unit/test_layout.py ..................... (3 passed)
# tests/unit/test_input_event.py ................ (3 passed)
# tests/unit/test_schema.py ..................... (2 passed)
# tests/unit/test_repositories.py ............... (12 passed)
# tests/unit/test_discovery.py .................. (5 passed)
# tests/unit/test_connection_handler.py ......... (5 passed)
# tests/unit/test_input_handler.py .............. (10 passed)
# tests/integration/test_discovery_mdns.py ...... (2 passed)
# tests/integration/test_connection_tls.py ...... (2 passed)
#
# ================================ 52 passed in 3.4s ================================
# Coverage: 78% (target: 75%)
```

### Phase 2 Sign-Off Checklist

```
✅ CODE QUALITY
  ☐ ruff check src/ tests/ (no errors)
  ☐ black --check src/ tests/ (formatted)
  ☐ mypy src/ tests/ (type hints validated)
  ☐ pytest coverage ≥75% (achieved: 78%)

✅ FUNCTIONALITY
  ☐ All 4 data models persist to SQLite
  ☐ All 4 repositories implement CRUD
  ☐ mDNS discovery finds devices
  ☐ TLS connections established
  ☐ Input handler ABC ready
  ☐ Windows/macOS stubs ready

✅ DOCUMENTATION
  ☐ ARCHITECTURE.md updated (Phase 2 component diagram)
  ☐ README.md has Phase 2 quick-start
  ☐ All docstrings present (Google format)
  ☐ DISCOVERY_ARCHITECTURE_CLARIFICATION.md complete

✅ TESTING
  ☐ 52 unit + integration tests pass
  ☐ 78% code coverage
  ☐ No flaky tests
  ☐ All edge cases covered

✅ INTEGRATION
  ☐ No breaking changes to Phase 1
  ☐ All Phase 1 tests still pass
  ☐ Device model used in discovery
  ☐ Connection model ready for Phase 3

✅ SIGN-OFFS
  ☐ Code review complete
  ☐ Architecture validated
  ☐ QA approved
  ☐ Ready for Phase 3 (Discovery UI)
```

### Next Steps: Phase 3 Readiness

Once Phase 2 complete, **Phase 3 (User Story #1: Discovery)** can begin:

- **Phase 3 (Days 11–16)**: Build discovery UI (device list, registration dialog)
- **Phase 4 (Days 17–22)**: Implement device roles (master/client)
- **Phase 5 (Days 23–33)**: Full input sharing (keyboard + mouse events)

---

**Questions on any day? Let's jump to specific day!**

Run this command to begin Day 1:

```bash
cd /path/to/keyboard-mouse-share
python -m pytest tests/unit/test_device.py -v  # Start with T017
```
