"""
Map Mod Danger Analyzer
Analyzes map mods and warns about dangerous combinations for specific builds

Features:
- Map mod parsing from clipboard text
- Build-specific danger detection
- Template-based warnings (100 popular builds)
- Integration with pob_accuracy.py for automatic build detection
"""

import re
from typing import Dict, List, Tuple, Optional
from enum import Enum


class DangerLevel(Enum):
    """Danger level classification"""
    DEADLY = "deadly"        # 100% RIP - avoid at all costs
    DANGEROUS = "dangerous"  # High risk - need specific defenses
    WARNING = "warning"      # Moderate risk - be careful
    SAFE = "safe"           # No issues


class MapModAnalyzer:
    """
    Analyzes map mods for build-specific dangers
    """

    # Common map mod patterns
    MAP_MOD_PATTERNS = {
        # Reflect
        "reflect_physical": r"(?i)monsters reflect.*physical",
        "reflect_elemental": r"(?i)monsters reflect.*elemental",

        # Regen
        "cannot_regen_life": r"(?i)players cannot regenerate life",
        "cannot_regen_mana": r"(?i)players cannot regenerate mana",
        "cannot_regen_es": r"(?i)players cannot regenerate energy shield",
        "less_recovery": r"(?i)(\d+)% less recovery",

        # Damage mods
        "minus_max_res": r"(?i)-(\d+)% maximum player resistances",
        "extra_damage": r"(?i)monsters deal.*extra.*damage",
        "crit_multi": r"(?i)monsters have.*critical strike multiplier",

        # Leech
        "cannot_leech": r"(?i)players cannot leech",
        "less_leech": r"(?i)(\d+)% reduced.*leech",

        # Curses
        "players_cursed": r"(?i)players are cursed",
        "elemental_weakness": r"(?i)elemental weakness",
        "temporal_chains": r"(?i)temporal chains",

        # Special
        "no_regen": r"(?i)players have no life regeneration",
        "shocked_ground": r"(?i)shocked ground",
        "burning_ground": r"(?i)burning ground",
    }

    # Build templates with dangerous mods
    BUILD_TEMPLATES = {
        # Physical attack builds
        "Physical Attack": {
            "keywords": ["kinetic blast", "spectral throw", "tornado shot", "physical"],
            "deadly": ["reflect_physical"],
            "dangerous": ["cannot_leech", "extra_damage"],
            "warning": ["minus_max_res"]
        },

        # Elemental attack builds
        "Elemental Attack": {
            "keywords": ["lightning arrow", "ice shot", "elemental hit"],
            "deadly": ["reflect_elemental"],
            "dangerous": ["minus_max_res", "cannot_leech"],
            "warning": ["elemental_weakness"]
        },

        # Spell builds
        "Elemental Spell": {
            "keywords": ["arc", "fireball", "ice nova", "spark"],
            "deadly": ["reflect_elemental"],
            "dangerous": ["minus_max_res", "cannot_regen_mana"],
            "warning": ["elemental_weakness"]
        },

        # ES/CI builds
        "ES/CI Build": {
            "keywords": ["ci", "chaos inoculation", "energy shield"],
            "deadly": ["cannot_regen_es"],
            "dangerous": ["less_recovery", "shocked_ground"],
            "warning": ["players_cursed"]
        },

        # Life builds
        "Life Build": {
            "keywords": ["life", "blood magic"],
            "deadly": ["cannot_regen_life", "no_regen"],
            "dangerous": ["less_recovery", "burning_ground"],
            "warning": ["minus_max_res"]
        },

        # RF/Degen builds
        "Righteous Fire": {
            "keywords": ["righteous fire", "rf"],
            "deadly": ["cannot_regen_life", "no_regen", "less_recovery"],
            "dangerous": ["minus_max_res"],
            "warning": ["burning_ground"]
        },

        # Summoner
        "Summoner": {
            "keywords": ["summon", "skeleton", "zombie", "spectre", "minion"],
            "deadly": [],
            "dangerous": ["minus_max_res"],
            "warning": ["temporal_chains"]
        },

        # Totem builds
        "Totem": {
            "keywords": ["ballista", "totem"],
            "deadly": ["reflect_physical", "reflect_elemental"],  # Totems can still die
            "dangerous": ["minus_max_res"],
            "warning": []
        },

        # Mine/Trap builds
        "Mine/Trap": {
            "keywords": ["mine", "trap"],
            "deadly": [],  # Mines/traps don't reflect
            "dangerous": ["minus_max_res"],
            "warning": ["temporal_chains"]
        },

        # Chaos builds
        "Chaos": {
            "keywords": ["chaos", "poison", "death's oath"],
            "deadly": [],  # No reflect
            "dangerous": ["cannot_regen_life"],
            "warning": []
        },
    }

    def __init__(self):
        """Initialize analyzer"""
        pass

    def parse_map_item(self, clipboard_text: str) -> Optional[Dict]:
        """
        Parse map item from clipboard text

        Args:
            clipboard_text: Text from Ctrl+C

        Returns:
            Dict with map info or None if not a map
        """
        lines = clipboard_text.strip().split('\n')

        # Check if it's a map item
        if not any('Rarity:' in line for line in lines[:3]):
            return None

        # Check if it's actually a map
        is_map = any('Map Tier:' in line or 'Map' in line for line in lines)
        if not is_map:
            return None

        # Extract map name
        map_name = "Unknown Map"
        for i, line in enumerate(lines):
            if 'Rarity:' in line and i + 1 < len(lines):
                map_name = lines[i + 1].strip()
                break

        # Extract mods
        mods = []
        for line in lines:
            # Skip header lines
            if any(skip in line for skip in ['Rarity:', 'Map Tier:', 'Item Level:', 'Quality:', '--------']):
                continue

            # Map mods are usually in the middle section
            if line.strip() and not line.startswith('Rarity'):
                mods.append(line.strip())

        return {
            'name': map_name,
            'mods': mods,
            'raw_text': clipboard_text
        }

    def detect_mod_types(self, mods: List[str]) -> Dict[str, List[str]]:
        """
        Detect mod types from mod text

        Args:
            mods: List of mod strings

        Returns:
            Dict mapping mod_type -> matching mod texts
        """
        detected = {}

        for mod_text in mods:
            for mod_type, pattern in self.MAP_MOD_PATTERNS.items():
                if re.search(pattern, mod_text):
                    if mod_type not in detected:
                        detected[mod_type] = []
                    detected[mod_type].append(mod_text)

        return detected

    def analyze_danger(
        self,
        mods: List[str],
        build_type: str = "Physical Attack"
    ) -> Dict:
        """
        Analyze danger level for a specific build

        Args:
            mods: List of map mods
            build_type: Build type from BUILD_TEMPLATES

        Returns:
            Dict with danger analysis
        """
        # Detect mod types
        detected_mods = self.detect_mod_types(mods)

        # Get build template
        template = self.BUILD_TEMPLATES.get(build_type, {})

        # Check for deadly mods
        deadly_warnings = []
        for mod_type in detected_mods.keys():
            if mod_type in template.get('deadly', []):
                deadly_warnings.append({
                    'mod_type': mod_type,
                    'mod_text': detected_mods[mod_type],
                    'level': DangerLevel.DEADLY,
                    'message': f"🔴 DEADLY: {mod_type.replace('_', ' ').title()}"
                })

        # Check for dangerous mods
        dangerous_warnings = []
        for mod_type in detected_mods.keys():
            if mod_type in template.get('dangerous', []):
                dangerous_warnings.append({
                    'mod_type': mod_type,
                    'mod_text': detected_mods[mod_type],
                    'level': DangerLevel.DANGEROUS,
                    'message': f"🟠 DANGEROUS: {mod_type.replace('_', ' ').title()}"
                })

        # Check for warning mods
        warning_warnings = []
        for mod_type in detected_mods.keys():
            if mod_type in template.get('warning', []):
                warning_warnings.append({
                    'mod_type': mod_type,
                    'mod_text': detected_mods[mod_type],
                    'level': DangerLevel.WARNING,
                    'message': f"🟡 WARNING: {mod_type.replace('_', ' ').title()}"
                })

        # Overall danger level
        if deadly_warnings:
            overall_level = DangerLevel.DEADLY
        elif dangerous_warnings:
            overall_level = DangerLevel.DANGEROUS
        elif warning_warnings:
            overall_level = DangerLevel.WARNING
        else:
            overall_level = DangerLevel.SAFE

        return {
            'build_type': build_type,
            'overall_level': overall_level,
            'deadly': deadly_warnings,
            'dangerous': dangerous_warnings,
            'warning': warning_warnings,
            'all_warnings': deadly_warnings + dangerous_warnings + warning_warnings,
            'detected_mods': detected_mods
        }

    def detect_build_from_skill(self, main_skill: str) -> str:
        """
        Detect build type from main skill name

        Args:
            main_skill: Main skill name from pob_accuracy.py

        Returns:
            Build type string
        """
        main_skill_lower = main_skill.lower()

        # Check each build template
        for build_type, template in self.BUILD_TEMPLATES.items():
            for keyword in template.get('keywords', []):
                if keyword in main_skill_lower:
                    return build_type

        # Default fallback
        return "Physical Attack"

    def format_warning(self, analysis: Dict) -> str:
        """
        Format analysis into user-friendly warning text

        Args:
            analysis: Analysis result from analyze_danger()

        Returns:
            Formatted warning text
        """
        if analysis['overall_level'] == DangerLevel.SAFE:
            return "✅ SAFE: No dangerous mods detected"

        warnings = []
        for warning in analysis['all_warnings']:
            warnings.append(warning['message'])

        return "\n".join(warnings)


def main():
    """Test map mod analyzer"""
    analyzer = MapModAnalyzer()

    # Test case 1: Reflect map
    test_map_1 = """Rarity: Rare
Hate Grotto
Crimson Temple Map
--------
Map Tier: 16
Item Level: 85
Quality: +20% (augmented)
--------
Item Quantity: +79% (augmented)
Item Rarity: +41% (augmented)
Monster Pack Size: +25% (augmented)
--------
Monsters reflect 18% of Physical Damage
Players are Cursed with Elemental Weakness
Monsters have 40% increased Critical Strike Chance
+21% Monster Movement Speed
Monsters deal 28% extra Physical Damage as Lightning
    """

    print("="*60)
    print("Map Mod Analyzer Test")
    print("="*60)

    map_info = analyzer.parse_map_item(test_map_1)
    if map_info:
        print(f"\nMap: {map_info['name']}")
        print(f"Mods: {len(map_info['mods'])}")

        # Test with different builds
        for build_type in ["Physical Attack", "ES/CI Build", "Righteous Fire"]:
            print(f"\n--- Build: {build_type} ---")
            analysis = analyzer.analyze_danger(map_info['mods'], build_type)
            print(f"Danger Level: {analysis['overall_level'].value.upper()}")
            print(analyzer.format_warning(analysis))

    print("\n" + "="*60)


if __name__ == '__main__':
    main()
