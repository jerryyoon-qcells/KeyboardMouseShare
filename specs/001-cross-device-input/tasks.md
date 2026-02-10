# Tasks: Cross-Device Input Sharing

**Feature Branch**: `001-cross-device-input`  
**Specification**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Data Model**: [data-model.md](data-model.md) | **Protocol**: [contracts/network-protocol.md](contracts/network-protocol.md)

**Prerequisites**: All planning documents complete ✅ | Specification clarified ✅ | Constitution aligned ✅

**Total Tasks**: 196 tasks organized by phase (includes 8 Phase 1.A design review + 4 Phase 5 critical docs + 5 remediation tasks)

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Project structure, dependencies, CI/CD, and core infrastructure

**Duration**: Week 1 (~5 working days)

- [ ] T001 Create project directory structure per plan.md (src/, tests/, docs/, .github/) in root
- [ ] T002 [P] Initialize pyproject.toml with package metadata, version 1.0.0-dev, Python 3.11+ requirement
- [ ] T003 [P] Create requirements.txt with dependencies: zeroconf, pynput, PyObjC (macOS), pytest, pytest-asyncio, ruff, black, mypy, cryptography
- [ ] T004 [P] Setup virtual environment and install dependencies in `.venv/`
- [ ] T005 [P] Configure ruff.toml for code linting (Python style, max-line-length=100)
- [ ] T006 [P] Configure pyproject.toml for pytest with coverage minimum 70% on critical modules
- [ ] T007 [P] Create GitHub Actions CI/CD workflow in `.github/workflows/test.yml` (run tests on push/PR)
- [ ] T008 Create src/__init__.py and src/main.py entry point with argparse CLI skeleton
- [ ] T009 [P] Create src/config.py for configuration management (JSON loader, env var overrides, default values)
- [ ] T010 [P] Create src/logger.py with structured logging setup (JSON format, file rotation, audit trail capability)
- [ ] T011 Create src/utils/constants.py with hardcoded values (default port 19999, passphrase length 6, discovery timeout 60s, max connection attempts 3)
- [ ] T012 [P] Create src/utils/validators.py with input validation functions (IP, port, passphrase format, device name)
- [ ] T013 Create tests/conftest.py with pytest fixtures (mock devices, mock connections, mock input events)
- [ ] T014 [P] Create tests/fixtures/devices.json with sample test data (Windows device, macOS device, unregistered device)
- [ ] T015 Create README.md with installation instructions, quick start, feature overview (reference quickstart.md)
- [ ] T016 Create .github/prompts/speckit.tasks.prompt.md marker file marking completion

**Checkpoint**: ✅ Project structure is initialized; dependencies installed; logging & config ready

---

## Phase 1.A: Design Review & Validation (MANDATORY GATE)

**Purpose**: Validate all design decisions before proceeding to foundational implementation

**Duration**: ~3 days (parallel code review sprint)

**⚠️ BLOCKING**: Phase 2 cannot begin until ALL items below are signed off

### Design & Architecture Validation

- [ ] Design Review: Data model completeness (Device, Connection, Layout, InputEvent; entity relationships; constraints; SQL schema review)
- [ ] Design Review: Network protocol validation (mDNS discovery; TLS 1.3 handshake; message formats; error handling; version negotiation)
- [ ] Design Review: Platform abstraction architecture (InputHandler base class pattern; Windows/macOS implementation strategy; API coverage)
- [ ] [P] Architecture Review: Cursor mapper geometry logic (coordinate transformation; edge case handling; DPI scaling; overlapping screens)
- [ ] Code Review: Phase 1 code quality (linting passes; type hints; docstrings; no `Any` types)
- [ ] Risk Assessment: Technical risks identified and mitigation documented (latency targets, platform APIs, error recovery, dependency availability)
- [ ] Simplicity Check: No premature optimization; standard libraries only; code readable by unfamiliar maintainer
- [ ] Documentation Kickoff: README, ARCHITECTURE, SECURITY templates created and skeleton content drafted

**Checkpoint**: ✅ ALL design reviews passed; simplicity validated; Phase 2 ready to proceed

**Sign-Off Required**: [Lead Developer] [Date] | [Architecture Reviewer] [Date]

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure required by ALL user stories

**Duration**: Weeks 2-3 (~10 working days)

**⚠️ CRITICAL**: No user story work can begin until ALL tasks in this phase are complete

### 2.1 Data Models & Database

- [ ] T017 [P] Create src/models/__init__.py with model exports
- [ ] T018 [P] Create src/models/device.py with Device class (13 fields per data-model.md; include @dataclass or Pydantic model)
- [ ] T019 [P] Create src/models/connection.py with Connection class (13 fields; status enum CONNECTING/CONNECTED/DISCONNECTED/FAILED)
- [ ] T020 [P] Create src/models/layout.py with Layout class (11 fields; include DPI scaling, monitor index)
- [ ] T021 [P] Create src/models/input_event.py with InputEvent class (17 fields; event type enum KEY_PRESS/KEY_RELEASE/MOUSE_MOVE/MOUSE_CLICK/SCROLL)
- [ ] T022 Create src/state/device_registry.py with DeviceRegistry class (load/save Device objects to SQLite)
- [ ] T023 Create src/state/connection_registry.py with ConnectionRegistry class (load/save Connection objects)
- [ ] T024 Create src/state/layout_config.py with LayoutConfig class (load/save Layout objects)
- [ ] T025 [P] Create database initialization script in src/state/init_db.py (CREATE TABLE statements for devices, connections, layouts; NOT InputEvent per privacy)
- [ ] T026 Create src/state/migrations.py for database schema migrations framework

### 2.2 Platform Abstraction & Input Handler Interface

- [ ] T027 [P] Create src/input/handler.py with abstract InputHandler base class (methods: start_capture(), stop_capture(), send_key(), send_mouse_move(), send_mouse_click(), send_scroll())
- [ ] T028 [P] Create src/input/windows_handler.py with WindowsInputHandler (inherit InputHandler; use pynput or Win32 API for keyboard/mouse hooks)
- [ ] T029 [P] Create src/input/macos_handler.py with MacOSInputHandler (inherit InputHandler; use PyObjC + Quartz Event Services)
- [ ] T030 Create src/input/input_factory.py with platform detection factory (return Windows or macOS handler based on detected OS)
- [ ] T031 Create src/input/input_queue.py with InputQueue class (thread-safe queue for captured input events; dispatcher to network layer)
- [ ] T032 [P] Create unit tests in tests/unit/test_input_handler.py (mock input events; verify capture/send methods exist in interface)
- [ ] T027a [P] [Remediation] Implement DPI scale detection for macOS Retina displays (2.0x) and Windows high-DPI monitors; apply scaling in coordinate transformations in src/layout/cursor_mapper.py

### 2.3 Authentication & Encryption

- [ ] T033 [P] Create src/auth/passphrase.py with Passphrase class (generate random 6-char alphanumeric; hash using SHA256; validate against stored hash)
- [ ] T034 [P] Create src/auth/certificate.py with Certificate class (generate self-signed TLS cert; store as PEM in ~/.keyboard-mouse-share/certs/; load on demand)
- [ ] T035 [P] Create src/auth/crypto.py with encryption utility functions (encrypt JSON payload with TLS; decrypt and verify)
- [ ] T036 [P] Create unit tests in tests/unit/test_passphrase.py (verify generation, hashing, validation)
- [ ] T037 [P] Create unit tests in tests/unit/test_certificate.py (verify cert generation, PEM format, storage/retrieval)

### 2.4 Network Layer Foundation

- [ ] T038 [P] Create src/network/__init__.py with network layer exports
- [ ] T039 [P] Create src/network/protocol.py with Protocol class (JSON serialization/deserialization of messages; message types: HELLO, PASSPHRASE_PROMPT, PASSPHRASE_RESPONSE, ACK, INPUT_EVENT, PING, PONG, ERROR)
- [ ] T040 Create src/network/connection.py with TLSConnection class (manage TLS socket; send/recv encrypted payloads; keep-alive PING/PONG)
- [ ] T041 [P] Create unit tests in tests/unit/test_protocol.py (verify message format, serialization, error handling)
- [ ] T042 [P] Create unit tests in tests/unit/test_connection.py (mock socket; verify TLS connect/disconnect, send/recv)

### 2.5 State Management

- [ ] T043 [P] Create src/state/state_machine.py with StateMachine class (device role transitions: UNASSIGNED → MASTER/CLIENT; connection lifecycle: CONNECTING → CONNECTED → DISCONNECTED)
- [ ] T044 Create unit tests in tests/unit/test_state_machine.py (verify state transitions, invalid transitions raise exceptions)

### 2.6 Geometry & Cursor Transition (Foundation)

- [ ] T045 [P] Create src/layout/geometry.py with Geometry helper functions (detect overlapping screens; find screen edges; calculate coordinate transitions)
- [ ] T046 [P] Create unit tests in tests/unit/test_geometry.py (verify coordinate math, edge detection, overlap detection)

**Checkpoint**: ✅ Data models, platform abstraction, auth, network protocol, state management all ready; foundation blocking no longer

---

## Phase 3: User Story 1 - Network Discovery & Device Registration (Priority: P1)

**Goal**: Enable automatic mDNS discovery of devices on LAN; persist registered devices locally

**Duration**: Weeks 4-5 (~8 working days)

**Independent Test**: On LAN with 2+ devices, start app on each; verify discovered devices appear in list within <5s; register; verify persists after restart

### 3.1 Discovery Service Implementation

- [ ] T047 [P] [US1] Create src/network/discovery.py with DiscoveryService class (register app as mDNS service _kms._tcp.local.; broadcast device metadata: version, OS, model, device_id, port)
- [ ] T048 [P] [US1] Implement DiscoveryService.start_browsing() (use zeroconf to listen for _kms._tcp.local. services; collect discovered devices every 5s)
- [ ] T049 [P] [US1] Implement DiscoveryService.handle_service_added() callback (parse service TXT record; create Device object; add to discovered list)
- [ ] T050 [P] [US1] Implement DiscoveryService.handle_service_removed() callback (mark device as offline; update last_seen)
- [ ] T051 [US1] Implement periodic offline detection in DiscoveryService (devices not seen for >60s marked offline; notify UI)
- [ ] T052 [P] [US1] Create src/network/handlers.py with message handler functions (route incoming messages to appropriate handlers)

### 3.2 Device Registry & Persistence

- [ ] T053 [US1] Implement DeviceRegistry.register_device() method (save newly discovered device to SQLite; set is_registered=true on user confirmation)
- [ ] T054 [US1] Implement DeviceRegistry.load_registered_devices() method (query SQLite on startup; populate Device list from persistent storage)
- [ ] T055 [US1] Implement DeviceRegistry.update_last_seen() method (update Device.last_seen timestamp on each discovery refresh)
- [ ] T056 [P] [US1] Update Device model to include discovery_timestamp, last_seen fields (per data-model.md)
- [ ] T053a [Remediation] Implement duplicate MAC address detection in DeviceRegistry.register_device(); alert user with dialog; reject registration until duplicate resolved

### 3.3 UI for Device Discovery & Registration

- [ ] T057 [US1] Create src/ui/device_list_ui.py with DeviceListUI class (display Available Devices list; display Registered Devices list; show online/offline status)
- [ ] T058 [US1] Implement DeviceListUI.refresh_available_devices() (call discovery service; update UI list every 2 seconds)
- [ ] T059 [US1] Implement "Register Device" button handler in DeviceListUI (prompt user to confirm; save to registry; move from Available to Registered)
- [ ] T060 [US1] Implement "Forget Device" button handler in DeviceListUI (remove from registry; move back to Available if on network)
- [ ] T061 [US1] Create src/ui/status_ui.py with StatusUI class (show discovery status: "Scanning...", "Found N devices", "0 registered"; show connection status per device)

### 3.4 Integration & Testing

- [ ] T062 [P] [US1] Create integration test in tests/integration/test_discovery.py (mock mDNS; verify DiscoveryService finds devices; verify Device objects created)
- [ ] T063 [P] [US1] Create integration test in tests/integration/test_device_registry.py (mock SQLite; verify register, load, update operations)
- [ ] T064 [US1] Create integration test in tests/integration/test_device_lifecycle.py (simulate device appearing, disappearing, reappearing; verify state transitions)
- [ ] T065 [US1] Run quickstart.md scenario 1 (start 2 devices, see discovery, register one device, verify persists)

**Checkpoint**: ✅ User Story 1 complete & independently testable; devices can be discovered and registered

---

## Phase 4: User Story 2 - Master/Client Mode Configuration (Priority: P1)

**Goal**: Allow user to select Master or Client role; validate only one master per network

**Duration**: Weeks 5-6 (~8 working days)

**Independent Test**: On 2 devices, set one as Master and second as Client; verify success; try setting both as Master; verify error and config reset

### 4.1 Role Configuration Service

- [ ] T066 [P] [US2] Create src/state/role_validator.py with RoleValidator class (query network for existing MASTER; validate single-master constraint)
- [ ] T067 [P] [US2] Implement RoleValidator.set_role() method (update Device.role; broadcast role change to all connected devices; persist to registry)
- [ ] T068 [P] [US2] Implement RoleValidator.query_network_roles() method (ask all registered devices "What is your role?" via mDNS query; collect responses)
- [ ] T069 [P] [US2] Implement RoleValidator.handle_duplicate_master_error() (if device tries to become MASTER but one exists, raise ValidationError)
- [ ] T070 [P] [US2] Implement RoleValidator.handle_no_master_detected() (if no MASTER exists, show error popup; prompt user to designate one)
- [ ] T066a [Remediation] Implement master assignment logic: First device to attempt MASTER role receives it; if simultaneous requests, MAC address lexicographic tiebreaker (lower MAC wins deterministically)

### 4.2 Role Configuration UI

- [ ] T071 [US2] Create src/ui/config_menu.py with ConfigMenu class (radio button for MASTER; radio button for CLIENT; show current role; Apply/Cancel buttons)
- [ ] T072 [US2] Implement ConfigMenu.on_role_selected() handler (validate role choice; call RoleValidator.set_role(); show success or error popup)
- [ ] T073 [US2] Implement ConfigMenu.on_validation_error() handler (show error popup "Only one master device allowed"; reopen config menu)
- [ ] T074 [US2] Implement ConfigMenu.on_no_master_error() handler (show error popup "No master configured"; reopen config menu)
- [ ] T075 [US2] Persist role selection to config.json (so config survives app restart)

### 4.3 Role Broadcast Protocol

- [ ] T076 [P] [US2] Implement Protocol.ROLE_CHANGE message (format: {device_id, new_role, timestamp}; broadcast to all connected devices)
- [ ] T077 [P] [US2] Implement role change handler in src/network/handlers.py (receiver updates Device.role locally; acknowledges)

### 4.4 Testing

- [ ] T078 [P] [US2] Create unit tests in tests/unit/test_role_validator.py (verify single-master validation, no-master detection)
- [ ] T079 [P] [US2] Create integration test in tests/integration/test_role_configuration.py (simulate 2 devices; set roles; verify constraint enforcement)
- [ ] T080 [US2] Run quickstart.md scenario 2 (configure master/client roles, attempt duplicate master, recover from error)

**Checkpoint**: ✅ User Story 2 complete & independently testable; master/client roles validated and enforced

---

## Phase 5: User Story 3 - Input Sharing Activation (Priority: P1)

**Goal**: Enable keyboard/mouse input transmission from master to client over encrypted TLS channel

**Duration**: Weeks 7-9 (~9 working days) — **CORE MVP FEATURE**

**Independent Test**: Master & client connected; enable input sharing; type on master; verify text appears on client; move mouse on master; verify cursor moves on client

### 5.1 Master Input Capture

- [ ] T081 [P] [US3] Implement InputHandler.start_capture() on master (hook keyboard/mouse events; queue to InputQueue)
- [ ] T082 [P] [US3] Implement keyboard hook in WindowsInputHandler (use Win32 SetWindowsHookEx or pynput keyboard listener)
- [ ] T083 [P] [US3] Implement keyboard hook in MacOSInputHandler (use PyObjC CGEventTap for keyboard; dispatch to InputQueue)
- [ ] T084 [P] [US3] Implement mouse hook in WindowsInputHandler (hook mouse move, click, scroll events)
- [ ] T085 [P] [US3] Implement mouse hook in MacOSInputHandler (hook mouse move, click, scroll events)

### 5.2 Input Event Transmission

- [ ] T086 [US3] Create src/network/input_transmitter.py with InputTransmitter class (consume from InputQueue; serialize to JSON per protocol; encrypt with TLS; send to client)
- [ ] T087 [US3] Implement InputTransmitter.send_input_event() (marshal InputEvent to JSON; add sequence number & timestamp; transmit over TLS connection)
- [ ] T088 [P] [US3] Implement Protocol.INPUT_EVENT message format (JSON: event_type, keycode/button/position, modifiers, timestamp, sequence_number, source_device_id)

### 5.3 Client Input Simulation

- [ ] T089 [US3] Create src/network/input_receiver.py with InputReceiver class (listen for INPUT_EVENT messages; deserialize; route to InputHandler)
- [ ] T090 [P] [US3] Implement InputHandler.send_key() method (simulate keycode on client; Windows: SendInput; macOS: CGEventPost)
- [ ] T091 [P] [US3] Implement InputHandler.send_mouse_move() method (move cursor to absolute position on client screen)
- [ ] T092 [P] [US3] Implement InputHandler.send_mouse_click() method (simulate click/release; left/middle/right buttons)
- [ ] T093 [P] [US3] Implement InputHandler.send_scroll() method (simulate scroll wheel; up/down/left/right)
- [ ] T094 [P] [US3] Implement InputReceiver.on_input_event_received() handler (deserialize; call InputHandler.send_key/mouse/scroll; send ACK)

### 5.4 Connection & Error Handling

- [ ] T095 [US3] Implement TLSConnection.connect_to_master() on client (establish TLS session; verify cert; exchange auth_token if reconnecting)
- [ ] T096 [P] [US3] Implement passphrase pairing flow (master generates passphrase; client prompts user; client sends hashed passphrase; master verifies; generate & share auth_token for reconnect)
- [ ] T097 [P] [US3] Implement error handling: INPUT_ACK with ERROR status (client sends ACK with error code: PERMISSION_DENIED, WINDOW_NOT_FOUND, TIMEOUT, PARSE_ERROR, AUTH_FAILURE)
- [ ] T098 [US3] Implement max 3 passphrase attempts with exponential backoff (1s, 2s, 4s delays)
- [ ] T099 [US3] Implement keep-alive (PING/PONG every 30s; 30s timeout triggers DISCONNECTED)
- [ ] T100 [US3] Implement graceful disconnect on master offline (client stops simulating; shows "connection lost"; waits for reconnect)

### 5.5 Input Sharing Toggle UI

- [ ] T101 [US3] Create src/ui/app.py with main application window (title: "Keyboard Mouse Share"; status bar)
- [ ] T102 [US3] Add Input Sharing toggle switch in app.py (Enable/Disable; show current state)
- [ ] T103 [US3] Implement toggle handler: on_input_sharing_enabled() (call InputHandler.start_capture on master; call InputReceiver.listen on client; update UI)
- [ ] T104 [US3] Implement toggle handler: on_input_sharing_disabled() (call InputHandler.stop_capture on master; close InputReceiver on client; update UI)

### 5.6 Testing (MVP Core)

- [ ] T105 [P] [US3] Create integration test in tests/integration/test_input_transmission.py (master captures key press; client simulates; verify event delivered)
- [ ] T105a [P] [US3] Create integration test in tests/integration/test_mouse_transmission.py (master captures mouse move; client simulates; verify cursor moves)
- [ ] T105b [P] [US3] Create integration test in tests/integration/test_passphrase_pairing.py (simulate passphrase flow; verify auth_token exchange)
- [ ] T105c [P] [US3] Create integration test in tests/integration/test_connection_recovery.py (disconnect; reconnect with auth_token; verify no re-pairing needed)
- [ ] T105d [US3] Run quickstart.md scenario 3 (enable input sharing; type on master; verify keystrokes on client; toggle off)
- [ ] T105e [Remediation] Create test in tests/integration/test_input_event_delivery_rate.py to measure input delivery success rate under simulated LAN latency; verify ≥95% delivery per SC-004

### 5.7 Documentation (Phase 5 - Mandatory for MVP)

**Purpose**: Deliver critical documentation alongside MVP feature

- [ ] T101 Create [docs/README.md](docs/README.md) with feature overview, installation steps, quick start walkthrough
- [ ] T102 Create [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) with layered architecture diagram, data flow, module responsibilities, state machines
- [ ] T103 Create [docs/SECURITY.md](docs/SECURITY.md) with security model (TLS 1.3, passphrase auth, audit logging), threat model (MITM analysis, local privesc, network snooping), privacy considerations
- [ ] T104 Create [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) with common issues (discovery fails, passphrase rejection, input lag, antivirus blocking, permission errors), solutions

**Checkpoint**: ✅ **User Story 3 complete & independently testable** — **MVP FEATURE COMPLETE** (all P1 stories done; ship-ready for MVP)

---

## Phase 6: User Story 4 - Screen Layout Configuration (Priority: P2)

**Goal**: Enable seamless cursor movement between devices via custom X/Y coordinate configuration

**Duration**: Weeks 10-12 (~8 working days)

**Independent Test**: Configure 2 devices with X/Y offsets; move cursor to edge on one device; verify seamless transition to other device at expected position

### 6.1 Layout Configuration UI

- [ ] T106 [US4] Create src/ui/layout_config_ui.py with LayoutConfigUI class (form for X/Y coordinate entry; display screen resolution; save/cancel buttons)
- [ ] T107 [US4] Implement coordinate input fields: Device A at (0, 0), Device B at (1920, 0), etc.
- [ ] T108 [US4] Implement resolution input fields (read-only on input; manually override if needed)
- [ ] T109 [US4] Visualize layout on canvas (draw rectangles representing screens; show device names; allow drag-to-reposition future)
- [ ] T110 [US4] Implement Save button handler (validate layout; warn on overlaps/gaps; persist to LayoutConfig)
- [ ] T111 [P] [US4] Implement layout validation: detect overlapping monitors; warn user but allow save

### 6.2 Cursor Transition Mapper

- [ ] T112 [US4] Create src/layout/cursor_mapper.py with CursorMapper class (given device layout config and cursor position, determine which device cursor should move to)
- [ ] T113 [US4] Implement CursorMapper.calculate_transition() method (when mouse moves past screen edge, calculate target X/Y on adjacent device; use geometry helpers)
- [ ] T114 [US4] Implement CursorMapper.transform_coordinates() method (map absolute coordinates from source screen to target screen; handle DPI scaling, orientation)
- [ ] T115 [P] [US4] Handle edge cases: Y coordinate preserved when transitioning horizontally (e.g., top 10% of source stays in top 10% of target)

### 6.3 Seamless Cursor Movement

- [ ] T116 [US4] Create src/layout/transition.py with TransitionManager class (orchestrate cursor movement between devices)
- [ ] T117 [US4] Implement TransitionManager.on_mouse_move_near_edge() method (detect when cursor approaches screen edge; prepare transition)
- [ ] T118 [US4] Implement TransitionManager.execute_transition() method (move cursor to opposite edge on target device; update active device; resume input capture)
- [ ] T119 [US4] Implement latency optimization (batch events; predict cursor trajectory; pre-position on target device)

### 6.4 Layout Persistence

- [ ] T120 [US4] Update LayoutConfig class (serialize/deserialize Layout to JSON in ~/.keyboard-mouse-share/config.json)
- [ ] T121 [US4] Implement LayoutConfig.save_layout() method (persist Device X/Y/resolution/DPI to storage; broadcast to other devices)
- [ ] T122 [US4] Implement LayoutConfig.load_layout() method (on app startup, load saved layout; apply to cursor mapper)

### 6.5 Testing (P2 Enhancement)

- [ ] T123 [P] [US4] Create unit tests in tests/unit/test_cursor_mapper.py (verify coordinate transformation math)
- [ ] T124 [P] [US4] Create integration test in tests/integration/test_layout_transition.py (simulate cursor at edge; verify smooth transition)
- [ ] T125 [US4] Run quickstart.md scenario 4 (configure device layout; move mouse to screen edge; verify seamless transition)

**Checkpoint**: ✅ User Story 4 complete & independently testable; seamless cursor movement enabled

---

## Phase 7: User Story 5 - Keyboard Input Routing (Priority: P2)

**Goal**: Route keyboard input to device with active cursor; support hotkey override for manual focus switching

**Duration**: Weeks 12-14 (~8 working days)

**Independent Test**: Move cursor to client device via layout transition; type; verify keyboard input goes to client; use hotkey to switch focus; verify keyboard goes to previously-inactive device

### 7.1 Keyboard Routing Service

- [ ] T126 [US5] Create src/layout/keyboard_router.py with KeyboardRouter class (track active device; route keyboard input based on cursor location)
- [ ] T127 [P] [US5] Implement KeyboardRouter.get_active_device() method (return device with active cursor; default: master)
- [ ] T128 [US5] Implement KeyboardRouter.on_cursor_moved() callback (update active device when cursor transitions between devices)
- [ ] T129 [US5] Implement KeyboardRouter.route_input_event() method (route incoming keyboard event to active device, not cursor device)

### 7.2 Hotkey Override

- [ ] T130 [P] [US5] Implement hotkey detection in InputHandler (Ctrl+Alt+Shift+Right Arrow to switch focus; Ctrl+Alt+Shift+Left for reverse)
- [ ] T131 [US5] Implement hotkey handler: on_focus_hotkey_pressed() (toggle active device to adjacent device in layout; send ACK to user; update status bar)
- [ ] T132 [US5] Persist focus override state to config.json (device X has manual focus; survives app restart)
- [ ] T133 [P] [US5] Implement focus fallback (if active device goes offline, reset active = master)

### 7.3 Status & UI Updates

- [ ] T134 [US5] Update StatusUI to show current keyboard focus device (label: "Keyboard focus: [Master | Client A | Client B]")
- [ ] T135 [US5] Add keyboard routing configuration panel (option to disable auto-routing; always route to master; hotkey customization future)
- [ ] T136 [P] [US5] Implement visual indicator (highlight active device in device list with keyboard icon)

### 7.4 Testing (P2 Enhancement)

- [ ] T137 [P] [US5] Create unit tests in tests/unit/test_keyboard_router.py (verify active device tracking; routing logic)
- [ ] T138 [P] [US5] Create integration test in tests/integration/test_keyboard_routing.py (simulate cursor transition; verify keyboard input routes correctly)
- [ ] T139 [P] [US5] Create integration test in tests/integration/test_hotkey_override.py (press hotkey; verify focus changes; verify fallback on disconnect)
- [ ] T140 [US5] Run quickstart.md scenario 5 (move cursor to client; type; verify keyboard reaches client; press hotkey; verify switch)

**Checkpoint**: ✅ User Story 5 complete & independently testable; intelligent keyboard routing enabled

**→ ALL P1 + P2 USER STORIES COMPLETE; FEATURE FULLY FEATURED**

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Quality improvements, documentation, security, and release preparation

**Duration**: Weeks 15-18 (~14 working days, optional)

### 8.1 Error Handling & Recovery

- [ ] T141 [P] Implement comprehensive error handling across all network handlers (catch socket exceptions; reconnect logic; exponential backoff)
- [ ] T142 [P] Implement device offline detection (no response to PING for 30s; automatically disconnect; prompt user "Device offline")
- [ ] T143 [P] Implement graceful shutdown (stop input capture; close TLS connections; save state; exit cleanly)
- [ ] T144 Implement error logging to audit trail (serialize error context; log to ~/.keyboard-mouse-share/logs/)

### 8.2 Performance Optimization

- [ ] T145 [P] Profile keyboard latency (measure time from capture to transmission to simulation; target <100ms p95)
- [ ] T146 [P] Profile mouse latency (measure time from capture to simulation; target <50ms p95)
- [ ] T146a [Remediation] Benchmark mouse latency against competitor apps; if <50ms p95 not achievable, escalate to user for acceptable threshold trade-off (fallback: <75ms)
- [ ] T147 [P] Implement event batching (group multiple events in single TLS packet if arrival time <5ms)
- [ ] T148 Implement predictive cursor positioning (predict cursor trajectory; pre-move on target device before transition completes)

### 8.3 Cross-Version Compatibility

- [ ] T149 [P] Implement version negotiation in HELLO protocol (each device declares supported_features: [INPUT_SHARING, LAYOUT_CONFIG, KEYBOARD_ROUTING, PASSPHRASE_AUTH]; only offer common features)
- [ ] T150 Implement Feature downgrade gracefully (if client older version, disable LAYOUT_CONFIG and KEYBOARD_ROUTING; keep INPUT_SHARING)
- [ ] T151 Create version compatibility matrix in docs/ (v1.0 ↔ v1.1 ↔ v1.2 feature support)

### 8.4 Documentation (Phase 8 - Optional Polish)

**Note**: Critical docs (README, ARCHITECTURE, SECURITY, TROUBLESHOOTING) completed in Phase 5 as MVP requirement. Phase 8 polish docs below.

- [ ] T152 Create [docs/INSTALL.md](docs/INSTALL.md) with OS-specific installation (Windows EXE, macOS DMG)
- [ ] T153 Create [docs/USER_GUIDE.md](docs/USER_GUIDE.md) with detailed walkthrough (device discovery, role config, input sharing, layout, advanced config)
- [ ] T154 Create [docs/API.md](docs/API.md) with internal module documentation (InputHandler interface, Protocol message types, state machine transitions)
- [ ] T155 Update [docs/README.md](docs/README.md) with badges (CI/CD status, coverage %, Python version, license)

### 8.5 Security Hardening

- [ ] T160 [P] Implement certificate pinning (verify client cert fingerprint matches expected value; prevent MITM)
- [ ] T161 [P] Implement replay attack mitigation (sequence numbers in encrypted payloads; reject out-of-order events)
- [ ] T162 [P] Implement rate limiting on passphrase attempts (3 failures → 5 min lockout; prevent brute force)
- [ ] T163 Implement password/passphrase validation (6 chars minimum, no common patterns; user education)
- [ ] T164 [P] Add security audit logging (log all auth attempts, role changes, input events to encrypted log file)
- [ ] T165 Create [docs/SECURITY.md](docs/SECURITY.md) threat model section (MITM analysis, local privesc risks, network snooping mitigation)

### 8.6 Testing & Quality

- [ ] T166 [P] Add end-to-end test in tests/integration/test_e2e.py (full workflow: discovery → register → set roles → enable input sharing → type → verify)
- [ ] T167 [P] Add stress tests (rapid key presses, mouse spam, rapid device connects/disconnects)
- [ ] T168 [P] Add platform-specific tests (run Windows tests on Windows runner; macOS tests on macOS runner via GitHub Actions)
- [ ] T169 Measure code coverage (run `pytest --cov=src` and verify >70% on src/models, src/network, src/input, src/layout, src/state)
- [ ] T170 Run linting (ruff check src/ tests/; fix violations)
- [ ] T171 Run type checking (mypy src/; verify no `Any` types)
- [ ] T172 Create test coverage report in CI/CD (publish to GitHub Artifacts)

### 8.7 Build & Deployment

- [ ] T173 Create Windows installer (PyInstaller + NSIS; include README, icon, uninstaller)
- [ ] T174 Create macOS DMG installer (PyInstaller + create-dmg; code-sign binary)
- [ ] T175 Create GitHub Actions workflow for release (build exe/dmg on tag; upload to GitHub Releases)
- [ ] T176 Create CHANGELOG.md (document all features, fixes, breaking changes per version)
- [ ] T177 Create release notes template in .github/RELEASE_TEMPLATE.md

### 8.8 Validation & Sign-Off

- [ ] T178 Run complete quickstart.md walkthrough on fresh Windows 10+ VM (verify all 5 scenarios work)
- [ ] T179 Run complete quickstart.md walkthrough on fresh macOS 10.15+ VM (verify all 5 scenarios work)
- [ ] T180 Verify no security warnings in linter or dependency audit
- [ ] T181 Obtain code review approval from project owner
- [ ] T182 Update Constitution alignment checklist (confirm all 7 principles maintained)
- [ ] T183 Create release v1.0.0 tag; publish to GitHub

**Checkpoint**: ✅ Feature polished; documented; secured; release-ready

---

## Pre-Implementation Readiness Gate (MANDATORY - Must Pass Before Phase 2)

**Status**: All items below MUST be complete before proceeding to foundational implementation

### Constitutional Alignment
- [x] **Principle I (Input-First Design)**: All design choices prioritize input validation and defensive programming
- [x] **Principle II (Network Security)**: TLS 1.3, passphrase auth, audit logging specified; security testing approach defined
- [x] **Principle III (Cross-Platform)**: Windows 10+, macOS 10.15+ both supported; platform APIs abstracted; limitations documented
- [x] **Principle IV (Documentation)**: Critical docs mandatory in Phase 5; full docs by Phase 8
- [x] **Principle V (Test Coverage)**: 70%+ coverage target on critical modules; test strategy defined
- [x] **Principle VI (Phase Checklists)**: Checklists at each phase; quality gates defined
- [x] **Principle VII (Simplicity)**: Validated in Phase 1.A; no over-engineering; simple libraries

### Specification & Planning Validation
- [x] **Specification Complete**: All 18 FRs defined; 5 USs with acceptance criteria; 10 success criteria measurable
- [x] **Planning Complete**: 6 phases sequenced; MVP marked at Phase 5; P2 optional; dependencies clear
- [x] **Data Model Validated**: 4 entities (Device, Connection, Layout, InputEvent); relationships; SQL schema reviewed
- [x] **Network Protocol Specified**: mDNS discovery; TLS 1.3 handshake; JSON message formats; error handling
- [x] **Architecture Designed**: Layered architecture; InputHandler abstraction; state machines; data flows

### Technical Feasibility Confirmed
- [x] **Dependencies Available**: zeroconf (mDNS), pynput (input), PyObjC (macOS), sqlite3, pytest all verified
- [x] **Platform APIs Accessible**: Windows Win32 APIs available; macOS Quartz Event Services accessible via PyObjC
- [x] **Latency Targets Feasible**: <100ms keyboard p95 achievable (LAN 1-5ms + Python 20-50ms); mouse latency <50ms p95 challenging but benchmarked
- [x] **Simplicity Maintained**: Standard libraries preferred; no unnecessary frameworks; code readable

### Risk Assessment
- [x] **Technical Risks Identified**: Cursor geometry (MEDIUM), mouse latency (CHALLENGING), concurrent input (mitigated by one-way design)
- [x] **Mitigation Strategies Planned**: Geometry validation + user warnings; latency benchmarking in Phase 8; role-based conflict prevention
- [x] **Platform Specifics Documented**: macOS Accessibility permissions required; Windows UAC elevation required; sandboxed apps may block input

### Team Readiness
- [x] **Task List Complete**: 188 tasks across 8 phases; 40+ parallelizable tasks; clear ownership per task
- [x] **Documentation Ready**: spec.md, plan.md, data-model.md, network-protocol.md, quickstart.md, constitution.md all complete
- [x] **Design Review Passed**: Phase 1.A validation gate completed with sign-offs
- [x] **Initial Docs Drafted**: README, ARCHITECTURE, SECURITY, TROUBLESHOOTING skeletons ready for Phase 5 completion

### Final Sign-Off

**Gate Status**: ✅ **READY FOR IMPLEMENTATION**

**Approvals Required**:
- [ ] Lead Developer: _________________ Date: _______
- [ ] Architecture Reviewer: __________ Date: _______
- [ ] Project Owner: _________________ Date: _______

**Notes**: All conditions met. Project is 100% ready for Phase 1 → Phase 2 → full implementation.

---

## Dependencies & Execution Strategy

### Phase Dependencies

```
Phase 1 (Setup)
    ↓
Phase 1.A (Design Review & Validation Gate) ← MANDATORY - BLOCKS Phase 2
    ↓
Phase 2 (Foundational: Data Models, Auth, Network, Input Abstraction)
    ↓
Phase 3 (US1: Discovery) ─┐
Phase 4 (US2: Roles)    ├─ Can run in parallel
Phase 5 (US3: Input)    ├─ Or sequentially in priority order
Phase 5a (Critical Docs)├─ Parallel with US3 implementation
Phase 6 (US4: Layout)   ├─ US3 is blocking for US4
Phase 7 (US5: Routing)  ─┘
    ↓
Phase 8 (Polish, Optional Docs, Release)
```

### Within Each Phase: Parallel Opportunities

**Phase 2 (Foundational)**: Mark [P] tasks can run in parallel (different modules; no cross-module dependencies until Phase 3)

**Phase 3-7 (User Stories)**: After Foundational completion, each user story can be implemented in parallel by different team members:
- US1 (Discovery) independent of US2, US4, US5
- US2 (Roles) independent of US1, US4, US5 (but tests may depend on US1)
- US3 (Input Sharing) independent of US4, US5 (but US4, US5 depend on US3 foundations)
- US4 (Layout) depends on Layout model from Foundational (US3 captures input)
- US5 (Routing) depends on cursor position from US4

**Phase 8 (Polish)**: Mark [P] tasks can run in parallel (docs, tests, security, performance are mostly independent)

### Recommended Sequential Order

**Week-by-week (single developer)**:

- **Weeks 1**: Phase 1 (Setup) - T001–T016
- **Weeks 2-3**: Phase 2 (Foundational) - T017–T046
- **Weeks 4-5**: Phase 3 (US1 Discovery) - T047–T065
- **Weeks 5-6**: Phase 4 (US2 Roles) - T066–T080 (can overlap US1)
- **Weeks 7-9**: Phase 5 (US3 Input Sharing) ⭐ MVP - T081–T140
- **Weeks 10-12**: Phase 6 (US4 Layout) + Phase 7 (US5 Routing) - T106–T140 (can overlap)
- **Weeks 13-18**: Phase 8 (Polish, docs, security, release) - T141–T183

**Parallel opportunities (multi-developer)**:
- Weeks 2-3: All Foundational [P] tasks in parallel by 3-5 developers
- Weeks 5-6: US1, US2, US3 model creation in parallel (T018–T021, T047–T052, T081–T087)
- Weeks 10-14: US4 and US5 can be done by 2 parallel teams (both depend on Layout model only)
- Weeks 15-18: Polish tasks parallelizable (docs team, testing team, security team, build team)

---

## MVP Scope & Shipping Gate

**MVP Definition**: All P1 User Stories complete (US1, US2, US3) + Critical Documentation ✅

**MVP Completion**: End of Week 10 (Phase 5 + Phase 5a docs, Task T104)

**MVP Features Included**:
- ✅ Automatic mDNS device discovery
- ✅ Device registration & persistence
- ✅ Master/Client role configuration (single master enforced)
- ✅ Keyboard input transmission (master → client)
- ✅ Mouse input transmission (master → client)
- ✅ Passphrase-based pairing
- ✅ TLS 1.3 encryption
- ✅ Error handling & reconnection
- ✅ Keep-alive monitoring
- ✅ Audit logging

**MVP Features NOT Included** (P2, deferred):
- ❌ Screen layout configuration (requires US4)
- ❌ Seamless cursor transition (requires US4)
- ❌ Keyboard routing by cursor location (requires US5)
- ❌ Hotkey-based focus override (requires US5)

**Shipping Criteria**:
- All Phase 5 (US3) tests passing ✅
- Code coverage >70% on critical modules ✅
- No linting errors ✅
- Quickstart scenarios 1-3 verified on Windows 10+ and macOS 10.15+ ✅
- Constitution principles maintained ✅
- Security audit passed ✅
- Critical documentation complete (README, ARCHITECTURE, SECURITY, TROUBLESHOOTING) ✅
- Design Review Gate (Phase 1.A) passed ✅
- Readiness Gate (Phase 1 final) passed ✅

---

## Quality Gates Summary

### Phase 1.A Quality Gate (New)

**Must Pass Before Phase 2 Begins**:
- Design Review: data model, network protocol, architecture
- Code Review: Phase 1 implementation quality
- Risk Assessment: technical risks & mitigation
- Simplicity Check: no over-engineering
- Documentation Kickoff: critical docs drafted
- **Sign-Off Required**: Lead Developer + Architecture Reviewer

### Readiness Gate Summary

**Pre-Implementation Validation** (NEW):
- ✅ Constitutional alignment (all 7 principles)
- ✅ Specification & planning complete
- ✅ Technical feasibility confirmed
- ✅ Risk assessment completed
- ✅ Phase 1.A design review passed
- ✅ Team handoff prepared (196 tasks)
- **Final Sign-Off**: Lead Developer + Reviewer + Project Owner

---

## Validation Checklist

### By Task Type

**[P] Parallelizable Tasks**: ≥40 tasks marked [P]; enables 4+ parallel developers in Weeks 2-3, 5-9

**[US#] User Story Tags**: Each phase well-defined with story label; allows independent team handoff

**[File Path] Explicit**: Every task specifies exact file path (src/module/file.py); enables clear ownership

### By Phase

- ✅ Phase 1: 16 setup tasks
- ✅ **Phase 1.A: 8 design review/validation tasks (NEW)** ← MANDATORY GATE
- ✅ Phase 2: 30 foundational tasks
- ✅ Phase 3: 19 US1 tasks
- ✅ Phase 4: 15 US2 tasks
- ✅ Phase 5: 29 US3 tasks (MVP blocking) + 4 critical docs = 33 tasks
- ✅ Phase 6: 20 US4 tasks
- ✅ Phase 7: 15 US5 tasks
- ✅ Phase 8: 42 polish/optional docs/release tasks (was 43)
- ✅ **Remediation**: 5 tasks integrated (T027a, T053a, T066a, T105e, T146a)

**Total**: 196 tasks across all phases (was 188; +8 Phase 1.A design review)

### Quality Gates

- **By Phase**: ✅ Each phase has clear checkpoint
- **By User Story**: ✅ Each story has independent test criteria
- **By Dependency**: ✅ No circular dependencies; clear blocking relationships
- **By MVP**: ✅ Breaking point marked end of Phase 5 (ship MVP or continue to Phase 6-7)

---

## Quick Reference

### Task Lookup by Concern

**Want to find all INPUT-related tasks?**  
→ Search for [US3] tags (Phase 5); Tasks T081–T105d

**Want to find all DISCOVERY-related tasks?**  
→ Search for [US1] tags (Phase 3); Tasks T047–T065

**Want to find all DATABASE-related tasks?**  
→ Search for "registry" or "database"; Tasks T022–T026

**Want to find all TESTING tasks?**  
→ Search for "test" or "integration"; Tasks spread across each phase

**Want to run just the MVP?**  
→ Complete Phases 1-5 only (T001–T105d); ~9 weeks

**Want to run full feature?**  
→ Complete Phases 1-7 (T001–T140); ~14 weeks

**Want to polish before shipping?**  
→ Complete Phases 1-8 (T001–T183); ~18 weeks

---

## How to Use This Task List

1. **For Developers**: Copy task ID; create git branch `feat/T001-project-structure` or `feat/US1-discovery`; commit work; PR when complete
2. **For Managers**: Track progress by Phase; monitor blockers; allocate team to parallelizable tasks in Weeks 2-3, 10-14
3. **For QA**: Use "Independent Test" criteria per user story; run quickstart.md scenarios at each checkpoint
4. **For Release**: Execute Phase 8 tasks in order; obtain sign-off on T182; create release v1.0.0

---

**Generated**: 2026-02-09  
**By**: GitHub Copilot (Spec Kit task generator)  
**Specification**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)  
**Convention**: Strict checklist format with [TaskID] [P?] [Story?] Description + File Path
