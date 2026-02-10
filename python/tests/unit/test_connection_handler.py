"""Unit tests for Connection Handler (mocked sockets)."""

import pytest
import json
import socket
import ssl
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timezone


@pytest.fixture
def handler_with_mocked_ssl():
    """Create ConnectionHandler with mocked SSL context."""
    with patch("src.network.connection.ssl.SSLContext"):
        from src.network.connection import ConnectionHandler
        handler = ConnectionHandler(19999, "cert.pem", "key.pem")
        handler.socket = MagicMock()
        return handler


@pytest.fixture
def cert_files(tmp_path):
    """Create temporary certificate files for testing."""
    cert_file = tmp_path / "cert.pem"
    key_file = tmp_path / "key.pem"
    
    cert_file.write_text("-----BEGIN CERTIFICATE-----\nDUMMY\n-----END CERTIFICATE-----")
    key_file.write_text("-----BEGIN PRIVATE KEY-----\nDUMMY\n-----END PRIVATE KEY-----")
    
    return str(cert_file), str(key_file)


class TestConnectionHandlerInitialization:
    """Test ConnectionHandler setup and initialization."""
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_init_creates_ssl_context(self, mock_ssl_context, cert_files):
        """Test that initialization creates SSL context."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        
        handler = ConnectionHandler(19999, cert_file, key_file)
        
        assert handler.port == 19999
        assert handler.certfile == cert_file
        assert handler.keyfile == key_file
        assert handler.socket is None
        assert handler.ssl_context is not None
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_ssl_context_configuration(self, mock_ssl_class, cert_files):
        """Test that SSL context is configured for TLS."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        mock_ssl_instance = MagicMock()
        mock_ssl_class.return_value = mock_ssl_instance
        
        handler = ConnectionHandler(19999, cert_file, key_file)
        
        # Verify SSLContext was created
        mock_ssl_class.assert_called_once()
        # Verify certificate chain was loaded
        mock_ssl_instance.load_cert_chain.assert_called_once_with(cert_file, key_file)


class TestClientConnection:
    """Test client-side connection (connect to master)."""
    
    @patch("src.network.connection.socket.socket")
    @patch("src.network.connection.ssl.SSLContext")
    def test_connect_success(self, mock_ssl_class, mock_socket_class, cert_files):
        """Test successful client connection."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        mock_socket_instance = MagicMock()
        mock_socket_class.return_value = mock_socket_instance
        
        mock_ssl_context = MagicMock()
        mock_ssl_instance = MagicMock()
        mock_ssl_context.wrap_socket.return_value = mock_ssl_instance
        mock_ssl_class.return_value = mock_ssl_context
        
        handler = ConnectionHandler(19999, cert_file, key_file)
        result = handler.connect("192.168.1.1", 19999)
        
        assert result == True
        mock_socket_instance.settimeout.assert_called_with(30)
        mock_socket_instance.close = MagicMock()  # Clean up
    
    @patch("src.network.connection.socket.socket")
    @patch("src.network.connection.ssl.SSLContext")
    def test_connect_timeout(self, mock_ssl_class, mock_socket_class, cert_files):
        """Test connection timeout."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        mock_socket_instance = MagicMock()
        mock_socket_class.return_value = mock_socket_instance
        
        mock_ssl_context = MagicMock()
        mock_ssl_instance = MagicMock()
        mock_ssl_instance.connect.side_effect = socket.timeout("timeout")
        mock_ssl_context.wrap_socket.return_value = mock_ssl_instance
        mock_ssl_class.return_value = mock_ssl_context
        
        handler = ConnectionHandler(19999, cert_file, key_file)
        result = handler.connect("192.168.1.1", 19999, timeout=5)
        
        assert result == False
    
    @patch("src.network.connection.socket.socket")
    @patch("src.network.connection.ssl.SSLContext")
    def test_connect_tls_error(self, mock_ssl_class, mock_socket_class, cert_files):
        """Test TLS connection error."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        mock_socket_instance = MagicMock()
        mock_ssl_context = MagicMock()
        mock_ssl_instance = MagicMock()
        
        mock_ssl_context.wrap_socket.side_effect = ssl.SSLError("TLS error")
        mock_ssl_class.return_value = mock_ssl_context
        mock_socket_class.return_value = mock_socket_instance
        
        handler = ConnectionHandler(19999, cert_file, key_file)
        result = handler.connect("192.168.1.1", 19999)
        
        assert result == False


class TestServerConnection:
    """Test server-side connection (listen and accept)."""
    
    @patch("src.network.connection.socket.socket")
    @patch("src.network.connection.ssl.SSLContext")
    def test_listen_success(self, mock_ssl_class, mock_socket_class, cert_files):
        """Test successful listen setup."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        mock_socket_instance = MagicMock()
        mock_socket_class.return_value = mock_socket_instance
        
        handler = ConnectionHandler(19999, cert_file, key_file)
        result = handler.listen(backlog=5)
        
        assert result == True
        mock_socket_instance.bind.assert_called_with(("0.0.0.0", 19999))
        mock_socket_instance.listen.assert_called_with(5)
    
    @patch("src.network.connection.socket.socket")
    @patch("src.network.connection.ssl.SSLContext")
    def test_listen_bind_error(self, mock_ssl_class, mock_socket_class, cert_files):
        """Test listen when bind fails."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        mock_socket_instance = MagicMock()
        mock_socket_instance.bind.side_effect = OSError("Address already in use")
        mock_socket_class.return_value = mock_socket_instance
        
        handler = ConnectionHandler(19999, cert_file, key_file)
        result = handler.listen()
        
        assert result == False
    
    @patch("src.network.connection.socket.socket")
    @patch("src.network.connection.ssl.SSLContext")
    def test_accept_connection(self, mock_ssl_class, mock_socket_class, cert_files):
        """Test accepting client connection."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        
        # Setup server socket
        mock_server_socket = MagicMock()
        mock_client_socket = MagicMock()
        mock_server_socket.accept.return_value = (mock_client_socket, ("192.168.1.100", 50000))
        mock_socket_class.return_value = mock_server_socket
        
        # Setup SSL context
        mock_ssl_context = MagicMock()
        mock_wrapped_socket = MagicMock()
        mock_ssl_context.wrap_socket.return_value = mock_wrapped_socket
        mock_ssl_class.return_value = mock_ssl_context
        
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = mock_server_socket
        
        client_handler = handler.accept()
        
        assert client_handler is not None
        assert client_handler.socket == mock_wrapped_socket


class TestMessageSending:
    """Test message sending over encrypted channel."""
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_send_message_format(self, mock_ssl_class, cert_files):
        """Test message format with length prefix."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = MagicMock()
        
        result = handler.send_message("HELLO", {"device_id": "abc123"})
        
        assert result == True
        # Should call sendall twice: length prefix + message
        assert handler.socket.sendall.call_count == 2
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_send_message_json_serialization(self, mock_ssl_class, cert_files):
        """Test that message is properly JSON serialized."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = MagicMock()
        
        result = handler.send_message("TEST_MSG", {"key": "value"})
        
        assert result == True
        # Get the actual message bytes sent
        calls = handler.socket.sendall.call_args_list
        assert len(calls) >= 2
        
        # Second call should be the JSON message
        message_bytes = calls[1][0][0]
        message_dict = json.loads(message_bytes.decode('utf-8'))
        
        assert message_dict["msg_type"] == "TEST_MSG"
        assert message_dict["data"]["key"] == "value"
        assert "timestamp" in message_dict
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_send_message_socket_error(self, mock_ssl_class, cert_files):
        """Test send error handling."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = MagicMock()
        handler.socket.sendall.side_effect = OSError("Connection broken")
        
        result = handler.send_message("HELLO", {})
        
        assert result == False


class TestMessageReceiving:
    """Test message receiving over encrypted channel."""
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_receive_message_format(self, mock_ssl_class, cert_files):
        """Test message reception and parsing."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = MagicMock()
        
        # Prepare message
        msg_dict = {
            "msg_type": "HELLO",
            "data": {"device_id": "xyz789"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        msg_json = json.dumps(msg_dict)
        msg_bytes = msg_json.encode('utf-8')
        
        # Mock socket to return length prefix + message
        length = len(msg_bytes)
        handler.socket.recv.side_effect = [
            length.to_bytes(4, 'big'),
            msg_bytes
        ]
        
        result = handler.receive_message(timeout=30)
        
        assert result is not None
        assert result["msg_type"] == "HELLO"
        assert result["data"]["device_id"] == "xyz789"
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_receive_message_timeout(self, mock_ssl_class, cert_files):
        """Test receive timeout handling."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = MagicMock()
        handler.socket.recv.side_effect = socket.timeout("timeout")
        
        result = handler.receive_message(timeout=5)
        
        assert result is None
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_receive_message_json_error(self, mock_ssl_class, cert_files):
        """Test handling of malformed JSON."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = MagicMock()
        
        # Mock socket to return length + invalid JSON
        invalid_json = b"not json at all"
        length = len(invalid_json)
        handler.socket.recv.side_effect = [
            length.to_bytes(4, 'big'),
            invalid_json
        ]
        
        result = handler.receive_message()
        
        assert result is None
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_receive_message_connection_closed(self, mock_ssl_class, cert_files):
        """Test handling of closed connection."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = MagicMock()
        handler.socket.recv.return_value = b""  # Empty means closed
        
        result = handler.receive_message()
        
        assert result is None


class TestConnectionClose:
    """Test connection closing and cleanup."""
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_close_connection(self, mock_ssl_class, cert_files):
        """Test closing connection."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = MagicMock()
        
        handler.close()
        
        handler.socket.close.assert_called_once()
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_close_no_socket(self, mock_ssl_class, cert_files):
        """Test closing when socket is None."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = None
        
        # Should not raise
        handler.close()
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_close_socket_error(self, mock_ssl_class, cert_files):
        """Test handling socket close error."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = MagicMock()
        handler.socket.close.side_effect = OSError("Already closed")
        
        # Should handle gracefully
        handler.close()


class TestLengthPrefixProtocol:
    """Test length-prefix message protocol."""
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_length_prefix_encoding(self, mock_ssl_class, cert_files):
        """Test length prefix is big-endian."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = MagicMock()
        
        # Send a message
        handler.send_message("TEST", {})
        
        # First call should be length prefix
        length_call = handler.socket.sendall.call_args_list[0]
        length_bytes = length_call[0][0]
        
        # Should be 4 bytes
        assert len(length_bytes) == 4
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_multiple_messages(self, mock_ssl_class, cert_files):
        """Test sending multiple messages."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = MagicMock()
        
        # Send multiple messages
        result1 = handler.send_message("MSG1", {"seq": 1})
        result2 = handler.send_message("MSG2", {"seq": 2})
        result3 = handler.send_message("MSG3", {"seq": 3})
        
        assert result1 == True
        assert result2 == True
        assert result3 == True
        
        # Should have 6 sendall calls (2 per message)
        assert handler.socket.sendall.call_count == 6


class TestMessageTypes:
    """Test different message types."""
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_hello_message(self, mock_ssl_class, cert_files):
        """Test HELLO message type."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = MagicMock()
        
        result = handler.send_message("HELLO", {
            "device_id": "dev1",
            "version": "1.0.0"
        })
        
        assert result == True
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_input_event_message(self, mock_ssl_class, cert_files):
        """Test input event message type."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = MagicMock()
        
        result = handler.send_message("INPUT_EVENT", {
            "event_type": "KEY_PRESS",
            "keycode": "A",
            "timestamp": "2026-02-09T12:00:00Z"
        })
        
        assert result == True
    
    @patch("src.network.connection.ssl.SSLContext")
    def test_custom_message_type(self, mock_ssl_class, cert_files):
        """Test custom message types."""
        from src.network.connection import ConnectionHandler
        
        cert_file, key_file = cert_files
        handler = ConnectionHandler(19999, cert_file, key_file)
        handler.socket = MagicMock()
        
        result = handler.send_message("CUSTOM_TYPE", {
            "custom_field": "custom_value"
        })
        
        assert result == True
