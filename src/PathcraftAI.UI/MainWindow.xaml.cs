using System;
using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using Newtonsoft.Json.Linq;

namespace PathcraftAI.UI
{
    public partial class MainWindow : Window
    {
        private readonly string _pythonPath;
        private readonly string _recommendationScriptPath;
        private readonly string _oauthScriptPath;
        private readonly string _compareBuildScriptPath;
        private readonly string _upgradePathScriptPath;
        private readonly string _passiveTreeScriptPath;
        private readonly string _tokenFilePath;
        private bool _isLoading = false;
        private string _currentLeague = "Keepers";
        private string _currentPhase = "Mid-Season";
        private JObject? _poeAccountData = null;
        private bool _isPOEConnected = false;
        private string? _currentPOBUrl = null;
        private int _currentBudget = 100; // Default budget in chaos orbs
        private GlobalHotkey? _hideoutHotkey;

        public MainWindow()
        {
            InitializeComponent();

            // F5 단축키 등록 (하이드아웃 이동)
            Loaded += (s, e) => RegisterHotkeys();
            Closed += (s, e) => UnregisterHotkeys();

            // Python 경로 설정
            var projectRoot = Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", ".."));
            var parserDir = Path.Combine(projectRoot, "src", "PathcraftAI.Parser");
            _pythonPath = Path.Combine(parserDir, ".venv", "Scripts", "python.exe");
            _recommendationScriptPath = Path.Combine(parserDir, "auto_recommendation_engine.py");
            _oauthScriptPath = Path.Combine(parserDir, "test_oauth.py");
            _compareBuildScriptPath = Path.Combine(parserDir, "compare_build.py");
            _upgradePathScriptPath = Path.Combine(parserDir, "upgrade_path.py");
            _passiveTreeScriptPath = Path.Combine(parserDir, "passive_tree_analyzer.py");
            _tokenFilePath = Path.Combine(parserDir, "poe_token.json");

            // 경로 확인
            if (!File.Exists(_pythonPath))
            {
                MessageBox.Show($"Python executable not found:\n{_pythonPath}\n\nPlease set up the virtual environment first.",
                    "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }

            if (!File.Exists(_recommendationScriptPath))
            {
                MessageBox.Show($"Recommendation script not found:\n{_recommendationScriptPath}",
                    "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }

            // 저장된 토큰 확인
            CheckPOEConnection();

            // 앱 시작 시 자동으로 추천 로드
            _ = LoadRecommendations();
        }

        private async void RefreshButton_Click(object sender, RoutedEventArgs e)
        {
            await LoadRecommendations();
        }

        private async Task LoadRecommendations()
        {
            if (_isLoading) return;

            try
            {
                _isLoading = true;
                RefreshButton.IsEnabled = false;
                RefreshButton.Content = "Loading...";
                PlaceholderText.Visibility = Visibility.Collapsed;
                ResultsPanel.Children.Clear();

                // Loading indicator
                var loadingText = new TextBlock
                {
                    Text = "Loading build recommendations...",
                    FontSize = 14,
                    Foreground = new SolidColorBrush(Color.FromRgb(175, 96, 37)),
                    HorizontalAlignment = HorizontalAlignment.Center,
                    Margin = new Thickness(0, 100, 0, 0)
                };
                ResultsPanel.Children.Add(loadingText);

                // Python 프로세스 실행
                var result = await System.Threading.Tasks.Task.Run(() => ExecuteRecommendationEngine());

                // 결과 표시
                ResultsPanel.Children.Clear();
                DisplayRecommendations(result);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to load recommendations:\n{ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                PlaceholderText.Visibility = Visibility.Visible;
            }
            finally
            {
                _isLoading = false;
                RefreshButton.IsEnabled = true;
                RefreshButton.Content = "Refresh Recommendations";
            }
        }

        private string ExecuteRecommendationEngine()
        {
            var psi = new ProcessStartInfo
            {
                FileName = _pythonPath,
                Arguments = $"\"{_recommendationScriptPath}\" --json-output",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                StandardOutputEncoding = System.Text.Encoding.UTF8
            };

            // Enable UTF-8 mode for Python
            psi.Environment["PYTHONUTF8"] = "1";

            // API 키 환경 변수로 전달
            psi.Environment["YOUTUBE_API_KEY"] = "AIzaSyBDC0li3oQsLwk6XPauI7wWL6QND9WUqGo";

            using var process = Process.Start(psi);
            if (process == null)
                throw new Exception("Failed to start Python process");

            var output = process.StandardOutput.ReadToEnd();
            var error = process.StandardError.ReadToEnd();
            process.WaitForExit();

            if (process.ExitCode != 0)
            {
                throw new Exception($"Recommendation engine error:\n{error}");
            }

            return output;
        }

        private void DisplayRecommendations(string jsonOutput)
        {
            try
            {
                // JSON이 비어있는지 확인
                if (string.IsNullOrWhiteSpace(jsonOutput))
                {
                    ShowNoRecommendations();
                    return;
                }

                // JSON 부분만 추출 (첫 번째 { 부터 마지막 } 까지)
                var jsonStart = jsonOutput.IndexOf('{');
                var jsonEnd = jsonOutput.LastIndexOf('}');

                if (jsonStart == -1 || jsonEnd == -1 || jsonEnd <= jsonStart)
                {
                    ShowNoRecommendations();
                    return;
                }

                var jsonString = jsonOutput.Substring(jsonStart, jsonEnd - jsonStart + 1);
                var data = JObject.Parse(jsonString);

                // 리그 정보 업데이트
                _currentLeague = data["league"]?.ToString() ?? "Keepers";
                _currentPhase = FormatLeaguePhase(data["league_phase"]?.ToString() ?? "mid");

                LeagueNameText.Text = $"Current League: {_currentLeague}";
                LeaguePhaseText.Text = $"League Phase: {_currentPhase}";

                // 사용자 빌드 정보 표시
                DisplayUserBuild(data["user_build"] as JObject);

                var recommendations = data["recommendations"] as JArray;

                if (recommendations == null || recommendations.Count == 0)
                {
                    ShowNoRecommendations();
                    return;
                }

                // 각 추천 카테고리 표시
                foreach (var rec in recommendations)
                {
                    var category = rec["category"]?.ToString();
                    var title = rec["title"]?.ToString();
                    var subtitle = rec["subtitle"]?.ToString();
                    var builds = rec["builds"] as JArray;

                    if (builds == null || builds.Count == 0)
                        continue;

                    // 카테고리 헤더
                    var categoryHeader = new TextBlock
                    {
                        Text = title,
                        FontSize = 16,
                        FontWeight = FontWeights.SemiBold,
                        Margin = new Thickness(0, 16, 0, 4)
                    };
                    ResultsPanel.Children.Add(categoryHeader);

                    var categorySubtitle = new TextBlock
                    {
                        Text = subtitle,
                        FontSize = 12,
                        Foreground = new SolidColorBrush(Color.FromRgb(180, 180, 180)),
                        Margin = new Thickness(0, 0, 0, 12)
                    };
                    ResultsPanel.Children.Add(categorySubtitle);

                    // 빌드 카드들
                    foreach (var build in builds)
                    {
                        var buildCard = CreateRecommendationCard(build as JObject, category);
                        ResultsPanel.Children.Add(buildCard);
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to parse recommendations:\n{ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                ShowNoRecommendations();
            }
        }

        private void DisplayUserBuild(JObject? userBuild)
        {
            if (userBuild == null)
            {
                // 빌드 데이터가 없으면 섹션 숨김
                YourBuildSection.Visibility = Visibility.Collapsed;
                BuildComparisonSection.Visibility = Visibility.Collapsed;
                return;
            }

            // 빌드 데이터가 있으면 섹션 표시
            YourBuildSection.Visibility = Visibility.Visible;

            // 캐릭터 정보
            var characterName = userBuild["character_name"]?.ToString() ?? "-";
            var characterClass = userBuild["class"]?.ToString() ?? "-";
            var level = userBuild["level"]?.ToString() ?? "-";
            BuildCharacterName.Text = $"Character: {characterName} (Lv{level} {characterClass})";

            // 빌드 타입
            var buildType = userBuild["build_type"]?.ToString() ?? "-";
            BuildType.Text = $"Build Type: {buildType}";

            // 메인 스킬
            var mainSkill = userBuild["main_skill"]?.ToString();
            BuildMainSkill.Text = $"Main Skill: {mainSkill ?? "Unknown"}";

            // 유니크 아이템 개수
            var uniqueItems = userBuild["unique_items"] as JArray;
            int uniqueCount = uniqueItems?.Count ?? 0;
            BuildUniqueCount.Text = $"Unique Items: {uniqueCount}";

            // 총 가치
            var totalValue = userBuild["total_unique_value"]?.ToObject<double>() ?? 0.0;
            BuildTotalValue.Text = $"Estimated Value: ~{totalValue:F0}c";

            // 업그레이드 제안
            var upgradeSuggestions = userBuild["upgrade_suggestions"] as JArray;
            if (upgradeSuggestions != null && upgradeSuggestions.Count > 0)
            {
                UpgradeSuggestionsPanel.Visibility = Visibility.Visible;

                var upgradeList = new List<object>();
                foreach (var suggestion in upgradeSuggestions)
                {
                    upgradeList.Add(new
                    {
                        ItemName = suggestion["item_name"]?.ToString() ?? "",
                        ChaosValue = suggestion["chaos_value"]?.ToObject<double>() ?? 0.0,
                        Reason = suggestion["reason"]?.ToString() ?? ""
                    });
                }

                UpgradesList.ItemsSource = upgradeList;
            }
            else
            {
                UpgradeSuggestionsPanel.Visibility = Visibility.Collapsed;
            }

            // POB 링크가 있으면 빌드 비교 로드
            var pobUrl = userBuild["pob_url"]?.ToString();
            if (!string.IsNullOrEmpty(pobUrl) && characterName != "-" && _isPOEConnected)
            {
                _ = LoadBuildComparison(pobUrl, characterName);
            }
            else
            {
                BuildComparisonSection.Visibility = Visibility.Collapsed;
            }
        }

        private string FormatLeaguePhase(string phase)
        {
            return phase switch
            {
                "pre_season" => "Pre-Season (Starting Soon)",
                "early" => "Early League (Week 1)",
                "mid" => "Mid-Season",
                "late" => "Late League (1+ Month)",
                _ => "Active"
            };
        }

        private Border CreateRecommendationCard(JObject? build, string? category)
        {
            if (build == null)
                return new Border();

            var card = new Border
            {
                Background = new SolidColorBrush(Color.FromRgb(50, 50, 50)),
                BorderBrush = new SolidColorBrush(Color.FromRgb(175, 96, 37)),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(4),
                Padding = new Thickness(12),
                Margin = new Thickness(0, 0, 0, 8)
            };

            var stackPanel = new StackPanel();

            // 빌드 이름 추출 (소스에 따라 다름)
            string buildName = ExtractBuildName(build, category);

            // Title
            var title = new TextBlock
            {
                Text = buildName,
                FontSize = 14,
                FontWeight = FontWeights.SemiBold,
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 4)
            };
            stackPanel.Children.Add(title);

            // Build Info (category별로 다른 정보 표시)
            var infoText = BuildInfoText(build, category);
            if (!string.IsNullOrEmpty(infoText))
            {
                var info = new TextBlock
                {
                    Text = infoText,
                    FontSize = 12,
                    Foreground = new SolidColorBrush(Color.FromRgb(180, 180, 180)),
                    Margin = new Thickness(0, 0, 0, 8),
                    TextWrapping = TextWrapping.Wrap
                };
                stackPanel.Children.Add(info);
            }

            card.Child = stackPanel;
            return card;
        }

        private string ExtractBuildName(JObject build, string? category)
        {
            // YouTube 빌드
            if (build["title"] != null)
                return build["title"]?.ToString() ?? "Unknown Build";

            // Ladder/Streamer 빌드
            var charName = build["character_name"]?.ToString();
            var className = build["class"]?.ToString();
            var ascendancy = build["ascendancy_class"]?.ToString();

            if (!string.IsNullOrEmpty(charName))
            {
                if (!string.IsNullOrEmpty(ascendancy))
                    return $"{charName} ({ascendancy})";
                else if (!string.IsNullOrEmpty(className))
                    return $"{charName} ({className})";
                else
                    return charName;
            }

            // poe.ninja 빌드
            if (!string.IsNullOrEmpty(className) && !string.IsNullOrEmpty(ascendancy))
                return $"{ascendancy} {className}";

            return "Unknown Build";
        }

        private string BuildInfoText(JObject build, string? category)
        {
            var infoParts = new List<string>();

            // Streamer 빌드
            if (build["streamer_name"] != null)
            {
                infoParts.Add($"Streamer: {build["streamer_name"]}");
            }

            // Ladder rank
            if (build["rank"] != null)
            {
                infoParts.Add($"Rank #{build["rank"]}");
            }

            // Level
            if (build["level"] != null)
            {
                infoParts.Add($"Lvl {build["level"]}");
            }

            // Popularity (poe.ninja)
            if (build["count"] != null)
            {
                infoParts.Add($"{build["count"]} players");
            }

            // YouTube stats
            if (build["channel"] != null)
            {
                infoParts.Add($"Channel: {build["channel"]}");
            }

            if (build["views"] != null)
            {
                var views = build["views"]?.Value<int>() ?? 0;
                infoParts.Add($"{views:N0} views");
            }

            return string.Join(" | ", infoParts);
        }

        private void ShowNoRecommendations()
        {
            var noResults = new TextBlock
            {
                Text = "No recommendations available.\nPlease check your internet connection or try refreshing.",
                FontSize = 14,
                Foreground = new SolidColorBrush(Color.FromRgb(180, 180, 180)),
                TextWrapping = TextWrapping.Wrap,
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center,
                Margin = new Thickness(0, 100, 0, 0)
            };
            ResultsPanel.Children.Add(noResults);
        }

        private void Settings_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Settings window coming soon!\n\nFeatures:\n- API key management (GPT/Gemini/Claude)\n- Theme selection\n- Premium subscription",
                "Settings", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void Donate_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Support PathcraftAI!\n\nPremium: $2.50/month (removes ads)\n\nThank you for your support!",
                "Donate", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private async void ConnectPOE_Click(object sender, RoutedEventArgs e)
        {
            if (_isPOEConnected)
            {
                // 이미 연결된 경우 - 연결 해제 옵션
                var result = MessageBox.Show(
                    $"Currently connected as: {_poeAccountData?["username"]}\n\nDo you want to disconnect?",
                    "POE Account",
                    MessageBoxButton.YesNo,
                    MessageBoxImage.Question);

                if (result == MessageBoxResult.Yes)
                {
                    DisconnectPOE();
                }
                return;
            }

            // OAuth 인증 시작
            try
            {
                ConnectPOEButton.IsEnabled = false;
                ConnectPOEButton.Content = "Connecting...";

                await System.Threading.Tasks.Task.Run(() => ExecuteOAuthFlow());

                // 토큰 확인
                CheckPOEConnection();

                if (_isPOEConnected)
                {
                    MessageBox.Show($"Successfully connected to POE!\n\nUsername: {_poeAccountData?["username"]}",
                        "Success", MessageBoxButton.OK, MessageBoxImage.Information);

                    // 추천 새로고침 (사용자 캐릭터 기반)
                    await LoadRecommendations();
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to connect POE account:\n{ex.Message}",
                    "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                ConnectPOEButton.IsEnabled = true;
                UpdatePOEButtonState();
            }
        }

        private void CheckPOEConnection()
        {
            try
            {
                if (File.Exists(_tokenFilePath))
                {
                    var tokenJson = File.ReadAllText(_tokenFilePath);
                    _poeAccountData = JObject.Parse(tokenJson);

                    var username = _poeAccountData["username"]?.ToString();
                    if (!string.IsNullOrEmpty(username))
                    {
                        _isPOEConnected = true;
                        POEAccountText.Text = $"Connected: {username}";
                        POEAccountText.Foreground = new SolidColorBrush(Color.FromRgb(100, 200, 100));

                        // 캐릭터 정보 로드
                        LoadCharacterInfo();
                    }
                }
                else
                {
                    _isPOEConnected = false;
                    POEAccountText.Text = "Not connected";
                    POEAccountText.Foreground = new SolidColorBrush(Color.FromRgb(128, 128, 128));
                }

                UpdatePOEButtonState();
            }
            catch
            {
                _isPOEConnected = false;
                POEAccountText.Text = "Not connected";
            }
        }

        private void LoadCharacterInfo()
        {
            try
            {
                // Python 스크립트로 캐릭터 정보 가져오기
                var parserDir = Path.GetDirectoryName(_pythonPath);
                var scriptPath = Path.Combine(parserDir!, "..", "get_characters.py");

                var psi = new ProcessStartInfo
                {
                    FileName = _pythonPath,
                    Arguments = $"-c \"from poe_oauth import load_token, get_user_characters; token = load_token(); chars = get_user_characters(token['access_token'])['characters'] if token else []; print(len(chars))\"",
                    WorkingDirectory = parserDir,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };

                using var process = Process.Start(psi);
                if (process != null)
                {
                    var output = process.StandardOutput.ReadToEnd();
                    process.WaitForExit();

                    if (int.TryParse(output.Trim(), out int charCount) && charCount > 0)
                    {
                        CharacterCountText.Text = $"Total Characters: {charCount}";
                        CharacterInfoPanel.Visibility = Visibility.Visible;

                        // 메인 캐릭터 찾기 (current: true인 캐릭터)
                        FindMainCharacter();
                    }
                }
            }
            catch
            {
                // 캐릭터 정보 로드 실패는 조용히 무시
            }
        }

        private void FindMainCharacter()
        {
            try
            {
                var pythonCode = @"
from poe_oauth import load_token, get_user_characters
token = load_token()
if token:
    chars = get_user_characters(token['access_token'])['characters']
    current = next((c for c in chars if c.get('current')), chars[0] if chars else None)
    if current:
        print(f""{current['name']} Lv{current['level']} {current['class']}"")
";
                var psi = new ProcessStartInfo
                {
                    FileName = _pythonPath,
                    Arguments = $"-c \"{pythonCode}\"",
                    WorkingDirectory = Path.GetDirectoryName(_pythonPath),
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };

                using var process = Process.Start(psi);
                if (process != null)
                {
                    var output = process.StandardOutput.ReadToEnd().Trim();
                    process.WaitForExit();

                    if (!string.IsNullOrEmpty(output) && output != "-")
                    {
                        MainCharacterText.Text = $"Main: {output}";
                    }
                }
            }
            catch
            {
                // 실패 시 무시
            }
        }

        private void UpdatePOEButtonState()
        {
            if (_isPOEConnected)
            {
                ConnectPOEButton.Content = "Disconnect POE";
            }
            else
            {
                ConnectPOEButton.Content = "Connect POE Account";
            }
        }

        private void DisconnectPOE()
        {
            try
            {
                if (File.Exists(_tokenFilePath))
                {
                    File.Delete(_tokenFilePath);
                }

                _isPOEConnected = false;
                _poeAccountData = null;
                POEAccountText.Text = "Not connected";
                POEAccountText.Foreground = new SolidColorBrush(Color.FromRgb(128, 128, 128));
                CharacterInfoPanel.Visibility = Visibility.Collapsed;
                UpdatePOEButtonState();

                MessageBox.Show("Disconnected from POE account.", "Info", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to disconnect:\n{ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void ExecuteOAuthFlow()
        {
            var psi = new ProcessStartInfo
            {
                FileName = _pythonPath,
                Arguments = $"\"{_oauthScriptPath}\"",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = false,  // 브라우저 열기 위해 window 표시
                WorkingDirectory = Path.GetDirectoryName(_oauthScriptPath)
            };

            using var process = Process.Start(psi);
            if (process == null)
                throw new Exception("Failed to start OAuth process");

            var output = process.StandardOutput.ReadToEnd();
            var error = process.StandardError.ReadToEnd();
            process.WaitForExit();

            if (process.ExitCode != 0)
            {
                throw new Exception($"OAuth authentication failed:\n{error}");
            }
        }

        private async Task LoadBuildComparison(string pobUrl, string characterName)
        {
            try
            {
                _currentPOBUrl = pobUrl;

                // Python 스크립트로 비교 데이터 가져오기
                var result = await System.Threading.Tasks.Task.Run(() =>
                    ExecuteBuildComparison(pobUrl, characterName));

                if (string.IsNullOrWhiteSpace(result))
                {
                    BuildComparisonSection.Visibility = Visibility.Collapsed;
                    return;
                }

                // JSON 파싱
                var data = JObject.Parse(result);

                // 에러 체크
                if (data["error"] != null)
                {
                    BuildComparisonSection.Visibility = Visibility.Collapsed;
                    return;
                }

                // 비교 데이터 표시
                DisplayBuildComparison(data);
                BuildComparisonSection.Visibility = Visibility.Visible;

                // 빌드 비교 로드 후 업그레이드 경로 로드
                _ = LoadUpgradePath(pobUrl, characterName, _currentBudget);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Build comparison failed: {ex.Message}");
                BuildComparisonSection.Visibility = Visibility.Collapsed;
            }
        }

        private string ExecuteBuildComparison(string pobUrl, string characterName)
        {
            var psi = new ProcessStartInfo
            {
                FileName = _pythonPath,
                Arguments = $"\"{_compareBuildScriptPath}\" --pob \"{pobUrl}\" --character \"{characterName}\" --json",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                StandardOutputEncoding = System.Text.Encoding.UTF8,
                WorkingDirectory = Path.GetDirectoryName(_compareBuildScriptPath)
            };

            // Enable UTF-8 mode for Python
            psi.Environment["PYTHONUTF8"] = "1";

            using var process = Process.Start(psi);
            if (process == null)
                throw new Exception("Failed to start comparison process");

            var output = process.StandardOutput.ReadToEnd();
            var error = process.StandardError.ReadToEnd();
            process.WaitForExit();

            if (process.ExitCode != 0)
            {
                Debug.WriteLine($"Comparison script error: {error}");
                return string.Empty;
            }

            return output;
        }

        private void DisplayBuildComparison(JObject data)
        {
            // 비교 데이터 바인딩
            var comparison = data["comparison"] as JArray;
            if (comparison != null && comparison.Count > 0)
            {
                var comparisonList = new List<ComparisonRow>();

                foreach (var item in comparison)
                {
                    var stat = item["stat"]?.ToString() ?? "";
                    var current = item["current"]?.ToObject<double>() ?? 0;
                    var target = item["target"]?.ToObject<double>() ?? 0;
                    var gap = item["gap"]?.ToObject<double>() ?? 0;
                    var status = item["status"]?.ToString() ?? "";
                    var unit = item["unit"]?.ToString() ?? "";

                    comparisonList.Add(new ComparisonRow
                    {
                        Stat = stat,
                        CurrentDisplay = FormatStatValue(current, unit),
                        TargetDisplay = FormatStatValue(target, unit),
                        GapDisplay = FormatGapValue(gap, unit),
                        Status = status
                    });
                }

                ComparisonGrid.ItemsSource = comparisonList;
            }

            // Priority Upgrades 표시
            var priorityUpgrades = data["priority_upgrades"] as JArray;
            if (priorityUpgrades != null && priorityUpgrades.Count > 0)
            {
                var upgradeList = new List<PriorityUpgrade>();

                foreach (var upgrade in priorityUpgrades)
                {
                    upgradeList.Add(new PriorityUpgrade
                    {
                        Priority = upgrade["priority"]?.ToObject<int>() ?? 0,
                        Category = upgrade["category"]?.ToString() ?? "",
                        Description = upgrade["description"]?.ToString() ?? "",
                        Suggestion = upgrade["suggestion"]?.ToString() ?? ""
                    });
                }

                PriorityUpgradesList.ItemsSource = upgradeList;
                PriorityUpgradesPanel.Visibility = Visibility.Visible;
            }
            else
            {
                PriorityUpgradesPanel.Visibility = Visibility.Collapsed;
            }
        }

        private string FormatStatValue(double value, string unit)
        {
            if (string.IsNullOrEmpty(unit))
                return value.ToString("N0");

            return $"{value:N0}{unit}";
        }

        private string FormatGapValue(double gap, string unit)
        {
            var sign = gap >= 0 ? "+" : "";

            if (string.IsNullOrEmpty(unit))
                return $"{sign}{gap:N0}";

            return $"{sign}{gap:N0}{unit}";
        }

        private async Task LoadUpgradePath(string pobUrl, string characterName, int budgetChaos)
        {
            try
            {
                // Python 스크립트로 업그레이드 경로 가져오기
                var result = await System.Threading.Tasks.Task.Run(() =>
                    ExecuteUpgradePath(pobUrl, characterName, budgetChaos));

                if (string.IsNullOrWhiteSpace(result))
                {
                    UpgradePathSection.Visibility = Visibility.Collapsed;
                    return;
                }

                // JSON 파싱
                var data = JObject.Parse(result);

                // 에러 체크
                if (data["error"] != null)
                {
                    UpgradePathSection.Visibility = Visibility.Collapsed;
                    return;
                }

                // 업그레이드 경로 표시
                DisplayUpgradePath(data);
                UpgradePathSection.Visibility = Visibility.Visible;

                // 업그레이드 경로 로드 후 패시브 트리 로드
                _ = LoadPassiveTreeRoadmap(pobUrl, characterName);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Upgrade path failed: {ex.Message}");
                UpgradePathSection.Visibility = Visibility.Collapsed;
            }
        }

        private string ExecuteUpgradePath(string pobUrl, string characterName, int budgetChaos)
        {
            var psi = new ProcessStartInfo
            {
                FileName = _pythonPath,
                Arguments = $"\"{_upgradePathScriptPath}\" --pob \"{pobUrl}\" --character \"{characterName}\" --budget {budgetChaos} --json",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                StandardOutputEncoding = System.Text.Encoding.UTF8,
                WorkingDirectory = Path.GetDirectoryName(_upgradePathScriptPath)
            };

            // Enable UTF-8 mode for Python
            psi.Environment["PYTHONUTF8"] = "1";

            using var process = Process.Start(psi);
            if (process == null)
                throw new Exception("Failed to start upgrade path process");

            var output = process.StandardOutput.ReadToEnd();
            var error = process.StandardError.ReadToEnd();
            process.WaitForExit();

            if (process.ExitCode != 0)
            {
                Debug.WriteLine($"Upgrade path script error: {error}");
                return string.Empty;
            }

            return output;
        }

        private void DisplayUpgradePath(JObject data)
        {
            // 예산 및 총 비용 표시
            var budgetChaos = data["budget_chaos"]?.ToObject<int>() ?? 100;
            var totalCost = data["total_cost"]?.ToObject<int>() ?? 0;

            UpgradeBudgetText.Text = $"Budget: {budgetChaos}c";
            UpgradeTotalCostText.Text = $"Total Cost: {totalCost}c";

            // 업그레이드 스텝 표시
            var upgradeSteps = data["upgrade_steps"] as JArray;
            if (upgradeSteps != null && upgradeSteps.Count > 0)
            {
                var stepsList = new List<UpgradeStep>();

                foreach (var step in upgradeSteps)
                {
                    var recommendations = step["recommendations"] as JArray;
                    var recList = new List<string>();

                    if (recommendations != null)
                    {
                        foreach (var rec in recommendations)
                        {
                            recList.Add(rec.ToString());
                        }
                    }

                    stepsList.Add(new UpgradeStep
                    {
                        Step = step["step"]?.ToObject<int>() ?? 0,
                        Priority = step["priority"]?.ToString() ?? "",
                        Title = step["title"]?.ToString() ?? "",
                        CostChaos = step["cost_chaos"]?.ToObject<int>() ?? 0,
                        Description = step["description"]?.ToString() ?? "",
                        Impact = step["impact"]?.ToString() ?? "",
                        Recommendations = recList
                    });
                }

                UpgradeStepsList.ItemsSource = stepsList;
            }
            else
            {
                UpgradePathSection.Visibility = Visibility.Collapsed;
            }
        }

        private async Task LoadPassiveTreeRoadmap(string pobUrl, string characterName)
        {
            try
            {
                // Python 스크립트로 패시브 트리 로드맵 가져오기
                var result = await System.Threading.Tasks.Task.Run(() =>
                    ExecutePassiveTreeAnalyzer(pobUrl, characterName));

                if (string.IsNullOrWhiteSpace(result))
                {
                    PassiveTreeSection.Visibility = Visibility.Collapsed;
                    return;
                }

                // JSON 파싱
                var data = JObject.Parse(result);

                // 에러 체크
                if (data["error"] != null)
                {
                    PassiveTreeSection.Visibility = Visibility.Collapsed;
                    return;
                }

                // 패시브 트리 로드맵 표시
                DisplayPassiveTreeRoadmap(data);
                PassiveTreeSection.Visibility = Visibility.Visible;
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Passive tree roadmap failed: {ex.Message}");
                PassiveTreeSection.Visibility = Visibility.Collapsed;
            }
        }

        private string ExecutePassiveTreeAnalyzer(string pobUrl, string characterName)
        {
            var psi = new ProcessStartInfo
            {
                FileName = _pythonPath,
                Arguments = $"\"{_passiveTreeScriptPath}\" --pob \"{pobUrl}\" --character \"{characterName}\" --json",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                StandardOutputEncoding = System.Text.Encoding.UTF8,
                WorkingDirectory = Path.GetDirectoryName(_passiveTreeScriptPath)
            };

            // Enable UTF-8 mode for Python
            psi.Environment["PYTHONUTF8"] = "1";

            using var process = Process.Start(psi);
            if (process == null)
                throw new Exception("Failed to start passive tree analyzer process");

            var output = process.StandardOutput.ReadToEnd();
            var error = process.StandardError.ReadToEnd();
            process.WaitForExit();

            if (process.ExitCode != 0)
            {
                Debug.WriteLine($"Passive tree analyzer error: {error}");
                return string.Empty;
            }

            return output;
        }

        private void DisplayPassiveTreeRoadmap(JObject data)
        {
            // 레벨 및 포인트 정보 표시
            var currentLevel = data["current_level"]?.ToObject<int>() ?? 1;
            var targetLevel = data["target_level"]?.ToObject<int>() ?? 100;
            var pointsNeeded = data["points_needed"]?.ToObject<int>() ?? 0;

            PassiveCurrentLevelText.Text = $"Lv{currentLevel}";
            PassiveTargetLevelText.Text = $"Lv{targetLevel}";
            PassivePointsNeededText.Text = $"{pointsNeeded} points needed";

            // 로드맵 스테이지 표시
            var roadmap = data["roadmap"] as JArray;
            if (roadmap != null && roadmap.Count > 0)
            {
                var stagesList = new List<PassiveRoadmapStage>();

                foreach (var stage in roadmap)
                {
                    var nodes = stage["nodes"] as JArray;
                    var nodesList = new List<PassiveNode>();

                    if (nodes != null)
                    {
                        foreach (var node in nodes)
                        {
                            var stats = node["stats"] as JArray;
                            var statsList = new List<string>();

                            if (stats != null)
                            {
                                foreach (var stat in stats)
                                {
                                    statsList.Add(stat.ToString());
                                }
                            }

                            var nodeType = node["type"]?.ToString() ?? "";
                            var typeDisplay = "";

                            if (nodeType == "notable")
                                typeDisplay = "[NOTABLE]";
                            else if (nodeType == "keystone")
                                typeDisplay = "[KEYSTONE]";
                            else if (nodeType == "jewel")
                                typeDisplay = "[JEWEL]";

                            nodesList.Add(new PassiveNode
                            {
                                Name = node["name"]?.ToString() ?? "",
                                Type = nodeType,
                                TypeDisplay = typeDisplay,
                                StatsDisplay = statsList
                            });
                        }
                    }

                    // Benefits를 문자열 리스트로 변환
                    var benefits = stage["benefits"] as JObject;
                    var benefitsList = new List<string>();

                    if (benefits != null)
                    {
                        foreach (var benefit in benefits)
                        {
                            benefitsList.Add($"{benefit.Key}: {benefit.Value}");
                        }
                    }

                    stagesList.Add(new PassiveRoadmapStage
                    {
                        LevelRange = stage["level_range"]?.ToString() ?? "",
                        Points = stage["points"]?.ToObject<int>() ?? 0,
                        PriorityFocus = stage["priority_focus"]?.ToString() ?? "",
                        Nodes = nodesList,
                        BenefitsDisplay = benefitsList
                    });
                }

                PassiveRoadmapList.ItemsSource = stagesList;
            }
            else
            {
                PassiveTreeSection.Visibility = Visibility.Collapsed;
            }
        }

        private void RegisterHotkeys()
        {
            try
            {
                var windowHandle = new System.Windows.Interop.WindowInteropHelper(this).Handle;

                // F5: 하이드아웃 이동
                _hideoutHotkey = new GlobalHotkey(Key.F5, KeyModifier.None, windowHandle);
                _hideoutHotkey.HotkeyPressed += (s, e) => ExecuteHideoutCommand();

                Debug.WriteLine("Hotkeys registered: F5 = /hideout");
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Failed to register hotkeys: {ex.Message}");
            }
        }

        private void UnregisterHotkeys()
        {
            _hideoutHotkey?.Dispose();
            _hideoutHotkey = null;
        }

        private void ExecuteHideoutCommand()
        {
            try
            {
                // 클립보드에 /hideout 명령어 복사
                Clipboard.SetText("/hideout");
                Debug.WriteLine("[F5] Copied '/hideout' to clipboard");

                // 토스트 알림 (옵션)
                ShowNotification("Hideout command copied!");
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Failed to execute hideout command: {ex.Message}");
            }
        }

        private void ShowNotification(string message)
        {
            // 간단한 토스트 알림 (향후 개선 가능)
            Dispatcher.Invoke(() =>
            {
                var notification = new System.Windows.Controls.TextBlock
                {
                    Text = message,
                    Foreground = Brushes.White,
                    Background = new SolidColorBrush(Color.FromArgb(200, 0, 0, 0)),
                    Padding = new Thickness(10),
                    FontSize = 14,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Top,
                    Margin = new Thickness(0, 20, 0, 0)
                };

                // MainWindow의 Grid에 추가 (첫 번째 Grid 찾기)
                var grid = Content as System.Windows.Controls.Grid;
                if (grid != null)
                {
                    grid.Children.Add(notification);

                    // 2초 후 제거
                    var timer = new System.Windows.Threading.DispatcherTimer
                    {
                        Interval = TimeSpan.FromSeconds(2)
                    };
                    timer.Tick += (s, e) =>
                    {
                        grid.Children.Remove(notification);
                        timer.Stop();
                    };
                    timer.Start();
                }
            });
        }
    }

    // 데이터 모델 클래스
    public class ComparisonRow
    {
        public string Stat { get; set; } = "";
        public string CurrentDisplay { get; set; } = "";
        public string TargetDisplay { get; set; } = "";
        public string GapDisplay { get; set; } = "";
        public string Status { get; set; } = "";
    }

    public class PriorityUpgrade
    {
        public int Priority { get; set; }
        public string Category { get; set; } = "";
        public string Description { get; set; } = "";
        public string Suggestion { get; set; } = "";
    }

    public class UpgradeStep
    {
        public int Step { get; set; }
        public string Priority { get; set; } = "";
        public string Title { get; set; } = "";
        public int CostChaos { get; set; }
        public string Description { get; set; } = "";
        public string Impact { get; set; } = "";
        public List<string> Recommendations { get; set; } = new List<string>();
    }

    public class PassiveRoadmapStage
    {
        public string LevelRange { get; set; } = "";
        public int Points { get; set; }
        public string PriorityFocus { get; set; } = "";
        public List<PassiveNode> Nodes { get; set; } = new List<PassiveNode>();
        public List<string> BenefitsDisplay { get; set; } = new List<string>();
    }

    public class PassiveNode
    {
        public string Name { get; set; } = "";
        public string Type { get; set; } = "";
        public string TypeDisplay { get; set; } = "";
        public List<string> StatsDisplay { get; set; } = new List<string>();
    }
}
