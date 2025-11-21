# -*- coding: utf-8 -*-
"""
Build Guide System
예산별 업그레이드 로드맵 및 현재 vs 목표 빌드 갭 분석
"""

import json
import os
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


class UpgradePriority(Enum):
    """업그레이드 우선순위"""
    CRITICAL = 1  # 저항 부족, 생존력 위험
    HIGH = 2      # DPS 병목, 주요 유니크
    MEDIUM = 3    # 최적화 단계
    LOW = 4       # 사치품


@dataclass
class UpgradeItem:
    """업그레이드 아이템 정보"""
    slot: str
    current_item: str
    target_item: str
    estimated_price: float  # Chaos 단위
    priority: UpgradePriority
    reason: str
    dps_gain: float = 0
    ehp_gain: float = 0


@dataclass
class BudgetTier:
    """예산 구간"""
    name: str
    min_budget: int  # Chaos
    max_budget: int  # Chaos
    upgrades: List[UpgradeItem]
    total_cost: int
    expected_dps_gain: float
    expected_ehp_gain: float


class BuildGuideSystem:
    """빌드 가이드 시스템"""

    def __init__(self, league: str = "Settlers"):
        self.league = league
        self._price_cache = {}

        # poe.ninja API 로드
        try:
            from poe_ninja_api import POENinjaAPI
            self.ninja_api = POENinjaAPI(league=league)
        except ImportError:
            self.ninja_api = None
            print("[WARN] poe_ninja_api not available", file=sys.stderr)

    def generate_upgrade_roadmap(
        self,
        build_data: Dict,
        current_budget: int = 0,
        target_budget: int = 1000
    ) -> Dict:
        """
        예산별 업그레이드 로드맵 생성

        Args:
            build_data: POB 파싱된 빌드 데이터
            current_budget: 현재 예산 (Chaos)
            target_budget: 목표 예산 (Chaos)

        Returns:
            예산 구간별 업그레이드 로드맵
        """

        # 빌드 정보 추출
        stages = build_data.get('progression_stages', [])
        if not stages:
            return {"error": "No build stages found"}

        stage = stages[0]
        gear = stage.get('gear_recommendation', {})

        # Divine 환율 가져오기
        divine_rate = 150  # 기본값
        if self.ninja_api:
            divine_rate = self.ninja_api.get_divine_chaos_rate()

        # 현재 장비 분석
        gear_analysis = self._analyze_current_gear(gear)

        # 예산 구간 정의
        budget_tiers = self._define_budget_tiers(divine_rate)

        # 각 구간별 업그레이드 추천 생성
        roadmap = {
            "build_name": build_data.get('meta', {}).get('build_name', 'Unknown'),
            "divine_rate": divine_rate,
            "current_budget": current_budget,
            "target_budget": target_budget,
            "current_gear": gear_analysis,
            "tiers": []
        }

        for tier_name, (min_budget, max_budget) in budget_tiers.items():
            if max_budget < current_budget:
                continue  # 이미 달성한 구간은 스킵
            if min_budget > target_budget:
                break  # 목표 예산을 초과하면 종료

            tier_upgrades = self._generate_tier_upgrades(
                gear, tier_name, min_budget, max_budget, divine_rate
            )

            if tier_upgrades['upgrades']:
                roadmap['tiers'].append(tier_upgrades)

        return roadmap

    def _define_budget_tiers(self, divine_rate: float) -> Dict[str, Tuple[int, int]]:
        """예산 구간 정의"""
        return {
            "리그 스타터": (0, 50),
            "저예산": (50, int(divine_rate * 0.5)),
            "중예산": (int(divine_rate * 0.5), int(divine_rate * 3)),
            "고예산": (int(divine_rate * 3), int(divine_rate * 10)),
            "엔드게임": (int(divine_rate * 10), int(divine_rate * 50)),
        }

    def _generate_tier_upgrades(
        self,
        gear: Dict,
        tier_name: str,
        min_budget: int,
        max_budget: int,
        divine_rate: float
    ) -> Dict:
        """각 예산 구간별 업그레이드 추천 생성"""

        upgrades = []
        total_cost = 0

        # 슬롯별 우선순위 (일반적인 업그레이드 순서)
        slot_priorities = {
            "Weapon 1": 1,       # 메인 무기
            "Weapon 2": 2,       # 오프핸드
            "Body Armour": 3,    # 갑옷
            "Helmet": 4,
            "Gloves": 5,
            "Boots": 6,
            "Amulet": 7,
            "Ring 1": 8,
            "Ring 2": 9,
            "Belt": 10,
        }

        # 예산 구간별 추천 템플릿
        tier_templates = {
            "리그 스타터": self._get_league_starter_upgrades,
            "저예산": self._get_low_budget_upgrades,
            "중예산": self._get_mid_budget_upgrades,
            "고예산": self._get_high_budget_upgrades,
            "엔드게임": self._get_endgame_upgrades,
        }

        # 현재 장비 분석
        gear_analysis = self._analyze_current_gear(gear)

        # 해당 구간의 추천 생성
        if tier_name in tier_templates:
            upgrades = tier_templates[tier_name](gear, divine_rate, gear_analysis)

        # 총 비용 계산
        total_cost = sum(u.estimated_price for u in upgrades)

        return {
            "tier_name": tier_name,
            "budget_range": f"{self._format_budget(min_budget, divine_rate)} ~ {self._format_budget(max_budget, divine_rate)}",
            "min_budget": min_budget,
            "max_budget": max_budget,
            "upgrades": [self._upgrade_to_dict(u, divine_rate) for u in upgrades],
            "total_cost": total_cost,
            "total_cost_formatted": self._format_budget(total_cost, divine_rate),
        }

    def _get_league_starter_upgrades(self, gear: Dict, divine_rate: float, gear_analysis: Dict = None) -> List[UpgradeItem]:
        """리그 스타터 업그레이드 (0-50c)"""
        upgrades = []
        slots = gear_analysis.get("slots", {}) if gear_analysis else {}

        # 빈 슬롯이나 저가 레어가 있는 곳 우선
        for slot_name in ["Ring 1", "Ring 2", "Belt", "Amulet"]:
            slot_info = slots.get(slot_name, {})
            current_name = slot_info.get("name", "Empty")
            slot_type = slot_info.get("type", "empty")

            if slot_type in ["empty", "rare"] and slot_info.get("estimated_price", 0) < 10:
                upgrades.append(UpgradeItem(
                    slot=slot_name,
                    current_item=current_name,
                    target_item=f"Life + Triple Resistance Rare {slot_name.replace(' 1', '').replace(' 2', '')}",
                    estimated_price=5,
                    priority=UpgradePriority.CRITICAL,
                    reason="저항 캡(75%) 달성 및 생명력 확보",
                    ehp_gain=400
                ))
                if len(upgrades) >= 2:
                    break

        # 갑옷 업그레이드 (현재 레어이거나 빈 슬롯)
        body_info = slots.get("Body Armour", {})
        if body_info.get("type") != "unique":
            upgrades.append(UpgradeItem(
                slot="Body Armour",
                current_item=body_info.get("name", "Empty"),
                target_item="5-Link Life + Resistance Rare",
                estimated_price=20,
                priority=UpgradePriority.HIGH,
                reason="5링크로 DPS 상승 + 생명력/저항",
                dps_gain=20,
                ehp_gain=800
            ))

        return upgrades

    def _get_low_budget_upgrades(self, gear: Dict, divine_rate: float, gear_analysis: Dict = None) -> List[UpgradeItem]:
        """저예산 업그레이드 (50c - 0.5 Divine)"""
        upgrades = []
        slots = gear_analysis.get("slots", {}) if gear_analysis else {}

        # 무기 업그레이드 (현재 레어인 경우)
        weapon_info = slots.get("Weapon 1", {})
        if weapon_info.get("type") != "unique":
            upgrades.append(UpgradeItem(
                slot="Weapon 1",
                current_item=weapon_info.get("name", "Empty"),
                target_item="Entry-level Unique / Good Rare Weapon",
                estimated_price=30,
                priority=UpgradePriority.HIGH,
                reason="메인 DPS 스케일링의 핵심",
                dps_gain=30
            ))

        # 6링크 갑옷 (현재 유니크가 아니거나 5링크 이하인 경우)
        body_info = slots.get("Body Armour", {})
        current_body = body_info.get("name", "Empty")
        if body_info.get("type") != "unique" or body_info.get("estimated_price", 0) < 30:
            upgrades.append(UpgradeItem(
                slot="Body Armour",
                current_item=current_body,
                target_item="Corrupted 6-Link Rare / Cheap Unique",
                estimated_price=int(divine_rate * 0.2),
                priority=UpgradePriority.HIGH,
                reason="6링크 = 약 40% DPS 증가",
                dps_gain=40
            ))

        return upgrades

    def _get_mid_budget_upgrades(self, gear: Dict, divine_rate: float, gear_analysis: Dict = None) -> List[UpgradeItem]:
        """중예산 업그레이드 (0.5 - 3 Divine)"""
        upgrades = []
        slots = gear_analysis.get("slots", {}) if gear_analysis else {}
        key_items = gear_analysis.get("key_items", []) if gear_analysis else []

        # 핵심 유니크가 없는 슬롯에 추천
        weapon_info = slots.get("Weapon 1", {})
        if weapon_info.get("estimated_price", 0) < divine_rate:
            upgrades.append(UpgradeItem(
                slot="Weapon 1",
                current_item=weapon_info.get("name", "Empty"),
                target_item="Build-defining Unique Weapon",
                estimated_price=int(divine_rate * 1),
                priority=UpgradePriority.HIGH,
                reason="빌드 핵심 유니크로 큰 DPS 점프",
                dps_gain=50
            ))

        # 클러스터 주얼 또는 일반 주얼 업그레이드
        upgrades.append(UpgradeItem(
            slot="Jewel Socket",
            current_item="Basic Jewel",
            target_item="Large Cluster Jewel (3 notables)",
            estimated_price=int(divine_rate * 0.5),
            priority=UpgradePriority.MEDIUM,
            reason="패시브 효율 극대화",
            dps_gain=15
        ))

        # 아직 저가 레어인 슬롯 업그레이드
        for slot_name in ["Helmet", "Gloves", "Boots", "Amulet"]:
            slot_info = slots.get(slot_name, {})
            if slot_info.get("type") == "rare" and slot_info.get("estimated_price", 0) < 20:
                upgrades.append(UpgradeItem(
                    slot=slot_name,
                    current_item=slot_info.get("name", "Empty"),
                    target_item=f"High-tier Rare {slot_name} or Budget Unique",
                    estimated_price=int(divine_rate * 0.3),
                    priority=UpgradePriority.MEDIUM,
                    reason=f"{slot_name} 슬롯 최적화",
                    dps_gain=10,
                    ehp_gain=300
                ))
                break  # 하나만 추천

        return upgrades

    def _get_high_budget_upgrades(self, gear: Dict, divine_rate: float, gear_analysis: Dict = None) -> List[UpgradeItem]:
        """고예산 업그레이드 (3 - 10 Divine)"""
        upgrades = []
        slots = gear_analysis.get("slots", {}) if gear_analysis else {}

        # 인플루언스 아이템으로 업그레이드할 레어 슬롯 찾기
        for slot_name in ["Helmet", "Gloves", "Boots"]:
            slot_info = slots.get(slot_name, {})
            if slot_info.get("type") == "rare":
                upgrades.append(UpgradeItem(
                    slot=slot_name,
                    current_item=slot_info.get("name", "Empty"),
                    target_item=f"Influenced {slot_name} with -res / +gem level / Suppress",
                    estimated_price=int(divine_rate * 2),
                    priority=UpgradePriority.MEDIUM,
                    reason="인플루언스 모드로 DPS/생존력 상승",
                    dps_gain=15,
                    ehp_gain=500
                ))
                break

        # Watcher's Eye 또는 고급 주얼
        upgrades.append(UpgradeItem(
            slot="Jewel Socket",
            current_item="Cluster Jewel",
            target_item="Watcher's Eye (2-mod) / Timeless Jewel",
            estimated_price=int(divine_rate * 3),
            priority=UpgradePriority.MEDIUM,
            reason="강력한 오라 연계 또는 키스톤 획득",
            dps_gain=20
        ))

        return upgrades

    def _get_endgame_upgrades(self, gear: Dict, divine_rate: float, gear_analysis: Dict = None) -> List[UpgradeItem]:
        """엔드게임 업그레이드 (10+ Divine)"""
        upgrades = []
        slots = gear_analysis.get("slots", {}) if gear_analysis else {}
        key_items = gear_analysis.get("key_items", []) if gear_analysis else []

        # 이미 보유한 고가 유니크의 더블 커럽션
        if key_items:
            best_item = max(key_items, key=lambda x: x.get("estimated_price", 0))
            upgrades.append(UpgradeItem(
                slot=best_item["slot"],
                current_item=best_item["name"],
                target_item=f"Double-corrupted {best_item['name']}",
                estimated_price=int(divine_rate * 15),
                priority=UpgradePriority.LOW,
                reason="더블 커럽션으로 최종 5-10% 최적화",
                dps_gain=10
            ))
        else:
            # 핵심 아이템이 없으면 무기 업그레이드 추천
            weapon_info = slots.get("Weapon 1", {})
            upgrades.append(UpgradeItem(
                slot="Weapon 1",
                current_item=weapon_info.get("name", "Empty"),
                target_item="Perfect rolled / Double-corrupted Unique",
                estimated_price=int(divine_rate * 15),
                priority=UpgradePriority.LOW,
                reason="최종 최적화 - 마지막 5-10% DPS",
                dps_gain=10
            ))

        # 어웨이큰드 젬
        upgrades.append(UpgradeItem(
            slot="Gem Upgrade",
            current_item="Level 20/21 Gem",
            target_item="Awakened Support Gems (21/23)",
            estimated_price=int(divine_rate * 5),
            priority=UpgradePriority.LOW,
            reason="젬 레벨/퀄리티 보너스로 DPS 상승",
            dps_gain=8
        ))

        # 3-mod Watcher's Eye (현재 2-mod 보유 가정)
        upgrades.append(UpgradeItem(
            slot="Jewel Socket",
            current_item="Watcher's Eye (2-mod)",
            target_item="Watcher's Eye (3-mod, perfect)",
            estimated_price=int(divine_rate * 20),
            priority=UpgradePriority.LOW,
            reason="최상위 오라 시너지",
            dps_gain=15
        ))

        return upgrades

    def analyze_build_gap(
        self,
        current_build: Dict,
        target_build: Dict
    ) -> Dict:
        """
        현재 빌드와 목표 빌드 사이의 갭 분석

        Args:
            current_build: 현재 캐릭터 데이터 (OAuth에서 가져온)
            target_build: 목표 POB 빌드 데이터

        Returns:
            갭 분석 결과
        """

        analysis = {
            "summary": "",
            "stat_gaps": [],
            "gear_gaps": [],
            "gem_gaps": [],
            "priority_upgrades": []
        }

        # 스탯 갭 분석
        stat_gaps = self._analyze_stat_gaps(current_build, target_build)
        analysis["stat_gaps"] = stat_gaps

        # 장비 갭 분석
        gear_gaps = self._analyze_gear_gaps(current_build, target_build)
        analysis["gear_gaps"] = gear_gaps

        # 젬 갭 분석
        gem_gaps = self._analyze_gem_gaps(current_build, target_build)
        analysis["gem_gaps"] = gem_gaps

        # 우선순위 정렬
        all_gaps = stat_gaps + gear_gaps + gem_gaps
        priority_gaps = sorted(all_gaps, key=lambda x: x.get('priority', 99))[:5]
        analysis["priority_upgrades"] = priority_gaps

        # 요약 생성
        analysis["summary"] = self._generate_gap_summary(stat_gaps, gear_gaps, gem_gaps)

        return analysis

    def _analyze_stat_gaps(self, current: Dict, target: Dict) -> List[Dict]:
        """스탯 갭 분석"""
        gaps = []

        # 현재 스탯
        current_stats = current.get('stats', {})
        target_stats = target.get('stats', {})

        # 생명력 체크
        current_life = current_stats.get('life', 0)
        target_life = target_stats.get('life', 0)
        if target_life > 0 and current_life < target_life * 0.8:
            gap_pct = round((1 - current_life / target_life) * 100) if target_life > 0 else 0
            gaps.append({
                "type": "stat",
                "stat": "Life",
                "current": current_life,
                "target": target_life,
                "gap_percent": gap_pct,
                "priority": 1 if gap_pct > 30 else 2,
                "suggestion": "생명력 모드가 있는 장비로 교체하거나 패시브 트리에서 Life 노드 추가"
            })

        # 저항 체크
        for res_type in ['fire', 'cold', 'lightning']:
            res_key = f'{res_type}_resistance' if 'resistance' not in res_type else res_type
            current_res = current_stats.get('resistances', {}).get(res_type, 0)

            if current_res < 75:
                gaps.append({
                    "type": "stat",
                    "stat": f"{res_type.capitalize()} Resistance",
                    "current": current_res,
                    "target": 75,
                    "gap_percent": round((75 - current_res) / 75 * 100),
                    "priority": 1,  # 저항은 항상 우선
                    "suggestion": f"{res_type.capitalize()} 저항이 있는 링/아뮬렛/벨트로 교체"
                })

        # 카오스 저항
        current_chaos = current_stats.get('resistances', {}).get('chaos', -60)
        if current_chaos < 0:
            gaps.append({
                "type": "stat",
                "stat": "Chaos Resistance",
                "current": current_chaos,
                "target": 0,
                "gap_percent": abs(current_chaos),
                "priority": 2,
                "suggestion": "Amethyst Ring 또는 카오스 저항 크래프트 추가"
            })

        return gaps

    def _analyze_gear_gaps(self, current: Dict, target: Dict) -> List[Dict]:
        """장비 갭 분석"""
        gaps = []

        # 목표 빌드의 장비
        target_stages = target.get('progression_stages', [])
        if not target_stages:
            return gaps

        target_gear = target_stages[0].get('gear_recommendation', {})

        # 현재 장비 (OAuth 데이터에서)
        current_gear = current.get('equipment', {})

        for slot, target_item in target_gear.items():
            target_name = target_item.get('name', '') if isinstance(target_item, dict) else str(target_item)
            current_name = current_gear.get(slot, {}).get('name', 'Empty')

            # 유니크 아이템 체크
            if target_name and target_name != current_name:
                is_unique = self._is_likely_unique(target_name)
                gaps.append({
                    "type": "gear",
                    "slot": slot,
                    "current": current_name,
                    "target": target_name,
                    "is_unique": is_unique,
                    "priority": 2 if is_unique else 3,
                    "suggestion": f"{slot}을 {target_name}으로 교체"
                })

        return gaps

    def _analyze_gem_gaps(self, current: Dict, target: Dict) -> List[Dict]:
        """젬 갭 분석"""
        gaps = []

        # 목표 빌드의 젬 셋업
        target_stages = target.get('progression_stages', [])
        if not target_stages:
            return gaps

        target_gems = target_stages[0].get('gem_setups', {})

        for label, setup in target_gems.items():
            links = setup.get('links', '')
            if links:
                gaps.append({
                    "type": "gem",
                    "skill": label,
                    "setup": links,
                    "priority": 3,
                    "suggestion": f"{label} 젬 링크 확인: {links}"
                })

        return gaps

    def _generate_gap_summary(
        self,
        stat_gaps: List[Dict],
        gear_gaps: List[Dict],
        gem_gaps: List[Dict]
    ) -> str:
        """갭 분석 요약 생성"""

        critical_issues = [g for g in stat_gaps if g.get('priority') == 1]

        if critical_issues:
            res_issues = [g for g in critical_issues if 'Resistance' in g.get('stat', '')]
            life_issues = [g for g in critical_issues if 'Life' in g.get('stat', '')]

            summary_parts = []
            if res_issues:
                summary_parts.append(f"저항 부족 ({len(res_issues)}개)")
            if life_issues:
                summary_parts.append("생명력 부족")

            return f"긴급: {', '.join(summary_parts)} - 먼저 해결 필요"

        if gear_gaps:
            unique_gaps = [g for g in gear_gaps if g.get('is_unique')]
            if unique_gaps:
                return f"핵심 유니크 {len(unique_gaps)}개 미확보 - 빌드 완성도 향상 필요"

        return "기본 스탯 충족 - 최적화 단계 진행 가능"

    def _is_likely_unique(self, item_name: str) -> bool:
        """유니크 아이템인지 추측"""
        # 일반적인 유니크 아이템 패턴
        unique_patterns = [
            "Aegis", "Skin of", "Shavro", "Headhunter", "Mageblood",
            "Atziri", "Badge", "Cospri", "Farrul", "Bottled Faith",
            "Thread of Hope", "Watcher's Eye", "Inspired Learning",
            "Nebulis", "Surrender", "Replica", "Forbidden", "Impossible",
            "Nimis", "Original Sin", "Melding", "Ashes of the Stars"
        ]
        return any(pattern.lower() in item_name.lower() for pattern in unique_patterns)

    def _analyze_current_gear(self, gear: Dict) -> Dict:
        """현재 장비 분석 - 유니크/레어 구분 및 가치 평가"""
        analysis = {
            "slots": {},
            "unique_count": 0,
            "rare_count": 0,
            "empty_count": 0,
            "estimated_value": 0,
            "key_items": []
        }

        # poe.ninja에서 실제 가격 가져오기 (캐시 사용)
        ninja_prices = {}
        if self.ninja_api:
            try:
                # 캐시된 가격 데이터 사용 (타임아웃 없음)
                ninja_prices = self.ninja_api.get_all_unique_prices()
            except Exception as e:
                print(f"[WARN] Failed to load ninja prices: {e}", file=sys.stderr)

        # 폴백용 기본 가격 (poe.ninja 실패 시)
        fallback_prices = {
            "skin of the lords": 50,
            "skin of the loyal": 10,
            "nebulis": 5,
            "aegis aurora": 200,
            "mageblood": 50000,
            "headhunter": 8000,
            "ashes of the stars": 3000,
            "melding of the flesh": 100,
            "forbidden flame": 500,
            "forbidden flesh": 500,
            "watcher's eye": 100,
            "thread of hope": 50,
            "the surrender": 30,
            "replica dreamfeather": 100,
            "doryani's prototype": 50,
            "crystallised omniscience": 100,
        }

        for slot, item_data in gear.items():
            if isinstance(item_data, dict):
                item_name = item_data.get('name', 'Empty')
                rarity = item_data.get('rarity', 'Unknown')
                sockets = item_data.get('sockets', '')
                mods = item_data.get('mods', [])
            else:
                item_name = str(item_data)
                rarity = 'Unknown'
                sockets = ''
                mods = []

            if not item_name or item_name.lower() in ['empty', 'none', '']:
                analysis["empty_count"] += 1
                analysis["slots"][slot] = {"name": "Empty", "type": "empty", "estimated_price": 0, "sockets": "", "mods": []}
                continue

            # 유니크 여부 판단 - rarity 필드가 있으면 우선 사용
            if rarity == "Unique":
                is_unique = True
            elif rarity in ["Rare", "Magic", "Normal"]:
                is_unique = False
            else:
                is_unique = self._is_likely_unique(item_name)

            # 가격 추정
            estimated_price = 1  # 기본 레어 가격
            if is_unique:
                analysis["unique_count"] += 1

                # 1. poe.ninja에서 실제 가격 검색 (이미 chaos 단위)
                found_price = False
                item_name_lower = item_name.lower()

                for ninja_name, ninja_price in ninja_prices.items():
                    # 아이템 이름이 포함되어 있는지 확인
                    if item_name_lower in ninja_name or ninja_name in item_name_lower:
                        # ninja_prices는 이미 chaos 단위
                        estimated_price = int(ninja_price)
                        found_price = True
                        break

                # 2. poe.ninja에서 못 찾으면 폴백 가격 사용
                if not found_price:
                    for fallback_key, fallback_price in fallback_prices.items():
                        if fallback_key in item_name_lower:
                            estimated_price = fallback_price
                            found_price = True
                            break

                # 3. 그래도 못 찾으면 기본값
                if not found_price:
                    estimated_price = 20  # 알 수 없는 유니크 기본값

                # 핵심 아이템 기록
                if estimated_price >= 50:
                    analysis["key_items"].append({
                        "slot": slot,
                        "name": item_name,
                        "estimated_price": estimated_price,
                        "mods": mods[:5]  # 핵심 모드 5개까지
                    })
            else:
                analysis["rare_count"] += 1
                # 레어 아이템 가치 추정 (슬롯별)
                if slot in ["Weapon 1", "Body Armour"]:
                    estimated_price = 20
                elif slot in ["Helmet", "Gloves", "Boots"]:
                    estimated_price = 10
                else:
                    estimated_price = 5

            analysis["slots"][slot] = {
                "name": item_name,
                "type": "unique" if is_unique else "rare",
                "estimated_price": estimated_price,
                "sockets": sockets,
                "mods": mods
            }
            analysis["estimated_value"] += estimated_price

        return analysis

    def _upgrade_to_dict(self, upgrade: UpgradeItem, divine_rate: float) -> Dict:
        """UpgradeItem을 딕셔너리로 변환"""
        return {
            "slot": upgrade.slot,
            "current_item": upgrade.current_item,
            "target_item": upgrade.target_item,
            "estimated_price": upgrade.estimated_price,
            "price_formatted": self._format_budget(upgrade.estimated_price, divine_rate),
            "priority": upgrade.priority.name,
            "priority_value": upgrade.priority.value,
            "reason": upgrade.reason,
            "dps_gain_percent": upgrade.dps_gain,
            "ehp_gain": upgrade.ehp_gain
        }

    def _format_budget(self, chaos_value: int, divine_rate: float) -> str:
        """예산을 읽기 좋은 형식으로 변환"""
        if chaos_value >= divine_rate:
            divine = chaos_value / divine_rate
            if divine >= 10:
                return f"{int(divine)}d"
            else:
                return f"{divine:.1f}d"
        else:
            return f"{chaos_value}c"


def main():
    """테스트 실행"""
    import argparse
    from pob_parser import get_pob_code_from_url, decode_pob_code, parse_pob_xml

    parser = argparse.ArgumentParser(description='Build Guide System')
    parser.add_argument('--pob', type=str, help='POB URL to analyze')
    parser.add_argument('--budget', type=int, default=1000, help='Target budget in chaos')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    if not args.pob:
        print("[ERROR] --pob is required", file=sys.stderr)
        sys.exit(1)

    # POB 데이터 로드
    pob_code = get_pob_code_from_url(args.pob)
    if not pob_code:
        print("[ERROR] Could not fetch POB code", file=sys.stderr)
        sys.exit(1)

    if pob_code.startswith("__XML_DIRECT__"):
        xml_data = pob_code[14:]
    else:
        xml_data = decode_pob_code(pob_code)
        if not xml_data:
            print("[ERROR] Could not decode POB data", file=sys.stderr)
            sys.exit(1)

    build_data = parse_pob_xml(xml_data, args.pob)
    if not build_data:
        print("[ERROR] Could not parse POB XML", file=sys.stderr)
        sys.exit(1)

    # 가이드 시스템 실행
    guide_system = BuildGuideSystem()
    roadmap = guide_system.generate_upgrade_roadmap(
        build_data,
        current_budget=0,
        target_budget=args.budget
    )

    if args.json:
        print(json.dumps(roadmap, ensure_ascii=False, indent=2))
    else:
        # 텍스트 출력
        print("=" * 80)
        print(f"BUILD UPGRADE ROADMAP: {roadmap['build_name']}")
        print("=" * 80)
        print(f"Divine Rate: {roadmap['divine_rate']}c")
        print(f"Target Budget: {args.budget}c")
        print()

        for tier in roadmap['tiers']:
            print("-" * 80)
            print(f"[{tier['tier_name']}] {tier['budget_range']}")
            print(f"Total Cost: {tier['total_cost_formatted']}")
            print("-" * 80)

            for i, upgrade in enumerate(tier['upgrades'], 1):
                print(f"\n  {i}. [{upgrade['priority']}] {upgrade['slot']}")
                print(f"     현재: {upgrade['current_item']}")
                print(f"     목표: {upgrade['target_item']}")
                print(f"     가격: {upgrade['price_formatted']}")
                print(f"     이유: {upgrade['reason']}")
                if upgrade['dps_gain_percent']:
                    print(f"     예상 DPS 증가: +{upgrade['dps_gain_percent']}%")
                if upgrade['ehp_gain']:
                    print(f"     예상 EHP 증가: +{upgrade['ehp_gain']}")

            print()


if __name__ == "__main__":
    main()
