# -*- coding: utf-8 -*-

"""
poe.ninja Build Scraper
poe.ninja의 빌드 페이지에서 특정 아이템/스킬 사용 빌드 수집
"""

import requests
import json
import os
import time
from typing import List, Dict, Optional
from poe_ladder_fetcher import get_character_items, get_character_passive_skills, parse_build_data

# poe.ninja API 엔드포인트
POE_NINJA_BUILDS_API = "https://poe.ninja/api/data/getbuilds"

REQUEST_DELAY = 1.0  # POE API 요청 간 딜레이

def fetch_poe_ninja_builds(
    league: str = "Keepers",
    item: Optional[str] = None,
    skill: Optional[str] = None,
    class_name: Optional[str] = None,
    sort: str = "depth",
    limit: int = 15
) -> List[Dict]:
    """
    poe.ninja 빌드 API에서 빌드 목록 가져오기

    Args:
        league: 리그 이름
        item: 아이템 필터 (예: "Death's Oath")
        skill: 스킬 필터 (예: "Death Aura")
        class_name: 클래스 필터 (예: "Occultist")
        sort: 정렬 기준 (depth, dps, energy-shield, etc.)
        limit: 가져올 빌드 수

    Returns:
        빌드 정보 리스트 (계정명, 캐릭터명, 클래스, 레벨 등)
    """
    params = {
        "overview": league.lower(),
        "type": "exp",
        "language": "en"
    }

    if item:
        params["item"] = item
    if skill:
        params["skill"] = skill
    if class_name:
        params["class"] = class_name
    if sort:
        params["sort"] = sort

    print(f"[INFO] Fetching builds from poe.ninja...")
    print(f"       League: {league}")
    if item:
        print(f"       Item: {item}")
    if skill:
        print(f"       Skill: {skill}")
    if class_name:
        print(f"       Class: {class_name}")

    try:
        response = requests.get(POE_NINJA_BUILDS_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        builds = data.get('builds', [])
        total_builds = len(builds)

        print(f"[OK] Found {total_builds} builds on poe.ninja")

        # 상위 N개만 반환
        return builds[:limit]

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch poe.ninja builds: {e}")
        return []

def collect_detailed_build_data(
    poe_ninja_builds: List[Dict],
    league: str = "Keepers"
) -> List[Dict]:
    """
    poe.ninja에서 가져온 빌드 정보를 바탕으로 POE 공식 API에서 상세 정보 수집

    Args:
        poe_ninja_builds: poe.ninja API에서 가져온 빌드 목록
        league: 리그 이름

    Returns:
        상세 빌드 데이터 리스트
    """
    detailed_builds = []
    total = len(poe_ninja_builds)

    print(f"\n[INFO] Collecting detailed data for {total} builds...")
    print("=" * 60)

    for i, build in enumerate(poe_ninja_builds, 1):
        account_name = build.get('account', {}).get('name')
        char_name = build.get('name')  # character name
        char_class = build.get('class')
        char_level = build.get('level')

        if not account_name or not char_name:
            print(f"[SKIP] Build {i}/{total}: Missing account or character name")
            continue

        try:
            print(f"[INFO] [{i}/{total}] Fetching: {char_name} ({char_class} Lvl {char_level})")
        except UnicodeEncodeError:
            print(f"[INFO] [{i}/{total}] Fetching: [Unicode Name] ({char_class} Lvl {char_level})")

        # 아이템 정보
        items_data = get_character_items(char_name, account_name)
        if not items_data:
            print(f"[WARN] {char_name} is private or not found")
            time.sleep(REQUEST_DELAY)
            continue

        # 패시브 트리
        passives_data = get_character_passive_skills(char_name, account_name)

        # 빌드 데이터 파싱
        temp_entry = {
            'character': {
                'name': char_name,
                'class': char_class,
                'level': char_level,
                'league': league
            },
            'account': {
                'name': account_name
            },
            'rank': build.get('depth-solo', 0)  # depth를 rank로 사용
        }

        build_data = parse_build_data(temp_entry, items_data, passives_data)

        # poe.ninja 추가 정보 병합
        build_data['poe_ninja'] = {
            'depth_solo': build.get('depth-solo', 0),
            'depth_group': build.get('depth', 0),
            'experience': build.get('experience', 0),
            'main_skill': build.get('mainSkill'),
            'items_value': build.get('items-value', 0)
        }

        detailed_builds.append(build_data)

        print(f"[OK] Collected: {char_name}")
        time.sleep(REQUEST_DELAY)

    print("=" * 60)
    print(f"[OK] Collected {len(detailed_builds)}/{total} detailed builds\n")

    return detailed_builds

def save_builds(builds: List[Dict], keyword: str, league: str):
    """빌드 데이터 저장"""
    output_dir = os.path.join(os.path.dirname(__file__), "build_data", "poe_ninja_builds")
    os.makedirs(output_dir, exist_ok=True)

    # 파일명 생성
    safe_keyword = keyword.replace("'", "").replace(" ", "_")
    filename = f"{safe_keyword}_{league}.json"
    filepath = os.path.join(output_dir, filename)

    # 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(builds, f, ensure_ascii=False, indent=2)

    print(f"[OK] Saved {len(builds)} builds to: {filename}")

    # 인덱스 업데이트
    index_file = os.path.join(output_dir, "index.json")

    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
    else:
        index = {"builds": []}

    # 중복 제거 (같은 키워드+리그 조합)
    index["builds"] = [b for b in index.get("builds", [])
                       if not (b.get("keyword") == keyword and b.get("league") == league)]

    # 새 빌드 추가
    index["builds"].append({
        "keyword": keyword,
        "league": league,
        "file": filename,
        "build_count": len(builds),
        "collected_at": time.strftime("%Y-%m-%d %H:%M:%S")
    })

    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"[OK] Updated index: {index_file}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='poe.ninja Build Scraper')
    parser.add_argument('--league', type=str, default='Keepers', help='League name')
    parser.add_argument('--item', type=str, help='Item filter (e.g., "Death\'s Oath")')
    parser.add_argument('--skill', type=str, help='Skill filter (e.g., "Death Aura")')
    parser.add_argument('--class', type=str, dest='class_name', help='Class filter (e.g., "Occultist")')
    parser.add_argument('--limit', type=int, default=10, help='Maximum builds to collect')
    parser.add_argument('--sort', type=str, default='depth', help='Sort by (depth, dps, energy-shield, etc.)')

    args = parser.parse_args()

    # poe.ninja에서 빌드 목록 가져오기
    poe_ninja_builds = fetch_poe_ninja_builds(
        league=args.league,
        item=args.item,
        skill=args.skill,
        class_name=args.class_name,
        sort=args.sort,
        limit=args.limit
    )

    if not poe_ninja_builds:
        print("[ERROR] No builds found")
        exit(1)

    # 상세 정보 수집
    detailed_builds = collect_detailed_build_data(poe_ninja_builds, args.league)

    if detailed_builds:
        # 키워드 생성 (item 또는 skill)
        keyword = args.item or args.skill or "general"
        save_builds(detailed_builds, keyword, args.league)

        print("\n" + "=" * 60)
        print("Collection Summary:")
        print(f"  Keyword: {keyword}")
        print(f"  League: {args.league}")
        print(f"  Builds collected: {len(detailed_builds)}")

        # 어센던시 분포
        ascendancies = {}
        for build in detailed_builds:
            asc = build.get('ascendancy', 'Unknown')
            ascendancies[asc] = ascendancies.get(asc, 0) + 1

        print("\n  Ascendancy Distribution:")
        for asc, count in sorted(ascendancies.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(detailed_builds)) * 100
            print(f"    {asc:20s} - {count} builds ({percentage:.1f}%)")

        print("=" * 60)
    else:
        print("[ERROR] Failed to collect any detailed builds")
