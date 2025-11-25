using System;
using System.Collections.Generic;
using System.Text.Json;
using System.IO;

namespace PathcraftAI.Core
{
    /// <summary>
    /// POE 한국어 DAT64 파일에서 번역 데이터 추출
    /// </summary>
    public class KoreanDatExtractor
    {
        private readonly GameDataExtractor _gameData;

        public KoreanDatExtractor(GameDataExtractor gameData)
        {
            _gameData = gameData;
        }

        /// <summary>
        /// BaseItemTypes.dat64에서 아이템 이름 추출
        /// </summary>
        public Dictionary<string, string> ExtractBaseItemTypes()
        {
            var result = new Dictionary<string, string>();
            var data = _gameData.ExtractFile("Data/Korean/BaseItemTypes.dat64");

            if (data == null)
            {
                Console.Error.WriteLine("[WARN] BaseItemTypes.dat64 not found");
                return result;
            }

            var parser = new Dat64Parser();
            if (!parser.Load(data))
                return result;

            Console.Error.WriteLine($"[INFO] BaseItemTypes: {parser.RowCount} rows");

            // BaseItemTypes 스키마 (주요 필드만)
            // Id(string), Name(string), ...
            // 행 크기는 대략 152바이트 (3.27 기준, 버전에 따라 다를 수 있음)
            int rowSize = EstimateRowSize(parser, 152);

            for (int i = 0; i < parser.RowCount; i++)
            {
                int offset = parser.GetRowOffset(i, rowSize);

                try
                {
                    // 첫 번째 필드: Id (string offset)
                    long idOffset = parser.ReadInt64(offset);
                    string? id = parser.ReadString(idOffset);

                    // 두 번째 필드: Name (string offset)
                    long nameOffset = parser.ReadInt64(offset + 8);
                    string? name = parser.ReadString(nameOffset);

                    if (!string.IsNullOrEmpty(id) && !string.IsNullOrEmpty(name))
                    {
                        result[id] = name;
                    }
                }
                catch (Exception ex)
                {
                    Console.Error.WriteLine($"[WARN] Error parsing row {i}: {ex.Message}");
                }
            }

            Console.Error.WriteLine($"[OK] Extracted {result.Count} base item types");
            return result;
        }

        /// <summary>
        /// ActiveSkills.dat64에서 스킬 이름 추출
        /// </summary>
        public Dictionary<string, string> ExtractActiveSkills()
        {
            var result = new Dictionary<string, string>();
            var data = _gameData.ExtractFile("Data/Korean/ActiveSkills.dat64");

            if (data == null)
            {
                Console.Error.WriteLine("[WARN] ActiveSkills.dat64 not found");
                return result;
            }

            var parser = new Dat64Parser();
            if (!parser.Load(data))
                return result;

            Console.Error.WriteLine($"[INFO] ActiveSkills: {parser.RowCount} rows");

            // ActiveSkills 스키마
            // Id(string), DisplayedName(string), ...
            int rowSize = EstimateRowSize(parser, 120);

            for (int i = 0; i < parser.RowCount; i++)
            {
                int offset = parser.GetRowOffset(i, rowSize);

                try
                {
                    long idOffset = parser.ReadInt64(offset);
                    string? id = parser.ReadString(idOffset);

                    long nameOffset = parser.ReadInt64(offset + 8);
                    string? name = parser.ReadString(nameOffset);

                    if (!string.IsNullOrEmpty(id) && !string.IsNullOrEmpty(name))
                    {
                        result[id] = name;
                    }
                }
                catch (Exception ex)
                {
                    Console.Error.WriteLine($"[WARN] Error parsing row {i}: {ex.Message}");
                }
            }

            Console.Error.WriteLine($"[OK] Extracted {result.Count} active skills");
            return result;
        }

        /// <summary>
        /// SkillGems.dat64에서 젬 이름 추출
        /// </summary>
        public Dictionary<string, string> ExtractSkillGems()
        {
            var result = new Dictionary<string, string>();
            var data = _gameData.ExtractFile("Data/Korean/SkillGems.dat64");

            if (data == null)
            {
                Console.Error.WriteLine("[WARN] SkillGems.dat64 not found");
                return result;
            }

            var parser = new Dat64Parser();
            if (!parser.Load(data))
                return result;

            Console.Error.WriteLine($"[INFO] SkillGems: {parser.RowCount} rows");

            // SkillGems는 BaseItemTypesKey를 참조하므로 별도 처리 필요
            // 여기서는 기본 구조만 파싱
            int rowSize = EstimateRowSize(parser, 80);

            for (int i = 0; i < parser.RowCount; i++)
            {
                int offset = parser.GetRowOffset(i, rowSize);

                try
                {
                    // SkillGems의 첫 필드는 보통 BaseItemTypesKey (foreign key)
                    // 실제 이름은 BaseItemTypes에서 가져와야 함
                    long keyOffset = parser.ReadInt64(offset);

                    // 간단히 인덱스를 키로 사용
                    result[$"gem_{i}"] = $"row_{keyOffset}";
                }
                catch
                {
                    // Skip errors
                }
            }

            Console.Error.WriteLine($"[OK] Extracted {result.Count} skill gems");
            return result;
        }

        /// <summary>
        /// Stats.dat64에서 스탯 ID 추출
        /// </summary>
        public Dictionary<string, string> ExtractStats()
        {
            var result = new Dictionary<string, string>();
            var data = _gameData.ExtractFile("Data/Korean/Stats.dat64");

            if (data == null)
            {
                Console.Error.WriteLine("[WARN] Stats.dat64 not found");
                return result;
            }

            var parser = new Dat64Parser();
            if (!parser.Load(data))
                return result;

            Console.Error.WriteLine($"[INFO] Stats: {parser.RowCount} rows");

            // Stats 스키마
            // Id(string), ...
            int rowSize = EstimateRowSize(parser, 48);

            for (int i = 0; i < parser.RowCount; i++)
            {
                int offset = parser.GetRowOffset(i, rowSize);

                try
                {
                    long idOffset = parser.ReadInt64(offset);
                    string? id = parser.ReadString(idOffset);

                    if (!string.IsNullOrEmpty(id))
                    {
                        result[id] = id; // Stats는 보통 ID만 있음
                    }
                }
                catch
                {
                    // Skip errors
                }
            }

            Console.Error.WriteLine($"[OK] Extracted {result.Count} stats");
            return result;
        }

        /// <summary>
        /// PassiveSkills.dat64에서 패시브 스킬 이름 추출
        /// </summary>
        public Dictionary<string, string> ExtractPassiveSkills()
        {
            var result = new Dictionary<string, string>();
            var data = _gameData.ExtractFile("Data/Korean/PassiveSkills.dat64");

            if (data == null)
            {
                Console.Error.WriteLine("[WARN] PassiveSkills.dat64 not found");
                return result;
            }

            var parser = new Dat64Parser();
            if (!parser.Load(data))
                return result;

            Console.Error.WriteLine($"[INFO] PassiveSkills: {parser.RowCount} rows");

            // PassiveSkills 스키마
            // Id(string), Name(string), ...
            int rowSize = EstimateRowSize(parser, 200);

            for (int i = 0; i < parser.RowCount; i++)
            {
                int offset = parser.GetRowOffset(i, rowSize);

                try
                {
                    long idOffset = parser.ReadInt64(offset);
                    string? id = parser.ReadString(idOffset);

                    // Name은 보통 두 번째나 세 번째 필드
                    long nameOffset = parser.ReadInt64(offset + 8);
                    string? name = parser.ReadString(nameOffset);

                    if (!string.IsNullOrEmpty(id) && !string.IsNullOrEmpty(name))
                    {
                        result[id] = name;
                    }
                }
                catch
                {
                    // Skip errors
                }
            }

            Console.Error.WriteLine($"[OK] Extracted {result.Count} passive skills");
            return result;
        }

        /// <summary>
        /// 모든 한국어 데이터 추출
        /// </summary>
        public Dictionary<string, Dictionary<string, string>> ExtractAll()
        {
            var result = new Dictionary<string, Dictionary<string, string>>
            {
                ["base_items"] = ExtractBaseItemTypes(),
                ["active_skills"] = ExtractActiveSkills(),
                ["skill_gems"] = ExtractSkillGems(),
                ["stats"] = ExtractStats(),
                ["passive_skills"] = ExtractPassiveSkills()
            };

            return result;
        }

        /// <summary>
        /// 추출된 데이터를 JSON으로 저장
        /// </summary>
        public void SaveToJson(string outputPath)
        {
            var data = ExtractAll();

            var options = new JsonSerializerOptions
            {
                WriteIndented = true,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            };

            var json = JsonSerializer.Serialize(data, options);
            File.WriteAllText(outputPath, json, System.Text.Encoding.UTF8);

            Console.Error.WriteLine($"[OK] Saved Korean DAT data to: {outputPath}");
        }

        /// <summary>
        /// 행 크기 추정 (고정 데이터 크기 / 행 수)
        /// </summary>
        private int EstimateRowSize(Dat64Parser parser, int defaultSize)
        {
            if (parser.RowCount == 0)
                return defaultSize;

            int fixedDataSize = parser.FixedDataSize;
            int estimated = fixedDataSize / parser.RowCount;

            // 합리적인 범위인지 확인
            if (estimated > 8 && estimated < 1000)
            {
                return estimated;
            }

            return defaultSize;
        }
    }
}
