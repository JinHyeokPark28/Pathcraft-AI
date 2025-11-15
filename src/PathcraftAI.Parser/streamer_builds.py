# -*- coding: utf-8 -*-

"""
Streamer Builds Collector
유명 스트리머들의 빌드 수집 (공식 래더 API 사용)
"""

import json
import os
from typing import List, Dict, Optional
from poe_ladder_fetcher import get_character_items, get_character_passive_skills, parse_build_data

# 유명 스트리머 목록 (계정 이름 또는 캐릭터 이름)
STREAMERS = {
    # 한국 스트리머
    "동양곰": {
        "region": "KR",
        "accounts": ["동양곰"],  # 실제 계정 이름으로 교체 필요
        "characters": []  # 알려진 캐릭터 이름
    },
    "ExiledCat": {
        "region": "KR",
        "accounts": ["ExiledCat"],
        "characters": []
    },

    # 해외 유명 스트리머
    "Zizaran": {
        "region": "Global",
        "accounts": ["Zizaran"],
        "characters": []
    },
    "Mathil": {
        "region": "Global",
        "accounts": ["Mathil"],
        "characters": []
    },
    "Quin69": {
        "region": "Global",
        "accounts": ["Quin69"],
        "characters": []
    },
    "Steelmage": {
        "region": "Global",
        "accounts": ["Steelmage"],
        "characters": []
    },
    "Nugiyen": {
        "region": "Global",
        "accounts": ["Nugiyen"],
        "characters": []
    }
}

def search_ladder_for_streamer(league: str, streamer_name: str, account_names: List[str]) -> List[Dict]:
    """
    래더에서 스트리머 캐릭터 검색

    Args:
        league: 리그 이름
        streamer_name: 스트리머 이름
        account_names: 스트리머의 계정 이름 리스트

    Returns:
        찾은 캐릭터 리스트
    """
    from poe_ladder_fetcher import get_ladder

    found_characters = []
    offset = 0
    max_pages = 10  # 상위 2000명만 검색

    print(f"[INFO] Searching for {streamer_name}...")

    while offset < max_pages * 200:
        ladder_data = get_ladder(league, offset=offset, limit=200)
        if not ladder_data:
            break

        entries = ladder_data.get('entries', [])
        if not entries:
            break

        for entry in entries:
            account = entry.get('account', {})
            character = entry.get('character', {})

            account_name = account.get('name', '')
            char_name = character.get('name', '')

            # 계정 이름이 일치하는지 확인
            if account_name in account_names:
                print(f"[FOUND] {streamer_name}: {char_name} (Rank {entry.get('rank')})")
                found_characters.append({
                    'streamer': streamer_name,
                    'rank': entry.get('rank'),
                    'character_name': char_name,
                    'account_name': account_name,
                    'class': character.get('class', ''),
                    'level': character.get('level', 0)
                })

        offset += 200

    return found_characters

def collect_streamer_builds(league: str = "Keepers") -> Dict[str, List[Dict]]:
    """
    모든 스트리머의 빌드 수집

    Args:
        league: 리그 이름

    Returns:
        스트리머별 빌드 데이터
    """
    print("=" * 60)
    print(f"Collecting Streamer Builds from {league}")
    print("=" * 60)

    all_builds = {}

    for streamer_name, info in STREAMERS.items():
        characters = search_ladder_for_streamer(
            league,
            streamer_name,
            info['accounts']
        )

        if not characters:
            print(f"[SKIP] {streamer_name}: Not found in ladder")
            continue

        # 각 캐릭터의 상세 정보 가져오기
        builds = []
        for char_info in characters:
            char_name = char_info['character_name']
            account_name = char_info['account_name']

            print(f"[INFO] Fetching details for {char_name}...")

            # 아이템 정보
            items_data = get_character_items(char_name, account_name)
            if not items_data:
                print(f"[WARN] {char_name} is private")
                continue

            # 패시브 트리
            passives_data = get_character_passive_skills(char_name, account_name)

            # 빌드 데이터 파싱
            # parse_build_data는 래더 entry 형식을 받으므로 임시로 만들어줌
            temp_entry = {
                'character': {
                    'name': char_name,
                    'class': char_info['class'],
                    'ascendancy_class': None,  # items_data에서 추출 필요
                    'level': char_info['level'],
                    'league': league
                },
                'account': {
                    'name': account_name
                },
                'rank': char_info['rank']
            }

            build = parse_build_data(temp_entry, items_data, passives_data)
            build['streamer'] = streamer_name
            build['region'] = info['region']

            builds.append(build)

        if builds:
            all_builds[streamer_name] = builds
            print(f"[OK] {streamer_name}: {len(builds)} build(s) collected")

    return all_builds

def save_streamer_builds(builds: Dict[str, List[Dict]], league: str):
    """스트리머 빌드 저장"""
    output_dir = os.path.join(os.path.dirname(__file__), "build_data", "streamer_builds")
    os.makedirs(output_dir, exist_ok=True)

    # 스트리머별로 저장
    for streamer_name, streamer_builds in builds.items():
        filename = f"{streamer_name.replace(' ', '_')}_{league}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(streamer_builds, f, ensure_ascii=False, indent=2)

        print(f"[OK] Saved {filename}")

    # 통합 인덱스
    index = {
        "league": league,
        "streamers": {},
        "total_builds": sum(len(b) for b in builds.values())
    }

    for streamer_name, streamer_builds in builds.items():
        index["streamers"][streamer_name] = {
            "build_count": len(streamer_builds),
            "region": STREAMERS[streamer_name]["region"],
            "characters": [b['character_name'] for b in streamer_builds]
        }

    index_file = os.path.join(output_dir, f"index_{league}.json")
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"[OK] Saved index: {index_file}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Streamer Builds Collector')
    parser.add_argument('--league', type=str, default='Keepers', help='League name')
    parser.add_argument('--streamer', type=str, help='Specific streamer to search for')

    args = parser.parse_args()

    if args.streamer:
        # 특정 스트리머만 검색
        if args.streamer in STREAMERS:
            streamer_info = STREAMERS[args.streamer]
            characters = search_ladder_for_streamer(
                args.league,
                args.streamer,
                streamer_info['accounts']
            )

            if characters:
                print(f"\nFound {len(characters)} character(s) for {args.streamer}:")
                for char in characters:
                    print(f"  Rank {char['rank']}: {char['character_name']} ({char['class']}) Lvl {char['level']}")
            else:
                print(f"[INFO] {args.streamer} not found in {args.league} ladder")
        else:
            print(f"[ERROR] Unknown streamer: {args.streamer}")
            print(f"Available streamers: {', '.join(STREAMERS.keys())}")
    else:
        # 모든 스트리머 검색
        builds = collect_streamer_builds(args.league)

        if builds:
            save_streamer_builds(builds, args.league)

            print("\n" + "=" * 60)
            print("Collection Summary:")
            for streamer, streamer_builds in builds.items():
                print(f"  {streamer}: {len(streamer_builds)} build(s)")
            print("=" * 60)
