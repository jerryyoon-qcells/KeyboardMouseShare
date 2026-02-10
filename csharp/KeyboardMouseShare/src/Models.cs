using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace KeyboardMouseShare.Models
{
    /// <summary>
    /// Represents types of input events that can be transmitted between devices
    /// </summary>
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum InputEventType
    {
        /// <summary>Keyboard key press event</summary>
        KEY_PRESS,
        
        /// <summary>Keyboard key release event</summary>
        KEY_RELEASE,
        
        /// <summary>Mouse movement event</summary>
        MOUSE_MOVE,
        
        /// <summary>Mouse button click event</summary>
        MOUSE_CLICK,
        
        /// <summary>Mouse scroll event</summary>
        MOUSE_SCROLL
    }

    /// <summary>
    /// Represents a device in the network (master or client)
    /// </summary>
    public class Device
    {
        /// <summary>Unique identifier for the device</summary>
        [JsonPropertyName("id")]
        public string Id { get; set; } = Guid.NewGuid().ToString();

        /// <summary>User-friendly name of the device</summary>
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        /// <summary>Role of device: master (source) or client (target)</summary>
        [JsonPropertyName("role")]
        public DeviceRole Role { get; set; } = DeviceRole.Unassigned;

        /// <summary>Operating system: Windows or macOS</summary>
        [JsonPropertyName("os")]
        public string OperatingSystem { get; set; } = string.Empty;

        /// <summary>IP address of the device</summary>
        [JsonPropertyName("ip_address")]
        public string IpAddress { get; set; } = string.Empty;

        /// <summary>Port number for communication</summary>
        [JsonPropertyName("port")]
        public int Port { get; set; } = 12345;

        /// <summary>Hostname of the device</summary>
        [JsonPropertyName("hostname")]
        public string Hostname { get; set; } = string.Empty;

        /// <summary>Timestamp when device was last seen</summary>
        [JsonPropertyName("last_seen")]
        public DateTime LastSeen { get; set; } = DateTime.UtcNow;

        /// <summary>Whether device is currently active</summary>
        [JsonPropertyName("is_active")]
        public bool IsActive { get; set; } = true;

        /// <summary>Application version</summary>
        [JsonPropertyName("app_version")]
        public string AppVersion { get; set; } = "1.0.0";

        public Device() { }

        public Device(string name, DeviceRole role)
        {
            Name = name;
            Role = role;
            OperatingSystem = "Windows";
        }

        public override string ToString()
        {
            return $"Device(id='{Id}', name='{Name}', role={Role}, os='{OperatingSystem}', is_active={IsActive})";
        }

        public override bool Equals(object? obj)
        {
            return obj is Device device && device.Id == Id;
        }

        public override int GetHashCode()
        {
            return Id.GetHashCode();
        }
    }

    /// <summary>
    /// Device roles in the keyboard/mouse sharing network
    /// </summary>
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum DeviceRole
    {
        /// <summary>Device role not yet determined</summary>
        Unassigned,
        
        /// <summary>Source device (controls keyboard/mouse)</summary>
        Master,
        
        /// <summary>Target device (receives input events)</summary>
        Client
    }

    /// <summary>
    /// Represents an input event (keyboard or mouse action)
    /// </summary>
    public class InputEvent
    {
        /// <summary>Unique identifier for this event</summary>
        [JsonPropertyName("id")]
        public string Id { get; set; } = Guid.NewGuid().ToString();

        /// <summary>Type of input event (KEY_PRESS, MOUSE_MOVE, etc.)</summary>
        [JsonPropertyName("event_type")]
        public InputEventType EventType { get; set; }

        /// <summary>ID of device where event originated</summary>
        [JsonPropertyName("source_device_id")]
        public string SourceDeviceId { get; set; } = string.Empty;

        /// <summary>ID of target device for this event</summary>
        [JsonPropertyName("target_device_id")]
        public string TargetDeviceId { get; set; } = string.Empty;

        /// <summary>Event-specific data (keycode, coordinates, etc.)</summary>
        [JsonPropertyName("payload")]
        public Dictionary<string, object> Payload { get; set; } = new();

        /// <summary>Timestamp when event was created</summary>
        [JsonPropertyName("timestamp")]
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;

        /// <summary>Sequence number for ordering events</summary>
        [JsonPropertyName("sequence")]
        public long Sequence { get; set; } = 0;

        public InputEvent() { }

        public InputEvent(InputEventType eventType, string sourceDeviceId, string targetDeviceId)
        {
            EventType = eventType;
            SourceDeviceId = sourceDeviceId;
            TargetDeviceId = targetDeviceId;
        }

        /// <summary>
        /// Validate the event payload structure and content
        /// </summary>
        /// <returns>True if valid, false otherwise</returns>
        public bool IsValid()
        {
            return EventType switch
            {
                InputEventType.KEY_PRESS or InputEventType.KEY_RELEASE =>
                    Payload.ContainsKey("keycode") && Payload["keycode"] is string,
                    
                InputEventType.MOUSE_MOVE =>
                    Payload.ContainsKey("x") && Payload.ContainsKey("y"),
                    
                InputEventType.MOUSE_CLICK =>
                    Payload.ContainsKey("button") && Payload.ContainsKey("clicks"),
                    
                InputEventType.MOUSE_SCROLL =>
                    Payload.ContainsKey("scroll_delta"),
                    
                _ => false
            };
        }

        public override string ToString()
        {
            return $"InputEvent(id='{Id}', type={EventType}, source='{SourceDeviceId}', target='{TargetDeviceId}')";
        }
    }

    /// <summary>
    /// Represents a connection between two devices
    /// </summary>
    public class Connection
    {
        /// <summary>Unique identifier for this connection</summary>
        [JsonPropertyName("id")]
        public string Id { get; set; } = Guid.NewGuid().ToString();

        /// <summary>Remote device ID (for quick lookup)</summary>
        [JsonPropertyName("device_id")]
        public string? DeviceId { get; set; }

        /// <summary>Remote device address (IP:port)</summary>
        [JsonPropertyName("remote_address")]
        public string? RemoteAddress { get; set; }

        /// <summary>Local device</summary>
        [JsonPropertyName("local_device")]
        public Device? LocalDevice { get; set; }

        /// <summary>Remote device connected to</summary>
        [JsonPropertyName("remote_device")]
        public Device? RemoteDevice { get; set; }

        /// <summary>Connection status</summary>
        [JsonPropertyName("is_connected")]
        public bool IsConnected { get; set; } = false;

        /// <summary>TLS certificate for secure communication</summary>
        [JsonPropertyName("certificate")]
        public string? Certificate { get; set; }

        /// <summary>Connection establishment timestamp</summary>
        [JsonPropertyName("connected_at")]
        public DateTime? ConnectedAt { get; set; }

        /// <summary>Last activity timestamp</summary>
        [JsonPropertyName("last_activity")]
        public DateTime LastActivity { get; set; } = DateTime.UtcNow;

        /// <summary>Connection error message if applicable</summary>
        [JsonPropertyName("error")]
        public string? Error { get; set; }

        public Connection() { }

        public Connection(Device localDevice, Device remoteDevice)
        {
            LocalDevice = localDevice;
            RemoteDevice = remoteDevice;
            DeviceId = remoteDevice?.Id;
            RemoteAddress = $"{remoteDevice?.IpAddress}:{remoteDevice?.Port}";
        }

        public override string ToString()
        {
            var remoteName = RemoteDevice?.Name ?? "unknown";
            return $"Connection(id='{Id}', remote='{remoteName}', is_connected={IsConnected})";
        }

        public override bool Equals(object? obj)
        {
            return obj is Connection connection && connection.Id == Id;
        }

        public override int GetHashCode()
        {
            return Id.GetHashCode();
        }
    }
}
