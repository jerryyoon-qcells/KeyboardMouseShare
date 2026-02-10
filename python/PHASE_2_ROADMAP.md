# Phase 2: Implementation Roadmap

**Status**: Ready to Implement  
**Duration**: 2 weeks (~10 working days)  
**Team Size**: 1–2 developers  
**Blocking**: All of Phases 3–7 depend on this  

---

## Quick Reference: By Deliverable

### 1️⃣ Models (Days 1–2) — T017–T026

```
Device Entity                    InputEvent Entity
├─ id                           ├─ event_type (KEY_PRESS, etc.)
├─ mac_address (unique)          ├─ source_device_id
├─ name, os, role               ├─ target_device_id
├─ ip_address, port             ├─ payload (keycode, x/y, button)
├─ is_registered (gate!)         ├─ timestamp
└─ timestamps                   └─ is_encrypted flag

Connection Entity               Layout Entity
├─ id (master-client pair)      ├─ device_id
├─ master_device_id             ├─ x, y (coordinates)
├─ client_device_id             ├─ width, height (pixels)
├─ status (CONNECTING→CONNECTED) ├─ dpi_scale (1.0–4.0)
├─ encryption_key (TLS cert)     └─ orientation
├─ auth_token (for reconnect)
└─ input_event_counter (audit)

├─ Repository Pattern
│   ├─ DeviceRepository
│   ├─ ConnectionRepository
│   ├─ LayoutRepository
│   └─ InputEventRepository
└─ SQLite Schema (migrations)
```

**Files**: `src/models/` (10 files, ~500 lines)  
**Tests**: 20+ unit tests, 5 integration tests  
**Deliverable**: Full CRUD operations + persistence

---

### 2️⃣ Discovery (Days 3–5) — T027–T035

```
mDNS Service Registration
┌──────────────────────────────┐
│ Local Device Registry        │
├──────────────────────────────┤
│ Device: Jerry's MacBook      │
│ Service: _kms._tcp.local.    │
│ TXT Record:                  │
│  - version=1.0.0             │
│  - device_id=<UUID>          │
│  - os=Darwin                 │
│  - port=19999                │
└──────────────────────────────┘
           ↓ (broadcast every 30s)
┌──────────────────────────────┐
│ Network (LAN, mDNS enabled)  │
└──────────────────────────────┘
           ↓ (discovered by others)
┌──────────────────────────────┐
│ Discovered Devices List      │
├──────────────────────────────┤
│ ✓ Jerry's MacBook            │
│ ✓ Windows PC (ready after 5s)│
│ ✓ iPad (if running app)      │
└──────────────────────────────┘

DiscoveryService API
├─ start_registration()     → Broadcast this device
├─ start_browsing()         → Listen for others
├─ add_listener(callback)   → Register device add/remove handler
├─ get_discovered()         → List of Device objects
└─ stop()                   → Cleanup
```

**Files**: `src/network/discovery.py` (~300 lines)  
**Dependencies**: zeroconf library  
**Tests**: Mocked mDNS + real network integration test  
**Deliverable**: Device discovery <5 seconds on LAN  

---

### 3️⃣ Connection (Days 6–8) — T036–T042

```
TLS 1.3 Handshake Flow

[Master]                                  [Client]
   │                                        │
   ├──── TCP Connection (port 19999) ────→ │
   │                                        │
   ├─── TLS ClientHello ──────────────────→ │
   │    (version, ciphers, key_share)       │
   │                                        │
   │← TLS ServerHello + Certificate ──── │
   │  (key_share, selected_cipher)         │
   │                                        │
   ├─── TLS ClientKeyExchange + Finished → │
   │                                        │
   │← TLS ServerFinished ────────────────│
   │                                        │
   ╔═══════════════════════════════════════╗
   ║ Encrypted Channel (TLS 1.3)           ║
   ╚═══════════════════════════════════════╝
   │                                        │
   ├──── HELLO (JSON) ────────────────────→ │
   │  { msg_type: "HELLO",                 │
   │    device_id: "...",                  │
   │    version: "1.0.0" }                 │
   │                                        │
   │←─ PASSPHRASE_PROMPT ─────────────── │
   │  { challenge_id: "..." }              │
   │                                        │
   ├──── PASSPHRASE_RESPONSE ────────────→ │
   │  { passphrase_hash: "sha256:..." }    │
   │                                        │
   ├──────────── OK ───────────────────────→ │
   │  { status: "CONNECTED" }              │
   │                                        ✓ Ready for input events

ConnectionHandler API
├─ initiate_connection()    → Client-side connect
├─ accept_connection()       → Server-side accept
├─ send_message(type, data) → Encrypt + send JSON
├─ receive_message()         → Receive + decrypt JSON
└─ close()                  → Cleanup
```

**Files**: `src/network/connection.py` (~400 lines)  
**Dependencies**: ssl, socket, json, cryptography  
**Tests**: Mocked sockets + real TLS handshake test  
**Deliverable**: Encrypted peer-to-peer communication  

---

### 4️⃣ Input Abstraction (Days 9–10) — T043–T046

```
InputHandler (Abstract Base Class)

┌────────────────────────────┐
│ InputHandler (ABC)         │
├────────────────────────────┤
│ + setup()                  │
│ + hook_keyboard(cb)        │
│ + hook_mouse(cb)           │
│ + send_keyboard_event()    │
│ + send_mouse_event()       │
│ + set_mouse_position()     │
│ + unhook()                 │
└────────────────────────────┘
          △              △
          │              │
    ┌─────┴─────┐   ┌────┴────┐
    │           │   │          │
Windows       macOS  Linux    Custom
┌──────────┐ ┌────────────┐
│ pynput   │ │ PyObjC +   │
│ Win32    │ │ Quartz ES  │
└──────────┘ └────────────┘
    Phase 2 Stubs → Phase 3+ Full Implementation
```

**Files**: 
- `src/input/handler.py` (abstract base, 60 lines)
- `src/input/windows_handler.py` (stub, 30 lines)
- `src/input/macos_handler.py` (stub, 30 lines)

**Tests**: 5+ unit tests verifying interface
**Deliverable**: Cross-platform input abstraction (stubs)

---

## Task Breakdown by Day

### **Week 1: Models + Discovery**

#### **Day 1–2: Data Models (Entities + Repositories)**
```
Morning:
  └─ T017: Device entity + validators
  └─ T018: Connection entity
  └─ T019: Layout entity

Afternoon:
  └─ T020: InputEvent entity
  └─ T021: SQLite schema + migrations
  
EOD Checklist:
  ☐ All dataclasses compile
  ☐ Validators work correctly
  ☐ SQLite database creates without errors
```

#### **Day 3: Repository Implementations**
```
Morning:
  └─ T022–T025: DeviceRepository, ConnectionRepository, etc.
  
Afternoon:
  └─ T026: Integration tests (transactions, foreign keys)
  
EOD Checklist:
  ☐ All CRUD operations work
  ☐ Foreign key constraints enforced
  ☐ 70%+ test coverage on models
```

#### **Day 4: Discovery Service**
```
Morning:
  └─ T027: DiscoveryService class architecture
  └─ T028–T031: Service registration, browsing, callbacks
  
Afternoon:
  └─ T032: Error handling + offline detection
  
EOD Checklist:
  ☐ Device registers as mDNS service
  ☐ Other devices discovered within 5 seconds
  ☐ Offline detection works
```

#### **Day 5: Discovery Testing + Reviews**
```
Morning:
  └─ T033–T034: Unit + integration tests
  localhost discovery simulator recommended)
  
Afternoon:
  └─ T035: Documentation + code review
  └─ Cleanup & merge to main
  
EOD Checklist:
  ☐ 75%+ test coverage
  ☐ Code review passed
  ☐ Discovery ready for Phase 3
```

---

### **Week 2: Connection + Input Abstraction**

#### **Day 6: TLS Connection Setup**
```
Morning:
  └─ T036: ConnectionHandler class architecture
  └─ T037: TLS 1.3 context setup
  
Afternoon:
  └─ T038: Certificate exchange protocol
  
EOD Checklist:
  ☐ TLS context created
  ☐ Self-signed certs generated for testing
  ☐ No compile errors
```

#### **Day 7: Connection Message Protocol**
```
Morning:
  └─ T039: Message serialization (JSON format)
  └─ send_message() / receive_message() stubs
  
Afternoon:
  └─ T040: Error handling + reconnection logic
  
EOD Checklist:
  ☐ Messages serializable
  ☐ Can send/receive over mock socket
  ☐ Timeout handling works
```

#### **Day 8: Connection Testing**
```
Morning:
  └─ T041: Unit tests (mocked sockets)
  
Afternoon:
  └─ T042: Integration test (real TLS handshake)
  └─ Code review + documentation
  
EOD Checklist:
  ☐ Tests pass
  ☐ Real TLS handshake works
  ☐ Connection ready for Phase 3
```

#### **Day 9–10: Input Abstraction**
```
Day 9:
  └─ T043: InputHandler ABC
  └─ T044–T045: Windows/macOS handler stubs
  
Day 10:
  └─ T046: Unit tests
  └─ Final review + Phase 2 cleanup
  
Final Deliverable:
  ☐ All 4 models persisting to SQLite
  ☐ mDNS discovery working
  ☐ TLS connections established
  ☐ Input abstract interface defined
  ☐ 75%+ test coverage
  ☐ Phase 3 can begin
```

---

## Weekly Standup (Suggested)

### **Monday (Start of Week)**
- Review completed tasks from previous week
- Any blockers from Phase 1 integration?
- Assign Day 1–2 tasks

### **Thursday (Mid-week)**
- Progress on Models + Discovery
- Any TLS/connection questions?
- Plan final integration

### **Friday (End of Week)**
- Merge completed features
- Test coverage check
- Prepare for next week

---

## Release Checklist for Phase 2

Before marking Phase 2 complete:

```
Code Quality
☐ All 30 tasks (T017–T046) complete
☐ ruff check src/ tests/ passes
☐ black format check passes
☐ mypy type hints validated
☐ pytest coverage ≥75%

Testing
☐ 45+ unit tests pass
☐ mDNS discovery test passes
☐ TLS handshake test passes
☐ Database transaction test passes

Documentation
☐ ARCHITECTURE.md updated with Phase 2 diagrams
☐ API docstrings complete (Google format)
☐ README.md has Phase 2 quick-start

Integration
☐ Models load/save from SQLite
☐ Discovery finds devices on LAN
☐ TLS connection between two instances works
☐ No breaking changes to Phase 1 code

Sign-Offs
☐ Lead Developer: Code complete
☐ QA: Testing complete
☐ Architecture: Design validated
```

---

## Phase 2 → Phase 3 Transition

Once Phase 2 completes:

1. **Phase 3 starts immediately** (Discovery UI)
   - Uses: DiscoveryService, DeviceRepository
   - Deliverable: Device list UI + registration flow

2. **Phases 4–5 follow** (Roles + Input Sharing)
   - Uses: ConnectionHandler, InputHandler
   - Deliverable: Input events flowing master→client

3. **Phases 6–8 complete** (Layout, Routing, Polish)
   - Uses: LayoutRepository, CursorMapper
   - Deliverable: MVP shipped

---

## Estimated Effort

| Component | Effort | Confidence |
|-----------|--------|-----------|
| **Models** (T017–T026) | 2 days | 95% |
| **Discovery** (T027–T035) | 2.5 days | 85% (mDNS learning curve) |
| **Connection** (T036–T042) | 2.5 days | 80% (TLS debugging) |
| **Input Abstraction** (T043–T046) | 0.5 days | 90% |
| **Testing + Reviews** | 1.5 days | 90% |
| **Buffer (unexpected issues)** | 1 day | - |
| **Total** | 10 days | **84% (avg)** |

---

**Ready to start Phase 2? Begin with Day 1: Entities.** 🚀

Let me know if you want me to:
1. Start implementation (create T017–T026 files)
2. Dive deeper into any specific task
3. Adjust timeline or scope
