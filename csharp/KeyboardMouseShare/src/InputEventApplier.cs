using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using KeyboardMouseShare.Models;
using KeyboardMouseShare.Platform;

namespace KeyboardMouseShare.Services
{
    /// <summary>
    /// Configuration for input event applier
    /// </summary>
    public class InputApplierConfig
    {
        /// <summary>Delay between events in milliseconds</summary>
        public int EventDelayMs { get; set; } = 10;

        /// <summary>Maximum queue size before rejecting events</summary>
        public int MaxQueueSize { get; set; } = 1000;

        /// <summary>Whether to validate events</summary>
        public bool ValidateEvents { get; set; } = true;

        /// <summary>Whether to track modifier keys</summary>
        public bool TrackModifiers { get; set; } = true;

        /// <summary>Whether to log events</summary>
        public bool LogEvents { get; set; } = true;
    }

    /// <summary>
    /// Metrics for input event application
    /// </summary>
    public class InputApplierMetrics
    {
        /// <summary>Total events received</summary>
        public int EventsReceived { get; set; }

        /// <summary>Total events applied</summary>
        public int EventsApplied { get; set; }

        /// <summary>Total events failed</summary>
        public int EventsFailed { get; set; }

        /// <summary>Count of keyboard events</summary>
        public int KeyboardEvents { get; set; }

        /// <summary>Count of mouse events</summary>
        public int MouseEvents { get; set; }

        /// <summary>List of error messages</summary>
        public List<string> Errors { get; set; } = new();

        /// <summary>Reset all metrics</summary>
        public void Reset()
        {
            EventsReceived = 0;
            EventsApplied = 0;
            EventsFailed = 0;
            KeyboardEvents = 0;
            MouseEvents = 0;
            Errors.Clear();
        }
    }

    /// <summary>
    /// Service for applying input events (keyboard and mouse) on the local device
    /// </summary>
    public interface IInputEventApplier
    {
        /// <summary>Start the applier</summary>
        void Start();

        /// <summary>Stop the applier</summary>
        void Stop();

        /// <summary>Apply an input event</summary>
        bool ApplyEvent(InputEvent @event);

        /// <summary>Get current metrics</summary>
        InputApplierMetrics GetMetrics();

        /// <summary>Reset metrics</summary>
        void ResetMetrics();
    }

    /// <summary>
    /// Implementation of input event applier
    /// </summary>
    public class InputEventApplier : IInputEventApplier
    {
        private readonly ILogger<InputEventApplier> _logger;
        private readonly InputApplierConfig _config;
        private readonly InputApplierMetrics _metrics = new();
        private readonly ConcurrentQueue<InputEvent> _eventQueue = new();
        private readonly WindowsInputSimulator _inputSimulator;
        private readonly HashSet<string> _pressedKeys = new();
        // ReSharper disable once NotAccessedField.Local - Reserved for future use
#pragma warning disable CS0414
        private (int X, int Y) _mousePosition = (0, 0);
#pragma warning restore CS0414

        private Thread? _processingThread;
        private volatile bool _isRunning = false;

        public InputEventApplier(ILogger<InputEventApplier> logger, InputApplierConfig? config = null)
        {
            _logger = logger;
            _config = config ?? new InputApplierConfig();
            // WindowsInputSimulator uses a different logger type, so pass null
            // The simulator will still log internally if needed
            _inputSimulator = new WindowsInputSimulator();
        }

        /// <summary>
        /// Start event applier thread
        /// </summary>
        public void Start()
        {
            if (_isRunning)
                return;

            _logger.LogInformation("Starting input event applier");
            _isRunning = true;

            _processingThread = new Thread(ProcessEventLoop)
            {
                IsBackground = true,
                Name = "InputEventApplier-Thread"
            };

            _processingThread.Start();
            _logger.LogInformation("Input event applier started");
        }

        /// <summary>
        /// Stop event applier thread
        /// </summary>
        public void Stop()
        {
            if (!_isRunning)
                return;

            _logger.LogInformation("Stopping input event applier");
            _isRunning = false;

            if (_processingThread != null)
            {
                _processingThread.Join(1000);
            }

            // Release all pressed keys
            ReleaseAllKeys();
            
            // Dispose simulator
            _inputSimulator?.Dispose();
            
            _logger.LogInformation("Input event applier stopped");
        }

        /// <summary>
        /// Queue an input event for application
        /// </summary>
        public bool ApplyEvent(InputEvent @event)
        {
            if (!_isRunning)
            {
                _logger.LogWarning("Cannot apply event when applier is not running");
                return false;
            }

            if (_config.ValidateEvents && !@event.IsValid())
            {
                _logger.LogWarning("Invalid event rejected: {EventType}", @event.EventType);
                _metrics.EventsFailed++;
                return false;
            }

            if (_eventQueue.Count >= _config.MaxQueueSize)
            {
                _logger.LogWarning("Event queue full, rejecting event");
                _metrics.EventsFailed++;
                return false;
            }

            _metrics.EventsReceived++;
            _eventQueue.Enqueue(@event);

            if (_config.LogEvents)
            {
                _logger.LogDebug("Event queued: {EventType}", @event.EventType);
            }

            return true;
        }

        /// <summary>
        /// Get current metrics
        /// </summary>
        public InputApplierMetrics GetMetrics()
        {
            return new InputApplierMetrics
            {
                EventsReceived = _metrics.EventsReceived,
                EventsApplied = _metrics.EventsApplied,
                EventsFailed = _metrics.EventsFailed,
                KeyboardEvents = _metrics.KeyboardEvents,
                MouseEvents = _metrics.MouseEvents,
                Errors = new List<string>(_metrics.Errors)
            };
        }

        /// <summary>
        /// Reset metrics
        /// </summary>
        public void ResetMetrics()
        {
            _metrics.Reset();
            _logger.LogInformation("Metrics reset");
        }

        /// <summary>
        /// Main event processing loop
        /// </summary>
        private void ProcessEventLoop()
        {
            while (_isRunning)
            {
                try
                {
                    if (_eventQueue.TryDequeue(out var @event))
                    {
                        ApplySingleEvent(@event);
                        Thread.Sleep(_config.EventDelayMs);
                    }
                    else
                    {
                        Thread.Sleep(2);
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error processing event");
                }
            }
        }

        /// <summary>
        /// Apply a single event
        /// </summary>
        private void ApplySingleEvent(InputEvent @event)
        {
            try
            {
                switch (@event.EventType)
                {
                    case InputEventType.KEY_PRESS:
                        ApplyKeyPress(@event);
                        _metrics.KeyboardEvents++;
                        break;

                    case InputEventType.KEY_RELEASE:
                        ApplyKeyRelease(@event);
                        _metrics.KeyboardEvents++;
                        break;

                    case InputEventType.MOUSE_MOVE:
                        ApplyMouseMove(@event);
                        _metrics.MouseEvents++;
                        break;

                    case InputEventType.MOUSE_CLICK:
                        ApplyMouseClick(@event);
                        _metrics.MouseEvents++;
                        break;

                    case InputEventType.MOUSE_SCROLL:
                        ApplyMouseScroll(@event);
                        _metrics.MouseEvents++;
                        break;

                    default:
                        _logger.LogWarning("Unknown event type: {EventType}", @event.EventType);
                        _metrics.EventsFailed++;
                        return;
                }

                _metrics.EventsApplied++;

                if (_config.LogEvents)
                {
                    _logger.LogDebug("Event applied: {EventType}", @event.EventType);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to apply event: {EventType}", @event.EventType);
                _metrics.EventsFailed++;
                _metrics.Errors.Add(ex.Message);
            }
        }

        /// <summary>
        /// Apply key press event
        /// </summary>
        private void ApplyKeyPress(InputEvent @event)
        {
            var keycode = @event.Payload["keycode"].ToString() ?? "";
            _logger.LogDebug("Key press: {Keycode}", keycode);
            
            var vk = MapKeycode(keycode);
            if (vk == 0)
            {
                _logger.LogWarning("Unknown keycode: {Keycode}", keycode);
                return;
            }

            if (_config.TrackModifiers)
            {
                _pressedKeys.Add(keycode);
            }

            var success = _inputSimulator.KeyDown(vk);
            if (!success)
            {
                _logger.LogWarning("Failed to send key down for {Keycode} (VK={VirtualKey})", keycode, vk);
            }
        }

        /// <summary>
        /// Apply key release event
        /// </summary>
        private void ApplyKeyRelease(InputEvent @event)
        {
            var keycode = @event.Payload["keycode"].ToString() ?? "";
            _logger.LogDebug("Key release: {Keycode}", keycode);
            
            var vk = MapKeycode(keycode);
            if (vk == 0)
            {
                _logger.LogWarning("Unknown keycode: {Keycode}", keycode);
                return;
            }

            if (_config.TrackModifiers)
            {
                _pressedKeys.Remove(keycode);
            }

            var success = _inputSimulator.KeyUp(vk);
            if (!success)
            {
                _logger.LogWarning("Failed to send key up for {Keycode} (VK={VirtualKey})", keycode, vk);
            }
        }

        /// <summary>
        /// Apply mouse move event
        /// </summary>
        private void ApplyMouseMove(InputEvent @event)
        {
            var x = (int)Convert.ToDouble(@event.Payload["x"]);
            var y = (int)Convert.ToDouble(@event.Payload["y"]);
            _logger.LogDebug("Mouse move to ({X}, {Y})", x, y);
            
            _mousePosition = (x, y);
            
            var success = _inputSimulator.MouseMoveTo(x, y);
            if (!success)
            {
                _logger.LogWarning("Failed to move mouse to ({X}, {Y})", x, y);
            }
        }

        /// <summary>
        /// Apply mouse click event
        /// </summary>
        private void ApplyMouseClick(InputEvent @event)
        {
            var button = @event.Payload["button"].ToString() ?? "left";
            var clicks = (int)Convert.ToDouble(@event.Payload.GetValueOrDefault("clicks", 1));
            _logger.LogDebug("Mouse click ({Button}) x{Clicks}", button, clicks);
            
            for (int i = 0; i < clicks; i++)
            {
                bool success = button.ToLower() switch
                {
                    "left" => _inputSimulator.LeftClick(),
                    "right" => _inputSimulator.RightClick(),
                    "middle" => _inputSimulator.MiddleClick(),
                    _ => false
                };

                if (!success)
                {
                    _logger.LogWarning("Failed to send mouse click ({Button})", button);
                }
            }
        }

        /// <summary>
        /// Apply mouse scroll event
        /// </summary>
        private void ApplyMouseScroll(InputEvent @event)
        {
            var delta = (int)Convert.ToDouble(@event.Payload["scroll_delta"]);
            _logger.LogDebug("Mouse scroll: {Delta}", delta);
            
            var success = _inputSimulator.Scroll(delta);
            if (!success)
            {
                _logger.LogWarning("Failed to scroll with delta={Delta}", delta);
            }
        }

        /// <summary>
        /// Release all pressed keys
        /// </summary>
        private void ReleaseAllKeys()
        {
            foreach (var key in _pressedKeys.ToList())
            {
                _logger.LogDebug("Releasing key: {Keycode}", key);
                var vk = MapKeycode(key);
                if (vk != 0)
                {
                    try
                    {
                        _inputSimulator.KeyUp(vk);
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning(ex, "Failed to release key: {Keycode}", key);
                    }
                }
            }

            _pressedKeys.Clear();
        }

        /// <summary>
        /// Map keycode string to Windows virtual key code
        /// Handles common keycodes from both Windows and macOS platforms
        /// </summary>
        private ushort MapKeycode(string keycode)
        {
            // Handle null/empty
            if (string.IsNullOrEmpty(keycode))
                return 0;

            // Normalize to uppercase for comparison
            var key = keycode.ToUpperInvariant();

            // Function keys
            if (key.StartsWith("F") && ushort.TryParse(key.Substring(1), out var fNum) && fNum >= 1 && fNum <= 24)
            {
                return (ushort)(VirtualKeyCodes.VK_F1 + fNum - 1);
            }

            // Number keys
            if (key.Length == 1 && char.IsDigit(key[0]))
            {
                return (ushort)(VirtualKeyCodes.VK_0 + (key[0] - '0'));
            }

            // Letter keys
            if (key.Length == 1 && char.IsLetter(key[0]))
            {
                return (ushort)(VirtualKeyCodes.VK_A + char.ToUpperInvariant(key[0]) - 'A');
            }

            // Named keys
            return key switch
            {
                "BACKSPACE" or "BACK" => VirtualKeyCodes.VK_BACK,
                "TAB" => VirtualKeyCodes.VK_TAB,
                "ENTER" or "RETURN" => VirtualKeyCodes.VK_RETURN,
                "SHIFT" or "LSHIFT" => VirtualKeyCodes.VK_LSHIFT,
                "RSHIFT" => VirtualKeyCodes.VK_RSHIFT,
                "CONTROL" or "CTRL" or "LCTRL" => VirtualKeyCodes.VK_LCONTROL,
                "RCTRL" => VirtualKeyCodes.VK_RCONTROL,
                "ALT" or "LALT" => VirtualKeyCodes.VK_LMENU,
                "RALT" => VirtualKeyCodes.VK_RMENU,
                "PAUSE" => VirtualKeyCodes.VK_PAUSE,
                "CAPSLOCK" or "CAPS" => VirtualKeyCodes.VK_CAPITAL,
                "ESCAPE" or "ESC" => VirtualKeyCodes.VK_ESCAPE,
                "SPACE" or " " => VirtualKeyCodes.VK_SPACE,
                "PAGEUP" or "PAGE_UP" => VirtualKeyCodes.VK_PRIOR,
                "PAGEDOWN" or "PAGE_DOWN" => VirtualKeyCodes.VK_NEXT,
                "END" => VirtualKeyCodes.VK_END,
                "HOME" => VirtualKeyCodes.VK_HOME,
                "LEFT" or "LEFTARROW" => VirtualKeyCodes.VK_LEFT,
                "UP" or "UPARROW" => VirtualKeyCodes.VK_UP,
                "RIGHT" or "RIGHTARROW" => VirtualKeyCodes.VK_RIGHT,
                "DOWN" or "DOWNARROW" => VirtualKeyCodes.VK_DOWN,
                "INSERT" or "INS" => VirtualKeyCodes.VK_INSERT,
                "DELETE" or "DEL" => VirtualKeyCodes.VK_DELETE,
                "PRINT" or "PRINTSCREEN" => VirtualKeyCodes.VK_SNAPSHOT,
                "LWIN" or "LSUPER" => VirtualKeyCodes.VK_LWIN,
                "RWIN" or "RSUPER" => VirtualKeyCodes.VK_RWIN,
                "NUMPAD0" or "NUM0" => VirtualKeyCodes.VK_NUMPAD0,
                "NUMPAD1" or "NUM1" => VirtualKeyCodes.VK_NUMPAD1,
                "NUMPAD2" or "NUM2" => VirtualKeyCodes.VK_NUMPAD2,
                "NUMPAD3" or "NUM3" => VirtualKeyCodes.VK_NUMPAD3,
                "NUMPAD4" or "NUM4" => VirtualKeyCodes.VK_NUMPAD4,
                "NUMPAD5" or "NUM5" => VirtualKeyCodes.VK_NUMPAD5,
                "NUMPAD6" or "NUM6" => VirtualKeyCodes.VK_NUMPAD6,
                "NUMPAD7" or "NUM7" => VirtualKeyCodes.VK_NUMPAD7,
                "NUMPAD8" or "NUM8" => VirtualKeyCodes.VK_NUMPAD8,
                "NUMPAD9" or "NUM9" => VirtualKeyCodes.VK_NUMPAD9,
                "MULTIPLY" or "NUMMUL" => VirtualKeyCodes.VK_MULTIPLY,
                "ADD" or "NUMADD" => VirtualKeyCodes.VK_ADD,
                "SUBTRACT" or "NUMSUB" => VirtualKeyCodes.VK_SUBTRACT,
                "DECIMAL" or "NUMDECIMAL" => VirtualKeyCodes.VK_DECIMAL,
                "DIVIDE" or "NUMDIV" => VirtualKeyCodes.VK_DIVIDE,
                "SEMICOLON" or ";" => VirtualKeyCodes.VK_SEMICOLON,
                "EQUAL" or "PLUS" or "=" or "+" => VirtualKeyCodes.VK_PLUS,
                "COMMA" or "," => VirtualKeyCodes.VK_COMMA,
                "MINUS" or "-" => VirtualKeyCodes.VK_MINUS,
                "PERIOD" or "." => VirtualKeyCodes.VK_PERIOD,
                "SLASH" or "/" => VirtualKeyCodes.VK_SLASH,
                "BACKTICK" or "`" => VirtualKeyCodes.VK_BACKTICK,
                "LBRACKET" or "[" => VirtualKeyCodes.VK_LBRACKET,
                "BACKSLASH" or "\\" => VirtualKeyCodes.VK_BACKSLASH,
                "RBRACKET" or "]" => VirtualKeyCodes.VK_RBRACKET,
                "QUOTE" or "'" => VirtualKeyCodes.VK_QUOTE,
                _ => 0  // Unknown keycode
            };
        }
    }
}
