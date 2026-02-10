using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using KeyboardMouseShare.Models;

namespace KeyboardMouseShare.Services
{
    /// <summary>
    /// Service for managing connections between devices
    /// </summary>
    public interface IConnectionService
    {
        /// <summary>Event fired when connection established</summary>
        event EventHandler<ConnectionEstablishedEventArgs>? ConnectionEstablished;
        
        /// <summary>Event fired when connection closed</summary>
        event EventHandler<ConnectionClosedEventArgs>? ConnectionClosed;

        /// <summary>Establish connection to remote device</summary>
        Task<Connection?> ConnectAsync(Device remoteDevice, Device localDevice);
        
        /// <summary>Close connection to device</summary>
        Task DisconnectAsync(string deviceId);
        
        /// <summary>Get connection status</summary>
        Connection? GetConnection(string deviceId);
        
        /// <summary>Get all active connections</summary>
        IReadOnlyList<Connection> GetAllConnections();
    }

    /// <summary>
    /// Implementation of connection service
    /// </summary>
    public class ConnectionService : IConnectionService
    {
        private readonly ILogger<ConnectionService> _logger;
        private readonly Dictionary<string, Connection> _connections = new();
        private readonly SemaphoreSlim _connectionLock = new(1, 1);

        public event EventHandler<ConnectionEstablishedEventArgs>? ConnectionEstablished;
        public event EventHandler<ConnectionClosedEventArgs>? ConnectionClosed;

        public ConnectionService(ILogger<ConnectionService> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Establish connection to remote device
        /// </summary>
        public async Task<Connection?> ConnectAsync(Device remoteDevice, Device localDevice)
        {
            await _connectionLock.WaitAsync();
            try
            {
                if (_connections.ContainsKey(remoteDevice.Id))
                {
                    _logger.LogWarning("Connection to device {DeviceId} already exists", remoteDevice.Id);
                    return _connections[remoteDevice.Id];
                }

                _logger.LogInformation("Connecting to device: {DeviceName} ({DeviceId})", 
                    remoteDevice.Name, remoteDevice.Id);

                var connection = new Connection(localDevice, remoteDevice)
                {
                    IsConnected = true,
                    ConnectedAt = DateTime.UtcNow
                };

                // TODO: Establish actual network connection
                // TODO: Setup TLS/SSL encryption
                // TODO: Verify device identity

                _connections[remoteDevice.Id] = connection;
                
                _logger.LogInformation("Successfully connected to device: {DeviceName}", remoteDevice.Name);
                ConnectionEstablished?.Invoke(this, new ConnectionEstablishedEventArgs(connection));

                return connection;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to connect to device {DeviceName}", remoteDevice.Name);
                return null;
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        /// <summary>
        /// Close connection to device
        /// </summary>
        public async Task DisconnectAsync(string deviceId)
        {
            await _connectionLock.WaitAsync();
            try
            {
                if (_connections.TryGetValue(deviceId, out var connection))
                {
                    _logger.LogInformation("Disconnecting from device: {DeviceId}", deviceId);
                    
                    connection.IsConnected = false;
                    _connections.Remove(deviceId);

                    ConnectionClosed?.Invoke(this, new ConnectionClosedEventArgs(connection));
                }
            }
            finally
            {
                _connectionLock.Release();
            }
        }

        /// <summary>
        /// Get connection to device
        /// </summary>
        public Connection? GetConnection(string deviceId)
        {
            return _connections.TryGetValue(deviceId, out var connection) ? connection : null;
        }

        /// <summary>
        /// Get all active connections
        /// </summary>
        public IReadOnlyList<Connection> GetAllConnections()
        {
            return _connections.Values.Where(c => c.IsConnected).ToList().AsReadOnly();
        }
    }

    /// <summary>Event args for connection established</summary>
    public class ConnectionEstablishedEventArgs : EventArgs
    {
        public Connection Connection { get; }
        
        public ConnectionEstablishedEventArgs(Connection connection)
        {
            Connection = connection;
        }
    }

    /// <summary>Event args for connection closed</summary>
    public class ConnectionClosedEventArgs : EventArgs
    {
        public Connection Connection { get; }
        
        public ConnectionClosedEventArgs(Connection connection)
        {
            Connection = connection;
        }
    }
}
