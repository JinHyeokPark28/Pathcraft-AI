"""
POE Korean-English Translation Database
Supports bilingual Map Mod analysis and skill detection

Data sources:
- poedb.tw (English reference)
- poeregexkr.web.app (Korean reference)
- Community translations
"""

from typing import Dict, List, Optional


class POETranslations:
    """Korean-English translation database for POE"""

    # Skill names (Korean -> English)
    SKILL_NAMES = {
        # Attack skills
        "키네틱 블라스트": "Kinetic Blast",
        "토네이도 샷": "Tornado Shot",
        "스펙트럴 스로우": "Spectral Throw",
        "라이트닝 애로우": "Lightning Arrow",
        "아이스 샷": "Ice Shot",
        "스플릿 애로우": "Split Arrow",
        "퓨실레이드": "Kinetic Fusillade",

        # Spell skills
        "아크": "Arc",
        "파이어볼": "Fireball",
        "아이스 노바": "Ice Nova",
        "스파크": "Spark",
        "라이트닝 스트라이크": "Lightning Strike",
        "프로스트 볼트": "Frost Bolt",

        # Summoner
        "소환 해골": "Summon Skeleton",
        "소환 좀비": "Raise Zombie",
        "소환 스펙터": "Raise Spectre",
        "소환 레이징 스피릿": "Summon Raging Spirit",
        "소환 골렘": "Summon Golem",

        # Totem
        "시즈 발리스타": "Siege Ballista",
        "토템": "Totem",

        # Mine/Trap
        "지뢰": "Mine",
        "함정": "Trap",

        # Special builds
        "라이처스 파이어": "Righteous Fire",
        "데스 오스": "Death's Oath",
        "독": "Poison",
        "카오스": "Chaos",
    }

    # Map mods (Korean -> English patterns)
    MAP_MODS_KR = {
        # Reflect
        "물리 피해 반사": "reflect_physical",
        "원소 피해 반사": "reflect_elemental",
        "몬스터가 받은 물리 피해의": "reflect_physical",
        "몬스터가 받은 원소 피해의": "reflect_elemental",

        # Regen
        "플레이어의 생명력 재생 불가": "cannot_regen_life",
        "플레이어의 마나 재생 불가": "cannot_regen_mana",
        "플레이어의 에너지 보호막 재생 불가": "cannot_regen_es",
        "생명력 재생 없음": "no_regen",
        "회복량 .*% 감소": "less_recovery",

        # Damage
        "최대 저항 .*% 감소": "minus_max_res",
        "추가 .*피해": "extra_damage",
        "치명타 피해 배율": "crit_multi",

        # Leech
        "흡수 불가": "cannot_leech",
        "흡수.*감소": "less_leech",

        # Curses
        "저주": "players_cursed",
        "원소 약화": "elemental_weakness",
        "시간의 사슬": "temporal_chains",

        # Ground effects
        "감전 지대": "shocked_ground",
        "발화 지대": "burning_ground",
    }

    # Map mod danger descriptions (Korean)
    DANGER_DESCRIPTIONS_KR = {
        "reflect_physical": {
            "name": "물리 피해 반사",
            "description": "몬스터가 받은 물리 피해를 플레이어에게 반사합니다.",
            "warning": "물리 공격 빌드는 즉사할 수 있습니다!"
        },
        "reflect_elemental": {
            "name": "원소 피해 반사",
            "description": "몬스터가 받은 원소 피해를 플레이어에게 반사합니다.",
            "warning": "원소 공격/주문 빌드는 즉사할 수 있습니다!"
        },
        "cannot_regen_life": {
            "name": "생명력 재생 불가",
            "description": "플레이어의 생명력이 자동으로 재생되지 않습니다.",
            "warning": "RF 빌드는 플레이 불가능합니다!"
        },
        "cannot_regen_es": {
            "name": "에너지 보호막 재생 불가",
            "description": "에너지 보호막이 자동으로 재생되지 않습니다.",
            "warning": "CI/ES 빌드는 매우 위험합니다!"
        },
        "minus_max_res": {
            "name": "최대 저항 감소",
            "description": "플레이어의 최대 저항이 감소합니다.",
            "warning": "원소 피해에 매우 취약해집니다!"
        },
    }

    # Build type translations
    BUILD_TYPES_KR = {
        "Physical Attack": "물리 공격",
        "Elemental Attack": "원소 공격",
        "Elemental Spell": "원소 주문",
        "ES/CI Build": "ES/CI 빌드",
        "Life Build": "생명력 빌드",
        "Righteous Fire": "라이처스 파이어",
        "Summoner": "소환사",
        "Totem": "토템",
        "Mine/Trap": "지뢰/함정",
        "Chaos": "카오스",
    }

    # Danger level translations
    DANGER_LEVELS_KR = {
        "deadly": "치명적",
        "dangerous": "위험",
        "warning": "주의",
        "safe": "안전",
    }

    @staticmethod
    def translate_skill(skill_name: str, to_korean: bool = True) -> Optional[str]:
        """
        Translate skill name

        Args:
            skill_name: Skill name to translate
            to_korean: True for EN->KR, False for KR->EN

        Returns:
            Translated name or None
        """
        if to_korean:
            # English -> Korean
            reverse_map = {v.lower(): k for k, v in POETranslations.SKILL_NAMES.items()}
            return reverse_map.get(skill_name.lower())
        else:
            # Korean -> English
            return POETranslations.SKILL_NAMES.get(skill_name)

    @staticmethod
    def translate_build_type(build_type: str) -> str:
        """Translate build type to Korean"""
        return POETranslations.BUILD_TYPES_KR.get(build_type, build_type)

    @staticmethod
    def translate_danger_level(level: str) -> str:
        """Translate danger level to Korean"""
        return POETranslations.DANGER_LEVELS_KR.get(level, level)

    @staticmethod
    def get_mod_description_kr(mod_type: str) -> Dict[str, str]:
        """Get Korean description for mod type"""
        return POETranslations.DANGER_DESCRIPTIONS_KR.get(mod_type, {
            "name": mod_type,
            "description": "설명 없음",
            "warning": ""
        })

    @staticmethod
    def detect_korean_map_mods(mod_text: str) -> List[str]:
        """
        Detect mod types from Korean map mod text

        Args:
            mod_text: Korean map mod text

        Returns:
            List of detected mod types
        """
        import re
        detected = []

        for kr_pattern, mod_type in POETranslations.MAP_MODS_KR.items():
            if re.search(kr_pattern, mod_text):
                detected.append(mod_type)

        return detected


def test_translations():
    """Test translation functions"""
    print("="*60)
    print("POE Translations Test")
    print("="*60)

    # Test skill translation
    print("\n[Skill Translation]")
    print(f"Siege Ballista -> {POETranslations.translate_skill('Siege Ballista', True)}")
    print(f"시즈 발리스타 -> {POETranslations.translate_skill('시즈 발리스타', False)}")

    # Test build type
    print("\n[Build Type Translation]")
    print(f"Physical Attack -> {POETranslations.translate_build_type('Physical Attack')}")

    # Test mod detection (Korean)
    print("\n[Korean Map Mod Detection]")
    korean_mod = "몬스터가 받은 물리 피해의 18%를 반사합니다"
    detected = POETranslations.detect_korean_map_mods(korean_mod)
    print(f"'{korean_mod}'")
    print(f"Detected: {detected}")

    # Test mod description
    print("\n[Mod Description (Korean)]")
    desc = POETranslations.get_mod_description_kr("reflect_physical")
    print(f"Name: {desc['name']}")
    print(f"Description: {desc['description']}")
    print(f"Warning: {desc['warning']}")

    print("\n" + "="*60)


if __name__ == '__main__':
    test_translations()
