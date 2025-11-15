# -*- coding: utf-8 -*-

"""
Ladder Item Filter - 래더에서 특정 아이템 사용 빌드만 필터링
"""

import json
import os
from typing import List, Dict
from poe_ladder_fetcher import collect_builds_from_ladder, save_builds

BUILD_DATA_DIR = os.path.join(os.path.dirname(__file__), "build_data")

def filter_builds_by_item(builds: List[Dict], item_name: str) -> List[Dict]:
    """
    특정 아이템을 사용하는 빌드만 필터링

    Args:
        builds: 빌드 리스트
        item_name: 찾을 아이템 이름 (예: "Death's Oath")

    Returns:
        필터링된 빌드 리스트
    """
    filtered = []

    for build in builds:
        # 유니크 아이템 목록에서 검색
        unique_items = build.get('items', {}).get('unique_items', [])

        # 아이템 이름이 포함되어 있는지 확인 (대소문자 무시)
        if any(item_name.lower() in item.lower() for item in unique_items):
            filtered.append(build)
            print(f"[FOUND] {build['character_name']} - {build['ascendancy']} Lvl {build['level']}")
            print(f"        Unique items: {', '.join(unique_items[:3])}...")

    return filtered

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Filter ladder builds by item')
    parser.add_argument('--item', type=str, required=True, help='Item name to search for')
    parser.add_argument('--league', type=str, default='Keepers', help='League name')
    parser.add_argument('--max', type=int, default=500, help='Maximum builds to scan')
    parser.add_argument('--limit', type=int, default=10, help='Maximum matching builds to keep')

    args = parser.parse_args()

    print(f"[INFO] Scanning {args.max} builds for: {args.item}")
    print("=" * 60)

    # 래더에서 빌드 수집
    all_builds = collect_builds_from_ladder(args.league, max_characters=args.max)

    # 아이템으로 필터링
    filtered = filter_builds_by_item(all_builds, args.item)

    print("\n" + "=" * 60)
    print(f"Found {len(filtered)} builds using {args.item}")
    print("=" * 60)

    # 상위 N개만 저장
    if filtered:
        builds_to_save = filtered[:args.limit]
        save_builds(builds_to_save, f"{args.league}_{args.item.replace(' ', '_')}")
        print(f"\n[OK] Saved {len(builds_to_save)} builds")

        # 어센던시 분포
        ascendancies = {}
        for build in builds_to_save:
            asc = build['ascendancy']
            ascendancies[asc] = ascendancies.get(asc, 0) + 1

        print("\nAscendancy Distribution:")
        for asc, count in sorted(ascendancies.items(), key=lambda x: x[1], reverse=True):
            print(f"  {asc:20s} - {count} builds")
