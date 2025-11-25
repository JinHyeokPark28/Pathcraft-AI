using System;

namespace PathcraftAI.Core
{
    /// <summary>
    /// DAT64 추출기 테스트용 진입점
    /// </summary>
    public static class TestDatExtractor
    {
        public static void Main(string[] args)
        {
            string poePath = args.Length > 0 ? args[0] : @"C:\Daum Games\Path of Exile";
            string outputPath = args.Length > 1 ? args[1] : @".\korean_dat_data.json";

            Console.Error.WriteLine($"POE Path: {poePath}");
            Console.Error.WriteLine($"Output: {outputPath}");
            Console.Error.WriteLine();

            using var gameData = new GameDataExtractor(poePath);

            if (!gameData.Initialize())
            {
                Console.Error.WriteLine("[ERROR] Failed to initialize GameDataExtractor");
                return;
            }

            // 먼저 한국어 데이터 디렉토리 목록 확인
            Console.Error.WriteLine("=== Korean Data Files ===");
            var files = gameData.ListFiles("Data/Korean");
            foreach (var file in files)
            {
                Console.Error.WriteLine($"  {file}");
            }
            Console.Error.WriteLine();

            // DAT64 파싱 테스트
            Console.Error.WriteLine("=== Extracting Korean Translations ===");
            var extractor = new KoreanDatExtractor(gameData);
            extractor.SaveToJson(outputPath);

            Console.Error.WriteLine();
            Console.Error.WriteLine("[완료] DAT64 extraction completed");
        }
    }
}
