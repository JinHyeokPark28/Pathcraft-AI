using PathcraftAI.Core;

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

// 루트 디렉토리 확인
Console.Error.WriteLine("=== Root Directory ===");
var rootFiles = gameData.ListFiles("");
foreach (var file in rootFiles.Take(20))
{
    Console.Error.WriteLine($"  {file}");
}
Console.Error.WriteLine();

// Bundles2 내부 확인
Console.Error.WriteLine("=== Bundles2 Directory ===");
var bundles2Files = gameData.ListFiles("Bundles2");
foreach (var file in bundles2Files.Take(30))
{
    Console.Error.WriteLine($"  {file}");
}
if (bundles2Files.Count > 30)
    Console.Error.WriteLine($"  ... and {bundles2Files.Count - 30} more");
Console.Error.WriteLine();

// 한국어 데이터 디렉토리 목록 확인
Console.Error.WriteLine("=== Korean Data Files ===");
var files = gameData.ListFiles("Data/Korean");
if (files.Count == 0)
{
    Console.Error.WriteLine("  (no files found - trying Data directory)");
    files = gameData.ListFiles("Data");
    foreach (var file in files.Take(20))
    {
        Console.Error.WriteLine($"  {file}");
    }
    if (files.Count > 20)
        Console.Error.WriteLine($"  ... and {files.Count - 20} more");
}
else
{
    foreach (var file in files.Take(30))
    {
        Console.Error.WriteLine($"  {file}");
    }
}
Console.Error.WriteLine();

// DAT64 파싱 테스트
Console.Error.WriteLine("=== Extracting Korean Translations ===");
var extractor = new KoreanDatExtractor(gameData);
extractor.SaveToJson(outputPath);

Console.Error.WriteLine();
Console.Error.WriteLine("[완료] DAT64 extraction completed");
