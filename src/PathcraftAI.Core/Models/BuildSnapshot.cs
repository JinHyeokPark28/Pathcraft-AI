namespace PathcraftAI.Core.Models
{
    public sealed class BuildSnapshot
    {
        public string CharacterName { get; set; } = "(unknown)";
        public string ClassAscendancy { get; set; } = "";
        public double Dps { get; set; }
        public double Ehp { get; set; }
        public string ResistLine { get; set; } = "";
    }
}
