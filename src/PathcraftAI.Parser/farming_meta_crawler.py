#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Farming Meta Crawler
3.24~3.27 시즌별 파밍 전략 데이터 수집 및 관리
"""

import sys
import os
import json
import re
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

# UTF-8 설정
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# 데이터 저장 경로
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "farming_meta")
os.makedirs(DATA_DIR, exist_ok=True)


@dataclass
class LeagueInfo:
    """리그 정보"""
    version: str
    name: str
    name_ko: str
    release_date: str
    key_features: List[str] = field(default_factory=list)


@dataclass
class FarmingStrategy:
    """파밍 전략 데이터"""
    name: str
    name_ko: str
    tier: str  # S, A, B, C (메타 티어)
    league_version: str
    description: str
    description_ko: str
    investment: str  # low, medium, high, very_high
    returns: str  # low, medium, high, very_high
    build_requirements: List[str] = field(default_factory=list)
    recommended_maps: List[str] = field(default_factory=list)
    atlas_passives: List[str] = field(default_factory=list)
    scarabs: List[str] = field(default_factory=list)
    tips: List[str] = field(default_factory=list)
    tips_ko: List[str] = field(default_factory=list)
    profit_per_hour: str = ""  # 예상 시간당 수익
    source_urls: List[str] = field(default_factory=list)


# 3.24 ~ 3.27 리그 정보
LEAGUE_INFO = {
    "3.24": LeagueInfo(
        version="3.24",
        name="Necropolis",
        name_ko="네크로폴리스",
        release_date="2024-03-29",
        key_features=[
            "T17 맵 드랍률 대폭 증가",
            "스카랍 시스템 개편 (5티어)",
            "아틀라스 트리 로드아웃 3개 저장",
            "네크로폴리스 묘지 메커닉"
        ]
    ),
    "3.25": LeagueInfo(
        version="3.25",
        name="Settlers of Kalguur",
        name_ko="칼구르의 정착자들",
        release_date="2024-07-26",
        key_features=[
            "킹스마치 마을 건설",
            "골드 화폐 시스템",
            "용병 시스템",
            "무역 선박 시스템"
        ]
    ),
    "3.26": LeagueInfo(
        version="3.26",
        name="Secrets of the Atlas",
        name_ko="아틀라스의 비밀",
        release_date="2024-10-25",
        key_features=[
            "T16.5 맵 (8모드 타락)",
            "용병 강화",
            "군단/하빙어 버프",
            "아틀라스 키스톤 밸런스"
        ]
    ),
    "3.27": LeagueInfo(
        version="3.27",
        name="Keepers League",
        name_ko="관리자의 리그",
        release_date="2025-01-24",
        key_features=[
            "Genesis Tree 크래프팅",
            "Foulborn 유니크",
            "스트롱박스 강화",
            "Legacy of Phrecia 이벤트 (아이돌 시스템)"
        ]
    )
}

# 3.24 네크로폴리스 파밍 전략
STRATEGIES_3_24 = [
    FarmingStrategy(
        name="Blight Maps",
        name_ko="역병 지도 파밍",
        tier="S",
        league_version="3.24",
        description="Blight maps require little to no budget and are scalable. Great for league start.",
        description_ko="역병 지도는 적은 투자로 시작 가능하고 확장성이 좋음. 리그 스타트에 최적",
        investment="low",
        returns="high",
        build_requirements=["aoe", "clear_speed"],
        recommended_maps=["Any"],
        atlas_passives=[
            "Epidemiology",
            "Immune Response",
            "Spores on the Wind"
        ],
        scarabs=["Blight Scarab", "Blight Scarab of Bounty"],
        tips=[
            "Oil drops are in high demand early league",
            "Chance for Headhunter/Mageblood drops",
            "Good for Chaos recipe"
        ],
        tips_ko=[
            "초반 리그에 오일 수요 높음",
            "헤드헌터/메이지블러드 드랍 가능",
            "카오스 레시피에 적합"
        ],
        profit_per_hour="3-8 Divine",
        source_urls=["https://www.aoeah.com/news/3186"]
    ),
    FarmingStrategy(
        name="Legion Farming",
        name_ko="군단 파밍",
        tier="A",
        league_version="3.24",
        description="Release and defeat Eternal Empire warriors for emblems and loot. Best for days 1-2.",
        description_ko="영원한 제국 전사들을 해방하고 처치하여 엠블럼과 전리품 획득. 1-2일차 최고",
        investment="low",
        returns="medium",
        build_requirements=["aoe", "clear_speed"],
        recommended_maps=["Glacier", "Dunes", "Cemetery"],
        atlas_passives=[
            "Monumental",
            "Protracted Battle",
            "Emblematic"
        ],
        scarabs=["Legion Scarab", "Legion Scarab of Command"],
        tips=[
            "Full release is the goal",
            "Timeless Emblems are main income",
            "Value drops quickly after day 2"
        ],
        tips_ko=[
            "전체 해방이 목표",
            "타임리스 엠블럼이 주요 수입원",
            "2일차 이후 가치 급락"
        ],
        profit_per_hour="2-5 Divine",
        source_urls=["https://www.aoeah.com/news/3186"]
    ),
    FarmingStrategy(
        name="T17 Map Farming",
        name_ko="T17 지도 파밍",
        tier="S",
        league_version="3.24",
        description="T17 maps with dramatically increased drop rates for currency and scarabs.",
        description_ko="화폐와 스카랍 드랍률이 대폭 증가한 T17 지도 파밍",
        investment="high",
        returns="very_high",
        build_requirements=["tankiness", "boss_dps", "sustain"],
        recommended_maps=["Fortress", "Sanctuary", "Citadel"],
        atlas_passives=[
            "Shaping the World",
            "All Map Boss nodes"
        ],
        scarabs=["Divination Scarab", "Ambush Scarab"],
        tips=[
            "Cannot sustain T17 from within T17",
            "Farm T16 maps to get T17 drops",
            "Fortress is most expensive T17"
        ],
        tips_ko=[
            "T17 내에서 T17 드랍 불가",
            "T16 파밍으로 T17 획득",
            "Fortress가 가장 비싼 T17"
        ],
        profit_per_hour="10-30 Divine",
        source_urls=["https://www.aoeah.com/news/3244"]
    ),
    FarmingStrategy(
        name="Expedition Farming",
        name_ko="탐험 파밍",
        tier="A",
        league_version="3.24",
        description="One of the best early map currency farming methods with cheap scarab setup.",
        description_ko="저렴한 스카랍으로 초반 지도에서 화폐 파밍하기 좋은 방법",
        investment="low",
        returns="high",
        build_requirements=["single_target", "tankiness"],
        recommended_maps=["Any with good layout"],
        atlas_passives=[
            "Buried Knowledge",
            "Ancient Writings",
            "Extreme Archaeology"
        ],
        scarabs=[
            "Expedition Scarab of Archaeology",
            "Expedition Scarab of Verisium Powder",
            "Expedition Scarab of Runefinding"
        ],
        tips=[
            "Only ~5 Chaos per map investment",
            "Logbooks are main income",
            "Tujen and Rog trades are valuable"
        ],
        tips_ko=[
            "맵당 약 5 카오스 투자",
            "로그북이 주요 수입원",
            "투젠과 로그 거래 활용"
        ],
        profit_per_hour="4-8 Divine",
        source_urls=["https://www.gameleap.com/articles/path-of-exile-necropolis-3-24-atlas-strategies-expedition"]
    ),
    FarmingStrategy(
        name="Harbinger Farming",
        name_ko="선구자 파밍",
        tier="A",
        league_version="3.24",
        description="Pair Harbinger with Expedition or Essence for bigger profit.",
        description_ko="탐험이나 에센스와 조합하여 더 큰 수익 창출",
        investment="low",
        returns="medium",
        build_requirements=["single_target"],
        recommended_maps=["Any"],
        atlas_passives=[
            "All Harbinger nodes (29 points)",
            "Scarab nodes"
        ],
        scarabs=["Harbinger Scarab"],
        tips=[
            "Works on any map layout",
            "Combine with Beyond or Expedition",
            "Ancient Orbs are main value"
        ],
        tips_ko=[
            "모든 맵 레이아웃에서 작동",
            "비욘드나 탐험과 조합",
            "Ancient Orb가 주요 가치"
        ],
        profit_per_hour="3-6 Divine",
        source_urls=["https://www.gameleap.com/articles/path-of-exile-necropolis-3-24-atlas-strategies-harbinger"]
    ),
    FarmingStrategy(
        name="Harvest Farming",
        name_ko="수확 파밍",
        tier="A",
        league_version="3.24",
        description="Run Jungle Valley with high quantity maps for Life Force farming.",
        description_ko="정글 계곡에서 높은 퀀티티 지도로 라이프 포스 파밍",
        investment="medium",
        returns="high",
        build_requirements=["clear_speed"],
        recommended_maps=["Jungle Valley"],
        atlas_passives=[
            "All Harvest nodes",
            "Heart of the Grove"
        ],
        scarabs=[
            "Harvest Scarab of Doubling",
            "Harvest Scarab of Cornucopia",
            "Scarab of Monstrous Lineage"
        ],
        tips=[
            "Roll high quantity on maps",
            "Use Atziri Fragments for extra quant",
            "Jungle Valley has great layout"
        ],
        tips_ko=[
            "지도에 높은 퀀티티 굴리기",
            "아츠리 파편으로 추가 퀀티티",
            "정글 계곡 레이아웃 최적"
        ],
        profit_per_hour="5-10 Divine",
        source_urls=["https://www.gameleap.com/articles/path-of-exile-necropolis-3-24-atlas-strategies-harvest"]
    ),
    FarmingStrategy(
        name="Ritual Farming",
        name_ko="의식 파밍",
        tier="B",
        league_version="3.24",
        description="Ritual farming focusing on Favour rerolls for valuable items.",
        description_ko="호의 리롤을 통한 고가 아이템 획득 의식 파밍",
        investment="medium",
        returns="medium",
        build_requirements=["clear_speed", "sustain"],
        recommended_maps=["Any linear map"],
        atlas_passives=[
            "All Ritual nodes",
            "Avoid Immutable Dogma",
            "Avoid Arbitrary Tenets"
        ],
        scarabs=["Ritual Scarab"],
        tips=[
            "Never take Immutable Dogma",
            "Arbitrary Tenets adds too much RNG",
            "Reroll for expensive uniques"
        ],
        tips_ko=[
            "Immutable Dogma 절대 찍지 말 것",
            "Arbitrary Tenets는 RNG 너무 높음",
            "비싼 유니크 나올 때까지 리롤"
        ],
        profit_per_hour="3-6 Divine",
        source_urls=["https://www.gameleap.com/articles/path-of-exile-necropolis-3-24-atlas-strategies-ritual"]
    )
]

# 3.25 칼구르의 정착자들 파밍 전략
STRATEGIES_3_25 = [
    FarmingStrategy(
        name="Simulacrum Farming",
        name_ko="시뮬라크럼 파밍",
        tier="S",
        league_version="3.25",
        description="Classic and reliable method for consistent currency gains. Potential for Voice Jewels worth mirrors.",
        description_ko="안정적인 화폐 획득의 클래식한 방법. 미러급 가치의 보이스 주얼 가능성",
        investment="medium",
        returns="very_high",
        build_requirements=["tankiness", "sustain", "boss_dps"],
        recommended_maps=["Simulacrum"],
        atlas_passives=["Delirium nodes"],
        scarabs=[],
        tips=[
            "Stable profits",
            "Voice Jewels worth mirror+",
            "Runs are inexpensive"
        ],
        tips_ko=[
            "안정적인 수익",
            "보이스 주얼 미러 이상 가치",
            "저렴한 입장료"
        ],
        profit_per_hour="5-15 Divine",
        source_urls=["https://www.mmopixel.com/news/poe-settlers-of-kalguur-league-3-25-best-currency-farming-strategies"]
    ),
    FarmingStrategy(
        name="Ritual + Harvest Farming",
        name_ko="의식 + 수확 파밍",
        tier="S",
        league_version="3.25",
        description="Classic combination for early league. Focus on stack deck drops.",
        description_ko="초반 리그 클래식 조합. 스택 덱 드랍에 집중",
        investment="medium",
        returns="high",
        build_requirements=["clear_speed", "sustain"],
        recommended_maps=["Any T16"],
        atlas_passives=[
            "All Ritual nodes",
            "All Harvest nodes"
        ],
        scarabs=["Cloister Divination Scarab x5"],
        tips=[
            "Use all Ritual and Harvest passive nodes",
            "Proper setup is crucial",
            "Great for early league"
        ],
        tips_ko=[
            "모든 의식/수확 패시브 찍기",
            "세팅이 중요",
            "초반 리그에 최적"
        ],
        profit_per_hour="4-8 Divine",
        source_urls=["https://www.mmopixel.com/news/poe-settlers-of-kalguur-league-3-25-best-currency-farming-strategies"]
    ),
    FarmingStrategy(
        name="T17 Fortress Farming",
        name_ko="T17 요새 파밍",
        tier="S",
        league_version="3.25",
        description="Focus on Fortress maps for ~26 Divine profit per 50 maps after costs.",
        description_ko="요새 지도 집중 파밍으로 50맵당 약 26 디바인 순수익",
        investment="high",
        returns="very_high",
        build_requirements=["tankiness", "boss_dps", "sustain"],
        recommended_maps=["Fortress"],
        atlas_passives=["T17 specific nodes"],
        scarabs=["Various based on strategy"],
        tips=[
            "~38.8 Divine gross in 50 maps",
            "Get Fortress every 2 runs avg",
            "Requires strong build"
        ],
        tips_ko=[
            "50맵당 총 38.8 디바인",
            "평균 2런당 요새 1개",
            "강한 빌드 필요"
        ],
        profit_per_hour="10-25 Divine",
        source_urls=["https://www.mmopixel.com/news/poe-settlers-of-kalguur-league-3-25-best-currency-farming-strategies"]
    ),
    FarmingStrategy(
        name="Alch and Go (Divine Altars)",
        name_ko="알케미 앤 고 (신성 제단)",
        tier="A",
        league_version="3.25",
        description="No-investment strategy. Fastest way to hit Divine Altars. New meta in 3.25.",
        description_ko="무투자 전략. 신성 제단 도달 최고 속도. 3.25 뉴메타",
        investment="low",
        returns="medium",
        build_requirements=["clear_speed"],
        recommended_maps=["Any linear T16"],
        atlas_passives=["Altar nodes", "Map sustain"],
        scarabs=[],
        tips=[
            "Faster than juiced T17",
            "Enter and exit quickly",
            "Divine Altars are main income"
        ],
        tips_ko=[
            "T17 주스보다 빠름",
            "빠른 진입/퇴장",
            "신성 제단이 주요 수입원"
        ],
        profit_per_hour="3-7 Divine",
        source_urls=["https://www.poecurrency.com/news/poe-3-25-how-to-perform-this-alch-and-go-farming-strategy"]
    ),
    FarmingStrategy(
        name="Logbook Farming",
        name_ko="로그북 파밍",
        tier="A",
        league_version="3.25",
        description="Reliable choice for currency farming when buying in bulk.",
        description_ko="대량 구매 시 안정적인 화폐 파밍 방법",
        investment="medium",
        returns="high",
        build_requirements=["single_target", "tankiness"],
        recommended_maps=["Logbooks"],
        atlas_passives=["Expedition nodes"],
        scarabs=[],
        tips=[
            "Buy logbooks in bulk",
            "One of the best methods",
            "Consistent returns"
        ],
        tips_ko=[
            "로그북 대량 구매",
            "최고의 방법 중 하나",
            "일관된 수익"
        ],
        profit_per_hour="5-12 Divine",
        source_urls=["https://www.mmopixel.com/news/poe-settlers-of-kalguur-league-3-25-best-currency-farming-strategies"]
    ),
    FarmingStrategy(
        name="Synthesis Maps (Gold Farming)",
        name_ko="합성 지도 (골드 파밍)",
        tier="A",
        league_version="3.25",
        description="Best way to earn gold for Kingsmarch. ~15k gold per run + 100% XP bonus.",
        description_ko="킹스마치 골드 최고 획득법. 런당 약 15k 골드 + 100% 경험치 보너스",
        investment="medium",
        returns="high",
        build_requirements=["clear_speed"],
        recommended_maps=["Synthesis Maps"],
        atlas_passives=["Synthesis nodes"],
        scarabs=[],
        tips=[
            "~15k gold per run average",
            "100% XP bonus",
            "Quick town upgrades"
        ],
        tips_ko=[
            "런당 평균 15k 골드",
            "100% 경험치 보너스",
            "빠른 마을 업그레이드"
        ],
        profit_per_hour="Gold focused",
        source_urls=["https://www.poecurrency.com/news/poe-3-25-best-strategies-for-gold-farming"]
    ),
    FarmingStrategy(
        name="Blight Farming",
        name_ko="역병 파밍",
        tier="A",
        league_version="3.25",
        description="Popular again due to T17/T16 juicing controversy. Provides bubble gum currency and rich loot.",
        description_ko="T17/T16 주스 논란으로 다시 인기. 버블검 화폐와 풍부한 전리품 제공",
        investment="low",
        returns="high",
        build_requirements=["aoe", "clear_speed"],
        recommended_maps=["Blight Maps"],
        atlas_passives=["Blight nodes"],
        scarabs=["Blight Scarab"],
        tips=[
            "Effective currency strategy",
            "Rich loot opportunities",
            "Good alternative to T17"
        ],
        tips_ko=[
            "효과적인 화폐 전략",
            "풍부한 전리품",
            "T17의 좋은 대안"
        ],
        profit_per_hour="3-8 Divine",
        source_urls=["https://www.poecurrency.com/news/poe-3-25-how-to-use-blight-farming-strategy-to-obtain-currency-and-resource"]
    ),
    FarmingStrategy(
        name="Delve Farming",
        name_ko="탐광 파밍",
        tier="B",
        league_version="3.25",
        description="Optimal depth 250-300. Good for fossils and resonators.",
        description_ko="최적 깊이 250-300. 화석과 공명기에 좋음",
        investment="medium",
        returns="medium",
        build_requirements=["tankiness", "sustain"],
        recommended_maps=["Delve"],
        atlas_passives=["Delve nodes"],
        scarabs=[],
        tips=[
            "Optimal depth 250-300",
            "Requires good gear",
            "Fossil farming main income"
        ],
        tips_ko=[
            "최적 깊이 250-300",
            "좋은 장비 필요",
            "화석 파밍이 주요 수입"
        ],
        profit_per_hour="3-6 Divine",
        source_urls=["https://www.mmopixel.com/news/poe-settlers-of-kalguur-league-3-25-best-currency-farming-strategies"]
    )
]

# 3.26 아틀라스의 비밀 파밍 전략
STRATEGIES_3_26 = [
    FarmingStrategy(
        name="Legion Farming",
        name_ko="군단 파밍",
        tier="S",
        league_version="3.26",
        description="Buffed in 3.26. Map crafting grants extra Legion without scarabs. Uses Dunes maps.",
        description_ko="3.26에서 버프됨. 맵 크래프팅으로 스카랍 없이 추가 군단. 듄즈 맵 사용",
        investment="low",
        returns="high",
        build_requirements=["aoe", "clear_speed"],
        recommended_maps=["Dunes"],
        atlas_passives=[
            "Protracted Battle",
            "Emblematic",
            "Stalwart Defenders"
        ],
        scarabs=["Legion Scarab", "Ambush Scarab", "Breach Scarab", "Harbinger Scarab"],
        tips=[
            "Legion was buffed in 3.26",
            "Works with non-meta builds",
            "Smooth and rewarding maps"
        ],
        tips_ko=[
            "3.26에서 군단 버프",
            "비메타 빌드도 가능",
            "부드럽고 보상 좋은 맵"
        ],
        profit_per_hour="5-10 Divine",
        source_urls=["https://www.aoeah.com/news/3984"]
    ),
    FarmingStrategy(
        name="Harbinger Farming",
        name_ko="선구자 파밍",
        tier="S",
        league_version="3.26",
        description="Safest way for currency flow. Fracturing orbs always in demand. Run T17+ for best results.",
        description_ko="가장 안전한 화폐 획득법. 프랙처링 오브 항상 수요. T17+ 최적",
        investment="medium",
        returns="high",
        build_requirements=["single_target", "clear_speed"],
        recommended_maps=["Any T17"],
        atlas_passives=["All Harbinger nodes"],
        scarabs=["Harbinger Scarab"],
        tips=[
            "Run T17 for extra density",
            "T16 with high pack size also works",
            "Fracturing orbs main value"
        ],
        tips_ko=[
            "T17으로 추가 밀도",
            "높은 팩사이즈 T16도 가능",
            "프랙처링 오브가 주요 가치"
        ],
        profit_per_hour="5-12 Divine",
        source_urls=["https://ggwtb.com/blog/poe-3-26-harbingers-farming-guide-best-atlas-tree-strategy"]
    ),
    FarmingStrategy(
        name="T16.5 Abyss Farming",
        name_ko="T16.5 심연 파밍",
        tier="S",
        league_version="3.26",
        description="8-mod corrupted T16s with Atlas scaling. Mercenary can carry the map. No Risk Scarabs needed.",
        description_ko="8모드 타락 T16에 아틀라스 스케일링. 용병이 맵 캐리 가능. 리스크 스카랍 불필요",
        investment="medium",
        returns="very_high",
        build_requirements=["tankiness"],
        recommended_maps=["Any 8-mod corrupted T16"],
        atlas_passives=["Abyss nodes", "Corruption nodes"],
        scarabs=["Abyss Scarab"],
        tips=[
            "Mercenary carries the map",
            "Only need to survive and loot",
            "Designed for non-mirror builds"
        ],
        tips_ko=[
            "용병이 맵 캐리",
            "생존하고 루팅만 하면 됨",
            "미러급 아닌 빌드용"
        ],
        profit_per_hour="8-15 Divine",
        source_urls=["https://www.aoeah.com/news/4017"]
    ),
    FarmingStrategy(
        name="Expedition Farming",
        name_ko="탐험 파밍",
        tier="A",
        league_version="3.26",
        description="One of the best early map currency farming methods. Atlas nodes available early.",
        description_ko="초반 지도 화폐 파밍 최고 방법 중 하나. 아틀라스 노드 초반 사용 가능",
        investment="low",
        returns="high",
        build_requirements=["single_target", "tankiness"],
        recommended_maps=["Any"],
        atlas_passives=["Expedition nodes"],
        scarabs=["Expedition Scarab"],
        tips=[
            "Encounter guaranteed across most maps",
            "Great for early league",
            "Atlas nodes available early"
        ],
        tips_ko=[
            "대부분 맵에서 인카운터 보장",
            "초반 리그에 최적",
            "아틀라스 노드 초반 사용 가능"
        ],
        profit_per_hour="4-8 Divine",
        source_urls=["https://www.aoeah.com/news/3997"]
    ),
    FarmingStrategy(
        name="Altar/Exarch Farming (Jungle Valley)",
        name_ko="제단/엑사크 파밍 (정글 계곡)",
        tier="A",
        league_version="3.26",
        description="Alch & Go Exarch farming. No boss until arena means no boss altars, more minion altars.",
        description_ko="알케미 앤 고 엑사크 파밍. 아레나까지 보스 없어 보스 제단 없음, 미니언 제단 더 많음",
        investment="low",
        returns="high",
        build_requirements=["clear_speed"],
        recommended_maps=["Jungle Valley", "Mesa"],
        atlas_passives=["Altar nodes", "Exarch influence"],
        scarabs=[],
        tips=[
            "No boss until arena",
            "More minion altars (most rewarding)",
            "Mesa is good fallback"
        ],
        tips_ko=[
            "아레나까지 보스 없음",
            "미니언 제단 더 많음 (가장 보상 좋음)",
            "메사가 대안"
        ],
        profit_per_hour="4-8 Divine",
        source_urls=["https://www.aoeah.com/news/3997"]
    ),
    FarmingStrategy(
        name="Mirror Farming",
        name_ko="미러 파밍",
        tier="S",
        league_version="3.26",
        description="High-end strategy combining multiple mechanics for maximum returns.",
        description_ko="여러 메커닉 조합 고급 전략으로 최대 수익 창출",
        investment="very_high",
        returns="very_high",
        build_requirements=["tankiness", "boss_dps", "clear_speed", "sustain"],
        recommended_maps=["T17"],
        atlas_passives=["Combined high-end setup"],
        scarabs=["Multiple premium scarabs"],
        tips=[
            "Combine multiple mechanics",
            "Requires mirror-tier investment",
            "Highest potential returns"
        ],
        tips_ko=[
            "여러 메커닉 조합",
            "미러급 투자 필요",
            "최고 잠재 수익"
        ],
        profit_per_hour="15-50+ Divine",
        source_urls=["https://www.aoeah.com/news/4030"]
    )
]

# 3.27 Keepers 리그 파밍 전략
STRATEGIES_3_27 = [
    FarmingStrategy(
        name="Strongbox Farming",
        name_ko="스트롱박스 파밍",
        tier="S",
        league_version="3.27",
        description="Full Ambush scarabs + Shrines = currency piñatas. Weekend warriors hit 10+ Divine/hour.",
        description_ko="앰부시 스카랍 + 성소 = 화폐 피냐타. 주말 워리어 시간당 10+ 디바인",
        investment="medium",
        returns="very_high",
        build_requirements=["clear_speed"],
        recommended_maps=["Any with good density"],
        atlas_passives=[
            "Max strongbox wheels",
            "Scarab clusters",
            "Quant smalls"
        ],
        scarabs=["Ambush Scarab (full set)"],
        tips=[
            "Combine with Shrines",
            "10+ Divine/hour possible",
            "Wait for scarab stocks"
        ],
        tips_ko=[
            "성소와 조합",
            "시간당 10+ 디바인 가능",
            "스카랍 재고 기다리기"
        ],
        profit_per_hour="10-15 Divine",
        source_urls=["https://www.iggm.com/news/poe-3-27-strongbox-farming-strategies-maximize-currency-returns"]
    ),
    FarmingStrategy(
        name="Idol Strategy (Phrecia Event)",
        name_ko="아이돌 전략 (프레시아 이벤트)",
        tier="S",
        league_version="3.27",
        description="Legacy of Phrecia event uses Idol system replacing Atlas tree. Combine multiple mechanics.",
        description_ko="프레시아 이벤트는 아틀라스 트리 대신 아이돌 시스템 사용. 여러 메커닉 조합",
        investment="medium",
        returns="high",
        build_requirements=["varied"],
        recommended_maps=["T16"],
        atlas_passives=["Idol based"],
        scarabs=["Various"],
        tips=[
            "Idol system replaces Atlas tree",
            "Combine multiple league mechanics",
            "Prioritize map sustain"
        ],
        tips_ko=[
            "아이돌이 아틀라스 트리 대체",
            "여러 리그 메커닉 조합",
            "맵 서스테인 우선"
        ],
        profit_per_hour="5-12 Divine",
        source_urls=["https://www.aoeah.com/news/3815"]
    ),
    FarmingStrategy(
        name="Simulacrum Farming",
        name_ko="시뮬라크럼 파밍",
        tier="S",
        league_version="3.27",
        description="Once T16 stable, shift to Simulacrum. Great for builds with strong AoE and sustain.",
        description_ko="T16 안정화 후 시뮬라크럼으로 전환. 강한 AoE와 서스테인 빌드에 최적",
        investment="medium",
        returns="very_high",
        build_requirements=["aoe", "sustain", "tankiness"],
        recommended_maps=["Simulacrum"],
        atlas_passives=["Delirium nodes"],
        scarabs=[],
        tips=[
            "Simulacrum keys widely available",
            "Great rewards",
            "Strong AoE/sustain builds excel"
        ],
        tips_ko=[
            "시뮬라크럼 키 쉽게 구함",
            "좋은 보상",
            "강한 AoE/서스테인 빌드 최적"
        ],
        profit_per_hour="8-15 Divine",
        source_urls=["https://www.aoeah.com/news/3818"]
    ),
    FarmingStrategy(
        name="Heist Farming",
        name_ko="강탈 파밍",
        tier="A",
        league_version="3.27",
        description="Generates basic currency efficiently. Grand Heists drop replica uniques and experimental bases.",
        description_ko="기본 화폐 효율적 생산. 대규모 강탈에서 레플리카 유니크와 실험용 베이스 드랍",
        investment="low",
        returns="high",
        build_requirements=["single_target"],
        recommended_maps=["Heist"],
        atlas_passives=["Heist nodes"],
        scarabs=[],
        tips=[
            "Efficient basic currency gen",
            "Replica uniques from Grand Heists",
            "Thieves' Trinkets valuable"
        ],
        tips_ko=[
            "효율적인 기본 화폐 생산",
            "대규모 강탈에서 레플리카 유니크",
            "도둑의 장신구 가치있음"
        ],
        profit_per_hour="4-8 Divine",
        source_urls=["https://www.aoeah.com/news/3818"]
    ),
    FarmingStrategy(
        name="Boss Farming (Trialmaster/Kosis)",
        name_ko="보스 파밍 (트라이얼마스터/코시스)",
        tier="A",
        league_version="3.27",
        description="Big-ticket bosses with hefty loot. Challenging but rewarding.",
        description_ko="큰 전리품의 빅티켓 보스. 도전적이지만 보상 좋음",
        investment="high",
        returns="very_high",
        build_requirements=["boss_dps", "tankiness"],
        recommended_maps=["Boss arenas"],
        atlas_passives=["Boss nodes"],
        scarabs=[],
        tips=[
            "Trialmaster and Kosis drop hefty loot",
            "Challenging fights",
            "Clear quickly for efficiency"
        ],
        tips_ko=[
            "트라이얼마스터와 코시스 큰 전리품",
            "도전적인 전투",
            "빠른 클리어가 효율"
        ],
        profit_per_hour="10-20 Divine",
        source_urls=["https://www.aoeah.com/news/3818"]
    ),
    FarmingStrategy(
        name="Foulborn Unique Crafting",
        name_ko="파울본 유니크 크래프팅",
        tier="A",
        league_version="3.27",
        description="Genesis Tree crafting system replaces original modifiers with potentially more powerful ones.",
        description_ko="Genesis Tree 크래프팅으로 원본 모디파이어를 더 강력한 것으로 교체",
        investment="high",
        returns="very_high",
        build_requirements=["crafting_knowledge"],
        recommended_maps=["Any"],
        atlas_passives=["Genesis Tree unlocked"],
        scarabs=[],
        tips=[
            "Genesis Tree must be unlocked",
            "Replaces unique modifiers",
            "Potentially more powerful results"
        ],
        tips_ko=[
            "Genesis Tree 해금 필요",
            "유니크 모디파이어 교체",
            "더 강력한 결과 가능"
        ],
        profit_per_hour="Variable",
        source_urls=["https://www.mmojugg.com/news/poe-327-best-currency-farming-profit-strategy.html"]
    )
]


class FarmingMetaManager:
    """파밍 메타 데이터 관리자"""

    def __init__(self):
        self.strategies = {
            "3.24": STRATEGIES_3_24,
            "3.25": STRATEGIES_3_25,
            "3.26": STRATEGIES_3_26,
            "3.27": STRATEGIES_3_27
        }
        self.league_info = LEAGUE_INFO

    def get_strategies_by_league(self, version: str) -> List[FarmingStrategy]:
        """리그별 전략 가져오기"""
        return self.strategies.get(version, [])

    def get_all_strategies(self) -> Dict[str, List[FarmingStrategy]]:
        """모든 전략 가져오기"""
        return self.strategies

    def get_top_strategies(self, version: str, tier: str = "S") -> List[FarmingStrategy]:
        """티어별 상위 전략 가져오기"""
        strategies = self.get_strategies_by_league(version)
        return [s for s in strategies if s.tier == tier]

    def get_strategy_by_name(self, name: str) -> Optional[FarmingStrategy]:
        """이름으로 전략 검색"""
        for version_strategies in self.strategies.values():
            for strategy in version_strategies:
                if strategy.name.lower() == name.lower() or strategy.name_ko == name:
                    return strategy
        return None

    def get_strategies_for_build(self, build_tags: List[str], budget: str = "medium") -> List[Dict]:
        """빌드에 맞는 전략 추천 (모든 리그에서)"""
        recommendations = []
        investment_order = ["low", "medium", "high", "very_high"]
        budget_index = investment_order.index(budget) if budget in investment_order else 1

        for version, strategies in self.strategies.items():
            for strategy in strategies:
                # 빌드 요구사항 매칭
                match_score = sum(1 for req in strategy.build_requirements if req in build_tags)

                # 예산 체크
                strategy_index = investment_order.index(strategy.investment) if strategy.investment in investment_order else 2

                if strategy_index <= budget_index + 1:
                    recommendations.append({
                        "version": version,
                        "strategy": strategy,
                        "match_score": match_score,
                        "suitable": match_score >= len(strategy.build_requirements) // 2
                    })

        # 티어와 매칭 점수로 정렬
        tier_order = {"S": 0, "A": 1, "B": 2, "C": 3}
        recommendations.sort(key=lambda x: (tier_order.get(x["strategy"].tier, 4), -x["match_score"]))

        return recommendations[:10]

    def get_strategies_by_build_power(self, dps: int, ehp: int, clear_speed: str = "medium") -> Dict:
        """빌드 파워에 따른 전략 추천

        Args:
            dps: 빌드 DPS
            ehp: Effective HP
            clear_speed: 클리어 속도 (slow, medium, fast, very_fast)

        Returns:
            티어별 추천 전략
        """
        recommendations = {
            "build_power": "",
            "recommended_tier": "",
            "strategies": {
                "main": [],      # 메인 전략
                "secondary": [], # 보조 전략
                "avoid": []      # 피해야 할 전략
            },
            "tips": []
        }

        # 빌드 파워 등급 결정 (DPS 또는 EHP 둘 중 하나가 높아도 인정)
        # Glass Cannon (높은 DPS, 낮은 EHP) 또는 Tank (낮은 DPS, 높은 EHP) 모두 고려
        if dps >= 50000000 and ehp >= 100000:  # 50M+ DPS, 100k+ EHP
            power_level = "god_tier"
            recommendations["build_power"] = "갓 티어 (God Tier)"
            recommendations["recommended_tier"] = "S+"
        elif (dps >= 20000000 and ehp >= 50000) or (dps >= 50000000 and ehp >= 20000):  # 고DPS 글캐 허용
            power_level = "high"
            recommendations["build_power"] = "하이 티어 (High)"
            recommendations["recommended_tier"] = "S"
        elif (dps >= 5000000 and ehp >= 30000) or (dps >= 10000000 and ehp >= 10000) or (dps >= 3000000 and ehp >= 50000):
            # 미드 티어: 밸런스 빌드 OR 글캐 OR 탱커
            power_level = "medium"
            recommendations["build_power"] = "미드 티어 (Medium)"
            recommendations["recommended_tier"] = "A"
        elif (dps >= 1000000 and ehp >= 15000) or (dps >= 5000000 and ehp >= 3000) or (dps >= 500000 and ehp >= 30000):
            # 로우 티어: 밸런스 OR 글캐(레벨링중) OR 탱커
            power_level = "low"
            recommendations["build_power"] = "로우 티어 (Low)"
            recommendations["recommended_tier"] = "B"
        else:
            power_level = "starter"
            recommendations["build_power"] = "스타터 (Starter)"
            recommendations["recommended_tier"] = "Beginner"

        # 전략 매핑
        strategy_mapping = {
            "god_tier": {
                "main": ["Mirror Farming", "T17 Fortress Farming", "Boss Farming (Trialmaster/Kosis)"],
                "secondary": ["Simulacrum Farming", "T16.5 Abyss Farming"],
                "avoid": []
            },
            "high": {
                "main": ["Simulacrum Farming", "T17 Map Farming", "T16.5 Abyss Farming"],
                "secondary": ["Harbinger Farming", "Legion Farming", "Strongbox Farming"],
                "avoid": ["Mirror Farming"]
            },
            "medium": {
                "main": ["Legion Farming", "Harbinger Farming", "Expedition Farming", "Blight Farming"],
                "secondary": ["Ritual + Harvest Farming", "Altar/Exarch Farming (Jungle Valley)"],
                "avoid": ["T17 Map Farming", "Boss Farming (Trialmaster/Kosis)", "Mirror Farming"]
            },
            "low": {
                "main": ["Essence Farming", "Heist Farming", "Alch and Go (Divine Altars)"],
                "secondary": ["Expedition Farming", "Blight Maps"],
                "avoid": ["Simulacrum Farming", "T17 Map Farming", "T16.5 Abyss Farming"]
            },
            "starter": {
                "main": ["Heist Farming", "Essence Farming", "Alch and Go (Divine Altars)"],
                "secondary": ["Blight Maps"],
                "avoid": ["모든 고투자 전략"]
            }
        }

        mapping = strategy_mapping.get(power_level, strategy_mapping["starter"])

        # 전략 상세 정보 수집
        for category in ["main", "secondary"]:
            for strategy_name in mapping[category]:
                strategy = self.get_strategy_by_name(strategy_name)
                if strategy:
                    recommendations["strategies"][category].append({
                        "name": strategy.name,
                        "name_ko": strategy.name_ko,
                        "tier": strategy.tier,
                        "profit_per_hour": strategy.profit_per_hour,
                        "investment": strategy.investment,
                        "tips_ko": strategy.tips_ko[:2]  # 상위 2개 팁만
                    })

        recommendations["strategies"]["avoid"] = mapping["avoid"]

        # 클리어 속도 기반 추가 팁
        speed_tips = {
            "slow": [
                "보스 킬 위주 전략 추천",
                "단일 타겟 콘텐츠 (강탈, 로그북) 집중",
                "클리어 속도보다 생존력 우선"
            ],
            "medium": [
                "균형 잡힌 전략 가능",
                "탐험 + 군단 조합 추천",
                "맵 서스테인 확보 후 주스 시작"
            ],
            "fast": [
                "밀도 높은 맵 선택",
                "군단/하빙어/역병 최적",
                "알케미 앤 고 효율 극대화"
            ],
            "very_fast": [
                "모든 전략 가능",
                "스트롱박스 + 성소 조합 최적",
                "T16.5 8모드 맵 도전 가능"
            ]
        }
        recommendations["tips"] = speed_tips.get(clear_speed, speed_tips["medium"])

        return recommendations

    def get_strategy_combinations(self, primary_strategy: str, budget: str = "medium") -> Dict:
        """전략 조합 추천

        Args:
            primary_strategy: 메인 전략 이름
            budget: 예산 (low, medium, high, very_high)

        Returns:
            조합 추천 정보
        """
        # 전략 조합 시너지 매핑
        synergy_map = {
            "Legion Farming": {
                "best_combos": ["Harbinger Farming", "Breach Farming", "Strongbox Farming"],
                "scarab_combo": ["Legion Scarab", "Ambush Scarab", "Breach Scarab", "Harbinger Scarab"],
                "atlas_focus": "밀도 + 몬스터 생성",
                "synergy_reason": "군단 해방 시 추가 몬스터/상자로 가치 증폭"
            },
            "Harbinger Farming": {
                "best_combos": ["Legion Farming", "Expedition Farming", "Beyond"],
                "scarab_combo": ["Harbinger Scarab", "Legion Scarab", "Expedition Scarab"],
                "atlas_focus": "화폐 파편 + 추가 메커닉",
                "synergy_reason": "하빙어 화폐 + 다른 메커닉 보상 동시 획득"
            },
            "Expedition Farming": {
                "best_combos": ["Essence Farming", "Harbinger Farming", "Harvest Farming"],
                "scarab_combo": ["Expedition Scarab of Archaeology", "Essence Scarab", "Harvest Scarab"],
                "atlas_focus": "탐험 확장 + 저투자 메커닉",
                "synergy_reason": "탐험 사이 시간에 에센스/수확 처리"
            },
            "Blight Farming": {
                "best_combos": ["Essence Farming", "Ritual Farming"],
                "scarab_combo": ["Blight Scarab", "Essence Scarab", "Ritual Scarab"],
                "atlas_focus": "역병 보상 + 추가 드랍",
                "synergy_reason": "역병 중 에센스/의식 처리로 시간 효율"
            },
            "Delirium Farming": {
                "best_combos": ["Beyond", "Breach Farming", "Legion Farming"],
                "scarab_combo": ["Delirium Orb", "Breach Scarab", "Legion Scarab", "Beyond Scarab"],
                "atlas_focus": "환영 + 밀도 극대화",
                "synergy_reason": "환영 안개 내 몬스터 밀도가 핵심"
            },
            "Simulacrum Farming": {
                "best_combos": ["단독 실행 추천"],
                "scarab_combo": [],
                "atlas_focus": "환영 노드 올인",
                "synergy_reason": "시뮬라크럼은 맵 외부 콘텐츠로 단독 실행이 효율적"
            },
            "Strongbox Farming": {
                "best_combos": ["Shrine", "Legion Farming", "Essence Farming"],
                "scarab_combo": ["Ambush Scarab (full set)", "Essence Scarab"],
                "atlas_focus": "상자 + 성소 + 추가 메커닉",
                "synergy_reason": "성소 버프 상태에서 상자 열기로 드랍 극대화"
            },
            "Harvest Farming": {
                "best_combos": ["Ritual Farming", "Essence Farming", "Expedition Farming"],
                "scarab_combo": ["Harvest Scarab of Doubling", "Ritual Scarab", "Essence Scarab"],
                "atlas_focus": "라이프포스 + 의식 호의",
                "synergy_reason": "의식에서 라이프포스/크래프트 재료 구매 가능"
            },
            "Ritual Farming": {
                "best_combos": ["Harvest Farming", "Essence Farming"],
                "scarab_combo": ["Ritual Scarab", "Harvest Scarab", "Essence Scarab"],
                "atlas_focus": "의식 호의 + 추가 가치",
                "synergy_reason": "의식 호의로 고가 아이템 구매"
            },
            "Heist Farming": {
                "best_combos": ["단독 실행 추천"],
                "scarab_combo": [],
                "atlas_focus": "강탈 노드",
                "synergy_reason": "강탈은 맵 외부 콘텐츠로 단독 실행"
            }
        }

        result = {
            "primary": primary_strategy,
            "combinations": [],
            "full_setup": {},
            "estimated_profit": "",
            "warnings": []
        }

        # 메인 전략 정보
        primary = self.get_strategy_by_name(primary_strategy)
        if not primary:
            return {"error": f"전략을 찾을 수 없음: {primary_strategy}"}

        synergy = synergy_map.get(primary_strategy, {})

        # 조합 추천
        if synergy.get("best_combos"):
            for combo_name in synergy["best_combos"]:
                if combo_name == "단독 실행 추천":
                    result["combinations"].append({
                        "name": "단독 실행",
                        "name_ko": "단독 실행 추천",
                        "reason": synergy.get("synergy_reason", "")
                    })
                else:
                    combo_strategy = self.get_strategy_by_name(combo_name)
                    if combo_strategy:
                        result["combinations"].append({
                            "name": combo_strategy.name,
                            "name_ko": combo_strategy.name_ko,
                            "tier": combo_strategy.tier,
                            "investment": combo_strategy.investment,
                            "reason": synergy.get("synergy_reason", "")
                        })

        # 풀 셋업 정보
        result["full_setup"] = {
            "scarabs": synergy.get("scarab_combo", []),
            "atlas_focus": synergy.get("atlas_focus", ""),
            "primary_investment": primary.investment,
            "primary_profit": primary.profit_per_hour
        }

        # 예상 수익 계산 (조합 시 약 30-50% 증가 추정)
        base_profit = primary.profit_per_hour
        if "+" in base_profit or "-" in base_profit:
            # "5-10 Divine" 형식 파싱
            try:
                parts = base_profit.replace(" Divine", "").replace("+", "").split("-")
                if len(parts) == 2:
                    low = float(parts[0])
                    high = float(parts[1])
                    combo_low = low * 1.3
                    combo_high = high * 1.5
                    result["estimated_profit"] = f"{combo_low:.0f}-{combo_high:.0f} Divine (조합 시)"
            except:
                result["estimated_profit"] = f"{base_profit} (기본) + 조합 보너스"
        else:
            result["estimated_profit"] = f"{base_profit} + 조합 보너스"

        # 예산 경고
        investment_order = ["low", "medium", "high", "very_high"]
        budget_idx = investment_order.index(budget) if budget in investment_order else 1
        primary_idx = investment_order.index(primary.investment) if primary.investment in investment_order else 2

        if primary_idx > budget_idx:
            result["warnings"].append(f"⚠️ 이 전략은 '{primary.investment}' 투자가 필요합니다. 현재 예산: '{budget}'")

        # 빌드 요구사항 안내
        if primary.build_requirements:
            result["warnings"].append(f"📋 빌드 요구사항: {', '.join(primary.build_requirements)}")

        return result

    def export_to_json(self, output_path: Optional[str] = None):
        """JSON으로 내보내기"""
        if not output_path:
            output_path = os.path.join(DATA_DIR, "farming_meta_all.json")

        data = {
            "version": "1.0",
            "generated_date": datetime.now().isoformat(),
            "leagues": {},
            "strategies": {}
        }

        # 리그 정보
        for version, info in self.league_info.items():
            data["leagues"][version] = asdict(info)

        # 전략 정보
        for version, strategies in self.strategies.items():
            data["strategies"][version] = [asdict(s) for s in strategies]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"데이터 내보내기 완료: {output_path}")
        return output_path

    def print_league_summary(self, version: str):
        """리그 요약 출력"""
        info = self.league_info.get(version)
        strategies = self.get_strategies_by_league(version)

        if not info:
            print(f"리그 {version} 정보 없음")
            return

        print(f"\n{'='*60}")
        print(f"POE {version} - {info.name} ({info.name_ko})")
        print(f"{'='*60}")
        print(f"출시일: {info.release_date}")
        print(f"\n주요 특징:")
        for feature in info.key_features:
            print(f"  • {feature}")

        print(f"\n파밍 전략 ({len(strategies)}개):")
        for tier in ["S", "A", "B", "C"]:
            tier_strategies = [s for s in strategies if s.tier == tier]
            if tier_strategies:
                print(f"\n  [{tier} 티어]")
                for s in tier_strategies:
                    print(f"    • {s.name_ko} ({s.name})")
                    print(f"      투자: {s.investment} | 수익: {s.returns} | 예상: {s.profit_per_hour}")


def main():
    """테스트 및 데이터 생성"""
    print("=" * 80)
    print("Farming Meta Crawler - 3.24 ~ 3.27 파밍 전략 데이터")
    print("=" * 80)

    manager = FarmingMetaManager()

    # 각 리그 요약 출력
    for version in ["3.24", "3.25", "3.26", "3.27"]:
        manager.print_league_summary(version)

    # JSON 내보내기
    print("\n" + "=" * 80)
    print("데이터 내보내기")
    print("=" * 80)
    output_path = manager.export_to_json()

    # 빌드 태그로 전략 추천 테스트
    print("\n" + "=" * 80)
    print("빌드별 전략 추천 테스트")
    print("=" * 80)

    test_builds = [
        {
            "name": "Fast Clear Speed Build",
            "tags": ["clear_speed", "aoe"],
            "budget": "low"
        },
        {
            "name": "Tanky Boss Killer",
            "tags": ["tankiness", "boss_dps", "single_target"],
            "budget": "high"
        },
        {
            "name": "All-Rounder",
            "tags": ["clear_speed", "tankiness", "sustain"],
            "budget": "medium"
        }
    ]

    for build in test_builds:
        print(f"\n{build['name']} (예산: {build['budget']}):")
        print(f"  태그: {', '.join(build['tags'])}")
        recommendations = manager.get_strategies_for_build(build["tags"], build["budget"])

        print("  추천 전략:")
        for i, rec in enumerate(recommendations[:5], 1):
            s = rec["strategy"]
            print(f"    {i}. [{s.tier}] {s.name_ko} (v{rec['version']}) - {s.profit_per_hour}")

    # 빌드 파워 기반 추천 테스트
    print("\n" + "=" * 80)
    print("빌드 파워 기반 전략 추천 테스트")
    print("=" * 80)

    power_tests = [
        {"name": "리그 스타터", "dps": 500000, "ehp": 10000, "speed": "slow"},
        {"name": "중간 빌드", "dps": 8000000, "ehp": 40000, "speed": "medium"},
        {"name": "고성능 빌드", "dps": 30000000, "ehp": 80000, "speed": "fast"},
        {"name": "갓 티어 빌드", "dps": 100000000, "ehp": 150000, "speed": "very_fast"}
    ]

    for test in power_tests:
        print(f"\n{test['name']} (DPS: {test['dps']:,}, EHP: {test['ehp']:,}, 속도: {test['speed']}):")
        result = manager.get_strategies_by_build_power(test["dps"], test["ehp"], test["speed"])

        print(f"  빌드 파워: {result['build_power']}")
        print(f"  추천 티어: {result['recommended_tier']}")

        print("  메인 전략:")
        for s in result["strategies"]["main"][:3]:
            print(f"    • {s['name_ko']} - {s['profit_per_hour']}")

        if result["strategies"]["secondary"]:
            print("  보조 전략:")
            for s in result["strategies"]["secondary"][:2]:
                print(f"    • {s['name_ko']} - {s['profit_per_hour']}")

        if result["strategies"]["avoid"]:
            print(f"  피해야 할 전략: {', '.join(result['strategies']['avoid'][:3])}")

        print("  팁:")
        for tip in result["tips"][:2]:
            print(f"    • {tip}")

    # 전략 조합 테스트
    print("\n" + "=" * 80)
    print("전략 조합 추천 테스트")
    print("=" * 80)

    combo_tests = [
        {"strategy": "Legion Farming", "budget": "medium"},
        {"strategy": "Expedition Farming", "budget": "low"},
        {"strategy": "Strongbox Farming", "budget": "medium"},
        {"strategy": "Simulacrum Farming", "budget": "high"}
    ]

    for test in combo_tests:
        print(f"\n{test['strategy']} (예산: {test['budget']}):")
        result = manager.get_strategy_combinations(test["strategy"], test["budget"])

        if "error" in result:
            print(f"  오류: {result['error']}")
            continue

        print("  추천 조합:")
        for combo in result["combinations"][:3]:
            if "tier" in combo:
                print(f"    • {combo['name_ko']} [{combo['tier']}]")
            else:
                print(f"    • {combo['name_ko']}")
        print(f"    이유: {result['combinations'][0]['reason'] if result['combinations'] else 'N/A'}")

        setup = result["full_setup"]
        if setup.get("scarabs"):
            print(f"  스카랍 조합: {', '.join(setup['scarabs'][:4])}")
        print(f"  아틀라스 포커스: {setup.get('atlas_focus', 'N/A')}")
        print(f"  예상 수익: {result['estimated_profit']}")

        if result["warnings"]:
            for warn in result["warnings"]:
                print(f"  {warn}")


if __name__ == '__main__':
    main()
