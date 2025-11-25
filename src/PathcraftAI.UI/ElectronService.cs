using System;
using System.Diagnostics;
using System.IO;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace PathcraftAI.UI
{
    /// <summary>
    /// Electron 모듈과의 IPC 통신을 관리하는 서비스
    /// Lazy Loading, 메모리 모니터링, 자동 종료 지원
    /// </summary>
    public class ElectronService : IDisposable
    {
        private const int IPC_PORT = 47851;
        private const string ELECTRON_PATH = "src/PathcraftAI.Electron";

        private Process? _electronProcess;
        private TcpClient? _client;
        private NetworkStream? _stream;
        private readonly object _lock = new object();
        private int _requestId = 0;
        private bool _isDisposed = false;

        public bool IsRunning => _electronProcess != null && !_electronProcess.HasExited;
        public bool IsConnected => _client?.Connected ?? false;

        /// <summary>
        /// Electron 모듈 시작 (Lazy Loading)
        /// </summary>
        public async Task<bool> StartAsync()
        {
            if (IsRunning)
            {
                return await ConnectAsync();
            }

            try
            {
                var electronExePath = FindElectronExecutable();
                if (string.IsNullOrEmpty(electronExePath))
                {
                    throw new FileNotFoundException("Electron 실행 파일을 찾을 수 없습니다.");
                }

                var startInfo = new ProcessStartInfo
                {
                    FileName = electronExePath,
                    Arguments = ".",
                    WorkingDirectory = GetElectronWorkingDirectory(),
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true
                };

                _electronProcess = Process.Start(startInfo);

                if (_electronProcess == null)
                {
                    throw new Exception("Electron 프로세스를 시작할 수 없습니다.");
                }

                // Wait for IPC server to start
                await Task.Delay(2000);

                return await ConnectAsync();
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Electron start error: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// IPC 서버에 연결
        /// </summary>
        private async Task<bool> ConnectAsync()
        {
            try
            {
                if (_client?.Connected == true)
                {
                    return true;
                }

                _client = new TcpClient();
                await _client.ConnectAsync("127.0.0.1", IPC_PORT);
                _stream = _client.GetStream();

                // Verify connection
                var pingResult = await SendRequestAsync("ping");
                return pingResult != null;
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"IPC connection error: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// JSON-RPC 요청 전송
        /// </summary>
        public async Task<JsonElement?> SendRequestAsync(string method, object? parameters = null)
        {
            if (!await EnsureConnectedAsync())
            {
                return null;
            }

            try
            {
                int id;
                lock (_lock)
                {
                    id = ++_requestId;
                }

                var request = new
                {
                    jsonrpc = "2.0",
                    id,
                    method,
                    @params = parameters
                };

                var json = JsonSerializer.Serialize(request);
                var bytes = Encoding.UTF8.GetBytes(json + "\n");

                await _stream!.WriteAsync(bytes);

                // Read response
                var response = await ReadResponseAsync();
                return response;
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"IPC request error: {ex.Message}");
                return null;
            }
        }

        private async Task<JsonElement?> ReadResponseAsync()
        {
            var buffer = new byte[4096];
            var responseBuilder = new StringBuilder();

            while (true)
            {
                var bytesRead = await _stream!.ReadAsync(buffer);
                if (bytesRead == 0) break;

                var chunk = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                responseBuilder.Append(chunk);

                if (chunk.Contains('\n'))
                {
                    var response = responseBuilder.ToString().Trim();
                    var jsonDoc = JsonDocument.Parse(response);
                    var root = jsonDoc.RootElement;

                    if (root.TryGetProperty("result", out var result))
                    {
                        return result;
                    }
                    else if (root.TryGetProperty("error", out var error))
                    {
                        Debug.WriteLine($"IPC error: {error}");
                        return null;
                    }

                    return root;
                }
            }

            return null;
        }

        private async Task<bool> EnsureConnectedAsync()
        {
            if (IsConnected)
            {
                return true;
            }

            if (!IsRunning)
            {
                return await StartAsync();
            }

            return await ConnectAsync();
        }

        /// <summary>
        /// Trade 창 표시
        /// </summary>
        public async Task<bool> ShowWindowAsync()
        {
            var result = await SendRequestAsync("show");
            return result?.GetProperty("success").GetBoolean() ?? false;
        }

        /// <summary>
        /// Trade 창 숨기기
        /// </summary>
        public async Task<bool> HideWindowAsync()
        {
            var result = await SendRequestAsync("hide");
            return result?.GetProperty("success").GetBoolean() ?? false;
        }

        /// <summary>
        /// URL로 이동
        /// </summary>
        public async Task<bool> NavigateAsync(string url)
        {
            var result = await SendRequestAsync("navigate", new { url });
            return result?.GetProperty("success").GetBoolean() ?? false;
        }

        /// <summary>
        /// 아이템 검색
        /// </summary>
        public async Task<bool> SearchAsync(string league, string? itemName = null,
            string? queryId = null, string? itemType = null, int? links = null,
            string? influence = null, bool? corrupted = null)
        {
            var result = await SendRequestAsync("search", new
            {
                league,
                itemName,
                queryId,
                itemType,
                links,
                influence,
                corrupted
            });
            return result?.GetProperty("success").GetBoolean() ?? false;
        }

        /// <summary>
        /// 메모리 사용량 조회
        /// </summary>
        public async Task<(int heapUsed, int total)?> GetMemoryUsageAsync()
        {
            var result = await SendRequestAsync("getMemory");
            if (result == null) return null;

            return (
                result.Value.GetProperty("heapUsed").GetInt32(),
                result.Value.GetProperty("total").GetInt32()
            );
        }

        /// <summary>
        /// 캐시 상태 조회
        /// </summary>
        public async Task<(int hot, int warm, int cold)?> GetCacheStatusAsync()
        {
            var result = await SendRequestAsync("getCache");
            if (result == null) return null;

            return (
                result.Value.GetProperty("hot").GetInt32(),
                result.Value.GetProperty("warm").GetInt32(),
                result.Value.GetProperty("cold").GetInt32()
            );
        }

        /// <summary>
        /// 캐시 초기화
        /// </summary>
        public async Task<bool> ClearCacheAsync()
        {
            var result = await SendRequestAsync("clearCache");
            return result?.GetProperty("success").GetBoolean() ?? false;
        }

        /// <summary>
        /// 리그 설정
        /// </summary>
        public async Task<bool> SetLeagueAsync(string league)
        {
            var result = await SendRequestAsync("setLeague", new { league });
            return result?.GetProperty("success").GetBoolean() ?? false;
        }

        /// <summary>
        /// Electron 모듈 종료
        /// </summary>
        public async Task ShutdownAsync()
        {
            try
            {
                if (IsConnected)
                {
                    await SendRequestAsync("shutdown");
                }
            }
            catch
            {
                // Ignore shutdown errors
            }
            finally
            {
                Cleanup();
            }
        }

        private string? FindElectronExecutable()
        {
            // Check common locations
            var locations = new[]
            {
                Path.Combine(GetElectronWorkingDirectory(), "node_modules", ".bin", "electron.cmd"),
                Path.Combine(GetElectronWorkingDirectory(), "node_modules", "electron", "dist", "electron.exe"),
                "electron.cmd",  // Global install
                "electron"
            };

            foreach (var location in locations)
            {
                if (File.Exists(location))
                {
                    return location;
                }
            }

            return null;
        }

        private string GetElectronWorkingDirectory()
        {
            var baseDir = AppDomain.CurrentDomain.BaseDirectory;

            // Development: go up from bin/Debug/net8.0-windows
            var devPath = Path.GetFullPath(Path.Combine(baseDir, "..", "..", "..", "..", ELECTRON_PATH));
            if (Directory.Exists(devPath))
            {
                return devPath;
            }

            // Production: electron module in same directory
            var prodPath = Path.Combine(baseDir, "electron");
            if (Directory.Exists(prodPath))
            {
                return prodPath;
            }

            return devPath;
        }

        private void Cleanup()
        {
            try
            {
                _stream?.Close();
                _client?.Close();

                if (_electronProcess != null && !_electronProcess.HasExited)
                {
                    _electronProcess.Kill();
                    _electronProcess.WaitForExit(5000);
                }
            }
            catch
            {
                // Ignore cleanup errors
            }
            finally
            {
                _stream = null;
                _client = null;
                _electronProcess = null;
            }
        }

        public void Dispose()
        {
            if (_isDisposed) return;
            _isDisposed = true;

            Task.Run(async () => await ShutdownAsync()).Wait(5000);
            GC.SuppressFinalize(this);
        }
    }
}
