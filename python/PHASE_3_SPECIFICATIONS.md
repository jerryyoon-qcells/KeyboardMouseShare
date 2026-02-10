"""Phase 3 Specifications: Discovery UI & Device Management Interface

## Overview

Phase 3 implements the graphical user interface for device discovery, connection management, 
and input relay status. This UI coordinates Phase 2 services (discovery, connection, input handlers) 
into a cohesive user experience.

## Phase 3 Architecture

### Components (3 high-level modules)

1. **DiscoveryUI** - Device discovery and pairing
   - Display available devices (LAN mDNS)
   - Show connection status indicators
   - Trigger pairing/unpair actions
   - Handle connection lifecycle UI

2. **ConnectionStatusUI** - Real-time connection monitoring
   - Display connected device details
   - Show active input relay status
   - Handle connection errors/reconnection UI
   - Display input event throughput metrics

3. **InputRelayUI** - Input capture and relay visualization
   - Show when input is being captured
   - Display target device selection
   - Handle relay pause/resume controls
   - Show latency and packet loss

## Requirements

### Functional Requirements

#### FR3.1 Device Discovery Display
- Display list of discovered devices on LAN (from Phase 2 DiscoveryService)
- Show device name, OS type, IP address
- Indicate connection status (connected, pairing, offline)
- Refresh available devices every 5 seconds
- Support manual device search trigger

#### FR3.2 Connection Management
- Allow user to select device and initiate connection
- Display TLS certificate verification UI (for Phase 4+)
- Show connection progress (DNS resolution → TLS handshake → ready)
- Display connection errors with actionable messages
- Support disconnect/reconnect actions

#### FR3.3 Input Relay Status
- Show active relay status (on/off/paused)
- Display which device is sending input (master)
- Display which devices are receiving (clients)
- Show real-time input event count (per second)
- Display connection latency to each client

#### FR3.4 Configuration Panel
- Allow user to set device name and role (master/client)
- Set keyboard capture mode (full/app-specific)
- Set mouse capture mode (full/region-specific)
- Configure auto-connect preferences

### Non-Functional Requirements

#### NFR3.1 Responsiveness
- UI updates within 100ms of network event
- Device list refresh < 200ms latency
- No UI freezing during network operations

####NFR3.2 Cross-Platform
- Windows: WinForms or PyQt5
- macOS: Cocoa or PyQt5
- Linux: GTK or PyQt5 (Phase 4+)

#### NFR3.3 Accessibility
- Keyboard shortcuts for all common actions
- Screen reader friendly labels
- 18pt minimum font for critical information

#### NFR3.4 Minimal Dependencies
- PyQt5 only (cross-platform, mature, GPL/commercial compatible)
- No Electron or web frameworks

## Phase 3 Tasks (T047-T060)

### Day 11 (T047-T050): Base UI Framework
- [ ] T047: Create UIManager class (QApplication lifecycle)
- [ ] T048: Create DeviceListWidget (QListWidget with models)
- [ ] T049: Create ConnectionStatusWidget (real-time updates)
- [ ] T050: Create MainWindow (layout, menus, signals)

### Day 12 (T051-T054): Device Discovery UI
- [ ] T051: Connect DiscoveryService to DeviceListWidget
- [ ] T052: Implement device filtering and search
- [ ] T053: Add device pair/unpair dialogs
- [ ] T054: Display connection status indicators

### Day 13 (T055-T058): Connection Management
- [ ] T055: Implement TLS connection progress indicator
- [ ] T056: Handle connection errors and user recovery
- [ ] T057: Display device role assignment UI
- [ ] T058: Implement auto-reconnect toggle

### Day 14 (T059-T060): Input Relay Status & Testing
- [ ] T059: Display real-time input event metrics
- [ ] T060: Create comprehensive UI tests (mocking Qt)

## Technical Design

### UI Architecture Pattern: Model-View-Controller (MVC)

```
Phase 2 Services       UI Models                UI Views
────────────────────  ─────────────────────  ──────────────────
DiscoveryService  →   DeviceModel        →   DeviceListWidget
                → DeviceListModel

ConnectionHandler →   ConnectionModel     →   ConnectionStatusWidget
                → ConnectionStatusModel

InputHandler      →   InputMetricsModel   →   InputRelayWidget
                → InputMetricsModel
```

### Data Flow

1. **Startup**
   - UIManager creates QApplication
   - Load saved configuration (device name, role, preferences)
   - Start Phase 2 DiscoveryService
   - Display MainWindow with empty device list

2. **Device Discovery (recurring every 5s)**
   - DiscoveryService.get_discovered_devices() → DeviceModel
   - DeviceModel notifies DeviceListWidget via signal
   - DeviceListWidget re-renders with new device list

3. **Pairing/Connection**
   - User selects device in list and clicks "Connect"
   - ConnectionDialog shows connection progress
   - ConnectionHandler.connect() establishes TLS
   - On success: update ConnectionModel → refresh ConnectionStatusWidget
   - On error: show error dialog with retry option

4. **Input Relay Active**
   - InputHandler.start() begins capturing keyboard/mouse
   - InputHandler calls listener_callback() for each event
   - EventRelay forwards events to connected device via ConnectionHandler
   - InputMetricsModel tracks event count/latency
   - InputRelayWidget updates display every 100ms

## File Structure

```
src/ui/
├── __init__.py
├── manager.py              # UIManager, QApplication lifecycle
├── main_window.py          # MainWindow, layout
├── widgets/
│   ├── __init__.py
│   ├── device_list.py      # DeviceListWidget, models
│   ├── connection_status.py # ConnectionStatusWidget
│   ├── input_relay.py      # InputRelayWidget
│   └── dialogs.py          # Connection, pairing dialogs
└── models/
    ├── __init__.py
    ├── device_model.py     # DeviceModel, DeviceListModel
    ├── connection_model.py # ConnectionModel
    └── input_metrics.py    # InputMetricsModel

tests/unit/test_ui_*.py    # 30+ tests for UI components
tests/integration/test_ui_integration.py  # Full workflow tests
```

## Success Criteria

- ✅ All 127 Phase 2 tests remain passing
- ✅ 30+ Phase 3 UI tests passing
- ✅ ≥70% code coverage including UI layer
- ✅ UI updates within 100ms of network events
- ✅ Zero UI freezes during network operations
- ✅ Cross-platform Qt5 compatibility verified

## Assumptions

1. PyQt5 is pre-installed or pip-installable
2. Display resolution ≥1024x768
3. Phase 2 services (DiscoveryService, ConnectionHandler) are fully functional
4. Network connectivity is stable (tested in Phase 2)
5. User has permission to capture keyboard/mouse on OS

## Risks & Mitigations

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Qt signals/slots complexity | Medium | Use comprehensive signal/slot tests |
| Cross-platform Qt issues | Medium | Test on Windows/macOS early |
| UI blocking on network ops | High | All network calls in background threads |
| Device list flickering | Low | Model-based updates with efficient diff |

## Integration Points

- **Phase 2 DiscoveryService**: Queries every 5s for device updates
- **Phase 2 ConnectionHandler**: TLS connection establishment
- **Phase 2 InputHandler**: Captures keyboard/mouse, calls UI callback
- **Configuration Storage**: JSON file with device name, role, preferences
"""
