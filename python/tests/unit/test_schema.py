"""Tests for SQLite schema and database initialization."""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from src.models.schema import Database


class TestDatabase:
    """Test Database class and schema initialization."""
    
    def test_database_creates_directory(self):
        """Test that database creates config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path=db_path)
            
            assert db_path.parent.exists()
    
    def test_database_connects(self):
        """Test database connection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path=db_path)
            db.connect()
            
            assert db.connection is not None
            
            db.close()
    
    def test_database_creates_all_tables(self):
        """Test that migration creates all required tables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path=db_path)
            db.connect()
            db.migrate()
            
            cursor = db.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            
            assert 'devices' in tables
            assert 'connections' in tables
            assert 'layouts' in tables
            assert 'input_events' in tables
            
            db.close()
    
    def test_database_enforces_device_port_constraint(self):
        """Test that device port constraint is enforced."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path=db_path)
            db.connect()
            db.migrate()
            
            cursor = db.connection.cursor()
            
            # Should fail: port too low
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO devices (id, mac_address, name, os, port) VALUES (?, ?, ?, ?, ?)",
                    ("id1", "aa:bb:cc:dd:ee:ff", "test", "Windows", 100)
                )
                db.connection.commit()
            
            db.close()
    
    def test_database_enforces_device_role_constraint(self):
        """Test that device role constraint is enforced."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path=db_path)
            db.connect()
            db.migrate()
            
            cursor = db.connection.cursor()
            
            # Should fail: invalid role
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO devices (id, mac_address, name, os, role) VALUES (?, ?, ?, ?, ?)",
                    ("id1", "aa:bb:cc:dd:ee:ff", "test", "Windows", "INVALID")
                )
                db.connection.commit()
            
            db.close()
    
    def test_database_enforces_connection_unique_pair(self):
        """Test that connections can't have duplicate device pairs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path=db_path)
            db.connect()
            db.migrate()
            
            cursor = db.connection.cursor()
            
            # Insert two devices
            cursor.execute(
                "INSERT INTO devices (id, mac_address, name, os) VALUES (?, ?, ?, ?)",
                ("device1", "aa:bb:cc:dd:ee:01", "Device1", "Windows")
            )
            cursor.execute(
                "INSERT INTO devices (id, mac_address, name, os) VALUES (?, ?, ?, ?)",
                ("device2", "aa:bb:cc:dd:ee:02", "Device2", "Windows")
            )
            
            # Insert connection
            cursor.execute(
                "INSERT INTO connections (id, master_device_id, client_device_id) VALUES (?, ?, ?)",
                ("conn1", "device1", "device2")
            )
            db.connection.commit()
            
            # Try to insert again - should fail
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO connections (id, master_device_id, client_device_id) VALUES (?, ?, ?)",
                    ("conn2", "device1", "device2")
                )
                db.connection.commit()
            
            db.close()
    
    def test_database_enforces_layout_unique_per_device(self):
        """Test that each device can have only one layout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path=db_path)
            db.connect()
            db.migrate()
            
            cursor = db.connection.cursor()
            
            # Insert device
            cursor.execute(
                "INSERT INTO devices (id, mac_address, name, os) VALUES (?, ?, ?, ?)",
                ("device1", "aa:bb:cc:dd:ee:01", "Device1", "Windows")
            )
            
            # Insert layout
            cursor.execute(
                "INSERT INTO layouts (id, device_id) VALUES (?, ?)",
                ("layout1", "device1")
            )
            db.connection.commit()
            
            # Try to insert another layout for same device - should fail
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO layouts (id, device_id) VALUES (?, ?)",
                    ("layout2", "device1")
                )
                db.connection.commit()
            
            db.close()
    
    def test_database_enforces_foreign_key_constraints(self):
        """Test that foreign key constraints are enforced."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path=db_path)
            db.connect()
            db.migrate()
            
            cursor = db.connection.cursor()
            
            # Try to insert connection with non-existent device - should fail
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO connections (id, master_device_id, client_device_id) VALUES (?, ?, ?)",
                    ("conn1", "nonexistent1", "nonexistent2")
                )
                db.connection.commit()
            
            db.close()
