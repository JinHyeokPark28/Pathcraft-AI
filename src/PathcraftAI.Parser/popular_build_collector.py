# -*- coding: utf-8 -*-
"""
Popular Build Collector
POE.Ninja 데이터 + YouTube 빌드 가이드를 결합하여 인기 빌드 데이터 생성
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Dict
from collections import Counter
import argparse

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

def analyze_poe_ninja_items(league: str) -> Dict:
    """
    POE.Ninja 데이터에서 인기 아이템 분석

    Returns:
        {
            "unique_weapons": [(name, count), ...],
            "unique_armours": [(name, count), ...],
            "skill_gems": [(name, count), ...]
        }
    """

    print("=" * 80)
    print("POE.NINJA DATA ANALYSIS")
    print("=" * 80)
    print(f"League: {league}")
    print()

    game_data_dir = os.path.join(os.path.dirname(__file__), "game_data")

    popular_items = {
        "unique_weapons": [],
        "unique_armours": [],
        "unique_accessories": [],
        "skill_gems": []
    }

    # 유니크 무기 분석
    weapons_file = os.path.join(game_data_dir, "unique_weapons.json")
    if os.path.exists(weapons_file):
        with open(weapons_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # chaosValue 기준으로 정렬 (비싼 = 인기있는)
        items = sorted(data.get('items', []),
                      key=lambda x: x.get('chaosValue', 0),
                      reverse=True)

        popular_items['unique_weapons'] = [
            {
                "name": item['name'],
                "chaos_value": item.get('chaosValue', 0),
                "divine_value": item.get('divineValue', 0),
                "icon": item.get('icon', ''),
                "links": item.get('links', 0)
            }
            for item in items[:20]  # 상위 20개
        ]

        print(f"[OK] Analyzed {len(items)} unique weapons")

    # 유니크 방어구 분석
    armours_file = os.path.join(game_data_dir, "unique_armours.json")
    if os.path.exists(armours_file):
        with open(armours_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        items = sorted(data.get('items', []),
                      key=lambda x: x.get('chaosValue', 0),
                      reverse=True)

        popular_items['unique_armours'] = [
            {
                "name": item['name'],
                "chaos_value": item.get('chaosValue', 0),
                "divine_value": item.get('divineValue', 0),
                "icon": item.get('icon', ''),
                "links": item.get('links', 0)
            }
            for item in items[:20]
        ]

        print(f"[OK] Analyzed {len(items)} unique armours")

    # 악세서리 분석
    accessories_file = os.path.join(game_data_dir, "unique_accessories.json")
    if os.path.exists(accessories_file):
        with open(accessories_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        items = sorted(data.get('items', []),
                      key=lambda x: x.get('chaosValue', 0),
                      reverse=True)

        popular_items['unique_accessories'] = [
            {
                "name": item['name'],
                "chaos_value": item.get('chaosValue', 0),
                "divine_value": item.get('divineValue', 0),
                "icon": item.get('icon', '')
            }
            for item in items[:20]
        ]

        print(f"[OK] Analyzed {len(items)} unique accessories")

    # 스킬 젬 분석 (레벨/퀄리티 기준 인기도)
    gems_file = os.path.join(game_data_dir, "skill_gems.json")
    if os.path.exists(gems_file):
        with open(gems_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 레벨 21, 퀄리티 20 이상만 필터링
        valuable_gems = [
            item for item in data.get('items', [])
            if item.get('gemLevel', 0) >= 21 or item.get('gemQuality', 0) >= 20
        ]

        items = sorted(valuable_gems,
                      key=lambda x: x.get('chaosValue', 0),
                      reverse=True)

        popular_items['skill_gems'] = [
            {
                "name": item['name'],
                "level": item.get('gemLevel', 1),
                "quality": item.get('gemQuality', 0),
                "corrupted": item.get('corrupted', False),
                "chaos_value": item.get('chaosValue', 0),
                "icon": item.get('icon', '')
            }
            for item in items[:30]
        ]

        print(f"[OK] Analyzed {len(items)} valuable skill gems")

    print()
    return popular_items


def extract_build_keywords(popular_items: Dict) -> List[str]:
    """
    인기 아이템에서 빌드 키워드 추출

    Returns:
        빌드 키워드 목록 (예: ["Death's Oath", "Lightning Arrow", "RF"])
    """

    print("=" * 80)
    print("EXTRACTING BUILD KEYWORDS")
    print("=" * 80)
    print()

    keywords = []

    # 유명한 빌드 아이템들
    build_defining_items = {
        "Death's Oath": "Death's Oath",
        "Mageblood": "Mageblood",
        "Headhunter": "Headhunter",
        "Mjölner": "Mjolner",
        "Shako": "Replica Shako",
        "Squire": "The Squire",
        "Covenant": "The Covenant",
        "Dawnbreaker": "Dawnbreaker"
    }

    # 무기/방어구에서 키워드 추출
    for category in ['unique_weapons', 'unique_armours']:
        for item in popular_items.get(category, []):
            item_name = item['name']

            # 빌드 정의 아이템인지 확인
            for keyword, full_name in build_defining_items.items():
                if keyword.lower() in item_name.lower():
                    if keyword not in keywords:
                        keywords.append(keyword)
                        print(f"[FOUND] Build keyword: {keyword} (from {item_name})")

    # 인기 스킬 젬에서 키워드 추출
    skill_keywords = []
    for gem in popular_items.get('skill_gems', []):
        gem_name = gem['name']

        # 메인 공격/스펠 스킬만 추출
        main_skills = [
            "Lightning Arrow", "Tornado Shot", "Ice Shot", "Barrage",
            "Righteous Fire", "RF", "Detonate Dead", "DD",
            "Cyclone", "Boneshatter", "Spectral Throw",
            "Spark", "Freezing Pulse", "Ball Lightning",
            "Summon Raging Spirit", "SRS", "Raise Spectre",
            "Blade Vortex", "BV", "Blade Blast",
            "Explosive Arrow", "EA"
        ]

        for skill in main_skills:
            if skill.lower() in gem_name.lower():
                if skill not in skill_keywords:
                    skill_keywords.append(skill)
                    print(f"[FOUND] Skill keyword: {skill} (from {gem_name})")

    keywords.extend(skill_keywords[:10])  # 상위 10개 스킬만

    print()
    print(f"[OK] Extracted {len(keywords)} build keywords")
    print()

    return keywords


def collect_youtube_builds_for_keywords(keywords: List[str], league_version: str = "3.27") -> List[Dict]:
    """
    각 키워드에 대한 YouTube 빌드 가이드 수집
    """

    print("=" * 80)
    print("COLLECTING YOUTUBE BUILD GUIDES")
    print("=" * 80)
    print(f"League Version: {league_version}")
    print(f"Keywords: {len(keywords)}")
    print()

    all_builds = []

    try:
        from youtube_build_collector import search_youtube_builds
    except ImportError:
        print("[ERROR] youtube_build_collector module not found")
        return []

    for i, keyword in enumerate(keywords, 1):
        print(f"[{i}/{len(keywords)}] Searching for: {keyword}")

        try:
            builds = search_youtube_builds(
                keyword=keyword,
                league_version=league_version,
                max_results=3  # 각 키워드당 상위 3개
            )

            # 키워드 태그 추가
            for build in builds:
                build['build_keyword'] = keyword
                build['source'] = 'youtube'

            all_builds.extend(builds)
            print(f"[OK] Found {len(builds)} builds for {keyword}")

        except Exception as e:
            print(f"[ERROR] Failed to search for {keyword}: {e}")
            continue

        print()

    print(f"[OK] Total builds collected: {len(all_builds)}")
    print()

    return all_builds


def create_build_database(league: str, league_version: str = "3.27") -> Dict:
    """
    전체 빌드 데이터베이스 생성

    Returns:
        {
            "league": "Keepers",
            "league_version": "3.27",
            "generated_at": "2025-11-15T...",
            "popular_items": {...},
            "build_keywords": [...],
            "youtube_builds": [...],
            "total_builds": 50
        }
    """

    print("=" * 80)
    print("POPULAR BUILD DATABASE GENERATOR")
    print("=" * 80)
    print(f"League: {league}")
    print(f"Version: {league_version}")
    print("=" * 80)
    print()

    # 1. POE.Ninja 데이터 분석
    popular_items = analyze_poe_ninja_items(league)

    # 2. 빌드 키워드 추출
    keywords = extract_build_keywords(popular_items)

    # 3. YouTube 빌드 수집
    youtube_builds = collect_youtube_builds_for_keywords(keywords, league_version)

    # 4. 데이터베이스 생성
    database = {
        "league": league,
        "league_version": league_version,
        "generated_at": datetime.now().isoformat(),
        "popular_items": popular_items,
        "build_keywords": keywords,
        "youtube_builds": youtube_builds,
        "total_builds": len(youtube_builds)
    }

    # 5. 저장
    build_data_dir = os.path.join(os.path.dirname(__file__), "build_data")
    os.makedirs(build_data_dir, exist_ok=True)

    output_file = os.path.join(build_data_dir, f"popular_builds_{league}.json")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print("BUILD DATABASE CREATED")
    print("=" * 80)
    print(f"Output: {output_file}")
    print(f"Popular Items: {sum(len(v) for v in popular_items.values())}")
    print(f"Build Keywords: {len(keywords)}")
    print(f"YouTube Builds: {len(youtube_builds)}")
    print("=" * 80)

    return database


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Popular Build Collector')
    parser.add_argument('--league', type=str, default='Keepers', help='League name')
    parser.add_argument('--version', type=str, default='3.27', help='POE version (e.g., 3.27)')

    args = parser.parse_args()

    try:
        database = create_build_database(args.league, args.version)

        print()
        print("=" * 80)
        print("SUCCESS!")
        print("=" * 80)
        print()
        print("Sample builds:")
        for i, build in enumerate(database['youtube_builds'][:5], 1):
            print(f"{i}. {build.get('title', 'Unknown')} ({build.get('build_keyword', '')})")
            print(f"   Channel: {build.get('channel_title', 'Unknown')}")
            print(f"   Views: {build.get('view_count', 0):,}")
            print()

    except Exception as e:
        print(f"[ERROR] Failed to create build database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
