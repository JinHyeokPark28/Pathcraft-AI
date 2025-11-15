using System;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;
using PathcraftAI.Overlay;

namespace PathcraftAI.UI
{
    public partial class MainWindow : Window
    {
        private OverlayWindow? _overlay;

        private const int HOTKEY_ID_TOGGLE_OVERLAY = 9001;  // Ctrl+F8
        private const int HOTKEY_ID_CLICKTHROUGH = 9002;  // Ctrl+F9
        private const uint MOD_CONTROL = 0x0002;
        private const uint VK_F8 = 0x77;
        private const uint VK_F9 = 0x78;

        public MainWindow()
        {
            InitializeComponent();
            // 이 시점엔 HWND가 아직 없음. 핫키 등록 금지.
            SourceInitialized += OnSourceInitialized;
        }

        private void OnSourceInitialized(object? sender, EventArgs e)
        {
            var hwnd = new WindowInteropHelper(this).Handle;
            var src = HwndSource.FromHwnd(hwnd);
            src.AddHook(WndProc);

            // 등록 실패하면 바로 알려주기
            if (!RegisterHotKey(hwnd, HOTKEY_ID_TOGGLE_OVERLAY, MOD_CONTROL, VK_F8))
                MessageBox.Show("Ctrl+F8 핫키 등록 실패", "Hotkey", MessageBoxButton.OK, MessageBoxImage.Warning);
            if (!RegisterHotKey(hwnd, HOTKEY_ID_CLICKTHROUGH, MOD_CONTROL, VK_F9))
                MessageBox.Show("Ctrl+F9 핫키 등록 실패", "Hotkey", MessageBoxButton.OK, MessageBoxImage.Warning);
        }

        protected override void OnClosed(EventArgs e)
        {
            var hwnd = new WindowInteropHelper(this).Handle;
            UnregisterHotKey(hwnd, HOTKEY_ID_TOGGLE_OVERLAY);
            UnregisterHotKey(hwnd, HOTKEY_ID_CLICKTHROUGH);
            base.OnClosed(e);
        }

        private nint WndProc(nint hwnd, int msg, nint wParam, nint lParam, ref bool handled)
        {
            const int WM_HOTKEY = 0x0312;

            if (msg == WM_HOTKEY)
            {
                int id = wParam.ToInt32();
                if (id == HOTKEY_ID_TOGGLE_OVERLAY)
                {
                    ToggleOverlay();
                    handled = true;
                }
                else if (id == HOTKEY_ID_CLICKTHROUGH)
                {
                    if (_overlay != null && _overlay.IsVisible)
                        _overlay.ToggleClickThrough();
                    handled = true;
                }
            }
            return nint.Zero;
        }

        private void ToggleOverlay()
        {
            if (_overlay == null || !_overlay.IsVisible)
            {
                _overlay = new OverlayWindow();
                _overlay.Show();
            }
            else
            {
                _overlay.Close();
                _overlay = null;
            }
        }

        // 수동 버튼(선택사항)
        private void ShowOverlay_Click(object sender, RoutedEventArgs e) => ToggleOverlay();

        [DllImport("user32.dll")] private static extern bool RegisterHotKey(nint hWnd, int id, uint fsModifiers, uint vk);
        [DllImport("user32.dll")] private static extern bool UnregisterHotKey(nint hWnd, int id);
    }
}
