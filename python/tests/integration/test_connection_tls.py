"""Integration tests for Connection Handler (real TLS handshake)."""

import pytest
import json
import logging
import tempfile
import threading
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from src.network.connection import ConnectionHandler

logger = logging.getLogger(__name__)


@pytest.fixture
def tls_certs(tmp_path):
    """Generate self-signed certificates for testing using cryptography library."""
    cert_file = tmp_path / "cert.pem"
    key_file = tmp_path / "key.pem"
    
    try:
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Test"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"Test"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Test"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(u"localhost"),
                x509.DNSName(u"127.0.0.1"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Write private key
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        return str(cert_file), str(key_file)
    except Exception as e:
        pytest.skip(f"Certificate generation failed: {e}")


class TestConnectionHandlerIntegration:
    """Integration tests for TLS communication."""
    
    def test_handler_creation(self, tls_certs):
        """Test creating ConnectionHandler with real certificates."""
        cert_file, key_file = tls_certs
        
        handler = ConnectionHandler(19999, cert_file, key_file)
        
        assert handler.port == 19999
        assert handler.certfile == cert_file
        assert handler.keyfile == key_file
        assert handler.ssl_context is not None
        assert handler.socket is None
    
    def test_listen_and_accept_flow(self, tls_certs):
        """Test server listen and accept methods."""
        cert_file, key_file = tls_certs
        
        server = ConnectionHandler(19999, cert_file, key_file)
        result = server.listen(backlog=5)
        
        assert result == True
        assert server.socket is not None
        
        # Cleanup
        server.close()
    
    def test_client_server_communication(self, tls_certs):
        """Test two-way communication between client and server."""
        cert_file, key_file = tls_certs
        port = 20000
        
        # Server-side code
        def run_server():
            server = ConnectionHandler(port, cert_file, key_file)
            server.listen(backlog=1)
            
            # Accept one connection
            client = server.accept()
            if client:
                # Receive message from client
                msg = client.receive_message(timeout=5)
                assert msg is not None
                assert msg["msg_type"] == "HELLO"
                assert msg["data"]["device_id"] == "client1"
                
                # Send response
                response = client.send_message("HELLO_RESPONSE", {
                    "device_id": "server1",
                    "accepted": True
                })
                assert response == True
                
                client.close()
            server.close()
        
        # Start server in background
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Give server time to start listening
        time.sleep(0.5)
        
        # Client-side code
        client = ConnectionHandler(port, cert_file, key_file)
        
        try:
            # Connect to server
            connected = client.connect("127.0.0.1", port, timeout=5)
            if connected:
                # Send greeting
                sent = client.send_message("HELLO", {"device_id": "client1"})
                assert sent == True
                
                # Receive response
                response = client.receive_message(timeout=5)
                assert response is not None
                assert response["msg_type"] == "HELLO_RESPONSE"
                assert response["data"]["device_id"] == "server1"
        finally:
            client.close()
        
        # Wait for server thread
        server_thread.join(timeout=5)
    
    def test_message_with_json_payload(self, tls_certs):
        """Test sending complex JSON payload."""
        cert_file, key_file = tls_certs
        port = 20001
        
        test_data = {
            "event_type": "KEY_PRESS",
            "keycode": "A",
            "modifiers": ["Shift", "Ctrl"],
            "x": 100,
            "y": 200,
            "button": "left",
            "nested": {
                "key": "value",
                "list": [1, 2, 3]
            }
        }
        
        received_data = {}
        server_ready = threading.Event()
        
        def run_server():
            try:
                server = ConnectionHandler(port, cert_file, key_file)
                if not server.listen(backlog=1):
                    return
                
                server_ready.set()
                
                client = server.accept()
                if client:
                    msg = client.receive_message(timeout=5)
                    if msg:
                        received_data["msg"] = msg
                    client.close()
                server.close()
            except Exception as e:
                logger.error(f"Server error: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to be listening
        assert server_ready.wait(timeout=5), "Server did not start listening in time"
        time.sleep(0.5)  # Increased delay for server initialization
        
        client = ConnectionHandler(port, cert_file, key_file)
        try:
            if client.connect("127.0.0.1", port, timeout=5):
                client.send_message("INPUT_EVENT", test_data)
        finally:
            client.close()
        
        server_thread.join(timeout=5)
        
        assert "msg" in received_data
        assert received_data["msg"]["data"] == test_data
    
    def test_multiple_messages(self, tls_certs):
        """Test sending multiple messages in sequence."""
        cert_file, key_file = tls_certs
        port = 20002
        
        received_messages = []
        server_ready = threading.Event()
        
        def run_server():
            try:
                server = ConnectionHandler(port, cert_file, key_file)
                if not server.listen(backlog=1):
                    return
                
                server_ready.set()
                
                client = server.accept()
                if client:
                    for _ in range(3):
                        msg = client.receive_message(timeout=5)
                        if msg:
                            received_messages.append(msg)
                    client.close()
                server.close()
            except Exception as e:
                logger.error(f"Server error: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to be listening
        assert server_ready.wait(timeout=5), "Server did not start listening in time"
        time.sleep(0.2)
        
        client = ConnectionHandler(port, cert_file, key_file)
        try:
            if client.connect("127.0.0.1", port, timeout=5):
                for i in range(3):
                    client.send_message(f"MSG{i}", {"seq": i})
        finally:
            client.close()
        
        server_thread.join(timeout=5)
        
        assert len(received_messages) == 3
        for i, msg in enumerate(received_messages):
            assert msg["msg_type"] == f"MSG{i}"
            assert msg["data"]["seq"] == i


class TestTLSHandshake:
    """Test TLS handshake specifics."""
    
    def test_mutual_tls_handshake(self, tls_certs):
        """Test that TLS handshake completes successfully."""
        cert_file, key_file = tls_certs
        port = 20003
        
        handshake_complete = {"server": False, "client": False}
        server_ready = threading.Event()
        
        def run_server():
            try:
                server = ConnectionHandler(port, cert_file, key_file)
                if server.listen(backlog=1):
                    server_ready.set()
                    client = server.accept()
                    if client and client.socket:
                        handshake_complete["server"] = True
                        client.close()
                server.close()
            except Exception as e:
                logger.error(f"Server error: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to be listening
        assert server_ready.wait(timeout=5), "Server did not start listening in time"
        time.sleep(0.2)
        
        client = ConnectionHandler(port, cert_file, key_file)
        if client.connect("127.0.0.1", port, timeout=5):
            handshake_complete["client"] = True
        client.close()
        
        server_thread.join(timeout=5)
        
        assert handshake_complete["server"] == True
        assert handshake_complete["client"] == True
    
    def test_connection_timeout(self, tls_certs):
        """Test connection timeout when server doesn't respond."""
        cert_file, key_file = tls_certs
        
        client = ConnectionHandler(20004, cert_file, key_file)
        
        # Try to connect to port with no service
        result = client.connect("127.0.0.1", 20004, timeout=1)
        
        assert result == False


class TestMessageProtocol:
    """Test message protocol compliance."""
    
    def test_timestamp_included(self, tls_certs):
        """Test that all messages include timestamp."""
        cert_file, key_file = tls_certs
        port = 20005
        
        received_messages = []
        server_ready = threading.Event()
        
        def run_server():
            try:
                server = ConnectionHandler(port, cert_file, key_file)
                if not server.listen(backlog=1):
                    return
                
                server_ready.set()
                
                client = server.accept()
                if client:
                    msg = client.receive_message(timeout=5)
                    if msg:
                        received_messages.append(msg)
                    client.close()
                server.close()
            except Exception as e:
                logger.error(f"Server error: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to be listening
        assert server_ready.wait(timeout=5), "Server did not start listening in time"
        time.sleep(0.2)
        
        client = ConnectionHandler(port, cert_file, key_file)
        try:
            if client.connect("127.0.0.1", port, timeout=5):
                client.send_message("TEST", {"data": "value"})
        finally:
            client.close()
        
        server_thread.join(timeout=5)
        
        assert len(received_messages) == 1
        assert "timestamp" in received_messages[0]
        
        # Parse timestamp to verify it's valid ISO format
        ts = received_messages[0]["timestamp"]
        try:
            datetime.fromisoformat(ts)
        except ValueError:
            pytest.fail(f"Invalid ISO timestamp: {ts}")


class TestErrorHandling:
    """Test error handling in TLS communication."""
    
    def test_receive_on_closed_connection(self, tls_certs):
        """Test receiving from a closed connection."""
        cert_file, key_file = tls_certs
        port = 20006
        
        handler = ConnectionHandler(port, cert_file, key_file)
        # Try to receive without connecting
        result = handler.receive_message(timeout=1)
        
        assert result is None
    
    def test_send_on_closed_connection(self, tls_certs):
        """Test sending on a closed connection."""
        cert_file, key_file = tls_certs
        port = 20007
        
        handler = ConnectionHandler(port, cert_file, key_file)
        # Try to send without connecting
        result = handler.send_message("TEST", {})
        
        assert result == False
