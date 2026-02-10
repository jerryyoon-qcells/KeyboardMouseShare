using System;
using System.Runtime.InteropServices;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;

namespace KeyboardMouseShare.Platform
{
    /// <summary>
    /// Windows API P/Invoke declarations for input simulation
    /// </summary>
    public static class WindowsInputApi
    {
        /// <summary>Windows SendInput API - simulates keyboard and mouse input</summary>
        [DllImport("user32.dll", SetLastError = true)]
        public static extern uint SendInput(uint nInputs, INPUT[] pInputs, int cbSize);

        /// <summary>Windows SetCursorPos API - moves cursor to specified position</summary>
        [DllImport("user32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool SetCursorPos(int x, int y);

        /// <summary>Windows GetCursorPos API - gets current cursor position</summary>
        [DllImport("user32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool GetCursorPos(out POINT lpPoint);

        /// <summary>Windows keybd_event API - legacy keyboard input (for compatibility)</summary>
        [DllImport("user32.dll", SetLastError = true)]
        public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);

        /// <summary>Windows mouse_event API - legacy mouse input (for compatibility)</summary>
        [DllImport("user32.dll", SetLastError = true)]
        public static extern void mouse_event(uint dwFlags, int dx, int dy, uint cButtons, UIntPtr dwExtraInfo);

        /// <summary>Windows MapVirtualKey API - maps virtual key codes</summary>
        [DllImport("user32.dll", SetLastError = true)]
        public static extern uint MapVirtualKey(uint uCode, uint uMapType);

        public const uint MAPVK_VK_TO_SCAN = 0; // Virtual key to scancode
        public const uint MAPVK_SCAN_TO_VK = 1; // Scancode to virtual key
    }

    /// <summary>
    /// POINT structure for cursor position
    /// </summary>
    [StructLayout(LayoutKind.Sequential)]
    public struct POINT
    {
        public int x;
        public int y;
    }

    /// <summary>
    /// INPUT structure for SendInput - can be keyboard or mouse input
    /// </summary>
    [StructLayout(LayoutKind.Explicit)]
    public struct INPUT
    {
        [FieldOffset(0)]
        public uint type;
        [FieldOffset(4)]
        public KEYBDINPUT ki;
        [FieldOffset(4)]
        public MOUSEINPUT mi;
    }

    /// <summary>
    /// KEYBDINPUT structure for keyboard input
    /// </summary>
    [StructLayout(LayoutKind.Sequential)]
    public struct KEYBDINPUT
    {
        public ushort wVk;      // Virtual key code
        public ushort wScan;    // Hardware scan code
        public uint dwFlags;    // Key event flags
        public uint time;       // Time of event (ms)
        public UIntPtr dwExtraInfo;  // Extended info
    }

    /// <summary>
    /// MOUSEINPUT structure for mouse input
    /// </summary>
    [StructLayout(LayoutKind.Sequential)]
    public struct MOUSEINPUT
    {
        public int dx;          // Mouse position x
        public int dy;          // Mouse position y
        public uint mouseData;  // Mouse button/wheel data
        public uint dwFlags;    // Mouse event flags
        public uint time;       // Time of event (ms)
        public UIntPtr dwExtraInfo;  // Extended info
    }

    /// <summary>
    /// Input type constants for SendInput
    /// </summary>
    public static class InputType
    {
        public const uint INPUT_MOUSE = 0;
        public const uint INPUT_KEYBOARD = 1;
        public const uint INPUT_HARDWARE = 2;
    }

    /// <summary>
    /// Keyboard event flags
    /// </summary>
    public static class KeyEventFlags
    {
        public const uint KEYEVENTF_KEYDOWN = 0;
        public const uint KEYEVENTF_KEYUP = 2;
        public const uint KEYEVENTF_EXTENDEDKEY = 1;
        public const uint KEYEVENTF_UNICODE = 4;
    }

    /// <summary>
    /// Mouse event flags
    /// </summary>
    public static class MouseEventFlags
    {
        public const uint MOUSEEVENTF_MOVE = 1;
        public const uint MOUSEEVENTF_LEFTDOWN = 2;
        public const uint MOUSEEVENTF_LEFTUP = 4;
        public const uint MOUSEEVENTF_RIGHTDOWN = 8;
        public const uint MOUSEEVENTF_RIGHTUP = 16;
        public const uint MOUSEEVENTF_MIDDLEDOWN = 32;
        public const uint MOUSEEVENTF_MIDDLEUP = 64;
        public const uint MOUSEEVENTF_WHEEL = 2048;
        public const uint MOUSEEVENTF_XDOWN = 128;
        public const uint MOUSEEVENTF_XUP = 256;
        public const uint MOUSEEVENTF_ABSOLUTE = 0x8000;
    }

    /// <summary>
    /// Virtual key codes (subset of common keys)
    /// </summary>
    public static class VirtualKeyCodes
    {
        public const ushort VK_LBUTTON = 0x01;
        public const ushort VK_RBUTTON = 0x02;
        public const ushort VK_CANCEL = 0x03;
        public const ushort VK_MBUTTON = 0x04;
        public const ushort VK_BACK = 0x08;
        public const ushort VK_TAB = 0x09;
        public const ushort VK_CLEAR = 0x0C;
        public const ushort VK_RETURN = 0x0D;
        public const ushort VK_SHIFT = 0x10;
        public const ushort VK_CONTROL = 0x11;
        public const ushort VK_MENU = 0x12;      // Alt key
        public const ushort VK_PAUSE = 0x13;
        public const ushort VK_CAPITAL = 0x14;   // Caps Lock
        public const ushort VK_ESCAPE = 0x1B;
        public const ushort VK_SPACE = 0x20;
        public const ushort VK_PRIOR = 0x21;     // Page Up
        public const ushort VK_NEXT = 0x22;      // Page Down
        public const ushort VK_END = 0x23;
        public const ushort VK_HOME = 0x24;
        public const ushort VK_LEFT = 0x25;
        public const ushort VK_UP = 0x26;
        public const ushort VK_RIGHT = 0x27;
        public const ushort VK_DOWN = 0x28;
        public const ushort VK_SELECT = 0x29;
        public const ushort VK_PRINT = 0x2A;
        public const ushort VK_EXECUTE = 0x2B;
        public const ushort VK_SNAPSHOT = 0x2C;  // Print Screen
        public const ushort VK_INSERT = 0x2D;
        public const ushort VK_DELETE = 0x2E;
        public const ushort VK_HELP = 0x2F;
        public const ushort VK_0 = 0x30;
        public const ushort VK_1 = 0x31;
        public const ushort VK_2 = 0x32;
        public const ushort VK_3 = 0x33;
        public const ushort VK_4 = 0x34;
        public const ushort VK_5 = 0x35;
        public const ushort VK_6 = 0x36;
        public const ushort VK_7 = 0x37;
        public const ushort VK_8 = 0x38;
        public const ushort VK_9 = 0x39;
        public const ushort VK_A = 0x41;
        public const ushort VK_B = 0x42;
        public const ushort VK_C = 0x43;
        public const ushort VK_D = 0x44;
        public const ushort VK_E = 0x45;
        public const ushort VK_F = 0x46;
        public const ushort VK_G = 0x47;
        public const ushort VK_H = 0x48;
        public const ushort VK_I = 0x49;
        public const ushort VK_J = 0x4A;
        public const ushort VK_K = 0x4B;
        public const ushort VK_L = 0x4C;
        public const ushort VK_M = 0x4D;
        public const ushort VK_N = 0x4E;
        public const ushort VK_O = 0x4F;
        public const ushort VK_P = 0x50;
        public const ushort VK_Q = 0x51;
        public const ushort VK_R = 0x52;
        public const ushort VK_S = 0x53;
        public const ushort VK_T = 0x54;
        public const ushort VK_U = 0x55;
        public const ushort VK_V = 0x56;
        public const ushort VK_W = 0x57;
        public const ushort VK_X = 0x58;
        public const ushort VK_Y = 0x59;
        public const ushort VK_Z = 0x5A;
        public const ushort VK_LWIN = 0x5B;
        public const ushort VK_RWIN = 0x5C;
        public const ushort VK_APPS = 0x5D;
        public const ushort VK_NUMPAD0 = 0x60;
        public const ushort VK_NUMPAD1 = 0x61;
        public const ushort VK_NUMPAD2 = 0x62;
        public const ushort VK_NUMPAD3 = 0x63;
        public const ushort VK_NUMPAD4 = 0x64;
        public const ushort VK_NUMPAD5 = 0x65;
        public const ushort VK_NUMPAD6 = 0x66;
        public const ushort VK_NUMPAD7 = 0x67;
        public const ushort VK_NUMPAD8 = 0x68;
        public const ushort VK_NUMPAD9 = 0x69;
        public const ushort VK_MULTIPLY = 0x6A;
        public const ushort VK_ADD = 0x6B;
        public const ushort VK_SUBTRACT = 0x6D;
        public const ushort VK_DECIMAL = 0x6E;
        public const ushort VK_DIVIDE = 0x6F;
        public const ushort VK_F1 = 0x70;
        public const ushort VK_F2 = 0x71;
        public const ushort VK_F3 = 0x72;
        public const ushort VK_F4 = 0x73;
        public const ushort VK_F5 = 0x74;
        public const ushort VK_F6 = 0x75;
        public const ushort VK_F7 = 0x76;
        public const ushort VK_F8 = 0x77;
        public const ushort VK_F9 = 0x78;
        public const ushort VK_F10 = 0x79;
        public const ushort VK_F11 = 0x7A;
        public const ushort VK_F12 = 0x7B;
        public const ushort VK_LSHIFT = 0xA0;
        public const ushort VK_RSHIFT = 0xA1;
        public const ushort VK_LCONTROL = 0xA2;
        public const ushort VK_RCONTROL = 0xA3;
        public const ushort VK_LMENU = 0xA4;    // Left Alt
        public const ushort VK_RMENU = 0xA5;    // Right Alt
        public const ushort VK_SEMICOLON = 0xBA;
        public const ushort VK_PLUS = 0xBB;
        public const ushort VK_COMMA = 0xBC;
        public const ushort VK_MINUS = 0xBD;
        public const ushort VK_PERIOD = 0xBE;
        public const ushort VK_SLASH = 0xBF;
        public const ushort VK_BACKTICK = 0xC0;
        public const ushort VK_LBRACKET = 0xDB;
        public const ushort VK_BACKSLASH = 0xDC;
        public const ushort VK_RBRACKET = 0xDD;
        public const ushort VK_QUOTE = 0xDE;
    }

    /// <summary>
    /// Windows input simulator using SendInput API
    /// </summary>
    public class WindowsInputSimulator : IDisposable
    {
        private readonly ILogger<WindowsInputSimulator>? _logger;

        public WindowsInputSimulator(ILogger<WindowsInputSimulator>? logger = null)
        {
            _logger = logger;
        }

        /// <summary>
        /// Send keyboard key down event
        /// </summary>
        public bool KeyDown(ushort virtualKey)
        {
            try
            {
                var scanCode = (ushort)WindowsInputApi.MapVirtualKey(virtualKey, WindowsInputApi.MAPVK_VK_TO_SCAN);
                var input = new INPUT
                {
                    type = InputType.INPUT_KEYBOARD,
                    ki = new KEYBDINPUT
                    {
                        wVk = virtualKey,
                        wScan = scanCode,
                        dwFlags = KeyEventFlags.KEYEVENTF_KEYDOWN,
                        time = 0,
                        dwExtraInfo = UIntPtr.Zero
                    }
                };

                var result = WindowsInputApi.SendInput(1, new[] { input }, Marshal.SizeOf<INPUT>());
                _logger?.LogDebug("KeyDown: VK={VirtualKey}, Scan={ScanCode}, Result={Result}", virtualKey, scanCode, result);
                return result == 1;
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, "KeyDown failed for VK={VirtualKey}", virtualKey);
                return false;
            }
        }

        /// <summary>
        /// Send keyboard key up event
        /// </summary>
        public bool KeyUp(ushort virtualKey)
        {
            try
            {
                var scanCode = (ushort)WindowsInputApi.MapVirtualKey(virtualKey, WindowsInputApi.MAPVK_VK_TO_SCAN);
                var input = new INPUT
                {
                    type = InputType.INPUT_KEYBOARD,
                    ki = new KEYBDINPUT
                    {
                        wVk = virtualKey,
                        wScan = scanCode,
                        dwFlags = KeyEventFlags.KEYEVENTF_KEYUP,
                        time = 0,
                        dwExtraInfo = UIntPtr.Zero
                    }
                };

                var result = WindowsInputApi.SendInput(1, new[] { input }, Marshal.SizeOf<INPUT>());
                _logger?.LogDebug("KeyUp: VK={VirtualKey}, Scan={ScanCode}, Result={Result}", virtualKey, scanCode, result);
                return result == 1;
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, "KeyUp failed for VK={VirtualKey}", virtualKey);
                return false;
            }
        }

        /// <summary>
        /// Move mouse to absolute position
        /// </summary>
        public bool MouseMoveTo(int x, int y)
        {
            try
            {
                var result = WindowsInputApi.SetCursorPos(x, y);
                _logger?.LogDebug("MouseMoveTo: ({X}, {Y}), Result={Result}", x, y, result);
                return result;
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, "MouseMoveTo failed to ({X}, {Y})", x, y);
                return false;
            }
        }

        /// <summary>
        /// Get current mouse position
        /// </summary>
        public (int X, int Y) GetMousePosition()
        {
            try
            {
                var success = WindowsInputApi.GetCursorPos(out var point);
                if (success)
                {
                    _logger?.LogDebug("GetMousePosition: ({X}, {Y})", point.x, point.y);
                    return (point.x, point.y);
                }
                return (0, 0);
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, "GetMousePosition failed");
                return (0, 0);
            }
        }

        /// <summary>
        /// Mouse left button click
        /// </summary>
        public bool LeftClick()
        {
            try
            {
                var inputs = new[]
                {
                    new INPUT
                    {
                        type = InputType.INPUT_MOUSE,
                        mi = new MOUSEINPUT
                        {
                            dx = 0,
                            dy = 0,
                            mouseData = 0,
                            dwFlags = MouseEventFlags.MOUSEEVENTF_LEFTDOWN,
                            time = 0,
                            dwExtraInfo = UIntPtr.Zero
                        }
                    },
                    new INPUT
                    {
                        type = InputType.INPUT_MOUSE,
                        mi = new MOUSEINPUT
                        {
                            dx = 0,
                            dy = 0,
                            mouseData = 0,
                            dwFlags = MouseEventFlags.MOUSEEVENTF_LEFTUP,
                            time = 0,
                            dwExtraInfo = UIntPtr.Zero
                        }
                    }
                };

                var result = WindowsInputApi.SendInput(2, inputs, Marshal.SizeOf<INPUT>());
                _logger?.LogDebug("LeftClick: Result={Result}", result);
                return result == 2;
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, "LeftClick failed");
                return false;
            }
        }

        /// <summary>
        /// Mouse right button click
        /// </summary>
        public bool RightClick()
        {
            try
            {
                var inputs = new[]
                {
                    new INPUT
                    {
                        type = InputType.INPUT_MOUSE,
                        mi = new MOUSEINPUT
                        {
                            dx = 0,
                            dy = 0,
                            mouseData = 0,
                            dwFlags = MouseEventFlags.MOUSEEVENTF_RIGHTDOWN,
                            time = 0,
                            dwExtraInfo = UIntPtr.Zero
                        }
                    },
                    new INPUT
                    {
                        type = InputType.INPUT_MOUSE,
                        mi = new MOUSEINPUT
                        {
                            dx = 0,
                            dy = 0,
                            mouseData = 0,
                            dwFlags = MouseEventFlags.MOUSEEVENTF_RIGHTUP,
                            time = 0,
                            dwExtraInfo = UIntPtr.Zero
                        }
                    }
                };

                var result = WindowsInputApi.SendInput(2, inputs, Marshal.SizeOf<INPUT>());
                _logger?.LogDebug("RightClick: Result={Result}", result);
                return result == 2;
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, "RightClick failed");
                return false;
            }
        }

        /// <summary>
        /// Mouse middle button click
        /// </summary>
        public bool MiddleClick()
        {
            try
            {
                var inputs = new[]
                {
                    new INPUT
                    {
                        type = InputType.INPUT_MOUSE,
                        mi = new MOUSEINPUT
                        {
                            dx = 0,
                            dy = 0,
                            mouseData = 0,
                            dwFlags = MouseEventFlags.MOUSEEVENTF_MIDDLEDOWN,
                            time = 0,
                            dwExtraInfo = UIntPtr.Zero
                        }
                    },
                    new INPUT
                    {
                        type = InputType.INPUT_MOUSE,
                        mi = new MOUSEINPUT
                        {
                            dx = 0,
                            dy = 0,
                            mouseData = 0,
                            dwFlags = MouseEventFlags.MOUSEEVENTF_MIDDLEUP,
                            time = 0,
                            dwExtraInfo = UIntPtr.Zero
                        }
                    }
                };

                var result = WindowsInputApi.SendInput(2, inputs, Marshal.SizeOf<INPUT>());
                _logger?.LogDebug("MiddleClick: Result={Result}", result);
                return result == 2;
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, "MiddleClick failed");
                return false;
            }
        }

        /// <summary>
        /// Mouse wheel scroll
        /// </summary>
        public bool Scroll(int delta)
        {
            try
            {
                var input = new INPUT
                {
                    type = InputType.INPUT_MOUSE,
                    mi = new MOUSEINPUT
                    {
                        dx = 0,
                        dy = 0,
                        mouseData = (uint)(delta * 120), // Standard wheel delta is 120
                        dwFlags = MouseEventFlags.MOUSEEVENTF_WHEEL,
                        time = 0,
                        dwExtraInfo = UIntPtr.Zero
                    }
                };

                var result = WindowsInputApi.SendInput(1, new[] { input }, Marshal.SizeOf<INPUT>());
                _logger?.LogDebug("Scroll: Delta={Delta}, Result={Result}", delta, result);
                return result == 1;
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, "Scroll failed with delta={Delta}", delta);
                return false;
            }
        }

        public void Dispose()
        {
            // No resources to dispose
        }
    }
}
