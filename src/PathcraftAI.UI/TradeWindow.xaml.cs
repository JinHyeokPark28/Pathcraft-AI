using System;
using System.Diagnostics;
using System.Windows;
using Microsoft.Web.WebView2.Core;

namespace PathcraftAI.UI
{
    public partial class TradeWindow : Window
    {
        private string? _currentUrl;
        private string _league;

        public TradeWindow(string league = "Keepers")
        {
            InitializeComponent();
            _league = league;
            InitializeWebView();
        }

        private async void InitializeWebView()
        {
            try
            {
                // WebView2 환경 초기화
                var env = await CoreWebView2Environment.CreateAsync();
                await TradeWebView.EnsureCoreWebView2Async(env);

                // 이벤트 핸들러 등록
                TradeWebView.NavigationStarting += TradeWebView_NavigationStarting;
                TradeWebView.NavigationCompleted += TradeWebView_NavigationCompleted;
                TradeWebView.SourceChanged += TradeWebView_SourceChanged;

                StatusText.Text = "WebView2 초기화 완료";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"WebView2 초기화 실패:\n{ex.Message}\n\nWebView2 Runtime이 설치되어 있는지 확인해주세요.",
                    "오류", MessageBoxButton.OK, MessageBoxImage.Error);
                Close();
            }
        }

        /// <summary>
        /// POE Trade 검색 URL로 이동
        /// </summary>
        public void NavigateToSearch(string itemName, string? itemType = null,
            int? links = null, string? influence = null, bool? corrupted = null,
            string? keystone = null, bool? foulborn = null)
        {
            // POE Trade 검색 URL 생성
            string searchUrl = $"https://www.pathofexile.com/trade/search/{_league}";

            // 기본 검색어가 있으면 직접 이동
            if (!string.IsNullOrEmpty(itemName))
            {
                // 간단한 이름 검색 URL
                // 복잡한 필터는 JSON query 필요하므로 기본 페이지로 이동 후 사용자가 검색
                TradeWebView.Source = new Uri(searchUrl);
                StatusText.Text = $"'{itemName}' 검색 준비 중...";
            }
            else
            {
                TradeWebView.Source = new Uri(searchUrl);
            }
        }

        /// <summary>
        /// 특정 POE Trade URL로 직접 이동
        /// </summary>
        public void NavigateToUrl(string url)
        {
            if (Uri.TryCreate(url, UriKind.Absolute, out Uri? uri))
            {
                TradeWebView.Source = uri;
            }
        }

        /// <summary>
        /// POE Trade API 검색 결과 URL로 이동 (검색 ID 사용)
        /// </summary>
        public void NavigateToSearchResult(string searchId)
        {
            string resultUrl = $"https://www.pathofexile.com/trade/search/{_league}/{searchId}";
            TradeWebView.Source = new Uri(resultUrl);
        }

        private void TradeWebView_NavigationStarting(object? sender, CoreWebView2NavigationStartingEventArgs e)
        {
            StatusText.Text = "로딩 중...";
        }

        private void TradeWebView_NavigationCompleted(object? sender, CoreWebView2NavigationCompletedEventArgs e)
        {
            if (e.IsSuccess)
            {
                StatusText.Text = "로드 완료";
            }
            else
            {
                StatusText.Text = $"로드 실패: {e.WebErrorStatus}";
            }
        }

        private void TradeWebView_SourceChanged(object? sender, CoreWebView2SourceChangedEventArgs e)
        {
            _currentUrl = TradeWebView.Source?.ToString();
            UrlTextBox.Text = _currentUrl ?? "";
        }

        private void BackButton_Click(object sender, RoutedEventArgs e)
        {
            if (TradeWebView.CanGoBack)
            {
                TradeWebView.GoBack();
            }
        }

        private void ForwardButton_Click(object sender, RoutedEventArgs e)
        {
            if (TradeWebView.CanGoForward)
            {
                TradeWebView.GoForward();
            }
        }

        private void RefreshButton_Click(object sender, RoutedEventArgs e)
        {
            TradeWebView.Reload();
        }

        private async void CopyWhisperButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // POE Trade 페이지에서 선택된 아이템의 귓속말 복사
                // JavaScript를 실행하여 클립보드에 복사된 귓속말을 가져옴
                string script = @"
                    (function() {
                        // 가장 최근에 복사된 귓속말 버튼 클릭 시뮬레이션
                        var whisperBtn = document.querySelector('.whisper-btn');
                        if (whisperBtn) {
                            whisperBtn.click();
                            return '귓속말이 클립보드에 복사되었습니다.';
                        }
                        return '귓속말 버튼을 찾을 수 없습니다. 아이템을 선택해주세요.';
                    })();
                ";

                string result = await TradeWebView.ExecuteScriptAsync(script);
                StatusText.Text = result.Trim('"');
            }
            catch (Exception ex)
            {
                StatusText.Text = $"귓속말 복사 실패: {ex.Message}";
            }
        }

        private void OpenInBrowserButton_Click(object sender, RoutedEventArgs e)
        {
            if (!string.IsNullOrEmpty(_currentUrl))
            {
                try
                {
                    Process.Start(new ProcessStartInfo
                    {
                        FileName = _currentUrl,
                        UseShellExecute = true
                    });
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"브라우저 열기 실패:\n{ex.Message}", "오류",
                        MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        /// <summary>
        /// 현재 리그 변경
        /// </summary>
        public void SetLeague(string league)
        {
            _league = league;
        }
    }
}
