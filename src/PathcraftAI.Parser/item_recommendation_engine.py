#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Item Recommendation Engine
빌드 분석 기반 동적 아이템 추천 시스템
- POB 빌드 분석 → 키워드 추출
- mods.json에서 관련 모드 필터링
- poe.ninja에서 가격 조회
- 예산 기반 최적화
"""

import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import Counter

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

# 로컬 모듈
from pob_item_parser import POBItemParser
from poe_ninja_api import POENinjaAPI


@dataclass
class ItemRecommendation:
    """추천 아이템 정보"""
    name: str
    item_type: str  # unique, rare
    slot: str  # helmet, body, weapon, etc
    price_chaos: float
    price_formatted: str
    reason: str  # 추천 이유
    priority: int  # 우선순위 (1=높음, 5=낮음)
    mods: List[str] = field(default_factory=list)  # 주요 모드


class ItemRecommendationEngine:
    """동적 아이템 추천 엔진"""

    def __init__(self, league: str = "Standard"):
        """
        Args:
            league: 리그 이름 (Standard, Hardcore, 또는 현재 챌린지 리그)
        """
        self.league = league
        self.ninja_api = POENinjaAPI(league=league, use_cache=True, cache_ttl=300)  # 5분 캐시
        self.mods_data = self._load_mods_data()
        self.uniques_data = self._load_uniques_data()

        # 키워드-모드 태그 매핑
        self.keyword_to_tags = {
            # 공격 스탯
            'spell_damage': ['spell', 'caster'],
            'elemental_damage': ['elemental'],
            'physical_damage': ['physical', 'attack'],
            'fire_damage': ['fire', 'elemental'],
            'cold_damage': ['cold', 'elemental'],
            'lightning_damage': ['lightning', 'elemental'],
            'chaos_damage': ['chaos'],
            'attack_speed': ['attack', 'speed'],
            'cast_speed': ['caster', 'speed'],
            'crit_chance': ['critical'],
            'crit_multi': ['critical'],
            'dot_damage': ['damage_over_time'],

            # 방어 스탯
            'max_life': ['life'],
            'max_es': ['energy_shield', 'defences'],
            'max_mana': ['mana', 'resource'],
            'resistance': ['resistance', 'elemental'],
            'armour': ['armour', 'defences'],
            'evasion': ['evasion', 'defences'],
            'energy_shield': ['energy_shield', 'defences'],

            # 유틸리티
            'movement_speed': ['speed'],
            'gem_level': ['gem'],
            'aura_effect': ['aura'],
            'curse_effect': ['curse'],
            'minion': ['minion'],
        }

        # 슬롯별 유니크 아이템 카테고리
        self.slot_categories = {
            'helmet': ['helmet', 'helm', 'mask', 'crown', 'hood', 'circlet', 'burgonet', 'tricorne', 'cap', 'cage', 'hauberk', 'bascinet', 'sallet', 'coif', 'casque', 'plate'],
            'body': ['body armour', 'body', 'robe', 'vest', 'vestment', 'garb', 'armour', 'brigandine', 'doublet', 'jerkin', 'tunic', 'jacket', 'coat', 'raiment', 'regalia', 'silks', 'wrap', 'wyrmscale', 'dragonscale', 'lamellar', 'plate', 'chainmail', 'ringmail'],
            'gloves': ['gloves', 'gauntlets', 'mitts', 'bracers'],
            'boots': ['boots', 'greaves', 'slippers', 'shoes'],
            'belt': ['belt', 'stygian', 'sash', 'rustic'],
            'amulet': ['amulet', 'talisman'],
            'ring': ['ring'],
            'weapon': ['sword', 'axe', 'mace', 'dagger', 'claw', 'bow', 'staff', 'wand', 'sceptre', 'rapier', 'foil', 'sabre'],
            'shield': ['shield', 'buckler', 'tower', 'kite'],
            'flask': ['flask'],
            'jewel': ['jewel'],
        }

    def _load_mods_data(self) -> List[Dict]:
        """mods.json 로드"""
        mods_path = Path(__file__).parent / "game_data" / "mods.json"
        if mods_path.exists():
            with open(mods_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _load_uniques_data(self) -> Dict[str, Dict]:
        """uniques.json 로드

        Returns:
            {아이템이름: {데이터}} 딕셔너리
        """
        uniques_path = Path(__file__).parent / "game_data" / "uniques.json"
        if uniques_path.exists():
            with open(uniques_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def analyze_build(self, pob_xml_path: str) -> Dict:
        """POB XML에서 빌드 분석

        Returns:
            빌드 분석 결과 (키워드, 데미지 타입 등)
        """
        parser = POBItemParser()
        parser.parse_xml(pob_xml_path)
        return parser.analyze_build_for_filter()

    def get_relevant_mods(self, keywords: List[str], limit: int = 50) -> List[Dict]:
        """키워드에 맞는 관련 모드 찾기

        Args:
            keywords: 빌드 키워드 (spell_damage, fire, crit 등)
            limit: 반환할 최대 모드 수

        Returns:
            관련 모드 리스트
        """
        if not self.mods_data:
            return []

        # 키워드를 태그로 변환
        target_tags = set()
        for keyword in keywords:
            if keyword in self.keyword_to_tags:
                target_tags.update(self.keyword_to_tags[keyword])
            else:
                # 직접 태그로 추가
                target_tags.add(keyword.lower())

        # 모드 필터링 및 스코어링
        scored_mods = []
        for mod in self.mods_data:
            mod_tags = set(mod.get('tags', []))

            # 태그 매칭 스코어
            match_score = len(target_tags & mod_tags)
            if match_score > 0:
                scored_mods.append({
                    **mod,
                    'relevance_score': match_score
                })

        # 스코어순 정렬
        scored_mods.sort(key=lambda x: x['relevance_score'], reverse=True)

        return scored_mods[:limit]

    def find_uniques_by_mods(self, keywords: List[str], build_type: str = None) -> List[Dict]:
        """키워드에 맞는 유니크 아이템 찾기

        Args:
            keywords: 빌드 키워드
            build_type: spell, attack, minion 등

        Returns:
            관련 유니크 아이템 리스트
        """
        if not self.uniques_data:
            return []

        # 키워드 패턴 생성
        keyword_patterns = []
        for kw in keywords:
            if kw == 'spell_damage':
                keyword_patterns.extend(['spell damage', 'spell skill'])
            elif kw == 'fire_damage':
                keyword_patterns.extend(['fire damage', 'fire resist', 'fire penetration'])
            elif kw == 'cold_damage':
                keyword_patterns.extend(['cold damage', 'cold resist', 'cold penetration'])
            elif kw == 'lightning_damage':
                keyword_patterns.extend(['lightning damage', 'lightning resist', 'lightning penetration'])
            elif kw == 'crit_chance':
                keyword_patterns.extend(['critical strike chance', 'critical chance'])
            elif kw == 'crit_multi':
                keyword_patterns.extend(['critical strike multiplier', 'critical multiplier'])
            elif kw == 'max_life':
                keyword_patterns.extend(['maximum life', 'to life', 'life regeneration'])
            elif kw == 'max_es':
                keyword_patterns.extend(['maximum energy shield', 'energy shield'])
            elif kw == 'attack_speed':
                keyword_patterns.append('attack speed')
            elif kw == 'cast_speed':
                keyword_patterns.append('cast speed')
            elif kw == 'dot_damage':
                keyword_patterns.extend(['damage over time', 'burning damage', 'poison damage', 'bleed'])
            elif kw == 'minion':
                keyword_patterns.extend(['minion', 'summon', 'zombie', 'spectre', 'golem', 'skeleton'])
            else:
                keyword_patterns.append(kw.replace('_', ' '))

        # 유니크 아이템 스코어링
        scored_uniques = []
        for name, unique_data in self.uniques_data.items():
            base = unique_data.get('base_type', '')
            # POB variant 태그 제거 (예: {variant:1,2}Siege Helmet -> Siege Helmet)
            base = re.sub(r'\{[^}]*\}', '', base).strip()
            mods = unique_data.get('mods', [])
            implicits = unique_data.get('implicits', [])

            # 모든 모드 텍스트 합치기
            all_mods = mods + implicits
            all_mod_text = ' '.join(all_mods).lower()

            # 패턴 매칭 스코어
            match_score = 0
            matched_keywords = []
            for pattern in keyword_patterns:
                if pattern.lower() in all_mod_text:
                    match_score += 1
                    matched_keywords.append(pattern)

            if match_score > 0:
                scored_uniques.append({
                    'name': name,
                    'base': base,
                    'mods': mods,
                    'relevance_score': match_score,
                    'matched_keywords': matched_keywords
                })

        # 스코어순 정렬
        scored_uniques.sort(key=lambda x: x['relevance_score'], reverse=True)

        return scored_uniques

    def get_price_data(self, item_names: List[str]) -> Dict[str, float]:
        """poe.ninja에서 가격 조회

        Args:
            item_names: 아이템 이름 리스트

        Returns:
            {아이템이름: chaos가격} 딕셔너리
        """
        all_prices = self.ninja_api.get_all_unique_prices()

        result = {}
        for name in item_names:
            price = self.ninja_api.get_item_price(name)
            if price:
                result[name] = price

        return result

    def recommend_items(
        self,
        build_analysis: Dict,
        budget_chaos: int = None,
        slots: List[str] = None,
        limit_per_slot: int = 5
    ) -> Dict[str, List[ItemRecommendation]]:
        """빌드 분석 기반 아이템 추천

        Args:
            build_analysis: analyze_build()의 결과
            budget_chaos: 최대 예산 (Chaos 단위)
            slots: 추천받을 슬롯 리스트 (None이면 전체)
            limit_per_slot: 슬롯당 최대 추천 수

        Returns:
            {슬롯: [추천아이템]} 딕셔너리
        """
        keywords = build_analysis.get('keywords', [])
        build_type = build_analysis.get('build_type', 'unknown')
        primary_element = build_analysis.get('primary_element')

        # 추가 키워드 생성
        if primary_element:
            keywords.append(f'{primary_element}_damage')

        # 관련 유니크 찾기
        relevant_uniques = self.find_uniques_by_mods(keywords, build_type)

        # 가격 조회
        unique_names = [u['name'] for u in relevant_uniques]
        prices = self.get_price_data(unique_names)

        # 슬롯별 추천 생성
        recommendations = {}
        target_slots = slots or list(self.slot_categories.keys())

        for slot in target_slots:
            slot_items = []
            slot_bases = self.slot_categories.get(slot, [])

            for unique in relevant_uniques:
                base_lower = unique.get('base', '').lower()

                # 슬롯 매칭 확인
                is_slot_match = any(sb in base_lower for sb in slot_bases)
                if not is_slot_match:
                    continue

                name = unique['name']
                price = prices.get(name)

                # 가격 없으면 스킵
                if price is None:
                    continue

                # 예산 필터링
                if budget_chaos and price > budget_chaos:
                    continue

                # 추천 이유 생성
                matched = unique.get('matched_keywords', [])
                reason = f"빌드 키워드 매칭: {', '.join(matched[:3])}"

                # 우선순위 계산 (높은 관련성 + 낮은 가격 = 높은 우선순위)
                relevance = unique.get('relevance_score', 1)
                # 가격 대비 가치 (100c당 1점)
                value_score = relevance * 100 / max(price, 1)
                priority = max(1, 5 - int(value_score / 2))

                recommendation = ItemRecommendation(
                    name=name,
                    item_type='unique',
                    slot=slot,
                    price_chaos=price,
                    price_formatted=self.ninja_api.format_price(price),
                    reason=reason,
                    priority=priority,
                    mods=unique.get('mods', [])[:5]  # 상위 5개 모드만
                )

                slot_items.append(recommendation)

            # 우선순위 및 가격순 정렬
            slot_items.sort(key=lambda x: (x.priority, x.price_chaos))
            recommendations[slot] = slot_items[:limit_per_slot]

        return recommendations

    def recommend_for_pob(
        self,
        pob_xml_path: str,
        budget_chaos: int = None,
        slots: List[str] = None
    ) -> Dict[str, List[ItemRecommendation]]:
        """POB 파일에서 직접 아이템 추천

        Args:
            pob_xml_path: POB XML 파일 경로
            budget_chaos: 최대 예산
            slots: 추천받을 슬롯

        Returns:
            슬롯별 추천 아이템
        """
        # 빌드 분석
        build_analysis = self.analyze_build(pob_xml_path)

        # 추천 생성
        return self.recommend_items(
            build_analysis,
            budget_chaos=budget_chaos,
            slots=slots
        )

    def get_upgrade_recommendations(
        self,
        pob_xml_path: str,
        budget_chaos: int = None
    ) -> List[ItemRecommendation]:
        """현재 장비 대비 업그레이드 추천

        Args:
            pob_xml_path: POB XML 파일 경로
            budget_chaos: 최대 예산

        Returns:
            업그레이드 추천 리스트 (우선순위순)
        """
        parser = POBItemParser()
        parser.parse_xml(pob_xml_path)

        # 현재 장착 아이템
        equipped = parser.get_equipped_items()
        equipped_names = {item.name.lower() for item in equipped}

        # 빌드 분석
        build_analysis = parser.analyze_build_for_filter()

        # 추천 생성
        all_recommendations = self.recommend_items(
            build_analysis,
            budget_chaos=budget_chaos
        )

        # 이미 장착한 아이템 제외
        upgrades = []
        for slot, items in all_recommendations.items():
            for item in items:
                if item.name.lower() not in equipped_names:
                    upgrades.append(item)

        # 우선순위 및 가격순 정렬
        upgrades.sort(key=lambda x: (x.priority, x.price_chaos))

        return upgrades

    def get_budget_optimized_set(
        self,
        pob_xml_path: str,
        total_budget_chaos: int
    ) -> List[ItemRecommendation]:
        """총 예산 내에서 최적화된 장비 세트 추천

        Args:
            pob_xml_path: POB XML 파일 경로
            total_budget_chaos: 총 예산

        Returns:
            예산 최적화된 장비 세트
        """
        # 빌드 분석
        build_analysis = self.analyze_build(pob_xml_path)

        # 슬롯별 추천
        all_recommendations = self.recommend_items(
            build_analysis,
            budget_chaos=total_budget_chaos,  # 개별 아이템 예산
            limit_per_slot=10
        )

        # 예산 최적화 (greedy 방식)
        selected = []
        remaining_budget = total_budget_chaos
        used_slots = set()

        # 모든 추천을 가치순으로 정렬
        all_items = []
        for slot, items in all_recommendations.items():
            for item in items:
                # 가치 = 관련성 / 가격
                value = (6 - item.priority) / max(item.price_chaos, 1)
                all_items.append((value, slot, item))

        all_items.sort(key=lambda x: x[0], reverse=True)

        # 가치 높은 순으로 선택
        for value, slot, item in all_items:
            if slot in used_slots:
                continue
            if item.price_chaos > remaining_budget:
                continue

            selected.append(item)
            used_slots.add(slot)
            remaining_budget -= item.price_chaos

        return selected

    def format_recommendations(self, recommendations: Dict[str, List[ItemRecommendation]]) -> str:
        """추천 결과를 읽기 쉬운 형식으로 포맷

        Args:
            recommendations: recommend_items()의 결과

        Returns:
            포맷된 문자열
        """
        lines = []

        for slot, items in recommendations.items():
            if not items:
                continue

            lines.append(f"\n=== {slot.upper()} ===")

            for i, item in enumerate(items, 1):
                lines.append(f"\n{i}. {item.name}")
                lines.append(f"   가격: {item.price_formatted}")
                lines.append(f"   이유: {item.reason}")

                if item.mods:
                    lines.append("   주요 모드:")
                    for mod in item.mods[:3]:
                        lines.append(f"     - {mod}")

        return '\n'.join(lines)


def test_engine():
    """추천 엔진 테스트"""
    print("=" * 80)
    print("Item Recommendation Engine Test")
    print("=" * 80)

    # 엔진 초기화
    engine = ItemRecommendationEngine(league="Standard")

    # mods.json 로드 확인
    print(f"\nLoaded {len(engine.mods_data)} mods")
    print(f"Loaded {len(engine.uniques_data)} uniques")

    # 테스트 빌드 분석 (하드코딩된 예시)
    test_analysis = {
        'build_type': 'spell',
        'primary_element': 'fire',
        'keywords': ['spell_damage', 'crit_chance', 'crit_multi', 'max_life', 'cast_speed'],
        'conversions': [],
        'gem_levels': []
    }

    print("\n" + "=" * 80)
    print("빌드 분석 결과:")
    print(f"  타입: {test_analysis['build_type']}")
    print(f"  속성: {test_analysis['primary_element']}")
    print(f"  키워드: {test_analysis['keywords']}")

    # 추천 생성
    print("\n" + "=" * 80)
    print("아이템 추천 생성 중...")

    recommendations = engine.recommend_items(
        test_analysis,
        budget_chaos=500,  # 500c 예산
        slots=['helmet', 'body', 'weapon'],
        limit_per_slot=3
    )

    # 결과 출력
    output = engine.format_recommendations(recommendations)
    print(output)

    # 총 비용 계산
    total_cost = 0
    for slot, items in recommendations.items():
        for item in items:
            total_cost += item.price_chaos

    print(f"\n총 추천 비용: {engine.ninja_api.format_price(total_cost)}")


def test_with_pob():
    """POB 파일로 테스트"""
    script_dir = Path(__file__).parent
    test_files = ["temp_pob.xml", "temp_pob2.xml", "temp_pob3.xml", "temp_pob4.xml"]

    for test_file in test_files:
        pob_path = script_dir / test_file
        if pob_path.exists():
            print(f"\n테스트 파일: {test_file}")
            print("=" * 80)

            engine = ItemRecommendationEngine(league="Standard")

            # 빌드 분석
            analysis = engine.analyze_build(str(pob_path))
            print(f"빌드 타입: {analysis['build_type']}")
            print(f"주요 속성: {analysis['primary_element']}")
            print(f"키워드: {analysis['keywords'][:10]}")

            # 추천 생성
            recommendations = engine.recommend_for_pob(
                str(pob_path),
                budget_chaos=1000,
                slots=['helmet', 'body', 'gloves', 'boots', 'weapon']
            )

            # 결과 출력
            output = engine.format_recommendations(recommendations)
            print(output)

            break
    else:
        print("POB 테스트 파일을 찾을 수 없습니다.")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Item Recommendation Engine')
    parser.add_argument('--pob', action='store_true', help='Test with POB file')
    args = parser.parse_args()

    if args.pob:
        test_with_pob()
    else:
        test_engine()
