using System;
using System.IO;
using System.Text.Json;
using PathcraftAI.Core.Models;


namespace PathcraftAI.Overlay.Services

{
    public static class BuildSnapshotLoader
    {
        public static BuildSnapshot? TryLoad(string jsonPath)
        {
            try
            {
                if (!File.Exists(jsonPath)) return null;
                var json = File.ReadAllText(jsonPath);
                var model = JsonSerializer.Deserialize<BuildModel>(json,
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
                if (model == null) return null;

                return new BuildSnapshot
                {
                    CharacterName = model.Character?.Name ?? "(unknown)",
                    ClassAscendancy = $"{model.Character?.Class}/{model.Character?.Ascendancy}",
                    Dps = model.Stats?.Dps ?? 0,
                    Ehp = model.Stats?.Ehp ?? 0,
                    ResistLine = model.Stats?.Res is { } r
                        ? $"F{r.Fire}/C{r.Cold}/L{r.Lightning}/Ch{r.Chaos}"
                        : "Res N/A"
                };
            }
            catch { return null; }
        }
    }
}
