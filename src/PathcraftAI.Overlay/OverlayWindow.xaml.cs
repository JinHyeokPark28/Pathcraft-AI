using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Threading;
using PathcraftAI.Overlay.Services; // BuildSnapshotLoader (복사본)
using PathcraftAI.Core.Models;      // BuildSnapshot/BuildModel

namespace PathcraftAI.Overlay
{
    public partial class OverlayWindow : Window
    {
        private readonly OverlayViewModel _vm = new();
        private readonly DispatcherTimer _timer;
        public bool IsClickThrough { get; private set; } = true;

        public OverlayWindow()
        {
            InitializeComponent();
            DataContext = _vm;

            Topmost = true;
            ShowActivated = false;
            Focusable = false;

            KeyDown += OnKeyDown;

            // 핸들 생긴 뒤 클릭-스루 적용
            SourceInitialized += (_, __) =>
            {
                var hwnd = new WindowInteropHelper(this).Handle;
                EnableClickThrough(hwnd, IsClickThrough);
            };

            _timer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
            _timer.Tick += (_, __) => TickUpdate();
            _timer.Start();
        }

        private void Close_Click(object sender, RoutedEventArgs e) => Close();

        private void OnKeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Escape) Close();
        }

        public void ToggleClickThrough()
        {
            IsClickThrough = !IsClickThrough;
            var hwnd = new WindowInteropHelper(this).Handle;
            EnableClickThrough(hwnd, IsClickThrough);
        }

        private void TickUpdate()
        {
            try
            {
                // PathCache를 사용하여 반복적인 탐색 방지
                var json = PathcraftAI.Core.Utils.PathCache.GetBuildOutputPath();
                if (File.Exists(json))
                {
                    var snap = BuildSnapshotLoader.TryLoad(json);
                    if (snap != null)
                    {
                        _vm.CharacterName = $"캐릭터: {snap.CharacterName}";
                        _vm.ClassAsc = snap.ClassAscendancy;
                        _vm.DpsText = $"DPS: {snap.Dps:N0}";
                        _vm.EhpText = $"EHP: {snap.Ehp:N0}";
                        _vm.ResText = $"Res: {snap.ResistLine}";
                    }
                }
            }
            catch
            {
                // 오버레이는 절대 죽지 않는다. 조용히 무시.
            }
        }

        // 64비트 안전한 스타일 변경
        private static void EnableClickThrough(nint hwnd, bool enable)
        {
            const int GWL_EXSTYLE = -20;
            const int WS_EX_TRANSPARENT = 0x00000020;
            const int WS_EX_LAYERED = 0x00080000;

            nint exPtr = GetWindowLongPtr(hwnd, GWL_EXSTYLE);
            int ex = unchecked((int)exPtr);

            if (enable) ex |= (WS_EX_LAYERED | WS_EX_TRANSPARENT);
            else ex &= ~WS_EX_TRANSPARENT;

            SetWindowLongPtr(hwnd, GWL_EXSTYLE, (nint)ex);
        }

        [DllImport("user32.dll", EntryPoint = "GetWindowLongPtrW")]
        private static extern nint GetWindowLongPtr(nint hWnd, int nIndex);

        [DllImport("user32.dll", EntryPoint = "SetWindowLongPtrW")]
        private static extern nint SetWindowLongPtr(nint hWnd, int nIndex, nint dwNewLong);
    }
}
