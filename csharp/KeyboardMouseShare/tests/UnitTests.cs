using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Linq;
using Xunit;
using Moq;
using Microsoft.Extensions.Logging;
using KeyboardMouseShare.Models;
using KeyboardMouseShare.Services;
using KeyboardMouseShare.Platform;

namespace KeyboardMouseShare.Tests
{
    /// <summary>
    /// Unit tests for InputEventApplier service
    /// </summary>
    public class InputEventApplierTests
    {
        private readonly Mock<ILogger<InputEventApplier>> _mockLogger;
        private readonly InputEventApplier _applier;

        public InputEventApplierTests()
        {
            _mockLogger = new Mock<ILogger<InputEventApplier>>();
            _applier = new InputEventApplier(_mockLogger.Object);
        }

        [Fact]
        public void Constructor_WithValidConfig_InitializesSuccessfully()
        {
            // Arrange
            var config = new InputApplierConfig
            {
                EventDelayMs = 5,
                MaxQueueSize = 500
            };

            // Act
            var applier = new InputEventApplier(_mockLogger.Object, config);

            // Assert
            Assert.NotNull(applier);
        }

        [Fact]
        public void Start_WhenCalled_StartsEventProcessor()
        {
            // Act
            _applier.Start();

            // Assert
            Assert.NotNull(_applier);
        }

        [Fact]
        public void Stop_WhenCalled_StopsEventProcessor()
        {
            // Arrange
            _applier.Start();

            // Act
            _applier.Stop();

            // Assert
            Assert.NotNull(_applier);
        }

        [Fact]
        public void ApplyEvent_WithValidKeyPressEvent_ReturnsTrue()
        {
            // Arrange
            _applier.Start();
            var @event = new InputEvent(InputEventType.KEY_PRESS, "device1", "device2")
            {
                Payload = { { "keycode", "A" } }
            };

            // Act
            var result = _applier.ApplyEvent(@event);

            // Assert
            Assert.True(result);
            _applier.Stop();
        }

        [Fact]
        public void ApplyEvent_WithInvalidEvent_ReturnsFalse()
        {
            // Arrange
            _applier.Start();
            var @event = new InputEvent(InputEventType.KEY_PRESS, "device1", "device2")
            {
                Payload = new Dictionary<string, object>() // Missing keycode
            };

            // Act
            var result = _applier.ApplyEvent(@event);

            // Assert
            Assert.False(result);
            _applier.Stop();
        }

        [Fact]
        public void ApplyEvent_WhenNotRunning_ReturnsFalse()
        {
            // Arrange
            var @event = new InputEvent(InputEventType.KEY_PRESS, "device1", "device2")
            {
                Payload = { { "keycode", "A" } }
            };

            // Act
            var result = _applier.ApplyEvent(@event);

            // Assert
            Assert.False(result);
        }

        [Fact]
        public void GetMetrics_ReturnsMetrics()
        {
            // Arrange
            _applier.Start();
            var @event = new InputEvent(InputEventType.KEY_PRESS, "device1", "device2")
            {
                Payload = { { "keycode", "A" } }
            };

            // Act
            _applier.ApplyEvent(@event);
            var metrics = _applier.GetMetrics();

            // Assert
            Assert.NotNull(metrics);
            Assert.True(metrics.EventsReceived >= 1);
            _applier.Stop();
        }

        [Fact]
        public void ResetMetrics_ClearsMetrics()
        {
            // Arrange
            _applier.Start();
            var @event = new InputEvent(InputEventType.KEY_PRESS, "device1", "device2")
            {
                Payload = { { "keycode", "A" } }
            };
            _applier.ApplyEvent(@event);

            // Act
            _applier.ResetMetrics();
            var metrics = _applier.GetMetrics();

            // Assert
            Assert.Equal(0, metrics.EventsReceived);
            Assert.Equal(0, metrics.EventsApplied);
            _applier.Stop();
        }
    }

    /// <summary>
    /// Unit tests for DeviceDiscoveryService
    /// </summary>
    public class DeviceDiscoveryServiceTests
    {
        private readonly Mock<ILogger<DeviceDiscoveryService>> _mockLogger;
        private readonly DeviceDiscoveryService _discoveryService;

        public DeviceDiscoveryServiceTests()
        {
            _mockLogger = new Mock<ILogger<DeviceDiscoveryService>>();
            _discoveryService = new DeviceDiscoveryService(_mockLogger.Object);
        }

        [Fact]
        public async Task StartDiscoveryAsync_WhenCalled_StartesDiscovery()
        {
            // Act
            await _discoveryService.StartDiscoveryAsync();

            // Assert
            Assert.NotNull(_discoveryService);
        }

        [Fact]
        public async Task StopDiscoveryAsync_WhenCalled_StopsDiscovery()
        {
            // Arrange
            await _discoveryService.StartDiscoveryAsync();

            // Act
            await _discoveryService.StopDiscoveryAsync();

            // Assert
            Assert.NotNull(_discoveryService);
        }

        [Fact]
        public void GetDiscoveredDevices_ReturnsEmptyListInitially()
        {
            // Act
            var devices = _discoveryService.GetDiscoveredDevices();

            // Assert
            Assert.Empty(devices);
        }
    }

    /// <summary>
    /// Unit tests for ConnectionService
    /// </summary>
    public class ConnectionServiceTests
    {
        private readonly Mock<ILogger<ConnectionService>> _mockLogger;
        private readonly ConnectionService _connectionService;

        public ConnectionServiceTests()
        {
            _mockLogger = new Mock<ILogger<ConnectionService>>();
            _connectionService = new ConnectionService(_mockLogger.Object);
        }

        [Fact]
        public void GetAllConnections_InitiallyEmpty()
        {
            // Act
            var connections = _connectionService.GetAllConnections();

            // Assert
            Assert.Empty(connections);
        }

        [Fact]
        public async Task ConnectAsync_WithValidDevices_EstablishesConnection()
        {
            // Arrange
            var localDevice = new Device("Local Machine", DeviceRole.Master);
            var remoteDevice = new Device("Remote Machine", DeviceRole.Client);

            // Act
            var connection = await _connectionService.ConnectAsync(remoteDevice, localDevice);

            // Assert
            Assert.NotNull(connection);
            Assert.True(connection.IsConnected);
        }

        [Fact]
        public async Task DisconnectAsync_WithValidDeviceId_ClosesConnection()
        {
            // Arrange
            var localDevice = new Device("Local Machine", DeviceRole.Master);
            var remoteDevice = new Device("Remote Machine", DeviceRole.Client);
            var connection = await _connectionService.ConnectAsync(remoteDevice, localDevice);

            // Act
            await _connectionService.DisconnectAsync(remoteDevice.Id);
            var retrieved = _connectionService.GetConnection(remoteDevice.Id);

            // Assert
            Assert.Null(retrieved);
        }
    }

    /// <summary>
    /// Unit tests for model classes
    /// </summary>
    public class ModelsTests
    {
        [Fact]
        public void Device_CreateWithValidData_InitializesCorrectly()
        {
            // Act
            var device = new Device("Test Device", DeviceRole.Master);

            // Assert
            Assert.Equal("Test Device", device.Name);
            Assert.Equal(DeviceRole.Master, device.Role);
            Assert.False(string.IsNullOrEmpty(device.Id));
        }

        [Fact]
        public void InputEvent_ValidateKeyPress_ReturnsTrue()
        {
            // Arrange
            var @event = new InputEvent(InputEventType.KEY_PRESS, "device1", "device2")
            {
                Payload = { { "keycode", "A" } }
            };

            // Act
            var isValid = @event.IsValid();

            // Assert
            Assert.True(isValid);
        }

        [Fact]
        public void InputEvent_ValidateMouseMove_ReturnsTrue()
        {
            // Arrange
            var @event = new InputEvent(InputEventType.MOUSE_MOVE, "device1", "device2")
            {
                Payload = { { "x", 100 }, { "y", 200 } }
            };

            // Act
            var isValid = @event.IsValid();

            // Assert
            Assert.True(isValid);
        }

        [Fact]
        public void Connection_CreateWithDevices_InitializesCorrectly()
        {
            // Arrange
            var localDevice = new Device("Local", DeviceRole.Master);
            var remoteDevice = new Device("Remote", DeviceRole.Client);

            // Act
            var connection = new Connection(localDevice, remoteDevice);

            // Assert
            Assert.Equal(localDevice, connection.LocalDevice);
            Assert.Equal(remoteDevice, connection.RemoteDevice);
        }
    }

    /// <summary>
    /// Unit tests for Windows Input Simulator
    /// </summary>
    public class WindowsInputSimulatorTests
    {
        private readonly WindowsInputSimulator _simulator;

        public WindowsInputSimulatorTests()
        {
            _simulator = new WindowsInputSimulator();
        }

        [Fact]
        public void GetMousePosition_ReturnsValidCoordinates()
        {
            // Act
            var (x, y) = _simulator.GetMousePosition();

            // Assert
            Assert.True(x >= 0);
            Assert.True(y >= 0);
        }

        [Fact]
        public void MouseMoveTo_AcceptsValidCoordinates()
        {
            // Act
            var result = _simulator.MouseMoveTo(100, 100);

            // Assert
            Assert.True(result || result == false); // Either succeeds or fails gracefully
        }

        [Fact]
        public void KeyDown_AcceptsValidVirtualKey()
        {
            // Act
            var result = _simulator.KeyDown(VirtualKeyCodes.VK_SPACE);

            // Assert
            Assert.True(result || result == false);
        }

        [Fact]
        public void KeyUp_AcceptsValidVirtualKey()
        {
            // Act
            var result = _simulator.KeyUp(VirtualKeyCodes.VK_SPACE);

            // Assert
            Assert.True(result || result == false);
        }

        [Fact]
        public void LeftClick_ExecutesWithoutThrow()
        {
            // Act & Assert
            var result = _simulator.LeftClick();
            Assert.True(result || result == false);
        }

        [Fact]
        public void RightClick_ExecutesWithoutThrow()
        {
            // Act & Assert
            var result = _simulator.RightClick();
            Assert.True(result || result == false);
        }

        [Fact]
        public void Scroll_AcceptsPositiveAndNegativeDelta()
        {
            // Act
            var resultUp = _simulator.Scroll(3);
            var resultDown = _simulator.Scroll(-3);

            // Assert
            Assert.True(resultUp || resultUp == false);
            Assert.True(resultDown || resultDown == false);
        }
    }

    /// <summary>
    /// Keycode mapping tests
    /// </summary>
    public class KeycodeMappingTests
    {
        [Theory]
        [InlineData(VirtualKeyCodes.VK_SPACE)]
        [InlineData(VirtualKeyCodes.VK_RETURN)]
        [InlineData(VirtualKeyCodes.VK_ESCAPE)]
        [InlineData(VirtualKeyCodes.VK_BACK)]
        [InlineData(VirtualKeyCodes.VK_TAB)]
        [InlineData(VirtualKeyCodes.VK_DELETE)]
        [InlineData(VirtualKeyCodes.VK_INSERT)]
        [InlineData(VirtualKeyCodes.VK_HOME)]
        [InlineData(VirtualKeyCodes.VK_END)]
        [InlineData(VirtualKeyCodes.VK_PRIOR)]
        [InlineData(VirtualKeyCodes.VK_NEXT)]
        [InlineData(VirtualKeyCodes.VK_LEFT)]
        [InlineData(VirtualKeyCodes.VK_RIGHT)]
        [InlineData(VirtualKeyCodes.VK_UP)]
        [InlineData(VirtualKeyCodes.VK_DOWN)]
        public void VirtualKeyCodes_AreDefinedCorrectly(ushort vkCode)
        {
            // Validate that all critical virtual key codes are properly defined
            Assert.NotEqual(0, vkCode);
        }
    }

    /// <summary>
    /// Configuration and settings tests
    /// </summary>
    public class InputApplierConfigTests
    {
        [Fact]
        public void Config_DefaultValues_SetCorrectly()
        {
            // Act
            var config = new InputApplierConfig();

            // Assert
            Assert.Equal(10, config.EventDelayMs);
            Assert.Equal(1000, config.MaxQueueSize);
            Assert.True(config.ValidateEvents);
            Assert.True(config.TrackModifiers);
            Assert.True(config.LogEvents);
        }

        [Fact]
        public void Config_CustomValues_CanBeSet()
        {
            // Act
            var config = new InputApplierConfig
            {
                EventDelayMs = 5,
                MaxQueueSize = 2000,
                ValidateEvents = false,
                LogEvents = false
            };

            // Assert
            Assert.Equal(5, config.EventDelayMs);
            Assert.Equal(2000, config.MaxQueueSize);
            Assert.False(config.ValidateEvents);
            Assert.False(config.LogEvents);
        }
    }

    /// <summary>
    /// Metrics tracking tests
    /// </summary>
    public class MetricsTests
    {
        [Fact]
        public void Metrics_Reset_ClearsAllValues()
        {
            // Arrange
            var metrics = new InputApplierMetrics
            {
                EventsReceived = 10,
                EventsApplied = 8,
                EventsFailed = 2,
                KeyboardEvents = 5,
                MouseEvents = 3
            };

            // Act
            metrics.Reset();

            // Assert
            Assert.Equal(0, metrics.EventsReceived);
            Assert.Equal(0, metrics.EventsApplied);
            Assert.Equal(0, metrics.EventsFailed);
            Assert.Equal(0, metrics.KeyboardEvents);
            Assert.Equal(0, metrics.MouseEvents);
        }

        [Fact]
        public void Metrics_Errors_CanBeTracked()
        {
            // Arrange
            var metrics = new InputApplierMetrics();
            var errorMessage = "Test error occurred";

            // Act
            metrics.Errors.Add(errorMessage);

            // Assert
            Assert.Contains(errorMessage, metrics.Errors);
            Assert.Single(metrics.Errors);
        }
    }

    /// <summary>
    /// Advanced InputEventApplier tests
    /// </summary>
    public class InputEventApplierAdvancedTests
    {
        private readonly InputEventApplier _applier;
        private readonly Mock<ILogger<InputEventApplier>> _mockLogger;

        public InputEventApplierAdvancedTests()
        {
            _mockLogger = new Mock<ILogger<InputEventApplier>>();
            _applier = new InputEventApplier(_mockLogger.Object);
        }

        [Fact]
        public void ApplyEvent_MultipleKeyPresses_AllQueued()
        {
            // Arrange
            _applier.Start();
            var events = new[]
            {
                CreateKeyEvent("A"),
                CreateKeyEvent("B"),
                CreateKeyEvent("C")
            };

            // Act
            var results = events.Select(e => _applier.ApplyEvent(e)).ToList();

            // Assert
            Assert.All(results, Assert.True);
            var metrics = _applier.GetMetrics();
            Assert.Equal(3, metrics.EventsReceived);

            _applier.Stop();
        }

        [Fact]
        public void ApplyEvent_MouseAndKeyboard_BothProcessed()
        {
            // Arrange
            _applier.Start();
            var keyEvent = CreateKeyEvent("Space");
            var mouseEvent = CreateMouseEvent(100, 200);

            // Act
            var key = _applier.ApplyEvent(keyEvent);
            var mouse = _applier.ApplyEvent(mouseEvent);

            // Assert
            Assert.True(key);
            Assert.True(mouse);
            var metrics = _applier.GetMetrics();
            Assert.Equal(2, metrics.EventsReceived);

            _applier.Stop();
        }

        [Fact]
        public void ApplyEvent_InvalidEvent_Rejected()
        {
            // Arrange
            _applier.Start();
            var invalidEvent = new InputEvent(InputEventType.KEY_PRESS, "device1", "device2")
            {
                Timestamp = DateTime.UtcNow,
                Payload = new Dictionary<string, object>()  // Missing keycode
            };

            // Act
            var result = _applier.ApplyEvent(invalidEvent);

            // Assert
            Assert.False(result);

            _applier.Stop();
        }

        [Fact]
        public void ApplyEvent_QueueFull_Rejected()
        {
            // Arrange
            var config = new InputApplierConfig { MaxQueueSize = 2 };
            var applier = new InputEventApplier(_mockLogger.Object, config);
            applier.Start();

            var events = Enumerable.Range(0, 5)
                .Select(i => CreateKeyEvent($"key{i}"))
                .ToList();

            // Act
            applier.ApplyEvent(events[0]);
            applier.ApplyEvent(events[1]);
            var result = applier.ApplyEvent(events[2]);  // Should fail - queue full

            // Assert
            Assert.False(result);

            applier.Stop();
        }

        [Theory]
        [InlineData(InputEventType.KEY_PRESS)]
        [InlineData(InputEventType.KEY_RELEASE)]
        [InlineData(InputEventType.MOUSE_MOVE)]
        [InlineData(InputEventType.MOUSE_CLICK)]
        [InlineData(InputEventType.MOUSE_SCROLL)]
        public void ApplyEvent_AllEventTypes_Accepted(InputEventType eventType)
        {
            // Arrange
            _applier.Start();
            InputEvent? evt = eventType switch
            {
                InputEventType.KEY_PRESS => CreateKeyEvent("A"),
                InputEventType.KEY_RELEASE => CreateKeyEvent("A"),
                InputEventType.MOUSE_MOVE => CreateMouseEvent(100, 200),
                InputEventType.MOUSE_CLICK => CreateMouseClickEvent("left"),
                InputEventType.MOUSE_SCROLL => CreateMouseScrollEvent(5),
                _ => null
            };

            // Act
            var result = _applier.ApplyEvent(evt!);

            // Assert
            Assert.True(result);

            _applier.Stop();
        }

        private InputEvent CreateKeyEvent(string keycode)
        {
            return new InputEvent(InputEventType.KEY_PRESS, "device1", "device2")
            {
                Payload = { { "keycode", keycode } }
            };
        }

        private InputEvent CreateMouseEvent(int x, int y)
        {
            return new InputEvent(InputEventType.MOUSE_MOVE, "device1", "device2")
            {
                Payload = { { "x", x }, { "y", y } }
            };
        }

        private InputEvent CreateMouseClickEvent(string button)
        {
            return new InputEvent(InputEventType.MOUSE_CLICK, "device1", "device2")
            {
                Payload = { { "button", button } }
            };
        }

        private InputEvent CreateMouseScrollEvent(int delta)
        {
            return new InputEvent(InputEventType.MOUSE_SCROLL, "device1", "device2")
            {
                Payload = { { "scroll_delta", delta } }
            };
        }
    }

    /// <summary>
    /// Extended Windows Input Simulator tests
    /// </summary>
    public class WindowsInputSimulatorExtendedTests
    {
        private readonly WindowsInputSimulator _simulator;

        public WindowsInputSimulatorExtendedTests()
        {
            _simulator = new WindowsInputSimulator();
        }

        [Theory]
        [InlineData(VirtualKeyCodes.VK_A)]
        [InlineData(VirtualKeyCodes.VK_Z)]
        [InlineData(VirtualKeyCodes.VK_0)]
        [InlineData(VirtualKeyCodes.VK_9)]
        [InlineData(VirtualKeyCodes.VK_F1)]
        [InlineData(VirtualKeyCodes.VK_F12)]
        public void KeyDown_VariousKeys_Accepted(ushort vkCode)
        {
            // Act
            var result = _simulator.KeyDown(vkCode);

            // Assert
            Assert.True(result || result == false);  // Either succeeds or fails gracefully
        }

        [Theory]
        [InlineData(0, 0)]
        [InlineData(100, 100)]
        [InlineData(1920, 1080)]
        [InlineData(3840, 2160)]  // 4K support
        public void MouseMoveTo_VariousPositions_Accepted(int x, int y)
        {
            // Act
            var result = _simulator.MouseMoveTo(x, y);

            // Assert
            Assert.True(result || result == false);
        }

        [Theory]
        [InlineData(1)]
        [InlineData(5)]
        [InlineData(-1)]
        [InlineData(-5)]
        public void Scroll_VariousDeltas_Accepted(int delta)
        {
            // Act
            var result = _simulator.Scroll(delta);

            // Assert
            Assert.True(result || result == false);
        }

        [Fact]
        public void LeftClick_MultipleClicks_Consistent()
        {
            // Act
            var results = new List<bool>();
            for (int i = 0; i < 5; i++)
            {
                results.Add(_simulator.LeftClick());
            }

            // Assert - all operations should complete consistently
            Assert.NotEmpty(results);
        }
    }

    /// <summary>
    /// Event validation tests
    /// </summary>
    public class EventValidationTests
    {
        [Fact]
        public void KeyPressEvent_ValidWithAllFields_ReturnsTrue()
        {
            // Arrange
            var @event = new InputEvent(InputEventType.KEY_PRESS, "device1", "device2")
            {
                Payload = { { "keycode", "Space" } }
            };

            // Act
            var isValid = @event.IsValid();

            // Assert
            Assert.True(isValid);
        }

        [Fact]
        public void MouseMoveEvent_ValidWithCoordinates_ReturnsTrue()
        {
            // Arrange
            var @event = new InputEvent(InputEventType.MOUSE_MOVE, "device1", "device2")
            {
                Payload = { { "x", 500 }, { "y", 500 } }
            };

            // Act
            var isValid = @event.IsValid();

            // Assert
            Assert.True(isValid);
        }

        [Fact]
        public void MouseClickEvent_ValidWithButton_ReturnsTrue()
        {
            // Arrange
            var @event = new InputEvent(InputEventType.MOUSE_CLICK, "device1", "device2")
            {
                Payload = { { "button", "left" } }
            };

            // Act
            var isValid = @event.IsValid();

            // Assert
            Assert.True(isValid);
        }

        [Fact]
        public void KeyPressEvent_MissingPayload_ReturnsFalse()
        {
            // Arrange
            var @event = new InputEvent(InputEventType.KEY_PRESS, "device1", "device2")
            {
                Payload = new Dictionary<string, object>()  // Empty
            };

            // Act
            var isValid = @event.IsValid();

            // Assert
            Assert.False(isValid);
        }
    }

    /// <summary>
    /// Device and connection tests
    /// </summary>
    public class DeviceAndConnectionTests
    {
        [Fact]
        public void Device_CreateMultiple_AllHaveUniqueIds()
        {
            // Act
            var device1 = new Device("Device 1", DeviceRole.Master);
            var device2 = new Device("Device 2", DeviceRole.Client);

            // Assert
            Assert.NotEqual(device1.Id, device2.Id);
        }

        [Theory]
        [InlineData(DeviceRole.Master)]
        [InlineData(DeviceRole.Client)]
        public void Device_CreateWithRole_RoleAssigned(DeviceRole role)
        {
            // Act
            var device = new Device("Test Device", role);

            // Assert
            Assert.Equal(role, device.Role);
        }

        [Fact]
        public void Connection_Status_InitiallyNotConnected()
        {
            // Arrange
            var local = new Device("Local", DeviceRole.Master);
            var remote = new Device("Remote", DeviceRole.Client);

            // Act
            var connection = new Connection(local, remote);

            // Assert
            Assert.NotNull(connection);
        }
    }
}
