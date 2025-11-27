#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Item Price Checker - Ctrl+D 시세 조회용
클립보드에서 아이템 정보를 파싱하고 poe.ninja에서 가격을 조회
"""

import sys
import os
import json
import re
from typing import Dict, Optional, Tuple, List
from pathlib import Path

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


class KoreanTranslator:
    """
    한글→영문 아이템 이름 번역기
    Awakened PoE Trade의 NDJSON 데이터를 사용하여 번역
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if KoreanTranslator._initialized:
            return

        self.ko_to_en: Dict[str, str] = {}
        self.namespace_map: Dict[str, str] = {}  # 한글 이름 → namespace
        self._load_translations()
        KoreanTranslator._initialized = True

    def _load_translations(self):
        """NDJSON 파일에서 번역 데이터 로드"""
        # items.ndjson 파일 경로 (여러 경로 시도)
        possible_paths = [
            # 개발 환경 (src/PathcraftAI.Parser 기준)
            Path(__file__).parent.parent.parent / "tools" / "awakened-poe-trade" / "renderer" / "public" / "data" / "ko" / "items.ndjson",
            # 절대 경로 (빌드된 환경)
            Path("d:/Pathcraft-AI/tools/awakened-poe-trade/renderer/public/data/ko/items.ndjson"),
        ]

        ndjson_path = None
        for path in possible_paths:
            if path.exists():
                ndjson_path = path
                break

        if not ndjson_path:
            print(f"[WARNING] items.ndjson not found, Korean translation disabled", file=sys.stderr)
            return

        try:
            with open(ndjson_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                        korean_name = item.get("name", "")
                        english_name = item.get("refName", "")
                        namespace = item.get("namespace", "")

                        if korean_name and english_name:
                            self.ko_to_en[korean_name] = english_name
                            self.namespace_map[korean_name] = namespace
                    except json.JSONDecodeError:
                        continue

            print(f"[INFO] Loaded {len(self.ko_to_en)} Korean→English translations", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Failed to load translations: {e}", file=sys.stderr)

    def translate(self, korean_name: str) -> str:
        """
        한글 아이템 이름을 영문으로 번역

        Args:
            korean_name: 한글 아이템 이름

        Returns:
            영문 이름 (번역 실패시 원본 반환)
        """
        if not korean_name:
            return korean_name

        # 이미 영문이면 그대로 반환
        if korean_name.isascii():
            return korean_name

        # 직접 매핑 확인
        if korean_name in self.ko_to_en:
            return self.ko_to_en[korean_name]

        # 부분 매칭 시도 (접두사가 있는 경우: "삿된 X", "바알 X" 등)
        for kor, eng in self.ko_to_en.items():
            if kor in korean_name:
                # 접두사 부분 추출
                prefix = korean_name.replace(kor, "").strip()
                if prefix:
                    # 접두사도 번역 시도
                    eng_prefix = self.translate(prefix)
                    if eng_prefix != prefix:
                        return f"{eng_prefix} {eng}"
                return korean_name.replace(kor, eng)

        # 번역 실패 - 원본 반환
        return korean_name

    def get_namespace(self, korean_name: str) -> Optional[str]:
        """아이템의 네임스페이스 반환"""
        return self.namespace_map.get(korean_name)


class POEItemParser:
    """POE 아이템 클립보드 텍스트 파서"""

    # 아이템 클래스 매핑 (영문/한글)
    ITEM_CLASS_MAP = {
        # 영문
        "Currency": "currency",
        "Stackable Currency": "currency",
        "Divination Card": "divination",
        "Divination Cards": "divination",
        "Map": "map",
        "Maps": "map",
        "Unique": "unique",
        "Gem": "gem",
        "Active Skill Gem": "gem",
        "Active Skill Gems": "gem",
        "Support Skill Gem": "gem",
        "Support Skill Gems": "gem",
        "Skill Gems": "gem",
        "Scarab": "scarab",
        "Scarabs": "scarab",
        "Fragment": "fragment",
        "Map Fragments": "fragment",
        "Oil": "oil",
        "Oils": "oil",
        "Incubator": "incubator",
        "Incubators": "incubator",
        "Essence": "essence",
        "Essences": "essence",
        "Fossil": "fossil",
        "Fossils": "fossil",
        "Resonator": "resonator",
        "Resonators": "resonator",
        "Vial": "vial",
        "Beast": "beast",
        "Jewel": "jewel",
        "Jewels": "jewel",
        "Abyss Jewel": "jewel",
        "Abyss Jewels": "jewel",
        "Cluster Jewel": "cluster_jewel",
        "Cluster Jewels": "cluster_jewel",
        "Small Cluster Jewel": "cluster_jewel",
        "Medium Cluster Jewel": "cluster_jewel",
        "Large Cluster Jewel": "cluster_jewel",
        "Flask": "flask",
        "Flasks": "flask",
        "Life Flasks": "flask",
        "Mana Flasks": "flask",
        "Utility Flasks": "flask",
        "Invitation": "invitation",
        "Invitations": "invitation",
        "Tattoo": "tattoo",
        "Omen": "omen",
        "Coffin": "coffin",
        "Allflame Ember": "allflame",
        "Memory": "memory",
        # 영문 장비 (무기)
        "Claws": "claw",
        "Claw": "claw",
        "Daggers": "dagger",
        "Dagger": "dagger",
        "Rune Daggers": "rune_dagger",
        "Rune Dagger": "rune_dagger",
        "Wands": "wand",
        "Wand": "wand",
        "One Hand Swords": "one_hand_sword",
        "One Hand Sword": "one_hand_sword",
        "Thrusting One Hand Swords": "thrusting_one_hand_sword",
        "Thrusting One Hand Sword": "thrusting_one_hand_sword",
        "One Hand Axes": "one_hand_axe",
        "One Hand Axe": "one_hand_axe",
        "One Hand Maces": "one_hand_mace",
        "One Hand Mace": "one_hand_mace",
        "Sceptres": "sceptre",
        "Sceptre": "sceptre",
        "Two Hand Swords": "two_hand_sword",
        "Two Hand Sword": "two_hand_sword",
        "Two Hand Axes": "two_hand_axe",
        "Two Hand Axe": "two_hand_axe",
        "Two Hand Maces": "two_hand_mace",
        "Two Hand Mace": "two_hand_mace",
        "Bows": "bow",
        "Bow": "bow",
        "Staves": "staff",
        "Staff": "staff",
        "Warstaves": "warstaff",
        "Warstaff": "warstaff",
        "Fishing Rods": "fishing_rod",
        "Fishing Rod": "fishing_rod",
        # 영문 장비 (방어구)
        "Helmets": "helmet",
        "Helmet": "helmet",
        "Body Armours": "body_armour",
        "Body Armour": "body_armour",
        "Gloves": "gloves",
        "Boots": "boots",
        "Shields": "shield",
        "Shield": "shield",
        "Quivers": "quiver",
        "Quiver": "quiver",
        # 영문 장비 (악세서리)
        "Amulets": "amulet",
        "Amulet": "amulet",
        "Rings": "ring",
        "Ring": "ring",
        "Belts": "belt",
        "Belt": "belt",
        "Trinkets": "trinket",
        "Trinket": "trinket",
        # 영문 기타
        "Heist Cloaks": "heist_cloak",
        "Heist Brooches": "heist_brooch",
        "Heist Gear": "heist_gear",
        "Heist Tools": "heist_tool",
        "Heist Contracts": "heist_contract",
        "Heist Blueprints": "heist_blueprint",
        "Delirium Orbs": "delirium_orb",
        "Catalysts": "catalyst",
        "Sentinel": "sentinel",
        "Sentinels": "sentinel",
        "Breachstones": "breachstone",
        "Breachstone": "breachstone",
        "Expedition Logbooks": "logbook",
        "Expedition Logbook": "logbook",
        "Tinctures": "tincture",
        "Tincture": "tincture",
        "Corpses": "corpse",
        "Corpse": "corpse",
        # 한글
        "화폐": "currency",
        "중첩 가능 화폐": "currency",
        "점술 카드": "divination",
        "지도": "map",
        "젬": "gem",
        "액티브 스킬 젬": "gem",
        "보조 스킬 젬": "gem",
        "스킬 젬": "gem",
        "성흔": "scarab",
        "파편": "fragment",
        "지도 파편": "fragment",
        "오일": "oil",
        "인큐베이터": "incubator",
        "에센스": "essence",
        "화석": "fossil",
        "공명기": "resonator",
        "주얼": "jewel",
        "심연 주얼": "jewel",
        "클러스터 주얼": "cluster_jewel",
        "스킬 군 주얼": "cluster_jewel",
        "플라스크": "flask",
        "생명력 플라스크": "flask",
        "마나 플라스크": "flask",
        "유틸리티 플라스크": "flask",
        "초대장": "invitation",
        "문신": "tattoo",
        "예조": "omen",
        "관": "coffin",
        "모든불꽃 잔불": "allflame",
        "기억": "memory",
        # 한글 장비 타입
        "투구": "helmet",
        "장갑": "gloves",
        "장화": "boots",
        "갑옷": "body_armour",
        "방패": "shield",
        "목걸이": "amulet",
        "반지": "ring",
        "허리띠": "belt",
        "무기": "weapon",
        "단검": "dagger",
        "클로": "claw",
        "한손 검": "one_hand_sword",
        "한손 도끼": "one_hand_axe",
        "한손 철퇴": "one_hand_mace",
        "단창": "sceptre",
        "지팡이": "wand",
        "홀": "sceptre",
        "양손 검": "two_hand_sword",
        "양손 도끼": "two_hand_axe",
        "양손 철퇴": "two_hand_mace",
        "활": "bow",
        "화살통": "quiver",
        "장대": "staff",
        "마법봉": "wand",
        "전투지팡이": "warstaff",
    }

    # 영향력 키워드 (영문/한글)
    INFLUENCE_KEYWORDS = {
        "Shaper Item": "shaper",
        "Elder Item": "elder",
        "Crusader Item": "crusader",
        "Hunter Item": "hunter",
        "Redeemer Item": "redeemer",
        "Warlord Item": "warlord",
        "Synthesised Item": "synthesised",
        # 한글
        "쉐이퍼 아이템": "shaper",
        "엘더 아이템": "elder",
        "십자군 아이템": "crusader",
        "사냥꾼 아이템": "hunter",
        "대속자 아이템": "redeemer",
        "전쟁군주 아이템": "warlord",
        "결합된 아이템": "synthesised",
    }

    def __init__(self):
        # 싱글톤 번역기 인스턴스
        self.translator = KoreanTranslator()

    def translate_korean_name(self, korean_name: str, item_type: str = "item") -> str:
        """
        한글 아이템 이름을 영문으로 번역 (KoreanTranslator 사용)

        Args:
            korean_name: 한글 아이템 이름
            item_type: "item", "gem", "currency", "base" 등 (현재는 미사용, 호환성 유지)

        Returns:
            영문 이름 (번역 실패시 원본 반환)
        """
        return self.translator.translate(korean_name)

    def parse(self, clipboard_text: str) -> Optional[Dict]:
        """
        클립보드 텍스트에서 아이템 정보 추출

        Returns:
            {
                "name": "아이템 이름",
                "base_type": "베이스 타입",
                "rarity": "Unique/Rare/Magic/Normal/Currency/Gem/Divination Card",
                "item_class": "currency/unique/gem/divination/...",
                "links": 6,  # 링크 수 (해당시)
                "corrupted": True/False,
                "gem_level": 21,  # 젬인 경우
                "gem_quality": 20,  # 젬인 경우
                "stack_size": 10,  # 스택 가능한 경우
                "map_tier": 16,  # 맵인 경우
                "implicits": [],  # 내재 모드 리스트
                "explicits": [],  # 명시적 모드 리스트
                "influences": [],  # 영향력 (Shaper, Elder 등)
                "fractured_mods": [],  # 분열 모드
                "crafted_mods": [],  # 제작 모드
            }
        """
        if not clipboard_text:
            return None

        lines = clipboard_text.strip().split('\n')
        if len(lines) < 2:
            return None

        result = {
            "name": "",
            "base_type": "",
            "rarity": "",
            "item_class": "unknown",
            "links": 0,
            "corrupted": False,
            "unidentified": False,
            "gem_level": 0,
            "gem_quality": 0,
            "stack_size": 1,
            "map_tier": 0,
            "ilvl": 0,
            "implicits": [],
            "explicits": [],
            "influences": [],
            "fractured_mods": [],
            "crafted_mods": [],
        }

        # 첫 번째 구분선 전후로 파싱
        sections = self._split_sections(clipboard_text)

        # 첫 번째 섹션에서 기본 정보 추출
        if sections:
            first_section = sections[0]
            result.update(self._parse_header(first_section))

        # 나머지 섹션에서 추가 정보 추출
        full_text = clipboard_text.lower()

        # Corrupted 체크 (영문/한글)
        if "corrupted" in full_text or "타락" in clipboard_text:
            result["corrupted"] = True

        # Unidentified 체크 (영문/한글)
        if "unidentified" in full_text or "미감정" in clipboard_text:
            result["unidentified"] = True

        # 링크 체크 (소켓 정보에서)
        result["links"] = self._parse_links(clipboard_text)

        # 젬 정보
        if result["rarity"] == "Gem" or "gem" in result["item_class"]:
            result.update(self._parse_gem_info(clipboard_text))

        # 맵 정보
        if "map tier:" in full_text:
            result["map_tier"] = self._parse_map_tier(clipboard_text)

        # 아이템 레벨 (영문/한글)
        ilvl_match = re.search(r'(?:Item Level|아이템 레벨):\s*(\d+)', clipboard_text)
        if ilvl_match:
            result["ilvl"] = int(ilvl_match.group(1))

        # 스택 크기 (영문/한글)
        stack_match = re.search(r'(?:Stack Size|중첩 개수):\s*(\d+)', clipboard_text)
        if stack_match:
            result["stack_size"] = int(stack_match.group(1))

        # 레어/매직 아이템의 경우 모드 파싱
        if result["rarity"] in ["Rare", "Magic", "Unique"]:
            mods = self._parse_mods(sections, result["rarity"])
            result["implicits"] = mods.get("implicits", [])
            result["explicits"] = mods.get("explicits", [])
            result["fractured_mods"] = mods.get("fractured_mods", [])
            result["crafted_mods"] = mods.get("crafted_mods", [])
            result["influences"] = mods.get("influences", [])

        return result

    def _split_sections(self, text: str) -> List[str]:
        """구분선(---------)으로 섹션 분리"""
        return re.split(r'-{8,}', text)

    def _parse_mods(self, sections: List[str], rarity: str) -> Dict:
        """
        섹션에서 implicit/explicit 모드 추출

        POE 아이템 텍스트 구조:
        Section 0: Item Class, Rarity, Name, Base
        Section 1: Physical properties (Armour, Evasion, etc.)
        Section 2: Requirements
        Section 3: Sockets
        Section 4: Item Level
        Section 5: Implicit mods (if any) - 구분선 후 바로 다음
        Section 6+: Explicit mods, influences, corruption status
        """
        result = {
            "implicits": [],
            "explicits": [],
            "fractured_mods": [],
            "crafted_mods": [],
            "influences": [],
        }

        if len(sections) < 2:
            return result

        # 모드가 아닌 키워드 (필터링용)
        skip_keywords = [
            # 영문
            "Item Class:", "Rarity:", "Requirements:", "Level:", "Str:", "Dex:", "Int:",
            "Sockets:", "Item Level:", "Quality:", "Armour:", "Evasion:", "Energy Shield:",
            "Ward:", "Chance to Block:", "Physical Damage:", "Elemental Damage:",
            "Critical Strike Chance:", "Attacks per Second:", "Weapon Range:",
            "Stack Size:", "중첩 개수:", "Map Tier:", "Atlas Region:", "LevelReq:",
            "Corrupted", "Mirrored", "Split", "Unidentified", "미감정",
            "Note:", "<<", ">>",
            # 한글
            "아이템 종류:", "희귀도:", "요구 사항", "레벨:", "힘:", "민첩:", "지능:",
            "홈:", "아이템 레벨:", "품질:", "방어도:", "회피:", "에너지 보호막:",
            "결계:", "막기 확률:", "물리 피해:", "원소 피해:",
            "치명타 확률:", "초당 공격 횟수:", "무기 범위:",
            "중첩 개수:", "지도 등급:", "아틀라스 지역:",
            "타락", "복제됨", "분리됨", "미감정",
        ]

        # 영향력 감지
        for section in sections:
            for keyword, influence in self.INFLUENCE_KEYWORDS.items():
                if keyword in section:
                    if influence not in result["influences"]:
                        result["influences"].append(influence)

        # Implicit 찾기: Item Level 직후 섹션 (보통 implicit이 한두 줄)
        # Explicit 찾기: 그 다음 섹션부터
        found_ilvl_section = False
        ilvl_section_idx = -1

        for i, section in enumerate(sections):
            section_text = section.strip()
            if "Item Level:" in section_text or "아이템 레벨:" in section_text:
                found_ilvl_section = True
                ilvl_section_idx = i
                break

        # POE 아이템 구조:
        # - ilvl 섹션 바로 다음 (ilvl_section_idx + 1)이 implicit (없을 수도 있음)
        # - 그 다음 섹션 (ilvl_section_idx + 2)부터가 explicit
        # - 단, implicit이 없으면 ilvl + 1이 explicit
        #
        # 판단 기준: implicit 섹션은 보통 1-2줄이고, explicit은 여러 줄
        implicit_section_idx = ilvl_section_idx + 1 if found_ilvl_section else -1
        explicit_start_idx = ilvl_section_idx + 2 if found_ilvl_section else 3

        # implicit 섹션이 실제로 implicit인지 확인 (라인 수로 추정)
        if implicit_section_idx > 0 and implicit_section_idx < len(sections):
            implicit_section = sections[implicit_section_idx].strip()
            implicit_lines = [l.strip() for l in implicit_section.split('\n') if l.strip() and self._is_mod_line(l.strip())]
            # implicit이 3줄 이상이면 explicit으로 간주 (implicit은 보통 1-2개)
            if len(implicit_lines) >= 3:
                explicit_start_idx = implicit_section_idx
                implicit_section_idx = -1  # implicit 없음

        # 섹션별로 모드 추출
        for i, section in enumerate(sections):
            section_text = section.strip()
            if not section_text:
                continue

            lines = [l.strip() for l in section_text.split('\n') if l.strip()]

            for line in lines:
                # 스킵 키워드 체크
                should_skip = False
                for skip in skip_keywords:
                    if line.startswith(skip) or line == skip:
                        should_skip = True
                        break

                if should_skip:
                    continue

                # 빈 줄이나 너무 짧은 줄 스킵
                if len(line) < 3:
                    continue

                # 모드인지 판단 (숫자 또는 +/- 포함, 또는 특정 패턴)
                if self._is_mod_line(line):
                    # 제작 모드 체크 (crafted) - 영문: (crafted), 한글: (제작)
                    is_crafted = "(crafted)" in line.lower() or "(제작)" in line
                    # 분열 모드 체크 (fractured) - 영문: (fractured), 한글: (분열)
                    is_fractured = "(fractured)" in line.lower() or "(분열)" in line

                    # 태그 제거한 실제 모드 텍스트
                    clean_line = re.sub(r'\s*\((crafted|fractured|제작|분열)\)\s*', '', line, flags=re.IGNORECASE).strip()

                    if is_fractured:
                        result["fractured_mods"].append(clean_line)
                        # explicits에는 추가하지 않음 (별도로 표시)
                    elif is_crafted:
                        result["crafted_mods"].append(clean_line)
                        # explicits에는 추가하지 않음 (별도로 표시)
                    elif found_ilvl_section and i == implicit_section_idx and implicit_section_idx > 0:
                        result["implicits"].append(clean_line)
                    elif i >= explicit_start_idx:
                        result["explicits"].append(clean_line)

        return result

    def _is_mod_line(self, line: str) -> bool:
        """라인이 모드인지 판단"""
        # 숫자 포함 체크
        has_number = bool(re.search(r'\d', line))

        # +/- 로 시작하거나 포함
        has_plus_minus = '+' in line or '-' in line or '%' in line

        # 특정 모드 패턴
        mod_patterns = [
            r'\+\d+',  # +숫자
            r'\d+%',   # 숫자%
            r'adds \d+',  # Adds X to Y
            r'gain \d+',
            r'(\d+) to (\d+)',  # X to Y
            r'increased',
            r'reduced',
            r'more',
            r'less',
            r'regenerate',
            r'leech',
            r'추가',
            r'증가',
            r'감소',
            r'재생',
            r'흡수',
            r'최대치',
            r'저항',
        ]

        for pattern in mod_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True

        return has_number and (has_plus_minus or len(line) > 10)

    # 한글 희귀도 매핑
    KOREAN_RARITY_MAP = {
        "노말": "Normal",
        "일반": "Normal",
        "마법": "Magic",
        "레어": "Rare",
        "희귀": "Rare",  # "레어" 또는 "희귀" 모두 지원
        "고유": "Unique",
        "유니크": "Unique",
        "젬": "Gem",
        "화폐": "Currency",
        "점술 카드": "Divination Card",
        "점술카드": "Divination Card",
    }

    def _parse_header(self, header_text: str) -> Dict:
        """헤더 섹션에서 아이템 기본 정보 추출"""
        lines = [l.strip() for l in header_text.strip().split('\n') if l.strip()]

        result = {
            "name": "",
            "base_type": "",
            "rarity": "",
            "item_class": "unknown",
        }

        if not lines:
            return result

        # Item Class / 아이템 종류 찾기
        item_class_line = None
        rarity_line = None

        for i, line in enumerate(lines):
            # 영문
            if line.startswith("Item Class:"):
                item_class_line = line.replace("Item Class:", "").strip()
            elif line.startswith("Rarity:"):
                rarity_line = line.replace("Rarity:", "").strip()
            # 한글 (여러 형식 지원)
            elif line.startswith("아이템 종류:"):
                item_class_line = line.replace("아이템 종류:", "").strip()
            elif line.startswith("희귀도:") or line.startswith("아이템 희귀도:"):
                # "희귀도:" 또는 "아이템 희귀도:" 모두 지원
                if line.startswith("아이템 희귀도:"):
                    rarity_line = line.replace("아이템 희귀도:", "").strip()
                else:
                    rarity_line = line.replace("희귀도:", "").strip()
                # 한글 희귀도 영문 변환
                rarity_line = self.KOREAN_RARITY_MAP.get(rarity_line, rarity_line)

        if rarity_line:
            result["rarity"] = rarity_line

        # Item Class 매핑 (정확한 매칭 우선, 부분 매칭은 긴 키부터)
        if item_class_line:
            item_class_lower = item_class_line.lower()

            # 1. 정확한 매칭 먼저
            for key, value in self.ITEM_CLASS_MAP.items():
                if key.lower() == item_class_lower:
                    result["item_class"] = value
                    break
            else:
                # 2. 부분 매칭 (긴 키부터 - "Map Fragments"가 "Map"보다 먼저 매칭)
                sorted_keys = sorted(self.ITEM_CLASS_MAP.keys(), key=len, reverse=True)
                for key in sorted_keys:
                    if key.lower() in item_class_lower:
                        result["item_class"] = self.ITEM_CLASS_MAP[key]
                        break
                else:
                    # 매핑 안되면 원래 값 유지
                    result["item_class"] = item_class_lower.replace(" ", "_")

        # 이름과 베이스 타입 추출
        # Currency, Divination Card 등은 Rarity 다음 줄이 이름
        name_lines = []
        rarity_found = False
        for line in lines:
            if line.startswith("Rarity:") or line.startswith("희귀도:") or line.startswith("아이템 희귀도:"):
                rarity_found = True
                continue
            if rarity_found and not line.startswith("Item Class:") and not line.startswith("아이템 종류:"):
                if line.strip():
                    name_lines.append(line.strip())

        if name_lines:
            if result["rarity"] == "Unique" and len(name_lines) >= 2:
                # Unique: 첫줄=이름, 둘째줄=베이스
                result["name"] = name_lines[0]
                result["base_type"] = name_lines[1]
            elif result["rarity"] in ["Rare", "Magic"] and len(name_lines) >= 2:
                # Rare/Magic: 첫줄=접두사+이름, 둘째줄=베이스
                result["name"] = name_lines[0]
                result["base_type"] = name_lines[1]
            else:
                # Currency, Gem 등: 첫줄이 이름
                result["name"] = name_lines[0]
                if len(name_lines) > 1:
                    result["base_type"] = name_lines[1]

        # 베이스 타입 또는 이름으로 item_class 보정 (클러스터 주얼 등)
        base_type_lower = result.get("base_type", "").lower()
        name_lower = result.get("name", "").lower()

        # 클러스터 주얼 감지 (이름 또는 베이스 타입에서)
        cluster_keywords = ["cluster jewel", "클러스터 주얼", "스킬 군 주얼", "소형 스킬 군", "중형 스킬 군", "대형 스킬 군"]
        for kw in cluster_keywords:
            if kw in base_type_lower or kw in name_lower:
                result["item_class"] = "cluster_jewel"
                break

        return result

    def _parse_links(self, text: str) -> int:
        """소켓에서 최대 링크 수 추출"""
        # Sockets: R-R-R-R-R-R (6링크) 또는 홈: B-B-R-B
        socket_match = re.search(r'(?:Sockets|홈):\s*([RGBWA\-\s]+)', text, re.IGNORECASE)
        if not socket_match:
            return 0

        socket_str = socket_match.group(1).strip()

        # 줄바꿈이나 다른 키워드 전까지만 파싱
        socket_str = socket_str.split('\n')[0].strip()

        # 연결된 그룹 찾기 (공백으로 분리된 그룹)
        groups = socket_str.split()

        max_links = 0
        for group in groups:
            # 유효한 소켓 문자만 남기기
            group = re.sub(r'[^RGBWA\-]', '', group, flags=re.IGNORECASE)
            if not group:
                continue
            # 각 그룹에서 - 로 연결된 소켓 수 계산
            links = group.count('-') + 1 if '-' in group else 1
            max_links = max(max_links, links)

        return max_links

    def _parse_gem_info(self, text: str) -> Dict:
        """젬 정보 추출"""
        result = {"gem_level": 1, "gem_quality": 0}

        # Level: 21 또는 레벨: 21 또는 "레벨: 6 (최대)"
        level_match = re.search(r'(?:Level|레벨):\s*(\d+)', text)
        if level_match:
            result["gem_level"] = int(level_match.group(1))

        # Quality: +20% 또는 품질: +20%
        quality_match = re.search(r'(?:Quality|품질):\s*\+?(\d+)%', text)
        if quality_match:
            result["gem_quality"] = int(quality_match.group(1))

        return result

    def _parse_map_tier(self, text: str) -> int:
        """맵 티어 추출"""
        tier_match = re.search(r'Map Tier:\s*(\d+)', text, re.IGNORECASE)
        if tier_match:
            return int(tier_match.group(1))
        return 0


class PriceChecker:
    """poe.ninja 가격 조회"""

    def __init__(self, league: str = None):
        # poe_ninja_api 임포트
        from poe_ninja_api import POENinjaAPI
        self.api = POENinjaAPI(league=league, use_cache=True)
        self.league = self.api.league
        self.parser = POEItemParser()  # 번역 함수 사용을 위해

    def get_price(self, item_info: Dict) -> Optional[Dict]:
        """
        아이템 정보로 가격 조회

        Returns:
            {
                "chaos": 가격(chaos),
                "divine": 가격(divine),
                "formatted": "150c" 또는 "1.5div",
                "confidence": "high/medium/low",
                "source": "poe.ninja",
                "unit_chaos": 단가 (스택인 경우),
                "stack_size": 스택 개수,
            }
        """
        if not item_info:
            return None

        item_class = item_info.get("item_class", "")
        name = item_info.get("name", "")
        base_type = item_info.get("base_type", "")
        rarity = item_info.get("rarity", "")
        stack_size = item_info.get("stack_size", 1)

        # 가격 조회 결과
        result = None

        # 커런시로 분류됐지만 실제로는 다른 타입인 경우 보정 (이름 기반)
        if item_class == "currency" or rarity == "Currency":
            name_lower = name.lower()
            if "essence" in name_lower or "에센스" in name:
                result = self._get_misc_price(name, "essence")
            elif "fossil" in name_lower or "화석" in name:
                result = self._get_misc_price(name, "fossil")
            elif "oil" in name_lower or "오일" in name:
                result = self._get_misc_price(name, "oil")
            elif "catalyst" in name_lower or "촉매" in name:
                result = self._get_misc_price(name, "catalyst")
            elif "resonator" in name_lower or "공명기" in name:
                result = self._get_misc_price(name, "resonator")
            else:
                # 일반 커런시
                result = self._get_currency_price(name)

        # 점술 카드
        elif item_class == "divination" or rarity == "Divination Card":
            result = self._get_divination_price(name)

        # 젬 (먼저 체크 - Unique Gem 가능)
        elif item_class == "gem" or rarity == "Gem":
            result = self._get_gem_price(name, item_info)

        # 맵 (고유 맵, 타락 맵 포함) - Unique 체크 전에!
        elif item_class == "map":
            result = self._get_map_price(name, item_info)

        # 클러스터 주얼
        elif item_class == "cluster_jewel":
            result = self._get_cluster_jewel_price(name, item_info)

        # 유니크 주얼 (Unique 일반 체크 전에)
        elif item_class == "jewel" and rarity == "Unique":
            result = self._get_unique_jewel_price(name, item_info)

        # 유니크 (무기/방어구/악세사리)
        elif rarity == "Unique":
            result = self._get_unique_price(name, base_type, item_info)

        # 기타 (스카라브, 에센스 등)
        elif item_class in ["scarab", "essence", "fossil", "oil", "fragment",
                          "invitation", "tattoo", "omen", "coffin", "allflame", "memory",
                          "incubator", "resonator", "vial", "beast", "catalyst",
                          "delirium_orb", "breachstone", "logbook"]:
            # fragment로 분류됐지만 이름이 scarab인 경우 보정
            if item_class == "fragment" and "scarab" in name.lower():
                result = self._get_misc_price(name, "scarab")
            else:
                result = self._get_misc_price(name, item_class)

        # 레어/매직 아이템 - Trade API 사용
        elif rarity in ["Rare", "Magic"]:
            result = self._get_rare_price(item_info)

        # 스택 사이즈 적용 (결과가 있고 스택이 1보다 큰 경우)
        if result and stack_size > 1:
            divine_rate = result.get("divine_rate", 150)
            # Divine Orb는 별도 처리
            if result.get("is_divine"):
                result = self._format_divine_result(1, divine_rate, stack_size)
            else:
                unit_chaos = result.get("chaos", 0)
                result = self._format_price_result(unit_chaos, divine_rate, result.get("note", ""), stack_size)

        return result

    def _get_currency_price(self, name: str) -> Optional[Dict]:
        """커런시 가격 조회 (일반 + 시즌 화폐)"""
        try:
            # Divine 환율
            divine_rate = self.api.get_divine_chaos_rate()

            # 한글 이름 영문 번역
            eng_name = self.parser.translate_korean_name(name, "currency")
            name_lower = eng_name.lower()

            # Divine Orb 특별 처리 (1div = 1div로 표시, chaos 환산 안함)
            if name_lower == "divine orb" or name == "신성한 오브":
                return self._format_divine_result(1, divine_rate)

            # Chaos Orb 특별 처리 (항상 1c)
            if name_lower == "chaos orb" or name == "카오스 오브":
                return self._format_price_result(1, divine_rate)

            from poe_ninja_api import PriceCache
            import requests
            cache = PriceCache()

            # 일반 Currency와 시즌 화폐 모두 체크
            currency_types = ["Currency"]

            for currency_type in currency_types:
                cache_key = f"{self.league}_{currency_type}"
                cached_data = cache.get(cache_key)

                if not cached_data:
                    url = f"https://poe.ninja/api/data/currencyoverview"
                    params = {"league": self.league, "type": currency_type}
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    cached_data = response.json()
                    cache.set(cache_key, cached_data)

                if cached_data:
                    lines = cached_data.get('lines', [])

                    # 정확한 매칭 먼저
                    for item in lines:
                        item_name = item.get('currencyTypeName', '')
                        if name_lower == item_name.lower():
                            chaos_value = item.get('chaosEquivalent', 0)
                            return self._format_price_result(chaos_value, divine_rate)

                    # 부분 매칭
                    for item in lines:
                        item_name = item.get('currencyTypeName', '')
                        if name_lower in item_name.lower() or item_name.lower() in name_lower:
                            chaos_value = item.get('chaosEquivalent', 0)
                            return self._format_price_result(chaos_value, divine_rate)

            # 시즌 화폐 (itemoverview 타입)
            # Delirium Orb, Catalyst, Artifact 등
            special_currency_types = ["DeliriumOrb", "Artifact"]

            for api_type in special_currency_types:
                cache_key = f"{self.league}_{api_type}"
                cached_data = cache.get(cache_key)

                if not cached_data:
                    url = f"https://poe.ninja/api/data/itemoverview"
                    params = {"league": self.league, "type": api_type}
                    try:
                        response = requests.get(url, params=params, timeout=10)
                        response.raise_for_status()
                        cached_data = response.json()
                        cache.set(cache_key, cached_data)
                    except:
                        continue

                if cached_data:
                    lines = cached_data.get('lines', [])

                    for item in lines:
                        item_name = item.get('name', '')
                        if name_lower == item_name.lower() or name_lower in item_name.lower():
                            chaos_value = item.get('chaosValue', 0)
                            return self._format_price_result(chaos_value, divine_rate)

            return None
        except Exception as e:
            print(f"[ERROR] Currency price lookup failed: {e}", file=sys.stderr)
            return None

    def _get_divination_price(self, name: str) -> Optional[Dict]:
        """점술 카드 가격 조회"""
        try:
            divine_rate = self.api.get_divine_chaos_rate()

            # 한글 이름 영문 번역
            eng_name = self.parser.translate_korean_name(name, "divination")

            # DivinationCard 타입 조회
            cache_key = f"{self.league}_DivinationCard"
            from poe_ninja_api import PriceCache
            cache = PriceCache()
            cached_data = cache.get(cache_key)

            if not cached_data:
                # 캐시 없으면 API 직접 호출
                import requests
                url = f"https://poe.ninja/api/data/itemoverview"
                params = {"league": self.league, "type": "DivinationCard"}
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                cached_data = response.json()
                cache.set(cache_key, cached_data)

            if cached_data:
                lines = cached_data.get('lines', [])
                name_lower = eng_name.lower()

                for item in lines:
                    item_name = item.get('name', '')
                    if name_lower == item_name.lower() or name_lower in item_name.lower():
                        chaos_value = item.get('chaosValue', 0)
                        return self._format_price_result(chaos_value, divine_rate)

            return None
        except Exception as e:
            print(f"[ERROR] Divination price lookup failed: {e}", file=sys.stderr)
            return None

    def _get_unique_price(self, name: str, base_type: str, item_info: Dict) -> Optional[Dict]:
        """유니크 아이템 가격 조회"""
        try:
            divine_rate = self.api.get_divine_chaos_rate()

            # 한글 이름 영문 번역
            eng_name = self.parser.translate_korean_name(name, "item")

            # 유니크 카테고리들
            unique_types = ["UniqueWeapon", "UniqueArmour", "UniqueAccessory", "UniqueJewel", "UniqueFlask"]

            from poe_ninja_api import PriceCache
            import requests
            cache = PriceCache()

            name_lower = eng_name.lower()
            links = item_info.get("links", 0)
            corrupted = item_info.get("corrupted", False)
            implicits = item_info.get("implicits", [])

            for utype in unique_types:
                cache_key = f"{self.league}_{utype}"
                cached_data = cache.get(cache_key)

                # 캐시가 없으면 API 호출
                if not cached_data:
                    try:
                        url = f"https://poe.ninja/api/data/itemoverview"
                        params = {"league": self.league, "type": utype}
                        response = requests.get(url, params=params, timeout=10)
                        response.raise_for_status()
                        cached_data = response.json()
                        cache.set(cache_key, cached_data)
                    except Exception:
                        continue

                lines = cached_data.get('lines', [])

                # 타락 아이템: implicit 매칭 시도
                if corrupted and implicits:
                    best_match = None
                    best_score = 0

                    for item in lines:
                        item_name = item.get('name', '')
                        if name_lower != item_name.lower():
                            continue

                        item_implicits = item.get('implicitModifiers', [])
                        if not item_implicits:
                            continue

                        # implicit 텍스트 매칭 점수 계산
                        score = 0
                        for our_impl in implicits:
                            our_impl_lower = our_impl.lower()
                            for ninja_impl in item_implicits:
                                ninja_text = ninja_impl.get('text', '').lower()
                                # 숫자 제거하고 비교 (범위 무시)
                                import re
                                our_clean = re.sub(r'[\d\.\-\+%]+', '', our_impl_lower).strip()
                                ninja_clean = re.sub(r'[\d\.\-\+%]+', '', ninja_text).strip()
                                if our_clean in ninja_clean or ninja_clean in our_clean:
                                    score += 1
                                    break

                        if score > best_score:
                            best_score = score
                            best_match = item

                    if best_match:
                        chaos_value = best_match.get('chaosValue', 0)
                        implicit_note = "Corrupted"
                        return self._format_price_result(chaos_value, divine_rate, implicit_note)

                # 일반 아이템 검색
                # poe.ninja는 variant가 있는 아이템도 하나의 가격으로 통합 (예: Mageblood의 2-4 플라스크)
                for item in lines:
                    item_name = item.get('name', '')
                    item_links = item.get('links', 0)
                    item_variant = item.get('variant')  # 예: "2 Jewels", "3 Flasks" 등

                    # 이름 매칭
                    if name_lower == item_name.lower():
                        # 6링크 체크
                        if links >= 6:
                            if item_links == 6:
                                chaos_value = item.get('chaosValue', 0)
                                return self._format_price_result(chaos_value, divine_rate, "6L")
                        elif item_links == 0 or item_links is None:
                            # variant 정보가 있으면 note에 추가
                            note = ""
                            if item_variant:
                                note = f"({item_variant})"
                            chaos_value = item.get('chaosValue', 0)
                            return self._format_price_result(chaos_value, divine_rate, note)

            # 못 찾으면 일반 검색 (영문 이름 사용)
            price = self.api.get_item_price(eng_name)
            if price:
                return self._format_price_result(price, divine_rate)

            return None
        except Exception as e:
            print(f"[ERROR] Unique price lookup failed: {e}", file=sys.stderr)
            return None

    def _get_gem_price(self, name: str, item_info: Dict) -> Optional[Dict]:
        """젬 가격 조회"""
        try:
            divine_rate = self.api.get_divine_chaos_rate()

            level = item_info.get("gem_level", 1)
            quality = item_info.get("gem_quality", 0)
            corrupted = item_info.get("corrupted", False)

            # 한글 이름 영문 번역
            eng_name = self.parser.translate_korean_name(name, "gem")

            # "바알" 접두사 처리 (Vaal 젬)
            # 주의: 각성 젬(Awakened)은 타락되어도 "Vaal" 접두사가 붙지 않음
            # 예: "바알 각성한 포악함" -> "Awakened Brutality Support" (corrupted)
            is_vaal_gem = eng_name.lower().startswith("vaal ") or name.startswith("바알 ") or eng_name.startswith("바알 ")
            is_awakened_gem = "awakened" in eng_name.lower() or "각성" in name

            if is_vaal_gem and not eng_name.lower().startswith("vaal "):
                # "바알 ..." -> "Vaal ..." 또는 그냥 기본 이름으로 변환
                if eng_name.startswith("바알 "):
                    base_name = eng_name[3:]
                    # 각성 젬은 Vaal 접두사 안 붙임
                    if "awakened" in base_name.lower():
                        eng_name = base_name
                    else:
                        eng_name = "Vaal " + base_name
                elif name.startswith("바알 "):
                    base_gem = name[3:]  # "바알 " 제거
                    eng_base = self.parser.translate_korean_name(base_gem, "gem")
                    if eng_base != base_gem:
                        # 각성 젬은 Vaal 접두사 안 붙임
                        if "awakened" in eng_base.lower():
                            eng_name = eng_base
                        else:
                            eng_name = f"Vaal {eng_base}"

            cache_key = f"{self.league}_SkillGem"
            from poe_ninja_api import PriceCache
            cache = PriceCache()
            cached_data = cache.get(cache_key)

            if not cached_data:
                import requests
                url = f"https://poe.ninja/api/data/itemoverview"
                params = {"league": self.league, "type": "SkillGem"}
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                cached_data = response.json()
                cache.set(cache_key, cached_data)

            if cached_data:
                lines = cached_data.get('lines', [])
                name_lower = eng_name.lower()

                best_match = None
                best_score = -1

                for item in lines:
                    item_name = item.get('name', '')
                    item_level = item.get('gemLevel', 1)
                    item_quality = item.get('gemQuality', 0)
                    item_corrupted = item.get('corrupted', False)

                    # 정확한 매칭 또는 부분 매칭
                    if name_lower != item_name.lower() and name_lower not in item_name.lower():
                        continue

                    # 매칭 점수 계산
                    score = 0
                    if item_level == level:
                        score += 10
                    elif abs(item_level - level) <= 1:
                        score += 5

                    if item_quality == quality:
                        score += 5
                    elif abs(item_quality - quality) <= 3:
                        score += 2

                    if item_corrupted == corrupted:
                        score += 3

                    if score > best_score:
                        best_score = score
                        best_match = item

                if best_match:
                    chaos_value = best_match.get('chaosValue', 0)
                    note = f"Lv{level}"
                    if quality > 0:
                        note += f" Q{quality}"
                    if corrupted:
                        note += " (C)"
                    return self._format_price_result(chaos_value, divine_rate, note)

            return None
        except Exception as e:
            print(f"[ERROR] Gem price lookup failed: {e}", file=sys.stderr)
            return None

    def _get_rare_price(self, item_info: Dict) -> Optional[Dict]:
        """레어/매직 아이템 - 모드 표시용 (Trade API 검색은 사용자 요청 시)"""
        try:
            divine_rate = self.api.get_divine_chaos_rate()

            # 검색 최소값 비율 (90% = 현재 값의 90% 이상인 아이템 검색)
            MIN_SEARCH_RATIO = 0.9

            # 모든 모드를 searched_mods로 반환 (Trade API 검색 없이)
            all_mods = []

            # Explicit 모드
            for mod in item_info.get("explicits", []):
                value = self._extract_mod_value(mod)
                all_mods.append({
                    "text": mod,
                    "stat_id": "",  # 아직 검색 안함
                    "value": value,
                    "min_search": int(value * MIN_SEARCH_RATIO) if value > 0 else None,
                    "mod_type": "explicit"
                })

            # Implicit 모드
            for mod in item_info.get("implicits", []):
                value = self._extract_mod_value(mod)
                all_mods.append({
                    "text": mod,
                    "stat_id": "",
                    "value": value,
                    "min_search": int(value * MIN_SEARCH_RATIO) if value > 0 else None,
                    "mod_type": "implicit"
                })

            # Fractured 모드
            for mod in item_info.get("fractured_mods", []):
                value = self._extract_mod_value(mod)
                all_mods.append({
                    "text": f"{mod} (fractured)",
                    "stat_id": "",
                    "value": value,
                    "min_search": int(value * MIN_SEARCH_RATIO) if value > 0 else None,
                    "mod_type": "fractured"
                })

            # Crafted 모드
            for mod in item_info.get("crafted_mods", []):
                value = self._extract_mod_value(mod)
                all_mods.append({
                    "text": f"{mod} (crafted)",
                    "stat_id": "",
                    "value": value,
                    "min_search": int(value * MIN_SEARCH_RATIO) if value > 0 else None,
                    "mod_type": "crafted"
                })

            if not all_mods:
                return None

            return {
                "chaos": 0,  # 아직 검색 안함
                "divine": 0,
                "formatted": "모드 선택 후 검색",
                "confidence": "pending",
                "source": "trade",
                "note": "Trade 검색 버튼을 눌러 가격 조회",
                "divine_rate": divine_rate,
                "trade_url": None,
                "searched_mods": all_mods,
            }

        except Exception as e:
            print(f"[ERROR] Rare price lookup failed: {e}", file=sys.stderr)
            return None

    def _extract_mod_value(self, mod_text: str) -> float:
        """모드 텍스트에서 숫자 값 추출"""
        import re
        # 첫 번째 숫자 추출
        match = re.search(r'[\+\-]?(\d+(?:\.\d+)?)', mod_text)
        if match:
            return float(match.group(1))
        return 0

    def _get_misc_price(self, name: str, item_class: str) -> Optional[Dict]:
        """기타 아이템 가격 조회"""
        try:
            divine_rate = self.api.get_divine_chaos_rate()

            # 한글 이름 영문 번역
            eng_name = self.parser.translate_korean_name(name, item_class)

            type_map = {
                "scarab": "Scarab",
                "essence": "Essence",
                "fossil": "Fossil",
                "oil": "Oil",
                "fragment": "Fragment",
                "invitation": "Invitation",
                "tattoo": "Tattoo",
                "omen": "Omen",
                "coffin": "Coffin",
                "allflame": "AllflameEmber",
                "memory": "Memory",
                "incubator": "Incubator",
                "resonator": "Resonator",
                "vial": "Vial",
                "beast": "Beast",
                "catalyst": "Catalyst",
            }

            api_type = type_map.get(item_class)
            if not api_type:
                return None

            cache_key = f"{self.league}_{api_type}"
            from poe_ninja_api import PriceCache
            cache = PriceCache()
            cached_data = cache.get(cache_key)

            if not cached_data:
                import requests
                url = f"https://poe.ninja/api/data/itemoverview"
                params = {"league": self.league, "type": api_type}
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                cached_data = response.json()
                cache.set(cache_key, cached_data)

            if cached_data:
                lines = cached_data.get('lines', [])
                name_lower = eng_name.lower()

                for item in lines:
                    item_name = item.get('name', '')
                    if name_lower in item_name.lower() or item_name.lower() in name_lower:
                        chaos_value = item.get('chaosValue', 0)
                        return self._format_price_result(chaos_value, divine_rate)

            return None
        except Exception as e:
            print(f"[ERROR] Misc price lookup failed: {e}", file=sys.stderr)
            return None

    def _get_map_price(self, name: str, item_info: Dict) -> Optional[Dict]:
        """맵 가격 조회 (고유 맵, 타락 맵 포함)"""
        try:
            divine_rate = self.api.get_divine_chaos_rate()
            rarity = item_info.get("rarity", "")
            map_tier = item_info.get("map_tier", 0)
            corrupted = item_info.get("corrupted", False)

            # 한글 이름 영문 번역
            eng_name = self.parser.translate_korean_name(name, "map")

            from poe_ninja_api import PriceCache
            cache = PriceCache()

            # 고유 맵
            if rarity == "Unique":
                cache_key = f"{self.league}_UniqueMap"
                cached_data = cache.get(cache_key)

                if not cached_data:
                    import requests
                    url = f"https://poe.ninja/api/data/itemoverview"
                    params = {"league": self.league, "type": "UniqueMap"}
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    cached_data = response.json()
                    cache.set(cache_key, cached_data)

                if cached_data:
                    lines = cached_data.get('lines', [])
                    name_lower = eng_name.lower()

                    for item in lines:
                        item_name = item.get('name', '')
                        if name_lower == item_name.lower() or name_lower in item_name.lower():
                            chaos_value = item.get('chaosValue', 0)
                            note = f"T{map_tier}" if map_tier > 0 else ""
                            return self._format_price_result(chaos_value, divine_rate, note)

            # 타락 맵 / Blighted 맵
            # Blighted Map 체크
            is_blighted = "blighted" in name.lower() or "역병" in name
            is_blight_ravaged = "blight-ravaged" in name.lower() or "역병에 유린당한" in name

            if is_blighted or is_blight_ravaged:
                map_type = "BlightRavagedMap" if is_blight_ravaged else "BlightedMap"
                cache_key = f"{self.league}_{map_type}"
                cached_data = cache.get(cache_key)

                if not cached_data:
                    import requests
                    url = f"https://poe.ninja/api/data/itemoverview"
                    params = {"league": self.league, "type": map_type}
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    cached_data = response.json()
                    cache.set(cache_key, cached_data)

                if cached_data:
                    lines = cached_data.get('lines', [])
                    name_lower = name.lower()

                    for item in lines:
                        item_name = item.get('name', '')
                        if name_lower in item_name.lower() or item_name.lower() in name_lower:
                            chaos_value = item.get('chaosValue', 0)
                            return self._format_price_result(chaos_value, divine_rate)

            # 일반/레어/매직/미감정 맵 - poe.ninja Map API 사용
            # 맵 이름으로 검색 (티어별 가격 제공)
            cache_key = f"{self.league}_Map"
            cached_data = cache.get(cache_key)

            if not cached_data:
                import requests
                url = f"https://poe.ninja/api/data/itemoverview"
                params = {"league": self.league, "type": "Map"}
                try:
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    cached_data = response.json()
                    cache.set(cache_key, cached_data)
                except Exception as e:
                    print(f"[WARNING] Map API failed: {e}", file=sys.stderr)
                    return None

            if cached_data:
                lines = cached_data.get('lines', [])
                name_lower = eng_name.lower()

                # 베이스 타입 추출 (레어 맵의 경우 base_type 사용)
                base_type = item_info.get("base_type", "")
                if base_type:
                    base_type_lower = self.parser.translate_korean_name(base_type, "map").lower()
                else:
                    base_type_lower = name_lower

                best_match = None
                best_tier_diff = float('inf')

                for item in lines:
                    item_name = item.get('name', '').lower()
                    item_tier = item.get('mapTier', 0)

                    # 이름 매칭 (베이스 타입 또는 맵 이름)
                    if base_type_lower in item_name or item_name in base_type_lower or \
                       name_lower in item_name or item_name in name_lower:
                        # 티어 매칭 (가장 가까운 티어 선택)
                        tier_diff = abs(item_tier - map_tier) if map_tier > 0 else 0
                        if tier_diff < best_tier_diff:
                            best_tier_diff = tier_diff
                            best_match = item

                if best_match:
                    chaos_value = best_match.get('chaosValue', 0)
                    item_tier = best_match.get('mapTier', 0)
                    note = f"T{item_tier}" if item_tier > 0 else ""
                    return self._format_price_result(chaos_value, divine_rate, note)

            return None

        except Exception as e:
            print(f"[ERROR] Map price lookup failed: {e}", file=sys.stderr)
            return None

    def _get_cluster_jewel_price(self, name: str, item_info: Dict) -> Optional[Dict]:
        """클러스터 주얼 가격 조회"""
        try:
            divine_rate = self.api.get_divine_chaos_rate()

            # 한글 이름 영문 번역
            eng_name = self.parser.translate_korean_name(name, "item")
            base_type_raw = item_info.get("base_type", "")
            eng_base_type = self.parser.translate_korean_name(base_type_raw, "base")

            from poe_ninja_api import PriceCache
            cache = PriceCache()

            cache_key = f"{self.league}_ClusterJewel"
            cached_data = cache.get(cache_key)

            if not cached_data:
                import requests
                url = f"https://poe.ninja/api/data/itemoverview"
                params = {"league": self.league, "type": "ClusterJewel"}
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                cached_data = response.json()
                cache.set(cache_key, cached_data)

            if cached_data:
                lines = cached_data.get('lines', [])
                name_lower = eng_name.lower()
                base_type = eng_base_type.lower()

                # 클러스터 주얼은 name이 패시브 이름, baseType이 주얼 크기
                for item in lines:
                    item_name = item.get('name', '')  # 패시브 이름
                    item_base = item.get('baseType', '')  # 주얼 크기

                    # 이름 또는 베이스 매칭
                    if (name_lower in item_name.lower() or item_name.lower() in name_lower or
                        base_type in item_base.lower()):
                        chaos_value = item.get('chaosValue', 0)
                        return self._format_price_result(chaos_value, divine_rate)

            # 못 찾으면 레어 아이템처럼 모드 표시
            return self._get_rare_price(item_info)

        except Exception as e:
            print(f"[ERROR] Cluster jewel price lookup failed: {e}", file=sys.stderr)
            return None

    def _get_unique_jewel_price(self, name: str, item_info: Dict) -> Optional[Dict]:
        """유니크 주얼 가격 조회"""
        try:
            divine_rate = self.api.get_divine_chaos_rate()

            # 한글 이름 영문 번역
            eng_name = self.parser.translate_korean_name(name, "item")

            from poe_ninja_api import PriceCache
            cache = PriceCache()

            cache_key = f"{self.league}_UniqueJewel"
            cached_data = cache.get(cache_key)

            if not cached_data:
                import requests
                url = f"https://poe.ninja/api/data/itemoverview"
                params = {"league": self.league, "type": "UniqueJewel"}
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                cached_data = response.json()
                cache.set(cache_key, cached_data)

            if cached_data:
                lines = cached_data.get('lines', [])
                name_lower = eng_name.lower()

                for item in lines:
                    item_name = item.get('name', '')
                    if name_lower == item_name.lower():
                        chaos_value = item.get('chaosValue', 0)
                        return self._format_price_result(chaos_value, divine_rate)

            return None

        except Exception as e:
            print(f"[ERROR] Unique jewel price lookup failed: {e}", file=sys.stderr)
            return None

    def _format_price_result(self, chaos_value: float, divine_rate: float, note: str = "", stack_size: int = 1) -> Dict:
        """가격 결과 포맷팅 (스택 사이즈 지원)"""
        # 스택 총 가치 계산
        total_chaos = chaos_value * stack_size
        total_divine = total_chaos / divine_rate if divine_rate > 0 else 0

        # 포맷된 문자열 (스택 표시)
        if stack_size > 1:
            # 스택인 경우: 총 가치 + 단가 표시
            if total_divine >= 1:
                formatted = f"{total_divine:.1f}div ({stack_size}×{chaos_value:.1f}c)"
            elif total_chaos >= 1:
                formatted = f"{int(total_chaos)}c ({stack_size}×{chaos_value:.1f}c)"
            else:
                formatted = f"{total_chaos:.2f}c ({stack_size}×{chaos_value:.2f}c)"
        else:
            # 단일 아이템
            if total_divine >= 1:
                formatted = f"{total_divine:.1f}div"
            elif total_chaos >= 1:
                formatted = f"{int(total_chaos)}c"
            else:
                formatted = f"{total_chaos:.1f}c"

        # 신뢰도 (총 가격 기반)
        if total_chaos > 10:
            confidence = "high"
        elif total_chaos > 1:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "chaos": round(total_chaos, 1),
            "divine": round(total_divine, 2),
            "unit_chaos": round(chaos_value, 1),  # 단가
            "stack_size": stack_size,
            "formatted": formatted,
            "confidence": confidence,
            "source": "poe.ninja",
            "note": note,
            "divine_rate": divine_rate,
        }

    def _format_divine_result(self, divine_count: float, divine_rate: float, stack_size: int = 1) -> Dict:
        """Divine Orb 전용 포맷팅 (Divine 기준으로 표시)"""
        total_divine = divine_count * stack_size
        total_chaos = total_divine * divine_rate

        if stack_size > 1:
            formatted = f"{int(total_divine)}div ({stack_size}×1div)"
        else:
            formatted = "1div"

        return {
            "chaos": round(total_chaos, 1),
            "divine": round(total_divine, 2),
            "unit_chaos": round(divine_rate, 1),  # 1div = Xc
            "unit_divine": 1,  # Divine 단가는 항상 1div
            "stack_size": stack_size,
            "formatted": formatted,
            "confidence": "high",
            "source": "poe.ninja",
            "note": "",
            "divine_rate": divine_rate,
            "is_divine": True,  # Divine Orb 플래그
        }


def check_price(clipboard_text: str) -> str:
    """
    CLI 엔트리포인트: 클립보드 텍스트로 가격 조회

    Returns:
        JSON 문자열
    """
    parser = POEItemParser()
    item_info = parser.parse(clipboard_text)

    if not item_info:
        return json.dumps({
            "success": False,
            "error": "아이템을 파싱할 수 없습니다.",
            "item": None,
            "price": None,
        }, ensure_ascii=False)

    checker = PriceChecker()
    price_info = checker.get_price(item_info)

    return json.dumps({
        "success": price_info is not None,
        "error": None if price_info else "가격 정보를 찾을 수 없습니다.",
        "item": item_info,
        "price": price_info,
        "league": checker.league,
    }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="POE Item Price Checker")
    parser.add_argument("--clipboard", type=str, help="Clipboard text to parse")
    parser.add_argument("--test", action="store_true", help="Run test mode")
    args = parser.parse_args()

    if args.test:
        # 테스트 모드
        test_items = [
            # Divine Orb
            """Item Class: Currency
Rarity: Currency
Divine Orb
--------
Stack Size: 1/10
--------
Randomises the numeric values of the random modifiers on an item
--------
Right click this item then left click a magic, rare or unique item to apply it.
Shift click to unstack.""",

            # Unique Weapon
            """Item Class: Claws
Rarity: Unique
Touch of Anguish
Imperial Claw
--------
Claw
Quality: +20% (augmented)
Physical Damage: 37-95
Elemental Damage: 40-100 (augmented)
Critical Strike Chance: 6.00%
Attacks per Second: 1.60
--------
Requirements:
Level: 68
Dex: 131
Int: 95
--------
Sockets: G-G-G
--------
Item Level: 84
--------
+46 Life gained for each Enemy hit by Attacks
--------
Adds 40 to 60 Cold Damage
30% increased Cold Damage
20% chance to gain a Frenzy Charge on Killing a Frozen Enemy
Skills Chain an additional time while at maximum Frenzy Charges
Critical Strikes do not inherently Freeze
--------
My reach exceeds my grasp.""",

            # Divination Card
            """Item Class: Divination Cards
Rarity: Divination Card
The Doctor
--------
Stack Size: 1/8
--------
Mageblood
--------
Void diviners of Oriath seek
only528
 to528
 528
528
breathe528
 the528
 528
528
immortal air.""",

            # Rare Helmet (영문)
            """Item Class: Helmets
Rarity: Rare
Sol Horn
Prophet Crown
--------
Armour: 292
Energy Shield: 53
--------
Requirements:
Level: 63
Str: 85
Int: 62
--------
Sockets: B-B-R-B
--------
Item Level: 84
--------
+30 to Strength
+38 to Armour
+17 to maximum Energy Shield
+91 to maximum Life
+19% to Fire Resistance
--------
Shaper Item""",

            # Rare Helmet (한글)
            """아이템 종류: 투구
희귀도: 레어
솔 뿔
예언자 왕관
--------
방어도: 292
에너지 보호막: 53
--------
요구 사항:
레벨: 63
힘: 85
지능: 62
--------
홈: B-B-R-B
--------
아이템 레벨: 84
--------
힘 +30
방어도 +38
에너지 보호막 최대치 +17
생명력 최대치 +91
화염 저항 +19%
--------
쉐이퍼 아이템""",
        ]

        print("=" * 60)
        print("Item Price Checker Test")
        print("=" * 60)

        item_parser = POEItemParser()
        price_checker = PriceChecker()

        for i, test_text in enumerate(test_items, 1):
            print(f"\n--- Test {i} ---")
            item_info = item_parser.parse(test_text)
            print(f"Parsed: {json.dumps(item_info, ensure_ascii=False, indent=2)}")

            if item_info:
                price = price_checker.get_price(item_info)
                print(f"Price: {json.dumps(price, ensure_ascii=False, indent=2)}")

    elif args.clipboard:
        result = check_price(args.clipboard)
        print(result)
    else:
        # stdin에서 읽기
        clipboard_text = sys.stdin.read()
        result = check_price(clipboard_text)
        print(result)
