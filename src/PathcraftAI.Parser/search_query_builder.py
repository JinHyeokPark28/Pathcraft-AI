#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search Query Builder
자연어 입력을 YouTube 검색 쿼리로 변환 (AI 해석 없이 키워드 매핑)
"""

import sys
import re
from typing import List, Dict, Tuple, Optional

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


class SearchQueryBuilder:
    """검색 쿼리 빌더"""

    # 스킬 이름 매핑 (한글 → 영어)
    SKILL_NAMES = {
        # 근접
        "사이클론": "Cyclone",
        "도약 강타": "Leap Slam",
        "지진": "Earthquake",
        "칼날폭풍": "Blade Storm",
        "이중 타격": "Double Strike",
        "분쇄 타격": "Sunder",
        "방패 돌진": "Shield Charge",
        "돌개바람 베기": "Whirlwind Slash",

        # 원거리
        "번개 화살": "Lightning Arrow",
        "폭발 화살": "Explosive Arrow",
        "독성 비": "Toxic Rain",
        "얼음 화살": "Ice Shot",
        "분열 화살": "Split Arrow",
        "회전 공격": "Tornado Shot",
        "화살비": "Rain of Arrows",

        # 주문
        "방전": "Discharge",
        "얼음 창": "Ice Spear",
        "서리 볼트": "Frostbolt",
        "화염구": "Fireball",
        "광선": "Arc",
        "폭풍 부름": "Storm Call",
        "폭풍 낙인": "Storm Brand",
        "칼날 소용돌이": "Blade Vortex",
        "정수 흡수": "Essence Drain",
        "전염": "Contagion",
        "빙하 폭포": "Glacial Cascade",
        "신성한 불길": "Righteous Fire",
        "영혼 분리": "Soulrend",
        "황폐": "Bane",
        "서리 구체": "Frost Orb",
        "오브 오브 스톰": "Orb of Storms",

        # 소환수
        "좀비": "Zombies",
        "해골": "Skeletons",
        "망령": "Spectres",
        "골렘": "Golems",
        "신성한 유물": "Animate Guardian",
        "죽음의 표적": "Herald of Purity",
        "죽음의 오라": "Herald of Agony",

        # 토템/덫/지뢰
        "토템": "Totem",
        "덫": "Trap",
        "지뢰": "Mine",
    }

    # 빌드 스타일 매핑
    STYLE_KEYWORDS = {
        # 방어 스타일
        "탱키": ["tank", "tanky", "defensive"],
        "탱커": ["tank", "tanky", "defensive"],
        "방어": ["defensive", "tank"],
        "생존": ["survival", "tanky"],
        "블록": ["block", "max block"],
        "회피": ["evasion", "dodge"],
        "방어막": ["energy shield", "ES"],

        # 공격 스타일
        "딜": ["damage", "dps", "high damage"],
        "딜러": ["damage", "dps"],
        "폭딜": ["high damage", "boss killer", "millions dps"],
        "광역": ["clear", "clear speed", "AOE"],
        "속도": ["fast", "speed", "zoom"],
        "보스킬러": ["boss killer", "bossing"],
        "매핑": ["mapping", "clear speed"],

        # 예산
        "저예산": ["budget", "league starter", "cheap"],
        "리그 스타터": ["league starter", "starter", "budget"],
        "가성비": ["budget", "cheap", "affordable"],
        "고예산": ["expensive", "endgame", "mirror tier"],

        # 콘텐츠
        "델브": ["delve", "deep delve"],
        "시뮬": ["simulacrum"],
        "우버": ["uber", "uber bosses"],
        "심연": ["abyss"],
    }

    # 클래스 이름 매핑
    CLASS_NAMES = {
        "위치": "Witch",
        "마녀": "Witch",
        "레인저": "Ranger",
        "궁수": "Ranger",
        "듀얼리스트": "Duelist",
        "결투사": "Duelist",
        "마라우더": "Marauder",
        "야만전사": "Marauder",
        "템플러": "Templar",
        "성기사": "Templar",
        "쉐도우": "Shadow",
        "암살자": "Shadow",
        "사이온": "Scion",

        # 전직
        "네크로맨서": "Necromancer",
        "엘리멘탈리스트": "Elementalist",
        "오컬티스트": "Occultist",
        "데드아이": "Deadeye",
        "레이더": "Raider",
        "패스파인더": "Pathfinder",
        "슬레이어": "Slayer",
        "글래디에이터": "Gladiator",
        "챔피온": "Champion",
        "저거너트": "Juggernaut",
        "버서커": "Berserker",
        "치프틴": "Chieftain",
        "인퀴지터": "Inquisitor",
        "하이로펀트": "Hierophant",
        "가디언": "Guardian",
        "어쌔신": "Assassin",
        "사보추어": "Saboteur",
        "트릭스터": "Trickster",
        "어센던트": "Ascendant",
    }

    def __init__(self, league_version: str = "3.27"):
        """
        Args:
            league_version: 리그 버전 (3.27, 3.26 등)
        """
        self.league_version = league_version

    def build_query(self, natural_input: str) -> str:
        """자연어 입력을 YouTube 검색 쿼리로 변환

        Args:
            natural_input: 자연어 입력 (예: "사이클론 탱키 빌드")

        Returns:
            YouTube 검색 쿼리 (예: "Cyclone tank tanky defensive build guide 3.27")
        """
        tokens = natural_input.lower().split()
        query_parts = []

        # 스킬 이름 찾기
        skill_found = False
        for korean, english in self.SKILL_NAMES.items():
            if korean.lower() in natural_input.lower():
                query_parts.append(english)
                skill_found = True
                break

        # 영어 스킬 이름 직접 입력 처리
        if not skill_found:
            for token in tokens:
                # 일반적인 영어 스킬 이름
                if token.capitalize() in ["Cyclone", "Arc", "Fireball", "Zombies", "Spectres"]:
                    query_parts.append(token.capitalize())
                    skill_found = True
                    break

        # 클래스 이름 찾기
        for korean, english in self.CLASS_NAMES.items():
            if korean.lower() in natural_input.lower():
                query_parts.append(english)
                break

        # 스타일 키워드 찾기
        style_keywords = []
        for korean, english_list in self.STYLE_KEYWORDS.items():
            if korean in natural_input.lower():
                style_keywords.extend(english_list[:2])  # 최대 2개

        if style_keywords:
            query_parts.extend(list(set(style_keywords)))

        # 기본 검색어 추가
        query_parts.append("build")
        query_parts.append("guide")
        query_parts.append(self.league_version)

        # POE 추가 (다른 게임과 구분)
        if "poe" not in natural_input.lower() and "path of exile" not in natural_input.lower():
            query_parts.insert(0, "POE")

        return " ".join(query_parts)

    def parse_input(self, natural_input: str) -> Dict:
        """자연어 입력을 구조화된 데이터로 파싱

        Args:
            natural_input: 자연어 입력

        Returns:
            파싱된 데이터 (skill, class, styles, etc.)
        """
        result = {
            "skill": None,
            "class": None,
            "ascendancy": None,
            "styles": [],
            "budget": None,
            "content": None,
            "raw_input": natural_input,
        }

        # 스킬 찾기
        for korean, english in self.SKILL_NAMES.items():
            if korean.lower() in natural_input.lower():
                result["skill"] = english
                break

        # 클래스 찾기
        for korean, english in self.CLASS_NAMES.items():
            if korean.lower() in natural_input.lower():
                # 전직인지 기본 클래스인지 구분
                ascendancies = ["Necromancer", "Elementalist", "Occultist", "Deadeye",
                              "Raider", "Pathfinder", "Slayer", "Gladiator", "Champion",
                              "Juggernaut", "Berserker", "Chieftain", "Inquisitor",
                              "Hierophant", "Guardian", "Assassin", "Saboteur", "Trickster",
                              "Ascendant"]
                if english in ascendancies:
                    result["ascendancy"] = english
                else:
                    result["class"] = english
                break

        # 스타일 찾기
        for korean, english_list in self.STYLE_KEYWORDS.items():
            if korean in natural_input.lower():
                result["styles"].extend(english_list)

        # 예산 찾기
        budget_keywords = ["저예산", "리그 스타터", "가성비", "budget", "cheap", "starter"]
        for kw in budget_keywords:
            if kw in natural_input.lower():
                result["budget"] = "budget"
                break

        expensive_keywords = ["고예산", "expensive", "endgame"]
        for kw in expensive_keywords:
            if kw in natural_input.lower():
                result["budget"] = "expensive"
                break

        return result


def build_search_query(natural_input: str, league_version: str = "3.27") -> str:
    """편의 함수: 자연어 입력을 검색 쿼리로 변환

    Args:
        natural_input: 자연어 입력
        league_version: 리그 버전

    Returns:
        YouTube 검색 쿼리
    """
    builder = SearchQueryBuilder(league_version)
    return builder.build_query(natural_input)


def main():
    """테스트"""
    test_inputs = [
        "사이클론 탱키 빌드",
        "Cyclone tank build",
        "번개 화살 딜러",
        "네크로맨서 좀비",
        "저예산 리그 스타터",
        "신성한 불길 저거너트",
        "독성 비 레인저 매핑",
        "칼날 소용돌이 보스킬러",
    ]

    print("=" * 80)
    print("Search Query Builder Test")
    print("=" * 80)
    print()

    builder = SearchQueryBuilder("3.27")

    for input_text in test_inputs:
        query = builder.build_query(input_text)
        parsed = builder.parse_input(input_text)

        print(f"Input: {input_text}")
        print(f"Query: {query}")
        print(f"Parsed: {parsed}")
        print("-" * 80)
        print()


if __name__ == '__main__':
    main()
