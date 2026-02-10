"""Demo script showing UI widgets with sample data."""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from datetime import datetime, timezone

from src.ui.manager import UIConfiguration
from src.ui.main_window import MainWindow
from src.models.input_event import InputEventType


logging.basicConfig(level=logging.INFO)


def demo_sample_devices():
    """Create sample devices for UI demo."""
    return [
        {
            "id": "device-001",
            "name": "Gaming PC",
            "os": "Windows",
            "ip_address": "192.168.1.100",
            "status": "online",
            "last_seen": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "device-002",
            "name": "MacBook Pro",
            "os": "macOS",
            "ip_address": "192.168.1.101",
            "status": "online",
            "last_seen": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "device-003",
            "name": "Work Laptop",
            "os": "Windows",
            "ip_address": "192.168.1.102",
            "status": "offline",
            "last_seen": "2026-02-09T08:30:00+00:00"
        },
        {
            "id": "device-004",
            "name": "Raspberry Pi",
            "os": "Linux",
            "ip_address": "192.168.1.200",
            "status": "online",
            "last_seen": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "device-005",
            "name": "Old Notebook",
            "os": "Windows",
            "ip_address": "192.168.1.103",
            "status": "offline",
            "last_seen": "2026-02-08T14:15:00+00:00"
        }
    ]


def main():
    """Run UI demo with sample data."""
    app = QApplication(sys.argv)
    
    # Create UI configuration
    config = UIConfiguration(device_name="MyMainPC")
    
    # Create main window
    main_window = MainWindow(config)
    
    # Populate device discovery tab with sample devices
    sample_devices = demo_sample_devices()
    main_window.device_list_widget.update_device_list(sample_devices)
    
    print("=" * 70)
    print("UI DEMO: Device Discovery & Connection Status")
    print("=" * 70)
    print()
    print("TAB 1: DEVICE DISCOVERY")
    print("-" * 70)
    print("[SIGNAL] Available Devices")
    print()
    for device in sample_devices:
        status_char = "[ON]" if device["status"] == "online" else "[OFF]"
        print(f"  {status_char} {device['name']:20} ({device['os']:8}) {device['ip_address']}")
    print()
    print("  [CONNECT] [DISCONNECT]  (buttons enabled for online/connected)")
    print()
    
    print("TAB 2: CONNECTION STATUS")
    print("-" * 70)
    print("[LOCK] Connection Status")
    print("  Connected Device: None")
    print("  TLS Status: Not Connected")
    print("  Connection Progress: [--------] 0%")
    print()
    print("[CHART] Input Event Metrics")
    print("  +------------------+-------+")
    print("  | Event Type       | Count |")
    print("  +------------------+-------+")
    print("  | Key Press        |     0 |")
    print("  | Key Release      |     0 |")
    print("  | Mouse Move       |     0 |")
    print("  | Mouse Click      |     0 |")
    print("  | Mouse Scroll     |     0 |")
    print("  +------------------+-------+")
    print()
    print("[FLASH] Activity Status")
    print("  Last Event: None")
    print()
    
    print("=" * 70)
    print("DEMO INTERACTIONS")
    print("=" * 70)
    print()
    print("Try selecting a device in the Device Discovery tab:")
    print("  1. Click 'Gaming PC' (online) -> Connect button enables")
    print("  2. Click 'Work Laptop' (offline) -> Connect button stays disabled")
    print()
    print("Watch Connection Status tab when connecting:")
    print("  * Connecting state: 'Connecting... (TLS Handshake)' 50%")
    print("  * Connected state: 'Connected (TLS 1.3)' 100%")
    print("  * Metrics reset on each connect/disconnect")
    print()
    print("Real-time metrics updates on input events:")
    print("  * Each keyboard key press/release increments counters")
    print("  * Each mouse move/click/scroll increments counters")
    print("  * Last event label shows most recent action")
    print()
    print("=" * 70)
    print()
    
    # Show window
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
