namespace PathcraftAI.Core.Rules
{
    public class ResistBaseline
    {
        public string Id { get; set; } = "";
        public string Description { get; set; } = "";
        public string[] Targets { get; set; } = Array.Empty<string>();
        public List<ResistReq> Rules { get; set; } = new();
    }
    public class ResistReq
    {
        public string League { get; set; } = "any";
        public int MapTierMin { get; set; } = 0;
        public Dictionary<string, int> Requirements { get; set; } = new();
    }

    public class ThresholdRule
    {
        public string Id { get; set; } = "";
        public string Severity { get; set; } = "Suggestion";
        public string Message { get; set; } = "";
        public When? When { get; set; }
        public Detect Detect { get; set; } = new();
        public List<string>? Suggestions { get; set; }
    }
    public class When { public string? Mode { get; set; } }
    public class Detect
    {
        public string Path { get; set; } = ""; // e.g., "stats.res.chaos"
        public double? Lt { get; set; }
        public double? Lte { get; set; }
        public double? Gt { get; set; }
        public double? Gte { get; set; }
    }

    public class GearAlias
    {
        public string Id { get; set; } = "";
        public Normalize Normalize { get; set; } = new();
    }
    public class Normalize { public Dictionary<string, string[]> Map { get; set; } = new(); }
}
