# -*- coding: utf-8 -*-
"""
Unified Build Search System
YouTube + Reddit + poe.ninja 통합 빌드 검색
"""

import json
import os
from datetime import datetime
from typing import List, Dict
import argparse


def unified_build_search(keyword: str, league_version: str = "3.27"):
    """
    통합 빌드 검색 시스템

    검색 순서:
    1. YouTube 검색 (가장 빠르고 많은 결과)
    2. Reddit 캐시 검색
    3. poe.ninja 아이템 가격 정보
    """

    print("=" * 80)
    print("PATHCRAFT AI - UNIFIED BUILD SEARCH")
    print("=" * 80)
    print(f"Keyword: {keyword}")
    print(f"League: {league_version}")
    print("=" * 80)
    print()

    all_builds = []

    # Phase 1: YouTube 검색 (< 5초, API 사용 시)
    print("[Phase 1/3] Searching YouTube...")
    print()

    from youtube_build_collector import search_youtube_builds

    youtube_builds = search_youtube_builds(keyword, league_version, max_results=10)

    if youtube_builds:
        all_builds.extend(youtube_builds)
        print(f"[OK] Found {len(youtube_builds)} builds on YouTube")
        print(f"     Total POB links: {sum(len(b['pob_links']) for b in youtube_builds)}")
    else:
        print("[INFO] No YouTube builds found")

    print()

    # Phase 2: Reddit 캐시 검색 (< 1초)
    print("[Phase 2/3] Searching Reddit cache...")
    print()

    reddit_index = os.path.join("build_data", "reddit_builds", "index.json")

    if os.path.exists(reddit_index):
        with open(reddit_index, 'r', encoding='utf-8') as f:
            reddit_data = json.load(f)

        builds = reddit_data.get('builds', [])
        reddit_builds = []

        for build in builds:
            build_name = build.get('build_name', '').lower()
            reddit_title = build.get('reddit_post', {}).get('title', '').lower()

            if keyword.lower() in build_name or keyword.lower() in reddit_title:
                build['source'] = 'reddit'
                reddit_builds.append(build)

        if reddit_builds:
            all_builds.extend(reddit_builds)
            print(f"[OK] Found {len(reddit_builds)} builds on Reddit")
        else:
            print("[INFO] No Reddit builds found")
    else:
        print("[WARN] No Reddit cache found")

    print()

    # Phase 3: poe.ninja 아이템 가격 (< 1초)
    print("[Phase 3/3] Loading item prices...")
    print()

    item_prices = load_item_prices(keyword)

    if item_prices:
        print(f"[OK] Found item data: {item_prices['name']}")
        print(f"     Current price: {item_prices['chaosValue']:.1f} chaos")
        if 'divineValue' in item_prices:
            print(f"                    {item_prices['divineValue']:.2f} divine")
    else:
        print("[INFO] No poe.ninja item data found")

    print()

    # 결과 요약
    print("=" * 80)
    print("SEARCH RESULTS")
    print("=" * 80)
    print()

    if not all_builds:
        print("[WARN] No builds found")
        print()
        print("Suggestions:")
        print("  - Try different keywords")
        print("  - Check spelling")
        print("  - Try item name instead of build archetype")
        return

    # YouTube 빌드
    youtube_only = [b for b in all_builds if b.get('source') == 'youtube']
    if youtube_only:
        print(f"YouTube Builds ({len(youtube_only)}):")
        print()
        for i, build in enumerate(youtube_only[:5], 1):
            print(f"{i}. {build['title']}")
            print(f"   Channel: {build['channel']}")
            print(f"   Views: {build['views']:,} | Likes: {build['likes']:,}")
            print(f"   URL: {build['url']}")
            print(f"   POB Links: {', '.join(build['pob_links'][:2])}")
            if len(build['pob_links']) > 2:
                print(f"              (+{len(build['pob_links']) - 2} more)")
            print()

    # Reddit 빌드
    reddit_only = [b for b in all_builds if b.get('source') == 'reddit']
    if reddit_only:
        print(f"Reddit Builds ({len(reddit_only)}):")
        print()
        for i, build in enumerate(reddit_only[:3], 1):
            print(f"{i}. {build['build_name']}")
            print(f"   Class: {build['class']} / {build['ascendancy']}")
            print(f"   Reddit: {build['reddit_post']['title']}")
            print(f"   Score: {build['reddit_post']['score']} upvotes")
            print(f"   POB: {build['pob_link']}")
            print()

    # 아이템 가격
    if item_prices:
        print("Item Pricing:")
        print()
        print(f"  Name: {item_prices['name']}")
        print(f"  Current Price: {item_prices['chaosValue']:.1f} chaos")
        if 'divineValue' in item_prices:
            print(f"                 {item_prices['divineValue']:.2f} divine")
        if 'sparkline' in item_prices:
            change = item_prices['sparkline'].get('totalChange', 0)
            print(f"  7-Day Change: {change:+.1f}%")
        print()

    # 통계
    total_pob = sum(len(b.get('pob_links', [])) for b in all_builds if 'pob_links' in b)
    total_pob += len([b for b in all_builds if 'pob_link' in b])

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Builds: {len(all_builds)}")
    print(f"  - YouTube: {len(youtube_only)}")
    print(f"  - Reddit: {len(reddit_only)}")
    print(f"Total POB Links: {total_pob}")
    print()

    return all_builds


def load_item_prices(keyword: str) -> Dict:
    """
    poe.ninja에서 아이템 가격 정보 로드
    """

    game_data_dir = "game_data"

    if not os.path.exists(game_data_dir):
        return {}

    # 모든 카테고리 파일 검색
    for filename in os.listdir(game_data_dir):
        if not filename.endswith('.json') or 'metadata' in filename:
            continue

        filepath = os.path.join(game_data_dir, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            items = data.get('items', data.get('lines', []))

            for item in items:
                item_name = item.get('name', '')
                if keyword.lower() in item_name.lower():
                    return item
        except:
            continue

    return {}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Unified Build Search')
    parser.add_argument('--keyword', type=str, required=True, help='Build keyword')
    parser.add_argument('--league', type=str, default='3.27', help='League version')

    args = parser.parse_args()

    unified_build_search(args.keyword, args.league)
