#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build-Based Item Filter Generator
POB 빌드 데이터를 기반으로 진행 단계별 .filter 파일 생성
"""

import sys
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

# 현재 디렉토리를 path에 추가
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from pob_item_parser import POBItemParser, ParsedItem
from poe_ninja_api import POENinjaAPI


@dataclass
class FilterConfig:
    """필터 설정"""
    account_name: str
    phase: str  # Starter, Mid, End, HighEnd
    league_type: str = "SC"  # SC, HC, SSF, Ruthless

    # 엄격도 (0-6)
    strictness: int = 0

    # 사운드 설정
    use_custom_sounds: bool = False
    sound_volume: int = 300


class BuildFilterGenerator:
    """빌드 기반 아이템 필터 생성기"""

    # 진행 단계별 기본 엄격도
    PHASE_STRICTNESS = {
        "Starter": 0,   # 액트 레벨링 - 매우 낮음
        "Mid": 2,       # T16까지 - 중간
        "End": 4,       # 빌드 완성 - 높음
        "HighEnd": 5    # 민맥싱 - 매우 높음
    }

    # 리그 타입별 엄격도 보정
    LEAGUE_STRICTNESS_MOD = {
        "SC": 0,
        "HC": 1,
        "SSF": -1,
        "Ruthless": 2
    }

    # 슬롯별 카테고리
    SLOT_CATEGORIES = {
        "Helmet": "armour",
        "Body Armour": "armour",
        "Gloves": "armour",
        "Boots": "armour",
        "Belt": "accessory",
        "Amulet": "accessory",
        "Ring 1": "accessory",
        "Ring 2": "accessory",
        "Weapon 1": "weapon",
        "Weapon 2": "weapon",
        "Flask 1": "flask",
        "Flask 2": "flask",
        "Flask 3": "flask",
        "Flask 4": "flask",
        "Flask 5": "flask",
    }

    def __init__(self, pob_xml_path: str, account_name: str, league_type: str = "SC"):
        """
        Args:
            pob_xml_path: POB XML 파일 경로
            account_name: OAuth 계정 이름
            league_type: 리그 타입 (SC/HC/SSF/Ruthless)
        """
        self.pob_xml_path = pob_xml_path
        self.account_name = account_name
        self.league_type = league_type

        # POB 파서
        self.parser = POBItemParser()
        self.items: List[ParsedItem] = []
        self.equipped_items: List[ParsedItem] = []

        # 빌드 아이템 정보
        self.build_uniques: Set[str] = set()
        self.build_base_types: Set[str] = set()
        self.build_influences: Set[str] = set()

    def parse_build(self) -> bool:
        """POB 빌드 파싱"""
        try:
            self.items = self.parser.parse_xml(self.pob_xml_path)
            self.equipped_items = self.parser.get_equipped_items()

            if not self.equipped_items:
                print("[WARN] No equipped items found", file=sys.stderr)
                return False

            # 빌드 아이템 정보 추출
            self._extract_build_items()

            print(f"[OK] Parsed {len(self.equipped_items)} equipped items", file=sys.stderr)
            print(f"  - Uniques: {len(self.build_uniques)}", file=sys.stderr)
            print(f"  - Base types: {len(self.build_base_types)}", file=sys.stderr)

            return True

        except Exception as e:
            print(f"[ERROR] Failed to parse build: {e}", file=sys.stderr)
            return False

    def _extract_build_items(self):
        """빌드에서 핵심 아이템 정보 추출"""
        for item in self.equipped_items:
            # 유니크 아이템
            if item.rarity == "UNIQUE" and item.name:
                self.build_uniques.add(item.name)

            # 베이스 타입 (플라스크 제외, 장비만)
            slot = item.slot or ""
            if item.base_type and not slot.startswith("Flask"):
                # 플라스크가 아닌 경우만 베이스 타입 추가
                self.build_base_types.add(item.base_type)

            # 영향력
            if item.shaper:
                self.build_influences.add("shaper")
            if item.elder:
                self.build_influences.add("elder")
            if item.crusader:
                self.build_influences.add("crusader")
            if item.redeemer:
                self.build_influences.add("redeemer")
            if item.hunter:
                self.build_influences.add("hunter")
            if item.warlord:
                self.build_influences.add("warlord")

    def generate_all_phases(self, output_dir: str) -> Dict[str, str]:
        """모든 진행 단계별 필터 생성

        Returns:
            Dict[str, str]: {phase: file_path}
        """
        results = {}

        for phase in ["Starter", "Mid", "End", "HighEnd"]:
            config = FilterConfig(
                account_name=self.account_name,
                phase=phase,
                league_type=self.league_type,
                strictness=self._calculate_strictness(phase)
            )

            filter_content = self._generate_filter(config)

            # 파일 저장
            filename = f"{self.account_name}_{phase}.filter"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(filter_content)

            results[phase] = filepath
            print(f"[OK] Generated: {filename}", file=sys.stderr)

        return results

    def generate_single_phase(self, phase: str, output_dir: str) -> str:
        """단일 진행 단계 필터 생성"""
        config = FilterConfig(
            account_name=self.account_name,
            phase=phase,
            league_type=self.league_type,
            strictness=self._calculate_strictness(phase)
        )

        filter_content = self._generate_filter(config)

        # 파일 저장
        filename = f"{self.account_name}_{phase}.filter"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(filter_content)

        print(f"[OK] Generated: {filename}", file=sys.stderr)
        return filepath

    def _calculate_strictness(self, phase: str) -> int:
        """엄격도 계산"""
        base = self.PHASE_STRICTNESS.get(phase, 2)
        mod = self.LEAGUE_STRICTNESS_MOD.get(self.league_type, 0)
        return max(0, min(6, base + mod))

    def _generate_filter(self, config: FilterConfig) -> str:
        """필터 파일 내용 생성"""
        lines = []

        # 헤더
        lines.extend(self._generate_header(config))

        # 빌드 하이라이트 섹션 (최상단)
        lines.extend(self._generate_build_highlight_section(config))

        # 고가 아이템 섹션
        lines.extend(self._generate_high_value_section(config))

        # 기본 필터 규칙 (엄격도별)
        lines.extend(self._generate_base_rules(config))

        return '\n'.join(lines)

    def _generate_header(self, config: FilterConfig) -> List[str]:
        """필터 헤더 생성"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        return [
            "#===============================================================================================================",
            f"# PathcraftAI Build Filter - {config.account_name}_{config.phase}",
            "#===============================================================================================================",
            f"# VERSION:  1.0.0",
            f"# TYPE:     {config.phase.upper()}",
            f"# LEAGUE:   {config.league_type}",
            f"# STRICTNESS: {config.strictness}",
            f"# GENERATED: {now}",
            "#",
            "# This filter is auto-generated based on your POB build.",
            "# It highlights items that are relevant to your build.",
            "#",
            "#===============================================================================================================",
            "",
        ]

    def _generate_build_highlight_section(self, config: FilterConfig) -> List[str]:
        """빌드 관련 아이템 하이라이트 섹션"""
        lines = [
            "#===============================================================================================================",
            "# [[0001]] BUILD ITEMS - Your build's core equipment",
            "#===============================================================================================================",
            "",
        ]

        # 유니크 아이템 하이라이트 (녹색 별)
        if self.build_uniques:
            lines.extend([
                "# Build Unique Items - Highest Priority",
                "Show",
                "    Rarity Unique",
                f'    BaseType == {self._format_base_types(self._get_unique_base_types())}',
                "    SetFontSize 45",
                "    SetTextColor 0 255 0 255",  # 녹색
                "    SetBorderColor 0 255 0 255",
                "    SetBackgroundColor 0 75 30 255",
                "    PlayAlertSound 6 300",
                "    PlayEffect Green",
                "    MinimapIcon 0 Green Star",
                "",
            ])

        # 빌드 베이스 타입 (황색 별) - 레어/매직
        if self.build_base_types:
            # 영향력이 있는 경우
            if self.build_influences:
                for influence in self.build_influences:
                    lines.extend([
                        f"# Build Base Types with {influence.title()} Influence",
                        "Show",
                        f"    HasInfluence {influence.title()}",
                        f'    BaseType == {self._format_base_types(list(self.build_base_types))}',
                        "    Rarity <= Rare",
                        "    SetFontSize 45",
                        "    SetTextColor 255 255 0 255",  # 황색
                        "    SetBorderColor 255 255 0 255",
                        "    SetBackgroundColor 75 75 0 255",
                        "    PlayAlertSound 2 300",
                        "    PlayEffect Yellow",
                        "    MinimapIcon 1 Yellow Star",
                        "",
                    ])

            # 일반 베이스 타입 (높은 아이템 레벨)
            lines.extend([
                "# Build Base Types - High Item Level",
                "Show",
                f'    BaseType == {self._format_base_types(list(self.build_base_types))}',
                "    ItemLevel >= 82",
                "    Rarity <= Rare",
                "    SetFontSize 40",
                "    SetTextColor 255 255 119 255",
                "    SetBorderColor 255 255 119 255",
                "    SetBackgroundColor 50 50 0 255",
                "    PlayAlertSound 2 200",
                "    MinimapIcon 2 Yellow Circle",
                "",
            ])

        # 6링크 아이템
        lines.extend([
            "# 6-Link Items",
            "Show",
            "    LinkedSockets 6",
            "    Rarity <= Rare",
            "    SetFontSize 45",
            "    SetTextColor 255 255 255 255",
            "    SetBorderColor 255 0 0 255",
            "    SetBackgroundColor 200 0 0 255",
            "    PlayAlertSound 6 300",
            "    PlayEffect Red",
            "    MinimapIcon 0 Red Diamond",
            "",
        ])

        return lines

    def _generate_high_value_section(self, config: FilterConfig) -> List[str]:
        """고가 아이템 섹션"""
        lines = [
            "#===============================================================================================================",
            "# [[0002]] HIGH VALUE ITEMS",
            "#===============================================================================================================",
            "",
            "# High-tier Currency",
            "Show",
            '    BaseType == "Mirror of Kalandra" "Divine Orb" "Exalted Orb" "Orb of Annulment"',
            "    SetFontSize 45",
            "    SetTextColor 255 0 0 255",
            "    SetBorderColor 255 0 0 255",
            "    SetBackgroundColor 255 255 255 255",
            "    PlayAlertSound 6 300",
            "    PlayEffect Red",
            "    MinimapIcon 0 Red Star",
            "",
            "# Valuable Currency",
            "Show",
            '    BaseType == "Chaos Orb" "Orb of Alchemy" "Orb of Fusing" "Jeweller\'s Orb" "Orb of Regret" "Vaal Orb" "Gemcutter\'s Prism"',
            "    SetFontSize 40",
            "    SetTextColor 255 165 0 255",
            "    SetBorderColor 255 165 0 255",
            "    SetBackgroundColor 50 25 0 255",
            "    PlayAlertSound 2 200",
            "    MinimapIcon 1 Orange Circle",
            "",
        ]

        return lines

    def _generate_base_rules(self, config: FilterConfig) -> List[str]:
        """기본 필터 규칙 (엄격도별)"""
        lines = [
            "#===============================================================================================================",
            f"# [[0100]] BASE RULES - Strictness {config.strictness}",
            "#===============================================================================================================",
            "",
        ]

        # 엄격도에 따른 규칙
        if config.strictness <= 1:
            # Soft/Regular - 대부분 표시
            lines.extend(self._generate_soft_rules())
        elif config.strictness <= 3:
            # Semi-Strict/Strict - 중간
            lines.extend(self._generate_strict_rules())
        else:
            # Very Strict/Uber Strict - 최소만 표시
            lines.extend(self._generate_uber_strict_rules())

        # 마지막 Hide 규칙
        lines.extend([
            "# Hide everything else",
            "Hide",
            "    SetFontSize 18",
            "",
        ])

        return lines

    def _generate_currency_tiering(self, sound_dir: str = "sounds/ko") -> List[str]:
        """NeverSink 스타일 커런시 티어링"""
        return [
            "# ========================================",
            "# CURRENCY TIERING (NeverSink Style)",
            "# ========================================",
            "",
            "# T0 - Mirror/Divine (TOP VALUE)",
            "Show",
            '    Class "Currency"',
            '    BaseType == "Mirror of Kalandra" "Mirror Shard"',
            "    SetFontSize 45",
            "    SetTextColor 255 0 0 255",
            "    SetBorderColor 255 0 0 255",
            "    SetBackgroundColor 255 255 255 255",
            f'    CustomAlertSound "{sound_dir}/currency_top.mp3"',
            "    PlayEffect Red",
            "    MinimapIcon 0 Red Star",
            "",
            "# T1 - Divine Orb",
            "Show",
            '    Class "Currency"',
            '    BaseType == "Divine Orb"',
            "    SetFontSize 45",
            "    SetTextColor 255 0 0 255",
            "    SetBorderColor 255 0 0 255",
            "    SetBackgroundColor 255 255 255 255",
            f'    CustomAlertSound "{sound_dir}/currency_top.mp3"',
            "    PlayEffect Red",
            "    MinimapIcon 0 Red Star",
            "",
            "# T2 - Exalted tier",
            "Show",
            '    Class "Currency"',
            '    BaseType == "Exalted Orb" "Awakener\'s Orb" "Hunter\'s Exalted Orb" "Warlord\'s Exalted Orb" "Redeemer\'s Exalted Orb" "Crusader\'s Exalted Orb" "Orb of Dominance" "Fracturing Orb" "Veiled Chaos Orb"',
            "    SetFontSize 45",
            "    SetTextColor 255 255 255 255",
            "    SetBorderColor 255 255 255 255",
            "    SetBackgroundColor 240 90 35 255",
            f'    CustomAlertSound "{sound_dir}/high_value.mp3"',
            "    PlayEffect Red",
            "    MinimapIcon 0 Red Circle",
            "",
            "# T3 - Annulment/Ancient tier",
            "Show",
            '    Class "Currency"',
            '    BaseType == "Orb of Annulment" "Ancient Orb" "Sacred Orb" "Tainted Divine Teardrop" "Eldritch Exalted Orb" "Tainted Exalted Orb"',
            "    SetFontSize 45",
            "    SetTextColor 255 255 255 255",
            "    SetBorderColor 0 0 0 255",
            "    SetBackgroundColor 240 90 35 255",
            "    PlayAlertSound 1 300",
            "    PlayEffect Yellow",
            "    MinimapIcon 1 Yellow Circle",
            "",
            "# T4 - Chaos tier (High value common)",
            "Show",
            '    Class "Currency"',
            '    BaseType == "Chaos Orb" "Vaal Orb" "Regal Orb" "Blessed Orb" "Gemcutter\'s Prism" "Orb of Regret" "Orb of Unmaking"',
            "    SetFontSize 42",
            "    SetTextColor 255 200 0 255",
            "    SetBorderColor 255 200 0 255",
            "    SetBackgroundColor 65 50 0 255",
            "    PlayAlertSound 2 200",
            "    MinimapIcon 2 Yellow Circle",
            "",
            "# T5 - Alchemy tier",
            "Show",
            '    Class "Currency"',
            '    BaseType == "Orb of Alchemy" "Orb of Fusing" "Cartographer\'s Chisel" "Orb of Scouring" "Orb of Chance" "Jeweller\'s Orb" "Chromatic Orb" "Glassblower\'s Bauble"',
            "    SetFontSize 38",
            "    SetTextColor 170 158 130 255",
            "    SetBorderColor 170 158 130 255",
            "    SetBackgroundColor 30 25 15 255",
            "",
            "# T6 - Basic currency",
            "Show",
            '    Class "Currency"',
            '    BaseType == "Orb of Alteration" "Orb of Augmentation" "Orb of Transmutation" "Armourer\'s Scrap" "Blacksmith\'s Whetstone"',
            "    SetFontSize 32",
            "    SetTextColor 170 158 130 200",
            "    SetBorderColor 170 158 130 200",
            "",
            "# ========================================",
            "# 6-LINK ITEMS",
            "# ========================================",
            "",
            "# 6-Link (Very valuable)",
            "Show",
            "    LinkedSockets 6",
            "    SetFontSize 45",
            "    SetTextColor 255 255 255 255",
            "    SetBorderColor 255 0 0 255",
            "    SetBackgroundColor 200 0 0 255",
            f'    CustomAlertSound "{sound_dir}/six_link.mp3"',
            "    PlayEffect Red",
            "    MinimapIcon 0 Red Diamond",
            "",
            "# 6-Socket (Vendor for jewellers)",
            "Show",
            "    Sockets == 6",
            "    SetFontSize 40",
            "    SetTextColor 255 255 255 255",
            "    SetBorderColor 255 255 255 255",
            "    PlayAlertSound 2 200",
            "",
        ]

    def _generate_soft_rules(self) -> List[str]:
        """Soft 엄격도 규칙"""
        lines = self._generate_currency_tiering()
        lines.extend([
            "# Remaining Currency (show all)",
            "Show",
            '    Class "Currency"',
            "    SetFontSize 35",
            "    SetTextColor 170 158 130 255",
            "    SetBorderColor 170 158 130 255",
            "",
            "# Show all Rare items",
            "Show",
            "    Rarity Rare",
            "    SetFontSize 35",
            "",
            "# Show all Magic items with Quality",
            "Show",
            "    Rarity Magic",
            "    Quality >= 10",
            "    SetFontSize 30",
            "",
            "# Show all Gems",
            "Show",
            '    Class "Gem"',
            "    SetFontSize 30",
            "",
        ])
        return lines

    def _generate_strict_rules(self) -> List[str]:
        """Strict 엄격도 규칙"""
        lines = self._generate_currency_tiering()
        lines.extend([
            "# Remaining Currency (hide scrolls)",
            "Show",
            '    Class "Currency"',
            '    BaseType != "Scroll of Wisdom" "Portal Scroll"',
            "    SetFontSize 35",
            "    SetTextColor 170 158 130 255",
            "    SetBorderColor 170 158 130 255",
            "",
            "# Show Rare items with high item level",
            "Show",
            "    Rarity Rare",
            "    ItemLevel >= 75",
            "    SetFontSize 35",
            "",
            "# Show quality Gems",
            "Show",
            '    Class "Gem"',
            "    Quality >= 10",
            "    SetFontSize 30",
            "",
        ])
        return lines

    def _generate_uber_strict_rules(self) -> List[str]:
        """Uber Strict 엄격도 규칙"""
        lines = self._generate_currency_tiering()
        lines.extend([
            "# Show only influenced Rare items",
            "Show",
            "    Rarity Rare",
            "    HasInfluence Shaper Elder Crusader Redeemer Hunter Warlord",
            "    SetFontSize 35",
            "",
        ])
        return lines

    def _get_unique_base_types(self) -> List[str]:
        """유니크 아이템의 베이스 타입 반환"""
        base_types = []
        for item in self.equipped_items:
            if item.rarity == "UNIQUE" and item.base_type:
                base_types.append(item.base_type)
        return list(set(base_types))

    def _get_rare_base_types(self) -> List[str]:
        """레어/매직 아이템의 베이스 타입 반환"""
        base_types = []
        for item in self.equipped_items:
            if item.rarity in ["RARE", "MAGIC"] and item.base_type:
                base_types.append(item.base_type)
        return list(set(base_types))

    def _format_base_types(self, base_types: List[str]) -> str:
        """베이스 타입 리스트를 필터 형식으로 변환"""
        if not base_types:
            return '""'
        return ' '.join(f'"{bt}"' for bt in base_types)


class NeverSinkParser:
    """NeverSink 필터 파서 - 규칙 블록 파싱 및 수정"""

    def __init__(self, filter_path: str):
        self.filter_path = filter_path
        self.sections: Dict[str, List[str]] = {}  # 섹션별 규칙
        self.rules: List[Dict] = []  # 파싱된 규칙 블록
        self.header: List[str] = []
        self.raw_lines: List[str] = []

    def load(self) -> bool:
        """필터 파일 로드"""
        if not os.path.exists(self.filter_path):
            print(f"[ERROR] Filter not found: {self.filter_path}")
            return False

        try:
            with open(self.filter_path, 'r', encoding='utf-8') as f:
                self.raw_lines = f.readlines()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load filter: {e}")
            return False

    def parse(self) -> bool:
        """필터 파일 파싱"""
        if not self.raw_lines:
            return False

        current_section = "header"
        current_rule = None
        rule_lines = []

        for line in self.raw_lines:
            stripped = line.strip()

            # 섹션 헤더 감지 [[XXXX]]
            section_match = re.match(r'#.*\[\[(\d+)\]\]', stripped)
            if section_match:
                # 이전 규칙 저장
                if current_rule:
                    self.rules.append({
                        'type': current_rule,
                        'section': current_section,
                        'lines': rule_lines
                    })
                    rule_lines = []
                    current_rule = None

                current_section = section_match.group(1)
                if current_section not in self.sections:
                    self.sections[current_section] = []
                continue

            # Show/Hide 블록 시작
            if stripped.startswith('Show') or stripped.startswith('Hide'):
                # 이전 규칙 저장
                if current_rule:
                    self.rules.append({
                        'type': current_rule,
                        'section': current_section,
                        'lines': rule_lines
                    })

                current_rule = 'Show' if stripped.startswith('Show') else 'Hide'
                rule_lines = [line]
                continue

            # 규칙 내용
            if current_rule:
                rule_lines.append(line)
            elif current_section == "header":
                self.header.append(line)

        # 마지막 규칙 저장
        if current_rule:
            self.rules.append({
                'type': current_rule,
                'section': current_section,
                'lines': rule_lines
            })

        print(f"[INFO] Parsed {len(self.rules)} rules from NeverSink filter")
        return True

    def get_rules_by_section(self, section_id: str) -> List[Dict]:
        """특정 섹션의 규칙들 반환"""
        return [r for r in self.rules if r['section'] == section_id]

    def inject_build_rules(self, build_rules: List[str], section_id: str = "0001") -> None:
        """빌드 기반 규칙을 특정 섹션 앞에 주입"""
        # 빌드 규칙을 최상위에 추가 (우선순위 높음)
        build_rule = {
            'type': 'Show',
            'section': section_id,
            'lines': build_rules,
            'is_build_rule': True
        }
        self.rules.insert(0, build_rule)

    def export(self, output_path: str) -> str:
        """수정된 필터 내보내기"""
        lines = []

        # 헤더 추가
        lines.extend(self.header)

        # 규칙 추가
        current_section = None
        for rule in self.rules:
            # 섹션 변경 시 구분선 추가
            if rule['section'] != current_section:
                current_section = rule['section']
                lines.append(f"\n#{'=' * 80}\n")
                if rule.get('is_build_rule'):
                    lines.append(f"# [[{current_section}]] PATHCRAFT BUILD ITEMS\n")
                lines.append(f"#{'=' * 80}\n\n")

            lines.extend(rule['lines'])
            lines.append("\n")

        # 파일 쓰기
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return output_path


class PathcraftFilter:
    """NeverSink 기반 PathcraftAI 필터 생성기"""

    # 5단계 엄격도 시스템
    STRICTNESS_LEVELS = {
        0: "ACT",         # 레벨링 (액트)
        1: "EARLY_MAP",   # 맵핑 초기 (화이트/옐로우)
        2: "MID_MAP",     # 맵핑 중기 (레드)
        3: "LATE_MAP",    # 맵핑 후기 (T16+)
        4: "UBER"         # 우버/특수 콘텐츠
    }

    # NeverSink 필터 매핑 (호환용)
    STRICTNESS_FILES = {
        0: "0-SOFT",
        1: "1-REGULAR",
        2: "2-SEMI-STRICT",
        3: "3-STRICT",
        4: "4-VERY-STRICT"
    }

    def __init__(self, pob_xml_path: str, neversink_dir: Optional[str] = None, league: str = "Settlers"):
        """
        Args:
            pob_xml_path: POB XML 파일 경로
            neversink_dir: NeverSink 필터 폴더 (없으면 기본 생성)
            league: 리그 이름 (poe.ninja 데이터용)
        """
        self.pob_xml_path = pob_xml_path
        self.neversink_dir = neversink_dir
        self.league = league
        self.build_generator = BuildFilterGenerator(pob_xml_path, "PathcraftAI")
        self.ninja_api = POENinjaAPI(league=league)

    def generate(self, strictness = 2, output_path: str = None) -> str:
        """
        NeverSink 기반 PathcraftAI 필터 생성

        Args:
            strictness: 엄격도 레벨 (0-4 또는 문자열)
            output_path: 출력 파일 경로
        """
        # 문자열 엄격도를 정수로 변환
        if isinstance(strictness, str):
            strictness_map = {
                "ACT": 0, "EARLY_MAP": 1, "MID_MAP": 2, "LATE_MAP": 3, "UBER": 4,
                "SOFT": 0, "REGULAR": 1, "SEMI-STRICT": 2, "STRICT": 3, "VERY-STRICT": 4
            }
            strictness = strictness_map.get(strictness.upper(), 2)

        # 1. POB 빌드 파싱
        if not self.build_generator.parse_build():
            print("[ERROR] Failed to parse POB build")
            return ""

        # 2. 빌드 기반 규칙 생성
        build_rules = self._generate_build_overlay()

        # 3. NeverSink 필터 로드 및 병합
        if self.neversink_dir:
            filter_name = f"NeverSink's filter - {self.STRICTNESS_FILES.get(strictness, '2-SEMI-STRICT')}.filter"
            filter_path = os.path.join(self.neversink_dir, filter_name)

            if os.path.exists(filter_path):
                parser = NeverSinkParser(filter_path)
                if parser.load() and parser.parse():
                    # 빌드 규칙 주입
                    parser.inject_build_rules(build_rules)

                    # 출력
                    if not output_path:
                        output_path = f"PathcraftAI_{self.STRICTNESS_FILES.get(strictness, '2-SEMI-STRICT')}.filter"

                    return parser.export(output_path)

        # NeverSink 없으면 기본 필터 생성
        print("[INFO] NeverSink not found, generating standalone filter")
        return self._generate_standalone(build_rules, strictness, output_path)

    def _generate_build_overlay(self) -> List[str]:
        """빌드 기반 오버레이 규칙 생성"""
        rules = []

        # 헤더
        rules.extend([
            f"# PathcraftAI Build Overlay - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
            "# POB-based item highlighting\n",
            "\n"
        ])

        # ===== 1. 현재 빌드에서 사용 중인 유니크 아이템 - 최고 우선순위 =====
        unique_bases = self.build_generator._get_unique_base_types()
        if unique_bases:
            rules.extend([
                "# ========================================\n",
                "# YOUR BUILD ITEMS - HIGHEST PRIORITY\n",
                "# ========================================\n",
                "\n",
                "# Build Unique Items - EXACT MATCH (Cyan/Magenta highlight)\n",
                "Show\n",
                "    Rarity Unique\n",
                f"    BaseType == {self.build_generator._format_base_types(unique_bases)}\n",
                "    SetFontSize 45\n",
                "    SetTextColor 0 255 255 255\n",      # 시안 텍스트
                "    SetBorderColor 255 0 255 255\n",    # 마젠타 테두리
                "    SetBackgroundColor 75 0 130 255\n", # 보라색 배경
                "    PlayAlertSound 1 300\n",            # 가장 눈에 띄는 사운드
                "    PlayEffect Purple\n",              # 보라색 빔
                "    MinimapIcon 0 Purple Star\n",      # 미니맵 별표
                "    CustomAlertSound \"sounds\\build_item.mp3\"\n" if False else "",  # 커스텀 사운드 (비활성)
                "\n"
            ])
            # 빈 문자열 제거
            rules = [r for r in rules if r]

        # ===== 2. 빌드에서 사용 중인 레어/매직 베이스 타입 =====
        rare_bases = self.build_generator._get_rare_base_types()
        if rare_bases:
            rules.extend([
                "# Build Rare/Magic Base Types - For crafting upgrades\n",
                "Show\n",
                f"    BaseType == {self.build_generator._format_base_types(rare_bases)}\n",
                "    Rarity <= Rare\n",
                "    ItemLevel >= 82\n",
                "    SetFontSize 45\n",
                "    SetTextColor 255 150 255 255\n",    # 밝은 핑크
                "    SetBorderColor 255 100 255 255\n",  # 핑크 테두리
                "    SetBackgroundColor 60 0 60 255\n",  # 어두운 보라
                "    PlayAlertSound 3 300\n",            # 눈에 띄는 사운드
                "    PlayEffect Pink\n",
                "    MinimapIcon 0 Pink Diamond\n",
                "\n"
            ])

        # ===== 3. 빌드 베이스 타입 + 인플루언스 =====
        all_bases = list(self.build_generator.build_base_types)
        if all_bases:
            # 인플루언스 아이템 (모든 인플루언스 통합) - 매우 중요
            rules.extend([
                "# Build Base Types with Influence - VERY IMPORTANT\n",
                "Show\n",
                "    HasInfluence Shaper Elder Crusader Redeemer Hunter Warlord\n",
                f"    BaseType == {self.build_generator._format_base_types(all_bases)}\n",
                "    Rarity <= Rare\n",
                "    SetFontSize 45\n",
                "    SetTextColor 255 255 0 255\n",       # 밝은 노랑
                "    SetBorderColor 255 200 0 255\n",     # 금색 테두리
                "    SetBackgroundColor 100 75 0 255\n",  # 어두운 금색
                "    PlayAlertSound 4 300\n",             # 눈에 띄는 사운드
                "    PlayEffect Yellow\n",
                "    MinimapIcon 0 Yellow Star\n",        # 가장 큰 아이콘
                "\n"
            ])

            # 높은 아이템 레벨 (ilvl 82+)
            rules.extend([
                "# Build Base Types - High Item Level (82+)\n",
                "Show\n",
                f"    BaseType == {self.build_generator._format_base_types(all_bases)}\n",
                "    ItemLevel >= 82\n",
                "    Rarity <= Rare\n",
                "    SetFontSize 42\n",
                "    SetTextColor 255 255 119 255\n",
                "    SetBorderColor 255 255 0 255\n",
                "    SetBackgroundColor 60 60 0 255\n",
                "    PlayAlertSound 2 250\n",
                "    PlayEffect Yellow\n",
                "    MinimapIcon 1 Yellow Diamond\n",
                "\n"
            ])

            # 일반 아이템 레벨 (75+)
            rules.extend([
                "# Build Base Types - Normal Item Level (75+)\n",
                "Show\n",
                f"    BaseType == {self.build_generator._format_base_types(all_bases)}\n",
                "    ItemLevel >= 75\n",
                "    Rarity <= Rare\n",
                "    SetFontSize 38\n",
                "    SetTextColor 200 200 100 255\n",
                "    SetBorderColor 200 200 0 255\n",
                "    MinimapIcon 2 Yellow Circle\n",
                "\n"
            ])

        # 빌드 스탯 기반 규칙 (장착 아이템 분석)
        rules.extend(self._generate_build_stat_rules())

        # poe.ninja 가치 기반 유니크 규칙
        rules.extend(self._generate_value_based_rules())

        return rules

    def _generate_build_stat_rules(self) -> List[str]:
        """빌드 스탯 분석 기반 아이템 하이라이트 규칙 생성"""
        rules = []

        # POB 아이템 파서에서 빌드 분석
        analysis = self.build_generator.parser.analyze_build_for_filter()

        if not analysis['keywords']:
            return rules

        rules.append("# Build Stat Analysis - Auto-detected keywords\n")
        rules.append(f"# Build Type: {analysis['build_type']}, Primary Element: {analysis['primary_element']}\n")
        rules.append(f"# Keywords: {', '.join(analysis['keywords'])}\n")
        rules.append("\n")

        # 주요 속성에 따른 젬 레벨 하이라이트
        if analysis['gem_levels']:
            gem_types = set()
            for gem_info in analysis['gem_levels']:
                gem_types.add(gem_info['type'])

            # 젬 레벨 증가가 중요한 빌드 - 해당 무기/아뮬렛 강조
            for gem_type in gem_types:
                # 주문 젬 레벨 빌드
                if gem_type in ['Spell', 'Fire', 'Cold', 'Lightning', 'Chaos']:
                    rules.extend([
                        f"# +Level to {gem_type} Gems weapons/amulets\n",
                        "Show\n",
                        '    Class "Wands" "Sceptres" "Daggers" "Rune Daggers" "Amulets"\n',
                        "    Rarity Rare\n",
                        "    ItemLevel >= 82\n",
                        "    SetFontSize 42\n",
                        "    SetTextColor 180 255 180 255\n",
                        "    SetBorderColor 100 255 100 255\n",
                        "    SetBackgroundColor 30 60 30 255\n",
                        "    PlayAlertSound 2 200\n",
                        "    MinimapIcon 2 Green Triangle\n",
                        "\n"
                    ])

        # 속성 변환 빌드 하이라이트
        if analysis['conversions']:
            conversion_types = set()
            for conv in analysis['conversions']:
                conversion_types.add(conv['to'].lower())

            for conv_to in conversion_types:
                rules.append(f"# Conversion to {conv_to.title()} - Build uses element conversion\n")

            # 변환 빌드는 특정 유니크가 중요 - 글로브/헬멧/부츠 강조
            rules.extend([
                "# Conversion Build - Relevant unique slots\n",
                "Show\n",
                '    Class "Gloves" "Helmets" "Boots"\n',
                "    Rarity Unique\n",
                "    SetFontSize 42\n",
                "    SetTextColor 255 200 100 255\n",
                "    SetBorderColor 255 150 50 255\n",
                "    SetBackgroundColor 60 40 10 255\n",
                "    PlayAlertSound 1 200\n",
                "\n"
            ])

        # 빌드 타입별 추가 규칙
        build_type = analysis['build_type']

        if build_type == 'spell':
            # 스펠 빌드 - 캐스터 무기 강조
            rules.extend([
                "# Spell Build - Caster weapons highlight\n",
                "Show\n",
                '    Class "Wands" "Sceptres" "Daggers" "Rune Daggers"\n',
                "    Rarity Rare\n",
                "    ItemLevel >= 84\n",
                "    SetFontSize 40\n",
                "    SetTextColor 150 200 255 255\n",
                "    SetBorderColor 100 150 255 255\n",
                "    SetBackgroundColor 20 30 60 255\n",
                "    PlayAlertSound 2 150\n",
                "\n"
            ])

        elif build_type == 'attack':
            # 어택 빌드 - 물리 무기 강조
            rules.extend([
                "# Attack Build - Physical weapons highlight\n",
                "Show\n",
                '    Class "One Hand" "Two Hand" "Bows" "Claws" "Axes" "Swords" "Maces"\n',
                "    Rarity Rare\n",
                "    ItemLevel >= 83\n",
                "    SetFontSize 40\n",
                "    SetTextColor 255 150 150 255\n",
                "    SetBorderColor 255 100 100 255\n",
                "    SetBackgroundColor 60 20 20 255\n",
                "    PlayAlertSound 2 150\n",
                "\n"
            ])

        elif build_type == 'dot':
            # DOT 빌드 - 디버프/지속 피해 아이템 강조
            rules.extend([
                "# DoT Build - Duration/debuff items highlight\n",
                "Show\n",
                '    Class "Wands" "Sceptres" "Bows"\n',
                "    Rarity Rare\n",
                "    ItemLevel >= 84\n",
                "    SetFontSize 40\n",
                "    SetTextColor 200 100 255 255\n",
                "    SetBorderColor 150 50 200 255\n",
                "    SetBackgroundColor 40 20 60 255\n",
                "    PlayAlertSound 2 150\n",
                "\n"
            ])

        # 주요 데미지 타입 기반 젬 하이라이트
        primary_element = analysis['primary_element']
        if primary_element:
            element_colors = {
                'fire': ('255 100 50', '200 50 0'),
                'cold': ('100 200 255', '50 150 255'),
                'lightning': ('255 255 100', '200 200 0'),
                'chaos': ('200 100 255', '150 50 200'),
                'physical': ('200 200 200', '150 150 150')
            }

            if primary_element in element_colors:
                text_color, border_color = element_colors[primary_element]
                rules.extend([
                    f"# Primary Element: {primary_element.title()} - Skill gems\n",
                    "Show\n",
                    f'    Class "Skill Gems"\n',
                    f'    GemLevel >= 20\n',
                    f"    SetFontSize 38\n",
                    f"    SetTextColor {text_color} 255\n",
                    f"    SetBorderColor {border_color} 255\n",
                    "\n"
                ])

        return rules

    def _generate_value_based_rules(self) -> List[str]:
        """poe.ninja 경제 데이터 기반 유니크 규칙 생성 (베이스 타입 사용)"""
        rules = []

        try:
            # 유니크 가격 + 베이스타입 데이터 로드
            unique_data = self.ninja_api.get_unique_with_base_types()
            if not unique_data:
                print("[INFO] No poe.ninja price data available", file=sys.stderr)
                return rules

            # 가격대별 유니크 분류 (베이스 타입 기준)
            top_tier = []      # 100+ chaos
            high_tier = []     # 20-100 chaos
            mid_tier = []      # 5-20 chaos

            for name, info in unique_data.items():
                base_type = info.get('base_type', '')
                price = info.get('price', 0)

                # 베이스 타입이 있어야 필터에서 사용 가능
                if not base_type:
                    continue

                if price >= 100:
                    top_tier.append(base_type)
                elif price >= 20:
                    high_tier.append(base_type)
                elif price >= 5:
                    mid_tier.append(base_type)

            # 중복 제거 (같은 베이스에 여러 유니크가 있을 수 있음)
            top_tier = list(set(top_tier))
            high_tier = list(set(high_tier))
            mid_tier = list(set(mid_tier))

            # 최상위 유니크 (100+ chaos) - 빨간색 배경
            if top_tier:
                top_bases = ' '.join('"' + n + '"' for n in top_tier[:50])
                rules.extend([
                    "# High Value Uniques (100+ chaos) - poe.ninja\n",
                    "Show\n",
                    "    Rarity Unique\n",
                    f"    BaseType == {top_bases}\n",
                    "    SetFontSize 45\n",
                    "    SetTextColor 255 0 0 255\n",
                    "    SetBorderColor 255 0 0 255\n",
                    "    SetBackgroundColor 100 0 0 255\n",
                    "    PlayAlertSound 1 300\n",
                    "    PlayEffect Red\n",
                    "    MinimapIcon 0 Red Star\n",
                    "\n"
                ])

            # 고가 유니크 (20-100 chaos) - 주황색
            if high_tier:
                high_bases = ' '.join('"' + n + '"' for n in high_tier[:50])
                rules.extend([
                    "# Valuable Uniques (20-100 chaos) - poe.ninja\n",
                    "Show\n",
                    "    Rarity Unique\n",
                    f"    BaseType == {high_bases}\n",
                    "    SetFontSize 45\n",
                    "    SetTextColor 255 150 0 255\n",
                    "    SetBorderColor 255 150 0 255\n",
                    "    SetBackgroundColor 75 50 0 255\n",
                    "    PlayAlertSound 3 300\n",
                    "    PlayEffect Yellow\n",
                    "    MinimapIcon 1 Yellow Star\n",
                    "\n"
                ])

            # 중가 유니크 (5-20 chaos) - 파란색
            if mid_tier:
                mid_bases = ' '.join('"' + n + '"' for n in mid_tier[:50])
                rules.extend([
                    "# Mid Value Uniques (5-20 chaos) - poe.ninja\n",
                    "Show\n",
                    "    Rarity Unique\n",
                    f"    BaseType == {mid_bases}\n",
                    "    SetFontSize 40\n",
                    "    SetTextColor 100 200 255 255\n",
                    "    SetBorderColor 100 200 255 255\n",
                    "    SetBackgroundColor 0 50 75 255\n",
                    "    PlayAlertSound 4 200\n",
                    "    MinimapIcon 2 Blue Circle\n",
                    "\n"
                ])

            print(f"[OK] Generated value rules: {len(top_tier)} top, {len(high_tier)} high, {len(mid_tier)} mid tier uniques", file=sys.stderr)

        except Exception as e:
            print(f"[WARN] Failed to generate value-based rules: {e}", file=sys.stderr)

        return rules

    def _generate_strictness_rules(self, strictness: int) -> List[str]:
        """5단계 엄격도에 따른 기본 규칙 생성

        Args:
            strictness: 0 (ACT) ~ 4 (UBER)
        """
        rules = []

        # 엄격도별 설정
        strictness_config = {
            0: {  # ACT - 레벨링
                'min_rare_ilvl': 1,
                'show_all_currency': True,
                'show_all_gems': True,
                'show_magic': True,
                'show_normal_6s': True,
                'show_leveling_uniques': True,
            },
            1: {  # EARLY_MAP - 맵핑 초기
                'min_rare_ilvl': 60,
                'show_all_currency': True,
                'show_all_gems': False,
                'show_magic': False,
                'show_normal_6s': True,
                'show_leveling_uniques': False,
            },
            2: {  # MID_MAP - 맵핑 중기
                'min_rare_ilvl': 75,
                'show_all_currency': False,
                'show_all_gems': False,
                'show_magic': False,
                'show_normal_6s': True,
                'show_leveling_uniques': False,
            },
            3: {  # LATE_MAP - 맵핑 후기
                'min_rare_ilvl': 83,
                'show_all_currency': False,
                'show_all_gems': False,
                'show_magic': False,
                'show_normal_6s': False,
                'show_leveling_uniques': False,
            },
            4: {  # UBER - 우버/특수
                'min_rare_ilvl': 86,
                'show_all_currency': False,
                'show_all_gems': False,
                'show_magic': False,
                'show_normal_6s': False,
                'show_leveling_uniques': False,
            },
        }

        config = strictness_config.get(strictness, strictness_config[2])
        strictness_name = self.STRICTNESS_LEVELS.get(strictness, "MID_MAP")

        rules.append(f"\n# Strictness Level: {strictness_name}\n")

        # 인플루언스 레어 아이템 (항상 표시)
        rules.extend([
            "\n# Influenced Rare Items - Always Show\n",
            "Show\n",
            "    Rarity Rare\n",
            "    HasInfluence Shaper Elder Crusader Redeemer Hunter Warlord\n",
            "    SetFontSize 45\n",
            "    SetTextColor 255 200 0 255\n",
            "    SetBorderColor 255 200 0 255\n",
            "    PlayAlertSound 2 300\n",
            "\n"
        ])

        # 레어 아이템 (엄격도에 따른 최소 ilvl)
        rules.extend([
            f"# Rare Items (ilvl >= {config['min_rare_ilvl']})\n",
            "Show\n",
            "    Rarity Rare\n",
            f"    ItemLevel >= {config['min_rare_ilvl']}\n",
            "    SetFontSize 35\n",
            "\n"
        ])

        # 6소켓 아이템 (판매용)
        if config['show_normal_6s']:
            rules.extend([
                "# 6-Socket Items (Vendor)\n",
                "Show\n",
                "    Sockets == 6\n",
                "    SetFontSize 45\n",
                "    SetTextColor 255 255 255 255\n",
                "    SetBorderColor 255 255 255 255\n",
                "    PlayAlertSound 2 300\n",
                "\n"
            ])

        # 커런시
        if config['show_all_currency']:
            rules.extend([
                "# All Currency\n",
                "Show\n",
                '    Class "Currency"\n',
                "    SetFontSize 35\n",
                "\n"
            ])
        else:
            rules.extend([
                "# Valuable Currency Only\n",
                "Show\n",
                '    Class "Currency"\n',
                '    BaseType == "Chaos Orb" "Exalted Orb" "Divine Orb" "Mirror of Kalandra" "Orb of Alchemy" "Vaal Orb" "Orb of Annulment" "Ancient Orb" "Awakener\'s Orb"\n',
                "    SetFontSize 45\n",
                "    PlayAlertSound 1 300\n",
                "\n"
            ])

        # 젬
        if config['show_all_gems']:
            rules.extend([
                "# All Gems\n",
                "Show\n",
                '    Class "Skill Gems" "Support Gems"\n',
                "    SetFontSize 30\n",
                "\n"
            ])
        else:
            rules.extend([
                "# Quality Gems Only\n",
                "Show\n",
                '    Class "Skill Gems" "Support Gems"\n',
                "    Quality >= 10\n",
                "    SetFontSize 35\n",
                "\n"
            ])

        # 매직 아이템
        if config['show_magic']:
            rules.extend([
                "# Magic Items with Quality\n",
                "Show\n",
                "    Rarity Magic\n",
                "    Quality >= 10\n",
                "    SetFontSize 30\n",
                "\n"
            ])

        # 모든 유니크 표시 (기본)
        rules.extend([
            "# All Unique Items\n",
            "Show\n",
            "    Rarity Unique\n",
            "    SetFontSize 40\n",
            "    SetTextColor 175 96 37 255\n",
            "    SetBorderColor 175 96 37 255\n",
            "    PlayAlertSound 3 300\n",
            "\n"
        ])

        # 맵
        rules.extend([
            "# Maps\n",
            "Show\n",
            '    Class "Maps"\n',
            "    SetFontSize 40\n",
            "    SetTextColor 255 255 255 255\n",
            "    SetBorderColor 255 255 255 255\n",
            "\n"
        ])

        # 나머지 숨기기 (LATE_MAP 이상에서만)
        if strictness >= 3:
            rules.extend([
                "# Hide remaining items\n",
                "Hide\n",
                "    SetFontSize 18\n",
                "\n"
            ])

        return rules

    def _generate_standalone(self, build_rules: List[str], strictness: int, output_path: str) -> str:
        """독립 실행형 필터 생성 (NeverSink 없을 때)"""
        if not output_path:
            output_path = f"PathcraftAI_Standalone_{strictness}.filter"

        lines = []

        # 헤더
        lines.extend([
            "#" + "=" * 80 + "\n",
            "# PathcraftAI Build Filter (Standalone)\n",
            "#" + "=" * 80 + "\n",
            f"# STRICTNESS: {strictness}\n",
            f"# GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
            "#" + "=" * 80 + "\n",
            "\n"
        ])

        # 빌드 규칙
        lines.extend(build_rules)

        # 7단계 엄격도 시스템에 따른 규칙 생성
        lines.extend(self._generate_strictness_rules(strictness))

        # 파일 쓰기
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"[OK] Generated standalone filter: {output_path}")
        return output_path


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate build-based item filters")
    parser.add_argument("pob_xml", help="Path to POB XML file")
    parser.add_argument("account_name", help="OAuth account name")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    parser.add_argument("--league", "-l", default="SC", choices=["SC", "HC", "SSF", "Ruthless"],
                       help="League type")
    parser.add_argument("--phase", "-p", choices=["Starter", "Mid", "End", "HighEnd", "all"],
                       default="all", help="Filter phase to generate")

    args = parser.parse_args()

    # 출력 디렉토리 확인
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    # 필터 생성기 초기화
    generator = BuildFilterGenerator(args.pob_xml, args.account_name, args.league)

    # 빌드 파싱
    if not generator.parse_build():
        print("[ERROR] Failed to parse build", file=sys.stderr)
        return 1

    # 필터 생성
    if args.phase == "all":
        results = generator.generate_all_phases(args.output)
        print(f"\n[완료] Generated {len(results)} filters:")
        for phase, filepath in results.items():
            print(f"  - {phase}: {filepath}")
    else:
        filepath = generator.generate_single_phase(args.phase, args.output)
        print(f"\n[완료] Generated filter: {filepath}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
