"""TLS 1.3 connection handler for encrypted peer-to-peer communication."""

import socket
import ssl
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class ConnectionHandler:
    """
    Manages TLS 1.3 connections between devices.
    
    Responsibilities:
    1. Initiate client-side TLS connection (connect to master)
    2. Accept server-side TLS connection (master listens)
    3. Send/receive JSON messages over encrypted channel with length prefix
    4. Handle connection lifecycle (connect, listen, accept, close)
    """
    
    def __init__(self, port: int, certfile: str, keyfile: str):
        """
        Initialize connection handler.
        
        Args:
            port: Port to listen/connect on (default 19999)
            certfile: Path to TLS certificate (PEM format)
            keyfile: Path to TLS private key (PEM format)
        
        Raises:
            ssl.SSLError: If certificate/key cannot be loaded
        """
        self.port = port
        self.certfile = certfile
        self.keyfile = keyfile
        
        self.socket: Optional[socket.socket] = None
        self.ssl_context: Optional[ssl.SSLContext] = None
        
        # Initialize server SSL context by default
        self._setup_server_ssl_context()
    
    def _setup_server_ssl_context(self):
        """Create and configure TLS 1.3 server context."""
        try:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            self.ssl_context.load_cert_chain(self.certfile, self.keyfile)
            
            # For MVP: disable certificate validation (can be enabled in Phase 3)
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
            
            logger.debug("TLS 1.3 server context created successfully")
        except ssl.SSLError as e:
            logger.error(f"Failed to setup SSL context: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in SSL setup: {e}")
            raise
    
    def _setup_client_ssl_context(self):
        """Create and configure TLS 1.3 client context."""
        try:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            
            # For MVP: skip certificate verification (can be enabled in Phase 3)
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
            
            logger.debug("TLS 1.3 client context created successfully")
        except ssl.SSLError as e:
            logger.error(f"Failed to setup client SSL context: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in client SSL setup: {e}")
            raise
    
    def connect(self, host: str, port: int, timeout: int = 30) -> bool:
        """
        Client-side connection: initiate TLS connection to master device.
        
        Args:
            host: Master device IP address (IPv4 or IPv6)
            port: Master device port
            timeout: Connection timeout in seconds (default 30)
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to master at {host}:{port}")
            
            # Setup client SSL context
            self._setup_client_ssl_context()
            
            if self.ssl_context is None:
                logger.error("SSL context not initialized")
                return False
            
            try:
                # Create unencrypted socket first
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                
                # Connect TCP
                sock.connect((host, port))
                logger.debug(f"TCP connection established to {host}:{port}")
                
                # Wrap socket with SSL - use modern approach
                ssl_sock = self.ssl_context.wrap_socket(
                    sock,
                    server_hostname=host,
                    do_handshake_on_connect=True
                )
                
                self.socket = ssl_sock
                logger.info(f"Connected to master at {host}:{port} (TLS 1.3 established)")
                return True
            
            except (socket.timeout, ssl.SSLError, OSError) as e:
                logger.error(f"Connection/TLS error to {host}:{port}: {type(e).__name__}: {e}")
                sock.close()
                return False
        
        except socket.gaierror as e:
            logger.error(f"DNS resolution error for {host}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to {host}:{port}: {type(e).__name__}: {e}")
            return False
    
    def listen(self, backlog: int = 5) -> bool:
        """
        Server-side: listen for incoming TLS connections from clients.
        
        Args:
            backlog: Number of pending connections to queue (default 5)
        
        Returns:
            True if listening started successfully, False otherwise
        """
        try:
            logger.info(f"Listening for connections on port {self.port}")
            
            # Create TCP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to port
            sock.bind(("0.0.0.0", self.port))
            
            # Listen for connections
            sock.listen(backlog)
            self.socket = sock
            
            logger.info(f"Listening on port {self.port}")
            return True
        
        except OSError as e:
            logger.error(f"Failed to listen on port {self.port}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in listen: {e}")
            return False
    
    def accept(self) -> Optional["ConnectionHandler"]:
        """
        Accept incoming TLS connection from a client.
        
        Returns:
            New ConnectionHandler instance for the accepted connection, or None if error
        """
        client_socket = None
        try:
            if not self.socket:
                logger.error("Socket not initialized for accept")
                return None
            
            # Accept client connection
            client_socket, client_address = self.socket.accept()
            logger.info(f"Accepted TCP connection from {client_address}")
            
            if self.ssl_context is None:
                logger.error("SSL context not initialized for TLS wrap")
                client_socket.close()
                return None
            
            try:
                # Wrap with TLS - use do_handshake_on_connect=True for proper handshake
                ssl_socket = self.ssl_context.wrap_socket(
                    client_socket,
                    server_side=True,
                    do_handshake_on_connect=True
                )
                
                # Create new handler for this connection
                handler = ConnectionHandler(self.port, self.certfile, self.keyfile)
                handler.socket = ssl_socket
                
                logger.debug(f"TLS 1.3 handshake completed with {client_address}")
                return handler
            
            except ssl.SSLError as e:
                logger.error(f"TLS error during handshake with {client_address}: {type(e).__name__}: {e}")
                client_socket.close()
                return None
            except Exception as e:
                logger.error(f"Error during TLS wrap with {client_address}: {type(e).__name__}: {e}")
                client_socket.close()
                return None
        
        except socket.timeout:
            logger.error("Accept timeout")
            if client_socket:
                client_socket.close()
            return None
        except OSError as e:
            logger.error(f"OS error accepting connection: {type(e).__name__}: {e}")
            if client_socket:
                client_socket.close()
            return None
        except Exception as e:
            logger.error(f"Error accepting connection: {type(e).__name__}: {e}")
            if client_socket:
                client_socket.close()
            return None
    
    def send_message(self, msg_type: str, data: Dict[str, Any]) -> bool:
        """
        Send JSON message over encrypted channel with length prefix.
        
        Message format:
        {
            "msg_type": str,
            "data": {...},
            "timestamp": ISO datetime string
        }
        
        Protocol:
        [4 bytes: message length in big-endian][JSON message bytes]
        
        Args:
            msg_type: Message type identifier (e.g., "HELLO", "INPUT_EVENT")
            data: Message payload (dict, will be JSON serialized)
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if not self.socket:
                logger.error("Socket not connected")
                return False
            
            # Build message
            message = {
                "msg_type": msg_type,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Serialize to JSON
            json_str = json.dumps(message)
            json_bytes = json_str.encode('utf-8')
            
            # Send length prefix (4 bytes, big-endian)
            length = len(json_bytes)
            length_bytes = length.to_bytes(4, 'big')
            self.socket.sendall(length_bytes)
            
            # Send message
            self.socket.sendall(json_bytes)
            
            logger.debug(f"Sent {msg_type} message ({length} bytes)")
            return True
        
        except BrokenPipeError:
            logger.error("Connection broken when sending message")
            return False
        except OSError as e:
            logger.error(f"Socket error when sending message: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def receive_message(self, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Receive JSON message over encrypted channel.
        
        Expects message format:
        [4 bytes: message length in big-endian][JSON message bytes]
        
        Args:
            timeout: Receive timeout in seconds (default 30)
        
        Returns:
            Parsed JSON message dict, or None if error or timeout
        """
        try:
            if not self.socket:
                logger.error("Socket not connected")
                return None
            
            # Set timeout
            self.socket.settimeout(timeout)
            
            # Receive length prefix (4 bytes) - handle partial reads
            length_bytes = b""
            while len(length_bytes) < 4:
                chunk = self.socket.recv(4 - len(length_bytes))
                if not chunk:
                    logger.warning("Connection closed by peer (no length data)")
                    return None
                length_bytes += chunk
            
            # Parse length
            length = int.from_bytes(length_bytes, 'big')
            
            if length <= 0 or length > 1024 * 1024:  # Max 1MB
                logger.error(f"Invalid message length: {length}")
                return None
            
            # Receive message bytes - handle partial reads
            json_bytes = b""
            while len(json_bytes) < length:
                chunk = self.socket.recv(length - len(json_bytes))
                if not chunk:
                    logger.warning(f"Connection closed by peer (received {len(json_bytes)}/{length} bytes)")
                    return None
                json_bytes += chunk
            
            # Parse JSON
            json_str = json_bytes.decode('utf-8')
            message = json.loads(json_str)
            
            logger.debug(f"Received {message.get('msg_type')} message ({length} bytes)")
            return message
        
        except socket.timeout:
            logger.error(f"Receive timeout ({timeout}s)")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
        except UnicodeDecodeError as e:
            logger.error(f"UTF-8 decode error: {e}")
            return None
        except OSError as e:
            logger.error(f"Socket error receiving message: {e}")
            return None
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None
    
    def close(self):
        """Close connection and cleanup resources."""
        try:
            if self.socket:
                try:
                    # Try graceful shutdown first
                    self.socket.shutdown(socket.SHUT_RDWR)
                except (OSError, AttributeError):
                    # Socket might already be closed or not support shutdown
                    pass
                
                try:
                    self.socket.close()
                except OSError:
                    pass
                
                self.socket = None
                logger.info("Connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
