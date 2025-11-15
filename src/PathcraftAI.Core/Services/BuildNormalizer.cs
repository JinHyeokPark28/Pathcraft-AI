using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using PathcraftAI.Core.Models;
using PathcraftAI.Core.Rules;

namespace PathcraftAI.Core.Services
{
    public class BuildNormalizer
    {
        private readonly List<ThresholdRule> _thresholds = new();
        private readonly ResistBaseline? _resist;
        private readonly GearAlias? _aliases;

        public BuildNormalizer(string rulesDir)
        {
            var chaos = Path.Combine(rulesDir, "chaos.low.json");
            if (File.Exists(chaos)) _thresholds.Add(RuleLoader.Load<ThresholdRule>(chaos));

            var hc = Path.Combine(rulesDir, "hc.safety.json");
            if (File.Exists(hc)) _thresholds.Add(RuleLoader.Load<ThresholdRule>(hc));

            var resist = Path.Combine(rulesDir, "resist.baseline.json");
            if (File.Exists(resist)) _resist = RuleLoader.Load<ResistBaseline>(resist);

            var alias = Path.Combine(rulesDir, "gear.alias.json");
            if (File.Exists(alias)) _aliases = RuleLoader.Load<GearAlias>(alias);
        }

        public BuildModel Normalize(BuildModel m, string mode = "SC", int mapTier = 1)
        {
            m.Meta.Mode = string.IsNullOrWhiteSpace(m.Meta.Mode) ? mode : m.Meta.Mode;

            // 장비 이름 정규화 (최적화: 미리 대소문자 구분 없는 비교를 위해 준비)
            if (_aliases != null && m.Gear != null)
            {
                foreach (var g in m.Gear)
                {
                    var gearName = g.Name.ToUpperInvariant();

                    // 최적화: 일치하는 별칭을 찾으면 즉시 break (모든 매핑을 순회하지 않음)
                    foreach (var kv in _aliases.Normalize.Map)
                    {
                        bool found = false;
                        foreach (var alias in kv.Value)
                        {
                            if (string.Equals(alias, g.Name, StringComparison.OrdinalIgnoreCase))
                            {
                                g.Name = kv.Key;
                                found = true;
                                break;
                            }
                        }
                        if (found) break;
                    }
                }
            }

            if (_thresholds.Count > 0)
            {
                foreach (var t in _thresholds)
                {
                    if (t.When?.Mode != null &&
                        !string.Equals(t.When.Mode, m.Meta.Mode, StringComparison.OrdinalIgnoreCase))
                        continue;

                    double value = ReadDouble(m, t.Detect.Path);
                    bool hit =
                        (t.Detect.Lt != null && value < t.Detect.Lt) ||
                        (t.Detect.Lte != null && value <= t.Detect.Lte) ||
                        (t.Detect.Gt != null && value > t.Detect.Gt) ||
                        (t.Detect.Gte != null && value >= t.Detect.Gte);

                    if (hit)
                    {
                        m.Issues ??= new();
                        m.Issues.Add(new Issue
                        {
                            Level = t.Severity,
                            Message = t.Message,
                            Suggestions = t.Suggestions,
                            Code = t.Id
                        });
                    }
                }
            }
            return m;
        }

        private static double ReadDouble(BuildModel m, string path)
        {
            var parts = path.Split('.');
            object? cur = m;
            foreach (var p in parts)
            {
                var prop = cur!.GetType().GetProperty(p,
                    System.Reflection.BindingFlags.IgnoreCase |
                    System.Reflection.BindingFlags.Public |
                    System.Reflection.BindingFlags.Instance);
                cur = prop?.GetValue(cur);
                if (cur == null) return double.NaN;
            }
            return cur switch
            {
                int i => i,
                long l => l,
                float f => f,
                double d => d,
                _ => double.NaN
            };
        }
    }
}
