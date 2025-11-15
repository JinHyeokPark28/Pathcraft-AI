# -*- coding: utf-8 -*-

"""
Ladder Cache Builder
POE 공식 래더에서 대량의 빌드 데이터를 미리 수집하여 캐시로 저장

사용법:
1. 정기적으로 실행 (하루 1-2회)
2. 상위 500-1000명의 빌드 데이터 수집
3. 로컬 캐시 파일로 저장
4. 사용자 요청 시 캐시에서 즉시 검색
"""

import json
import os
import time
from typing import List, Dict
from datetime import datetime
from poe_ladder_fetcher import (
    get_ladder,
    get_character_items,
    get_character_passive_skills,
    parse_build_data,
    extract_unique_items
)

CACHE_DIR = os.path.join(os.path.dirname(__file__), "build_data", "ladder_cache")
REQUEST_DELAY = 1.0  # POE API 속도 제한

def ensure_cache_dir():
    """캐시 디렉토리 생성"""
    os.makedirs(CACHE_DIR, exist_ok=True)

def build_ladder_cache(
    league: str = "Keepers",
    max_characters: int = 500,
    resume_from: int = 0
) -> List[Dict]:
    """
    래더에서 빌드 데이터 수집 및 캐시 생성

    Args:
        league: 리그 이름
        max_characters: 수집할 최대 캐릭터 수
        resume_from: 재개할 순위 (중단 시 재개용)

    Returns:
        수집된 빌드 리스트
    """
    print("=" * 80)
    print(f"Building Ladder Cache for {league}")
    print(f"Target: {max_characters} characters")
    if resume_from > 0:
        print(f"Resuming from rank: {resume_from}")
    print("=" * 80)

    builds = []
    collected = 0
    offset = (resume_from // 200) * 200  # 200개 단위로 페이징
    private_count = 0
    error_count = 0

    while collected < max_characters:
        print(f"\n[INFO] Fetching ladder page (offset={offset})...")
        ladder_data = get_ladder(league, offset=offset, limit=200)

        if not ladder_data:
            print("[ERROR] Failed to fetch ladder")
            break

        entries = ladder_data.get('entries', [])
        if not entries:
            print("[INFO] No more entries")
            break

        for entry in entries:
            if collected >= max_characters:
                break

            character = entry.get('character', {})
            account = entry.get('account', {})
            rank = entry.get('rank')

            # resume_from보다 작은 순위는 스킵
            if rank < resume_from:
                continue

            char_name = character.get('name', '')
            account_name = account.get('name', '')

            if not char_name or not account_name:
                continue

            try:
                print(f"[{collected + 1}/{max_characters}] Rank {rank}: {char_name} ({character.get('class')})")
            except UnicodeEncodeError:
                print(f"[{collected + 1}/{max_characters}] Rank {rank}: [Unicode Name] ({character.get('class')})")

            # 아이템 정보
            items_data = get_character_items(char_name, account_name)
            if not items_data:
                private_count += 1
                print(f"  [SKIP] Private character")
                time.sleep(REQUEST_DELAY)
                continue

            # 패시브 트리
            passives_data = get_character_passive_skills(char_name, account_name)

            # 빌드 데이터 파싱
            try:
                build = parse_build_data(entry, items_data, passives_data)

                # 추가 메타데이터
                build['cache_metadata'] = {
                    'cached_at': datetime.now().isoformat(),
                    'league': league,
                    'rank': rank
                }

                builds.append(build)
                collected += 1

                # 진행 상황 출력 (10개마다)
                if collected % 10 == 0:
                    print(f"\n--- Progress: {collected}/{max_characters} ({private_count} private, {error_count} errors) ---\n")

            except Exception as e:
                error_count += 1
                print(f"  [ERROR] Failed to parse build: {e}")

            time.sleep(REQUEST_DELAY)

        offset += 200

    print("\n" + "=" * 80)
    print("Cache Build Summary:")
    print(f"  - Total builds collected: {len(builds)}")
    print(f"  - Private characters: {private_count}")
    print(f"  - Errors: {error_count}")
    print("=" * 80)

    return builds

def save_cache(builds: List[Dict], league: str):
    """캐시 파일 저장"""
    ensure_cache_dir()

    cache_file = os.path.join(CACHE_DIR, f"{league}_ladder_cache.json")

    cache_data = {
        "metadata": {
            "league": league,
            "cached_at": datetime.now().isoformat(),
            "build_count": len(builds)
        },
        "builds": builds
    }

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Cache saved: {cache_file}")
    print(f"     {len(builds)} builds")

    # 통계 생성
    generate_cache_stats(builds, league)

def generate_cache_stats(builds: List[Dict], league: str):
    """캐시 통계 생성"""
    stats = {
        "total_builds": len(builds),
        "ascendancies": {},
        "unique_items": {},
        "main_skills": {}
    }

    for build in builds:
        # Ascendancy 분포
        asc = build.get('ascendancy', 'Unknown')
        stats['ascendancies'][asc] = stats['ascendancies'].get(asc, 0) + 1

        # 유니크 아이템 사용 빈도
        for item in build.get('items', {}).get('unique_items', []):
            stats['unique_items'][item] = stats['unique_items'].get(item, 0) + 1

    # 상위 통계
    stats['top_ascendancies'] = sorted(
        stats['ascendancies'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    stats['top_unique_items'] = sorted(
        stats['unique_items'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:20]

    # 통계 저장
    stats_file = os.path.join(CACHE_DIR, f"{league}_cache_stats.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"[OK] Stats saved: {stats_file}")

    # 통계 출력
    print("\nTop Ascendancies:")
    for asc, count in stats['top_ascendancies'][:5]:
        percentage = (count / stats['total_builds']) * 100
        print(f"  {asc:20s} - {count:3d} builds ({percentage:.1f}%)")

    print("\nTop Unique Items:")
    for item, count in stats['top_unique_items'][:10]:
        print(f"  {item:40s} - {count:3d} builds")

def search_cache(
    league: str,
    item: str = None,
    skill: str = None,
    ascendancy: str = None,
    limit: int = 10
) -> List[Dict]:
    """
    캐시에서 빌드 검색

    Args:
        league: 리그 이름
        item: 아이템 필터
        skill: 스킬 필터
        ascendancy: 어센던시 필터
        limit: 최대 결과 수

    Returns:
        매칭되는 빌드 리스트
    """
    cache_file = os.path.join(CACHE_DIR, f"{league}_ladder_cache.json")

    if not os.path.exists(cache_file):
        print(f"[ERROR] No cache found for {league}")
        print(f"        Run: python ladder_cache_builder.py --build --league {league}")
        return []

    with open(cache_file, 'r', encoding='utf-8') as f:
        cache_data = json.load(f)

    builds = cache_data.get('builds', [])
    print(f"[INFO] Loaded {len(builds)} builds from cache")

    # 필터 적용
    filtered = []
    for build in builds:
        match = True

        if item:
            unique_items = build.get('items', {}).get('unique_items', [])
            if not any(item.lower() in ui.lower() for ui in unique_items):
                match = False

        if skill:
            # TODO: skill 필터 구현
            pass

        if ascendancy:
            if build.get('ascendancy', '').lower() != ascendancy.lower():
                match = False

        if match:
            filtered.append(build)

        if len(filtered) >= limit:
            break

    print(f"[FOUND] {len(filtered)} matching builds")
    return filtered

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Ladder Cache Builder')
    parser.add_argument('--build', action='store_true', help='Build cache from ladder')
    parser.add_argument('--search', action='store_true', help='Search cache')
    parser.add_argument('--league', type=str, default='Keepers', help='League name')
    parser.add_argument('--max', type=int, default=500, help='Maximum builds to collect')
    parser.add_argument('--resume', type=int, default=0, help='Resume from rank')
    parser.add_argument('--item', type=str, help='Search for item')
    parser.add_argument('--skill', type=str, help='Search for skill')
    parser.add_argument('--ascendancy', type=str, help='Search for ascendancy')
    parser.add_argument('--limit', type=int, default=10, help='Search result limit')

    args = parser.parse_args()

    if args.build:
        builds = build_ladder_cache(
            league=args.league,
            max_characters=args.max,
            resume_from=args.resume
        )
        if builds:
            save_cache(builds, args.league)

    elif args.search:
        results = search_cache(
            league=args.league,
            item=args.item,
            skill=args.skill,
            ascendancy=args.ascendancy,
            limit=args.limit
        )

        if results:
            print("\nSearch Results:")
            for i, build in enumerate(results, 1):
                print(f"\n{i}. {build['character_name']} - {build['ascendancy']} Lvl {build['level']}")
                print(f"   Rank: {build.get('cache_metadata', {}).get('rank', 'N/A')}")
                print(f"   Unique Items: {', '.join(build.get('items', {}).get('unique_items', [])[:5])}")

    else:
        parser.print_help()
