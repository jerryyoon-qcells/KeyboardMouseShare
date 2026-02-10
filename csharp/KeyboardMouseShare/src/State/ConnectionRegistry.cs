using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using KeyboardMouseShare.Models;

namespace KeyboardMouseShare.State
{
    /// <summary>
    /// Manages active connections between devices
    /// Tracks connection state and enables communication
    /// </summary>
    public interface IConnectionRegistry
    {
        /// <summary>Register a new active connection</summary>
        Task<bool> RegisterConnectionAsync(Connection connection, CancellationToken cancellationToken = default);
        
        /// <summary>Get connection by device ID</summary>
        Task<Connection?> GetConnectionAsync(string deviceId, CancellationToken cancellationToken = default);
        
        /// <summary>Get all active connections</summary>
        Task<List<Connection>> GetAllConnectionsAsync(CancellationToken cancellationToken = default);
        
        /// <summary>Remove a connection</summary>
        Task<bool> RemoveConnectionAsync(string deviceId, CancellationToken cancellationToken = default);
        
        /// <summary>Check if device has active connection</summary>
        Task<bool> IsConnectedAsync(string deviceId, CancellationToken cancellationToken = default);
        
        /// <summary>Update connection last activity time</summary>
        Task<bool> TouchConnectionAsync(string deviceId, CancellationToken cancellationToken = default);
        
        /// <summary>Get connections that have timed out (no activity)</summary>
        Task<List<Connection>> GetTimedOutConnectionsAsync(TimeSpan timeout, CancellationToken cancellationToken = default);
        
        /// <summary>Clear all connections</summary>
        Task<bool> ClearAllAsync(CancellationToken cancellationToken = default);
    }

    /// <summary>
    /// In-memory connection registry
    /// </summary>
    public class ConnectionRegistry : IConnectionRegistry
    {
        private readonly ConcurrentDictionary<string, Connection> _connections;
        private readonly ILogger<ConnectionRegistry> _logger;

        public ConnectionRegistry(ILogger<ConnectionRegistry> logger)
        {
            _logger = logger;
            _connections = new ConcurrentDictionary<string, Connection>();
        }

        /// <summary>Register new connection</summary>
        public async Task<bool> RegisterConnectionAsync(
            Connection connection,
            CancellationToken cancellationToken = default)
        {
            if (connection?.DeviceId == null)
            {
                _logger.LogWarning("Cannot register connection with null device ID");
                return false;
            }

            try
            {
                connection.ConnectedAt = DateTime.UtcNow;
                connection.LastActivity = DateTime.UtcNow;

                var added = _connections.TryAdd(connection.DeviceId, connection);

                if (added)
                {
                    _logger.LogInformation("Connection registered: {DeviceId} ({RemoteAddress})",
                        connection.DeviceId, connection.RemoteAddress);
                }
                else
                {
                    _logger.LogWarning("Connection already exists for device: {DeviceId}",
                        connection.DeviceId);
                }

                return added;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to register connection for {DeviceId}",
                    connection?.DeviceId);
                return false;
            }
        }

        /// <summary>Get connection by device ID</summary>
        public async Task<Connection?> GetConnectionAsync(
            string deviceId,
            CancellationToken cancellationToken = default)
        {
            if (string.IsNullOrEmpty(deviceId))
                return null;

            _connections.TryGetValue(deviceId, out var connection);
            return connection;
        }

        /// <summary>Get all active connections</summary>
        public async Task<List<Connection>> GetAllConnectionsAsync(CancellationToken cancellationToken = default)
        {
            return _connections.Values.ToList();
        }

        /// <summary>Remove connection</summary>
        public async Task<bool> RemoveConnectionAsync(
            string deviceId,
            CancellationToken cancellationToken = default)
        {
            if (string.IsNullOrEmpty(deviceId))
                return false;

            try
            {
                var removed = _connections.TryRemove(deviceId, out var connection);

                if (removed)
                {
                    _logger.LogInformation("Connection removed: {DeviceId}", deviceId);
                }
                else
                {
                    _logger.LogDebug("No connection found to remove: {DeviceId}", deviceId);
                }

                return removed;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to remove connection for {DeviceId}", deviceId);
                return false;
            }
        }

        /// <summary>Check if device is connected</summary>
        public async Task<bool> IsConnectedAsync(string deviceId, CancellationToken cancellationToken = default)
        {
            if (string.IsNullOrEmpty(deviceId))
                return false;

            return _connections.ContainsKey(deviceId);
        }

        /// <summary>Update last activity time for connection</summary>
        public async Task<bool> TouchConnectionAsync(string deviceId, CancellationToken cancellationToken = default)
        {
            if (string.IsNullOrEmpty(deviceId))
                return false;

            if (!_connections.TryGetValue(deviceId, out var connection))
            {
                _logger.LogDebug("Cannot touch connection: device not found {DeviceId}", deviceId);
                return false;
            }

            try
            {
                connection.LastActivity = DateTime.UtcNow;
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to touch connection for {DeviceId}", deviceId);
                return false;
            }
        }

        /// <summary>Get connections that have timed out</summary>
        public async Task<List<Connection>> GetTimedOutConnectionsAsync(
            TimeSpan timeout,
            CancellationToken cancellationToken = default)
        {
            var cutoffTime = DateTime.UtcNow - timeout;

            return _connections.Values
                .Where(c => c.LastActivity < cutoffTime)
                .ToList();
        }

        /// <summary>Clear all connections</summary>
        public async Task<bool> ClearAllAsync(CancellationToken cancellationToken = default)
        {
            try
            {
                var count = _connections.Count;
                _connections.Clear();
                
                _logger.LogInformation("Cleared {Count} connections", count);
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to clear connections");
                return false;
            }
        }
    }
}
