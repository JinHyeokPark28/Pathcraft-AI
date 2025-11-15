# -*- coding: utf-8 -*-
"""
PathcraftAI Build Search Demo
실제 빌드 검색 시스템 동작 데모
"""

import json
import os
from datetime import datetime

def demo_build_search(keyword="Kinetic Fusillade"):
    """빌드 검색 데모"""

    print("=" * 80)
    print("PATHCRAFT AI - BUILD SEARCH DEMO")
    print("=" * 80)
    print()
    print(f'User Request: "{keyword} build please"')
    print()

    # Phase 1: 로컬 Reddit 빌드 검색
    print("[Phase 1] Searching local cache (< 1 second)...")
    print()

    reddit_index = os.path.join("build_data", "reddit_builds", "index.json")

    if os.path.exists(reddit_index):
        with open(reddit_index, 'r', encoding='utf-8') as f:
            reddit_data = json.load(f)

        builds = reddit_data.get('builds', [])
        matching_builds = []

        for build in builds:
            build_name = build.get('build_name', '').lower()
            reddit_title = build.get('reddit_post', {}).get('title', '').lower()

            if keyword.lower() in build_name or keyword.lower() in reddit_title:
                matching_builds.append(build)

        print(f"[OK] Found {len(matching_builds)} builds from Reddit")
        print()

    if matching_builds:
            print("=" * 80)
            print(f"{keyword.upper()} BUILD GUIDE")
            print("=" * 80)
            print()

            for i, build in enumerate(matching_builds, 1):
                print(f"{i}. {build['build_name']}")
                print(f"   Class: {build['class']}")
                print(f"   Ascendancy: {build['ascendancy']}")
                print(f"   Reddit Post: \"{build['reddit_post']['title']}\"")
                print(f"   Score: {build['reddit_post']['score']} upvotes")
                print(f"   POB Link: {build['pob_link']}")
                print()

            print("=" * 80)
            print("NEXT STEPS")
            print("=" * 80)
            print()
            print("1. Load poe.ninja item prices")
            print("2. Load patch notes for 3.27 Keepers")
            print("3. Generate comprehensive guide with LLM")
            print()
            print("[Background] Searching ladder for more builds (2-5 min)...")
            print()

            # Don't return early, continue to Phase 2
    else:
        matching_builds = []
        print("[WARN] No Reddit builds cache found")

    # Phase 2: 래더 캐시 검색
    print()
    print("[Phase 2] Searching ladder cache...")
    print()

    ladder_cache = os.path.join("build_data", "ladder_cache", "Keepers_ladder_cache.json")

    if os.path.exists(ladder_cache):
        with open(ladder_cache, 'r', encoding='utf-8') as f:
            ladder_data = json.load(f)

        ladder_builds = ladder_data.get('builds', [])
        print(f"[OK] Loaded {len(ladder_builds)} builds from ladder cache")

        # keyword를 사용하는 빌드 찾기 (아이템 기준)
        keyword_builds = []
        for build in ladder_builds:
            unique_items = build.get('items', {}).get('unique_items', [])
            if any(keyword.lower() in item.lower() for item in unique_items):
                keyword_builds.append(build)

        if keyword_builds:
            print(f"[OK] Found {len(keyword_builds)} builds using {keyword} in ladder")
            print()
            print("Ladder Builds:")
            for i, build in enumerate(keyword_builds[:5], 1):
                try:
                    print(f"  {i}. Rank {build.get('cache_metadata', {}).get('rank', 'N/A')}: "
                          f"{build['character_name']} - {build['ascendancy']} Lvl {build['level']}")
                    top_uniques = build.get('items', {}).get('unique_items', [])[:3]
                    print(f"     Items: {', '.join(top_uniques)}")
                except UnicodeEncodeError:
                    print(f"  {i}. Rank {build.get('cache_metadata', {}).get('rank', 'N/A')}: "
                          f"[Unicode Name] - {build['ascendancy']} Lvl {build['level']}")
                    top_uniques = build.get('items', {}).get('unique_items', [])[:3]
                    print(f"     Items: {', '.join(top_uniques)}")
        else:
            print(f"[INFO] No {keyword} builds in top 50 ladder")

        # 상위 어센던시 통계
        ladder_stats_file = os.path.join("build_data", "ladder_cache", "Keepers_cache_stats.json")
        if os.path.exists(ladder_stats_file):
            with open(ladder_stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)

            print()
            print("Current Meta (Top 50 Ladder):")
            for asc, count in stats.get('top_ascendancies', [])[:5]:
                percentage = (count / stats['total_builds']) * 100
                print(f"  {asc:20s} - {count:3d} builds ({percentage:.1f}%)")

            print()
            print("Top 10 Unique Items:")
            for item, count in stats.get('top_unique_items', [])[:10]:
                print(f"  {item:40s} - {count:2d} builds")
    else:
        ladder_builds = []
        print("[WARN] No ladder cache found")

    # Phase 3: poe.ninja 아이템 가격
    print()
    print("[Phase 3] Loading item prices from poe.ninja...")
    print()

    ninja_dir = "game_data"
    total_items = 0
    if os.path.exists(ninja_dir):
        for file in os.listdir(ninja_dir):
            if file.endswith('.json') and 'metadata' not in file:
                filepath = os.path.join(ninja_dir, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # poe.ninja JSON has 'items' key, not 'lines'
                        items = data.get('items', data.get('lines', []))
                        total_items += len(items)
                except:
                    pass

        print(f"[OK] Loaded {total_items:,} items with prices from poe.ninja")
    else:
        print("[WARN] No poe.ninja item data found")

    # Summary
    print()
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()
    print("System Status:")
    print(f"  - Reddit builds: {len(matching_builds) if matching_builds else 0}")
    print(f"  - Ladder cache: {len(ladder_builds) if os.path.exists(ladder_cache) else 0} builds")
    print(f"  - Item prices: {total_items if os.path.exists(ninja_dir) else 0:,} items")
    print()
    print("Ready to generate comprehensive build guides!")
    print()

    return matching_builds if matching_builds else []

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Build Search Demo')
    parser.add_argument('--keyword', type=str, default='Kinetic Fusillade', help='Search keyword')

    args = parser.parse_args()

    demo_build_search(args.keyword)