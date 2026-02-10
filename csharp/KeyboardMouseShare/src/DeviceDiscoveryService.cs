using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using KeyboardMouseShare.Models;

namespace KeyboardMouseShare.Services
{
    /// <summary>
    /// Service for discovering devices on the local network using mDNS
    /// </summary>
    public interface IDeviceDiscoveryService
    {
        /// <summary>Event fired when a device is discovered</summary>
        event EventHandler<DeviceDiscoveredEventArgs>? DeviceDiscovered;
        
        /// <summary>Event fired when a device is lost</summary>
        event EventHandler<DeviceLostEventArgs>? DeviceLost;

        /// <summary>Start discovering devices</summary>
        Task StartDiscoveryAsync();
        
        /// <summary>Stop discovering devices</summary>
        Task StopDiscoveryAsync();
        
        /// <summary>Get list of discovered devices</summary>
        IReadOnlyList<Device> GetDiscoveredDevices();
        
        /// <summary>Find device by ID</summary>
        Device? FindDevice(string deviceId);
    }

    /// <summary>
    /// Internal implementation of device discovery service
    /// </summary>
    public class DeviceDiscoveryService : IDeviceDiscoveryService
    {
        private readonly ILogger<DeviceDiscoveryService> _logger;
        private readonly List<Device> _discoveredDevices = new();
        private bool _isDiscovering = false;

        public event EventHandler<DeviceDiscoveredEventArgs>? DeviceDiscovered;
        public event EventHandler<DeviceLostEventArgs>? DeviceLost;

        public DeviceDiscoveryService(ILogger<DeviceDiscoveryService> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Start mDNS discovery
        /// </summary>
        public async Task StartDiscoveryAsync()
        {
            if (_isDiscovering)
                return;

            _logger.LogInformation("Starting device discovery");
            _isDiscovering = true;

            // TODO: Implement mDNS discovery using SharpZeroConf
            await Task.CompletedTask;
        }

        /// <summary>
        /// Stop discovery process
        /// </summary>
        public async Task StopDiscoveryAsync()
        {
            if (!_isDiscovering)
                return;

            _logger.LogInformation("Stopping device discovery");
            _isDiscovering = false;

            // TODO: Cleanup mDNS listeners
            await Task.CompletedTask;
        }

        /// <summary>
        /// Get all discovered devices
        /// </summary>
        public IReadOnlyList<Device> GetDiscoveredDevices()
        {
            return _discoveredDevices.AsReadOnly();
        }

        /// <summary>
        /// Find device by ID
        /// </summary>
        public Device? FindDevice(string deviceId)
        {
            return _discoveredDevices.FirstOrDefault(d => d.Id == deviceId);
        }

        /// <summary>
        /// Handle device discovered event
        /// </summary>
        protected virtual void OnDeviceDiscovered(Device device)
        {
            _logger.LogInformation("Device discovered: {DeviceName} ({DeviceId})", device.Name, device.Id);
            _discoveredDevices.Add(device);
            DeviceDiscovered?.Invoke(this, new DeviceDiscoveredEventArgs(device));
        }

        /// <summary>
        /// Handle device lost event
        /// </summary>
        protected virtual void OnDeviceLost(Device device)
        {
            _logger.LogInformation("Device lost: {DeviceName} ({DeviceId})", device.Name, device.Id);
            _discoveredDevices.Remove(device);
            DeviceLost?.Invoke(this, new DeviceLostEventArgs(device));
        }
    }

    /// <summary>Event args for device discovered</summary>
    public class DeviceDiscoveredEventArgs : EventArgs
    {
        public Device Device { get; }
        
        public DeviceDiscoveredEventArgs(Device device)
        {
            Device = device;
        }
    }

    /// <summary>Event args for device lost</summary>
    public class DeviceLostEventArgs : EventArgs
    {
        public Device Device { get; }
        
        public DeviceLostEventArgs(Device device)
        {
            Device = device;
        }
    }
}
