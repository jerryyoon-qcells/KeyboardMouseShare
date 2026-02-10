# Data Model: Cross-Device Input Sharing

**Feature**: Cross-Device Input Sharing (001-cross-device-input)  
**Created**: 2026-02-09  
**Status**: Design Phase 1

## Entity Definitions

### Device

Represents a machine running Keyboard Mouse Share application.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | UUID | Primary Key | Unique identifier; generated on first run; persisted across restarts |
| `mac_address` | String | Unique, immutable | Physical MAC address (fallback identifier) |
| `name` | String | Required, max 50 chars | User-friendly name (e.g., "Jerry's MacBook", "Windows Desktop") |
| `os` | Enum[WINDOWS, MACOS] | Required, immutable | Operating system |
| `role` | Enum[MASTER, CLIENT, UNASSIGNED] | Required, mutable | Master controls input; clients receive input |
| `ip_address` | String | Mutable | Current IP on network (changes if using DHCP) |
| `port` | Integer | Mutable | Listening port for TLS connections (default: 19999) |
| `version` | String | Required | App version (e.g., "1.0.0") for backward compatibility checks |
| `discovery_timestamp` | DateTime | Auto-set | When device was first discovered via mDNS |
| `last_seen` | DateTime | Auto-update | When device was last seen on network (for offline detection) |
| `is_registered` | Boolean | Default: false | True if user clicked "Register" or completed pairing |
| `created_at` | DateTime | Auto-set | When this Device record was created |
| `updated_at` | DateTime | Auto-update | When this record was last modified |

**Relationships**:
- One Device can have many Connections (as master or client)
- One Device can have one Layout configuration
- One Device can have many InputEvents (as source or target)

**Constraints**:
- A network can have AT MOST one MASTER device (validated on role change)
- A device MUST have `is_registered = true` before accepting connections
- `mac_address` is immutable; used to detect duplicate device registration

**Example**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "mac_address": "A1:B2:C3:D4:E5:F6",
  "name": "Jerry's MacBook",
  "os": "MACOS",
  "role": "MASTER",
  "ip_address": "192.168.1.101",
  "port": 19999,
  "version": "1.0.0",
  "discovery_timestamp": "2026-02-09T14:00:00Z",
  "last_seen": "2026-02-09T14:30:00Z",
  "is_registered": true,
  "created_at": "2026-02-09T14:00:00Z",
  "updated_at": "2026-02-09T14:30:00Z"
}
```

---

### Connection

Represents an established link between a master and a client device for encrypted input transmission.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | String | Primary Key | Format: "{master_id}-{client_id}" |
| `master_device_id` | UUID | Foreign Key, Required | Reference to master Device |
| `client_device_id` | UUID | Foreign Key, Required | Reference to client Device |
| `encryption_key` | Bytes | Required | TLS certificate (PEM-encoded) for this connection |
| `encryption_key_hash` | String | Required | SHA256 hash of encryption_key for integrity checks |
| `status` | Enum[CONNECTING, CONNECTED, DISCONNECTED, FAILED] | Required | Connection lifecycle state |
| `auth_token` | String | Required after pairing | Secure token for subsequent connections without re-pairing |
| `established_timestamp` | DateTime | Set on CONNECTED | When TLS handshake completed |
| `disconnected_timestamp` | DateTime | Set on DISCONNECTED | When connection was closed (for retry delay) |
| `input_event_counter` | Integer | Default: 0 | Audit: count of input events transmitted |
| `input_event_last_timestamp` | DateTime | Auto-update | Timestamp of last input event (for timeout detection) |
| `failures_count` | Integer | Default: 0 | Number of failed auth attempts (triggers exponential backoff) |
| `created_at` | DateTime | Auto-set | When this Connection was first attempted |
| `updated_at` | DateTime | Auto-update | Last state change |

**Relationships**:
- Many InputEvents reference a Connection's master/client pair

**Constraints**:
- A Connection is unidirectional: master is always the input source
- A Device can have multiple Connections (one per other device)
- Only one active Connection per (master, client) pair allowed
- `status` transitions: CONNECTING → CONNECTED → DISCONNECTED (only forward; reconnect creates new Connection)

**Example**:
```json
{
  "id": "550e8400-abc-bcd-abc-446655440000-550e8400-def-def-def-446655440001",
  "master_device_id": "550e8400-abc-bcd-abc-446655440000",
  "client_device_id": "550e8400-def-def-def-446655440001",
  "encryption_key": "-----BEGIN CERTIFICATE-----\nMIID...",
  "encryption_key_hash": "sha256:abc123def456...",
  "status": "CONNECTED",
  "auth_token": "dGVzdGF1dGh0b2tlbg==",
  "established_timestamp": "2026-02-09T14:05:00Z",
  "disconnected_timestamp": null,
  "input_event_counter": 1234,
  "input_event_last_timestamp": "2026-02-09T14:30:00Z",
  "failures_count": 0,
  "created_at": "2026-02-09T14:05:00Z",
  "updated_at": "2026-02-09T14:30:00Z"
}
```

---

### Layout

Represents the spatial configuration of devices on the user's desk.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | String | Primary Key | Format: "layout_{device_id}" |
| `device_id` | UUID | Foreign Key, Required | Which device this layout config applies to |
| `x_offset` | Integer | Required | Pixel X coordinate (relative to origin, e.g., 0, 1920, -1920) |
| `y_offset` | Integer | Required | Pixel Y coordinate (relative to origin) |
| `screen_width` | Integer | Required | Native resolution width in pixels |
| `screen_height` | Integer | Required | Native resolution height in pixels |
| `orientation` | Enum[LANDSCAPE, PORTRAIT] | Required | Screen orientation |
| `dpi_scale` | Float | Default: 1.0 | For high-DPI displays (e.g., 1.5, 2.0 on Retina, 4K) |
| `scale_factor` | Float | Default: 1.0 | OS-level scaling (macOS: 1.0 or 2.0 for Retina; Windows: varies) |
| `monitor_index` | Integer | Optional | For multi-monitor systems; which monitor on this device (0, 1, 2) |
| `created_at` | DateTime | Auto-set | When layout was created |
| `updated_at` | DateTime | Auto-update | When layout was last modified |

**Relationships**:
- One Device has one Layout record (or none if layout not configured)

**Constraints**:
- All devices in a multi-device setup should have LANDSCAPE orientation (v1 assumption)
- Screen dimensions must be positive integers
- No validation on X/Y overlap or gaps (user can create; system warns

**Example**:
```json
{
  "id": "layout_550e8400-abc-bcd-abc-446655440000",
  "device_id": "550e8400-abc-bcd-abc-446655440000",
  "x_offset": 0,
  "y_offset": 0,
  "screen_width": 1920,
  "screen_height": 1080,
  "orientation": "LANDSCAPE",
  "dpi_scale": 1.0,
  "scale_factor": 1.0,
  "monitor_index": 0,
  "created_at": "2026-02-09T14:10:00Z",
  "updated_at": "2026-02-09T14:10:00Z"
}
```

---

### InputEvent

Represents a keyboard or mouse event to be transmitted from master to client.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-----------|-------------|
| `id` | UUID | Primary Key | Generated per event |
| `event_type` | Enum[KEY_PRESS, KEY_RELEASE, MOUSE_MOVE, MOUSE_CLICK, MOUSE_SCROLL] | Required | Type of input |
| `keycode` | Integer | Conditional (if KEY_*) | Virtual key code (cross-platform: will be translated) |
| `key_name` | String | Conditional (if KEY_*) | Human-readable key (e.g., "A", "Return", "LeftShift") |
| `modifiers` | Set[String] | Optional | Active modifiers: CTRL, ALT, SHIFT, META (OS-specific: Cmd on macOS, Win on Windows) |
| `button` | Enum[LEFT, MIDDLE, RIGHT, SCROLL_UP, SCROLL_DOWN] | Optional | Which mouse button (if MOUSE_CLICK or MOUSE_SCROLL) |
| `x` | Integer | Conditional (if MOUSE_*) | X coordinate (relative to master device's screen) |
| `y` | Integer | Conditional (if MOUSE_*) | Y coordinate (relative to master device's screen) |
| `scroll_delta` | Integer | Conditional (if MOUSE_SCROLL) | Scroll amount (positive = up, negative = down) |
| `source_device_id` | UUID | Required | Which device generated this (always master) |
| `target_device_id` | UUID | Required | Which device should receive this (client) |
| `connection_id` | String | Foreign Key, Optional | Reference to Connection for auditing |
| `timestamp` | DateTime | Auto-set, UTC | When event was generated on master |
| `client_received_timestamp` | DateTime | Optional | When client received the event (for latency tracking) |
| `client_executed_timestamp` | DateTime | Optional | When client actually simulated the event (for debugging) |
| `is_encrypted` | Boolean | Default: true | Always encrypted; included for audit trail |
| `is_delivered` | Boolean | Default: false | Set to true after client acknowledges receipt |
| `sequence_number` | Integer | Required | For ordering events; incremented per connection per session |

**Relationships**:
- References Connection by (source_device_id, target_device_id) pair
- Transient: not persisted by default (in-memory only, per Constitution privacy principle)
- Audit logs: Timestamps + counters logged; payloads NOT logged by default

**Constraints**:
- Events older than 1 second are dropped (assumption: LAN latency < 1s)
- `sequence_number` resets on connection restart
- Encrypted before transmission; decrypted only on target device

**Example**:
```json
{
  "id": "12345678-1234-1234-1234-123456789012",
  "event_type": "KEY_PRESS",
  "keycode": 65,
  "key_name": "A",
  "modifiers": ["CTRL"],
  "button": null,
  "x": null,
  "y": null,
  "scroll_delta": null,
  "source_device_id": "550e8400-abc-bcd-abc-446655440000",
  "target_device_id": "550e8400-def-def-def-446655440001",
  "connection_id": "550e8400-abc-abc-abc-446655440000-550e8400-def-def-def-446655440001",
  "timestamp": "2026-02-09T14:30:00.123Z",
  "client_received_timestamp": "2026-02-09T14:30:00.145Z",
  "client_executed_timestamp": "2026-02-09T14:30:00.150Z",
  "is_encrypted": true,
  "is_delivered": true,
  "sequence_number": 42
}
```

---

## State Machine

### Device Role Transitions

```
Initial State:
┌─────────────────────────────────────────────────────────────┐
│ UNASSIGNED (user has not selected master or client role)    │
└─────────────────────────────────────────────────────────────┘
                          ↓ (user picks role)
            ┌─────────────┴─────────────┐
            ↓                           ↓
      ┌──────────┐              ┌──────────┐
      │ MASTER   │              │ CLIENT   │
      └──────────┘              └──────────┘
      (input source)            (input receiver)
            ↔ ←────────────────→ ↔
            (can switch roles at runtime)

Error State: If user tries to set second device as MASTER
├─ System detects: Multiple MASTERs exist
├─ Error popup: "Only one master allowed"
├─ Revert second device to UNASSIGNED or demote first to CLIENT
└─ Resolution: User reconfigures
```

### Connection Lifecycle

```
User initiates connection from client device:

1. CONNECTING
   ├─ Client discovers master via mDNS
   ├─ Client sends HELLO packet (version, device_id)
   ├─ Master displays passphrase prompt to user
   └─ Waiting for passphrase entry...

2. PASSPHRASE_AUTH
   ├─ Client prompts user to enter 6-char passphrase
   ├─ Client sends passphrase hash → Master
   ├─ Master verifies: if correct → proceed; else → increment failures_count, retry
   └─ Passphrase max attempts: 3; then exponential backoff (30s, 60s, 120s)

3. TLS_HANDSHAKE
   ├─ Master generates TLS certificate for this client
   ├─ Certificate exchange over authenticated channel
   ├─ TLS 1.3 encrypted session established
   └─ Master saves encryption_key + auth_token locally

4. CONNECTED
   ├─ Master → Client: ACK + client_role assignment
   ├─ Client stores auth_token (for future reconnections)
   ├─ Input transmission enabled
   └─ Heartbeat: periodic ping/pong to detect disconnection

5. DISCONNECTED / RECONNECTING
   ├─ Network timeout (no heartbeat for 30s)
   ├─ Or user clicks "Disconnect"
   ├─ Input transmission paused
   ├─ Attempt to reconnect if auto-reconnect enabled (default: YES)
   ├─ Exponential backoff on failures: 5s, 10s, 30s, 60s
   └─ Max retries: 10; then give up, mark as offline

6. FAILED
   ├─ Passphrase auth failed (max 3 attempts)
   ├─ Or: TLS certificate validation failed
   ├─ Or: Network unreachable
   └─ User must re-initiate connection (no auto-retry)
```

---

## Database Schema

**Storage Options**:
- Option 1: SQLite (default) - `~/.keyboard-mouse-share/device_registry.db`
- Option 2: JSON files - `~/.keyboard-mouse-share/devices.json`, `connections.json`, etc. (simpler but less efficient)

**Recommendation**: SQLite for v1 (simplicity, ACID compliance for device registry).

**SQL Schema**:
```sql
CREATE TABLE devices (
  id TEXT PRIMARY KEY,
  mac_address TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  os TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'UNASSIGNED',
  ip_address TEXT,
  port INTEGER DEFAULT 19999,
  version TEXT NOT NULL,
  discovery_timestamp TEXT,
  last_seen TEXT,
  is_registered INTEGER DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE connections (
  id TEXT PRIMARY KEY,
  master_device_id TEXT NOT NULL,
  client_device_id TEXT NOT NULL,
  encryption_key BLOB NOT NULL,
  encryption_key_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  auth_token TEXT,
  established_timestamp TEXT,
  disconnected_timestamp TEXT,
  input_event_counter INTEGER DEFAULT 0,
  input_event_last_timestamp TEXT,
  failures_count INTEGER DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (master_device_id) REFERENCES devices(id),
  FOREIGN KEY (client_device_id) REFERENCES devices(id),
  UNIQUE (master_device_id, client_device_id)
);

CREATE TABLE layouts (
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL UNIQUE,
  x_offset INTEGER NOT NULL,
  y_offset INTEGER NOT NULL,
  screen_width INTEGER NOT NULL,
  screen_height INTEGER NOT NULL,
  orientation TEXT NOT NULL,
  dpi_scale REAL DEFAULT 1.0,
  scale_factor REAL DEFAULT 1.0,
  monitor_index INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- InputEvent table NOT persisted; in-memory only per Constitution privacy principle
-- Audit logs stored separately in log files
```

---

**Data Model Version**: 1.0.0 | **Created**: 2026-02-09
