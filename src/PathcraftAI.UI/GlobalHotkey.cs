using System;
using System.Runtime.InteropServices;
using System.Windows.Input;
using System.Windows.Interop;

namespace PathcraftAI.UI
{
    /// <summary>
    /// Global hotkey manager for Windows
    /// </summary>
    public class GlobalHotkey : IDisposable
    {
        private const int WM_HOTKEY = 0x0312;

        [DllImport("user32.dll")]
        private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

        [DllImport("user32.dll")]
        private static extern bool UnregisterHotKey(IntPtr hWnd, int id);

        private readonly int _id;
        private readonly IntPtr _handle;
        private bool _disposed = false;

        public event EventHandler? HotkeyPressed;

        public GlobalHotkey(Key key, KeyModifier modifiers, IntPtr windowHandle)
        {
            _id = GetHashCode();
            _handle = windowHandle;

            uint modifierFlags = (uint)modifiers;
            uint vk = (uint)KeyInterop.VirtualKeyFromKey(key);

            if (!RegisterHotKey(_handle, _id, modifierFlags, vk))
            {
                throw new InvalidOperationException($"Failed to register hotkey: {key} with modifiers {modifiers}");
            }

            ComponentDispatcher.ThreadFilterMessage += ThreadFilterMessage;
        }

        private void ThreadFilterMessage(ref MSG msg, ref bool handled)
        {
            if (!handled && msg.message == WM_HOTKEY && (int)msg.wParam == _id)
            {
                HotkeyPressed?.Invoke(this, EventArgs.Empty);
                handled = true;
            }
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        protected virtual void Dispose(bool disposing)
        {
            if (!_disposed)
            {
                if (disposing)
                {
                    ComponentDispatcher.ThreadFilterMessage -= ThreadFilterMessage;
                }

                UnregisterHotKey(_handle, _id);
                _disposed = true;
            }
        }

        ~GlobalHotkey()
        {
            Dispose(false);
        }
    }

    [Flags]
    public enum KeyModifier : uint
    {
        None = 0,
        Alt = 1,
        Control = 2,
        Shift = 4,
        Win = 8
    }
}
