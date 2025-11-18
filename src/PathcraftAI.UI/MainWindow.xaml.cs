using System;
using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
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
        private readonly string _upgradePathTradeScriptPath;
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
            var baseDir = AppDomain.CurrentDomain.BaseDirectory;
            var projectRoot = Path.GetFullPath(Path.Combine(baseDir, "..", "..", "..", "..", ".."));
            var parserDir = Path.Combine(projectRoot, "src", "PathcraftAI.Parser");
            _pythonPath = Path.Combine(parserDir, ".venv", "Scripts", "python.exe");
            _recommendationScriptPath = Path.Combine(parserDir, "auto_recommendation_engine.py");
            _oauthScriptPath = Path.Combine(parserDir, "test_oauth.py");
            _compareBuildScriptPath = Path.Combine(parserDir, "compare_build.py");
            _upgradePathScriptPath = Path.Combine(parserDir, "upgrade_path.py");
            _upgradePathTradeScriptPath = Path.Combine(parserDir, "upgrade_path_trade.py");
            _passiveTreeScriptPath = Path.Combine(parserDir, "passive_tree_analyzer.py");
            _tokenFilePath = Path.Combine(parserDir, "poe_token.json");

            // 경로 확인 및 디버깅
            var logPath = Path.Combine(baseDir, "pathcraft_debug.log");
            try
            {
                File.WriteAllText(logPath, $"[PATH DEBUG] BaseDirectory: {baseDir}\n" +
                    $"[PATH DEBUG] ProjectRoot: {projectRoot}\n" +
                    $"[PATH DEBUG] ParserDir: {parserDir}\n" +
                    $"[PATH DEBUG] PythonPath: {_pythonPath}\n" +
                    $"[PATH DEBUG] Python exists: {File.Exists(_pythonPath)}\n" +
                    $"[PATH DEBUG] RecommendationScript exists: {File.Exists(_recommendationScriptPath)}\n");
            }
            catch { }

            Debug.WriteLine($"[PATH DEBUG] BaseDirectory: {baseDir}");
            Debug.WriteLine($"[PATH DEBUG] ProjectRoot: {projectRoot}");
            Debug.WriteLine($"[PATH DEBUG] ParserDir: {parserDir}");
            Debug.WriteLine($"[PATH DEBUG] PythonPath: {_pythonPath}");
            Debug.WriteLine($"[PATH DEBUG] Python exists: {File.Exists(_pythonPath)}");

            if (!File.Exists(_pythonPath))
            {
                PlaceholderPanel.Visibility = Visibility.Visible;
                PlaceholderText.Text = $"⚠️ Python not found\n\n{_pythonPath}\n\nPlease check virtual environment setup.\n\nSee pathcraft_debug.log for details.";
            }

            if (!File.Exists(_recommendationScriptPath))
            {
                PlaceholderPanel.Visibility = Visibility.Visible;
                PlaceholderText.Text = $"⚠️ Script not found\n\n{_recommendationScriptPath}\n\nSee pathcraft_debug.log for details.";
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
                PlaceholderPanel.Visibility = Visibility.Collapsed;
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
                ShowFriendlyError(ex, "추천 빌드를 불러오는 중 오류가 발생했습니다.");
                PlaceholderPanel.Visibility = Visibility.Visible;
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
            var parserDir = Path.GetDirectoryName(_recommendationScriptPath)!;

            var psi = new ProcessStartInfo
            {
                FileName = _pythonPath,
                Arguments = $"\"{_recommendationScriptPath}\" --json-output --include-user-build-analysis",
                WorkingDirectory = parserDir,
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

            Debug.WriteLine($"[EXEC] Running: {_pythonPath}");
            Debug.WriteLine($"[EXEC] Args: {psi.Arguments}");
            Debug.WriteLine($"[EXEC] WorkingDir: {parserDir}");

            using var process = Process.Start(psi);
            if (process == null)
                throw new Exception("Failed to start Python process");

            var output = process.StandardOutput.ReadToEnd();
            var error = process.StandardError.ReadToEnd();
            process.WaitForExit();

            Debug.WriteLine($"[EXEC] Exit code: {process.ExitCode}");
            Debug.WriteLine($"[EXEC] Output length: {output.Length}");
            if (!string.IsNullOrWhiteSpace(error))
            {
                Debug.WriteLine($"[EXEC] Stderr: {error}");
            }

            if (process.ExitCode != 0)
            {
                throw new Exception($"Recommendation engine error (exit code {process.ExitCode}):\n{error}");
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

                JObject data;
                try
                {
                    data = JObject.Parse(jsonString);
                }
                catch (Newtonsoft.Json.JsonReaderException ex)
                {
                    // JSON 파싱 실패 - Python 로그가 섞였을 가능성
                    Debug.WriteLine($"JSON Parse Error: {ex.Message}");
                    Debug.WriteLine($"Python Output (first 500 chars):\n{jsonOutput.Substring(0, Math.Min(500, jsonOutput.Length))}");

                    var errorMsg = $"JSON 파싱에 실패했습니다.\n\n" +
                                  $"원인: Python 스크립트가 로그를 stdout으로 출력했을 가능성이 있습니다.\n\n" +
                                  $"해결: PYTHON_LOGGING_RULES.md 참고\n\n" +
                                  $"에러: {ex.Message}\n\n" +
                                  $"Python 출력 (처음 200자):\n{jsonOutput.Substring(0, Math.Min(200, jsonOutput.Length))}";

                    MessageBox.Show(errorMsg, "추천 데이터 파싱 오류", MessageBoxButton.OK, MessageBoxImage.Error);
                    ShowNoRecommendations();
                    return;
                }

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

                // Popular Builds 섹션 추가 (YouTube 빌드 가이드)
                DisplayPopularBuilds();
            }
            catch (Exception ex)
            {
                ShowFriendlyError(ex, "추천 데이터를 파싱하는 중 오류가 발생했습니다.");
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

                var upgradeList = new List<UpgradeSuggestion>();
                foreach (var suggestion in upgradeSuggestions)
                {
                    upgradeList.Add(new UpgradeSuggestion
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
                Width = 320,
                Background = new SolidColorBrush(Color.FromRgb(38, 38, 56)),  // #262638
                BorderBrush = new SolidColorBrush(Color.FromRgb(69, 71, 90)),  // #45475A
                BorderThickness = new Thickness(2),
                CornerRadius = new CornerRadius(8),
                Padding = new Thickness(0),
                Margin = new Thickness(0, 0, 8, 12),
                Cursor = Cursors.Hand,
                VerticalAlignment = VerticalAlignment.Top
            };

            // Mouse hover effects
            card.MouseEnter += (s, e) =>
            {
                card.Background = new SolidColorBrush(Color.FromRgb(49, 50, 68));  // #313244
                card.BorderBrush = new SolidColorBrush(Color.FromRgb(137, 180, 250));  // #89B4FA
            };

            card.MouseLeave += (s, e) =>
            {
                card.Background = new SolidColorBrush(Color.FromRgb(38, 38, 56));  // #262638
                card.BorderBrush = new SolidColorBrush(Color.FromRgb(69, 71, 90));  // #45475A
            };

            var mainGrid = new Grid();
            mainGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(160) }); // Thumbnail
            mainGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) }); // Content

            // YouTube 썸네일 영역
            var thumbnail = build["thumbnail"]?.ToString();
            if (!string.IsNullOrEmpty(thumbnail) || build["url"] != null)
            {
                var thumbnailBorder = new Border
                {
                    Width = 160,
                    Height = 90,
                    Background = new SolidColorBrush(Color.FromRgb(24, 24, 37)),  // #181825
                    CornerRadius = new CornerRadius(8, 0, 0, 8),
                    ClipToBounds = true
                };

                if (!string.IsNullOrEmpty(thumbnail))
                {
                    // 실제 YouTube 썸네일 이미지 표시
                    var image = new System.Windows.Controls.Image
                    {
                        Stretch = Stretch.UniformToFill,
                        HorizontalAlignment = HorizontalAlignment.Center,
                        VerticalAlignment = VerticalAlignment.Center
                    };

                    var bitmap = new BitmapImage();
                    bitmap.BeginInit();
                    bitmap.UriSource = new Uri(thumbnail, UriKind.Absolute);
                    bitmap.CacheOption = BitmapCacheOption.OnLoad;
                    bitmap.EndInit();
                    image.Source = bitmap;

                    thumbnailBorder.Child = image;
                }
                else
                {
                    // 썸네일 URL이 없으면 이모지 표시
                    var thumbnailText = new TextBlock
                    {
                        Text = "🎬",
                        FontSize = 32,
                        Foreground = new SolidColorBrush(Color.FromRgb(137, 180, 250)),  // #89B4FA
                        HorizontalAlignment = HorizontalAlignment.Center,
                        VerticalAlignment = VerticalAlignment.Center
                    };
                    thumbnailBorder.Child = thumbnailText;
                }

                Grid.SetColumn(thumbnailBorder, 0);
                mainGrid.Children.Add(thumbnailBorder);
            }

            // Content area
            var contentStack = new StackPanel
            {
                Margin = new Thickness(12)
            };

            Grid.SetColumn(contentStack, thumbnail != null || build["url"] != null ? 1 : 0);
            if (thumbnail == null && build["url"] == null)
            {
                Grid.SetColumnSpan(contentStack, 2);
            }

            // 빌드 이름
            string buildName = ExtractBuildName(build, category);
            var title = new TextBlock
            {
                Text = buildName,
                FontSize = 15,
                FontWeight = FontWeights.Bold,
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 6),
                Foreground = Brushes.White
            };
            contentStack.Children.Add(title);

            // Build keyword/category tag
            var buildKeyword = build["build_keyword"]?.ToString();
            if (!string.IsNullOrEmpty(buildKeyword))
            {
                var keywordBorder = new Border
                {
                    Background = new SolidColorBrush(Color.FromArgb(100, 175, 96, 37)),
                    CornerRadius = new CornerRadius(4),
                    Padding = new Thickness(6, 2, 6, 2),
                    Margin = new Thickness(0, 0, 0, 6),
                    HorizontalAlignment = HorizontalAlignment.Left
                };

                var keywordText = new TextBlock
                {
                    Text = buildKeyword,
                    FontSize = 10,
                    FontWeight = FontWeights.SemiBold,
                    Foreground = new SolidColorBrush(Color.FromRgb(249, 226, 175))  // #F9E2AF
                };

                keywordBorder.Child = keywordText;
                contentStack.Children.Add(keywordBorder);
            }

            // Build metadata
            var metadata = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 0, 0, 8) };

            // Channel name
            var channel = build["channel_title"]?.ToString() ?? build["channel"]?.ToString();
            if (!string.IsNullOrEmpty(channel))
            {
                metadata.Children.Add(new TextBlock
                {
                    Text = $"📺 {channel}",
                    FontSize = 11,
                    Foreground = new SolidColorBrush(Color.FromRgb(186, 194, 222)),  // #BAC2DE
                    Margin = new Thickness(0, 0, 12, 0)
                });
            }

            // View count
            var views = build["view_count"]?.ToObject<int>() ?? build["views"]?.ToObject<int>() ?? 0;
            if (views > 0)
            {
                metadata.Children.Add(new TextBlock
                {
                    Text = $"👁 {views:N0}",
                    FontSize = 11,
                    Foreground = new SolidColorBrush(Color.FromRgb(186, 194, 222)),  // #BAC2DE
                    Margin = new Thickness(0, 0, 12, 0)
                });
            }

            // Build Info
            var infoText = BuildInfoText(build, category);
            if (!string.IsNullOrEmpty(infoText))
            {
                metadata.Children.Add(new TextBlock
                {
                    Text = infoText,
                    FontSize = 11,
                    Foreground = new SolidColorBrush(Color.FromRgb(186, 194, 222))  // #BAC2DE
                });
            }

            if (metadata.Children.Count > 0)
            {
                contentStack.Children.Add(metadata);
            }

            // Action buttons
            var buttonStack = new StackPanel { Orientation = Orientation.Horizontal };

            // POB links
            var pobLinks = build["pob_links"] as JArray;
            if (pobLinks != null && pobLinks.Count > 0)
            {
                var pobButton = new Button
                {
                    Content = "Open POB",
                    FontSize = 11,
                    Padding = new Thickness(10, 4, 10, 4),
                    Margin = new Thickness(0, 0, 8, 0),
                    Background = new SolidColorBrush(Color.FromRgb(166, 227, 161)),  // #A6E3A1
                    Foreground = new SolidColorBrush(Color.FromRgb(30, 30, 46)),  // Dark text
                    BorderThickness = new Thickness(0),
                    Cursor = Cursors.Hand,
                    Tag = pobLinks[0].ToString()
                };

                pobButton.Click += (s, e) =>
                {
                    var url = (s as Button)?.Tag?.ToString();
                    if (!string.IsNullOrEmpty(url))
                    {
                        try
                        {
                            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                            {
                                FileName = url,
                                UseShellExecute = true
                            });
                        }
                        catch (Exception ex)
                        {
                            ShowNotification($"Failed to open POB link: {ex.Message}", isError: true);
                        }
                    }
                };

                buttonStack.Children.Add(pobButton);

                // AI Analyze button (only if POB link exists)
                var aiAnalyzeButton = new Button
                {
                    Content = "🤖 Analyze",
                    FontSize = 11,
                    Padding = new Thickness(10, 4, 10, 4),
                    Margin = new Thickness(0, 0, 8, 0),
                    Background = new SolidColorBrush(Color.FromRgb(203, 166, 247)),  // #CBA6F7
                    Foreground = new SolidColorBrush(Color.FromRgb(30, 30, 46)),  // Dark text
                    BorderThickness = new Thickness(0),
                    Cursor = Cursors.Hand,
                    Tag = pobLinks[0].ToString()
                };

                aiAnalyzeButton.Click += (s, e) =>
                {
                    var pobUrl = (s as Button)?.Tag?.ToString();
                    if (!string.IsNullOrEmpty(pobUrl))
                    {
                        // Set the POB URL and trigger AI analysis
                        _currentPOBUrl = pobUrl;
                        AIAnalysis_Click(s, e);
                    }
                };

                buttonStack.Children.Add(aiAnalyzeButton);
            }

            // YouTube video link
            var videoUrl = build["url"]?.ToString();
            if (!string.IsNullOrEmpty(videoUrl))
            {
                var videoButton = new Button
                {
                    Content = "Watch Video",
                    FontSize = 11,
                    Padding = new Thickness(10, 4, 10, 4),
                    Margin = new Thickness(0, 0, 8, 0),
                    Background = new SolidColorBrush(Color.FromRgb(243, 139, 168)),  // #F38BA8
                    Foreground = new SolidColorBrush(Color.FromRgb(30, 30, 46)),  // Dark text
                    BorderThickness = new Thickness(0),
                    Cursor = Cursors.Hand,
                    Tag = videoUrl
                };

                videoButton.Click += (s, e) =>
                {
                    var url = (s as Button)?.Tag?.ToString();
                    if (!string.IsNullOrEmpty(url))
                    {
                        try
                        {
                            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                            {
                                FileName = url,
                                UseShellExecute = true
                            });
                        }
                        catch (Exception ex)
                        {
                            ShowNotification($"Failed to open video: {ex.Message}", isError: true);
                        }
                    }
                };

                buttonStack.Children.Add(videoButton);
            }

            if (buttonStack.Children.Count > 0)
            {
                contentStack.Children.Add(buttonStack);
            }

            mainGrid.Children.Add(contentStack);
            card.Child = mainGrid;

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

        private void DisplayPopularBuilds()
        {
            try
            {
                // popular_builds JSON 파일 로드
                var parserDir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "..", "..", "PathcraftAI.Parser");
                var buildDataPath = Path.Combine(parserDir, "build_data", $"popular_builds_{_currentLeague}.json");

                // Standard 리그로 폴백
                if (!File.Exists(buildDataPath))
                {
                    buildDataPath = Path.Combine(parserDir, "build_data", "popular_builds_Standard.json");
                }

                if (!File.Exists(buildDataPath))
                {
                    return; // 파일이 없으면 섹션 표시 안 함
                }

                var jsonContent = File.ReadAllText(buildDataPath, System.Text.Encoding.UTF8);
                var popularData = JObject.Parse(jsonContent);

                var youtubeBuilds = popularData["youtube_builds"] as JArray;

                if (youtubeBuilds == null || youtubeBuilds.Count == 0)
                {
                    return; // 빌드가 없으면 섹션 표시 안 함
                }

                // 섹션 헤더
                var sectionHeader = new TextBlock
                {
                    Text = "🎬 Popular Build Guides from YouTube",
                    FontSize = 18,
                    FontWeight = FontWeights.Bold,
                    Foreground = new SolidColorBrush(Color.FromRgb(200, 120, 50)),
                    Margin = new Thickness(0, 24, 0, 4)
                };
                ResultsPanel.Children.Add(sectionHeader);

                var sectionSubtitle = new TextBlock
                {
                    Text = $"Based on POE.Ninja data and YouTube community guides (League: {popularData["league_version"]})",
                    FontSize = 12,
                    Foreground = new SolidColorBrush(Color.FromRgb(180, 180, 180)),
                    Margin = new Thickness(0, 0, 0, 12)
                };
                ResultsPanel.Children.Add(sectionSubtitle);

                // 빌드 키워드별로 그룹화
                var buildGroups = youtubeBuilds
                    .Cast<JObject>()
                    .GroupBy(b => b["build_keyword"]?.ToString() ?? "Other")
                    .Take(5); // 상위 5개 키워드만

                foreach (var group in buildGroups)
                {
                    var keyword = group.Key;

                    // 키워드 헤더
                    var keywordHeader = new TextBlock
                    {
                        Text = $"🔸 {keyword} Builds",
                        FontSize = 14,
                        FontWeight = FontWeights.SemiBold,
                        Foreground = new SolidColorBrush(Color.FromRgb(255, 200, 100)),
                        Margin = new Thickness(0, 12, 0, 8)
                    };
                    ResultsPanel.Children.Add(keywordHeader);

                    // 각 키워드의 빌드 카드 (최대 3개)
                    foreach (var build in group.Take(3))
                    {
                        // channel_title 또는 channel 필드를 channel_title로 통일
                        if (build["channel"] != null && build["channel_title"] == null)
                        {
                            build["channel_title"] = build["channel"];
                        }

                        var buildCard = CreateRecommendationCard(build, "youtube");
                        ResultsPanel.Children.Add(buildCard);
                    }
                }
            }
            catch (Exception ex)
            {
                // 에러가 발생해도 전체 UI를 망가뜨리지 않음
                Debug.WriteLine($"Failed to load popular builds: {ex.Message}");
            }
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
            MessageBox.Show("Settings window coming soon!\n\nFeatures:\n- API key management (GPT/Gemini/Claude)\n- Theme selection",
                "Settings", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void ShowFriendlyError(Exception ex, string context = "")
        {
            string title = "알림";
            string message = ex.Message;
            MessageBoxImage icon = MessageBoxImage.Warning;

            // Rate Limit 에러 (HTTP 429)
            if (ex is System.Net.Http.HttpRequestException && (message.Contains("429") || message.Contains("Too Many Requests")))
            {
                title = "요청 제한 도달";
                message = "POE API 요청 제한에 도달했습니다.\n\n30초 후 다시 시도해주세요.";
                icon = MessageBoxImage.Information;
            }
            // Privacy 설정 에러
            else if (message.Contains("privacy", StringComparison.OrdinalIgnoreCase) ||
                     message.Contains("private", StringComparison.OrdinalIgnoreCase) ||
                     message.Contains("character tab", StringComparison.OrdinalIgnoreCase))
            {
                title = "캐릭터 비공개 설정";
                message = "캐릭터 아이템이 비공개 상태입니다.\n\n" +
                          "POE 웹사이트에서 설정 변경:\n" +
                          "1. My Account → Privacy Settings\n" +
                          "2. 'Hide characters' 옵션 체크 해제\n" +
                          "3. 저장 후 다시 시도해주세요";
                icon = MessageBoxImage.Information;
            }
            // 네트워크 에러
            else if (ex is System.Net.Http.HttpRequestException ||
                     ex is System.Net.WebException ||
                     message.Contains("network", StringComparison.OrdinalIgnoreCase) ||
                     message.Contains("connection", StringComparison.OrdinalIgnoreCase))
            {
                title = "네트워크 오류";
                message = "인터넷 연결을 확인해주세요.\n\n" +
                          "다음을 확인하세요:\n" +
                          "1. 인터넷 연결 상태\n" +
                          "2. 방화벽 설정\n" +
                          "3. POE 서버 상태 (pathofexile.com)";
                icon = MessageBoxImage.Error;
            }
            // YouTube API 키 에러
            else if (message.Contains("API key", StringComparison.OrdinalIgnoreCase) ||
                     message.Contains("YOUTUBE_API_KEY", StringComparison.OrdinalIgnoreCase))
            {
                title = "YouTube API 키 없음";
                message = "YouTube API 키가 설정되지 않았습니다.\n\n" +
                          "설정 방법:\n" +
                          "1. Google Cloud Console에서 API 키 발급\n" +
                          "2. YouTube Data API v3 활성화\n" +
                          "3. 환경 변수에 API 키 추가\n\n" +
                          "현재는 Mock 데이터로 표시됩니다.";
                icon = MessageBoxImage.Information;
            }
            // Python 프로세스 에러
            else if (message.Contains("Python", StringComparison.OrdinalIgnoreCase) ||
                     message.Contains("process", StringComparison.OrdinalIgnoreCase))
            {
                title = "Python 실행 오류";
                message = "Python 스크립트 실행에 실패했습니다.\n\n" +
                          "해결 방법:\n" +
                          "1. Virtual environment 활성화 확인\n" +
                          "2. 필요한 패키지 설치 확인\n" +
                          "3. Python 경로 확인\n\n" +
                          $"오류 내용: {ex.Message}";
                icon = MessageBoxImage.Error;
            }
            // POB 파싱 에러
            else if (message.Contains("POB", StringComparison.OrdinalIgnoreCase) ||
                     message.Contains("pastebin", StringComparison.OrdinalIgnoreCase))
            {
                title = "POB 링크 오류";
                message = "POB 링크를 불러올 수 없습니다.\n\n" +
                          "확인사항:\n" +
                          "1. 올바른 POB 링크인지 확인\n" +
                          "2. Pastebin이 접근 가능한지 확인\n" +
                          "3. POB 데이터가 유효한지 확인";
                icon = MessageBoxImage.Warning;
            }
            // 일반 에러 (컨텍스트 추가)
            else if (!string.IsNullOrEmpty(context))
            {
                title = "오류 발생";
                message = $"{context}\n\n오류 내용:\n{ex.Message}";
                icon = MessageBoxImage.Error;
            }

            MessageBox.Show(message, title, MessageBoxButton.OK, icon);
        }

        private void Donate_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Support PathcraftAI!\n\nThank you for your support!",
                "Donate", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private async void AIAnalysis_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_currentPOBUrl))
            {
                MessageBox.Show("POB 링크를 먼저 입력해주세요.\n\n'Refresh Recommendations'를 먼저 실행하거나, POB 링크가 있는 빌드를 선택해주세요.",
                    "POB 링크 필요", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            try
            {
                AIAnalysisButton.IsEnabled = false;
                AIAnalysisButton.Content = "Analyzing...";
                AIAnalysisSection.Visibility = Visibility.Visible;
                AIAnalysisText.Text = "🔄 AI가 빌드를 분석 중입니다. 잠시만 기다려주세요...";

                // Get selected AI provider
                int selectedProvider = AIProviderCombo.SelectedIndex;
                string provider = selectedProvider == 0 ? "rule-based" :
                                  selectedProvider == 1 ? "claude" :
                                  selectedProvider == 2 ? "openai" : "both";

                // Run AI analysis via Python
                var result = await System.Threading.Tasks.Task.Run(() => ExecuteAIAnalysis(_currentPOBUrl, provider));

                // Parse and display result
                var analysisData = JObject.Parse(result);

                if (analysisData["error"] != null)
                {
                    AIAnalysisText.Text = $"❌ 오류: {analysisData["error"]}";
                }
                else
                {
                    DisplayAIAnalysis(analysisData);
                }
            }
            catch (Exception ex)
            {
                ShowFriendlyError(ex, "AI 분석 중 오류가 발생했습니다.");
                AIAnalysisText.Text = $"❌ 분석 실패: {ex.Message}";
            }
            finally
            {
                AIAnalysisButton.IsEnabled = true;
                AIAnalysisButton.Content = "🤖 AI Analysis";
            }
        }

        private string ExecuteAIAnalysis(string pobUrl, string provider)
        {
            var parserDir = Path.GetDirectoryName(_pythonPath);
            var aiAnalyzerScript = Path.Combine(parserDir!, "..", "ai_build_analyzer.py");

            var psi = new ProcessStartInfo
            {
                FileName = _pythonPath,
                Arguments = $"\"{aiAnalyzerScript}\" --pob \"{pobUrl}\" --provider {provider} --json",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                WorkingDirectory = parserDir,
                StandardOutputEncoding = System.Text.Encoding.UTF8
            };

            // API 키 환경 변수로 전달
            var anthropicKey = Environment.GetEnvironmentVariable("ANTHROPIC_API_KEY");
            var openaiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY");

            if (!string.IsNullOrEmpty(anthropicKey))
                psi.Environment["ANTHROPIC_API_KEY"] = anthropicKey;
            if (!string.IsNullOrEmpty(openaiKey))
                psi.Environment["OPENAI_API_KEY"] = openaiKey;

            psi.Environment["PYTHONUTF8"] = "1";

            using var process = Process.Start(psi);
            if (process == null)
                throw new Exception("Failed to start AI analysis process");

            var output = process.StandardOutput.ReadToEnd();
            var error = process.StandardError.ReadToEnd();
            process.WaitForExit();

            if (process.ExitCode != 0)
            {
                throw new Exception($"AI analysis failed:\n{error}");
            }

            return output;
        }

        private void DisplayAIAnalysis(JObject analysisData)
        {
            var provider = analysisData["provider"]?.ToString() ?? "unknown";
            var model = analysisData["model"]?.ToString() ?? "unknown";
            var analysis = analysisData["analysis"]?.ToString() ?? "";
            var elapsed = analysisData["elapsed_seconds"]?.ToObject<double>() ?? 0;
            var inputTokens = analysisData["input_tokens"]?.ToObject<int>() ?? 0;
            var outputTokens = analysisData["output_tokens"]?.ToObject<int>() ?? 0;

            // Update header
            AIProviderText.Text = $"Provider: {model}";
            AITimeText.Text = $"{elapsed:F1}s";
            AITokensText.Text = $"Tokens: {inputTokens:N0} in / {outputTokens:N0} out";

            // Update analysis text
            AIAnalysisText.Text = analysis;
        }

        private void CopyAIAnalysis_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var analysisText = AIAnalysisText.Text;
                if (string.IsNullOrEmpty(analysisText) || analysisText.StartsWith("Click"))
                {
                    MessageBox.Show("분석 결과가 없습니다.\n먼저 'AI Analysis' 버튼을 클릭해주세요.",
                        "알림", MessageBoxButton.OK, MessageBoxImage.Information);
                    return;
                }

                Clipboard.SetText(analysisText);
                ShowNotification("AI 분석 결과가 클립보드에 복사되었습니다!");
            }
            catch (Exception ex)
            {
                ShowFriendlyError(ex, "분석 결과 복사 중 오류가 발생했습니다.");
            }
        }

        private void CopyWhisper_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button button && button.Tag is string whisperMessage)
            {
                try
                {
                    Clipboard.SetText(whisperMessage);
                    ShowNotification("Whisper message copied to clipboard!");
                }
                catch (Exception ex)
                {
                    ShowFriendlyError(ex, "Whisper 메시지 복사 중 오류가 발생했습니다.");
                }
            }
        }

        private void POBInputBox_GotFocus(object sender, RoutedEventArgs e)
        {
            if (sender is TextBox textBox && textBox.Text == "https://pobb.in/...")
            {
                textBox.Text = "";
            }
        }

        private async void AnalyzePOB_Click(object sender, RoutedEventArgs e)
        {
            var pobUrl = POBInputBox.Text?.Trim();

            if (string.IsNullOrWhiteSpace(pobUrl) || pobUrl == "https://pobb.in/...")
            {
                // POB 링크 없으면 Refresh Recommendations 실행
                await LoadRecommendations();
                return;
            }

            // POB 링크가 있으면 AI 분석 실행
            _currentPOBUrl = pobUrl;
            await AnalyzePOBBuild(pobUrl);
        }

        private async Task AnalyzePOBBuild(string pobUrl)
        {
            try
            {
                PlaceholderPanel.Visibility = Visibility.Collapsed;
                ResultsPanel.Children.Clear();

                var loadingText = new TextBlock
                {
                    Text = "🤖 AI 분석 중... 잠시만 기다려주세요",
                    FontSize = 14,
                    Foreground = new SolidColorBrush(Color.FromRgb(175, 96, 37)),
                    HorizontalAlignment = HorizontalAlignment.Center,
                    Margin = new Thickness(0, 100, 0, 0)
                };
                ResultsPanel.Children.Add(loadingText);

                // Rule-Based 분석 먼저 실행 (빠름)
                await System.Threading.Tasks.Task.Run(() => AnalyzePOBWithRules(pobUrl));

                // 추천 빌드도 함께 로드
                await LoadRecommendations();
            }
            catch (Exception ex)
            {
                ShowFriendlyError(ex, "POB 분석 중 오류가 발생했습니다.");
                PlaceholderPanel.Visibility = Visibility.Visible;
            }
        }

        private void AnalyzePOBWithRules(string pobUrl)
        {
            var parserDir = Path.GetDirectoryName(_recommendationScriptPath)!;
            var ruleAnalyzerScript = Path.Combine(parserDir, "rule_based_analyzer.py");

            var psi = new ProcessStartInfo
            {
                FileName = _pythonPath,
                Arguments = $"\"{ruleAnalyzerScript}\" --pob \"{pobUrl}\" --json",
                WorkingDirectory = parserDir,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                StandardOutputEncoding = System.Text.Encoding.UTF8
            };

            psi.Environment["PYTHONUTF8"] = "1";

            using var process = Process.Start(psi);
            if (process == null)
                throw new Exception("Failed to start Python process");

            var output = process.StandardOutput.ReadToEnd();
            var error = process.StandardError.ReadToEnd();
            process.WaitForExit();

            if (process.ExitCode != 0)
            {
                throw new Exception($"Rule-based analyzer error (exit code {process.ExitCode}):\n{error}");
            }

            // JSON 파싱 및 AI Analysis 섹션 표시
            Dispatcher.Invoke(() =>
            {
                DisplayRuleBasedAnalysis(output);
            });
        }

        private void DisplayRuleBasedAnalysis(string jsonOutput)
        {
            try
            {
                var jsonStart = jsonOutput.IndexOf('{');
                var jsonEnd = jsonOutput.LastIndexOf('}');

                if (jsonStart == -1 || jsonEnd == -1)
                    return;

                var jsonString = jsonOutput.Substring(jsonStart, jsonEnd - jsonStart + 1);
                var data = JObject.Parse(jsonString);

                // AI Analysis 섹션 표시
                AIAnalysisSection.Visibility = Visibility.Visible;
                AIProviderText.Text = "Provider: Rule-Based (Free)";

                var analysis = data["analysis"]?.ToString() ?? "분석 결과가 없습니다.";
                AIAnalysisText.Text = analysis;

                // 토큰 정보는 Rule-Based에서는 N/A
                AITokensText.Text = "Tokens: N/A (Free)";
                AITimeText.Text = $"{data["execution_time"]?.ToObject<double>() ?? 0.0:F1}s";
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[ERROR] DisplayRuleBasedAnalysis: {ex.Message}");
            }
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
                }
            }
            catch (Exception ex)
            {
                ShowFriendlyError(ex, "POE 계정 연결 중 오류가 발생했습니다.");
            }
            finally
            {
                ConnectPOEButton.IsEnabled = true;
                UpdatePOEButtonState();

                // 추천 새로고침 (사용자 캐릭터 기반) - UI 블로킹 방지를 위해 비동기로 실행
                if (_isPOEConnected)
                {
                    _ = LoadRecommendations();
                }
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
                        POEAccountText.Foreground = new SolidColorBrush(Color.FromRgb(166, 227, 161));  // #A6E3A1

                        // 캐릭터 정보 로드
                        LoadCharacterInfo();
                    }
                }
                else
                {
                    _isPOEConnected = false;
                    POEAccountText.Text = "Not connected";
                    POEAccountText.Foreground = new SolidColorBrush(Color.FromRgb(127, 132, 156));  // #7F849C
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
                ShowFriendlyError(ex, "POE 계정 연결 해제 중 오류가 발생했습니다.");
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
                // Show loading indicator
                UpgradePathDescription.Text = "Loading upgrade path recommendations...";
                UpgradePathSection.Visibility = Visibility.Visible;

                // Python 스크립트로 업그레이드 경로 가져오기 (with timeout)
                var timeoutTask = System.Threading.Tasks.Task.Delay(30000); // 30초 타임아웃
                var upgradeTask = System.Threading.Tasks.Task.Run(() =>
                    ExecuteUpgradePath(pobUrl, characterName, budgetChaos));

                var completedTask = await System.Threading.Tasks.Task.WhenAny(upgradeTask, timeoutTask);

                if (completedTask == timeoutTask)
                {
                    ShowNotification("Upgrade path request timed out. Please try again.", isError: true);
                    UpgradePathSection.Visibility = Visibility.Collapsed;
                    return;
                }

                var result = await upgradeTask;

                if (string.IsNullOrWhiteSpace(result))
                {
                    ShowNotification("Failed to load upgrade path. Please check your POB URL.", isError: true);
                    UpgradePathSection.Visibility = Visibility.Collapsed;
                    return;
                }

                // JSON 파싱
                JObject? data;
                try
                {
                    data = JObject.Parse(result);
                }
                catch (Exception ex)
                {
                    Debug.WriteLine($"JSON parse error: {ex.Message}");
                    ShowNotification("Failed to parse upgrade path data.", isError: true);
                    UpgradePathSection.Visibility = Visibility.Collapsed;
                    return;
                }

                // 에러 체크
                if (data["error"] != null)
                {
                    var errorMsg = data["error"]?.ToString() ?? "Unknown error";
                    ShowNotification($"Upgrade path error: {errorMsg}", isError: true);
                    UpgradePathSection.Visibility = Visibility.Collapsed;
                    return;
                }

                // 업그레이드 경로 표시
                UpgradePathDescription.Text = "Based on your current build and target POB, here's the recommended upgrade path:";
                DisplayUpgradePath(data);
                UpgradePathSection.Visibility = Visibility.Visible;

                // 업그레이드 경로 로드 후 패시브 트리 로드
                _ = LoadPassiveTreeRoadmap(pobUrl, characterName);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Upgrade path failed: {ex.Message}");
                ShowNotification($"Error loading upgrade path: {ex.Message}", isError: true);
                UpgradePathSection.Visibility = Visibility.Collapsed;
            }
        }

        private string ExecuteUpgradePath(string pobUrl, string characterName, int budgetChaos)
        {
            // Use Trade API version for real trade data
            var scriptPath = _upgradePathTradeScriptPath;

            var psi = new ProcessStartInfo
            {
                FileName = _pythonPath,
                Arguments = $"\"{scriptPath}\" --pob \"{pobUrl}\" --character \"{characterName}\" --budget {budgetChaos} --league Standard --mock --json",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                StandardOutputEncoding = System.Text.Encoding.UTF8,
                WorkingDirectory = Path.GetDirectoryName(scriptPath)
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

                    // Trade results 파싱
                    var tradeResults = step["trade_results"] as JArray;
                    var tradeItemsList = new List<TradeItem>();

                    if (tradeResults != null)
                    {
                        foreach (var item in tradeResults)
                        {
                            tradeItemsList.Add(new TradeItem
                            {
                                Name = item["name"]?.ToString() ?? "",
                                Type = item["type"]?.ToString() ?? "",
                                PriceDisplay = item["price_display"]?.ToString() ?? "",
                                Seller = item["seller"]?.ToString() ?? "",
                                Whisper = item["whisper"]?.ToString() ?? ""
                            });
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
                        Recommendations = recList,
                        TradeItems = tradeItemsList
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

        private void ShowNotification(string message, bool isError = false)
        {
            // 간단한 토스트 알림 (향후 개선 가능)
            Dispatcher.Invoke(() =>
            {
                var bgColor = isError
                    ? Color.FromArgb(200, 180, 0, 0)  // Red for errors
                    : Color.FromArgb(200, 0, 0, 0);   // Black for normal

                var notification = new System.Windows.Controls.TextBlock
                {
                    Text = message,
                    Foreground = Brushes.White,
                    Background = new SolidColorBrush(bgColor),
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

                    // 에러는 4초, 일반은 2초 후 제거
                    var duration = isError ? 4 : 2;
                    var timer = new System.Windows.Threading.DispatcherTimer
                    {
                        Interval = TimeSpan.FromSeconds(duration)
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
        public List<TradeItem> TradeItems { get; set; } = new List<TradeItem>();

        public bool HasTradeItems => TradeItems != null && TradeItems.Count > 0;
    }

    public class TradeItem
    {
        public string Name { get; set; } = "";
        public string Type { get; set; } = "";
        public string PriceDisplay { get; set; } = "";
        public string Seller { get; set; } = "";
        public string Whisper { get; set; } = "";

        public string WhisperPreview
        {
            get
            {
                if (string.IsNullOrEmpty(Whisper))
                    return "";
                return Whisper.Length > 80 ? Whisper.Substring(0, 80) + "..." : Whisper;
            }
        }
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

    public class BoolToVisibilityConverter : System.Windows.Data.IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
        {
            if (value is bool boolValue)
                return boolValue ? Visibility.Visible : Visibility.Collapsed;
            return Visibility.Collapsed;
        }

        public object ConvertBack(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }

    // Helper class for upgrade suggestions
    public class UpgradeSuggestion
    {
        public string ItemName { get; set; } = "";
        public double ChaosValue { get; set; }
        public string Reason { get; set; } = "";
    }
}
