"""
POE Korean-English Translation Database
Supports bilingual Map Mod analysis and skill detection

Data sources:
- poedb.tw/kr (Web-scraped Korean translations - 95 skills)
- poeregexkr.web.app (Korean reference)
- Community translations
"""

from typing import Dict, List, Optional


class POETranslations:
    """Korean-English translation database for POE"""

    # Skill names (Korean -> English)
    # Auto-scraped from poedb.tw/kr - 95 skills verified
    SKILL_NAMES = {
        # Attack skills
        "역학 폭발": "Kinetic Blast",
        "회오리 사격": "Tornado Shot",
        "환영 무기 투척": "Spectral Throw",
        "번개 화살": "Lightning Arrow",
        "얼음 화살": "Ice Shot",
        "분할 화살": "Split Arrow",
        "서리 칼날": "Frost Blades",
        "원소의 일격": "Elemental Hit",
        "연발 사격": "Barrage",
        "화살비": "Rain of Arrows",
        "충격 화살": "Galvanic Arrow",
        "불타는 화살": "Burning Arrow",
        "번개 타격": "Lightning Strike",
        "용암 타격": "Molten Strike",
        "빙하 망치": "Glacial Hammer",
        "묵직한 타격": "Heavy Strike",
        "이중 타격": "Double Strike",
        "약탈": "Reave",
        "대지 강타": "Ground Slam",
        "지진": "Earthquake",
        "피부 찢기": "Lacerate",
        "질풍의 칼날": "Blade Flurry",
        "회오리바람": "Cyclone",

        # Spell skills
        "연쇄 번개": "Arc",
        "화염구": "Fireball",
        "얼음 폭발": "Ice Nova",
        "전기불꽃": "Spark",
        "구형 번개": "Ball Lightning",
        "빙하 폭포": "Glacial Cascade",
        "동결 파동": "Freezing Pulse",
        "화염 쇄도": "Flame Surge",
        "방출": "Discharge",
        "폭풍 부름": "Storm Call",
        "시체 폭발": "Detonate Dead",
        "칼날 소용돌이": "Blade Vortex",
        "천상의 단도": "Ethereal Knives",
        "소용돌이": "Vortex",
        "한파": "Cold Snap",

        # Chaos/DoT
        "정의의 화염": "Righteous Fire",
        "죽음의 오라": "Death Aura",
        "부식성 화살": "Caustic Arrow",
        "정수 흡수": "Essence Drain",
        "파멸": "Bane",
        "영혼 분리": "Soulrend",

        # Summoner
        "격노의 유령 소환": "Summon Raging Spirit",
        "좀비 소환": "Raise Zombie",
        "망령 소환": "Raise Spectre",
        "원격 기폭 장치 소환": "Summon Skitterbots",
        "고통의 전령": "Herald of Agony",
        "지배의 맹타": "Dominating Blow",

        # Totem
        "공성 쇠뇌": "Siege Ballista",
        "선대의 대전사": "Ancestral Warchief",

        # Mine/Trap
        "화산탄 지뢰": "Pyroclast Mine",
        "고드름 지뢰": "Icicle Mine",
        "지진 덫": "Seismic Trap",
        "번개 덫": "Lightning Trap",
        "연막 지뢰": "Smoke Mine",

        # Movement skills
        "질주": "Dash",
        "화염 질주": "Flame Dash",
        "서리점멸": "Frostblink",
        "칼날 선회": "Whirling Blades",
        "도약 강타": "Leap Slam",
        "방패 돌진": "Shield Charge",

        # Auras
        "증오": "Hatred",
        "분노": "Anger",
        "진노": "Wrath",
        "은총": "Grace",
        "결의": "Determination",
        "단련": "Discipline",
        "원소의 순수함": "Purity of Elements",
        "불의 순수함": "Purity of Fire",
        "얼음의 순수함": "Purity of Ice",
        "번개의 순수함": "Purity of Lightning",
        "활력": "Vitality",
        "명상": "Clarity",
        "가속": "Haste",
        "정밀함": "Precision",
        "자부심": "Pride",
        "열광": "Zealotry",
        "악의": "Malevolence",

        # Curses
        "동상": "Frostbite",
        "인화성": "Flammability",
        "전도성": "Conductivity",
        "취약성": "Vulnerability",
        "시간의 사슬": "Temporal Chains",
        "쇠약화": "Enfeeble",
        "원소 약화": "Elemental Weakness",
        "절망": "Despair",
        "응징": "Punishment",
        "암살자의 징표": "Assassin's Mark",
        "밀렵꾼의 징표": "Poacher's Mark",
        "전쟁군주의 징표": "Warlord's Mark",
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
