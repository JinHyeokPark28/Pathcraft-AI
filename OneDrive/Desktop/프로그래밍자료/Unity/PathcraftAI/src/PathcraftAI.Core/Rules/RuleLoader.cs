using System.Text.Json;

namespace PathcraftAI.Core.Rules
{
    public static class RuleLoader
    {
        static readonly JsonSerializerOptions J = new()
        {
            PropertyNameCaseInsensitive = true,
            AllowTrailingCommas = true,
            ReadCommentHandling = JsonCommentHandling.Skip
        };

        public static T Load<T>(string path)
        {
            var json = File.ReadAllText(path);
            return JsonSerializer.Deserialize<T>(json, J)!;
        }
    }
}
