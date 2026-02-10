# Network Protocol Specification

**Feature**: Cross-Device Input Sharing (001-cross-device-input)  
**Created**: 2026-02-09  
**Status**: Design Phase 1

## 1. Discovery Protocol (mDNS)

### Service Registration

Each device running Keyboard Mouse Share registers itself as an mDNS service for automatic discovery on the local network.

**Service Type**: `_kms._tcp.local.`
- `kms` = Keyboard Mouse Share
- `_tcp` = TCP protocol
- `.local.` = Local LAN only (per Assumptions)

**Service Instance Name**: `{device_name}._kms._tcp.local.`
- Example: `Jerry's MacBook._kms._tcp.local.`

**TXT Record Fields**:
```
version=1.0.0
model=keyboard-mouse-share
os=Windows|macOS
device_id={UUID}
port=19999
```

**Discovery Behavior**:
- Broadcast TXT record on startup and every 30 seconds (refresh)
- Listen for mDNS queries from other instances
- Respond with TXT record + A/AAAA records (IPv4/IPv6)
- Timeout: Device considered offline if no refresh for 60 seconds
- Query interval (on startup): Every 1 second for 5 seconds total

---

## 2. Connection Protocol (TLS 1.3)

### Handshake Sequence

```
[Master Device]                          [Client Device]
     │                                           │
     │◄──────────── Device Discovery ──────────│
     │            (mDNS Resolution)             │
     │                                           │
     │◄──────────── TCP Connection ─────────────│
     │              (port 19999)                 │
     │                                           │
     │───── TLS 1.3 ClientHello ───────────────►│
     │      (version, ciphers, key_share)       │
     │                                           │
     │◄────── TLS ServerHello + Cert ──────────│
     │        (key_share, selected_cipher)      │
     │                                           │
     │───── TLS ClientKeyExchange ────────────►│
     │       FinishedCertificate                 │
     │                                           │
     │◄───── TLS ServerFinished ───────────────│
     │                                           │
     │    === TLS 1.3 Encrypted ===             │
     │                                           │
     │───── HELLO (JSON) ────────────────────►│
     │  {                                        │
     │    "msg_type": "HELLO",                  │
     │    "version": "1.0.0",                   │
     │    "device_id": "{UUID}",                │
     │    "device_name": "My Windows PC",      │
     │    "os": "Windows",                      │
     │    "initial_setup": true                 │
     │  }                                        │
     │                                           │
     │      [Master displays passphrase UI]     │
     │      Example: "Passphrase: ABC123"       │
     │                                           │
     │◄───── PASSPHRASE_PROMPT (JSON) ────────│
     │  {                                        │
     │    "msg_type": "PASSPHRASE_PROMPT",     │
     │    "challenge_id": "{UUID}",             │
     │    "hint": "Enter 6-character code"     │
     │  }                                        │
     │                                           │
     │      [Client prompts user]               │
     │      User enters: "ABC123"                │
     │                                           │
     │───── PASSPHRASE_RESPONSE (JSON) ──────►│
     │  {                                        │
     │    "msg_type": "PASSPHRASE_RESPONSE",   │
     │    "challenge_id": "{UUID}",             │
     │    "passphrase_hash": "sha256:...", │
     │    "client_random": "{32-bytes}"         │
     │  }                                        │
     │                                           │
     │      [Master verifies hash]              │
     │      ✓ MATCH: Proceed                    │
     │      ✗ MISMATCH: Revert to PASSPHRASE_  │
     │                   PROMPT (max 3 times)   │
     │                                           │
     │───── KMS_ACK + ACK_CONTENT ────────────►│
     │  {                                        │
     │    "msg_type": "ACK",                    │
     │    "connection_id": "{id}",              │
     │    "client_role": "CLIENT",              │
     │    "master_device_id": "{UUID}",         │
     │    "master_device_name": "...",          │
     │    "auth_token": "dGVz...",              │
     │    "encryption_method": "TLS1.3",       │
     │    "protocol_version": "1.0.0"           │
     │  }                                        │
     │                                           │
     │◄───── KMS_ACK_RESPONSE ────────────────│
     │  {                                        │
     │    "msg_type": "ACK_RESPONSE",           │
     │    "connection_id": "{id}",              │
     │    "status": "CONNECTED"                 │
     │  }                                        │
     │                                           │
     │      === Connection Established ===      │
     │      Input transmission ready             │
```

---

## 3. Input Event Message Format

All input events are transmitted as JSON over the TLS 1.3 encrypted channel.

### Keyboard Event

```json
{
  "msg_type": "INPUT_EVENT",
  "event_id": "{UUID}",
  "connection_id": "{master-client-id}",
  "timestamp": "2026-02-09T14:30:00.123456Z",
  "sequence_number": 42,
  "event": {
    "type": "KEY_PRESS",
    "keycode": 65,
    "key_name": "A",
    "modifiers": ["CTRL", "SHIFT"],
    "repeat_count": 1
  }
}
```

**Fields**:
- `msg_type`: Always "INPUT_EVENT"
- `event_id`: Unique per event (for deduplication)
- `connection_id`: For routing + audit trail
- `timestamp`: UTC timestamp (ISO 8601)
- `sequence_number`: Incremented per connection; helps detect lost events
- `event.type`: KEY_PRESS, KEY_RELEASE
- `event.keycode`: Virtual key code (platform-independent)
- `event.key_name`: Human-readable (e.g., "A", "Return", "LeftShift")
- `event.modifiers`: Active modifiers
- `event.repeat_count`: Number of repeats (for key held down)

### Mouse Event

```json
{
  "msg_type": "INPUT_EVENT",
  "event_id": "{UUID}",
  "connection_id": "{master-client-id}",
  "timestamp": "2026-02-09T14:30:00.123456Z",
  "sequence_number": 43,
  "event": {
    "type": "MOUSE_MOVE",
    "x": 500,
    "y": 300,
    "is_absolute": true,
    "delta_x": 10,
    "delta_y": -5
  }
}
```

**Fields**:
- `event.type`: MOUSE_MOVE, MOUSE_CLICK, MOUSE_SCROLL
- `event.x`, `event.y`: Absolute coordinates on source screen
- `event.is_absolute`: If true, coords are absolute; if false, coords are relative delta
- `event.delta_x`, `event.delta_y`: Relative movement (for smooth transition)

### Mouse Click Event

```json
{
  "msg_type": "INPUT_EVENT",
  "event_id": "{UUID}",
  "connection_id": "{master-client-id}",
  "timestamp": "2026-02-09T14:30:00.123456Z",
  "sequence_number": 44,
  "event": {
    "type": "MOUSE_CLICK",
    "button": "LEFT",
    "action": "PRESS",
    "x": 500,
    "y": 300,
    "click_count": 1
  }
}
```

**Fields**:
- `event.button`: LEFT, MIDDLE, RIGHT
- `event.action`: PRESS, RELEASE
- `event.click_count`: 1 for single click, 2 for double-click

### Mouse Scroll Event

```json
{
  "msg_type": "INPUT_EVENT",
  "event_id": "{UUID}",
  "connection_id": "{master-client-id}",
  "timestamp": "2026-02-09T14:30:00.123456Z",
  "sequence_number": 45,
  "event": {
    "type": "MOUSE_SCROLL",
    "direction": "UP",
    "delta": 3,
    "x": 500,
    "y": 300
  }
}
```

**Fields**:
- `event.direction`: UP, DOWN, LEFT, RIGHT
- `event.delta`: Positive = up/right; negative = down/left

---

## 4. Acknowledgment & Error Protocols

### Input Event Acknowledgment

After client receives and simulates an input event, it sends an ACK:

```json
{
  "msg_type": "INPUT_ACK",
  "event_id": "{UUID}",
  "connection_id": "{master-client-id}",
  "timestamp": "2026-02-09T14:30:00.145Z",
  "status": "OK"
}
```

If client fails to simulate:

```json
{
  "msg_type": "INPUT_ACK",
  "event_id": "{UUID}",
  "connection_id": "{master-client-id}",
  "timestamp": "2026-02-09T14:30:00.145Z",
  "status": "ERROR",
  "error_code": "PERMISSION_DENIED",
  "error_message": "Cannot simulate input; app not in focus"
}
```

**Error Codes**:
- OK: Event simulated successfully
- PERMISSION_DENIED: OS permission issue (e.g., input hook failed)
- WINDOW_NOT_FOUND: Target window closed
- TIMEOUT: Event processing took >500ms
- PARSE_ERROR: Event format invalid
- AUTH_FAILURE: Connection no longer authenticated

### Heartbeat / Keep-Alive

Every 30 seconds, both devices exchange heartbeats to detect disconnection:

```json
{
  "msg_type": "PING",
  "timestamp": "2026-02-09T14:30:00.123456Z",
  "connection_id": "{master-client-id}"
}
```

Response:

```json
{
  "msg_type": "PONG",
  "timestamp": "2026-02-09T14:30:00.145Z",
  "connection_id": "{master-client-id}"
}
```

If no PONG received within 30 seconds → Connection considered DISCONNECTED.

### Role Change Broadcast

When master/client roles change on the network, master broadcasts to all connected clients:

```json
{
  "msg_type": "ROLE_CHANGE",
  "timestamp": "2026-02-09T14:30:00.123456Z",
  "device_id": "{UUID}",
  "new_role": "CLIENT",
  "action": "DEMOTED",
  "reason": "Another device became master"
}
```

---

## 5. Version Negotiation (Backward Compatibility)

When devices connect, they exchange versions to determine feature compatibility (FR-016).

In HELLO message:
```json
{
  "msg_type": "HELLO",
  "version": "1.0.0",
  "device_id": "{UUID}",
  "supported_features": [
    "INPUT_SHARING",
    "LAYOUT_CONFIG",
    "KEYBOARD_ROUTING",
    "PASSPHRASE_AUTH"
  ]
}
```

Master responds with ACK including which features are supported by BOTH:

```json
{
  "msg_type": "ACK",
  "connection_id": "{id}",
  "supported_features": [
    "INPUT_SHARING",
    "PASSPHRASE_AUTH"
  ],
  "deprecated_features": [
    "LAYOUT_CONFIG",
    "KEYBOARD_ROUTING"
  ],
  "note": "Client version 0.9.0 does not support layout config; falling back to shared-screen mode"
}
```

---

## 6. Error Scenarios & Recovery

### Passphrase Auth Failure (3 attempts)

1st failure:
```json
{
  "msg_type": "PASSPHRASE_RESPONSE",
  "status": "MISMATCH",
  "attempts_remaining": 2
}
```

3rd failure (max):
```json
{
  "msg_type": "PASSPHRASE_RESPONSE",
  "status": "MAX_ATTEMPTS",
  "attempts_remaining": 0,
  "retry_after_seconds": 30,
  "error_message": "Passphrase auth failed 3 times. Please try again in 30 seconds."
}
```

### Connection Loss & Reconnection

Client reconnects with auth_token (no re-pairing):

```json
{
  "msg_type": "HELLO",
  "version": "1.0.0",
  "device_id": "{UUID}",
  "initial_setup": false,
  "auth_token": "dGVz...",
  "previous_connection_id": "{id}"
}
```

Master verifies auth_token. If valid:

```json
{
  "msg_type": "ACK",
  "connection_id": "{id}",
  "status": "RECONNECTED",
  "message": "Session resumed"
}
```

If invalid (token expired or revoked):

```json
{
  "msg_type": "NACK",
  "status": "AUTH_EXPIRED",
  "message": "Please re-pair device",
  "retry_initial_setup": true
}
```

---

**Protocol Version**: 1.0.0 | **Created**: 2026-02-09
