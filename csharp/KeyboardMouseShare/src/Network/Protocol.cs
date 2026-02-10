using System;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Collections.Generic;

namespace KeyboardMouseShare.Network
{
    /// <summary>
    /// Network protocol message types for device communication
    /// </summary>
    public enum MessageType
    {
        /// <summary>Initial handshake from connecting device</summary>
        HELLO = 0,
        
        /// <summary>Acknowledgment of successful connection</summary>
        ACK = 1,
        
        /// <summary>Input event (keyboard/mouse) being transmitted</summary>
        INPUT_EVENT = 2,
        
        /// <summary>Device role announcement (Master/Client)</summary>
        ROLE_ANNOUNCEMENT = 3,
        
        /// <summary>Keep-alive ping to detect offline devices</summary>
        PING = 4,
        
        /// <summary>Response to PING</summary>
        PONG = 5,
        
        /// <summary>Error message indicating protocol violation or failure</summary>
        ERROR = 6,
        
        /// <summary>Device disconnecting gracefully</summary>
        GOODBYE = 7,
        
        /// <summary>Authentication challenge for passphrase verification</summary>
        AUTH_CHALLENGE = 8,
        
        /// <summary>Authentication response with passphrase hash</summary>
        AUTH_RESPONSE = 9
    }

    /// <summary>
    /// Base class for all network protocol messages
    /// </summary>
    public class ProtocolMessage
    {
        /// <summary>Type of message being sent</summary>
        [JsonPropertyName("type")]
        public MessageType Type { get; set; }
        
        /// <summary>Unique message identifier for tracking and ACK</summary>
        [JsonPropertyName("id")]
        public string MessageId { get; set; } = Guid.NewGuid().ToString();
        
        /// <summary>Timestamp when message was created (UTC milliseconds)</summary>
        [JsonPropertyName("timestamp")]
        public long Timestamp { get; set; } = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        
        /// <summary>Version of protocol this message conforms to</summary>
        [JsonPropertyName("version")]
        public string ProtocolVersion { get; set; } = "1.0.0";
        
        /// <summary>Source device ID</summary>
        [JsonPropertyName("source")]
        public string? SourceDeviceId { get; set; }
        
        /// <summary>Destination device ID (null for broadcast)</summary>
        [JsonPropertyName("destination")]
        public string? DestinationDeviceId { get; set; }
        
        /// <summary>Message payload (varies by type)</summary>
        [JsonPropertyName("payload")]
        public Dictionary<string, object>? Payload { get; set; }
    }

    /// <summary>
    /// HELLO message - Sent when device first connects
    /// </summary>
    public class HelloMessage : ProtocolMessage
    {
        public HelloMessage()
        {
            Type = MessageType.HELLO;
        }
        
        /// <summary>Device name as shown to other devices</summary>
        [JsonPropertyName("device_name")]
        public string? DeviceName { get; set; }
        
        /// <summary>Application version</summary>
        [JsonPropertyName("app_version")]
        public string AppVersion { get; set; } = "1.0.0";
        
        /// <summary>Operating system (Windows/macOS)</summary>
        [JsonPropertyName("os_type")]
        public string? OsType { get; set; }
        
        /// <summary>Device unique identifier</summary>
        [JsonPropertyName("device_id")]
        public string? DeviceId { get; set; }
    }

    /// <summary>
    /// ACK message - Confirms receipt of another message
    /// </summary>
    public class AckMessage : ProtocolMessage
    {
        public AckMessage()
        {
            Type = MessageType.ACK;
        }
        
        /// <summary>Message ID being acknowledged</summary>
        [JsonPropertyName("ack_message_id")]
        public string? AckMessageId { get; set; }
        
        /// <summary>Status code (0=success, >0=error)</summary>
        [JsonPropertyName("status")]
        public int Status { get; set; } = 0;
    }

    /// <summary>
    /// ERROR message - Indicates protocol error or failure
    /// </summary>
    public class ErrorMessage : ProtocolMessage
    {
        public ErrorMessage()
        {
            Type = MessageType.ERROR;
        }
        
        /// <summary>Error code for classification</summary>
        [JsonPropertyName("error_code")]
        public int ErrorCode { get; set; }
        
        /// <summary>Human-readable error description</summary>
        [JsonPropertyName("error_message")]
        public string? ErrorDescription { get; set; }
        
        /// <summary>ID of message that caused error (if applicable)</summary>
        [JsonPropertyName("related_message_id")]
        public string? RelatedMessageId { get; set; }
    }

    /// <summary>
    /// Protocol handler for serialization and deserialization
    /// </summary>
    public class Protocol
    {
        private static readonly JsonSerializerOptions JsonOptions = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            WriteIndented = false,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
        };

        /// <summary>
        /// Serialize message object to JSON string
        /// </summary>
        public string SerializeMessage(ProtocolMessage message)
        {
            try
            {
                return JsonSerializer.Serialize(message, JsonOptions);
            }
            catch (JsonException ex)
            {
                throw new ProtocolException($"Failed to serialize message: {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Deserialize JSON string to ProtocolMessage
        /// </summary>
        public ProtocolMessage DeserializeMessage(string json)
        {
            try
            {
                var message = JsonSerializer.Deserialize<ProtocolMessage>(json, JsonOptions);
                if (message == null)
                    throw new ProtocolException("Deserialized message is null");
                
                return message;
            }
            catch (JsonException ex)
            {
                throw new ProtocolException($"Failed to deserialize message: {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Serialize generic object to JSON
        /// </summary>
        public string Serialize<T>(T obj)
        {
            try
            {
                return JsonSerializer.Serialize(obj, JsonOptions);
            }
            catch (JsonException ex)
            {
                throw new ProtocolException($"Failed to serialize object: {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Deserialize JSON to typed object
        /// </summary>
        public T Deserialize<T>(string json)
        {
            try
            {
                var obj = JsonSerializer.Deserialize<T>(json, JsonOptions);
                if (obj == null)
                    throw new ProtocolException("Deserialized object is null");
                
                return obj;
            }
            catch (JsonException ex)
            {
                throw new ProtocolException($"Failed to deserialize: {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Validate message format and required fields
        /// </summary>
        public void ValidateMessage(ProtocolMessage message)
        {
            if (message == null)
                throw new ProtocolException("Message cannot be null");
            
            if (string.IsNullOrEmpty(message.MessageId))
                throw new ProtocolException("Message ID is required");
            
            if (string.IsNullOrEmpty(message.ProtocolVersion))
                throw new ProtocolException("Protocol version is required");

            // Version compatibility check (must be exactly 1.0.0 for now)
            if (message.ProtocolVersion != "1.0.0")
                throw new ProtocolException($"Unsupported protocol version: {message.ProtocolVersion}");
        }

        /// <summary>
        /// Create error message response
        /// </summary>
        public ErrorMessage CreateErrorMessage(int errorCode, string description, string? relatedMessageId = null)
        {
            return new ErrorMessage
            {
                ErrorCode = errorCode,
                ErrorDescription = description,
                RelatedMessageId = relatedMessageId
            };
        }

        /// <summary>
        /// Create ACK message response
        /// </summary>
        public AckMessage CreateAckMessage(string messageIdToAck, int status = 0)
        {
            return new AckMessage
            {
                AckMessageId = messageIdToAck,
                Status = status
            };
        }
    }

    /// <summary>
    /// Exception thrown when protocol serialization/deserialization fails
    /// </summary>
    public class ProtocolException : Exception
    {
        public ProtocolException(string message) : base(message) { }
        public ProtocolException(string message, Exception innerException) 
            : base(message, innerException) { }
    }

    /// <summary>
    /// Protocol error codes
    /// </summary>
    public static class ProtocolErrorCodes
    {
        public const int INVALID_MESSAGE = 1001;
        public const int AUTHENTICATION_FAILED = 1002;
        public const int ROLE_CONFLICT = 1003;
        public const int DEVICE_OFFLINE = 1004;
        public const int VERSION_MISMATCH = 1005;
        public const int INVALID_INPUT_EVENT = 1006;
        public const int CONNECTION_TIMEOUT = 1007;
        public const int INTERNAL_ERROR = 1008;
    }
}
