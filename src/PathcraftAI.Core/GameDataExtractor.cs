using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json;
using LibBundle3;
using LibBundle3.Nodes;
using LibBundledGGPK3;
using LibGGPK3;

namespace PathcraftAI.Core
{
    /// <summary>
    /// POE 게임 데이터 추출 서비스
    /// Bundle 파일에서 한국어 번역, 패시브 트리, 스킬 데이터 등을 추출
    /// 구형 GGPK와 신형 Bundles2 모두 지원
    /// </summary>
    public class GameDataExtractor : IDisposable
    {
        // 신형 (Bundles2 + Oodle)
        private BundledGGPK? _bundledGgpk;
        private DirectoryNode? _root;

        // 구형 (Content.ggpk without Oodle)
        private GGPK? _legacyGgpk;

        private readonly string _poePath;
        private bool _disposed;
        private bool _isLegacyFormat;

        public GameDataExtractor(string poePath)
        {
            _poePath = poePath;
        }

        /// <summary>
        /// Bundle 인덱스 로드 (구형/신형 자동 감지)
        /// </summary>
        public bool Initialize()
        {
            var ggpkPath = Path.Combine(_poePath, "Content.ggpk");
            var bundles2Path = Path.Combine(_poePath, "Bundles2");

            // 1. Bundles2 폴더가 디스크에 있으면 신형 (POE2 / 국제 POE1)
            if (Directory.Exists(bundles2Path))
            {
                return InitializeNewFormat(ggpkPath);
            }

            // 2. Content.ggpk가 있으면 먼저 로드해서 내부 구조 확인
            if (File.Exists(ggpkPath))
            {
                // 먼저 legacy GGPK로 로드해서 Bundles2가 내부에 있는지 확인
                try
                {
                    var tempGgpk = new GGPK(ggpkPath);
                    bool hasBundles2Inside = tempGgpk.Root.TryFindNode("Bundles2", out _);

                    // Oodle DLL 존재 여부 확인
                    var oodleDllPath = Directory.GetFiles(_poePath, "oo2core*.dll").FirstOrDefault();
                    bool hasOodleDll = !string.IsNullOrEmpty(oodleDllPath);

                    if (hasBundles2Inside)
                    {
                        // Bundles2가 있으면 신형 시도 (Oodle 없으면 자동으로 비압축 모드로 동작할 수 있음)
                        tempGgpk.Dispose();

                        if (hasOodleDll)
                        {
                            Console.Error.WriteLine("[INFO] Detected Bundles2 inside GGPK with Oodle - using new format");
                        }
                        else
                        {
                            Console.Error.WriteLine("[INFO] Detected Bundles2 inside GGPK without Oodle - attempting new format");
                        }

                        // 신형 포맷 시도, 실패하면 legacy로 폴백
                        if (InitializeNewFormat(ggpkPath))
                        {
                            return true;
                        }

                        // 신형 실패시 legacy로 폴백
                        Console.Error.WriteLine("[INFO] Falling back to legacy format");
                        return InitializeLegacyFormat(ggpkPath);
                    }
                    else
                    {
                        // 순수 구형 GGPK
                        _legacyGgpk = tempGgpk;
                        _isLegacyFormat = true;
                        Console.Error.WriteLine($"[INFO] Loaded POE data (legacy format) from: {_poePath}");
                        return true;
                    }
                }
                catch (Exception ex)
                {
                    Console.Error.WriteLine($"[WARN] Failed to detect format: {ex.Message}");
                    // 감지 실패시 구형으로 시도
                    return InitializeLegacyFormat(ggpkPath);
                }
            }

            Console.Error.WriteLine($"[ERROR] No valid POE data found in: {_poePath}");
            return false;
        }

        /// <summary>
        /// 신형 BundledGGPK 초기화 (Oodle 압축)
        /// </summary>
        private bool InitializeNewFormat(string ggpkPath)
        {
            try
            {
                if (!File.Exists(ggpkPath))
                {
                    Console.Error.WriteLine($"[ERROR] Content.ggpk not found: {ggpkPath}");
                    return false;
                }

                _bundledGgpk = new BundledGGPK(ggpkPath, false);
                var failed = _bundledGgpk.Index.ParsePaths();
                if (failed != 0)
                {
                    Console.Error.WriteLine($"[WARN] Failed to parse path of {failed} files");
                }
                _root = _bundledGgpk.Index.BuildTree(true);

                _isLegacyFormat = false;
                Console.Error.WriteLine($"[INFO] Loaded POE data (new format) from: {_poePath}");
                return true;
            }
            catch (DllNotFoundException ex)
            {
                Console.Error.WriteLine($"[ERROR] Failed to initialize: {ex.Message}");
                Console.Error.WriteLine("[INFO] Oodle DLL (oo2core_*.dll) is required. Copy it from POE folder to the output directory.");
                return false;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"[ERROR] Failed to initialize new format: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// 구형 GGPK 초기화 (압축 없음)
        /// </summary>
        private bool InitializeLegacyFormat(string ggpkPath)
        {
            try
            {
                _legacyGgpk = new GGPK(ggpkPath);

                _isLegacyFormat = true;
                Console.Error.WriteLine($"[INFO] Loaded POE data (legacy format) from: {_poePath}");
                return true;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"[ERROR] Failed to initialize legacy format: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// 특정 파일의 내용을 바이트 배열로 추출
        /// </summary>
        public byte[]? ExtractFile(string path)
        {
            if (_isLegacyFormat)
            {
                return ExtractFileLegacy(path);
            }
            else
            {
                return ExtractFileNew(path);
            }
        }

        /// <summary>
        /// 신형 형식에서 파일 추출
        /// </summary>
        private byte[]? ExtractFileNew(string path)
        {
            if (_bundledGgpk == null)
            {
                Console.Error.WriteLine("[ERROR] Not initialized");
                return null;
            }

            try
            {
                if (!_bundledGgpk.Index.TryFindNode(path.TrimEnd('/'), out var node, _root))
                {
                    Console.Error.WriteLine($"[WARN] File not found: {path}");
                    return null;
                }

                if (node is FileNode fileNode)
                {
                    return fileNode.Record.Read().ToArray();
                }

                Console.Error.WriteLine($"[WARN] Not a file: {path}");
                return null;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"[ERROR] Failed to extract {path}: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// 구형 GGPK에서 파일 추출
        /// </summary>
        private byte[]? ExtractFileLegacy(string path)
        {
            if (_legacyGgpk == null)
            {
                Console.Error.WriteLine("[ERROR] Not initialized");
                return null;
            }

            try
            {
                // 구형 GGPK의 Root에서 파일 찾기
                if (!_legacyGgpk.Root.TryFindNode(path, out var node))
                {
                    Console.Error.WriteLine($"[WARN] File not found: {path}");
                    return null;
                }

                if (node is LibGGPK3.Records.FileRecord fileRecord)
                {
                    return fileRecord.Read().ToArray();
                }

                Console.Error.WriteLine($"[WARN] Not a file: {path}");
                return null;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"[ERROR] Failed to extract {path}: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// 텍스트 파일 추출
        /// </summary>
        public string? ExtractTextFile(string path, Encoding? encoding = null)
        {
            var data = ExtractFile(path);
            if (data == null) return null;

            encoding ??= Encoding.UTF8;
            return encoding.GetString(data);
        }

        /// <summary>
        /// 한국어 번역 데이터 추출
        /// </summary>
        public Dictionary<string, string> ExtractKoreanTranslations()
        {
            var translations = new Dictionary<string, string>();

            if (_bundledGgpk == null)
            {
                Console.Error.WriteLine("[ERROR] Not initialized");
                return translations;
            }

            // 한국어 데이터 파일 경로들
            var koreanDataPaths = new[]
            {
                "Data/Korean/ActiveSkills.dat64",
                "Data/Korean/BaseItemTypes.dat64",
                "Data/Korean/SkillGems.dat64",
                "Data/Korean/Stats.dat64",
                "Data/Korean/PassiveSkills.dat64",
            };

            // TODO: DAT64 파싱 로직 구현
            // LibGGPK3는 파일 추출만 지원하고, DAT 파싱은 별도 구현 필요
            Console.Error.WriteLine("[INFO] Korean data paths found:");
            foreach (var path in koreanDataPaths)
            {
                var data = ExtractFile(path);
                if (data != null)
                {
                    Console.Error.WriteLine($"  {path}: {data.Length} bytes");
                }
            }

            return translations;
        }

        /// <summary>
        /// 디렉토리 내 모든 파일 목록 가져오기
        /// </summary>
        public List<string> ListFiles(string directory)
        {
            if (_isLegacyFormat)
            {
                return ListFilesLegacy(directory);
            }
            else
            {
                return ListFilesNew(directory);
            }
        }

        /// <summary>
        /// 신형에서 파일 목록 가져오기
        /// </summary>
        private List<string> ListFilesNew(string directory)
        {
            var files = new List<string>();

            if (_bundledGgpk == null)
            {
                Console.Error.WriteLine("[ERROR] Not initialized");
                return files;
            }

            try
            {
                if (!_bundledGgpk.Index.TryFindNode(directory.TrimEnd('/'), out var node, _root))
                {
                    Console.Error.WriteLine($"[WARN] Directory not found: {directory}");
                    return files;
                }

                if (node is DirectoryNode dirNode)
                {
                    foreach (var child in dirNode.Children)
                    {
                        files.Add(ITreeNode.GetPath(child));
                    }
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"[ERROR] Failed to list {directory}: {ex.Message}");
            }

            return files;
        }

        /// <summary>
        /// 구형에서 파일 목록 가져오기
        /// </summary>
        private List<string> ListFilesLegacy(string directory)
        {
            var files = new List<string>();

            if (_legacyGgpk == null)
            {
                Console.Error.WriteLine("[ERROR] Not initialized");
                return files;
            }

            try
            {
                if (!_legacyGgpk.Root.TryFindNode(directory, out var node))
                {
                    Console.Error.WriteLine($"[WARN] Directory not found: {directory}");
                    return files;
                }

                if (node is LibGGPK3.Records.DirectoryRecord dirRecord)
                {
                    foreach (var child in dirRecord)
                    {
                        files.Add($"{directory}/{child.Name}");
                    }
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"[ERROR] Failed to list {directory}: {ex.Message}");
            }

            return files;
        }

        /// <summary>
        /// 추출된 데이터를 JSON으로 저장
        /// </summary>
        public void SaveToJson(object data, string outputPath)
        {
            var options = new JsonSerializerOptions
            {
                WriteIndented = true,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            };

            var json = JsonSerializer.Serialize(data, options);
            File.WriteAllText(outputPath, json, Encoding.UTF8);
            Console.Error.WriteLine($"[OK] Saved to: {outputPath}");
        }

        public void Dispose()
        {
            if (_disposed) return;

            _bundledGgpk?.Dispose();
            _bundledGgpk = null;

            _legacyGgpk?.Dispose();
            _legacyGgpk = null;

            _disposed = true;

            GC.SuppressFinalize(this);
        }
    }
}
