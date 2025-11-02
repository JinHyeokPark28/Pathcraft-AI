using System;
using System.Diagnostics;
using System.IO;
using PathcraftAI.Core.Utils;

namespace PathcraftAI.Parser
{
    /// <summary>
    /// Python 스크립트 실행기.
    /// PathCache를 사용하여 반복적인 경로 탐색을 방지합니다.
    /// </summary>
    public static class PythonRunner
    {
        public static (int exitCode, string stdout, string stderr) Run(string? args)
        {
            try
            {
                // 경로 캐싱 사용 (반복적인 탐색 방지)
                var parserDir = PathCache.GetParserDir();
                var exePath = Path.Combine(parserDir, @".venv\Scripts\python.exe");
                var script = Path.Combine(parserDir, "pob_parser.py");

                if (!File.Exists(exePath))
                    return (-2, "", $"python.exe not found: {exePath}");
                if (!File.Exists(script))
                    return (-3, "", $"pob_parser.py not found: {script}");

                var psi = new ProcessStartInfo
                {
                    FileName = exePath,
                    Arguments = $"\"{script}\" {args ?? ""}",
                    WorkingDirectory = parserDir,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var p = Process.Start(psi)!;
                var stdout = p.StandardOutput.ReadToEnd();
                var stderr = p.StandardError.ReadToEnd();
                p.WaitForExit();
                return (p.ExitCode, stdout, stderr);
            }
            catch (Exception ex)
            {
                // 라이브러리층이므로 UI 호출 금지, 문자열로만 반환
                return (-1, "", $"[PythonRunner Exception] {ex.GetType().Name}: {ex.Message}");
            }
        }
    }
}
