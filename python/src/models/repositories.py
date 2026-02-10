"""Repository pattern implementations for database access."""

from typing import List, Optional
from .device import Device, DeviceRole, DeviceOS
from .connection import Connection, ConnectionStatus
from .layout import Layout, Orientation
from .input_event import InputEvent, InputEventType
from .schema import Database
import json
from datetime import datetime
import uuid


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
            1 if device.is_registered else 0,
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
            device.version, 1 if device.is_registered else 0,
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
    
    def list_active(self) -> List[Connection]:
        """Fetch only active connections (status=CONNECTED)."""
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM connections WHERE status = 'CONNECTED'")
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


class LayoutRepository:
    """CRUD operations for Layout entities."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, layout: Layout) -> Layout:
        """Create a new layout in the database."""
        if not layout.id:
            layout.id = str(uuid.uuid4())
        
        cursor = self.db.connection.cursor()
        cursor.execute("""
            INSERT INTO layouts (
                id, device_id, x, y, width, height, dpi_scale, orientation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            layout.id, layout.device_id,
            layout.x, layout.y, layout.width, layout.height,
            layout.dpi_scale, layout.orientation.value
        ))
        self.db.connection.commit()
        return layout
    
    def read(self, layout_id: str) -> Optional[Layout]:
        """Fetch a layout by ID."""
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM layouts WHERE id = ?", (layout_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_layout(row)
    
    def read_by_device(self, device_id: str) -> Optional[Layout]:
        """Fetch layout by device ID."""
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM layouts WHERE device_id = ?", (device_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_layout(row)
    
    def list_all(self) -> List[Layout]:
        """Fetch all layouts."""
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM layouts")
        return [self._row_to_layout(row) for row in cursor.fetchall()]
    
    def update(self, layout: Layout) -> Layout:
        """Update an existing layout."""
        cursor = self.db.connection.cursor()
        cursor.execute("""
            UPDATE layouts SET
                device_id = ?, x = ?, y = ?, width = ?, height = ?,
                dpi_scale = ?, orientation = ?
            WHERE id = ?
        """, (
            layout.device_id, layout.x, layout.y,
            layout.width, layout.height, layout.dpi_scale,
            layout.orientation.value, layout.id
        ))
        self.db.connection.commit()
        return layout
    
    def delete(self, layout_id: str) -> bool:
        """Delete a layout by ID."""
        cursor = self.db.connection.cursor()
        cursor.execute("DELETE FROM layouts WHERE id = ?", (layout_id,))
        self.db.connection.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def _row_to_layout(row) -> Layout:
        """Convert SQLite row to Layout object."""
        return Layout(
            id=row['id'],
            device_id=row['device_id'],
            x=row['x'],
            y=row['y'],
            width=row['width'],
            height=row['height'],
            dpi_scale=row['dpi_scale'],
            orientation=Orientation(row['orientation']),
        )


class InputEventRepository:
    """CRUD operations for InputEvent entities."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, event: InputEvent) -> InputEvent:
        """Create a new input event in the database."""
        cursor = self.db.connection.cursor()
        cursor.execute("""
            INSERT INTO input_events (
                id, event_type, source_device_id, target_device_id,
                payload, timestamp, is_encrypted
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event.id, event.event_type.value,
            event.source_device_id, event.target_device_id,
            json.dumps(event.payload),
            event.timestamp.isoformat(),
            1 if event.is_encrypted else 0
        ))
        self.db.connection.commit()
        return event
    
    def read(self, event_id: str) -> Optional[InputEvent]:
        """Fetch an event by ID."""
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM input_events WHERE id = ?", (event_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_event(row)
    
    def list_by_connection(
        self,
        source_device_id: str,
        target_device_id: str,
        limit: int = 100
    ) -> List[InputEvent]:
        """Fetch recent events for a connection."""
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT * FROM input_events
            WHERE source_device_id = ? AND target_device_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (source_device_id, target_device_id, limit))
        return [self._row_to_event(row) for row in cursor.fetchall()]
    
    def list_all(self, limit: int = 1000) -> List[InputEvent]:
        """Fetch all events with limit."""
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM input_events ORDER BY timestamp DESC LIMIT ?", (limit,))
        return [self._row_to_event(row) for row in cursor.fetchall()]
    
    def delete(self, event_id: str) -> bool:
        """Delete an event by ID."""
        cursor = self.db.connection.cursor()
        cursor.execute("DELETE FROM input_events WHERE id = ?", (event_id,))
        self.db.connection.commit()
        return cursor.rowcount > 0
    
    def delete_older_than(self, days: int) -> int:
        """Delete events older than N days (for cleanup)."""
        cursor = self.db.connection.cursor()
        cursor.execute("""
            DELETE FROM input_events
            WHERE datetime(timestamp) < datetime('now', '-' || ? || ' days')
        """, (days,))
        self.db.connection.commit()
        return cursor.rowcount
    
    @staticmethod
    def _row_to_event(row) -> InputEvent:
        """Convert SQLite row to InputEvent object."""
        return InputEvent(
            id=row['id'],
            event_type=InputEventType(row['event_type']),
            source_device_id=row['source_device_id'],
            target_device_id=row['target_device_id'],
            payload=json.loads(row['payload']),
            timestamp=datetime.fromisoformat(row['timestamp']),
            is_encrypted=bool(row['is_encrypted']),
        )
