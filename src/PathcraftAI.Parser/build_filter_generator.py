#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Filter Generator
- POB 1개 입력 → 3단계 필터 자동 생성
- poe.ninja 저가 유니크 추천
- 젬 세팅 링크별 분리
"""

import urllib.request
import base64
import zlib
import xml.etree.ElementTree as ET
import re
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


class BuildFilterGenerator:
    def __init__(self):
        self.game_data_dir = Path(__file__).parent / "game_data"
        self.data_dir = Path(__file__).parent / "data"
        self.cheap_uniques = {}  # slot -> list of cheap uniques
        self.pob_data = None
        self.transition_patterns = []  # 빌드 트랜지션 패턴
        self.leveling_skills = []  # 현재 빌드의 레벨링 스킬들

    def load_transition_patterns(self):
        """build_transition_patterns.json 로드"""
        filepath = self.data_dir / "build_transition_patterns.json"
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.transition_patterns = data.get('patterns', [])
                print(f"[INFO] 트랜지션 패턴 {len(self.transition_patterns)}개 로드됨")
        else:
            print(f"[WARN] {filepath} 파일을 찾을 수 없음")

    def find_leveling_skills(self, final_skill: str, ascendancy: str = None) -> List[str]:
        """파이널 스킬에 맞는 레벨링 스킬들 찾기"""
        if not self.transition_patterns:
            self.load_transition_patterns()

        leveling_skills = []

        for pattern in self.transition_patterns:
            if pattern.get('final_skill', '').lower() == final_skill.lower():
                # 아센던시가 일치하거나 None인 패턴
                pattern_asc = pattern.get('ascendancy')
                if pattern_asc is None or ascendancy is None or pattern_asc.lower() == ascendancy.lower():
                    skill = pattern.get('leveling_skill')
                    if skill and skill not in leveling_skills:
                        leveling_skills.append(skill)

        return leveling_skills

    def get_leveling_phases(self, final_skill: str, ascendancy: str = None) -> List[Dict]:
        """파이널 스킬에 맞는 레벨링 페이즈 정보 가져오기"""
        if not self.transition_patterns:
            self.load_transition_patterns()

        for pattern in self.transition_patterns:
            if pattern.get('final_skill', '').lower() == final_skill.lower():
                pattern_asc = pattern.get('ascendancy')
                if pattern_asc is None or ascendancy is None or pattern_asc.lower() == ascendancy.lower():
                    phases = pattern.get('leveling_phases', [])
                    if phases:
                        return phases

        return []

    def get_utility_gems(self, final_skill: str, ascendancy: str = None) -> Dict:
        """파이널 스킬에 맞는 유틸리티 젬 정보 가져오기"""
        if not self.transition_patterns:
            self.load_transition_patterns()

        for pattern in self.transition_patterns:
            if pattern.get('final_skill', '').lower() == final_skill.lower():
                pattern_asc = pattern.get('ascendancy')
                if pattern_asc is None or ascendancy is None or pattern_asc.lower() == ascendancy.lower():
                    utility = pattern.get('utility_gems', {})
                    if utility:
                        return utility

        return {}

    def get_leveling_items_for_skill(self, leveling_skill: str) -> Dict[str, List[str]]:
        """레벨링 스킬에 맞는 추천 아이템 (카오스 DoT 전용)"""

        # 카오스 DoT 레벨링 스킬용 유니크 추천
        chaos_dot_skills = {'Soulrend', 'Bane', 'Essence Drain', 'Contagion', 'Blight', 'Death Aura'}

        if leveling_skill in chaos_dot_skills:
            return {
                'weapon': [
                    'Obliteration',  # 카오스 피해
                    'Cane of Kulemak',  # DoT
                    'Ming\'s Heart',  # 카오스 피해
                    'Breath of the Council',  # 카오스 피해
                ],
                'body_armour': [
                    'Cloak of Flame',  # 저가
                    'The Covenant',  # 카오스 스킬
                    'Carcass Jack',  # AoE
                    'Dendrobate',  # 독/카오스
                ],
                'helmet': [
                    'Rime Gaze',  # 저가
                    'Crown of the Inward Eye',
                    'Vertex',
                ],
                'gloves': [
                    'Doedre\'s Tenure',  # 주문 피해
                    'Allelopathy',  # Blight
                    'Asenath\'s Gentle Touch',  # 폭발
                ],
                'boots': [
                    'Windscream',  # 저주 추가
                    'Sin Trek',  # ES
                    'Rainbowstride',  # ES/스펠
                ],
                'amulet': [
                    'Impresence',  # 카오스
                    'Eye of Chayula',  # 스턴 면역
                    'Aul\'s Uprising',
                ],
                'ring': [
                    'Ming\'s Heart',  # 카오스 피해
                    'Doedre\'s Damning',  # 저주 추가
                ],
                'belt': [
                    'Bated Breath',  # ES 리젠
                    'Darkness Enthroned',  # 어비스 주얼
                ],
            }

        # 기본값 (빈 딕셔너리)
        return {}

    def filter_cheap_uniques_by_skill(self, skill_items: Dict[str, List[str]]) -> Dict[str, List[Dict]]:
        """스킬별 추천 아이템을 poe.ninja 가격 데이터와 매칭"""
        result = {}

        for slot, recommended_names in skill_items.items():
            if slot not in self.cheap_uniques:
                continue

            matched = []
            for item in self.cheap_uniques[slot]:
                # 추천 아이템 중 poe.ninja에 있는 저가 아이템만
                if item['name'] in recommended_names:
                    matched.append(item)

            # 추천 아이템 중 저가가 아닌 것도 이름만 추가 (가격 정보 없이)
            for name in recommended_names:
                if not any(m['name'] == name for m in matched):
                    # 가격 정보 없이 추천 (높은 가격으로 표시)
                    matched.append({'name': name, 'price': 999, 'slot': slot})

            if matched:
                # 가격순 정렬
                matched.sort(key=lambda x: x['price'])
                result[slot] = matched

        return result

    def get_leveling_base_types(self) -> List[str]:
        """레벨링용 베이스 타입 (DoT 빌드는 ES 기반)"""
        build_type = self.detect_build_type()

        if build_type == 'dot':
            # 카오스 DoT는 주로 ES 기반
            return [
                # ES 방어구
                'Vaal Regalia', 'Occultist\'s Vestment', 'Widowsilk Robe',
                'Sorcerer Boots', 'Arcanist Slippers',
                'Sorcerer Gloves', 'Arcanist Gloves',
                'Hubris Circlet', 'Mind Cage',
                # 완드 (스펠 피해)
                'Prophecy Wand', 'Opal Wand', 'Tornado Wand',
                # ES 방패
                'Titanium Spirit Shield', 'Harmonic Spirit Shield',
            ]
        elif build_type == 'spell':
            return [
                # 스펠 기반 방어구
                'Vaal Regalia', 'Saintly Chainmail',
                'Sorcerer Boots', 'Two-Toned Boots',
                'Sorcerer Gloves', 'Fingerless Silk Gloves',
                'Hubris Circlet', 'Royal Burgonet',
                # 완드/셉터
                'Prophecy Wand', 'Opal Sceptre',
            ]
        else:  # attack
            return self.pob_data.get('base_types', [])

    def load_cheap_uniques(self, max_price: float = 5.0):
        """poe.ninja에서 저가 유니크 로드 (슬롯별 분류)"""

        # baseType 기반 슬롯 매핑
        base_type_keywords = {
            'body_armour': ['Robe', 'Vest', 'Plate', 'Garb', 'Armour', 'Coat', 'Jacket', 'Regalia', 'Vestment', 'Brigandine', 'Doublet', 'Tunic', 'Lamellar', 'Hauberk', 'Chainmail', 'Wyrmscale', 'Dragonscale'],
            'boots': ['Boots', 'Greaves', 'Shoes', 'Slippers'],
            'gloves': ['Gloves', 'Gauntlets', 'Mitts', 'Wraps'],
            'helmet': ['Helm', 'Cap', 'Hood', 'Mask', 'Circlet', 'Crown', 'Burgonet', 'Casque', 'Bascinet', 'Sallet', 'Visage', 'Cage', 'Tricorne', 'Hat', 'Pelt'],
            'shield': ['Shield', 'Buckler', 'Kite', 'Tower'],
        }

        weapon_keywords = ['Wand', 'Sceptre', 'Dagger', 'Claw', 'Sword', 'Axe', 'Mace', 'Staff', 'Bow', 'Foil', 'Rapier', 'Blade']
        accessory_keywords = {'Ring': 'ring', 'Amulet': 'amulet', 'Belt': 'belt'}

        categories = ['unique_armours', 'unique_weapons', 'unique_accessories', 'unique_flasks', 'unique_jewels']

        for category in categories:
            filepath = self.game_data_dir / f"{category}.json"
            if not filepath.exists():
                continue

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for item in data.get('items', []):
                price = item.get('chaosValue', 999)
                if price > max_price:
                    continue

                base_type = item.get('baseType', '')
                name = item.get('name', '')
                slot = None

                # 방어구 슬롯 결정
                if category == 'unique_armours':
                    for slot_name, keywords in base_type_keywords.items():
                        if any(kw in base_type for kw in keywords):
                            slot = slot_name
                            break

                # 무기
                elif category == 'unique_weapons':
                    if any(kw in base_type for kw in weapon_keywords):
                        slot = 'weapon'

                # 악세서리
                elif category == 'unique_accessories':
                    for kw, slot_name in accessory_keywords.items():
                        if kw in base_type:
                            slot = slot_name
                            break

                # 플라스크
                elif category == 'unique_flasks':
                    slot = 'flask'

                # 주얼
                elif category == 'unique_jewels':
                    slot = 'jewel'

                if not slot:
                    continue

                if slot not in self.cheap_uniques:
                    self.cheap_uniques[slot] = []

                self.cheap_uniques[slot].append({
                    'name': name,
                    'base_type': base_type,
                    'price': price,
                    'links': item.get('links', 0),
                })

        # 가격순 정렬
        for slot in self.cheap_uniques:
            self.cheap_uniques[slot].sort(key=lambda x: x['price'])

        return self.cheap_uniques

    def get_leveling_uniques(self) -> Dict[str, List[Dict]]:
        """레벨링용 저가 유니크 추천 (슬롯별 상위 3개)"""
        recommendations = {}

        for slot, items in self.cheap_uniques.items():
            # 상위 3개만
            recommendations[slot] = items[:3]

        return recommendations

    def fetch_pob(self, pob_input: str) -> str:
        """POB 코드 또는 링크에서 XML 추출"""

        # 로컬 XML 파일인 경우
        if pob_input.endswith('.xml') and Path(pob_input).exists():
            with open(pob_input, 'r', encoding='utf-8') as f:
                return f.read()

        # pobb.in URL인 경우
        if 'pobb.in' in pob_input:
            # URL에서 ID 추출
            match = re.search(r'pobb\.in/([a-zA-Z0-9_-]+)', pob_input)
            if match:
                pob_id = match.group(1)
                url = f'https://pobb.in/{pob_id}/raw'
            else:
                raise ValueError(f"Invalid pobb.in URL: {pob_input}")
        # pastebin URL인 경우
        elif 'pastebin.com' in pob_input:
            match = re.search(r'pastebin\.com/(\w+)', pob_input)
            if match:
                paste_id = match.group(1)
                url = f'https://pastebin.com/raw/{paste_id}'
            else:
                raise ValueError(f"Invalid pastebin URL: {pob_input}")
        # POB 코드 직접 입력인 경우
        else:
            # Base64 디코딩 시도
            try:
                decoded = base64.urlsafe_b64decode(pob_input)
                return zlib.decompress(decoded).decode('utf-8')
            except:
                raise ValueError("Invalid POB code or URL")

        # URL에서 데이터 가져오기
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()

        # Base64 디코딩 및 압축 해제
        decoded = base64.urlsafe_b64decode(data)
        return zlib.decompress(decoded).decode('utf-8')

    def parse_pob(self, xml_data: str) -> Dict:
        """POB XML 파싱 - 빌드 정보 추출"""
        root = ET.fromstring(xml_data)

        result = {
            'class': '',
            'ascendancy': '',
            'level': 0,
            'main_skill': '',
            'skills': [],  # 스킬 그룹별 젬 목록
            'items': [],   # 장착 아이템
            'uniques': [],      # 유니크 이름
            'unique_bases': [], # 유니크 베이스 타입
            'base_types': [],
        }

        # Build 기본 정보
        build = root.find('Build')
        if build is not None:
            result['class'] = build.get('className', '')
            result['ascendancy'] = build.get('ascendClassName', '')
            result['level'] = int(build.get('level', '1'))
            main_group = int(build.get('mainSocketGroup', '1'))
        else:
            main_group = 1

        # 스킬 그룹 파싱
        skills_section = root.find('.//Skills')
        if skills_section is not None:
            group_idx = 0
            for skill_set in skills_section.findall('SkillSet'):
                for skill in skill_set.findall('Skill'):
                    if skill.get('enabled', 'true') != 'true':
                        continue

                    group_idx += 1
                    gems = []

                    for gem in skill.findall('Gem'):
                        gem_name = gem.get('nameSpec', gem.get('skillId', ''))
                        gem_level = int(gem.get('level', '1'))
                        gem_quality = int(gem.get('quality', '0'))

                        if gem_name:
                            gems.append({
                                'name': gem_name,
                                'level': gem_level,
                                'quality': gem_quality,
                            })

                    if gems:
                        skill_data = {
                            'group': group_idx,
                            'label': skill.get('label', '') or skill.get('slot', ''),
                            'gems': gems,
                            'is_main': (group_idx == main_group),
                        }
                        result['skills'].append(skill_data)

        # 메인 스킬 찾기 - 저주/오라가 아닌 실제 데미지 스킬
        result['main_skill'] = self._find_main_damage_skill(result['skills'], main_group)

        # 아이템 파싱
        items_elem = root.find('Items')
        if items_elem is not None:
            for item in items_elem.findall('Item'):
                item_text = item.text or ''

                # Rarity 파싱
                rarity_match = re.search(r'Rarity: (\w+)', item_text)
                if not rarity_match:
                    continue
                rarity = rarity_match.group(1)

                # 아이템 이름/베이스 타입 추출
                lines = [l.strip() for l in item_text.strip().split('\n') if l.strip()]
                unique_name = None
                base_type = None

                for i, line in enumerate(lines):
                    if line.startswith('Rarity:'):
                        # UNIQUE와 RARE 모두 이름 → 베이스 타입 구조
                        if rarity in ['UNIQUE', 'RARE'] and i + 2 < len(lines):
                            unique_name = lines[i + 1]  # 아이템 이름
                            base_type = lines[i + 2]    # 베이스 타입
                        elif i + 1 < len(lines):
                            base_type = lines[i + 1]
                        break

                if base_type:
                    # 접두사 제거
                    base_type = re.sub(r'^(Superior |Synthesised |Fractured )', '', base_type)

                    # Flask 베이스 타입 정리
                    if 'Flask' in base_type:
                        base_type = self._extract_flask_base(base_type)

                    # Two-Stone Ring 정규화
                    if 'Two-Stone Ring' in base_type:
                        base_type = 'Two-Stone Ring'

                    if rarity == 'UNIQUE' and unique_name:
                        result['uniques'].append(unique_name)
                        result['unique_bases'].append(base_type)
                    result['base_types'].append(base_type)

        self.pob_data = result
        return result

    def _extract_flask_base(self, name: str) -> str:
        """Flask 이름에서 베이스 타입 추출"""
        flask_bases = [
            "Divine Life Flask", "Eternal Life Flask", "Hallowed Life Flask",
            "Divine Mana Flask", "Eternal Mana Flask",
            "Quicksilver Flask", "Granite Flask", "Jade Flask", "Quartz Flask",
            "Diamond Flask", "Basalt Flask", "Silver Flask", "Gold Flask",
        ]

        for base in flask_bases:
            if base in name:
                return base
        return name

    def _find_main_damage_skill(self, skills: List[Dict], main_group: int) -> str:
        """실제 데미지 스킬 찾기 (저주/오라 제외)"""

        # 저주 젬 목록
        curse_gems = {
            'Punishment', 'Despair', 'Temporal Chains', 'Enfeeble', 'Vulnerability',
            'Elemental Weakness', 'Flammability', 'Frostbite', 'Conductivity',
            'Assassin\'s Mark', 'Warlord\'s Mark', 'Poacher\'s Mark', 'Sniper\'s Mark',
        }

        # 오라/버프 젬 목록 (데미지 오라 제외)
        aura_gems = {
            'Arrogance', 'Blasphemy', 'Awakened Blasphemy', 'Herald of Ash',
            'Herald of Ice', 'Herald of Thunder', 'Herald of Purity', 'Herald of Agony',
            'Hatred', 'Wrath', 'Anger', 'Grace', 'Determination', 'Discipline',
            'Clarity', 'Vitality', 'Purity of Fire', 'Purity of Ice', 'Purity of Lightning',
            'Zealotry', 'Malevolence', 'Pride', 'Blood and Sand', 'Flesh and Stone',
            'Dread Banner', 'War Banner', 'Defiance Banner', 'Petrified Blood',
            'Tempest Shield', 'Arctic Armour', 'Haste', 'Aspect of the Spider',
        }

        # 이동기/유틸리티 스킬
        utility_gems = {
            'Frostblink', 'Flame Dash', 'Shield Charge', 'Leap Slam', 'Whirling Blades',
            'Dash', 'Smoke Mine', 'Phase Run', 'Withering Step',
        }

        # 서포트 젬 키워드
        support_keywords = ['Support']

        # 특수 케이스: Death Aura, Righteous Fire 등 (아이템 스킬)
        special_damage_skills = {'Death Aura', 'Righteous Fire', 'Scorching Ray'}

        # 1. 특수 데미지 스킬 먼저 확인
        for skill in skills:
            gems = skill.get('gems', [])
            if gems:
                main_gem = gems[0]['name']
                if main_gem in special_damage_skills:
                    return main_gem

        # 2. label이 "Body Armour"나 특정 아이템인 스킬 확인
        for skill in skills:
            label = skill.get('label', '')
            gems = skill.get('gems', [])
            if label == 'Body Armour' and gems:
                main_gem = gems[0]['name']
                if main_gem not in curse_gems and main_gem not in aura_gems:
                    return main_gem

        # 3. 가장 많은 서포트 젬이 연결된 스킬 그룹 찾기
        best_skill = None
        best_support_count = 0

        for skill in skills:
            gems = skill.get('gems', [])
            if not gems:
                continue

            # 첫 번째 젬 (메인 스킬)
            main_gem = gems[0]['name']

            # 저주/오라/유틸리티면 스킵
            if main_gem in curse_gems or main_gem in aura_gems or main_gem in utility_gems:
                continue

            # 서포트 젬이면 스킵
            if any(kw in main_gem for kw in support_keywords):
                continue

            # 서포트 젬 개수 세기
            support_count = sum(1 for g in gems[1:]
                              if any(kw in g['name'] for kw in support_keywords))

            # 가장 많은 서포트가 연결된 스킬 선택
            if support_count > best_support_count:
                best_support_count = support_count
                best_skill = main_gem

        # 찾지 못하면 mainSocketGroup의 첫 젬 반환
        if not best_skill:
            for skill in skills:
                if skill.get('is_main') and skill.get('gems'):
                    return skill['gems'][0]['name']
            return ''

        return best_skill

    def get_gem_setup_by_links(self, skill_group: Dict, links: int) -> List[str]:
        """스킬 그룹에서 링크 수에 맞는 젬 세팅 추출"""
        gems = skill_group.get('gems', [])
        return [g['name'] for g in gems[:links]]

    def generate_gem_recommendations(self) -> Dict:
        """메인 스킬의 링크별 젬 세팅 추천"""
        if not self.pob_data:
            return {}

        main_skill_name = self.pob_data.get('main_skill', '')

        # 메인 스킬 그룹 찾기 - 실제 데미지 스킬 기준
        main_skill = None

        # 1. 먼저 메인 스킬 이름으로 찾기
        for skill in self.pob_data.get('skills', []):
            gems = skill.get('gems', [])
            if gems and gems[0]['name'] == main_skill_name:
                main_skill = skill
                break

        # 2. 못 찾으면 is_main 플래그로 찾기
        if not main_skill:
            for skill in self.pob_data.get('skills', []):
                if skill.get('is_main'):
                    main_skill = skill
                    break

        if not main_skill:
            return {}

        gems = main_skill.get('gems', [])
        gem_names = [g['name'] for g in gems]

        return {
            '4-link': gem_names[:4] if len(gems) >= 4 else gem_names,
            '5-link': gem_names[:5] if len(gems) >= 5 else gem_names,
            '6-link': gem_names[:6] if len(gems) >= 6 else gem_names,
        }

    def generate_three_stage_items(self) -> Dict:
        """엔드게임 POB에서 3단계 아이템 목록 생성"""
        if not self.pob_data:
            return {}

        # 트랜지션 패턴 로드
        self.load_transition_patterns()

        # 메인 스킬과 아센던시
        main_skill = self.pob_data.get('main_skill', '')
        ascendancy = self.pob_data.get('ascendancy', '')

        # 레벨링 스킬 찾기
        self.leveling_skills = self.find_leveling_skills(main_skill, ascendancy)

        # 레벨링 페이즈 정보 가져오기
        self.leveling_phases = self.get_leveling_phases(main_skill, ascendancy)
        self.utility_gems = self.get_utility_gems(main_skill, ascendancy)

        if self.leveling_skills:
            print(f"[INFO] 레벨링 스킬 추천: {', '.join(self.leveling_skills)}")
        else:
            print(f"[INFO] {main_skill}에 대한 레벨링 패턴이 없음, 동일 스킬 사용")
            self.leveling_skills = [main_skill]

        if self.leveling_phases:
            print(f"[INFO] 레벨링 페이즈 {len(self.leveling_phases)}개 로드됨")
            for phase in self.leveling_phases:
                print(f"  - {phase.get('level_range')}: {phase.get('skill')} ({phase.get('socket_colors')})")

        # 레벨링 유니크 로드 - 빌드 타입 기반
        self.load_cheap_uniques(max_price=5.0)

        # 트랜지션 데이터 기반 레벨링 추천 아이템
        if self.leveling_skills:
            primary_leveling_skill = self.leveling_skills[0]
            skill_specific_items = self.get_leveling_items_for_skill(primary_leveling_skill)

            if skill_specific_items:
                print(f"[INFO] {primary_leveling_skill} 전용 유니크 추천 활성화")
                leveling_uniques = self.filter_cheap_uniques_by_skill(skill_specific_items)
            else:
                leveling_uniques = self.get_leveling_uniques()
        else:
            leveling_uniques = self.get_leveling_uniques()

        # 레벨링용 베이스 타입 (엔드게임과 다를 수 있음)
        leveling_base_types = self.get_leveling_base_types()

        result = {
            'leveling': {
                'uniques': [],
                'base_types': leveling_base_types,
                'recommended_uniques': leveling_uniques,
                'leveling_skills': self.leveling_skills,
                'leveling_phases': self.leveling_phases,
                'utility_gems': self.utility_gems,
                'gem_setup': self.get_gem_setup_by_links(
                    next((s for s in self.pob_data.get('skills', []) if s.get('is_main')), {}),
                    4
                ),
            },
            'early_map': {
                'uniques': self.pob_data.get('uniques', []),           # 엔드게임과 동일 유니크
                'unique_bases': self.pob_data.get('unique_bases', []), # 베이스 타입 (필터용)
                'base_types': self.pob_data.get('base_types', []),
                'gem_setup': self.get_gem_setup_by_links(
                    next((s for s in self.pob_data.get('skills', []) if s.get('is_main')), {}),
                    5
                ),
            },
            'endgame': {
                'uniques': self.pob_data.get('uniques', []),           # 이름 (표시용)
                'unique_bases': self.pob_data.get('unique_bases', []), # 베이스 (필터용)
                'base_types': self.pob_data.get('base_types', []),
                'gem_setup': self.get_gem_setup_by_links(
                    next((s for s in self.pob_data.get('skills', []) if s.get('is_main')), {}),
                    6
                ),
            },
        }

        # 초반맵용 유니크 - poe.ninja에서 5-50c 사이 유니크 중 빌드에 맞는 것
        self.load_cheap_uniques(max_price=50.0)
        mid_price_uniques = []
        for slot, items in self.cheap_uniques.items():
            for item in items:
                if 5 <= item['price'] <= 50:
                    mid_price_uniques.append(item['name'])

        # 엔드게임 유니크와 겹치는 것만 추천
        endgame_uniques = set(self.pob_data.get('uniques', []))
        result['early_map']['uniques'] = [u for u in mid_price_uniques if u in endgame_uniques][:5]

        return result

    def load_neversink_base(self) -> Optional[str]:
        """NeverSink 베이스 필터 로드"""
        possible_paths = [
            Path(r"d:\Pathcraft-AI\Leveling 3.27 filter.filter"),
            Path(__file__).parent.parent.parent / "Leveling 3.27 filter.filter",
        ]

        for path in possible_paths:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
        return None

    def detect_build_type(self) -> str:
        """빌드 타입 감지: 'attack', 'spell', 'dot' 중 하나 반환"""
        if not self.pob_data:
            return 'spell'  # 기본값

        main_skill = self.pob_data.get('main_skill', '')
        ascendancy = self.pob_data.get('ascendancy', '')

        # DoT 빌드 (지속 피해)
        dot_skills = {
            'Death Aura', 'Righteous Fire', 'Scorching Ray', 'Blight',
            'Essence Drain', 'Contagion', 'Soulrend', 'Bane', 'Vortex',
            'Cold Snap', 'Wintertide Brand', 'Caustic Arrow', 'Toxic Rain',
            'Poison', 'Bleed', 'Ignite', 'Burning Arrow', 'Venom Gyre',
            'Creeping Frost', 'Searing Bond', 'Fire Trap',
        }

        # 공격 스킬 (물리/원소 공격)
        attack_skills = {
            'Cyclone', 'Blade Flurry', 'Double Strike', 'Lacerate', 'Cleave',
            'Ground Slam', 'Earthquake', 'Ice Crash', 'Molten Strike',
            'Spectral Throw', 'Lightning Strike', 'Frost Blades', 'Wild Strike',
            'Smite', 'Consecrated Path', 'Tectonic Slam', 'Sunder', 'Reave',
            'Blade Storm', 'Perforate', 'Bladestorm', 'Flicker Strike',
            'Viper Strike', 'Cobra Lash', 'Pestilent Strike', 'Puncture',
            'Split Arrow', 'Rain of Arrows', 'Barrage', 'Tornado Shot',
            'Ice Shot', 'Lightning Arrow', 'Galvanic Arrow', 'Scourge Arrow',
            'Shrapnel Ballista', 'Artillery Ballista', 'Siege Ballista',
            'Kinetic Blast', 'Power Siphon', 'Ethereal Knives', 'Spectral Helix',
            'Shield Crush', 'Shield Charge', 'Leap Slam', 'Static Strike',
            'Infernal Blow', 'Heavy Strike', 'Glacial Hammer', 'Ancestral Warchief',
            'Ancestral Protector', 'Earthshatter', 'General\'s Cry', 'Rage Vortex',
            'Boneshatter', 'Steel Skills', 'Lancing Steel', 'Shattering Steel',
            'Splitting Steel', 'Charged Dash', 'Consecrated Path', 'Sweep',
        }

        # 주문 스킬
        spell_skills = {
            'Arc', 'Ball Lightning', 'Spark', 'Storm Brand', 'Orb of Storms',
            'Freezing Pulse', 'Ice Spear', 'Glacial Cascade', 'Frostbolt',
            'Fireball', 'Magma Orb', 'Rolling Magma', 'Flame Surge', 'Flameblast',
            'Incinerate', 'Wave of Conviction', 'Purifying Flame', 'Divine Ire',
            'Storm Call', 'Lightning Tendrils', 'Crackling Lance', 'Penance Brand',
            'Armageddon Brand', 'Blade Vortex', 'Bladefall', 'Ethereal Knives',
            'Exsanguinate', 'Reap', 'Dark Pact', 'Forbidden Rite', 'Eye of Winter',
            'Winter Orb', 'Ice Nova', 'Vaal Ice Nova', 'Detonate Dead', 'Cremation',
            'Volatile Dead', 'Firestorm', 'Meteor', 'Blazing Salvo', 'Flame Wall',
            'Summon Skeletons', 'Raise Zombie', 'Summon Raging Spirit', 'Animate Weapon',
            'Summon Phantasm', 'Summon Holy Relic', 'Absolution', 'Dominating Blow',
        }

        # 1. 메인 스킬로 판단
        if main_skill in dot_skills:
            return 'dot'
        elif main_skill in attack_skills:
            return 'attack'
        elif main_skill in spell_skills:
            return 'spell'

        # 2. 아센던시로 추가 판단
        melee_ascendancies = {'Champion', 'Gladiator', 'Slayer', 'Berserker', 'Juggernaut', 'Chieftain'}
        caster_ascendancies = {'Occultist', 'Elementalist', 'Necromancer', 'Hierophant', 'Inquisitor', 'Trickster'}

        if ascendancy in melee_ascendancies:
            return 'attack'
        elif ascendancy in caster_ascendancies:
            return 'spell'

        return 'spell'  # 기본값

    def modify_neversink_for_build(self, neversink_content: str) -> str:
        """빌드 타입에 맞게 NeverSink 필터 수정"""
        build_type = self.detect_build_type()

        if build_type == 'attack':
            # 공격 빌드면 그대로 사용
            return neversink_content

        # 주문/DoT 빌드: 근접 무기 레벨링 규칙 숨기기
        lines = neversink_content.split('\n')
        result = []
        i = 0

        # 숨길 레벨링 무기 베이스 타입
        melee_weapon_bases = {
            'Rusted Sword', 'Rusted Hatchet', 'Rusted Spike', 'Boarding Axe',
            'Whalebone Rapier', 'Jagged Foil', 'Tomahawk', 'Elegant Foil',
            'Serrated Foil', 'Fancy Foil', 'Siege Axe', 'Spiraled Foil',
            'Butcher Axe', 'Vaal Axe', 'Despot Axe', 'Void Axe', 'Infernal Axe',
            'Apex Cleaver', 'Headsman Axe', 'Reaver Axe', 'Ezomyte Axe',
            'Vaal Hatchet', 'Royal Axe', 'Sundering Axe', 'Cleaver',
        }

        # DoT 빌드는 셉터도 숨김 (셉터는 원소 피해 - 카오스 DoT에 안맞음)
        sceptre_bases = {
            'Driftwood Sceptre', 'Darkwood Sceptre', 'Bronze Sceptre', 'Quartz Sceptre',
            'Iron Sceptre', 'Ochre Sceptre', 'Ritual Sceptre', 'Shadow Sceptre',
            'Grinning Fetish', 'Horned Sceptre', 'Sekhem', 'Crystal Sceptre',
            'Lead Sceptre', 'Blood Sceptre', 'Royal Sceptre', 'Abyssal Sceptre',
            'Stag Sceptre', 'Karui Sceptre', 'Tyrant\'s Sekhem', 'Opal Sceptre',
            'Platinum Sceptre', 'Vaal Sceptre', 'Carnal Sceptre', 'Void Sceptre',
            'Sambar Sceptre',
        }

        # DoT 빌드면 셉터도 숨김 대상에 추가
        if build_type == 'dot':
            melee_weapon_bases = melee_weapon_bases.union(sceptre_bases)

        while i < len(lines):
            line = lines[i]

            # Show 규칙 시작 감지
            if line.strip().startswith('Show'):
                # 이 규칙 블록을 수집
                block = [line]
                i += 1

                while i < len(lines):
                    current = lines[i]
                    # 빈 줄이나 다음 Show/Hide 만나면 블록 끝
                    if current.strip() == '' or current.strip().startswith('Show') or current.strip().startswith('Hide'):
                        break
                    block.append(current)
                    i += 1

                # 블록 내용 분석
                block_text = '\n'.join(block)
                has_melee_weapon = any(base in block_text for base in melee_weapon_bases)
                has_area_level_limit = 'AreaLevel <=' in block_text or 'AreaLevel >= 1' in block_text
                has_white_highlight = 'SetBackgroundColor 255 255 255' in block_text

                # DoT 빌드에서 셉터 Class 규칙 감지 - 레벨링 규칙이면 숨김
                has_sceptre_class = build_type == 'dot' and 'Class' in block_text and 'Sceptre' in block_text
                # Wand만 있는 규칙은 제외 (완드는 DoT에 필요)
                has_only_wand = 'Wand' in block_text and 'Sceptre' not in block_text

                # 레벨링 규칙 여부 (레벨/에어리어 제한 또는 Rarity Magic/Rare)
                is_leveling_rule = has_area_level_limit or ('ItemLevel <=' in block_text) or ('Rarity' in block_text and ('Magic' in block_text or 'Rare' in block_text))

                # 근접 무기/셉터 레벨링 규칙이면 Hide로 변경
                # DoT 빌드에서 셉터는 조건 없이 숨김 (커스텀 색상도 포함)
                should_hide = (has_melee_weapon and has_area_level_limit and has_white_highlight) or (has_sceptre_class and not has_only_wand)
                if should_hide:
                    # Show를 Hide로 변경하고 스타일 제거
                    hide_reason = 'Sceptre' if has_sceptre_class else 'Melee weapon'
                    modified_block = [f'# Hidden: {hide_reason} leveling rule (not for this build)']
                    modified_block.append('Hide')
                    for b_line in block[1:]:
                        # 색상/사운드/이펙트 제거
                        if not any(kw in b_line for kw in ['SetTextColor', 'SetBorderColor', 'SetBackgroundColor',
                                                           'PlayEffect', 'MinimapIcon', 'CustomAlertSound', 'PlayAlertSound']):
                            modified_block.append(b_line)
                    result.extend(modified_block)
                else:
                    result.extend(block)

                # 빈 줄 추가
                result.append('')
            else:
                result.append(line)
                i += 1

        return '\n'.join(result)

    def generate_filter(self, stage: str, uniques: List[str], base_types: List[str],
                       recommended_uniques: Dict = None, leveling_phases: List = None,
                       strictness: int = 1) -> str:
        """필터 파일 생성"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M')

        # 스테이지별 설정
        stage_configs = {
            'leveling': {'name': 'Leveling', 'strictness': 1, 'sound_dir': 'sounds/ko'},
            'early_map': {'name': 'Early Map', 'strictness': 2, 'sound_dir': 'sounds/ko'},
            'endgame': {'name': 'Endgame', 'strictness': 3, 'sound_dir': 'sounds/ko'},
        }

        config = stage_configs.get(stage, stage_configs['leveling'])
        sound_dir = config['sound_dir']

        lines = [
            '#' + '=' * 80,
            '# PathcraftAI Build Filter',
            f'# Stage: {config["name"]}',
            '# Based on NeverSink with POB-specific highlighting',
            '#' + '=' * 80,
            f'# STRICTNESS: {config["strictness"]}',
            f'# GENERATED: {now}',
            f'# Build: {self.pob_data.get("class", "")} / {self.pob_data.get("ascendancy", "")}',
            f'# Main Skill: {self.pob_data.get("main_skill", "")}',
            '#' + '=' * 80,
            '',
            '# ' + '=' * 40,
            '# YOUR BUILD ITEMS - HIGHEST PRIORITY',
            '# (These rules override NeverSink below)',
            '# ' + '=' * 40,
            '',
        ]

        # 추천 저가 유니크 (레벨링 단계만)
        if recommended_uniques and stage == 'leveling':
            rec_names = []
            for slot, items in recommended_uniques.items():
                for item in items[:2]:  # 슬롯당 2개
                    rec_names.append(item['name'])

            if rec_names:
                # 베이스 타입 수집 (유니크는 베이스 타입으로 매칭)
                rec_base_types = []
                for slot, items in recommended_uniques.items():
                    for item in items[:2]:
                        base_type = item.get('base_type')
                        if base_type and base_type not in rec_base_types:
                            rec_base_types.append(base_type)

                if rec_base_types:
                    rec_str = ' '.join(f'"{bt}"' for bt in rec_base_types)
                    lines.extend([
                        '# Recommended Leveling Uniques (cheap from poe.ninja)',
                        'Show',
                        '    Rarity Unique',
                        f'    BaseType {rec_str}',
                        '    SetFontSize 45',
                        '    SetTextColor 0 255 0 255',
                        '    SetBorderColor 0 255 0 255',
                        '    SetBackgroundColor 0 75 0 255',
                        f'    CustomAlertSound "{sound_dir}/build_unique.mp3"',
                        '    PlayEffect Green',
                        '    MinimapIcon 0 Green Star',
                        '',
                    ])

        # 레벨링 중요 아이템 규칙 (레벨링 단계만)
        if stage == 'leveling':
            build_type = self.detect_build_type()

            lines.extend([
                '# ' + '=' * 40,
                '# LEVELING IMPORTANT ITEMS',
                '# ' + '=' * 40,
                '',
            ])

            # 1. 마법 완드 (스펠 피해) - 캐스터 빌드 (셉터는 원소 피해라 카오스에 안맞음)
            if build_type in ['dot', 'spell']:
                lines.extend([
                    '# Magic Wands with Spell Damage - For leveling casters (Chaos DoT)',
                    'Show',
                    '    Rarity Magic',
                    '    Class "Wand"',
                    '    ItemLevel >= 11',
                    '    ItemLevel <= 50',
                    '    SetFontSize 40',
                    '    SetTextColor 136 136 255 255',
                    '    SetBorderColor 136 136 255 255',
                    '    SetBackgroundColor 30 30 80 200',
                    f'    CustomAlertSound "{sound_dir}/mid_value.mp3"',
                    '',
                ])

            # 레벨링 페이즈 기반 소켓 색상 규칙
            if leveling_phases:
                lines.extend([
                    '# Phase-based Socket Color Rules',
                    '',
                ])

                # 역순으로 규칙 생성 (더 구체적인 조건이 먼저 오도록)
                # POE 필터는 위에서 아래로 매칭하므로 더 좁은 범위가 먼저
                for i, phase in enumerate(reversed(leveling_phases)):
                    # 실제 인덱스 계산 (역순이므로)
                    actual_idx = len(leveling_phases) - 1 - i
                    level_range = phase.get('level_range', '')
                    skill = phase.get('skill', '')
                    socket_colors = phase.get('socket_colors', 'BBB')

                    # level_range 파싱 (예: "1-12", "12-28", "28+")
                    if '-' in level_range:
                        parts = level_range.split('-')
                        min_level = int(parts[0])
                        max_level = int(parts[1]) if parts[1] else 999
                    elif '+' in level_range:
                        min_level = int(level_range.replace('+', ''))
                        max_level = 999
                    else:
                        min_level = 1
                        max_level = 999

                    # AreaLevel 변환 (캐릭터 레벨 → 에어리어 레벨 근사)
                    # 일반적으로 AreaLevel은 캐릭터 레벨보다 약간 낮음
                    area_min = max(1, min_level - 2)
                    area_max = min(67, max_level + 5) if max_level < 999 else 67

                    # 3링크 규칙 (소켓 색상이 3자 이상인 경우)
                    if len(socket_colors) >= 3:
                        socket_3link = socket_colors[:3]

                        # AreaLevel 조건 설정 (actual_idx 기반)
                        if actual_idx == 0:  # 첫 번째 페이즈
                            area_condition = f'    AreaLevel <= {area_max}'
                        elif actual_idx == len(leveling_phases) - 1:  # 마지막 페이즈
                            area_condition = f'    AreaLevel >= {area_min}'
                        else:  # 중간 페이즈
                            area_condition = f'    AreaLevel >= {area_min}\n    AreaLevel <= {area_max}'

                        lines.extend([
                            f'# Phase {actual_idx+1}: {skill} ({level_range}) - 3-Link {socket_3link}',
                            'Show',
                            '    LinkedSockets >= 3',
                            f'    SocketGroup "{socket_3link}"',
                            area_condition,
                            '    SetFontSize 38',
                            '    SetTextColor 100 200 200 220',
                            '    SetBorderColor 100 200 200 220',
                            f'    CustomAlertSound "{sound_dir}/mid_value.mp3"',
                            '',
                        ])

                    # 4링크 규칙 (소켓 색상이 4자 이상인 경우)
                    if len(socket_colors) >= 4:
                        socket_4link = socket_colors[:4]

                        # AreaLevel 조건 설정 (actual_idx 기반)
                        if actual_idx == len(leveling_phases) - 1:  # 마지막 페이즈 (메인 스킬)
                            area_condition = f'    AreaLevel >= {area_min}\n    AreaLevel <= 67'
                        else:
                            area_condition = f'    AreaLevel >= {area_min}\n    AreaLevel <= {area_max}'

                        lines.extend([
                            f'# Phase {actual_idx+1}: {skill} ({level_range}) - 4-Link {socket_4link}',
                            'Show',
                            '    LinkedSockets >= 4',
                            f'    SocketGroup "{socket_4link}"',
                            area_condition,
                            '    SetFontSize 45',
                            '    SetTextColor 30 200 200 255',
                            '    SetBorderColor 30 200 200 255',
                            '    SetBackgroundColor 0 50 50 200',
                            f'    CustomAlertSound "{sound_dir}/high_value.mp3"',
                            '    PlayEffect Cyan',
                            '    MinimapIcon 1 Cyan Diamond',
                            '',
                        ])
            else:
                # 레벨링 페이즈가 없으면 기존 로직 사용
                # 빌드 타입별 젬 색상 결정
                if build_type == 'dot':
                    socket_colors = ['B', 'B', 'B', 'G']  # 3B1G
                    gem_color_desc = '3B1G (Chaos DoT)'
                elif build_type == 'spell':
                    socket_colors = ['B', 'B', 'B', 'B']  # 4B
                    gem_color_desc = '4B (Spell)'
                else:
                    socket_colors = ['R', 'R', 'G', 'G']  # 2R2G
                    gem_color_desc = '2R2G (Attack)'

                # 3링크 아이템
                socket_3link = ''.join(socket_colors[:3])
                lines.extend([
                    f'# 3-Link Items ({socket_3link})',
                    'Show',
                    '    LinkedSockets >= 3',
                    f'    SocketGroup "{socket_3link}"',
                    '    AreaLevel <= 40',
                    '    SetFontSize 38',
                    '    SetTextColor 100 200 200 220',
                    '    SetBorderColor 100 200 200 220',
                    f'    CustomAlertSound "{sound_dir}/mid_value.mp3"',
                    '',
                ])

                # 4링크 아이템
                socket_str = ''.join(socket_colors)
                lines.extend([
                    f'# 4-Link Items ({gem_color_desc})',
                    'Show',
                    '    LinkedSockets >= 4',
                    f'    SocketGroup "{socket_str}"',
                    '    AreaLevel <= 67',
                    '    SetFontSize 45',
                    '    SetTextColor 30 200 200 255',
                    '    SetBorderColor 30 200 200 255',
                    '    SetBackgroundColor 0 50 50 200',
                    f'    CustomAlertSound "{sound_dir}/high_value.mp3"',
                    '    PlayEffect Cyan',
                    '    MinimapIcon 1 Cyan Diamond',
                    '',
                ])

            # 3. 아무 4링크나 (색상 무관)
            lines.extend([
                '# Any 4-Link Items (for chromatic crafting)',
                'Show',
                '    LinkedSockets >= 4',
                '    AreaLevel <= 67',
                '    SetFontSize 40',
                '    SetTextColor 200 200 200 255',
                '    SetBorderColor 100 100 100 255',
                f'    CustomAlertSound "{sound_dir}/mid_value.mp3"',
                '',
            ])

            # 4. 무브스피드 부츠 베이스
            lines.extend([
                '# Movement Speed Boot Bases - Leveling essentials',
                'Show',
                '    Class "Boots"',
                '    Rarity Magic Rare',
                '    ItemLevel <= 50',
                '    SetFontSize 38',
                '    SetTextColor 200 180 100 255',
                '    SetBorderColor 150 130 50 255',
                '',
            ])

            # 5. +1 젬 레벨 완드 (레벨링 핵심) - 카오스 DoT는 완드만
            if build_type == 'dot':
                lines.extend([
                    '# +1 Gem Level Wands - Check for chaos/spell damage mods',
                    'Show',
                    '    Rarity Magic Rare',
                    '    Class "Wand"',
                    '    ItemLevel >= 2',
                    '    ItemLevel <= 40',
                    '    SetFontSize 38',
                    '    SetTextColor 136 136 255 220',
                    '    SetBorderColor 100 100 200 220',
                    '',
                ])
            elif build_type == 'spell':
                lines.extend([
                    '# +1 Gem Level Wands/Sceptres - Check for spell damage mods',
                    'Show',
                    '    Rarity Magic Rare',
                    '    Class "Wand" "Sceptre"',
                    '    ItemLevel >= 2',
                    '    ItemLevel <= 40',
                    '    SetFontSize 38',
                    '    SetTextColor 136 136 255 220',
                    '    SetBorderColor 100 100 200 220',
                    '',
                ])

            # 6. ES 방어구 베이스 (카오스 DoT 빌드)
            if build_type == 'dot':
                lines.extend([
                    '# ES Armor Bases - For Chaos DoT builds',
                    'Show',
                    '    Class "Body Armour" "Helmet" "Gloves" "Boots" "Shield"',
                    '    Rarity Magic Rare',
                    '    BaseType "Silk" "Velvet" "Robe" "Vestment" "Regalia" "Circlet" "Crown" "Cage" "Spirit Shield"',
                    '    ItemLevel >= 20',
                    '    ItemLevel <= 68',
                    '    SetFontSize 36',
                    '    SetTextColor 100 180 255 220',
                    '    SetBorderColor 50 100 200 220',
                    '',
                ])

            # 7. 레벨링용 플라스크
            lines.extend([
                '# Utility Flasks - Quicksilver, Silver for leveling',
                'Show',
                '    Class "Utility Flask"',
                '    BaseType "Quicksilver Flask" "Silver Flask"',
                '    SetFontSize 40',
                '    SetTextColor 200 200 200 255',
                '    SetBorderColor 150 150 150 255',
                f'    CustomAlertSound "{sound_dir}/mid_value.mp3"',
                '',
            ])

            lines.extend([
                '# ' + '=' * 40,
                '',
            ])

        # 빌드 유니크 아이템
        if uniques:
            unique_str = ' '.join(f'"{u}"' for u in uniques)
            lines.extend([
                '# Build Unique Items - EXACT MATCH (Cyan/Magenta highlight)',
                'Show',
                '    Rarity Unique',
                f'    BaseType == {unique_str}',
                '    SetFontSize 45',
                '    SetTextColor 0 255 255 255',
                '    SetBorderColor 255 0 255 255',
                '    SetBackgroundColor 75 0 130 255',
                f'    CustomAlertSound "{sound_dir}/build_unique.mp3"',
                '    PlayEffect Purple',
                '    MinimapIcon 0 Purple Star',
                '',
            ])

        # 레어 베이스 타입 (크래프팅용)
        rare_bases = [b for b in base_types if b not in uniques]
        if rare_bases:
            base_str = ' '.join(f'"{b}"' for b in rare_bases)
            lines.extend([
                '# Build Rare/Magic Base Types - For crafting upgrades',
                'Show',
                f'    BaseType == {base_str}',
                '    Rarity <= Rare',
                '    ItemLevel >= 82',
                '    SetFontSize 45',
                '    SetTextColor 255 150 255 255',
                '    SetBorderColor 255 100 255 255',
                '    SetBackgroundColor 60 0 60 255',
                f'    CustomAlertSound "{sound_dir}/build_base.mp3"',
                '    PlayEffect Pink',
                '    MinimapIcon 0 Pink Diamond',
                '',
            ])

        # 인플루언스 아이템
        all_bases = ' '.join(f'"{b}"' for b in base_types)
        if base_types:
            lines.extend([
                '# Build Base Types with Influence - VERY IMPORTANT',
                'Show',
                '    HasInfluence Shaper Elder Crusader Redeemer Hunter Warlord',
                f'    BaseType == {all_bases}',
                '    Rarity <= Rare',
                '    SetFontSize 45',
                '    SetTextColor 255 255 0 255',
                '    SetBorderColor 255 200 0 255',
                '    SetBackgroundColor 100 75 0 255',
                f'    CustomAlertSound "{sound_dir}/influenced.mp3"',
                '    PlayEffect Yellow',
                '    MinimapIcon 0 Yellow Star',
                '',
            ])

            # 높은 ilvl 베이스
            lines.extend([
                '# Build Base Types - High Item Level (82+)',
                'Show',
                f'    BaseType == {all_bases}',
                '    ItemLevel >= 82',
                '    Rarity <= Rare',
                '    SetFontSize 42',
                '    SetTextColor 255 255 119 255',
                '    SetBorderColor 255 255 0 255',
                '    SetBackgroundColor 60 60 0 255',
                f'    CustomAlertSound "{sound_dir}/build_upgrade.mp3"',
                '    PlayEffect Yellow',
                '    MinimapIcon 1 Yellow Diamond',
                '',
            ])

            # 일반 ilvl 베이스
            lines.extend([
                '# Build Base Types - Normal Item Level (75+)',
                'Show',
                f'    BaseType == {all_bases}',
                '    ItemLevel >= 75',
                '    Rarity <= Rare',
                '    SetFontSize 38',
                '    SetTextColor 200 200 100 255',
                '    SetBorderColor 200 200 0 255',
                '    MinimapIcon 2 Yellow Circle',
                '',
            ])

        # NeverSink 베이스 추가
        lines.extend([
            '',
            '#' + '=' * 80,
            '# NEVERSINK BASE FILTER',
            '# All rules below are from NeverSink 3.27 Leveling filter',
            '#' + '=' * 80,
            '',
        ])

        neversink_base = self.load_neversink_base()
        if neversink_base:
            # 빌드 타입에 맞게 NeverSink 수정
            build_type = self.detect_build_type()
            lines.append(f'# Build Type: {build_type}')
            lines.append('')

            modified_neversink = self.modify_neversink_for_build(neversink_base)

            # NeverSink 헤더 제거
            ns_lines = modified_neversink.split('\n')
            skip_header = True
            for line in ns_lines:
                if skip_header:
                    if line.startswith('Show') or line.startswith('Hide'):
                        skip_header = False
                        lines.append(line)
                else:
                    lines.append(line)
        else:
            lines.extend([
                '# WARNING: NeverSink base filter not found!',
                '# Please place "Leveling 3.27 filter.filter" in the project root',
                '',
            ])

        return '\n'.join(lines)

    def generate_all_filters(self, output_dir: str = None, build_name: str = None):
        """3단계 필터 모두 생성"""
        if not self.pob_data:
            print("Error: No POB data loaded")
            return []

        # 출력 디렉토리 설정
        if output_dir:
            out_path = Path(output_dir)
        else:
            out_path = Path(r'C:\Users\User\Documents\My Games\Path of Exile')

        # 빌드 이름 설정
        if not build_name:
            ascendancy = self.pob_data.get('ascendancy', 'Build')
            main_skill = self.pob_data.get('main_skill', '')
            build_name = f"{ascendancy}_{main_skill}".replace(' ', '_')

        # 3단계 아이템 데이터 생성
        stages = self.generate_three_stage_items()

        generated_files = []

        for stage_key, stage_data in stages.items():
            stage_name = stage_key.replace('_', ' ').title().replace(' ', '')
            filename = f"PathcraftAI_{build_name}_{stage_name}.filter"
            filepath = out_path / filename

            # 필터 생성 - unique_bases가 있으면 사용 (필터는 베이스타입으로 매칭)
            uniques_for_filter = stage_data.get('unique_bases', stage_data.get('uniques', []))
            filter_content = self.generate_filter(
                stage=stage_key,
                uniques=uniques_for_filter,
                base_types=stage_data.get('base_types', []),
                recommended_uniques=stage_data.get('recommended_uniques'),
                leveling_phases=stage_data.get('leveling_phases', []),
            )

            # 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(filter_content)

            generated_files.append(str(filepath))
            print(f"Generated: {filepath}")

        return generated_files

    def print_build_summary(self):
        """빌드 요약 출력"""
        if not self.pob_data:
            print("No POB data loaded")
            return

        print("=" * 60)
        print("BUILD SUMMARY")
        print("=" * 60)
        print(f"Class: {self.pob_data['class']} / {self.pob_data['ascendancy']}")
        print(f"Level: {self.pob_data['level']}")
        print(f"Main Skill: {self.pob_data['main_skill']}")
        print()

        # 젬 세팅
        gem_setup = self.generate_gem_recommendations()
        print("GEM SETUP:")
        for links, gems in gem_setup.items():
            print(f"  {links}: {' - '.join(gems)}")
        print()

        # 3단계 아이템
        stages = self.generate_three_stage_items()

        print("=" * 60)
        print("LEVELING STAGE")
        print("=" * 60)
        print(f"Gem Setup (4-link): {' - '.join(stages['leveling']['gem_setup'])}")
        print()
        print("Recommended Cheap Uniques:")
        for slot, items in stages['leveling']['recommended_uniques'].items():
            if items:
                print(f"  {slot}:")
                for item in items[:2]:
                    print(f"    - {item['name']} ({item['price']}c)")
        print()

        print("=" * 60)
        print("EARLY MAP STAGE")
        print("=" * 60)
        print(f"Gem Setup (5-link): {' - '.join(stages['early_map']['gem_setup'])}")
        if stages['early_map']['uniques']:
            print(f"Target Uniques: {', '.join(stages['early_map']['uniques'])}")
        print()

        print("=" * 60)
        print("ENDGAME STAGE")
        print("=" * 60)
        print(f"Gem Setup (6-link): {' - '.join(stages['endgame']['gem_setup'])}")
        print(f"Target Uniques: {', '.join(stages['endgame']['uniques'])}")
        print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate 3-stage filters from POB')
    parser.add_argument('pob', nargs='?', default="https://pobb.in/ozmUjt87nmuS",
                       help='POB URL or code')
    parser.add_argument('--output', '-o', default=None,
                       help='Output directory for filters')
    parser.add_argument('--name', '-n', default=None,
                       help='Build name for filter files')
    parser.add_argument('--summary', '-s', action='store_true',
                       help='Print build summary only')

    args = parser.parse_args()

    generator = BuildFilterGenerator()

    print(f"Fetching POB: {args.pob}")
    print()

    try:
        xml_data = generator.fetch_pob(args.pob)
        generator.parse_pob(xml_data)
        generator.print_build_summary()

        if not args.summary:
            print()
            print("=" * 60)
            print("GENERATING FILTERS")
            print("=" * 60)

            # 출력 디렉토리 설정
            output_dir = args.output or str(Path(__file__).parent)

            files = generator.generate_all_filters(
                output_dir=output_dir,
                build_name=args.name
            )

            print()
            print(f"Generated {len(files)} filter files")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
