using System.Text.Json;
using PathcraftAI.Core.Models;

namespace PathcraftAI.Core.Services
{
    public sealed class ReasoningFiller
    {
        private readonly Templates _tpl;

        private ReasoningFiller(Templates tpl) { _tpl = tpl; }

        public static ReasoningFiller LoadFrom(string baseDir)
        {
            // baseDir = Core/Resources/Reasoning/ 까지 들어오게 기대
            var path = Path.Combine(baseDir, "reasoning.templates.json");
            if (!File.Exists(path)) throw new FileNotFoundException(path);
            var json = File.ReadAllText(path);
            var tpl = JsonSerializer.Deserialize<Templates>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            }) ?? new Templates();
            return new ReasoningFiller(tpl);
        }

        public int FillMissing(BuildModel model)
        {
            if (model.Gear == null) return 0;
            int filled = 0;

            foreach (var g in model.Gear)
            {
                if (g.Reasoning?.Text is { Length: > 0 }) continue;

                // 태그 매칭: 이름/슬롯 기반으로 유추된 태그로 매칭
                var implied = InferTags(g);
                var impliedSet = new HashSet<string>(implied, StringComparer.OrdinalIgnoreCase);

                // 최적화: Intersect 대신 HasIntersect 구현으로 불필요한 전체 교집합 계산 방지
                GearTpl? match = null;
                foreach (var t in _tpl.Gear)
                {
                    if (!string.Equals(t.Slot, g.Slot, StringComparison.OrdinalIgnoreCase))
                        continue;

                    // 태그 교집합 확인 (최적화: 하나라도 일치하면 break)
                    if (t.Match?.TagsAny != null)
                    {
                        bool hasMatch = false;
                        foreach (var tag in t.Match.TagsAny)
                        {
                            if (impliedSet.Contains(tag))
                            {
                                hasMatch = true;
                                break;
                            }
                        }
                        if (hasMatch)
                        {
                            match = t;
                            break;
                        }
                    }
                }

                if (match != null)
                {
                    g.Reasoning ??= new Reasoning();
                    g.Reasoning.Text = match.Text;
                    g.Reasoning.Source = "template";
                    g.Reasoning.Tags = match.Tags?.ToList();
                    filled++;
                }
            }

            // 슬롯별 템플릿 미매칭이면 전역 fallback
            foreach (var g in model.Gear)
            {
                if (g.Reasoning?.Text is { Length: > 0 }) continue;
                g.Reasoning ??= new Reasoning();
                g.Reasoning.Text = _tpl.Fallback?.Text ?? "기본 보조 슬롯.";
                g.Reasoning.Source = "template";
                g.Reasoning.Tags = _tpl.Fallback?.Tags?.ToList() ?? new List<string> { "General" };
                filled++;
            }

            return filled;
        }

        private static IEnumerable<string> InferTags(GearItem g)
        {
            var name = (g.Name ?? "").ToLowerInvariant();
            // 아주 얕은 규칙. 필요하면 Rules 쪽과 합칠 수 있음.
            if (name.Contains("void") || name.Contains("wand") || name.Contains("battery")) yield return "spell";
            if (name.Contains("crit") || name.Contains("battery")) yield return "crit";
            if (name.Contains("loreweave")) { yield return "res"; yield return "life"; }
            if (g.Slot.Equals("Ring", StringComparison.OrdinalIgnoreCase)) yield return "res";
            if (g.Slot.Equals("Chest", StringComparison.OrdinalIgnoreCase)) { yield return "life"; yield return "armour"; }
        }

        // DTOs
        private sealed class Templates
        {
            public Meta? Meta { get; set; }
            public List<GearTpl> Gear { get; set; } = new();
            public Fallback? Fallback { get; set; }
        }
        private sealed class Meta { public int Version { get; set; } }
        private sealed class GearTpl
        {
            public string Slot { get; set; } = "";
            public Match? Match { get; set; }
            public string Text { get; set; } = "";
            public string[]? Tags { get; set; }
        }
        private sealed class Match { public string[]? TagsAny { get; set; } }
        private sealed class Fallback { public string Text { get; set; } = ""; public string[]? Tags { get; set; } }
    }
}
