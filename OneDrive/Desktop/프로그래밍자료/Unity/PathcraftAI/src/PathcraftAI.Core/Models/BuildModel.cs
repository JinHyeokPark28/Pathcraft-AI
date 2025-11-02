namespace PathcraftAI.Core.Models
{
    public class BuildModel
    {
        public Meta Meta { get; set; } = new();
        public CharacterInfo Character { get; set; } = new();
        public Stats Stats { get; set; } = new();
        public List<GearItem> Gear { get; set; } = new();
        public List<Issue> Issues { get; set; } = new();
    }

    public class Meta
    {
        public string Mode { get; set; } = "SC";
        public string League { get; set; } = "Unknown";
        public string? Build_Notes { get; set; }
        public string Source { get; set; } = "pob";
    }

    public class CharacterInfo
    {
        public string Name { get; set; } = "";
        public string Class { get; set; } = "";
        public string Ascendancy { get; set; } = "";
        public int Level { get; set; }
    }

    public class Stats
    {
        public double Dps { get; set; }
        public double Ehp { get; set; }
        public Resist Res { get; set; } = new();
    }

    public class Resist
    {
        public int Fire { get; set; }
        public int Cold { get; set; }
        public int Lightning { get; set; }
        public int Chaos { get; set; }
    }

    public class GearItem
    {
        public string Slot { get; set; } = "";
        public string Name { get; set; } = "";
        public Reasoning? Reasoning { get; set; }
        public List<string>? Alternatives { get; set; }
    }

    public class Reasoning
    {
        public string? Text { get; set; }
        public string? Source { get; set; } // "notes" | "community" | "ai"
        public List<string>? Tags { get; set; }
    }

    public class Issue
    {
        public string Level { get; set; } = "Suggestion"; // Critical/Warning/Suggestion
        public string Message { get; set; } = "";
        public List<string>? Suggestions { get; set; }
        public string? Code { get; set; } // e.g., CHAOS_RES_LOW
    }
}
