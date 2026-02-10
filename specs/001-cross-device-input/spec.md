# Feature Specification: Cross-Device Input Sharing

**Feature Branch**: `001-cross-device-input`  
**Created**: 2026-02-09  
**Status**: Draft  
**Input**: User description: Build a unified keyboard and mouse sharing system where devices auto-discover each other on a network, with configurable master/client roles and intelligent input routing based on cursor position and screen layout.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Network Discovery & Device Registration (Priority: P1)

A user starts the Keyboard Mouse Share application on their Windows machine. The app automatically scans the local network (via mDNS or broadcast) and discovers other devices running the app. Once discovered, devices are displayed in a list. The user can select another device and establish a connection. The connection is registered locally so that devices remember each other across restarts.

**Why this priority**: Without network discovery, manual device registration would be tedious. Auto-discovery is the primary UX differentiator and makes the tool "easy to use."

**Independent Test**: Can be tested by starting two instances on different machines on the same network (or simulated network) and verifying that each discovers the other within a reasonable time (<5 seconds). A successful discovery shows the remote device in the UI without manual configuration.

**Acceptance Scenarios**:

1. **Given** two devices running Keyboard Mouse Share on the same network, **When** both apps are started, **Then** each device discovers the other and displays it in the "Available Devices" list.
2. **Given** discovery has found a device, **When** the user clicks "Register" or "Connect", **Then** the connection is saved and the device appears in "Registered Devices" list even after restart.
3. **Given** a registered device is no longer on the network, **When** the app attempts to connect, **Then** it gracefully shows "Device offline" without crashing.

---

### User Story 2 - Master/Client Mode Configuration (Priority: P1)

The user opens a configuration menu and selects whether their device should operate as a "Master" (controls input from one primary location) or "Client" (receives input from master). The app validates that only one master exists per network. If the user tries to set two devices as master, an error popup appears: "Only one master device allowed in the network. Please select another device to be the client." The configuration menu reopens, allowing the user to change the role.

**Why this priority**: Master/Client mode is essential to define the input control hierarchy. Without clear roles, input conflicts and unexpected behavior occur.

**Independent Test**: Can be tested on two devices by attempting to set both as master and verifying the error popup and configuration reset; then verifying that setting one as master and one as client succeeds.

**Acceptance Scenarios**:

1. **Given** two connected devices, **When** the first device is set as "Master" and second as "Client", **Then** both devices save the configuration and agree on roles.
2. **Given** the first device is set as "Master", **When** the user tries to set the second device as "Master" as well, **Then** an error popup says "Only one master device allowed in the network" and opens the configuration menu.
3. **Given** a device is configured as a role, **When** the configuration menu is opened at any time, **Then** the current role is shown as selected and can be changed on-the-fly without disconnecting.
4. **Given** no master is configured (both are clients or offline), **When** the app detects this state, **Then** it shows an error popup and prompts the user to designate one device as master.

---

### User Story 3 - Input Sharing Activation (Priority: P1)

After master/client roles are set, the user enables "Input Sharing" toggle. When enabled, keyboard and mouse input from the master device can be sent to the client device. The physical keyboard and mouse remain connected to the master; the client receives the input events remotely and simulates them locally. The user can toggle this on/off at any time without disconnecting the device.

**Why this priority**: Enabling actual input sharing is the core functionality. This is the MVP feature.

**Independent Test**: Can be tested by enabling input sharing, typing on the master device, and verifying that characters appear in an input field on the client device; similarly, moving the master's mouse can be simulated on the client.

**Acceptance Scenarios**:

1. **Given** master/client roles are configured, **When** "Input Sharing" is enabled on the master, **Then** keyboard input from the master is transmitted to the client and simulated locally.
2. **Given** input sharing is active, **When** the user types on the master's keyboard, **Then** the keystrokes appear in the active window on the client device.
3. **Given** input sharing is active, **When** the user moves the master's mouse, **Then** the client device's mouse cursor moves in sync (subject to layout configuration).
4. **Given** input sharing is active, **When** the user toggles "Input Sharing" off, **Then** input is no longer transmitted and devices operate independently.
5. **Given** input sharing is active, **When** the master device goes offline, **Then** the client device shows "connection lost" and input stops being transmitted.

---

### User Story 4 - Screen Layout Configuration (Priority: P2)

The user opens the "Layout Settings" menu and defines the physical positioning of devices relative to each other using custom X/Y coordinates. For example, if a MacBook is on the left side of the desk and a Windows PC is on the right, the user specifies: "MacBook at coordinates (0, 0), Windows at (1920, 0)." The app also captures screen resolution and orientation (landscape/portrait) for each device. When the mouse cursor moves to the edge of the MacBook's screen on the left, it seamlessly transitions to the opposite edge of the Windows screen on the right, creating the illusion of a single extended desktop.

**Why this priority**: Layout configuration enables seamless cursor movement between devices, which is critical for usability but can be implemented after basic input sharing works.

**Independent Test**: Can be tested by positioning two displays in the layout configuration, moving the mouse to an edge on one device, and verifying smooth cursor transition to the connected device at the expected position.

**Acceptance Scenarios**:

1. **Given** two devices are connected, **When** the user opens "Layout Settings" and sets Device A at coordinates (0, 0) and Device B at (1920, 0), **Then** the configuration is saved for cursor tracking.
2. **Given** layout is configured with Device A (1920×1080, at 0/0) and Device B (2560×1440, at 1920/0), **When** the mouse moves right past Device A's screen edge (X > 1920), **Then** the cursor appears on the left edge of Device B's screen.
3. **Given** layout is configured, **When** the user adjusts the X/Y coordinates or resolution, **Then** the cursor movement immediately adapts to the new layout.
4. **Given** layout is configured, **When** the user moves the mouse up/down while transitioning horizontally, **Then** the vertical position is preserved relative to the new screen (e.g., top 10% of one screen stays in top 10% of the other).
5. **Given** a device is removed or goes offline, **When** the layout is reconfigured with a new device, **Then** the old device is removed from the layout map.

---

### User Story 5 - Keyboard Input Routing (Priority: P2)

By default, keyboard input is sent to whichever device is currently holding the mouse cursor. So if the user moves the mouse to the client device using layout-based cursor transitions, subsequent keyboard input automatically goes to the client. The user can also manually switch focus using a hotkey (e.g., Ctrl+Alt+Shift+Right Arrow) to override cursor-based routing, allowing keyboard input to the non-active device if needed.

**Why this priority**: Keyboard routing completes the seamless input experience; users don't need to think about "which device gets my typing." This follows the principle that input should go where the cursor is.

**Independent Test**: Can be tested by moving the cursor to a client device and typing, verifying keystrokes reach the client; then using a hotkey to switch focus and verifying keyboard goes to the previously-inactive device.

**Acceptance Scenarios**:

1. **Given** layout is configured and cursor has moved to the client device, **When** the user types, **Then** keyboard input is routed to the client device.
2. **Given** input routing is active, **When** the user moves the mouse back to the master device, **Then** keyboard input automatically switches to the master.
3. **Given** input is routed to a device, **When** the user presses the focus hotkey (e.g., Ctrl+Alt+Shift+Right), **Then** keyboard input switches to the adjacent device in the layout.
4. **Given** keyboard input is routed to a device, **When** that device goes offline, **Then** keyboard input automatically switches to the master (fallback to master).

---

### Edge Cases

- What happens when a device is removed from the network while input sharing is active? ➜ Connection should gracefully close; input reverts to master. No data loss or crashes.
- How does the system handle clock skew between master and client? ➜ Input events should be timestamped and replayed in order, tolerating small clock differences (< 1 second).
- What if the user defines a layout with overlapping monitor positions? ➜ System should warn and ask for clarification, but not reject the configuration outright.
- What if a user tries to set a client device as master without offline master? ➜ Allowed; the system demotes the old master to client automatically.
- What if two devices are configured with the same MAC address (duplicate)? ➜ System should detect and alert the user; registration is rejected until resolved.
- What if the network times out during device discovery? ➜ Display "Searching..." state and retry automatically; show "No devices found" after 10 seconds with option to retry manually.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST auto-discover devices on the local network (LAN) using mDNS or broadcast discovery within 5 seconds of startup.
- **FR-002**: System MUST maintain a persistent registry of registered devices (local database or file), so re-connecting after restart does not require re-discovery.
- **FR-003**: System MUST allow the user to configure one device as "Master" and others as "Client" via a configuration UI menu.
- **FR-004**: System MUST validate that only one master exists per network and show an error popup if multiple masters are detected or if no master is configured.
- **FR-005**: System MUST allow configuration to be changed at runtime (switching between master/client) without disconnecting the device.
- **FR-006**: System MUST transmit keyboard events (keycodes, modifiers like Ctrl, Alt) **from the master device's physical keyboard only** to client devices with end-to-end encryption (TLS 1.3). Client devices' local keyboards are out of scope—each device manages its own local input independently.
- **FR-007**: System MUST transmit mouse events (X/Y position, button clicks, scroll wheel) **from the master device's physical mouse only** to client devices with end-to-end encryption (TLS 1.3). Client devices' local mice are out of scope.
- **FR-008**: System MUST NOT disconnect the physical keyboard or mouse from the master device during input sharing.
- **FR-009**: System MUST accept layout configuration where each device is positioned at custom X/Y coordinates (pixel-based offset from origin), screen resolutions, orientation (landscape/portrait), and DPI scale factor (e.g., 1.0 native, 2.0 Retina macOS, variable on Windows), and persist it locally. Users can define the coordinate system freely (e.g., top-left device at 0,0; right device at 1920,0). System MUST capture and apply DPI scaling during coordinate transformation for seamless cursor positioning across high-DPI and standard displays.
- **FR-010**: System MUST calculate cursor transitions based on custom device coordinates: when cursor reaches the edge of one device's screen, it MUST determine which adjacent device (based on proximity and coordinate overlap) should receive the cursor and route it to the appropriate edge position on that device.
- **FR-011**: System MUST interpolate cursor movement across devices to create seamless transitions at screen edges based on configured layout.
- **FR-012**: System MUST provide a hotkey (default: Ctrl+Alt+Shift+Right Arrow) to manually switch keyboard focus to adjacent device in layout, overriding cursor-based routing.
- **FR-013**: System MUST default keyboard routing to the master device if no layout is configured or cursor position is ambiguous.
- **FR-014**: System MUST gracefully handle device disconnection: input sharing should stop, connection should not be re-established until explicitly triggered by user.
- **FR-015**: System MUST log all connection attempts, master/client role changes, and input events with timestamps for debugging and security audit purposes.
- **FR-016**: System MUST support backward compatibility: when connecting devices with different versions, the connection MUST succeed if both versions support the requested feature set; if a feature is unavailable in the older version, the system MUST fall back to supported features or show an explicit warning to the user.
- **FR-017**: **Out of Scope - Clarification**: Client devices' local keyboards and mice are NOT part of input sharing. Each client device manages its own local input independently. Input sharing is strictly master-to-client transmission only; client input never flows through the shared input pipeline.
- **FR-018**: System MUST require passphrase-based authentication for first-time device pairing. When a new client device connects, both master and client must enter the same 6-character passphrase. After successful authentication, the device is registered; subsequent connections MAY skip passphrase re-entry (configurable by user). Master MUST NOT accept input events from any client until passphrase is verified.
- **FR-019**: System MUST detect and reject duplicate device registration attempts. If MAC address already exists in device registry, alert user with clear message; prevent registration until duplicate is resolved.

### Functional Requirements (Updated)

- **FR-016**: System MUST support backward compatibility: when connecting devices with different versions, the connection MUST succeed if both versions support the requested feature set; if a feature is unavailable in the older version, the system MUST fall back to supported features or show an explicit warning to the user.

## Key Entities *(include if feature involves data)*

- **Device**: Represents a machine running Keyboard Mouse Share. Attributes: MAC address (unique ID), device name (user-friendly), IP address, OS type (Windows/macOS), role (Master/Client), discovery timestamp, last seen timestamp.
- **Connection**: Represents a link between two devices. Attributes: source device ID, destination device ID, encryption key (TLS certificate), established timestamp, input event counter.
- **Layout**: Represents the spatial configuration of devices. Attributes: device ID, X coordinate (pixel offset from origin), Y coordinate (pixel offset from origin), screen resolution (W×H), orientation (landscape/portrait), created/updated timestamp. Note: Coordinate system is user-defined; users establish relative positions by entering X/Y values for each device.
- **InputEvent**: Represents a keyboard or mouse event to be transmitted. Attributes: event type (KEY_PRESS, KEY_RELEASE, MOUSE_MOVE, MOUSE_CLICK, SCROLL), payload (keycode, button, X/Y, scroll delta), source device, timestamp, encrypted.

## Security & Privacy Considerations *(mandatory per Constitution)*

### Network Security
- **Does this feature transmit keyboard/mouse input or other sensitive data?** YES. Keyboard input may include passwords, credit card numbers, personal messages, etc.; mouse position may reveal sensitive UI actions.
- **Encryption method required**: TLS 1.3 for all network traffic. All connections initiated by master MUST validate client certificate to prevent unauthorized input injection.
- **Authentication/validation required**: YES. Master device MUST authenticate client device before accepting any input events. Initial pairing uses pre-shared passphrase (4-6 characters) that both devices must enter to verify identity. After first successful pairing, device is registered; subsequent connections require passphrase re-entry optional (configurable by user).
- **Security testing approach**: Penetration testing for input interception; fuzzing of encrypted payloads; testing for replay attacks; validation that client cannot inject input without master authorization; passphrase brute-force testing (suggest rate-limiting after N failed attempts).

### Privacy & Data Handling
- **What personal/sensitive data does this feature handle?** Keyboard input (passwords, messages, search queries), mouse position and clicks (revealing which UI elements user interacts with), device identities (MAC, IP, device names).
- **How is data retained/deleted?** Input events are transmitted in-memory only and MUST NOT be logged to disk by default. Audit logs (timestamps, device IDs, event counts—NOT payloads) can be retained for 7 days and then purged. User can enable detailed logging for debugging, but MUST see a warning.
- **Are there compliance requirements?** Check local regulations; GDPR may apply if collecting device info across EU users. Implement privacy notice in UI explaining what data is collected/transmitted.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can discover and connect two devices within 10 seconds of starting the app, without manual IP entry or pairing codes.
- **SC-002**: Keyboard input latency from master to client is <100ms (p95) under normal LAN conditions to feel responsive.
- **SC-003**: Mouse cursor movement appears smooth with <50ms latency (p95) when moving across configured layout boundaries.
- **SC-004**: 95% of input events (keypresses, mouse clicks) are successfully transmitted and simulated on the client device without loss or duplication.
- **SC-005**: System correctly identifies and prevents multiple masters: attempting to set a second master triggers an error popup within 2 seconds of role change.
- **SC-006**: Layout configuration allows seamless cursor transitions between devices: cursor moving to edge of one screen appears at opposite edge of adjacent screen within 100ms.
- **SC-007**: Keyboard focus automatically follows cursor position: typing while cursor is on client device sends input to client 100% of the time (when layout is configured).
- **SC-008**: System supports at least 3 connected devices simultaneously with no performance degradation (input latency remains <100ms).
- **SC-009**: Device can be added/removed from configuration without requiring app restart; users complete config changes in <30 seconds.
- **SC-010**: 90% of users successfully configure master/client roles and enable input sharing on first attempt (validated via onboarding/tutorial or user testing).

## Timing Constraints

| Operation | Time Constraint | Rationale |
|-----------|-----------------|----------|
| Device discovery scan | <5 seconds | Users expect near-immediate discovery on LAN |
| "No devices found" user message | <10 seconds | Prevent long hangs; prompt user to retry manually |
| Device offline detection | 60 seconds | Tolerate brief network hiccups; 60s is standard keep-alive timeout |
| Passphrase entry UI display | Immediate | User must see passphrase entry prompt within 1s of connection attempt |
| Input event delivery (keyboard) | <100ms p95 | Perceived responsiveness threshold for typing |
| Input event delivery (mouse) | <50ms p95 | Perceived responsiveness threshold for cursor movement |

## Known Limitations

- **Lock/Login Screen Unavailability**: Input sharing is unavailable during OS lock screen, login screen, or secure operation modes per OS security restrictions. Input sharing resumes automatically upon unlock/login completion.
- **Sandboxed Applications**: Some sandboxed or security-restricted applications may block input simulation or enforce additional permission prompts.
- **Elevated Privileges Required**: Input hook installation requires administrator/elevated user privileges on Windows and Accessibility permissions on macOS system settings.

## Assumptions

- Devices are on the same local network (LAN); no WAN/internet sharing is planned for this version.
- Users have administrative access on their devices to install and run the application.
- Device discovery via mDNS is available; in restricted networks, broadcast discovery is fallback.
- Input event simulation can be performed via OS APIs (Windows: SendInput API, macOS: Quartz Event Services).
- Configuration menu can be a simple JSON file or lightweight SQLite database; no cloud sync is assumed.

## Clarifications

### Session 2026-02-09

- Q: When devices running different versions of Keyboard Mouse Share try to connect (e.g., Master v1.0, Client v1.1), should they be compatible or reject? → A: **Option B - Backward compatible**: Newer version supports old versions; features work if both support them.
  - **Impact**: Added FR-016 requiring version negotiation on connection establishment. Documented in Requirements below.

- Q: How should 3+ devices be arranged spatially in layout configuration? → A: **Option C - Fully Custom**: User can place any device at any position using coordinates (X, Y pixel offsets).
  - **Impact**: Updated FR-009 to support custom coordinate positioning instead of discrete LEFT/RIGHT/TOP/BOTTOM positions. Updated Layout entity to use pixel offsets instead of predefined positions.

- Q: What should happen if user presses a key on both master and client simultaneously? → A: **Clarification: Input sharing is one-way only (Master → Client)**. The master device's physical keyboard and mouse events are the ONLY input transmitted via the app. Client devices' local keyboards/mice are completely separate and NOT part of input sharing scope. Each client device handles its own local input independently.
  - **Impact**: Simplified FR-006, FR-007 to explicitly state "from master device only". Added FR-017 to clarify client device local input is out of scope. No conflict possible because client input never enters the shared input pipeline.

- Q: How should authentication/pairing work between master and client devices? → A: **Option A - Pre-shared Passphrase**: User manually enters a one-time passphrase on BOTH devices to pair them during initial connection (e.g., 4-6 character code). After first successful pairing, device is registered and subsequent connections may skip passphrase re-entry.
  - **Impact**: Added FR-018 requiring passphrase-based pairing for first-time connections. Client must authenticate with master using passphrase before accepting any input events.

### Functional Requirements (Updated)

- **FR-016**: System MUST support backward compatibility: when connecting devices with different versions, the connection MUST succeed if both versions support the requested feature set; if a feature is unavailable in the older version, the system MUST fall back to supported features or show an explicit warning to the user.

## Assumptions

- Devices are on the same local network (LAN); no WAN/internet sharing is planned for this version.
- Users have administrative access on their devices to install and run the application.
- Device discovery via mDNS is available; in restricted networks, broadcast discovery is fallback.
- Input event simulation can be performed via OS APIs (Windows: SendInput API, macOS: Quartz Event Services).
- Configuration menu can be a simple JSON file or lightweight SQLite database; no cloud sync is assumed.
- Version negotiation protocol MUST be documented as part of the network protocol specification during planning phase.
