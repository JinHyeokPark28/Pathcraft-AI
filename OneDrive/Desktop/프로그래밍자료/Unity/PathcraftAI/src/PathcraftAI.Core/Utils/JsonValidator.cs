using System.Text.Json;

namespace PathcraftAI.Core.Utils
{
    public static class JsonValidator
    {
        private static readonly JsonSerializerOptions Options = new()
        {
            PropertyNameCaseInsensitive = true,
            ReadCommentHandling = JsonCommentHandling.Skip,
            AllowTrailingCommas = true
        };

        public static T Load<T>(string jsonPath)
        {
            if (!File.Exists(jsonPath))
                throw new FileNotFoundException(jsonPath);

            var json = File.ReadAllText(jsonPath);
            var obj = JsonSerializer.Deserialize<T>(json, Options);
            if (obj == null)
                throw new InvalidDataException("JSON deserialize result was null.");
            return obj;
        }
    }
}
