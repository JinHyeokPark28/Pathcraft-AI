# PathcraftAI - C# Unity Integration Plan
**Date**: 2025-11-15
**Target Platform**: .NET 8 WPF Desktop Application
**Python Backend**: Completed and tested

---

## Overview

이 문서는 Python 백엔드 시스템을 C# Unity WPF 애플리케이션과 연동하는 구현 계획입니다.

---

## Architecture Options

### Option 1: Process Communication (Recommended)
**Python을 별도 프로세스로 실행하고 JSON으로 통신**

```
[C# WPF App]
     ↓ Start process
[Python Process] ← Stdin (JSON commands)
     ↓ Stdout (JSON responses)
[C# WPF App] ← Parse results
```

**장점**:
- 구현 간단
- Python 환경 독립적
- 디버깅 용이
- Python 코드 수정 시 재컴파일 불필요

**단점**:
- 프로세스 시작 오버헤드 (~1초)
- 메모리 사용량 증가

---

### Option 2: Python.NET (IronPython/pythonnet)
**C#에서 Python 코드 직접 호출**

```
[C# WPF App]
     ↓ pythonnet
[Python Runtime] ← Direct function calls
     ↓ Return objects
[C# WPF App] ← Convert to C# types
```

**장점**:
- 더 빠른 응답 (프로세스 시작 없음)
- 메모리 공유 가능

**단점**:
- 설정 복잡 (Python 환경 임베딩)
- 디버깅 어려움
- 버전 호환성 이슈

---

### Option 3: REST API Server
**Python FastAPI 서버 + C# HttpClient**

```
[C# WPF App]
     ↓ HTTP POST
[Python FastAPI Server] ← JSON request
     ↓ JSON response
[C# WPF App] ← Deserialize
```

**장점**:
- 완전 분리 (마이크로서비스)
- 웹 UI로 확장 가능
- 다중 클라이언트 지원

**단점**:
- 서버 관리 필요
- 네트워크 오버헤드
- 로컬 전용에는 과한 구조

---

## 🎯 Recommended: Option 1 (Process Communication)

데스크톱 앱 특성상 **Process Communication**이 가장 적합합니다.

---

## Implementation Steps

### Step 1: Python CLI Wrapper 생성

모든 기능을 CLI로 호출 가능하게 통합:

```python
# pathcraft_cli.py
"""
PathcraftAI Command Line Interface
C#에서 호출할 수 있는 통합 CLI
"""

import json
import sys
from typing import Dict, Any

def search_builds(keyword: str, max_results: int = 10) -> Dict[str, Any]:
    """빌드 검색"""
    from demo_build_search import demo_build_search

    results = demo_build_search(keyword)

    return {
        "success": True,
        "keyword": keyword,
        "results": results,
        "total_found": len(results)
    }

def generate_guide(keyword: str, llm_provider: str = "mock") -> Dict[str, Any]:
    """빌드 가이드 생성"""
    from build_guide_generator import generate_build_guide_with_llm

    output_file = f"build_guides/{keyword}_guide.md"
    guide = generate_build_guide_with_llm(
        keyword=keyword,
        llm_provider=llm_provider,
        output_file=output_file
    )

    return {
        "success": True,
        "keyword": keyword,
        "guide_file": output_file,
        "preview": guide[:500]  # 처음 500자만
    }

def get_item_price(item_name: str) -> Dict[str, Any]:
    """아이템 가격 조회"""
    from build_analyzer import load_item_data

    item_data = load_item_data(item_name)

    if item_data:
        return {
            "success": True,
            "item_name": item_name,
            "chaos_price": item_data.get("chaosValue"),
            "divine_price": item_data.get("divineValue"),
            "trend": item_data.get("sparkline", {}).get("totalChange")
        }
    else:
        return {
            "success": False,
            "error": f"Item '{item_name}' not found"
        }

def main():
    """CLI Entry Point"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: pathcraft_cli.py <command> [args...]",
            "commands": ["search", "guide", "price"]
        }))
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "search":
            keyword = sys.argv[2] if len(sys.argv) > 2 else "Kinetic Fusillade"
            result = search_builds(keyword)

        elif command == "guide":
            keyword = sys.argv[2] if len(sys.argv) > 2 else "Mageblood"
            llm = sys.argv[3] if len(sys.argv) > 3 else "mock"
            result = generate_guide(keyword, llm)

        elif command == "price":
            item_name = sys.argv[2] if len(sys.argv) > 2 else "Mageblood"
            result = get_item_price(item_name)

        else:
            result = {
                "error": f"Unknown command: {command}",
                "available": ["search", "guide", "price"]
            }

        # JSON 출력 (C#에서 파싱)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

### Step 2: C# Wrapper Class 작성

```csharp
// PathcraftAI.Core/PythonBackend.cs
using System;
using System.Diagnostics;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace PathcraftAI.Core
{
    /// <summary>
    /// Python 백엔드와 통신하는 C# 래퍼
    /// </summary>
    public class PythonBackend
    {
        private readonly string _pythonPath;
        private readonly string _scriptPath;

        public PythonBackend(string pythonPath, string scriptPath)
        {
            _pythonPath = pythonPath;
            _scriptPath = scriptPath;
        }

        /// <summary>
        /// Python 프로세스 실행 및 결과 반환
        /// </summary>
        private async Task<string> ExecutePython(params string[] args)
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = _pythonPath,
                Arguments = $"\"{_scriptPath}\" {string.Join(" ", args)}",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                StandardOutputEncoding = Encoding.UTF8
            };

            using var process = Process.Start(startInfo);
            if (process == null)
                throw new Exception("Failed to start Python process");

            var output = await process.StandardOutput.ReadToEndAsync();
            var error = await process.StandardError.ReadToEndAsync();

            await process.WaitForExitAsync();

            if (process.ExitCode != 0)
            {
                throw new Exception($"Python error: {error}");
            }

            return output;
        }

        /// <summary>
        /// 빌드 검색
        /// </summary>
        public async Task<BuildSearchResult> SearchBuilds(string keyword, int maxResults = 10)
        {
            var json = await ExecutePython("search", keyword, maxResults.ToString());
            return JsonSerializer.Deserialize<BuildSearchResult>(json);
        }

        /// <summary>
        /// 빌드 가이드 생성
        /// </summary>
        public async Task<BuildGuideResult> GenerateGuide(string keyword, string llmProvider = "mock")
        {
            var json = await ExecutePython("guide", keyword, llmProvider);
            return JsonSerializer.Deserialize<BuildGuideResult>(json);
        }

        /// <summary>
        /// 아이템 가격 조회
        /// </summary>
        public async Task<ItemPriceResult> GetItemPrice(string itemName)
        {
            var json = await ExecutePython("price", itemName);
            return JsonSerializer.Deserialize<ItemPriceResult>(json);
        }
    }

    // Result DTOs
    public class BuildSearchResult
    {
        public bool Success { get; set; }
        public string Keyword { get; set; }
        public List<BuildInfo> Results { get; set; }
        public int TotalFound { get; set; }
    }

    public class BuildInfo
    {
        public string BuildName { get; set; }
        public string Class { get; set; }
        public string Ascendancy { get; set; }
        public int Level { get; set; }
        public string PobLink { get; set; }
        public List<string> MainSkills { get; set; }
    }

    public class BuildGuideResult
    {
        public bool Success { get; set; }
        public string Keyword { get; set; }
        public string GuideFile { get; set; }
        public string Preview { get; set; }
    }

    public class ItemPriceResult
    {
        public bool Success { get; set; }
        public string ItemName { get; set; }
        public double? ChaosPrice { get; set; }
        public double? DivinePrice { get; set; }
        public double? Trend { get; set; }
    }
}
```

---

### Step 3: WPF ViewModel 작성

```csharp
// PathcraftAI.UI/ViewModels/MainViewModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PathcraftAI.Core;
using System.Collections.ObjectModel;
using System.Threading.Tasks;

namespace PathcraftAI.UI.ViewModels
{
    public partial class MainViewModel : ObservableObject
    {
        private readonly PythonBackend _backend;

        [ObservableProperty]
        private string _searchKeyword = "Kinetic Fusillade";

        [ObservableProperty]
        private bool _isSearching;

        [ObservableProperty]
        private ObservableCollection<BuildInfo> _searchResults = new();

        [ObservableProperty]
        private string _statusMessage = "Ready";

        public MainViewModel()
        {
            var pythonPath = @"C:\Path\To\Python\python.exe";
            var scriptPath = @"C:\Path\To\PathcraftAI\src\PathcraftAI.Parser\pathcraft_cli.py";

            _backend = new PythonBackend(pythonPath, scriptPath);
        }

        [RelayCommand]
        private async Task SearchBuilds()
        {
            if (string.IsNullOrWhiteSpace(SearchKeyword))
                return;

            IsSearching = true;
            StatusMessage = $"Searching for '{SearchKeyword}'...";

            try
            {
                var result = await _backend.SearchBuilds(SearchKeyword);

                if (result.Success)
                {
                    SearchResults.Clear();
                    foreach (var build in result.Results)
                    {
                        SearchResults.Add(build);
                    }

                    StatusMessage = $"Found {result.TotalFound} builds";
                }
                else
                {
                    StatusMessage = "No results found";
                }
            }
            catch (Exception ex)
            {
                StatusMessage = $"Error: {ex.Message}";
            }
            finally
            {
                IsSearching = false;
            }
        }

        [RelayCommand]
        private async Task GenerateGuide(BuildInfo build)
        {
            StatusMessage = $"Generating guide for {build.BuildName}...";

            try
            {
                var result = await _backend.GenerateGuide(build.BuildName, "mock");

                if (result.Success)
                {
                    StatusMessage = $"Guide generated: {result.GuideFile}";

                    // 가이드 파일 열기
                    System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                    {
                        FileName = result.GuideFile,
                        UseShellExecute = true
                    });
                }
            }
            catch (Exception ex)
            {
                StatusMessage = $"Error: {ex.Message}";
            }
        }
    }
}
```

---

### Step 4: WPF View (XAML)

```xml
<!-- PathcraftAI.UI/Views/MainWindow.xaml -->
<Window x:Class="PathcraftAI.UI.Views.MainWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:vm="clr-namespace:PathcraftAI.UI.ViewModels"
        Title="PathcraftAI - Build Search" Height="600" Width="900">

    <Window.DataContext>
        <vm:MainViewModel />
    </Window.DataContext>

    <Grid Margin="20">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="*"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>

        <!-- Search Box -->
        <StackPanel Grid.Row="0" Margin="0,0,0,20">
            <TextBlock Text="Search for POE Builds" FontSize="20" FontWeight="Bold" Margin="0,0,0,10"/>

            <Grid>
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="Auto"/>
                </Grid.ColumnDefinitions>

                <TextBox Grid.Column="0"
                         Text="{Binding SearchKeyword, UpdateSourceTrigger=PropertyChanged}"
                         FontSize="14"
                         Padding="10"
                         Margin="0,0,10,0"
                         VerticalContentAlignment="Center"/>

                <Button Grid.Column="1"
                        Content="Search"
                        Command="{Binding SearchBuildsCommand}"
                        IsEnabled="{Binding IsSearching, Converter={StaticResource InverseBoolConverter}}"
                        Padding="20,10"
                        FontSize="14"/>
            </Grid>
        </StackPanel>

        <!-- Results List -->
        <ListView Grid.Row="1" ItemsSource="{Binding SearchResults}">
            <ListView.ItemTemplate>
                <DataTemplate>
                    <Border BorderBrush="LightGray" BorderThickness="1" Padding="10" Margin="0,5">
                        <Grid>
                            <Grid.RowDefinitions>
                                <RowDefinition Height="Auto"/>
                                <RowDefinition Height="Auto"/>
                                <RowDefinition Height="Auto"/>
                            </Grid.RowDefinitions>

                            <TextBlock Grid.Row="0" Text="{Binding BuildName}" FontWeight="Bold" FontSize="16"/>
                            <TextBlock Grid.Row="1" Margin="0,5">
                                <Run Text="Class: "/><Run Text="{Binding Class}"/>
                                <Run Text=" | "/><Run Text="Ascendancy: "/><Run Text="{Binding Ascendancy}"/>
                                <Run Text=" | "/><Run Text="Level: "/><Run Text="{Binding Level}"/>
                            </TextBlock>

                            <Button Grid.Row="2"
                                    Content="Generate Build Guide"
                                    Command="{Binding DataContext.GenerateGuideCommand, RelativeSource={RelativeSource AncestorType=ListView}}"
                                    CommandParameter="{Binding}"
                                    HorizontalAlignment="Left"
                                    Margin="0,5,0,0"/>
                        </Grid>
                    </Border>
                </DataTemplate>
            </ListView.ItemTemplate>
        </ListView>

        <!-- Status Bar -->
        <Border Grid.Row="2"
                Background="LightGray"
                Padding="10"
                Margin="0,10,0,0">
            <TextBlock Text="{Binding StatusMessage}"/>
        </Border>
    </Grid>
</Window>
```

---

## Configuration Management

### appsettings.json

```json
{
  "PathcraftAI": {
    "PythonPath": "C:\\Path\\To\\Python\\python.exe",
    "ScriptPath": "C:\\Path\\To\\PathcraftAI\\src\\PathcraftAI.Parser\\pathcraft_cli.py",
    "CacheDirectory": "C:\\Path\\To\\PathcraftAI\\build_data",
    "LLM": {
      "Provider": "mock",
      "OpenAI_API_Key": "",
      "Anthropic_API_Key": ""
    }
  }
}
```

---

## Project Structure

```
PathcraftAI/
├── src/
│   ├── PathcraftAI.Core/           # C# 비즈니스 로직
│   │   ├── PythonBackend.cs        # Python 통신 래퍼
│   │   ├── Models/
│   │   │   ├── BuildInfo.cs
│   │   │   ├── ItemPrice.cs
│   │   │   └── BuildGuide.cs
│   │   └── Services/
│   │       ├── BuildSearchService.cs
│   │       └── ConfigurationService.cs
│   │
│   ├── PathcraftAI.UI/             # WPF UI
│   │   ├── Views/
│   │   │   ├── MainWindow.xaml
│   │   │   ├── BuildDetailView.xaml
│   │   │   └── SettingsView.xaml
│   │   ├── ViewModels/
│   │   │   ├── MainViewModel.cs
│   │   │   ├── BuildDetailViewModel.cs
│   │   │   └── SettingsViewModel.cs
│   │   └── App.xaml
│   │
│   └── PathcraftAI.Parser/         # Python 백엔드 (기존)
│       ├── pathcraft_cli.py        # 새로 추가
│       ├── demo_build_search.py
│       ├── build_guide_generator.py
│       └── ...
│
├── docs/
│   └── CSHARP_INTEGRATION_PLAN.md  # 이 문서
│
└── PathcraftAI.sln
```

---

## Testing Strategy

### Unit Tests

```csharp
// PathcraftAI.Tests/PythonBackendTests.cs
using Xunit;
using PathcraftAI.Core;

public class PythonBackendTests
{
    [Fact]
    public async Task SearchBuilds_ValidKeyword_ReturnsResults()
    {
        // Arrange
        var backend = new PythonBackend("python", "pathcraft_cli.py");

        // Act
        var result = await backend.SearchBuilds("Mageblood");

        // Assert
        Assert.True(result.Success);
        Assert.NotEmpty(result.Results);
    }

    [Fact]
    public async Task GetItemPrice_KnownItem_ReturnsPrice()
    {
        // Arrange
        var backend = new PythonBackend("python", "pathcraft_cli.py");

        // Act
        var result = await backend.GetItemPrice("Mageblood");

        // Assert
        Assert.True(result.Success);
        Assert.True(result.ChaosPrice > 0);
    }
}
```

---

## Deployment Considerations

### Python Distribution

**Option A: Bundled Python**
- PyInstaller로 Python 스크립트를 .exe로 패키징
- 사용자 PC에 Python 설치 불필요
- 파일 크기 증가 (~50-100MB)

**Option B: Python Installer**
- 앱 설치 시 Python 자동 설치
- 업데이트 용이
- 사용자 환경 오염 가능성

**추천**: Option A (PyInstaller)

```bash
# 패키징 명령
pyinstaller --onefile --name pathcraft_cli pathcraft_cli.py
```

---

## Next Steps

### Immediate (This Week)
1. ✅ `pathcraft_cli.py` 작성
2. ✅ C# `PythonBackend` 클래스 구현
3. ✅ 간단한 WPF 프로토타입

### Short-term (Next Week)
4. 전체 기능 통합 (검색, 가이드 생성, 가격 조회)
5. UI 디자인 개선
6. 에러 처리 강화

### Mid-term (Next Month)
7. PyInstaller 배포 파일 생성
8. 자동 업데이트 시스템
9. 베타 테스트

---

## Estimated Timeline

| Task | Time | Status |
|------|------|--------|
| Python CLI 작성 | 2 hours | ⏳ To Do |
| C# Backend 래퍼 | 4 hours | ⏳ To Do |
| WPF UI 프로토타입 | 6 hours | ⏳ To Do |
| 통합 테스트 | 4 hours | ⏳ To Do |
| UI 디자인 | 8 hours | ⏳ To Do |
| 배포 준비 | 4 hours | ⏳ To Do |
| **Total** | **~3-4 days** | |

---

## Conclusion

Process Communication 방식을 사용하여 Python 백엔드와 C# WPF를 연동합니다.

**핵심 구현**:
1. `pathcraft_cli.py` - JSON 기반 CLI
2. `PythonBackend.cs` - C# 프로세스 래퍼
3. MVVM 패턴의 WPF UI

이 방식은 구현이 간단하고, 디버깅이 쉬우며, Python 코드 수정 시 재컴파일이 필요 없어 개발 효율이 높습니다.

---

**작성일**: 2025-11-15
**작성자**: PathcraftAI Development Team
