using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using KeyboardMouseShare.Models;

namespace KeyboardMouseShare.State
{
    /// <summary>
    /// Manages device role transitions and validates role constraints
    /// Ensures only one master device per network
    /// </summary>
    public interface IRoleStateMachine
    {
        /// <summary>Request to set a device as master (validates constraint)</summary>
        Task<RoleTransitionResult> RequestMasterRoleAsync(Device device);
        
        /// <summary>Request to set a device as client</summary>
        Task<RoleTransitionResult> RequestClientRoleAsync(Device device);
        
        /// <summary>Unset role (return to unassigned)</summary>
        Task<RoleTransitionResult> UnsetRoleAsync(Device device);
        
        /// <summary>Get current device role</summary>
        Task<DeviceRole> GetRoleAsync(string deviceId);
        
        /// <summary>Get all devices with master role</summary>
        Task<List<Device>> GetMasterDevicesAsync();
        
        /// <summary>Get all devices with client role</summary>
        Task<List<Device>> GetClientDevicesAsync();
        
        /// <summary>Check if a role change is valid</summary>
        Task<(bool IsValid, string? Reason)> ValidateRoleChangeAsync(Device device, DeviceRole newRole);
        
        /// <summary>Reset all roles (useful on startup)</summary>
        Task ResetAllRolesAsync();
    }

    /// <summary>
    /// Result of a role transition attempt
    /// </summary>
    public class RoleTransitionResult
    {
        /// <summary>Whether the transition was successful</summary>
        public bool Success { get; set; }
        
        /// <summary>The device that was transitioned</summary>
        public Device? Device { get; set; }
        
        /// <summary>Previous role before change</summary>
        public DeviceRole PreviousRole { get; set; }
        
        /// <summary>New role after change (or attempted role)</summary>
        public DeviceRole NewRole { get; set; }
        
        /// <summary>Error message if transition failed</summary>
        public string? Error { get; set; }
        
        /// <summary>Timestamp of the transition attempt</summary>
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    }

    /// <summary>
    /// Implements role state machine with constraints
    /// </summary>
    public class RoleStateMachine : IRoleStateMachine
    {
        private readonly IDeviceRegistry _deviceRegistry;
        private readonly ILogger<RoleStateMachine> _logger;
        private readonly object _lockObject = new object();

        // Track roles in memory for quick access (synced with registry)
        private Dictionary<string, DeviceRole> _deviceRoles;

        public RoleStateMachine(
            IDeviceRegistry deviceRegistry,
            ILogger<RoleStateMachine> logger)
        {
            _deviceRegistry = deviceRegistry;
            _logger = logger;
            _deviceRoles = new Dictionary<string, DeviceRole>();
        }

        /// <summary>
        /// Request to set device as master
        /// Only one master allowed per network
        /// </summary>
        public async Task<RoleTransitionResult> RequestMasterRoleAsync(Device device)
        {
            if (device == null)
                return FailedTransition(device, DeviceRole.Unassigned, DeviceRole.Master, "Device is null");

            lock (_lockObject)
            {
                var previousRole = GetRoleUnsafe(device.Id);

                // Check if another device is already master
                var existingMaster = _deviceRoles
                    .Where(kvp => kvp.Value == DeviceRole.Master && kvp.Key != device.Id)
                    .FirstOrDefault();

                if (existingMaster.Key != null)
                {
                    var errorMsg = $"Cannot set device as master: {existingMaster.Key} is already master on this network";
                    _logger.LogWarning(errorMsg);
                    return FailedTransition(device, previousRole, DeviceRole.Master, errorMsg);
                }

                // Transition is valid
                _deviceRoles[device.Id] = DeviceRole.Master;
                device.Role = DeviceRole.Master;

                _logger.LogInformation("Device {DeviceId} transitioned to Master role", device.Id);

                return SuccessfulTransition(device, previousRole, DeviceRole.Master);
            }
        }

        /// <summary>
        /// Request to set device as client
        /// Multiple clients allowed
        /// </summary>
        public async Task<RoleTransitionResult> RequestClientRoleAsync(Device device)
        {
            if (device == null)
                return FailedTransition(device, DeviceRole.Unassigned, DeviceRole.Client, "Device is null");

            lock (_lockObject)
            {
                var previousRole = GetRoleUnsafe(device.Id);

                _deviceRoles[device.Id] = DeviceRole.Client;
                device.Role = DeviceRole.Client;

                _logger.LogInformation("Device {DeviceId} transitioned to Client role", device.Id);

                return SuccessfulTransition(device, previousRole, DeviceRole.Client);
            }
        }

        /// <summary>
        /// Reset device to unassigned role
        /// </summary>
        public async Task<RoleTransitionResult> UnsetRoleAsync(Device device)
        {
            if (device == null)
                return FailedTransition(device, DeviceRole.Unassigned, DeviceRole.Unassigned, "Device is null");

            lock (_lockObject)
            {
                var previousRole = GetRoleUnsafe(device.Id);

                _deviceRoles[device.Id] = DeviceRole.Unassigned;
                device.Role = DeviceRole.Unassigned;

                _logger.LogInformation("Device {DeviceId} role unset (was {PreviousRole})", device.Id, previousRole);

                return SuccessfulTransition(device, previousRole, DeviceRole.Unassigned);
            }
        }

        /// <summary>
        /// Get role for a device
        /// </summary>
        public async Task<DeviceRole> GetRoleAsync(string deviceId)
        {
            if (string.IsNullOrEmpty(deviceId))
                return DeviceRole.Unassigned;

            lock (_lockObject)
            {
                return GetRoleUnsafe(deviceId);
            }
        }

        /// <summary>
        /// Get all master devices
        /// </summary>
        public async Task<List<Device>> GetMasterDevicesAsync()
        {
            var allDevices = await _deviceRegistry.GetAllDevicesAsync();
            
            lock (_lockObject)
            {
                return allDevices
                    .Where(d => GetRoleUnsafe(d.Id) == DeviceRole.Master)
                    .ToList();
            }
        }

        /// <summary>
        /// Get all client devices
        /// </summary>
        public async Task<List<Device>> GetClientDevicesAsync()
        {
            var allDevices = await _deviceRegistry.GetAllDevicesAsync();
            
            lock (_lockObject)
            {
                return allDevices
                    .Where(d => GetRoleUnsafe(d.Id) == DeviceRole.Client)
                    .ToList();
            }
        }

        /// <summary>
        /// Validate if a role change would be valid
        /// </summary>
        public async Task<(bool IsValid, string? Reason)> ValidateRoleChangeAsync(Device device, DeviceRole newRole)
        {
            if (device == null)
                return (false, "Device is null");

            if (newRole == DeviceRole.Master)
            {
                lock (_lockObject)
                {
                    var existingMaster = _deviceRoles
                        .Where(kvp => kvp.Value == DeviceRole.Master && kvp.Key != device.Id)
                        .FirstOrDefault();

                    if (existingMaster.Key != null)
                    {
                        return (false, $"Another device ({existingMaster.Key}) is already master");
                    }
                }
            }

            return (true, null);
        }

        /// <summary>
        /// Reset all device roles to unassigned
        /// Useful on application startup
        /// </summary>
        public async Task ResetAllRolesAsync()
        {
            lock (_lockObject)
            {
                _deviceRoles.Clear();
                _logger.LogInformation("All device roles reset to unassigned");
            }
        }

        /// <summary>
        /// Get role without locking (internal use only)
        /// </summary>
        private DeviceRole GetRoleUnsafe(string deviceId)
        {
            if (string.IsNullOrEmpty(deviceId))
                return DeviceRole.Unassigned;

            return _deviceRoles.TryGetValue(deviceId, out var role)
                ? role
                : DeviceRole.Unassigned;
        }

        /// <summary>
        /// Helper to create successful transition result
        /// </summary>
        private RoleTransitionResult SuccessfulTransition(
            Device device,
            DeviceRole previousRole,
            DeviceRole newRole)
        {
            return new RoleTransitionResult
            {
                Success = true,
                Device = device,
                PreviousRole = previousRole,
                NewRole = newRole,
                Error = null,
                Timestamp = DateTime.UtcNow
            };
        }

        /// <summary>
        /// Helper to create failed transition result
        /// </summary>
        private RoleTransitionResult FailedTransition(
            Device? device,
            DeviceRole previousRole,
            DeviceRole attemptedRole,
            string error)
        {
            return new RoleTransitionResult
            {
                Success = false,
                Device = device,
                PreviousRole = previousRole,
                NewRole = attemptedRole,
                Error = error,
                Timestamp = DateTime.UtcNow
            };
        }
    }

    /// <summary>
    /// Exception thrown when role validation fails
    /// </summary>
    public class RoleValidationException : Exception
    {
        public RoleValidationException(string message) : base(message) { }
    }
}
