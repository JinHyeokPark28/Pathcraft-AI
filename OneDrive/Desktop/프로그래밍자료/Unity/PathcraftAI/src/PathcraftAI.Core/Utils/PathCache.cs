using System;
using System.IO;

namespace PathcraftAI.Core.Utils
{
    /// <summary>
    /// 프로젝트 경로를 캐싱하여 반복적인 디렉토리 탐색을 방지합니다.
    /// 1차 초기화 시에만 탐색을 수행하고, 이후는 캐시된 값을 반환합니다.
    /// </summary>
    public static class PathCache
    {
        private static string? _cachedParserDir;
        private static string? _cachedBuildOutputJson;

        /// <summary>
        /// Parser 폴더 경로를 가져옵니다 (캐싱됨).
        /// AppContext.BaseDirectory에서 상위 8단계까지 탐색합니다.
        /// </summary>
        public static string GetParserDir()
        {
            if (_cachedParserDir != null)
                return _cachedParserDir;

            string? cur = AppContext.BaseDirectory;
            for (int i = 0; i < 8 && !string.IsNullOrEmpty(cur); i++)
            {
                var candidate = Path.Combine(cur, "src", "PathcraftAI.Parser");
                if (File.Exists(Path.Combine(candidate, "pob_parser.py")))
                {
                    _cachedParserDir = candidate;
                    return candidate;
                }

                cur = Directory.GetParent(cur)?.FullName;
            }

            throw new DirectoryNotFoundException(
                "Parser directory not found. Expected: src\\PathcraftAI.Parser with pob_parser.py");
        }

        /// <summary>
        /// build_output.json 파일 경로를 가져옵니다 (캐싱됨).
        /// </summary>
        public static string GetBuildOutputPath()
        {
            if (_cachedBuildOutputJson != null)
                return _cachedBuildOutputJson;

            var parserDir = GetParserDir();
            var path = Path.Combine(parserDir, "build_output.json");
            _cachedBuildOutputJson = path;
            return path;
        }

        /// <summary>
        /// 캐시를 초기화합니다 (테스트 또는 경로 변경 시 사용).
        /// </summary>
        public static void ClearCache()
        {
            _cachedParserDir = null;
            _cachedBuildOutputJson = null;
        }
    }
}
