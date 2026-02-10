"""Tests for Connection Status Widget."""

import pytest
from PyQt5.QtWidgets import QApplication

from src.ui.widgets.connection_status import ConnectionStatusWidget
from src.models.device import Device, DeviceRole, DeviceOS
from src.models.input_event import InputEventType


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def widget():
    """Create ConnectionStatusWidget for testing."""
    return ConnectionStatusWidget()


class TestConnectionStatusWidgetInit:
    """Test ConnectionStatusWidget initialization."""
    
    def test_init_creates_widget(self, widget):
        """Test widget is properly initialized."""
        assert widget is not None
        assert widget.current_device is None
    
    def test_init_metrics_empty(self, widget):
        """Test metrics are initialized to zero."""
        assert widget.metrics["key_press"] == 0
        assert widget.metrics["key_release"] == 0
        assert widget.metrics["mouse_move"] == 0
        assert widget.metrics["mouse_click"] == 0
        assert widget.metrics["mouse_scroll"] == 0
    
    def test_init_shows_disconnected(self, widget):
        """Test widget shows disconnected state on init."""
        assert "Not Connected" in widget.tls_status.text()
        assert "None" in widget.device_label.text()


class TestConnectionStatusWidgetLayout:
    """Test ConnectionStatusWidget UI layout."""
    
    def test_has_device_label(self, widget):
        """Test widget has device label."""
        assert widget.device_label is not None
    
    def test_has_tls_status(self, widget):
        """Test widget has TLS status label."""
        assert widget.tls_status is not None
    
    def test_has_connection_progress(self, widget):
        """Test widget has connection progress bar."""
        assert widget.connection_progress is not None
    
    def test_has_metrics_table(self, widget):
        """Test widget has metrics table."""
        assert widget.metrics_table is not None
        assert widget.metrics_table.rowCount() == 5
        assert widget.metrics_table.columnCount() == 2
    
    def test_has_last_event_label(self, widget):
        """Test widget has last event label."""
        assert widget.last_event_label is not None


class TestConnectionStatusConnected:
    """Test connected state."""
    
    def test_set_connected_updates_device_label(self, widget):
        """Test set_connected updates device label."""
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100",
            port=19999
        )
        
        widget.set_connected(device)
        
        assert "TestPC" in widget.device_label.text()
    
    def test_set_connected_updates_tls_status(self, widget):
        """Test set_connected shows connected TLS status."""
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100",
            port=19999
        )
        
        widget.set_connected(device)
        
        assert "Connected" in widget.tls_status.text()
        assert "TLS 1.3" in widget.tls_status.text()
    
    def test_set_connected_sets_progress_to_100(self, widget):
        """Test set_connected sets progress bar to 100%."""
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100",
            port=19999
        )
        
        widget.set_connected(device)
        
        assert widget.connection_progress.value() == 100
    
    def test_set_connected_resets_metrics(self, widget):
        """Test set_connected resets metrics."""
        # Set some metrics first
        widget.metrics["key_press"] = 5
        widget.metrics["mouse_move"] = 10
        
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100",
            port=19999
        )
        
        widget.set_connected(device)
        
        assert widget.metrics["key_press"] == 0
        assert widget.metrics["mouse_move"] == 0


class TestConnectionStatusConnecting:
    """Test connecting state."""
    
    def test_set_connecting_updates_device_label(self, widget):
        """Test set_connecting updates device label."""
        widget.set_connecting("TestPC")
        
        assert "TestPC" in widget.device_label.text()
    
    def test_set_connecting_updates_tls_status(self, widget):
        """Test set_connecting shows connecting TLS status."""
        widget.set_connecting("TestPC")
        
        assert "Connecting" in widget.tls_status.text()
        assert "Handshake" in widget.tls_status.text()
    
    def test_set_connecting_sets_progress_to_50(self, widget):
        """Test set_connecting sets progress bar to 50%."""
        widget.set_connecting("TestPC")
        
        assert widget.connection_progress.value() == 50


class TestConnectionStatusDisconnected:
    """Test disconnected state."""
    
    def test_set_disconnected_updates_labels(self, widget):
        """Test set_disconnected resets labels."""
        # First connect
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100",
            port=19999
        )
        
        widget.set_connected(device)
        assert widget.current_device is not None
        
        # Now disconnect
        widget.set_disconnected()
        
        assert widget.current_device is None
        assert "None" in widget.device_label.text()
        assert "Not Connected" in widget.tls_status.text()
    
    def test_set_disconnected_sets_progress_to_zero(self, widget):
        """Test set_disconnected sets progress to 0%."""
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100",
            port=19999
        )
        
        widget.set_connected(device)
        widget.set_disconnected()
        
        assert widget.connection_progress.value() == 0
    
    def test_set_disconnected_resets_metrics(self, widget):
        """Test set_disconnected resets metrics."""
        # Set some metrics
        widget.metrics["key_press"] = 5
        widget.metrics["mouse_click"] = 3
        
        widget.set_disconnected()
        
        assert widget.metrics["key_press"] == 0
        assert widget.metrics["mouse_click"] == 0


class TestConnectionStatusInputEvents:
    """Test input event tracking."""
    
    def test_update_key_press_event(self, widget):
        """Test update_input_event increments key press count."""
        widget.update_input_event(InputEventType.KEY_PRESS, {})
        
        assert widget.metrics["key_press"] == 1
    
    def test_update_key_release_event(self, widget):
        """Test update_input_event increments key release count."""
        widget.update_input_event(InputEventType.KEY_RELEASE, {})
        
        assert widget.metrics["key_release"] == 1
    
    def test_update_mouse_move_event(self, widget):
        """Test update_input_event increments mouse move count."""
        widget.update_input_event(InputEventType.MOUSE_MOVE, {})
        
        assert widget.metrics["mouse_move"] == 1
    
    def test_update_mouse_click_event(self, widget):
        """Test update_input_event increments mouse click count."""
        widget.update_input_event(InputEventType.MOUSE_CLICK, {})
        
        assert widget.metrics["mouse_click"] == 1
    
    def test_update_mouse_scroll_event(self, widget):
        """Test update_input_event increments mouse scroll count."""
        widget.update_input_event(InputEventType.MOUSE_SCROLL, {})
        
        assert widget.metrics["mouse_scroll"] == 1
    
    def test_multiple_events_increment_counts(self, widget):
        """Test multiple events increment counts correctly."""
        widget.update_input_event(InputEventType.KEY_PRESS, {})
        widget.update_input_event(InputEventType.KEY_PRESS, {})
        widget.update_input_event(InputEventType.KEY_PRESS, {})
        
        assert widget.metrics["key_press"] == 3
    
    def test_mixed_events_track_separately(self, widget):
        """Test different event types tracked separately."""
        widget.update_input_event(InputEventType.KEY_PRESS, {})
        widget.update_input_event(InputEventType.KEY_PRESS, {})
        widget.update_input_event(InputEventType.MOUSE_CLICK, {})
        widget.update_input_event(InputEventType.MOUSE_MOVE, {})
        
        assert widget.metrics["key_press"] == 2
        assert widget.metrics["mouse_click"] == 1
        assert widget.metrics["mouse_move"] == 1
    
    def test_last_event_label_updated(self, widget):
        """Test last event label is updated."""
        widget.update_input_event(InputEventType.KEY_PRESS, {})
        
        assert "Key Press" in widget.last_event_label.text()
        assert "1" in widget.last_event_label.text()
    
    def test_last_event_reflects_latest(self, widget):
        """Test last event label reflects most recent event."""
        widget.update_input_event(InputEventType.KEY_PRESS, {})
        widget.update_input_event(InputEventType.MOUSE_CLICK, {})
        
        assert "Mouse Click" in widget.last_event_label.text()


class TestConnectionStatusMetricsDisplay:
    """Test metrics table display."""
    
    def test_metrics_table_rows(self, widget):
        """Test metrics table has correct rows."""
        assert widget.metrics_table.rowCount() == 5
    
    def test_metrics_table_headers(self, widget):
        """Test metrics table has correct headers."""
        header0 = widget.metrics_table.horizontalHeaderItem(0).text()
        header1 = widget.metrics_table.horizontalHeaderItem(1).text()
        
        assert "Event Type" in header0 or "Type" in header0
        assert "Count" in header1
    
    def test_metrics_table_initial_state(self, widget):
        """Test metrics table shows zeros initially."""
        for row in range(5):
            item = widget.metrics_table.item(row, 1)
            assert item is not None
            assert "0" in item.text()
    
    def test_metrics_table_updates_on_event(self, widget):
        """Test metrics table updates when event occurs."""
        widget.update_input_event(InputEventType.KEY_PRESS, {})
        
        item = widget.metrics_table.item(0, 1)
        assert "1" in item.text()
    
    def test_metrics_table_reflects_all_counts(self, widget):
        """Test metrics table reflects all event counts."""
        events = [
            (InputEventType.KEY_PRESS, 0),
            (InputEventType.KEY_RELEASE, 1),
            (InputEventType.MOUSE_MOVE, 2),
            (InputEventType.MOUSE_CLICK, 3),
            (InputEventType.MOUSE_SCROLL, 4),
        ]
        
        for event_type, row in events:
            widget.update_input_event(event_type, {})
            
            item = widget.metrics_table.item(row, 1)
            assert "1" in item.text()


class TestConnectionStatusStateTransitions:
    """Test state transitions."""
    
    def test_transition_disconnected_to_connecting(self, widget):
        """Test transition from disconnected to connecting."""
        assert "Not Connected" in widget.tls_status.text()
        
        widget.set_connecting("TestPC")
        
        assert "Connecting" in widget.tls_status.text()
    
    def test_transition_connecting_to_connected(self, widget):
        """Test transition from connecting to connected."""
        widget.set_connecting("TestPC")
        
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100",
            port=19999
        )
        
        widget.set_connected(device)
        
        assert "Connected" in widget.tls_status.text()
    
    def test_transition_connected_to_disconnected(self, widget):
        """Test transition from connected to disconnected."""
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100",
            port=19999
        )
        
        widget.set_connected(device)
        widget.set_disconnected()
        
        assert "Not Connected" in widget.tls_status.text()
    
    def test_metrics_reset_on_reconnect(self, widget):
        """Test metrics reset when reconnecting."""
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100",
            port=19999
        )
        
        # Connect and generate events
        widget.set_connected(device)
        widget.update_input_event(InputEventType.KEY_PRESS, {})
        widget.update_input_event(InputEventType.KEY_PRESS, {})
        
        assert widget.metrics["key_press"] == 2
        
        # Disconnect
        widget.set_disconnected()
        assert widget.metrics["key_press"] == 0
        
        # Reconnect
        widget.set_connected(device)
        assert widget.metrics["key_press"] == 0


class TestConnectionStatusErrorHandling:
    """Test error handling."""
    
    def test_handles_missing_device_data(self, widget):
        """Test handles missing device gracefully."""
        # Should not raise exception
        widget.update_input_event(InputEventType.KEY_PRESS, {})
        assert widget.metrics["key_press"] == 1
    
    def test_handles_invalid_event_type(self, widget):
        """Test handles invalid event type gracefully."""
        # Should not crash on unexpected event type
        try:
            widget.update_input_event(None, {})
        except Exception as e:
            pytest.fail(f"Should not raise exception: {e}")
    
    def test_multiple_disconnects_safe(self, widget):
        """Test multiple disconnects are safe."""
        widget.set_disconnected()
        widget.set_disconnected()
        
        # Should not raise exception
        assert widget.current_device is None


class TestConnectionStatusDeviceStorage:
    """Test device storage."""
    
    def test_current_device_stored(self, widget):
        """Test current device is stored in widget."""
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100",
            port=19999
        )
        
        widget.set_connected(device)
        
        assert widget.current_device is not None
        assert widget.current_device.name == "TestPC"
    
    def test_current_device_cleared_on_disconnect(self, widget):
        """Test current device is cleared on disconnect."""
        device = Device(
            name="TestPC",
            os=DeviceOS.WINDOWS,
            role=DeviceRole.MASTER,
            ip_address="192.168.1.100",
            port=19999
        )
        
        widget.set_connected(device)
        assert widget.current_device is not None
        
        widget.set_disconnected()
        assert widget.current_device is None
