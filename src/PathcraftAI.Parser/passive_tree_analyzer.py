#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Passive Tree Analyzer - 패시브 트리 추천 강화
현재 레벨에서 목표 레벨까지 단계별 패시브 노드 추천
"""

import sys
import json
import argparse
from typing import Dict, List, Set, Tuple

# UTF-8 설정 (Windows)
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


class PassiveTreeAnalyzer:
    """패시브 트리 분석 및 추천"""

    def __init__(self, current_level: int, target_level: int):
        self.current_level = current_level
        self.target_level = target_level
        self.current_points = self._calculate_points(current_level)
        self.target_points = self._calculate_points(target_level)
        self.points_needed = self.target_points - self.current_points

        # 노드 데이터
        self.current_nodes: Set[str] = set()
        self.target_nodes: Set[str] = set()
        self.missing_nodes: Set[str] = set()
        self.node_info: Dict[str, Dict] = {}

    def _calculate_points(self, level: int) -> int:
        """레벨에서 사용 가능한 패시브 포인트 계산

        - Starting class: 기본 포인트 포함
        - Quest rewards: 24 points (Act 완료 보상)
        - Level-up: level - 1 points
        """
        if level < 2:
            return 0

        # 퀘스트 보상 (최대 24포인트)
        quest_points = min(24, (level - 1) // 3)

        # 레벨업 포인트
        levelup_points = level - 1

        return quest_points + levelup_points

    def set_current_tree(self, allocated_nodes: List[str]):
        """현재 캐릭터의 할당된 노드 설정"""
        self.current_nodes = set(allocated_nodes)

    def set_target_tree(self, target_nodes_data: Dict[str, Dict]):
        """목표 POB의 노드 데이터 설정

        Args:
            target_nodes_data: {
                'node_id': {
                    'name': 'node name',
                    'stats': ['stat1', 'stat2'],
                    'type': 'notable' | 'keystone' | 'normal',
                    'priority': 1-3  # 1=Life, 2=DPS, 3=Utility
                }
            }
        """
        self.target_nodes = set(target_nodes_data.keys())
        self.node_info = target_nodes_data
        self.missing_nodes = self.target_nodes - self.current_nodes

    def calculate_missing_nodes(self) -> List[Dict]:
        """부족한 노드 목록과 우선순위 계산"""
        missing = []

        for node_id in self.missing_nodes:
            node_data = self.node_info.get(node_id, {})

            missing.append({
                'node_id': node_id,
                'name': node_data.get('name', f'Node {node_id}'),
                'stats': node_data.get('stats', []),
                'type': node_data.get('type', 'normal'),
                'priority': node_data.get('priority', 3),
                'category': self._categorize_node(node_data)
            })

        # 우선순위로 정렬 (1=Life 최우선, 2=DPS, 3=Utility)
        missing.sort(key=lambda x: (x['priority'], x['name']))

        return missing

    def _categorize_node(self, node_data: Dict) -> str:
        """노드 카테고리 분류"""
        stats = ' '.join(node_data.get('stats', [])).lower()

        # Life/ES 노드 (최우선)
        if any(keyword in stats for keyword in ['life', 'energy shield', 'es']):
            return 'Life/Defense'

        # DPS 노드
        if any(keyword in stats for keyword in ['damage', 'crit', 'attack', 'spell', 'elemental']):
            return 'DPS'

        # Utility 노드
        if any(keyword in stats for keyword in ['mana', 'resist', 'movement', 'flask']):
            return 'Utility'

        return 'Other'

    def generate_level_roadmap(self, missing_nodes: List[Dict]) -> List[Dict]:
        """레벨별 노드 할당 로드맵 생성"""
        roadmap = []

        # 5레벨 단위로 그룹핑
        level_ranges = []
        current = self.current_level

        while current < self.target_level:
            next_level = min(current + 5, self.target_level)
            points_in_range = self._calculate_points(next_level) - self._calculate_points(current)

            level_ranges.append({
                'level_from': current + 1,
                'level_to': next_level,
                'points': points_in_range
            })

            current = next_level

        # 각 레벨 범위에 노드 할당
        node_index = 0

        for level_range in level_ranges:
            points = level_range['points']
            allocated = []

            # 우선순위에 따라 노드 할당
            while points > 0 and node_index < len(missing_nodes):
                node = missing_nodes[node_index]
                allocated.append(node)
                node_index += 1
                points -= 1

            if allocated:
                # 카테고리별 이득 계산
                benefits = self._calculate_benefits(allocated)

                roadmap.append({
                    'level_range': f"Level {level_range['level_from']}-{level_range['level_to']}",
                    'points': level_range['points'],
                    'nodes': allocated,
                    'benefits': benefits,
                    'priority_focus': self._get_priority_focus(allocated)
                })

        return roadmap

    def _calculate_benefits(self, nodes: List[Dict]) -> Dict[str, str]:
        """할당된 노드들의 이득 요약"""
        categories = {}

        for node in nodes:
            category = node['category']
            categories[category] = categories.get(category, 0) + 1

        benefits = {}

        if 'Life/Defense' in categories:
            benefits['Survivability'] = f"+{categories['Life/Defense']} defense nodes"

        if 'DPS' in categories:
            benefits['Damage'] = f"+{categories['DPS']} damage nodes"

        if 'Utility' in categories:
            benefits['Utility'] = f"+{categories['Utility']} utility nodes"

        return benefits

    def _get_priority_focus(self, nodes: List[Dict]) -> str:
        """주요 포커스 카테고리 반환"""
        if not nodes:
            return "None"

        # 가장 많은 카테고리 찾기
        categories = {}
        for node in nodes:
            cat = node['category']
            categories[cat] = categories.get(cat, 0) + 1

        max_cat = max(categories.items(), key=lambda x: x[1])
        return max_cat[0]

    def print_roadmap(self, roadmap: List[Dict]):
        """로드맵 텍스트 출력"""
        print("=" * 80)
        print(f"PASSIVE TREE ROADMAP (Lv{self.current_level} → Lv{self.target_level})")
        print("=" * 80)
        print()
        print(f"Current Points: {self.current_points} | Target Points: {self.target_points}")
        print(f"Points Needed: {self.points_needed}")
        print(f"Missing Nodes: {len(self.missing_nodes)}")
        print()

        for i, stage in enumerate(roadmap, 1):
            print(f"{stage['level_range']} ({stage['points']} points):")
            print(f"  ✓ Priority Focus: {stage['priority_focus']}")
            print()

            # 노드 목록
            for node in stage['nodes']:
                node_type = node['type'].upper() if node['type'] != 'normal' else ''
                type_str = f" [{node_type}]" if node_type else ""
                print(f"  → {node['name']}{type_str}")

                # 스탯 표시
                for stat in node['stats'][:2]:  # 처음 2개만
                    print(f"     • {stat}")

            print()

            # 이득 요약
            if stage['benefits']:
                print("  Gains:")
                for benefit_type, benefit_desc in stage['benefits'].items():
                    print(f"    • {benefit_type}: {benefit_desc}")

            print()
            print("-" * 80)
            print()

    def to_json(self, roadmap: List[Dict]) -> Dict:
        """JSON 출력용 데이터 생성"""
        return {
            'current_level': self.current_level,
            'target_level': self.target_level,
            'current_points': self.current_points,
            'target_points': self.target_points,
            'points_needed': self.points_needed,
            'missing_nodes_count': len(self.missing_nodes),
            'roadmap': roadmap
        }


def create_mock_data() -> Tuple[int, int, List[str], Dict[str, Dict]]:
    """Mock 데이터 생성 (테스트용)"""
    current_level = 69
    target_level = 94

    # 현재 할당된 노드 (간략화)
    current_nodes = [
        'node_1', 'node_2', 'node_3', 'node_4', 'node_5',
        'node_6', 'node_7', 'node_8', 'node_9', 'node_10'
    ]

    # 목표 노드 (더 많은 노드 포함)
    target_nodes = {
        # 현재 노드들 (이미 할당됨)
        'node_1': {'name': 'Coordination', 'stats': ['+10 Dexterity'], 'type': 'normal', 'priority': 3},
        'node_2': {'name': 'Sovereignty', 'stats': ['+6% Mana Reserved'], 'type': 'notable', 'priority': 3},
        'node_3': {'name': 'Written in Blood', 'stats': ['+15% increased maximum Life', '+5% Attack Speed'], 'type': 'notable', 'priority': 1},
        'node_4': {'name': 'Blood Siphon', 'stats': ['+8% maximum Life'], 'type': 'normal', 'priority': 1},
        'node_5': {'name': 'Devotion', 'stats': ['+10 to all Attributes'], 'type': 'normal', 'priority': 3},
        'node_6': {'name': 'Heart of Thunder', 'stats': ['+24% Lightning Damage'], 'type': 'normal', 'priority': 2},
        'node_7': {'name': 'Breath of Lightning', 'stats': ['+15% Lightning Damage', '+8% Shock Effect'], 'type': 'notable', 'priority': 2},
        'node_8': {'name': 'Light of Divinity', 'stats': ['+12% Energy Shield'], 'type': 'normal', 'priority': 1},
        'node_9': {'name': 'Deep Wisdom', 'stats': ['+15 Intelligence', '+4% Energy Shield'], 'type': 'notable', 'priority': 1},
        'node_10': {'name': 'Arcane Will', 'stats': ['+6% Mana', '+10% Spell Damage'], 'type': 'normal', 'priority': 2},

        # 부족한 노드들 (아직 미할당)
        'node_11': {'name': 'Throatseeker', 'stats': ['+40% Critical Strike Multiplier', '+10% Critical Strike Chance'], 'type': 'notable', 'priority': 2},
        'node_12': {'name': 'Assassination', 'stats': ['+30% Critical Strike Multiplier'], 'type': 'notable', 'priority': 2},
        'node_13': {'name': 'Doom Cast', 'stats': ['+20% Spell Damage', '+10% Cast Speed'], 'type': 'notable', 'priority': 2},
        'node_14': {'name': 'Jewel Socket', 'stats': ['Can allocate Cluster Jewel'], 'type': 'jewel', 'priority': 2},
        'node_15': {'name': 'Constitution', 'stats': ['+24% increased maximum Life'], 'type': 'notable', 'priority': 1},
        'node_16': {'name': 'Void Barrier', 'stats': ['+18% Energy Shield', '+6% Chaos Resistance'], 'type': 'notable', 'priority': 1},
        'node_17': {'name': 'Heart and Soul', 'stats': ['+8% maximum Life', '+6% maximum Mana'], 'type': 'normal', 'priority': 1},
        'node_18': {'name': 'Spell Breaker', 'stats': ['+15% Spell Damage', '+4% Mana'], 'type': 'normal', 'priority': 2},
        'node_19': {'name': 'Prismatic Skin', 'stats': ['+6% All Resistances'], 'type': 'normal', 'priority': 3},
        'node_20': {'name': 'Diamond Skin', 'stats': ['+15% All Resistances'], 'type': 'notable', 'priority': 3},
        'node_21': {'name': 'Cruel Preparation', 'stats': ['+20% maximum Life', '+6 Life Regeneration per second'], 'type': 'notable', 'priority': 1},
        'node_22': {'name': 'Elemental Focus', 'stats': ['+24% Elemental Damage'], 'type': 'normal', 'priority': 2},
        'node_23': {'name': 'Potency of Will', 'stats': ['+15% Spell Damage', '+10% Effect Duration'], 'type': 'notable', 'priority': 2},
        'node_24': {'name': 'Enigmatic Defense', 'stats': ['+12% Energy Shield', '+8% Evasion'], 'type': 'normal', 'priority': 1},
        'node_25': {'name': 'Quickstep', 'stats': ['+5% Movement Speed'], 'type': 'normal', 'priority': 3},
        'node_26': {'name': 'Path of the Savant', 'stats': ['+20 Intelligence', '+6% Energy Shield'], 'type': 'notable', 'priority': 1},
        'node_27': {'name': 'Overcharged', 'stats': ['+30% Lightning Damage', '+10% Shock Effect'], 'type': 'notable', 'priority': 2},
        'node_28': {'name': 'Static Blows', 'stats': ['+20% Shock Duration', '+15% Lightning Damage'], 'type': 'notable', 'priority': 2},
        'node_29': {'name': 'Entropy', 'stats': ['+15% Elemental Damage', '+8% Ailment Damage'], 'type': 'normal', 'priority': 2},
    }

    return current_level, target_level, current_nodes, target_nodes


def get_pob_passive_tree(pob_url: str) -> Tuple[int, List[str], Dict[str, Dict]]:
    """POB에서 패시브 트리 데이터 추출"""
    try:
        from smart_build_analyzer import SmartBuildAnalyzer

        analyzer = SmartBuildAnalyzer(pob_url)
        analyzer.fetch_pob()

        # Build 정보에서 레벨 가져오기
        build = analyzer.root.find('.//Build')
        target_level = 94  # 기본값

        if build is not None:
            level_str = build.get('level')
            if level_str:
                target_level = int(level_str)

        # Tree 섹션 찾기
        tree = analyzer.root.find('.//Tree')
        if tree is None:
            return target_level, [], {}

        # Spec 찾기 (활성화된 패시브 트리)
        spec = tree.find('.//Spec')
        if spec is None:
            return target_level, [], {}

        # 할당된 노드 추출
        nodes = spec.findall('.//Node')
        allocated_node_ids = []
        node_info = {}

        for node in nodes:
            node_id = node.get('nodeId') or node.get('id')
            if node_id:
                allocated_node_ids.append(node_id)

                # 노드 이름과 타입 추출 (가능한 경우)
                node_name = node.get('name', f'Node {node_id}')
                node_type = node.get('type', 'normal')

                # 간단한 카테고리 추정 (이름 기반)
                priority = 3  # 기본값
                stats = []

                # 노드 이름으로 카테고리 추정
                name_lower = node_name.lower()
                if any(k in name_lower for k in ['life', 'vitality', 'constitution', 'heart', 'energy shield', 'shield']):
                    priority = 1
                    stats.append('Life/ES node')
                elif any(k in name_lower for k in ['damage', 'power', 'crit', 'elemental', 'spell', 'attack']):
                    priority = 2
                    stats.append('Damage node')
                else:
                    stats.append('Utility node')

                node_info[node_id] = {
                    'name': node_name,
                    'stats': stats,
                    'type': node_type,
                    'priority': priority
                }

        return target_level, allocated_node_ids, node_info

    except Exception as e:
        print(f"[ERROR] Failed to parse POB tree: {e}", file=sys.stderr)
        return 94, [], {}


def get_character_level(character_name: str) -> int:
    """캐릭터 레벨 가져오기"""
    try:
        from poe_oauth import load_token, get_user_characters

        token_data = load_token()
        if not token_data:
            return 1

        characters = get_user_characters(token_data['access_token'])
        char_list = characters.get('characters', [])

        for char in char_list:
            if char.get('name') == character_name:
                return char.get('level', 1)

        return 1

    except Exception as e:
        print(f"[ERROR] Failed to get character level: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description='패시브 트리 분석 및 추천')
    parser.add_argument('--current-level', type=int, help='현재 레벨')
    parser.add_argument('--target-level', type=int, help='목표 레벨')
    parser.add_argument('--pob', type=str, help='POB URL (목표 빌드)')
    parser.add_argument('--character', type=str, help='캐릭터 이름 (현재 빌드)')
    parser.add_argument('--mock', action='store_true', help='Mock 데이터 사용')
    parser.add_argument('--json', action='store_true', help='JSON 출력 모드')

    args = parser.parse_args()

    # Mock 또는 실제 데이터 로드
    if args.mock:
        current_level, target_level, current_nodes, target_nodes_data = create_mock_data()
    elif args.pob and args.character:
        # POB와 캐릭터에서 실제 데이터 로드
        try:
            if not args.json:
                print("Loading POB passive tree...")

            # POB에서 목표 레벨과 노드 가져오기
            target_level, target_node_ids, target_nodes_data = get_pob_passive_tree(args.pob)

            # 캐릭터에서 현재 레벨 가져오기
            current_level = get_character_level(args.character)

            # 현재는 캐릭터의 패시브 트리를 가져올 수 없으므로 빈 리스트 사용
            # (POE API는 패시브 트리를 제공하지 않음)
            current_nodes = []

            if not target_nodes_data:
                if args.json:
                    print(json.dumps({"error": "Failed to parse POB passive tree"}))
                else:
                    print("[ERROR] Failed to parse POB passive tree")
                return

            if not args.json:
                print(f"  ✓ Target level: {target_level}")
                print(f"  ✓ Current level: {current_level}")
                print(f"  ✓ Total nodes in POB: {len(target_nodes_data)}")

        except Exception as e:
            if args.json:
                print(json.dumps({"error": str(e)}))
            else:
                print(f"[ERROR] Failed to load data: {e}")
            return
    else:
        if args.json:
            print(json.dumps({"error": "No data source specified. Use --pob and --character, or --mock"}))
        else:
            print("[ERROR] No data source specified")
            print("[INFO] Use --pob <url> --character <name>, or --mock for testing")
        return

    # Override with command-line args if provided
    if args.current_level:
        current_level = args.current_level
    if args.target_level:
        target_level = args.target_level

    # 분석기 초기화
    analyzer = PassiveTreeAnalyzer(current_level, target_level)
    analyzer.set_current_tree(current_nodes)
    analyzer.set_target_tree(target_nodes_data)

    # 부족한 노드 계산
    missing_nodes = analyzer.calculate_missing_nodes()

    # 레벨별 로드맵 생성
    roadmap = analyzer.generate_level_roadmap(missing_nodes)

    # 출력
    if args.json:
        output = analyzer.to_json(roadmap)
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        analyzer.print_roadmap(roadmap)


if __name__ == '__main__':
    main()
