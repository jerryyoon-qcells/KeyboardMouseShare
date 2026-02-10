using System;
using System.Linq;
using System.Net.Sockets;
using System.Net.Security;
using System.Security.Cryptography.X509Certificates;
using System.Threading.Tasks;
using System.Text;
using System.Threading;
using Microsoft.Extensions.Logging;

namespace KeyboardMouseShare.Network
{
    /// <summary>
    /// Manages TLS encrypted connections between devices
    /// Handles certificate validation and secure communication
    /// </summary>
    public interface ITLSConnection
    {
        /// <summary>Connect to remote device with TLS encryption</summary>
        Task<bool> ConnectAsync(string hostname, int port, CancellationToken cancellationToken = default);
        
        /// <summary>Send encrypted message to connected device</summary>
        Task<bool> SendAsync(string message, CancellationToken cancellationToken = default);
        
        /// <summary>Receive encrypted message from connected device</summary>
        Task<string?> ReceiveAsync(CancellationToken cancellationToken = default);
        
        /// <summary>Close the connection gracefully</summary>
        Task DisconnectAsync();
        
        /// <summary>Check if connection is active</summary>
        bool IsConnected { get; }
        
        /// <summary>Get connected to hostname</summary>
        string? RemoteHost { get; }
    }

    /// <summary>
    /// Implementation of TLS connection using .NET SslStream
    /// </summary>
    public class TLSConnection : ITLSConnection, IDisposable
    {
        private TcpClient? _tcpClient;
        private SslStream? _sslStream;
        private readonly ILogger<TLSConnection> _logger;
        private bool _disposed = false;
        private readonly byte[] _buffer = new byte[65536]; // 64KB buffer

        public bool IsConnected => _sslStream?.CanRead ?? false;
        public string? RemoteHost { get; private set; }

        public TLSConnection(ILogger<TLSConnection> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Connect to remote device with TLS
        /// </summary>
        public async Task<bool> ConnectAsync(
            string hostname,
            int port,
            CancellationToken cancellationToken = default)
        {
            try
            {
                if (IsConnected)
                {
                    _logger.LogWarning("Already connected to {Host}", RemoteHost);
                    return false;
                }

                _logger.LogInformation("Initiating TLS connection to {Hostname}:{Port}", hostname, port);

                // Create TCP connection
                _tcpClient = new TcpClient();
                await _tcpClient.ConnectAsync(hostname, port, cancellationToken);

                _logger.LogDebug("TCP connection established to {Hostname}:{Port}", hostname, port);

                // Upgrade to TLS
                _sslStream = new SslStream(
                    _tcpClient.GetStream(),
                    leaveInnerStreamOpen: false,
                    (sender, cert, chain, errors) => ValidateServerCertificate(sender, cert, chain, errors));

                await _sslStream.AuthenticateAsClientAsync(
                    new SslClientAuthenticationOptions
                    {
                        TargetHost = hostname,
                        ClientCertificates = new X509CertificateCollection(),
                        EncryptionPolicy = EncryptionPolicy.RequireEncryption,
                        EnabledSslProtocols = System.Security.Authentication.SslProtocols.Tls13
                    },
                    cancellationToken);

                RemoteHost = hostname;

                _logger.LogInformation("TLS connection established to {Hostname}:{Port}", hostname, port);
                _logger.LogDebug("TLS Protocol: {Protocol}, Cipher: {Cipher}",
                    _sslStream.SslProtocol,
                    _sslStream.CipherAlgorithm);

                return true;
            }
            catch (OperationCanceledException)
            {
                _logger.LogWarning("TLS connection to {Hostname} was cancelled", hostname);
                await DisconnectAsync();
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to establish TLS connection to {Hostname}:{Port}", hostname, port);
                await DisconnectAsync();
                return false;
            }
        }

        /// <summary>
        /// Send message through encrypted connection
        /// </summary>
        public async Task<bool> SendAsync(string message, CancellationToken cancellationToken = default)
        {
            if (!IsConnected)
            {
                _logger.LogWarning("Cannot send: not connected");
                return false;
            }

            try
            {
                if (string.IsNullOrEmpty(message))
                {
                    _logger.LogWarning("Cannot send empty message");
                    return false;
                }

                var messageBytes = Encoding.UTF8.GetBytes(message);
                var lengthBytes = BitConverter.GetBytes(messageBytes.Length);

                // Send message length first (4 bytes, big-endian)
                await _sslStream!.WriteAsync(lengthBytes, 0, 4, cancellationToken);

                // Send message bytes
                await _sslStream.WriteAsync(messageBytes, 0, messageBytes.Length, cancellationToken);

                // Flush to ensure delivery
                await _sslStream.FlushAsync(cancellationToken);

                _logger.LogDebug("Sent {ByteCount} bytes to {Host}", messageBytes.Length, RemoteHost);
                return true;
            }
            catch (OperationCanceledException)
            {
                _logger.LogWarning("Send operation to {Host} was cancelled", RemoteHost);
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to send message to {Host}", RemoteHost);
                await DisconnectAsync();
                return false;
            }
        }

        /// <summary>
        /// Receive message from encrypted connection
        /// </summary>
        public async Task<string?> ReceiveAsync(CancellationToken cancellationToken = default)
        {
            if (!IsConnected)
            {
                _logger.LogWarning("Cannot receive: not connected");
                return null;
            }

            try
            {
                // Read message length (4 bytes)
                var lengthBuffer = new byte[4];
                var bytesRead = await _sslStream!.ReadAsync(lengthBuffer, 0, 4, cancellationToken);

                if (bytesRead == 0)
                {
                    _logger.LogInformation("Connection closed by {Host}", RemoteHost);
                    await DisconnectAsync();
                    return null;
                }

                if (bytesRead < 4)
                {
                    _logger.LogWarning("Invalid message length header from {Host}", RemoteHost);
                    await DisconnectAsync();
                    return null;
                }

                var messageLength = BitConverter.ToInt32(lengthBuffer, 0);

                // Validate message length (max 1MB)
                if (messageLength <= 0 || messageLength > 1048576)
                {
                    _logger.LogWarning("Invalid message length {Length} from {Host}", messageLength, RemoteHost);
                    await DisconnectAsync();
                    return null;
                }

                // Read message bytes
                var messageBuffer = new byte[messageLength];
                bytesRead = 0;

                while (bytesRead < messageLength)
                {
                    var chunk = await _sslStream.ReadAsync(
                        messageBuffer,
                        bytesRead,
                        messageLength - bytesRead,
                        cancellationToken);

                    if (chunk == 0)
                    {
                        _logger.LogWarning("Connection closed while receiving from {Host}", RemoteHost);
                        await DisconnectAsync();
                        return null;
                    }

                    bytesRead += chunk;
                }

                var message = Encoding.UTF8.GetString(messageBuffer);
                _logger.LogDebug("Received {ByteCount} bytes from {Host}", messageLength, RemoteHost);
                return message;
            }
            catch (OperationCanceledException)
            {
                _logger.LogWarning("Receive operation from {Host} was cancelled", RemoteHost);
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to receive message from {Host}", RemoteHost);
                await DisconnectAsync();
                return null;
            }
        }

        /// <summary>
        /// Disconnect gracefully
        /// </summary>
        public async Task DisconnectAsync()
        {
            try
            {
                if (_sslStream != null)
                {
                    await _sslStream.ShutdownAsync();
                    _sslStream.Dispose();
                    _sslStream = null;
                }

                if (_tcpClient != null)
                {
                    _tcpClient.Close();
                    _tcpClient.Dispose();
                    _tcpClient = null;
                }

                _logger.LogInformation("Disconnected from {Host}", RemoteHost);
                RemoteHost = null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during disconnect");
            }
        }

        /// <summary>
        /// Validate server certificate (for now, accept self-signed)
        /// In production, would validate against pinned certificate
        /// </summary>
        private bool ValidateServerCertificate(
            object sender,
            X509Certificate? certificate,
            X509Chain? chain,
            SslPolicyErrors sslPolicyErrors)
        {
            // In production, implement proper certificate pinning/validation
            // For now, accept self-signed certs (suitable for local network)
            if (sslPolicyErrors == SslPolicyErrors.None)
            {
                _logger.LogDebug("Certificate validation successful");
                return true;
            }

            // Accept self-signed certificates for local network scenarios
            if (sslPolicyErrors == SslPolicyErrors.RemoteCertificateChainErrors)
            {
                var selfSigned = chain?.ChainStatus?.Any(status =>
                    status.Status == X509ChainStatusFlags.UntrustedRoot) ?? false;

                if (selfSigned && certificate != null)
                {
                    _logger.LogWarning("Accepting self-signed certificate from {Subject}",
                        certificate.Subject);
                    return true;
                }
            }

            _logger.LogError("Certificate validation failed: {Errors}", sslPolicyErrors);
            return false;
        }

        public void Dispose()
        {
            if (_disposed)
                return;

            _sslStream?.Dispose();
            _tcpClient?.Dispose();
            _disposed = true;
        }
    }

    /// <summary>
    /// Exception for TLS connection errors
    /// </summary>
    public class TLSException : Exception
    {
        public TLSException(string message) : base(message) { }
        public TLSException(string message, Exception innerException)
            : base(message, innerException) { }
    }
}
