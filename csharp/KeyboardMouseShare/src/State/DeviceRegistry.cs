using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using KeyboardMouseShare.Models;

namespace KeyboardMouseShare.State
{
    /// <summary>
    /// Persists and retrieves device information from storage
    /// Handles both in-memory cache and file-based persistence
    /// </summary>
    public interface IDeviceRegistry
    {
        /// <summary>Save or update a device in the registry</summary>
        Task<bool> SaveDeviceAsync(Device device, CancellationToken cancellationToken = default);
        
        /// <summary>Load a device by ID</summary>
        Task<Device?> GetDeviceAsync(string deviceId, CancellationToken cancellationToken = default);
        
        /// <summary>Load all known devices</summary>
        Task<List<Device>> GetAllDevicesAsync(CancellationToken cancellationToken = default);
        
        /// <summary>Delete a device from the registry</summary>
        Task<bool> DeleteDeviceAsync(string deviceId, CancellationToken cancellationToken = default);
        
        /// <summary>Clear all devices from the registry</summary>
        Task<bool> ClearAllAsync(CancellationToken cancellationToken = default);
        
        /// <summary>Check if a device exists</summary>
        Task<bool> DeviceExistsAsync(string deviceId, CancellationToken cancellationToken = default);
        
        /// <summary>Get count of registered devices</summary>
        Task<int> GetDeviceCountAsync(CancellationToken cancellationToken = default);
    }

    /// <summary>
    /// File-based device registry implementation
    /// Stores devices as JSON in AppData with in-memory caching
    /// </summary>
    public class FileDeviceRegistry : IDeviceRegistry
    {
        private readonly string _registryPath;
        private readonly ILogger<FileDeviceRegistry> _logger;
        private readonly SemaphoreSlim _fileLock;
        private Dictionary<string, Device> _cache;
        private bool _cacheLoaded;

        private static readonly JsonSerializerOptions JsonOptions = new()
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            WriteIndented = true,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
        };

        public FileDeviceRegistry(ILogger<FileDeviceRegistry> logger)
        {
            _logger = logger;
            _fileLock = new SemaphoreSlim(1, 1);
            _cache = new Dictionary<string, Device>();
            _cacheLoaded = false;

            var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            var appFolder = Path.Combine(appDataPath, "KeyboardMouseShare");
            Directory.CreateDirectory(appFolder);

            _registryPath = Path.Combine(appFolder, "devices.json");
            
            _logger.LogInformation("Device registry initialized at {Path}", _registryPath);
        }

        /// <summary>
        /// Load all devices from file into cache (lazy load on first access)
        /// </summary>
        private async Task LoadCacheAsync(CancellationToken cancellationToken = default)
        {
            if (_cacheLoaded)
                return;

            await _fileLock.WaitAsync(cancellationToken);
            try
            {
                if (_cacheLoaded)
                    return;

                if (!File.Exists(_registryPath))
                {
                    _logger.LogInformation("Registry file does not exist, starting with empty cache");
                    _cacheLoaded = true;
                    return;
                }

                try
                {
                    var json = await File.ReadAllTextAsync(_registryPath, cancellationToken);
                    var devices = JsonSerializer.Deserialize<List<Device>>(json, JsonOptions);

                    if (devices != null)
                    {
                        _cache = devices.ToDictionary(d => d.Id, d => d);
                        _logger.LogInformation("Loaded {Count} devices from registry", _cache.Count);
                    }
                }
                catch (JsonException ex)
                {
                    _logger.LogError(ex, "Failed to deserialize devices registry, starting fresh");
                    _cache.Clear();
                }

                _cacheLoaded = true;
            }
            finally
            {
                _fileLock.Release();
            }
        }

        /// <summary>
        /// Save cache to file
        /// </summary>
        private async Task SaveCacheAsync(CancellationToken cancellationToken = default)
        {
            await _fileLock.WaitAsync(cancellationToken);
            try
            {
                var devices = _cache.Values.ToList();
                var json = JsonSerializer.Serialize(devices, JsonOptions);
                
                var tempPath = _registryPath + ".tmp";
                await File.WriteAllTextAsync(tempPath, json, cancellationToken);
                
                // Atomic replace
                if (File.Exists(_registryPath))
                    File.Delete(_registryPath);
                File.Move(tempPath, _registryPath);

                _logger.LogDebug("Saved {Count} devices to registry", devices.Count);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to save registry to disk");
                throw;
            }
            finally
            {
                _fileLock.Release();
            }
        }

        /// <summary>
        /// Save or update device
        /// </summary>
        public async Task<bool> SaveDeviceAsync(Device device, CancellationToken cancellationToken = default)
        {
            if (device?.Id == null)
            {
                _logger.LogWarning("Cannot save device with null ID");
                return false;
            }

            await LoadCacheAsync(cancellationToken);

            _cache[device.Id] = device;
            device.LastSeen = DateTime.UtcNow;

            await SaveCacheAsync(cancellationToken);

            _logger.LogInformation("Device saved: {DeviceId} ({Name})", device.Id, device.Name);
            return true;
        }

        /// <summary>
        /// Get device by ID
        /// </summary>
        public async Task<Device?> GetDeviceAsync(string deviceId, CancellationToken cancellationToken = default)
        {
            if (string.IsNullOrEmpty(deviceId))
                return null;

            await LoadCacheAsync(cancellationToken);

            if (_cache.TryGetValue(deviceId, out var device))
            {
                _logger.LogDebug("Retrieved device: {DeviceId}", deviceId);
                return device;
            }

            _logger.LogDebug("Device not found: {DeviceId}", deviceId);
            return null;
        }

        /// <summary>
        /// Get all devices
        /// </summary>
        public async Task<List<Device>> GetAllDevicesAsync(CancellationToken cancellationToken = default)
        {
            await LoadCacheAsync(cancellationToken);
            return _cache.Values.ToList();
        }

        /// <summary>
        /// Delete device
        /// </summary>
        public async Task<bool> DeleteDeviceAsync(string deviceId, CancellationToken cancellationToken = default)
        {
            if (string.IsNullOrEmpty(deviceId))
                return false;

            await LoadCacheAsync(cancellationToken);

            if (!_cache.Remove(deviceId))
            {
                _logger.LogWarning("Device not found for deletion: {DeviceId}", deviceId);
                return false;
            }

            await SaveCacheAsync(cancellationToken);
            _logger.LogInformation("Device deleted: {DeviceId}", deviceId);
            return true;
        }

        /// <summary>
        /// Clear all devices
        /// </summary>
        public async Task<bool> ClearAllAsync(CancellationToken cancellationToken = default)
        {
            await LoadCacheAsync(cancellationToken);
            
            var count = _cache.Count;
            _cache.Clear();
            
            await SaveCacheAsync(cancellationToken);
            
            _logger.LogInformation("Cleared {Count} devices from registry", count);
            return true;
        }

        /// <summary>
        /// Check if device exists
        /// </summary>
        public async Task<bool> DeviceExistsAsync(string deviceId, CancellationToken cancellationToken = default)
        {
            if (string.IsNullOrEmpty(deviceId))
                return false;

            await LoadCacheAsync(cancellationToken);
            return _cache.ContainsKey(deviceId);
        }

        /// <summary>
        /// Get device count
        /// </summary>
        public async Task<int> GetDeviceCountAsync(CancellationToken cancellationToken = default)
        {
            await LoadCacheAsync(cancellationToken);
            return _cache.Count;
        }
    }

    /// <summary>
    /// In-memory device registry (useful for testing)
    /// </summary>
    public class MemoryDeviceRegistry : IDeviceRegistry
    {
        private readonly Dictionary<string, Device> _devices;
        private readonly ILogger<MemoryDeviceRegistry> _logger;

        public MemoryDeviceRegistry(ILogger<MemoryDeviceRegistry> logger)
        {
            _devices = new Dictionary<string, Device>();
            _logger = logger;
        }

        public Task<bool> SaveDeviceAsync(Device device, CancellationToken cancellationToken = default)
        {
            if (device?.Id == null)
                return Task.FromResult(false);

            device.LastSeen = DateTime.UtcNow;
            _devices[device.Id] = device;
            _logger.LogInformation("Device saved in memory: {DeviceId}", device.Id);
            return Task.FromResult(true);
        }

        public Task<Device?> GetDeviceAsync(string deviceId, CancellationToken cancellationToken = default)
        {
            _devices.TryGetValue(deviceId, out var device);
            return Task.FromResult(device);
        }

        public Task<List<Device>> GetAllDevicesAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult(_devices.Values.ToList());
        }

        public Task<bool> DeleteDeviceAsync(string deviceId, CancellationToken cancellationToken = default)
        {
            var result = _devices.Remove(deviceId);
            if (result)
                _logger.LogInformation("Device deleted from memory: {DeviceId}", deviceId);
            return Task.FromResult(result);
        }

        public Task<bool> ClearAllAsync(CancellationToken cancellationToken = default)
        {
            _devices.Clear();
            _logger.LogInformation("All devices cleared from memory");
            return Task.FromResult(true);
        }

        public Task<bool> DeviceExistsAsync(string deviceId, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(_devices.ContainsKey(deviceId));
        }

        public Task<int> GetDeviceCountAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult(_devices.Count);
        }
    }
}
