let'# Implementation Plan: Cross-Device Input Sharing

**Branch**: `001-cross-device-input` | **Date**: 2026-02-09 | **Spec**: [spec.md](spec.md)

## Summary

Implement a unified keyboard and mouse sharing system that allows users to control multiple devices (Windows/macOS) from a single master device over a local network. Core features include:
- **Auto-discovery** of devices on LAN using mDNS/broadcast (P1)
- **Master/Client role configuration** with network validation (P1)
- **Input transmission** from master keyboard/mouse to client devices via encrypted TLS 1.3 channel (P1)
- **Screen layout configuration** with custom coordinate positioning for seamless cursor movement (P2)
- **Keyboard input routing** to cursor location with hotkey override (P2)
- **Passphrase-based authentication** for device pairing and security
- **Backward compatibility** across versions for non-breaking features

**Estimated Scope**: MVP (P1 stories) = ~8-12 weeks; Full feature (P1+P2) = ~14-18 weeks

---

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: 
- Network: `zeroconf` (mDNS discovery), `socket`, `ssl` (TLS 1.3)
- Input Handling: `pynput` (cross-platform keyboard/mouse hook), platform-specific APIs (Windows: Win32 API via `pywinusb`/`ctypes`, macOS: Quartz Event Services via `PyObjC`)
- UI/Configuration: `tkinter` (lightweight cross-platform GUI) or `PyQt6` (richer UX)
- Data Persistence: `sqlite3` (device registry) or JSON files (config)
- Testing: `pytest`, `pytest-asyncio` (async I/O testing)  
**Testing**: pytest with coverage reporting  
**Target Platform**: Windows 10+, macOS 10.15+ (Intel & Apple Silicon)
**Project Type**: Single monolithic Python application with platform-specific submodules  
**Performance Goals**: 
- Discovery: <5 seconds (LAN)
- Keyboard latency: <100ms (p95)
- Mouse latency: <50ms (p95)
- Event success rate: 95%+  
**Constraints**: 
- <100MB memory footprint
- <5% CPU under normal operation
- LAN-only (no internet/WAN in v1)
- Requires admin/elevated privileges for input hook installation  
**Scale/Scope**: 
- MVP: 2-3 devices
- Full: 4+ devices simultaneously
- ~5,000-8,000 lines of code (MVP estimate)

---

## Constitution Check

*Evaluated against Keyboard Mouse Share Constitution (v1.0.0)*

### Core Principles Alignment

| Principle | Status | Alignment |
|-----------|--------|-----------|
| **I. Input-First Design** | ✅ PASS | Feature is entirely input-centric; all design choices prioritize input handling, validation, and defensive programming |
| **II. Network Security** | ✅ PASS | TLS 1.3 encryption (FR-006, FR-007), passphrase authentication (FR-018), audit logging (FR-015), security testing approach defined |
| **III. Cross-Platform (Windows & macOS)** | ✅ PASS | Both platforms explicitly supported; platform-specific APIs abstracted; testing strategy includes real hardware; limitations documented (e.g., macOS requires Accessibility permissions) |
| **IV. Comprehensive Documentation** | ⚠️ CONDITIONAL | Plan must include README, API docs, architecture diagrams, user guides, CHANGELOG. Will be enforced during implementation; defer detailed doc structure to Phase 1. |
| **V. Moderate Test Coverage** | ✅ PASS | Target 70%+ critical modules (input validation, protocol parsing, device discovery). Plan includes unit + integration tests. |
| **VI. Phase Checklists** | ✅ PASS | Spec + Clarif phase complete with requirements checklist. Planning phase will include technical checklist. Implementation phase will include quality gates checklist. |
| **VII. Simplicity & Maintainability** | ⚠️ CONDITIONAL | Architecture must avoid premature optimization, use standard libraries, keep dependencies shallow. Will evaluate during design review. |

### Technical Constraints Review

| Constraint | Feasibility | Notes |
|-----------|-------------|-------|
| **Python 3.11+** | ✅ YES | Widely available; supports async/await, type hints, performance improvements |
| **TLS 1.3** | ✅ YES | `ssl` module supports TLS 1.3 natively in Python 3.7+ |
| **mDNS discovery** | ✅ YES | `zeroconf` library provides cross-platform mDNS (Bonjour on macOS, mDNS on Windows) |
| **Windows input handling** | ✅ YES | `pynput` provides cross-platform input hooks; Win32 API available for low-level control |
| **macOS input handling** | ✅ YES | PyObjC + Quartz Event Services enable input hook + simulation (requires Accessibility permissions) |
| **Coordinate-based cursor transition** | ⚠️ COMPLEX | Requires careful geometry calculation and edge-case handling (overlapping screens, gaps). Feasible but needs design review. |
| **<100ms keyboard latency** | ✅ FEASIBLE | LAN latency typically 1-5ms; Python processing ~20-50ms; TLS encryption ~5-10ms; buffer = ~30-50ms. Achievable with async I/O and event queuing. |
| **<50ms mouse latency** | ⚠️ CHALLENGING | Same as keyboard but stricter requirement. May require further optimization (event batching, prediction). Benchmark against competitors. |

### Gates & Violations

**No violations detected.** All core principles can be met with the proposed architecture. Conditional items (IV, VII) are implementation concerns, not design flaws—will be verified during Phase 1 design review.

---

## Platform Compatibility *(Principle III: Cross-Platform)*

**Supported Platforms**: 
- ✅ Windows 10+
- ✅ macOS 10.15+ (Intel & Apple Silicon)

**Platform-Specific Considerations**:
- **Windows**: Use Win32 `SetWindowsHookEx` or `pynput` for keyboard hook; `SendInput` API for input simulation; WMI or registry for device enumeration
- **macOS**: Use Quartz Event Services (`CGEventTap`, `CGEventPost`) via PyObjC for input hook/simulation; requires Accessibility permissions (must prompt user on first run); supports both Intel and Apple Silicon via native code
- **Shared Abstraction**: Create `InputHandler` abstract base class; implement `WindowsInputHandler` and `MacOSInputHandler` subclasses; input events flow through abstract interface
- **Testing Strategy**: 
  - Unit tests: Mock input events; test coordinate math, device discovery protocol
  - Integration tests: Real hardware (Windows VM + macOS VM, or physical devices on LAN)
  - CI/CD: GitHub Actions for Windows; macOS runners if available
- **Known Limitations**: 
  - macOS requires user to grant Accessibility permissions (System Preferences → Security & Privacy)
  - Windows may require UAC elevation for low-level input hooks
  - Some sandboxed applications (browsers in some contexts) may block input simulation
  - Input hook disabled during lock screen, login screen (OS security)

---

## Phase 0: Research & Clarification

**Status**: ✅ COMPLETE (Clarifications recorded in spec.md)

**Outstanding Technical Unknowns** (resolved):
- ✅ Version compatibility: Backward compatible model (Option B)
- ✅ Multi-device layout: Custom X/Y coordinates (Option C)
- ✅ Concurrent input handling: One-way master→client only (Clarification)
- ✅ Device authentication: Pre-shared passphrase (Option A)

**Research Topics Remaining** (Phase 1 design):
- Network protocol design: Message format (JSON vs. Protocol Buffers), versioning strategy, error handling
- Encryption key exchange: Certificate generation/exchange during passphrase pairing
- Device discovery protocol: mDNS service registration format, retry logic, timeout handling
- Cursor transition algorithm: How to handle overlapping/gapped monitor layouts; edge case resolution
- State machine: Master/client state transitions; offline detection; reconnection logic

---

## Phase 1: Design & Architecture

### 1.1 Data Model

**Device Entity**:
```
Device {
  id: str (unique, MAC address or device UUID)
  name: str (user-friendly, e.g., "Jerry's MacBook")
  os: Enum (WINDOWS | MACOS)
  role: Enum (MASTER | CLIENT | UNASSIGNED)
  ip_address: str
  port: int
  discovery_timestamp: datetime
  last_seen: datetime
  is_registered: bool
}
```

**Connection Entity**:
```
Connection {
  id: str (unique, e.g., "device1-device2")
  master_device_id: str (foreign key to Device.id)
  client_device_id: str (foreign key to Device.id)
  encryption_key: bytes (TLS certificate/key pair)
  established_timestamp: datetime
  status: Enum (CONNECTING | CONNECTED | DISCONNECTED)
  input_event_counter: int (audit tracking)
}
```

**Layout Entity**:
```
Layout {
  id: str (unique, e.g., "layout_v1")
  device_id: str (foreign key to Device.id)
  x_offset: int (pixel coordinate)
  y_offset: int (pixel coordinate)
  screen_width: int (native resolution)
  screen_height: int (native resolution)
  orientation: Enum (LANDSCAPE | PORTRAIT)
  created_timestamp: datetime
  updated_timestamp: datetime
}
```

**InputEvent Entity**:
```
InputEvent {
  id: str (unique, UUID)
  event_type: Enum (KEY_PRESS | KEY_RELEASE | MOUSE_MOVE | MOUSE_CLICK | SCROLL)
  keycode: int (if KEY_*, else null)
  modifiers: Set[str] (CTRL, ALT, SHIFT, META, etc.)
  button: Enum (LEFT | MIDDLE | RIGHT, if MOUSE_CLICK, else null)
  x: int (if MOUSE_*, else null)
  y: int (if MOUSE_*, else null)
  scroll_delta: int (if SCROLL, else null)
  source_device_id: str (foreign key to Device.id)
  target_device_id: str (foreign key to Device.id)
  timestamp: datetime (with UTC timezone)
  encrypted: bool (always true)
}
```

### 1.2 API Contracts / Network Protocol

**Discovery Protocol (mDNS)**:
- Service type: `_kms._tcp.local.` (Keyboard Mouse Share)
- Broadcast TXT record: `version=1.0.0&model=keyboard-mouse-share&os=Windows/macOS`
- Query interval: 5s on startup; 30s periodic refresh
- Timeout: 60s (device considered offline if no refresh)

**Connection Handshake (TLS + Passphrase)**:
```
1. Client → Master: HELLO packet (device_id, version, initial_setup=true)
2. Master: Generate random 6-char passphrase; display to user
3. Master → Client: PASSPHRASE_PROMPT (challenge)
4. Client: Prompt user to enter passphrase
5. Client → Master: PASSPHRASE_RESPONSE (hashed)
6. Master: Verify hash; if match:
   - Generate TLS certificate for this device
   - Create Connection entry in database
   - Send ACK + client_role assignment
7. Establish TLS 1.3 encrypted channel
8. Master → Client: INPUT_SHARE_ENABLED or INPUT_SHARE_DISABLED
```

**Input Event Format (over TLS)**:
```json
{
  "event_type": "KEY_PRESS",
  "keycode": 65,
  "modifiers": ["CTRL"],
  "timestamp": "2026-02-09T14:30:00Z",
  "source_device_id": "master-device-uuid",
  "sequence_number": 12345
}
```

**Master/Client Role Validation**:
```
1. Client wants to become MASTER:
   - Master queries network: "Is there a MASTER device?"
   - If yes: Return error "Only one master allowed"
   - If no: Allow; demote old master (if any) to CLIENT
2. If no MASTER (both CLIENTS): Error popup "Designate one device as MASTER"
3. Master → Clients: Broadcast role change; all non-master devices must acknowledge
```

**Passphrase Authentication UX Flow**:
- Master generates 6-character alphanumeric code; displays in center-screen modal
- Master verbally communicates code to user (or shows on same device for intra-device pairing)
- Client user types code into dialog prompt within 30-second window
- Max 3 passphrase entry attempts; 5-minute lockout after 3 failures (exponential backoff: 1s, 2s, 4s)
- Hashing algorithm: SHA256 (no salt required; single-session pairing only)
- On successful match: Master generates TLS certificate for client; stores in ~/.keyboard-mouse-share/certs/; issues auth_token for future reconnects without re-pairing

**Version Negotiation Features**:
- HELLO message includes `supported_features` list: [INPUT_SHARING, LAYOUT_CONFIG, KEYBOARD_ROUTING, PASSPHRASE_AUTH]
- Server (master) and client negotiate common features by intersection
- Features offered only if BOTH devices support them
- Example: Master v1.0 (supports INPUT_SHARING, PASSPHRASE_AUTH) connects to Client v1.1 (supports INPUT_SHARING, LAYOUT_CONFIG, KEYBOARD_ROUTING, PASSPHRASE_AUTH) 
  - Common features: [INPUT_SHARING, PASSPHRASE_AUTH]
  - LAYOUT_CONFIG and KEYBOARD_ROUTING disabled with silent downgrade (no error)

**Audit Logging**:
- Format: JSON (timestamp, device_id, event_type, status, optional_error)
- Events logged: connection attempts, passphrase validation (success/failure/attempt_count), role changes, input event counters per connection
- Retention: 7 days, then automatic purge
- Location: ~/.keyboard-mouse-share/logs/kms-{date}.log
- Encryption: Not required (LAN-only assumption; sensitive payloads never logged)
- User can enable detailed event logging for debugging (with warning)

**Master Assignment Logic**:
- If no master configured: First device to attempt MASTER role receives it
- If simultaneous role change requests: MAC address lexicographic comparison; lower MAC wins (deterministic tiebreaker)
- Master demotion: Old master automatically demoted to CLIENT when new master elected (broadcast notification)

### 1.3 Project Structure

```
keyboard-mouse-share/
├── README.md                          # Quick start, installation, configuration
├── ARCHITECTURE.md                    # Detailed design docs
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Package metadata, version bumping
├── .venv/                             # Virtual environment
├── .github/                           # GitHub Actions CI/CD, issue templates
│   ├── workflows/
│   │   ├── test.yml                   # Run tests on every push
│   │   └── build.yml                  # Build executable for Windows/macOS
│   └── prompts/                       # Spec Kit prompts (already in place)
├── src/                               # Source code
│   ├── __init__.py
│   ├── main.py                        # Entry point
│   ├── config.py                      # Configuration loader (JSON, env vars)
│   ├── logger.py                      # Structured logging setup
│   ├── models/                        # Data models
│   │   ├── device.py
│   │   ├── connection.py
│   │   ├── layout.py
│   │   └── input_event.py
│   ├── network/                       # Network layer
│   │   ├── discovery.py               # mDNS service, device enumeration
│   │   ├── connection.py              # TLS socket management
│   │   ├── protocol.py                # Message parsing/serialization
│   │   └── handlers.py                # Incoming message handlers
│   ├── input/                         # Input handling (platform-specific)
│   │   ├── handler.py                 # Abstract InputHandler base class
│   │   ├── windows_handler.py         # Windows implementation
│   │   ├── macos_handler.py           # macOS implementation
│   │   └── input_queue.py             # Event queue + dispatcher
│   ├── auth/                          # Authentication
│   │   ├── passphrase.py              # Passphrase generation, validation
│   │   ├── certificate.py             # TLS cert generation/storage
│   │   └── crypto.py                  # Encryption utilities
│   ├── layout/                        # Cursor transition logic
│   │   ├── cursor_mapper.py           # Coordinate transformation
│   │   ├── geometry.py                # Screen overlap detection, edge finding
│   │   └── transition.py              # Seamless cursor movement
│   ├── state/                         # State management
│   │   ├── state_machine.py           # Master/client state transitions
│   │   ├── device_registry.py         # Local device persistence
│   │   └── layout_config.py           # Layout storage/retrieval
│   ├── ui/                            # User interface
│   │   ├── app.py                     # Main window
│   │   ├── config_menu.py             # Master/client role selection
│   │   ├── layout_config_ui.py        # Layout visualization + editor
│   │   ├── device_list_ui.py          # Available/registered devices list
│   │   └── status_ui.py               # Connection status, input sharing toggle
│   └── utils/                         # Utilities
│       ├── constants.py               # Hardcoded values (default hotkey, passphrase length, etc.)
│       └── validators.py              # Input validation (passphrases, IPs, etc.)
├── tests/                             # Test suite
│   ├── conftest.py                    # Pytest fixtures
│   ├── unit/                          # Unit tests
│   │   ├── test_device_model.py
│   │   ├── test_passphrase.py
│   │   ├── test_geometry.py           # Cursor mapper math
│   │   ├── test_protocol.py           # Message format tests
│   │   └── test_input_handler.py      # Mock input events
│   ├── integration/                   # Integration tests
│   │   ├── test_discovery.py          # mDNS service browsing
│   │   ├── test_connection.py         # TLS handshake
│   │   ├── test_input_sharing.py      # Master → client input flow
│   │   ├── test_layout_transition.py  # Cursor movement across devices
│   │   └── test_authentication.py     # Passphrase pairing
│   └── fixtures/                      # Test data, mock configs
│       └── devices.json
├── docs/                              # Documentation
│   ├── INSTALL.md                     # OS-specific installation
│   ├── USER_GUIDE.md                  # How to use the app
│   ├── ARCHITECTURE.md                # Technical design (code structure, protocols)
│   ├── SECURITY.md                    # Security model, threat model
│   ├── TROUBLESHOOTING.md             # Common issues and solutions
│   └── API.md                         # Internal API documentation (docstrings reference)
├── specs/                             # Feature specifications (Spec Kit)
│   └── 001-cross-device-input/
│       ├── spec.md                    # Functional requirements
│       ├── plan.md                    # This file
│       ├── data-model.md              # Entity definitions
│       ├── contracts/                 # Protocol/API specs
│       │   └── network-protocol.md
│       ├── quickstart.md              # Quick setup guide
│       ├── checklists/
│       │   └── requirements.md        # Requirements validation
│       └── research.md                # Phase 0 research findings

# Configuration & data files (created at runtime)
└── ~/.keyboard-mouse-share/           # Home directory config
    ├── config.json                    # User settings (UI layout, theme)
    ├── device_registry.db             # SQLite: registered devices
    ├── certs/                         # TLS certificates per device
    │   └── device-{uuid}.pem
    └── logs/                          # Audit logs
        └── kms-{date}.log
```

### 1.4 Implementation Phases

**Phase 1 (Weeks 1-4): Foundation**
- [ ] Project setup: dependencies, CI/CD pipeline, test framework
- [ ] Data models: Device, Connection, Layout, InputEvent
- [ ] Configuration: Load from JSON, environment variables
- [ ] Logging: Structured logger with audit trail
- [ ] Platform abstraction: InputHandler interfaces (Windows/macOS)

**Phase 2 (Weeks 5-6): Network Discovery & Authentication**
- [ ] mDNS service registration + discovery (Device Discovery User Story)
- [ ] Device registry: Persist registered devices locally
- [ ] Passphrase generation + validation
- [ ] TLS certificate generation + storage
- [ ] Connection handshake protocol

**Phase 3 (Weeks 7-9): Master/Client Configuration & Input Sharing**
- [ ] Role configuration UI (Master/Client Mode Configuration User Story)
- [ ] Role validation: Only one master per network
- [ ] Input capture: Hook keyboard/mouse on master
- [ ] Input transmission: Master → client over TLS
- [ ] Input simulation: Client simulates received events
- [ ] Input Sharing Activation (User Story 3)

**Phase 4 (Weeks 10-12): Layout Configuration & Keyboard Routing** *(P2 - Optional for MVP)*
- [ ] Layout configuration UI: Custom X/Y coordinate positioning
- [ ] Cursor mapper: Calculate transitions between devices
- [ ] Seamless cursor movement (User Story 4)
- [ ] Keyboard input routing: Default to cursor location (User Story 5)
- [ ] Hotkey override: Manual focus switching

**Phase 5 (Weeks 13-15): Integration & Polish** *(If timeline permits)*
- [ ] Error handling + recovery (disconnection, timeout)
- [ ] Performance optimization: Latency profiling, event batching
- [ ] Cross-version compatibility: Version negotiation (FR-016)
- [ ] Documentation: README, user guide, architecture docs
- [ ] User testing: Beta release, gather feedback

**Phase 6 (Weeks 16-18): Security Hardening & Release** *(Stretch)*
- [ ] Security testing: Penetration testing, fuzzing, replay attack mitigation
- [ ] Code review + audit
- [ ] Release builds: Windows installer, macOS DMG
- [ ] Release notes + changelog

### 1.5 Quality Gates & Checklist

**Planning Phase Checklist**:
- [x] Specification is complete and clarified (no ambiguities)
- [x] Constitution alignment verified (no violations)
- [x] Technical feasibility confirmed (all platforms, latency targets)
- [x] Data model defined (entities, relationships)
- [x] API contracts sketched (discovery, handshake, input format)
- [x] Project structure designed (layered architecture, separation of concerns)
- [x] Implementation phases sequenced (MVP-first, P2 optional)
- [x] Platform-specific considerations documented (Windows, macOS)
- [x] Dependencies identified & evaluated (zeroconf, pynput, PyObjC, etc.)
- [ ] Tech debt & tradeoffs documented (deferred to Phase 1 design review)

---

## Complexity Tracking

> *No Constitution violations requiring justification identified.*

| Aspect | Complexity | Rationale |
|--------|-----------|-----------|
| **Cross-platform input handling** | HIGH | Windows Win32 API + macOS Quartz Event Services require platform-specific coding; abstracted behind InputHandler interface to minimize complexity. |
| **Cursor transition geometry** | MEDIUM | Coordinate mapping for overlapping/gapped monitors requires careful math; feasible with Shapely/geometric library; edge cases (gaps, overlaps) handled by validation + user warnings. |
| **Async network I/O** | MEDIUM | TLS sockets + event loops add complexity; mitigated by using `asyncio` + proven libraries (zeroconf). |
| **Device discovery & state sync** | MEDIUM | mDNS + passphrase pairing + role validation require careful sequencing; state machine design clarifies transitions. |

---

## Next Steps

1. ✅ Specification complete & clarified
2. ✅ Planning phase in progress (this document)
3. → **Phase 1.A: Data Model Details** - Finalize entity schemas, relationships
4. → **Phase 1.B: Network Protocol Design** - Formalize message formats, error codes
5. → **Phase 1.C: Architecture Review** - Validate design choices, identify risks
6. → **Phase 2: Implementation** - Begin Phase 1 (Foundation) coding
7. → `/speckit.tasks` - Generate granular task list from this plan

**Readiness for Implementation**: ✅ READY

---

**Plan Version**: 1.0.0 | **Created**: 2026-02-09 | **Last Updated**: 2026-02-09
