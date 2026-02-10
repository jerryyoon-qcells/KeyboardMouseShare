"""SQLite schema definition and migration management."""

import sqlite3
from pathlib import Path
from typing import Optional


class Database:
    """Database connection manager and schema initializer."""
    
    DB_PATH = Path.home() / ".keyboard-mouse-share" / "devices.db"
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection."""
        if isinstance(db_path, str):
            db_path = Path(db_path)
        self.db_path = db_path or self.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection: Optional[sqlite3.Connection] = None
    
    def connect(self):
        """Open database connection."""
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row  # Return rows as dicts
        # Enable foreign key constraints
        self.connection.execute("PRAGMA foreign_keys = ON")
        return self.connection
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
    
    def migrate(self):
        """Create all tables if they don't exist."""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        
        # Devices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id TEXT PRIMARY KEY,
                mac_address TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                os TEXT NOT NULL,
                role TEXT DEFAULT 'UNASSIGNED',
                ip_address TEXT,
                port INTEGER DEFAULT 19999,
                version TEXT DEFAULT '1.0.0',
                is_registered INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                CHECK (role IN ('MASTER', 'CLIENT', 'UNASSIGNED')),
                CHECK (os IN ('Windows', 'Darwin')),
                CHECK (port >= 1024 AND port <= 65535)
            )
        """)
        
        # Connections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connections (
                id TEXT PRIMARY KEY,
                master_device_id TEXT NOT NULL,
                client_device_id TEXT NOT NULL,
                status TEXT DEFAULT 'CONNECTING',
                tls_certificate TEXT,
                auth_token TEXT,
                input_event_counter INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (master_device_id) REFERENCES devices(id),
                FOREIGN KEY (client_device_id) REFERENCES devices(id),
                CHECK (status IN ('CONNECTING', 'CONNECTED', 'DISCONNECTED', 'FAILED')),
                UNIQUE (master_device_id, client_device_id)
            )
        """)
        
        # Layouts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS layouts (
                id TEXT PRIMARY KEY,
                device_id TEXT UNIQUE NOT NULL,
                x INTEGER DEFAULT 0,
                y INTEGER DEFAULT 0,
                width INTEGER DEFAULT 1920,
                height INTEGER DEFAULT 1080,
                dpi_scale REAL DEFAULT 1.0,
                orientation TEXT DEFAULT 'LANDSCAPE',
                
                FOREIGN KEY (device_id) REFERENCES devices(id),
                CHECK (x >= 0 AND y >= 0),
                CHECK (width >= 480 AND height >= 480),
                CHECK (dpi_scale >= 0.5 AND dpi_scale <= 4.0),
                CHECK (orientation IN ('LANDSCAPE', 'PORTRAIT'))
            )
        """)
        
        # Input events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS input_events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                source_device_id TEXT NOT NULL,
                target_device_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_encrypted INTEGER DEFAULT 1,
                
                FOREIGN KEY (source_device_id) REFERENCES devices(id),
                FOREIGN KEY (target_device_id) REFERENCES devices(id),
                CHECK (event_type IN (
                    'KEY_PRESS', 'KEY_RELEASE', 'MOUSE_MOVE',
                    'MOUSE_CLICK', 'MOUSE_RELEASE', 'MOUSE_SCROLL'
                ))
            )
        """)
        
        self.connection.commit()
