#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POB XML Item Parser
POB XML에서 아이템 정보를 파싱하고 POE Trade 필터를 자동 생성
"""

import sys
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import Counter

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


@dataclass
class ParsedItem:
    """파싱된 아이템 정보"""
    id: int
    name: str
    base_type: str
    rarity: str  # NORMAL, MAGIC, RARE, UNIQUE
    slot: Optional[str] = None

    # 소켓/링크
    sockets: str = ""  # "R-R-R-R-R-R" 형식
    socket_count: int = 0
    link_count: int = 0

    # 영향력
    shaper: bool = False
    elder: bool = False
    crusader: bool = False
    redeemer: bool = False
    hunter: bool = False
    warlord: bool = False
    synthesised: bool = False
    fractured: bool = False

    # 특수 속성
    corrupted: bool = False
    foulborn: bool = False
    mirrored: bool = False
    keystone: Optional[str] = None  # Skin of the Lords 등의 키스톤

    # 스탯
    item_level: int = 0
    quality: int = 0
    armour: int = 0
    evasion: int = 0
    energy_shield: int = 0

    # 모드
    implicits: List[str] = field(default_factory=list)
    explicits: List[str] = field(default_factory=list)

    # 원본 데이터
    raw_text: str = ""


class POBItemParser:
    """POB XML 아이템 파서"""

    def __init__(self):
        self.items: Dict[int, ParsedItem] = {}
        self.slots: Dict[str, int] = {}  # slot_name -> item_id

    def parse_xml(self, xml_path: str) -> List[ParsedItem]:
        """XML 파일에서 아이템 파싱"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Items 섹션 찾기
            items_elem = root.find(".//Items")
            if items_elem is None:
                print("[ERROR] Items section not found", file=sys.stderr)
                return []

            # 아이템 파싱
            for item_elem in items_elem.findall("Item"):
                item = self._parse_item_element(item_elem)
                if item:
                    self.items[item.id] = item

            # 슬롯 매핑 파싱
            for item_set in items_elem.findall(".//ItemSet"):
                for slot_elem in item_set.findall("Slot"):
                    slot_name = slot_elem.get("name", "")
                    item_id = int(slot_elem.get("itemId", 0))
                    if item_id > 0 and slot_name:
                        self.slots[slot_name] = item_id
                        if item_id in self.items:
                            self.items[item_id].slot = slot_name

            return list(self.items.values())

        except Exception as e:
            print(f"[ERROR] Failed to parse XML: {e}", file=sys.stderr)
            return []

    def _parse_item_element(self, elem: ET.Element) -> Optional[ParsedItem]:
        """Item 엘리먼트 파싱"""
        try:
            item_id = int(elem.get("id", 0))
            if item_id == 0:
                return None

            # 아이템 텍스트 가져오기
            raw_text = elem.text or ""
            raw_text = raw_text.strip()

            if not raw_text:
                return None

            # 기본 정보 파싱
            item = ParsedItem(
                id=item_id,
                name="",
                base_type="",
                rarity="RARE",
                raw_text=raw_text
            )

            # 라인별 파싱
            lines = raw_text.split('\n')
            current_section = "header"
            implicits_count = 0

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Rarity
                if line.startswith("Rarity:"):
                    item.rarity = line.replace("Rarity:", "").strip().upper()
                    continue

                # 이름과 베이스 타입
                if current_section == "header" and not line.startswith("{") and ":" not in line:
                    # UNIQUE: 첫줄=이름, 둘째줄=베이스
                    # RARE/MAGIC: 첫줄=커스텀이름, 둘째줄=베이스타입
                    if item.rarity == "UNIQUE":
                        if not item.name:
                            item.name = line
                        elif not item.base_type:
                            item.base_type = line
                    else:
                        # RARE/MAGIC 아이템
                        if not item.name:
                            item.name = line  # 커스텀 이름
                        elif not item.base_type:
                            item.base_type = line  # 실제 베이스 타입

                # Sockets
                if line.startswith("Sockets:"):
                    item.sockets = line.replace("Sockets:", "").strip()
                    item.socket_count, item.link_count = self._parse_sockets(item.sockets)
                    continue

                # Quality
                if line.startswith("Quality:"):
                    try:
                        item.quality = int(line.replace("Quality:", "").strip())
                    except:
                        pass
                    continue

                # Item Level / LevelReq
                if line.startswith("LevelReq:"):
                    try:
                        item.item_level = int(line.replace("LevelReq:", "").strip())
                    except:
                        pass
                    continue

                # Armour
                if line.startswith("Armour:"):
                    try:
                        item.armour = int(line.replace("Armour:", "").strip())
                    except:
                        pass
                    continue

                # Energy Shield
                if line.startswith("Energy Shield:"):
                    try:
                        item.energy_shield = int(line.replace("Energy Shield:", "").strip())
                    except:
                        pass
                    continue

                # Evasion
                if line.startswith("Evasion:"):
                    try:
                        item.evasion = int(line.replace("Evasion:", "").strip())
                    except:
                        pass
                    continue

                # Implicits count
                if line.startswith("Implicits:"):
                    try:
                        implicits_count = int(line.replace("Implicits:", "").strip())
                    except:
                        pass
                    current_section = "implicits"
                    continue

                # 영향력
                if "Shaper Item" in line:
                    item.shaper = True
                if "Elder Item" in line:
                    item.elder = True
                if "Crusader Item" in line:
                    item.crusader = True
                if "Redeemer Item" in line:
                    item.redeemer = True
                if "Hunter Item" in line:
                    item.hunter = True
                if "Warlord Item" in line:
                    item.warlord = True
                if "Synthesised Item" in line or "Synthesised" in line:
                    item.synthesised = True
                if "Fractured Item" in line:
                    item.fractured = True

                # Searing Exarch / Eater of Worlds (영향력으로 처리)
                if "Searing Exarch Item" in line:
                    item.crusader = True  # 대체 표시
                if "Eater of Worlds Item" in line:
                    item.redeemer = True  # 대체 표시

                # 부패
                if line == "Corrupted":
                    item.corrupted = True

                # Foulborn (삿된) - 이름에 "Foulborn" 포함 여부
                if "Foulborn" in item.name:
                    item.foulborn = True

                # 모드 파싱 (implicit/explicit)
                if current_section == "implicits" and implicits_count > 0:
                    if not line.startswith("{") or "{crafted}" in line or "{tags:" in line:
                        # 태그 제거
                        clean_line = re.sub(r'\{[^}]*\}', '', line).strip()
                        if clean_line:
                            item.implicits.append(clean_line)

                            # 키스톤 감지 (Skin of the Lords 등)
                            # 패턴: "Grants Level X <Keystone Name>"
                            keystone_match = re.search(r'Grants Level \d+ (.+)', clean_line)
                            if keystone_match:
                                item.keystone = keystone_match.group(1).strip()

                            implicits_count -= 1
                            if implicits_count == 0:
                                current_section = "explicits"
                elif current_section == "explicits":
                    if not line.startswith("Crafted:") and not line.startswith("Prefix:") and not line.startswith("Suffix:"):
                        clean_line = re.sub(r'\{[^}]*\}', '', line).strip()
                        if clean_line and not any(clean_line.startswith(x) for x in ["Variant:", "Selected", "Has Alt", "Limited"]):
                            item.explicits.append(clean_line)

            return item

        except Exception as e:
            print(f"[ERROR] Failed to parse item element: {e}", file=sys.stderr)
            return None

    def _parse_sockets(self, socket_str: str) -> Tuple[int, int]:
        """소켓 문자열에서 소켓 수와 최대 링크 수 계산"""
        if not socket_str:
            return 0, 0

        # 소켓 색상: R, G, B, W, A (Abyssal)
        socket_count = len(re.findall(r'[RGBWA]', socket_str))

        # 링크 그룹 분리 (공백으로)
        groups = socket_str.split()
        max_links = 0

        for group in groups:
            # '-'로 연결된 소켓 수 계산
            links = group.count('-') + 1
            if links > max_links:
                max_links = links

        return socket_count, max_links

    def get_equipped_items(self) -> List[ParsedItem]:
        """장착된 아이템만 반환"""
        equipped = []

        # 주요 슬롯
        main_slots = [
            "Helmet", "Body Armour", "Gloves", "Boots", "Belt",
            "Amulet", "Ring 1", "Ring 2",
            "Weapon 1", "Weapon 2",
            "Flask 1", "Flask 2", "Flask 3", "Flask 4", "Flask 5"
        ]

        for slot_name in main_slots:
            if slot_name in self.slots:
                item_id = self.slots[slot_name]
                if item_id in self.items:
                    equipped.append(self.items[item_id])

        return equipped

    def generate_trade_filters(self, item: ParsedItem) -> Dict:
        """아이템에 대한 POE Trade 필터 생성"""
        filters = {
            "name": item.name if item.rarity == "UNIQUE" else "",
            "type": item.base_type if item.rarity != "UNIQUE" else None,
            "influence": None,
            "links": item.link_count if item.link_count >= 5 else None,
            "sockets": None,
            "corrupted": item.corrupted if item.corrupted else None,
            "foulborn": item.foulborn if item.foulborn else None,
            "keystone": item.keystone if item.keystone else None,
            "stats": []
        }

        # 영향력 설정
        if item.shaper:
            filters["influence"] = "shaper"
        elif item.elder:
            filters["influence"] = "elder"
        elif item.crusader:
            filters["influence"] = "crusader"
        elif item.redeemer:
            filters["influence"] = "redeemer"
        elif item.hunter:
            filters["influence"] = "hunter"
        elif item.warlord:
            filters["influence"] = "warlord"

        # 주요 스탯 필터 (Life, Resistance 등)
        for mod in item.explicits:
            # Life
            life_match = re.search(r'\+(\d+) to maximum Life', mod)
            if life_match:
                life_value = int(life_match.group(1))
                if life_value >= 50:
                    filters["stats"].append({
                        "id": "explicit.stat_3299347043",
                        "value": {"min": int(life_value * 0.8)}  # 80% 최소값
                    })

            # Total Elemental Resistance
            res_match = re.search(r'\+(\d+)% to (Fire|Cold|Lightning) Resistance', mod)
            if res_match:
                res_value = int(res_match.group(1))
                if res_value >= 30:
                    # pseudo total resistance 사용
                    pass  # 복잡한 로직 필요

        return filters

    def extract_build_stats(self) -> Dict:
        """장착된 아이템에서 빌드 스탯 키워드 추출"""
        equipped = self.get_equipped_items()

        # 스탯 카테고리
        stats = {
            'offensive': Counter(),      # 공격적 스탯
            'defensive': Counter(),      # 방어적 스탯
            'utility': Counter(),        # 유틸리티 스탯
            'conversion': [],            # 속성 변환
            'gem_level': [],            # 젬 레벨 증가
            'damage_types': Counter(),   # 데미지 타입
            'all_mods': []              # 모든 모드 (필터용)
        }

        # 키워드 패턴 정의
        offensive_patterns = [
            (r'(\d+)% increased Spell Damage', 'spell_damage'),
            (r'(\d+)% increased Elemental Damage', 'elemental_damage'),
            (r'(\d+)% increased (Fire|Cold|Lightning) Damage', 'elemental_damage'),
            (r'(\d+)% increased Physical Damage', 'physical_damage'),
            (r'(\d+)% increased Attack Speed', 'attack_speed'),
            (r'(\d+)% increased Cast Speed', 'cast_speed'),
            (r'(\d+)% increased Critical Strike Chance', 'crit_chance'),
            (r'\+(\d+)% to Critical Strike Multiplier', 'crit_multi'),
            (r'(\d+)% increased Damage over Time', 'dot_damage'),
            (r'(\d+)% increased (Chaos|Poison) Damage', 'chaos_damage'),
            (r'Adds (\d+) to (\d+) (Fire|Cold|Lightning|Physical|Chaos) Damage', 'flat_damage'),
            (r'\+(\d+) to Level of all (.+) Skill Gems', 'gem_level'),
            (r'\+(\d+) to Level of all (.+) Gems', 'gem_level'),
            (r'(\d+)% increased Area of Effect', 'area_effect'),
            (r'(\d+)% increased Projectile Speed', 'projectile_speed'),
            (r'Gain (\d+)% of (.+) Damage as Extra (.+) Damage', 'damage_conversion'),
        ]

        defensive_patterns = [
            (r'\+(\d+) to maximum Life', 'max_life'),
            (r'\+(\d+) to maximum Energy Shield', 'max_es'),
            (r'\+(\d+) to maximum Mana', 'max_mana'),
            (r'\+(\d+)% to (Fire|Cold|Lightning|Chaos|all Elemental) Resistance', 'resistance'),
            (r'(\d+)% increased Armour', 'armour'),
            (r'(\d+)% increased Evasion Rating', 'evasion'),
            (r'(\d+)% increased Energy Shield', 'energy_shield'),
            (r'(\d+)% increased maximum Life', 'max_life_percent'),
            (r'(\d+)% of Physical Damage.*taken as', 'phys_mitigation'),
            (r'(\d+)% additional Physical Damage Reduction', 'phys_reduction'),
            (r'Recover (\d+)% of Life', 'life_recovery'),
            (r'Life Regeneration', 'life_regen'),
        ]

        utility_patterns = [
            (r'(\d+)% increased Movement Speed', 'movement_speed'),
            (r'(\d+)% reduced Mana Cost', 'mana_cost'),
            (r'\+(\d+)% to Quality of Socketed Gems', 'gem_quality'),
            (r'Socketed Gems are Supported by Level (\d+) (.+)', 'pseudo_links'),
            (r'(\d+)% increased Effect of (.+)', 'effect_increase'),
            (r'(\d+)% increased Cooldown Recovery Rate', 'cooldown'),
            (r'(\d+)% increased Duration', 'skill_duration'),
        ]

        # 컨버전 패턴
        conversion_patterns = [
            (r'(\d+)% of Physical Damage Converted to (Fire|Cold|Lightning|Chaos) Damage', 'phys_to_ele'),
            (r'(\d+)% of (Fire|Cold|Lightning) Damage Converted to (Fire|Cold|Lightning|Chaos) Damage', 'ele_to_ele'),
            (r'(\d+)% of Elemental Damage Converted to Chaos Damage', 'ele_to_chaos'),
        ]

        # 젬 레벨 패턴
        gem_patterns = [
            (r'\+(\d+) to Level of all (Fire|Cold|Lightning|Chaos|Physical|Spell|Minion|Aura|Curse|Vaal|Trap|Mine|Totem|Brand|Herald|Golem) Skill Gems', 'skill_gem'),
            (r'\+(\d+) to Level of all (Fire|Cold|Lightning|Chaos|Physical|Spell|Minion|Aura|Curse|Vaal|Trap|Mine|Totem|Brand|Herald|Golem) Gems', 'support_gem'),
            (r'\+(\d+) to Level of Socketed (.+) Gems', 'socketed_gem'),
        ]

        # 모든 장착 아이템 분석
        for item in equipped:
            all_mods = item.implicits + item.explicits
            stats['all_mods'].extend(all_mods)

            for mod in all_mods:
                # 공격 스탯
                for pattern, stat_type in offensive_patterns:
                    if re.search(pattern, mod, re.IGNORECASE):
                        stats['offensive'][stat_type] += 1

                        # 데미지 타입 감지
                        if 'Fire' in mod:
                            stats['damage_types']['fire'] += 1
                        if 'Cold' in mod:
                            stats['damage_types']['cold'] += 1
                        if 'Lightning' in mod:
                            stats['damage_types']['lightning'] += 1
                        if 'Chaos' in mod:
                            stats['damage_types']['chaos'] += 1
                        if 'Physical' in mod:
                            stats['damage_types']['physical'] += 1

                # 방어 스탯
                for pattern, stat_type in defensive_patterns:
                    if re.search(pattern, mod, re.IGNORECASE):
                        stats['defensive'][stat_type] += 1

                # 유틸리티 스탯
                for pattern, stat_type in utility_patterns:
                    if re.search(pattern, mod, re.IGNORECASE):
                        stats['utility'][stat_type] += 1

                # 컨버전 감지
                for pattern, conv_type in conversion_patterns:
                    match = re.search(pattern, mod, re.IGNORECASE)
                    if match:
                        stats['conversion'].append({
                            'mod': mod,
                            'type': conv_type,
                            'value': match.group(1),
                            'from': match.group(2) if conv_type != 'phys_to_ele' else 'Physical',
                            'to': match.group(2) if conv_type == 'phys_to_ele' else match.group(3)
                        })

                # 젬 레벨 감지
                for pattern, gem_type in gem_patterns:
                    match = re.search(pattern, mod, re.IGNORECASE)
                    if match:
                        stats['gem_level'].append({
                            'mod': mod,
                            'level': match.group(1),
                            'type': match.group(2),
                            'category': gem_type
                        })

        return stats

    def get_build_keywords(self) -> Set[str]:
        """빌드에 필요한 핵심 키워드 추출 (필터 생성용)"""
        stats = self.extract_build_stats()
        keywords = set()

        # 상위 공격 스탯 (3회 이상 등장)
        for stat, count in stats['offensive'].most_common():
            if count >= 2:
                keywords.add(stat)

        # 상위 방어 스탯
        for stat, count in stats['defensive'].most_common():
            if count >= 2:
                keywords.add(stat)

        # 주요 데미지 타입
        if stats['damage_types']:
            main_type = stats['damage_types'].most_common(1)[0][0]
            keywords.add(f'{main_type}_damage')

        # 컨버전 있으면 추가
        if stats['conversion']:
            keywords.add('conversion')
            for conv in stats['conversion']:
                keywords.add(f"convert_to_{conv['to'].lower()}")

        # 젬 레벨 타입
        for gem_info in stats['gem_level']:
            keywords.add(f"gem_{gem_info['type'].lower()}")

        return keywords

    def get_primary_damage_type(self) -> Optional[str]:
        """빌드의 주요 데미지 타입 감지"""
        stats = self.extract_build_stats()

        if not stats['damage_types']:
            return None

        # 가장 많이 등장하는 데미지 타입
        return stats['damage_types'].most_common(1)[0][0]

    def get_conversion_summary(self) -> List[Dict]:
        """속성 변환 요약"""
        stats = self.extract_build_stats()
        return stats['conversion']

    def analyze_build_for_filter(self) -> Dict:
        """필터 생성을 위한 빌드 분석 요약"""
        stats = self.extract_build_stats()
        keywords = self.get_build_keywords()

        # 빌드 타입 추정
        build_type = 'unknown'
        if stats['offensive'].get('spell_damage', 0) > stats['offensive'].get('physical_damage', 0):
            build_type = 'spell'
        elif stats['offensive'].get('dot_damage', 0) > 2:
            build_type = 'dot'
        elif stats['offensive'].get('attack_speed', 0) > stats['offensive'].get('cast_speed', 0):
            build_type = 'attack'
        else:
            build_type = 'spell'

        # 주요 데미지 타입
        primary_element = self.get_primary_damage_type()

        return {
            'build_type': build_type,
            'primary_element': primary_element,
            'keywords': list(keywords),
            'conversions': stats['conversion'],
            'gem_levels': stats['gem_level'],
            'offensive_focus': dict(stats['offensive'].most_common(5)),
            'defensive_focus': dict(stats['defensive'].most_common(5)),
            'all_mods': stats['all_mods']
        }


def test_parser():
    """파서 테스트"""
    import os

    print("=" * 80)
    print("POB Item Parser Test")
    print("=" * 80)
    print()

    # 테스트 파일 찾기
    test_files = [
        "temp_pob.xml",
        "temp_pob2.xml",
        "temp_pob3.xml",
        "temp_pob4.xml"
    ]

    script_dir = os.path.dirname(os.path.abspath(__file__))

    for test_file in test_files:
        file_path = os.path.join(script_dir, test_file)
        if os.path.exists(file_path):
            print(f"\n파싱 중: {test_file}")
            print("-" * 80)

            parser = POBItemParser()
            items = parser.parse_xml(file_path)

            print(f"총 아이템 수: {len(items)}")

            # 장착된 아이템 출력
            equipped = parser.get_equipped_items()
            print(f"\n장착된 아이템 ({len(equipped)}개):")

            for item in equipped:
                print(f"\n  [{item.slot}] {item.name or item.base_type}")
                print(f"    Rarity: {item.rarity}")

                if item.sockets:
                    print(f"    Sockets: {item.sockets} ({item.socket_count}S, {item.link_count}L)")

                # 영향력
                influences = []
                if item.shaper: influences.append("Shaper")
                if item.elder: influences.append("Elder")
                if item.crusader: influences.append("Crusader")
                if item.redeemer: influences.append("Redeemer")
                if item.hunter: influences.append("Hunter")
                if item.warlord: influences.append("Warlord")
                if item.synthesised: influences.append("Synthesised")
                if item.fractured: influences.append("Fractured")

                if influences:
                    print(f"    Influence: {', '.join(influences)}")

                if item.corrupted:
                    print(f"    Corrupted: Yes")

                if item.foulborn:
                    print(f"    Foulborn: Yes")

                if item.keystone:
                    print(f"    Keystone: {item.keystone}")

                # Trade 필터 생성
                filters = parser.generate_trade_filters(item)
                if any([filters["influence"], filters["links"], filters["corrupted"], filters["foulborn"], filters["keystone"]]):
                    print(f"    Trade Filters: {filters}")

            # 빌드 분석 출력
            print("\n" + "=" * 80)
            print("빌드 스탯 분석")
            print("=" * 80)

            analysis = parser.analyze_build_for_filter()

            print(f"\n빌드 타입: {analysis['build_type']}")
            print(f"주요 속성: {analysis['primary_element']}")
            print(f"\n공격 스탯: {analysis['offensive_focus']}")
            print(f"방어 스탯: {analysis['defensive_focus']}")

            if analysis['conversions']:
                print(f"\n속성 변환:")
                for conv in analysis['conversions']:
                    print(f"  - {conv['value']}% {conv['from']} -> {conv['to']}")

            if analysis['gem_levels']:
                print(f"\n젬 레벨 증가:")
                for gem in analysis['gem_levels']:
                    print(f"  - +{gem['level']} to {gem['type']} Gems")

            print(f"\n필터 키워드: {analysis['keywords']}")

            break  # 첫 번째 파일만 테스트
    else:
        print("테스트 파일을 찾을 수 없습니다.")


if __name__ == '__main__':
    test_parser()
