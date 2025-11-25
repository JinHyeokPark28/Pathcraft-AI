#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Farming Strategy System
빌드 특성에 따른 맵핑/파밍 전략 추천
"""

import sys
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, field

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


@dataclass
class MapInfo:
    """맵 정보"""
    name: str
    tier: int
    layout_rating: str  # S, A, B, C, D
    density: str  # high, medium, low
    boss_difficulty: str  # easy, medium, hard
    div_cards: List[str] = field(default_factory=list)
    special_drops: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)  # indoor, outdoor, linear, open, etc.


@dataclass
class FarmingStrategy:
    """파밍 전략"""
    name: str
    description: str
    required_investment: str  # low, medium, high
    expected_returns: str  # low, medium, high, very_high
    build_requirements: List[str] = field(default_factory=list)
    recommended_maps: List[str] = field(default_factory=list)
    atlas_passives: List[str] = field(default_factory=list)
    tips: List[str] = field(default_factory=list)


class FarmingStrategySystem:
    """파밍 전략 시스템"""

    # POE 2에서 업데이트 필요 - 현재는 POE 1 기준 예시
    MAP_DATABASE = {
        # Tier 1-5 (Early Maps)
        "Strand": MapInfo(
            name="Strand",
            tier=2,
            layout_rating="S",
            density="high",
            boss_difficulty="easy",
            div_cards=["The Nurse", "The Doctor"],
            tags=["outdoor", "linear", "beach"]
        ),
        "Glacier": MapInfo(
            name="Glacier",
            tier=2,
            layout_rating="A",
            density="high",
            boss_difficulty="easy",
            div_cards=["The Brittle Emperor"],
            tags=["outdoor", "open", "legion"]
        ),
        "Alleyways": MapInfo(
            name="Alleyways",
            tier=3,
            layout_rating="A",
            density="medium",
            boss_difficulty="easy",
            div_cards=["Saint's Treasure"],
            tags=["indoor", "linear"]
        ),

        # Tier 6-10 (Mid Maps)
        "Tower": MapInfo(
            name="Tower",
            tier=7,
            layout_rating="A",
            density="high",
            boss_difficulty="medium",
            div_cards=["The Nurse", "The Doctor"],
            tags=["indoor", "linear", "tower"]
        ),
        "Crimson Temple": MapInfo(
            name="Crimson Temple",
            tier=8,
            layout_rating="S",
            density="high",
            boss_difficulty="easy",
            div_cards=["Apothecary", "Seven Years Bad Luck"],
            tags=["indoor", "linear"]
        ),
        "Cemetery": MapInfo(
            name="Cemetery",
            tier=6,
            layout_rating="A",
            density="high",
            boss_difficulty="easy",
            div_cards=["The Doctor"],
            tags=["outdoor", "open"]
        ),

        # Tier 11-16 (High Tier)
        "Jungle Valley": MapInfo(
            name="Jungle Valley",
            tier=11,
            layout_rating="S",
            density="very_high",
            boss_difficulty="medium",
            div_cards=["The Apothecary"],
            tags=["outdoor", "linear", "jungle"]
        ),
        "Dunes": MapInfo(
            name="Dunes",
            tier=12,
            layout_rating="S",
            density="high",
            boss_difficulty="easy",
            div_cards=["Brother's Stash"],
            tags=["outdoor", "open", "desert"]
        ),
        "Underground Sea": MapInfo(
            name="Underground Sea",
            tier=13,
            layout_rating="A",
            density="very_high",
            boss_difficulty="medium",
            div_cards=["The Nurse"],
            tags=["indoor", "open", "water"]
        ),
        "Defiled Cathedral": MapInfo(
            name="Defiled Cathedral",
            tier=14,
            layout_rating="A",
            density="high",
            boss_difficulty="hard",
            div_cards=["The Fiend", "The Doctor"],
            tags=["indoor", "linear"]
        ),
    }

    # 파밍 전략 데이터베이스
    STRATEGY_DATABASE = {
        "essence_farming": FarmingStrategy(
            name="Essence Farming",
            description="에센스 수집 및 판매 전략",
            required_investment="low",
            expected_returns="medium",
            build_requirements=["clear_speed"],
            recommended_maps=["Strand", "Glacier", "Cemetery"],
            atlas_passives=[
                "Essence Extraction",
                "Crystal Resonance",
                "Amplified Energies"
            ],
            tips=[
                "Remnant of Corruption으로 고급 에센스 업그레이드",
                "Deafening 에센스가 가장 가치있음",
                "빠른 클리어 속도가 중요"
            ]
        ),
        "expedition_farming": FarmingStrategy(
            name="Expedition Farming",
            description="탐험 콘텐츠 집중 파밍",
            required_investment="medium",
            expected_returns="high",
            build_requirements=["single_target", "tankiness"],
            recommended_maps=["Crimson Temple", "Dunes", "Cemetery"],
            atlas_passives=[
                "Buried Knowledge",
                "Ancient Writings",
                "Expedition Specialist"
            ],
            tips=[
                "Logbooks가 주요 수입원",
                "Tujen과 Rog 거래 활용",
                "큰 Remnant 체인 만들기"
            ]
        ),
        "legion_farming": FarmingStrategy(
            name="Legion Farming",
            description="군단 전투 집중 파밍",
            required_investment="low",
            expected_returns="medium",
            build_requirements=["clear_speed", "aoe"],
            recommended_maps=["Glacier", "Dunes", "Cemetery"],
            atlas_passives=[
                "Monumental",
                "Face of the Monolith",
                "War Supplies"
            ],
            tips=[
                "전체 군단 해방이 목표",
                "Timeless Emblems 수집",
                "Incubators 판매"
            ]
        ),
        "delirium_farming": FarmingStrategy(
            name="Delirium Farming",
            description="환영 콘텐츠 집중 파밍",
            required_investment="high",
            expected_returns="very_high",
            build_requirements=["tankiness", "sustain", "clear_speed"],
            recommended_maps=["Crimson Temple", "Tower", "Underground Sea"],
            atlas_passives=[
                "Perseverance",
                "Delirious",
                "Descent into Madness"
            ],
            tips=[
                "높은 생존력 필요",
                "Simulacrum Splinters 수집",
                "Delirium Orbs로 맵 강화"
            ]
        ),
        "breach_farming": FarmingStrategy(
            name="Breach Farming",
            description="균열 콘텐츠 집중 파밍",
            required_investment="medium",
            expected_returns="medium",
            build_requirements=["clear_speed", "aoe"],
            recommended_maps=["Strand", "Dunes", "Cemetery"],
            atlas_passives=[
                "Flash Breach",
                "Breach Specialist",
                "Torn Veil"
            ],
            tips=[
                "Breachstones가 주요 수입원",
                "빠른 몬스터 처치가 핵심",
                "Chayula Breachstone이 가장 가치있음"
            ]
        ),
        "harbinger_farming": FarmingStrategy(
            name="Harbinger Farming",
            description="선구자 콘텐츠 집중 파밍",
            required_investment="low",
            expected_returns="medium",
            build_requirements=["single_target"],
            recommended_maps=["Tower", "Strand", "Alleyways"],
            atlas_passives=[
                "Titled Expectations",
                "The Price is Right",
                "Harbinger Specialist"
            ],
            tips=[
                "Ancient Orbs 수집",
                "Harbinger Orbs로 맵 업그레이드",
                "Beachhead 맵 경험치 파밍"
            ]
        ),
        "div_card_farming": FarmingStrategy(
            name="Divination Card Farming",
            description="고가 디비네이션 카드 타겟 파밍",
            required_investment="high",
            expected_returns="very_high",
            build_requirements=["clear_speed", "sustain"],
            recommended_maps=["Crimson Temple", "Tower", "Defiled Cathedral"],
            atlas_passives=[
                "Tamper-Proof",
                "Priceless Bounty",
                "Fortune Favors"
            ],
            tips=[
                "The Apothecary - Crimson Temple",
                "The Doctor - Tower/Strand",
                "Brother's Stash - Dunes",
                "높은 Quantity/Rarity 필요"
            ]
        ),
        "boss_farming": FarmingStrategy(
            name="Boss Farming",
            description="엔드게임 보스 킬 전략",
            required_investment="very_high",
            expected_returns="very_high",
            build_requirements=["single_target", "tankiness", "boss_dps"],
            recommended_maps=["Any T16"],
            atlas_passives=[
                "Shaping the World",
                "Guardian's Aid",
                "Map Boss Specialist"
            ],
            tips=[
                "Maven's Invitation 수집",
                "Uber Boss 도전",
                "Fragment 세트 완성",
                "높은 보스 DPS 필요 (최소 10M+)"
            ]
        ),
    }

    def __init__(self):
        pass

    def get_map_info(self, map_name: str) -> Optional[MapInfo]:
        """맵 정보 가져오기"""
        return self.MAP_DATABASE.get(map_name)

    def get_strategy(self, strategy_name: str) -> Optional[FarmingStrategy]:
        """전략 정보 가져오기"""
        return self.STRATEGY_DATABASE.get(strategy_name)

    def get_all_strategies(self) -> Dict[str, FarmingStrategy]:
        """모든 전략 가져오기"""
        return self.STRATEGY_DATABASE

    def recommend_strategies_for_build(self, build_tags: List[str], budget: str = "medium") -> List[Dict]:
        """빌드 특성에 맞는 전략 추천"""
        recommendations = []

        for strategy_name, strategy in self.STRATEGY_DATABASE.items():
            # 빌드 요구사항 체크
            match_score = 0
            for req in strategy.required_investment_reqs if hasattr(strategy, 'required_investment_reqs') else strategy.build_requirements:
                if req in build_tags:
                    match_score += 1

            # 투자 비용 체크
            investment_order = ["low", "medium", "high", "very_high"]
            budget_index = investment_order.index(budget) if budget in investment_order else 1
            strategy_index = investment_order.index(strategy.required_investment) if strategy.required_investment in investment_order else 2

            if strategy_index <= budget_index + 1:  # 예산 ±1 허용
                recommendations.append({
                    "strategy": strategy_name,
                    "name": strategy.name,
                    "description": strategy.description,
                    "match_score": match_score,
                    "investment": strategy.required_investment,
                    "returns": strategy.expected_returns,
                    "suitable": match_score >= len(strategy.build_requirements) // 2
                })

        # 매치 점수로 정렬
        recommendations.sort(key=lambda x: (-x["match_score"], x["investment"]))
        return recommendations[:5]

    def get_recommended_maps_for_strategy(self, strategy_name: str) -> List[Dict]:
        """전략에 맞는 맵 추천"""
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            return []

        maps = []
        for map_name in strategy.recommended_maps:
            map_info = self.get_map_info(map_name)
            if map_info:
                maps.append({
                    "name": map_info.name,
                    "tier": map_info.tier,
                    "layout": map_info.layout_rating,
                    "density": map_info.density,
                    "div_cards": map_info.div_cards[:3]
                })

        return maps

    def generate_farming_guide(self, build_info: Dict) -> Dict:
        """빌드 정보로 파밍 가이드 생성"""
        # 빌드 태그 추출
        build_tags = []

        # DPS 기반 태그
        dps = build_info.get("dps", 0)
        if dps >= 10000000:  # 10M+
            build_tags.extend(["boss_dps", "single_target"])
        if dps >= 1000000:  # 1M+
            build_tags.append("clear_speed")

        # 스킬 태그 기반
        skill_tags = build_info.get("skill_tags", [])
        if "aoe" in skill_tags:
            build_tags.append("aoe")
        if "minion" in skill_tags:
            build_tags.append("minion")
        if "dot" in skill_tags:
            build_tags.append("dot")

        # 방어 태그
        ehp = build_info.get("ehp", 0)
        if ehp >= 50000:
            build_tags.append("tankiness")
        life_regen = build_info.get("life_regen", 0)
        if life_regen >= 500:
            build_tags.append("sustain")

        # 클리어 스피드 태그 (속성 기반)
        if "projectile" in skill_tags or "chaining" in skill_tags:
            build_tags.append("clear_speed")
        if "brand" in skill_tags:
            build_tags.extend(["clear_speed", "aoe"])

        # 예산 추정
        budget = build_info.get("budget", "medium")

        # 전략 추천
        strategies = self.recommend_strategies_for_build(build_tags, budget)

        # 가이드 생성
        guide = {
            "build_tags": list(set(build_tags)),
            "budget": budget,
            "recommended_strategies": [],
            "atlas_setup": [],
            "general_tips": []
        }

        # 상위 3개 전략 상세 정보
        for rec in strategies[:3]:
            strategy = self.get_strategy(rec["strategy"])
            if strategy:
                guide["recommended_strategies"].append({
                    "name": strategy.name,
                    "description": strategy.description,
                    "investment": strategy.required_investment,
                    "returns": strategy.expected_returns,
                    "maps": self.get_recommended_maps_for_strategy(rec["strategy"]),
                    "atlas_passives": strategy.atlas_passives,
                    "tips": strategy.tips
                })

                # Atlas 패시브 수집
                guide["atlas_setup"].extend(strategy.atlas_passives)

        # 중복 제거
        guide["atlas_setup"] = list(set(guide["atlas_setup"]))[:10]

        # 일반 팁
        guide["general_tips"] = [
            "맵 퀀티티/레어리티를 높이면 수익 증가",
            "Chisel + Alch + Vaal로 맵 강화",
            "Sextants로 추가 콘텐츠 활성화",
            "Scarabs로 타겟 콘텐츠 추가",
            "Kirac missions 활용"
        ]

        return guide


def analyze_build_for_farming(pob_data: Dict) -> Dict:
    """POB 데이터로 파밍 전략 분석"""
    system = FarmingStrategySystem()

    # POB에서 빌드 정보 추출
    build_info = {
        "dps": pob_data.get("dps", 0),
        "ehp": pob_data.get("ehp", 0),
        "life_regen": pob_data.get("life_regen", 0),
        "skill_tags": pob_data.get("skill_tags", []),
        "budget": pob_data.get("budget", "medium")
    }

    return system.generate_farming_guide(build_info)


def get_league_meta_strategies(version: str = "3.27") -> Dict:
    """특정 리그의 메타 전략 가져오기 (farming_meta_crawler 연동)"""
    try:
        from farming_meta_crawler import FarmingMetaManager
        manager = FarmingMetaManager()

        strategies = manager.get_strategies_by_league(version)
        league_info = manager.league_info.get(version)

        if not strategies:
            return {"error": f"No strategies found for version {version}"}

        result = {
            "version": version,
            "league_name": league_info.name if league_info else "Unknown",
            "league_name_ko": league_info.name_ko if league_info else "알 수 없음",
            "strategies": []
        }

        for strategy in strategies:
            result["strategies"].append({
                "name": strategy.name,
                "name_ko": strategy.name_ko,
                "tier": strategy.tier,
                "investment": strategy.investment,
                "returns": strategy.returns,
                "profit_per_hour": strategy.profit_per_hour,
                "tips_ko": strategy.tips_ko,
                "recommended_maps": strategy.recommended_maps,
                "build_requirements": strategy.build_requirements
            })

        return result
    except ImportError:
        return {"error": "farming_meta_crawler module not found"}


def get_recommended_strategies_for_build_v2(build_tags: List[str], budget: str = "medium") -> List[Dict]:
    """빌드에 맞는 전략 추천 v2 (모든 리그 데이터 사용)"""
    try:
        from farming_meta_crawler import FarmingMetaManager
        manager = FarmingMetaManager()

        recommendations = manager.get_strategies_for_build(build_tags, budget)

        return [{
            "version": rec["version"],
            "name": rec["strategy"].name,
            "name_ko": rec["strategy"].name_ko,
            "tier": rec["strategy"].tier,
            "investment": rec["strategy"].investment,
            "returns": rec["strategy"].returns,
            "profit_per_hour": rec["strategy"].profit_per_hour,
            "match_score": rec["match_score"],
            "suitable": rec["suitable"]
        } for rec in recommendations]
    except ImportError:
        return []


def get_personalized_farming_guide(pob_data: Dict) -> Dict:
    """POB 데이터로 맞춤형 파밍 가이드 생성 (알케앤고 + 전략 파밍 포함)

    Args:
        pob_data: POB에서 추출한 빌드 데이터
            - dps: 총 DPS
            - ehp: Effective HP
            - life_regen: 생명력 재생
            - skill_tags: 스킬 태그 목록
            - main_skill: 메인 스킬 이름
            - budget: 예산 (low/medium/high)

    Returns:
        맞춤형 파밍 가이드
    """
    try:
        from farming_meta_crawler import FarmingMetaManager
        manager = FarmingMetaManager()

        # 빌드 스펙 추출
        dps = pob_data.get("dps", 0)
        ehp = pob_data.get("ehp", 0)
        skill_tags = pob_data.get("skill_tags", [])
        main_skill = pob_data.get("main_skill", "Unknown")
        budget = pob_data.get("budget", "medium")

        # 클리어 속도 추정
        clear_speed = "medium"
        if "projectile" in skill_tags or "chaining" in skill_tags or "aoe" in skill_tags:
            if dps >= 10000000:
                clear_speed = "very_fast"
            elif dps >= 5000000:
                clear_speed = "fast"
        elif "minion" in skill_tags:
            clear_speed = "medium"
        elif "single_target" in skill_tags or "boss" in skill_tags:
            clear_speed = "slow"

        # 빌드 파워 기반 추천
        power_recommendations = manager.get_strategies_by_build_power(dps, ehp, clear_speed)

        # 결과 구성
        result = {
            "build_summary": {
                "main_skill": main_skill,
                "dps": dps,
                "ehp": ehp,
                "clear_speed": clear_speed,
                "build_power": power_recommendations["build_power"],
                "recommended_tier": power_recommendations["recommended_tier"]
            },
            "alch_and_go": {
                "description": "알케미 앤 고 (Alch & Go) - 저투자 고효율 전략",
                "suitable": True,
                "maps": [],
                "tips": [],
                "expected_profit": ""
            },
            "strategic_farming": {
                "description": "전략 파밍 - 특화 콘텐츠 집중",
                "main_strategies": [],
                "combinations": []
            },
            "warnings": [],
            "general_tips": power_recommendations["tips"]
        }

        # 알케앤고 적합성 평가 (DPS 또는 EHP 기준 완화 - Glass Cannon 허용)
        # 기본: 1M+ DPS AND 15k+ EHP
        # Glass Cannon: 5M+ DPS AND 3k+ EHP
        alch_suitable = (dps >= 1000000 and ehp >= 15000) or (dps >= 5000000 and ehp >= 3000)

        if alch_suitable:
            result["alch_and_go"]["suitable"] = True

            # 낮은 EHP 경고 추가
            if ehp < 10000:
                result["warnings"].append("⚠️ EHP가 낮습니다. 알케앤고 시 사망 주의 - 방어력 업그레이드 권장")

            # 클리어 속도에 따른 맵 추천
            if clear_speed in ["fast", "very_fast"]:
                result["alch_and_go"]["maps"] = [
                    {"name": "Jungle Valley", "name_ko": "정글 계곡", "reason": "보스 없이 제단 파밍, 미니언 제단 최적"},
                    {"name": "Mesa", "name_ko": "메사", "reason": "리니어 레이아웃, 빠른 클리어"},
                    {"name": "Strand", "name_ko": "해변", "reason": "직선 레이아웃, S티어"},
                    {"name": "Dunes", "name_ko": "사구", "reason": "오픈 레이아웃, 군단에 최적"}
                ]
                result["alch_and_go"]["tips"] = [
                    "신성 제단(Divine Altar)이 주요 수입원",
                    "빠른 진입/퇴장으로 시간당 맵 수 극대화",
                    "맵 퀀티티보다 속도가 중요",
                    "Exarch/Eater 영향력 유지"
                ]
                result["alch_and_go"]["expected_profit"] = "3-7 Divine/hour"
            elif clear_speed == "medium":
                result["alch_and_go"]["maps"] = [
                    {"name": "Cemetery", "name_ko": "묘지", "reason": "밀도 높음, 적당한 레이아웃"},
                    {"name": "Glacier", "name_ko": "빙하", "reason": "군단 파밍에 좋음"},
                    {"name": "Alleyways", "name_ko": "골목길", "reason": "리니어, 안정적"}
                ]
                result["alch_and_go"]["tips"] = [
                    "제단 + 에센스 조합 추천",
                    "맵 퀀티티 60%+ 유지",
                    "Chisel + Alch 기본"
                ]
                result["alch_and_go"]["expected_profit"] = "2-5 Divine/hour"
            else:
                result["alch_and_go"]["suitable"] = False
                result["alch_and_go"]["tips"] = [
                    "클리어 속도가 느려 알케앤고 비추천",
                    "보스 킬이나 로그북 파밍 추천"
                ]
                result["alch_and_go"]["expected_profit"] = "비추천"
        else:
            result["alch_and_go"]["suitable"] = False
            result["alch_and_go"]["tips"] = [
                "빌드 파워 부족 - 장비 업그레이드 필요",
                "강탈(Heist)이나 저티어 에센스 파밍 추천"
            ]

        # 전략 파밍 추천
        main_strategies = power_recommendations["strategies"]["main"]
        for strategy in main_strategies[:3]:
            # 조합 정보 가져오기
            combo_info = manager.get_strategy_combinations(strategy["name"], budget)

            strategy_info = {
                "name": strategy["name"],
                "name_ko": strategy["name_ko"],
                "tier": strategy["tier"],
                "profit_per_hour": strategy["profit_per_hour"],
                "investment": strategy["investment"],
                "tips": strategy["tips_ko"],
                "best_combos": []
            }

            # 조합 정보 추가
            if "combinations" in combo_info:
                for combo in combo_info["combinations"][:2]:
                    strategy_info["best_combos"].append(combo.get("name_ko", combo.get("name", "")))

            result["strategic_farming"]["main_strategies"].append(strategy_info)

        # 전체 조합 추천
        if main_strategies:
            top_strategy = main_strategies[0]["name"]
            combo_result = manager.get_strategy_combinations(top_strategy, budget)
            if "full_setup" in combo_result:
                result["strategic_farming"]["combinations"] = {
                    "primary": top_strategy,
                    "scarabs": combo_result["full_setup"].get("scarabs", []),
                    "atlas_focus": combo_result["full_setup"].get("atlas_focus", ""),
                    "estimated_profit": combo_result.get("estimated_profit", "")
                }

        # 피해야 할 전략
        avoid_strategies = power_recommendations["strategies"]["avoid"]
        if avoid_strategies:
            result["warnings"].append(f"⚠️ 현재 빌드로 피해야 할 전략: {', '.join(avoid_strategies[:3])}")

        # 빌드 파워 경고
        if power_recommendations["recommended_tier"] in ["Beginner", "B"]:
            result["warnings"].append("💡 빌드 파워가 낮습니다. 장비 업그레이드 후 고수익 전략 도전 추천")

        return result

    except ImportError as e:
        return {"error": f"farming_meta_crawler 모듈을 찾을 수 없음: {e}"}
    except Exception as e:
        return {"error": f"파밍 가이드 생성 실패: {e}"}


def get_farming_guide_from_pob_url(pob_url: str, budget: str = "medium") -> Dict:
    """POB URL에서 직접 파밍 가이드 생성

    Args:
        pob_url: POB URL (pobb.in, pastebin.com) 또는 POB 코드
        budget: 예산 수준 (low/medium/high)

    Returns:
        맞춤형 파밍 가이드
    """
    try:
        # pob_parser 임포트
        import pob_parser
        from skill_tag_system import SkillTagSystem

        # 스킬 태그 시스템 초기화
        skill_system = SkillTagSystem()

        # POB URL에서 코드 가져오기
        if pob_url.startswith(('http://', 'https://')):
            pob_code = pob_parser.get_pob_code_from_url(pob_url)
        else:
            # 직접 POB 코드가 입력된 경우
            pob_code = pob_url

        if not pob_code:
            return {"error": "POB 데이터를 가져올 수 없습니다"}

        # XML 직접 로드 체크
        if pob_code.startswith("__XML_DIRECT__"):
            xml_string = pob_code[14:]
        else:
            xml_string = pob_parser.decode_pob_code(pob_code)

        if not xml_string:
            return {"error": "POB 코드 디코딩 실패"}

        # XML 파싱하여 빌드 데이터 추출
        build_data = pob_parser.parse_pob_xml(xml_string, pob_url)
        if not build_data:
            return {"error": "POB XML 파싱 실패"}

        # 메인 스킬 찾기 (오라/버프 젬 제외)
        main_skill = "Unknown"
        gem_setups = build_data.get("progression_stages", [{}])[0].get("gem_setups", {})

        # 오라/버프/저주/이동기 젬 목록 (메인 스킬로 선택하지 않음)
        non_main_skills = {
            # 오라
            "Grace", "Determination", "Hatred", "Anger", "Wrath", "Malevolence",
            "Zealotry", "Pride", "Discipline", "Clarity", "Vitality", "Purity of Fire",
            "Purity of Ice", "Purity of Lightning", "Purity of Elements", "Haste",
            "Precision", "Herald of Ice", "Herald of Thunder", "Herald of Ash",
            "Herald of Agony", "Herald of Purity", "Blood and Sand", "Flesh and Stone",
            "Defiance Banner", "War Banner", "Dread Banner", "Petrified Blood",
            "Tempest Shield", "Arctic Armour",
            # 방어기
            "Immortal Call", "Steelskin", "Molten Shell", "Vaal Molten Shell",
            "Cast when Damage Taken", "Bone Armour", "Vaal Grace", "Vaal Discipline",
            # 이동기
            "Flame Dash", "Shield Charge", "Leap Slam", "Whirling Blades", "Blink Arrow",
            "Dash", "Frostblink", "Lightning Warp", "Smoke Mine", "Portal",
            # 저주
            "Frostbite", "Enfeeble", "Temporal Chains", "Vulnerability", "Despair",
            "Punishment", "Elemental Weakness", "Flammability", "Conductivity",
            "Projectile Weakness", "Assassin's Mark", "Warlord's Mark", "Poacher's Mark",
            "Sniper's Mark", "Mark of Submission",
            # 버프/유틸
            "Blood Rage", "Berserk", "Vaal Haste", "Phase Run", "Withering Step",
            "Enduring Cry", "Rallying Cry", "Intimidating Cry", "Ancestral Cry",
            "Seismic Cry", "General's Cry", "Vaal Righteous Fire",
            # 서포트 젬
            "Enlighten", "Empower", "Enhance"
        }

        if gem_setups:
            # 유틸리티가 아닌 첫 번째 스킬을 메인 스킬로
            for skill_name in gem_setups.keys():
                if skill_name not in non_main_skills:
                    main_skill = skill_name
                    break

            # 모든 젬이 유틸리티인 경우 첫 번째 스킬 사용
            if main_skill == "Unknown" and gem_setups:
                main_skill = list(gem_setups.keys())[0]

        # 스킬 태그 가져오기
        skill_tags = []
        try:
            skill_info = skill_system.SKILL_DATABASE.get(main_skill)
            if skill_info:
                skill_tags = skill_info.tags
        except:
            # 기본 태그 추정
            pass

        # stats에서 DPS/EHP 추출
        stats = build_data.get("stats", {})
        dps = stats.get("dps", 0)
        life = stats.get("life", 0)
        es = stats.get("energy_shield", 0)
        ehp = stats.get("ehp", 0) or (life + es)

        # 빌드 데이터 구성
        pob_data = {
            "dps": dps,
            "ehp": ehp,
            "skill_tags": skill_tags,
            "main_skill": main_skill,
            "budget": budget
        }

        # 파밍 가이드 생성
        result = get_personalized_farming_guide(pob_data)

        # 빌드 메타 정보 추가
        meta = build_data.get("meta", {})
        result["build_info"] = {
            "name": meta.get("build_name", "Unknown Build"),
            "class": meta.get("class", "Unknown"),
            "ascendancy": meta.get("ascendancy", "Unknown"),
            "pob_url": pob_url
        }

        return result

    except Exception as e:
        import traceback
        return {"error": f"파밍 가이드 생성 실패: {str(e)}", "traceback": traceback.format_exc()}


def main():
    """테스트"""
    print("=" * 80)
    print("Farming Strategy System Test")
    print("=" * 80)
    print()

    system = FarmingStrategySystem()

    # Brand 빌드 테스트
    test_build = {
        "dps": 5000000,
        "ehp": 40000,
        "life_regen": 800,
        "skill_tags": ["spell", "aoe", "brand", "lightning"],
        "budget": "medium"
    }

    print("Test Build:")
    print(f"  DPS: {test_build['dps']:,}")
    print(f"  EHP: {test_build['ehp']:,}")
    print(f"  Tags: {', '.join(test_build['skill_tags'])}")
    print()

    guide = system.generate_farming_guide(test_build)

    print("Build Tags Identified:", ", ".join(guide["build_tags"]))
    print()

    print("=" * 80)
    print("RECOMMENDED STRATEGIES")
    print("=" * 80)
    print()

    for i, strategy in enumerate(guide["recommended_strategies"], 1):
        print(f"{i}. {strategy['name']}")
        print(f"   {strategy['description']}")
        print(f"   Investment: {strategy['investment']} | Returns: {strategy['returns']}")
        print()

        print("   Recommended Maps:")
        for map_info in strategy["maps"]:
            cards = ", ".join(map_info["div_cards"]) if map_info["div_cards"] else "None"
            print(f"     - {map_info['name']} (T{map_info['tier']}, {map_info['layout']}) - Cards: {cards}")
        print()

        print("   Atlas Passives:")
        for passive in strategy["atlas_passives"]:
            print(f"     - {passive}")
        print()

        print("   Tips:")
        for tip in strategy["tips"]:
            print(f"     • {tip}")
        print()
        print("-" * 80)
        print()

    print("General Tips:")
    for tip in guide["general_tips"]:
        print(f"  • {tip}")

    # 맞춤형 파밍 가이드 테스트
    print("\n" + "=" * 80)
    print("맞춤형 파밍 가이드 테스트 (알케앤고 + 전략 파밍)")
    print("=" * 80)

    test_builds = [
        {
            "name": "Lightning Arrow Deadeye",
            "pob_data": {
                "dps": 15000000,
                "ehp": 45000,
                "skill_tags": ["projectile", "chaining", "aoe", "lightning"],
                "main_skill": "Lightning Arrow",
                "budget": "medium"
            }
        },
        {
            "name": "RF Juggernaut",
            "pob_data": {
                "dps": 3000000,
                "ehp": 120000,
                "skill_tags": ["dot", "fire", "tankiness"],
                "main_skill": "Righteous Fire",
                "budget": "low"
            }
        },
        {
            "name": "Spark Inquisitor",
            "pob_data": {
                "dps": 50000000,
                "ehp": 80000,
                "skill_tags": ["projectile", "spell", "lightning", "aoe"],
                "main_skill": "Spark",
                "budget": "high"
            }
        }
    ]

    for build in test_builds:
        print(f"\n{'='*60}")
        print(f"빌드: {build['name']}")
        print('='*60)

        result = get_personalized_farming_guide(build["pob_data"])

        if "error" in result:
            print(f"오류: {result['error']}")
            continue

        # 빌드 요약
        summary = result["build_summary"]
        print(f"\n[빌드 요약]")
        print(f"  메인 스킬: {summary['main_skill']}")
        print(f"  DPS: {summary['dps']:,}")
        print(f"  EHP: {summary['ehp']:,}")
        print(f"  클리어 속도: {summary['clear_speed']}")
        print(f"  빌드 파워: {summary['build_power']}")

        # 알케앤고
        alch = result["alch_and_go"]
        print(f"\n[알케미 앤 고]")
        print(f"  적합: {'✓ 추천' if alch['suitable'] else '✗ 비추천'}")
        if alch["maps"]:
            print("  추천 맵:")
            for m in alch["maps"][:3]:
                print(f"    • {m['name_ko']} ({m['name']}) - {m['reason']}")
        print(f"  예상 수익: {alch['expected_profit']}")
        if alch["tips"]:
            print("  팁:")
            for tip in alch["tips"][:2]:
                print(f"    • {tip}")

        # 전략 파밍
        strategic = result["strategic_farming"]
        print(f"\n[전략 파밍]")
        for i, strategy in enumerate(strategic["main_strategies"][:2], 1):
            print(f"  {i}. {strategy['name_ko']} [{strategy['tier']}] - {strategy['profit_per_hour']}")
            if strategy["best_combos"]:
                print(f"     조합: {', '.join(strategy['best_combos'][:2])}")
            if strategy["tips"]:
                print(f"     팁: {strategy['tips'][0]}")

        # 조합 정보
        if strategic.get("combinations"):
            combo = strategic["combinations"]
            print(f"\n  [추천 조합 세팅]")
            if combo.get("scarabs"):
                print(f"    스카랍: {', '.join(combo['scarabs'][:3])}")
            print(f"    예상 수익: {combo.get('estimated_profit', 'N/A')}")

        # 경고
        if result["warnings"]:
            print(f"\n[주의사항]")
            for warn in result["warnings"]:
                print(f"  {warn}")


# =============================================================================
# 리그 페이즈 + 동적 스카랍 조합 시스템
# =============================================================================

import requests
from pathlib import Path

# JSON 데이터 로드
def load_farming_strategies() -> Dict:
    """farming_strategies.json 로드"""
    json_path = Path(__file__).parent / "data" / "farming_strategies.json"
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading farming_strategies.json: {e}")
        return {}


# poe.ninja API 연동
def fetch_poe_ninja_currency(league: str = "Keepers") -> Dict[str, float]:
    """poe.ninja에서 커런시 가격 가져오기"""
    try:
        url = f"https://poe.ninja/api/data/currencyoverview?league={league}&type=Currency"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        prices = {}
        for item in data.get("lines", []):
            name = item.get("currencyTypeName", "")
            chaos_value = item.get("chaosEquivalent", 0)
            if name and chaos_value:
                prices[name] = chaos_value

        return prices
    except Exception as e:
        print(f"Error fetching currency prices: {e}")
        return {}


def fetch_poe_ninja_scarabs(league: str = "Keepers") -> Dict[str, float]:
    """poe.ninja에서 스카랍 가격 가져오기"""
    try:
        url = f"https://poe.ninja/api/data/itemoverview?league={league}&type=Scarab"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        prices = {}
        for item in data.get("lines", []):
            name = item.get("name", "")
            chaos_value = item.get("chaosValue", 0)
            if name and chaos_value:
                prices[name] = chaos_value

        return prices
    except Exception as e:
        print(f"Error fetching scarab prices: {e}")
        return {}


def fetch_poe_ninja_items(league: str = "Keepers", item_type: str = "Essence") -> Dict[str, float]:
    """poe.ninja에서 아이템 가격 가져오기"""
    try:
        url = f"https://poe.ninja/api/data/itemoverview?league={league}&type={item_type}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        prices = {}
        for item in data.get("lines", []):
            name = item.get("name", "")
            chaos_value = item.get("chaosValue", 0)
            if name and chaos_value:
                prices[name] = chaos_value

        return prices
    except Exception as e:
        print(f"Error fetching {item_type} prices: {e}")
        return {}


def get_divine_chaos_ratio(currency_prices: Dict[str, float]) -> float:
    """Divine:Chaos 비율 계산"""
    return currency_prices.get("Divine Orb", 150)


# 리그 페이즈 가이드
def get_league_phase_guide(
    league_phase: str,
    dps: int = 0,
    ehp: int = 0,
    main_skill: str = "Unknown"
) -> Dict:
    """리그 페이즈에 따른 파밍 가이드

    Args:
        league_phase: "early", "mid", "late"
        dps: 빌드 DPS
        ehp: 빌드 EHP
        main_skill: 메인 스킬

    Returns:
        리그 페이즈 맞춤 가이드
    """
    strategies_data = load_farming_strategies()
    if not strategies_data:
        return {"error": "전략 데이터를 로드할 수 없습니다"}

    phase_info = strategies_data.get("league_phases", {}).get(league_phase, {})
    all_strategies = strategies_data.get("strategies", {})

    result = {
        "phase": league_phase,
        "phase_name_ko": phase_info.get("name_ko", league_phase),
        "duration": phase_info.get("duration", ""),
        "divine_chaos_ratio": phase_info.get("divine_chaos_ratio", ""),
        "priorities": phase_info.get("priorities", []),
        "recommended_strategies": [],
        "build_suitable_strategies": [],
        "warnings": []
    }

    # 페이즈에 맞는 전략 필터링
    phase_strategies = phase_info.get("key_strategies", [])

    for strategy_key in phase_strategies:
        strategy = all_strategies.get(strategy_key)
        if not strategy:
            continue

        # 빌드 요구사항 체크
        build_reqs = strategy.get("build_requirements", {})
        min_dps = build_reqs.get("min_dps", 0)
        tags = build_reqs.get("tags", [])

        is_suitable = True
        if min_dps and dps < min_dps:
            is_suitable = False

        strategy_info = {
            "name": strategy.get("name"),
            "name_ko": strategy.get("name_ko"),
            "tier": strategy.get("tier"),
            "investment": strategy.get("investment"),
            "description_ko": strategy.get("description_ko"),
            "expected_profit": strategy.get("expected_profit", {}),
            "build_suitable": is_suitable,
            "execution_guide": strategy.get("execution_guide", {}),
            "scarab_setup": strategy.get("scarab_setup"),
            "atlas_nodes": strategy.get("atlas_nodes", [])
        }

        result["recommended_strategies"].append(strategy_info)

        if is_suitable:
            result["build_suitable_strategies"].append(strategy_info)

    # 페이즈별 특별 팁
    if league_phase == "early":
        result["special_tips"] = [
            "아틀라스 등반이 최우선 - 맵 티어 올리면서 패시브 수집",
            "카오스 레시피: 첫 빌드 자금 (50-100c) 모으면 중단",
            "액트 강탈: 레벨 61-67에서 1시간 → 100-200c",
            "Divine 40-80c일 때 카오스 가치 최고"
        ]
    elif league_phase == "mid":
        result["special_tips"] = [
            "빌드 파워에 맞는 전략 선택",
            "스카랍 가격 체크 후 ROI 높은 조합 사용",
            "TFT 벌크 거래 활용"
        ]
    else:  # late
        result["special_tips"] = [
            "스카랍/맵 가격 하락으로 고투자 전략 접근 가능",
            "Divine 가격 유지 → 수익 동일",
            "T17, 딜리리움 등 고급 전략 도전"
        ]

    return result


# 동적 수익 계산
def calculate_strategy_profit(
    strategy_name: str,
    scarab_prices: Dict[str, float],
    divine_ratio: float
) -> Dict:
    """전략의 실제 수익 계산

    Args:
        strategy_name: 전략 이름
        scarab_prices: 스카랍 가격 딕셔너리
        divine_ratio: Divine:Chaos 비율

    Returns:
        수익 정보
    """
    strategies_data = load_farming_strategies()
    strategy = strategies_data.get("strategies", {}).get(strategy_name)

    if not strategy:
        return {"error": f"전략 '{strategy_name}'을 찾을 수 없습니다"}

    scarab_setup = strategy.get("scarab_setup", {})
    if not scarab_setup:
        return {
            "strategy": strategy_name,
            "scarab_cost": 0,
            "expected_profit": strategy.get("expected_profit", {}),
            "net_profit": "N/A (스카랍 불필요)"
        }

    # 각 투자 수준별 계산
    results = {}

    for investment_level, setup in scarab_setup.items():
        if not isinstance(setup, dict):
            continue

        scarabs = setup.get("scarabs", [])
        estimated_cost = setup.get("cost_per_map", 0)

        # 실제 스카랍 가격 계산
        actual_cost = 0
        scarab_details = []

        for scarab in scarabs:
            # "x2" 같은 수량 처리
            qty = 1
            scarab_name = scarab
            if " x" in scarab:
                parts = scarab.rsplit(" x", 1)
                scarab_name = parts[0]
                qty = int(parts[1])

            price = scarab_prices.get(scarab_name, 0)
            total = price * qty
            actual_cost += total

            if price > 0:
                scarab_details.append({
                    "name": scarab_name,
                    "quantity": qty,
                    "unit_price": price,
                    "total": total
                })

        # 예상 수익
        expected = strategy.get("expected_profit", {})
        chaos_per_hour = expected.get("chaos_per_hour", 0)
        divine_per_hour = expected.get("divine_per_hour", 0)

        # Divine을 Chaos로 환산
        total_chaos_per_hour = chaos_per_hour + (divine_per_hour * divine_ratio)

        # 시간당 맵 수 추정 (평균 5분/맵 = 12맵/시간)
        maps_per_hour = 12
        cost_per_hour = actual_cost * maps_per_hour

        net_profit_per_hour = total_chaos_per_hour - cost_per_hour
        roi = (net_profit_per_hour / cost_per_hour * 100) if cost_per_hour > 0 else float('inf')

        results[investment_level] = {
            "scarabs": scarab_details,
            "estimated_cost_per_map": estimated_cost,
            "actual_cost_per_map": actual_cost,
            "cost_per_hour": cost_per_hour,
            "expected_profit_per_hour": total_chaos_per_hour,
            "net_profit_per_hour": net_profit_per_hour,
            "net_profit_in_divine": net_profit_per_hour / divine_ratio if divine_ratio > 0 else 0,
            "roi_percent": roi
        }

    return {
        "strategy": strategy_name,
        "strategy_name_ko": strategy.get("name_ko"),
        "divine_ratio": divine_ratio,
        "investment_options": results
    }


# 최적 스카랍 조합 추천
def get_optimal_farming_strategies(
    budget: str = "medium",
    build_tags: List[str] = None,
    league_phase: str = "mid",
    league: str = "Keepers"
) -> Dict:
    """현재 가격 기반 최적 파밍 전략 추천

    Args:
        budget: "low", "medium", "high"
        build_tags: 빌드 태그 목록
        league_phase: "early", "mid", "late"
        league: 리그 이름

    Returns:
        최적 전략 목록
    """
    if build_tags is None:
        build_tags = []

    # 가격 데이터 가져오기
    currency_prices = fetch_poe_ninja_currency(league)
    scarab_prices = fetch_poe_ninja_scarabs(league)
    divine_ratio = get_divine_chaos_ratio(currency_prices)

    strategies_data = load_farming_strategies()
    all_strategies = strategies_data.get("strategies", {})

    # 투자 수준 매핑
    budget_map = {
        "low": ["none", "low"],
        "medium": ["none", "low", "medium"],
        "high": ["none", "low", "medium", "high", "very_high"]
    }
    allowed_investments = budget_map.get(budget, ["low", "medium"])

    results = []

    for strategy_key, strategy in all_strategies.items():
        # 투자 수준 체크
        investment = strategy.get("investment", "medium")
        if investment not in allowed_investments:
            continue

        # 리그 페이즈 체크
        phases = strategy.get("phase", [])
        if league_phase not in phases:
            continue

        # 빌드 요구사항 체크
        build_reqs = strategy.get("build_requirements", {})
        req_tags = build_reqs.get("tags", [])

        tag_match = 0
        for tag in req_tags:
            if tag in build_tags:
                tag_match += 1

        # 수익 계산
        profit_info = calculate_strategy_profit(strategy_key, scarab_prices, divine_ratio)

        # 최고 ROI 투자 옵션 찾기
        best_option = None
        best_roi = -float('inf')

        investment_options = profit_info.get("investment_options", {})
        for level, option in investment_options.items():
            # 예산에 맞는지 체크
            cost = option.get("actual_cost_per_map", 0)
            if budget == "low" and cost > 20:
                continue
            elif budget == "medium" and cost > 50:
                continue

            roi = option.get("roi_percent", 0)
            if roi > best_roi:
                best_roi = roi
                best_option = {
                    "investment_level": level,
                    **option
                }

        if best_option:
            results.append({
                "strategy_key": strategy_key,
                "name": strategy.get("name"),
                "name_ko": strategy.get("name_ko"),
                "tier": strategy.get("tier"),
                "description_ko": strategy.get("description_ko"),
                "tag_match_score": tag_match,
                "build_requirements": req_tags,
                "best_option": best_option,
                "atlas_nodes": strategy.get("atlas_nodes", []),
                "execution_guide": strategy.get("execution_guide", {})
            })

    # ROI로 정렬
    results.sort(key=lambda x: x["best_option"]["roi_percent"], reverse=True)

    return {
        "league": league,
        "league_phase": league_phase,
        "budget": budget,
        "divine_chaos_ratio": divine_ratio,
        "recommended_strategies": results[:10],
        "price_update_time": "실시간",
        "note": "ROI = (시간당 수익 - 시간당 비용) / 시간당 비용 * 100"
    }


# 통합 가이드 생성
def get_complete_farming_guide(
    pob_data: Dict,
    league_phase: str = "mid",
    budget: str = "medium",
    league: str = "Keepers"
) -> Dict:
    """POB 데이터 + 리그 페이즈 기반 완전한 파밍 가이드

    Args:
        pob_data: POB에서 추출한 빌드 데이터
        league_phase: "early", "mid", "late"
        budget: "low", "medium", "high"
        league: 리그 이름

    Returns:
        완전한 파밍 가이드
    """
    # 빌드 정보 추출
    dps = pob_data.get("dps", 0)
    ehp = pob_data.get("ehp", 0)
    skill_tags = pob_data.get("skill_tags", [])
    main_skill = pob_data.get("main_skill", "Unknown")

    # 빌드 태그 생성
    build_tags = list(skill_tags)

    if dps >= 10000000:
        build_tags.extend(["boss_dps", "single_target"])
    if dps >= 1000000:
        build_tags.append("clear_speed")
    if ehp >= 50000:
        build_tags.append("tankiness")
    if "projectile" in skill_tags or "chaining" in skill_tags or "aoe" in skill_tags:
        build_tags.append("clear_speed")

    build_tags = list(set(build_tags))

    # 리그 페이즈 가이드
    phase_guide = get_league_phase_guide(league_phase, dps, ehp, main_skill)

    # 최적 전략 추천
    optimal_strategies = get_optimal_farming_strategies(
        budget=budget,
        build_tags=build_tags,
        league_phase=league_phase,
        league=league
    )

    # 기존 맞춤형 가이드
    personalized = get_personalized_farming_guide(pob_data)

    return {
        "build_summary": {
            "main_skill": main_skill,
            "dps": dps,
            "ehp": ehp,
            "build_tags": build_tags
        },
        "league_phase_guide": phase_guide,
        "optimal_strategies": optimal_strategies,
        "personalized_guide": personalized,
        "meta": {
            "league": league,
            "league_phase": league_phase,
            "budget": budget
        }
    }


if __name__ == '__main__':
    main()
