# -*- coding: utf-8 -*-

"""
Path of Exile Official Ladder API Fetcher
공식 래더 API를 사용하여 실제 플레이어 빌드 데이터 수집
"""

import requests
import json
import os
import time
from typing import List, Dict, Optional, Any
from datetime import datetime

# POE Official API
POE_API_BASE = "https://www.pathofexile.com/api"
POE_CHARACTER_WINDOW = "https://www.pathofexile.com/character-window"

HEADERS = {
    'User-Agent': 'PathcraftAI/1.0',
    'Accept': 'application/json'
}

# 빌드 데이터 저장 디렉토리
BUILD_DATA_DIR = os.path.join(os.path.dirname(__file__), "build_data")
BUILD_INDEX_FILE = os.path.join(BUILD_DATA_DIR, "build_index.json")

# Rate limiting (POE API는 엄격함)
REQUEST_DELAY = 1.0  # 요청 간 1초 대기
MAX_RETRIES = 3

def ensure_build_data_dir():
    """빌드 데이터 저장 디렉토리 생성"""
    if not os.path.exists(BUILD_DATA_DIR):
        os.makedirs(BUILD_DATA_DIR)
        print(f"[INFO] Created directory: {BUILD_DATA_DIR}")

def get_ladder(league: str, offset: int = 0, limit: int = 200) -> Optional[Dict]:
    """
    래더 데이터 가져오기

    Args:
        league: 리그 이름 (e.g., "Keepers")
        offset: 시작 순위
        limit: 가져올 캐릭터 수 (최대 200)

    Returns:
        래더 데이터
    """
    url = f"{POE_API_BASE}/ladders/{league}"
    params = {
        'offset': offset,
        'limit': min(limit, 200)  # API 최대 200
    }

    for attempt in range(MAX_RETRIES):
        try:
            print(f"[INFO] Fetching ladder: {league} (offset={offset}, limit={limit})")
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)

            if response.status_code == 429:
                # Rate limited
                wait_time = 60
                print(f"[WARN] Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            data = response.json()

            time.sleep(REQUEST_DELAY)
            return data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"[ERROR] League '{league}' not found (404)")
                return None
            print(f"[ERROR] HTTP error: {e}")

        except Exception as e:
            print(f"[ERROR] Failed to fetch ladder (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

        if attempt < MAX_RETRIES - 1:
            time.sleep(REQUEST_DELAY * 2)

    return None

def get_character_items(character_name: str, account_name: str) -> Optional[Dict]:
    """
    캐릭터의 장비 및 스킬 정보 가져오기

    Args:
        character_name: 캐릭터 이름
        account_name: 계정 이름

    Returns:
        캐릭터 데이터 (장비, 스킬, 패시브)
    """
    url = f"{POE_CHARACTER_WINDOW}/get-items"
    params = {
        'character': character_name,
        'accountName': account_name
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)

            if response.status_code == 403:
                # Private profile
                print(f"[WARN] Character '{character_name}' is private")
                return None

            if response.status_code == 429:
                wait_time = 60
                print(f"[WARN] Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            data = response.json()

            time.sleep(REQUEST_DELAY)
            return data

        except Exception as e:
            print(f"[WARN] Failed to fetch character '{character_name}' (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

        if attempt < MAX_RETRIES - 1:
            time.sleep(REQUEST_DELAY * 2)

    return None

def get_character_passive_skills(character_name: str, account_name: str) -> Optional[Dict]:
    """
    캐릭터의 패시브 스킬 트리 가져오기

    Args:
        character_name: 캐릭터 이름
        account_name: 계정 이름

    Returns:
        패시브 스킬 데이터
    """
    url = f"{POE_CHARACTER_WINDOW}/get-passive-skills"
    params = {
        'character': character_name,
        'accountName': account_name
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)

            if response.status_code == 403:
                return None

            if response.status_code == 429:
                wait_time = 60
                print(f"[WARN] Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            data = response.json()

            time.sleep(REQUEST_DELAY)
            return data

        except Exception as e:
            print(f"[WARN] Failed to fetch passives for '{character_name}' (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

        if attempt < MAX_RETRIES - 1:
            time.sleep(REQUEST_DELAY * 2)

    return None

def extract_main_skill(items_data: Dict) -> Optional[str]:
    """
    장비에서 메인 스킬 추출

    Args:
        items_data: 캐릭터 아이템 데이터

    Returns:
        메인 스킬 젬 이름
    """
    # items_data의 items 배열에서 6링크 아이템 찾기
    items = items_data.get('items', [])

    max_links = 0
    main_skill = None

    for item in items:
        # 소켓이 있는 아이템만
        sockets = item.get('sockets', [])
        if not sockets:
            continue

        # 소켓 그룹 중 가장 큰 링크 찾기
        socket_groups = {}
        for socket in sockets:
            group = socket.get('group', 0)
            socket_groups[group] = socket_groups.get(group, 0) + 1

        if not socket_groups:
            continue

        max_group_size = max(socket_groups.values())

        if max_group_size > max_links:
            max_links = max_group_size

            # 해당 그룹의 첫 번째 액티브 스킬 젬 찾기
            for socket in sockets:
                if socket.get('group') == max(socket_groups, key=socket_groups.get):
                    socketed_item = item.get('socketedItems', [])
                    for gem in socketed_item:
                        if socket.get('group') == gem.get('socket', -1):
                            gem_name = gem.get('typeLine', '')
                            # Support 젬이 아닌 액티브 젬만
                            if 'Support' not in gem_name:
                                main_skill = gem_name
                                break
                    if main_skill:
                        break

    return main_skill

def extract_unique_items(items_data: Dict) -> List[str]:
    """
    착용한 유니크 아이템 목록 추출

    Args:
        items_data: 캐릭터 아이템 데이터

    Returns:
        유니크 아이템 이름 리스트
    """
    unique_items = []

    items = items_data.get('items', [])
    for item in items:
        # frameType: 3 = Unique
        if item.get('frameType') == 3:
            name = item.get('name', '').strip()
            if name:
                unique_items.append(name)

    return unique_items

def parse_build_data(character_data: Dict, items_data: Optional[Dict], passives_data: Optional[Dict]) -> Dict[str, Any]:
    """
    래더 캐릭터 데이터를 빌드 정보로 파싱

    Args:
        character_data: 래더에서 가져온 캐릭터 기본 정보
        items_data: 캐릭터 장비 정보
        passives_data: 패시브 스킬 정보

    Returns:
        빌드 데이터 구조
    """
    character = character_data.get('character', {})
    account = character_data.get('account', {})

    build = {
        "character_name": character.get('name', ''),
        "account_name": account.get('name', ''),
        "class": character.get('class', ''),
        "ascendancy": character.get('ascendancy_class') or character.get('class', ''),
        "level": character.get('level', 0),
        "league": character.get('league', ''),
        "rank": character_data.get('rank', 0),
        "experience": character.get('experience', 0),
        "dead": character.get('dead', False),
        "items": {
            "unique_items": [],
            "main_skill": None,
            "has_items": False
        },
        "passive_tree": {
            "allocated_nodes": [],
            "has_passives": False
        },
        "metadata": {
            "collected_at": datetime.now().isoformat(),
            "profile_public": False
        }
    }

    # 아이템 데이터 파싱
    if items_data:
        build['items']['has_items'] = True
        build['items']['unique_items'] = extract_unique_items(items_data)
        build['items']['main_skill'] = extract_main_skill(items_data)
        build['metadata']['profile_public'] = True

    # 패시브 트리 파싱
    if passives_data:
        build['passive_tree']['has_passives'] = True
        build['passive_tree']['allocated_nodes'] = passives_data.get('hashes', [])

    return build

def collect_builds_from_ladder(league: str, max_characters: int = 1000, offset: int = 0) -> List[Dict]:
    """
    래더에서 빌드 데이터 수집

    Args:
        league: 리그 이름
        max_characters: 수집할 최대 캐릭터 수
        offset: 시작 순위

    Returns:
        빌드 데이터 리스트
    """
    ensure_build_data_dir()

    print("=" * 60)
    print(f"Collecting builds from {league} ladder")
    print("=" * 60)

    builds = []
    current_offset = offset
    batch_size = 200  # API 최대치

    collected = 0
    private_count = 0

    while collected < max_characters:
        # 래더 데이터 가져오기
        ladder_data = get_ladder(league, current_offset, batch_size)
        if not ladder_data:
            print("[ERROR] Failed to fetch ladder data")
            break

        entries = ladder_data.get('entries', [])
        if not entries:
            print("[INFO] No more ladder entries")
            break

        print(f"[INFO] Processing {len(entries)} characters from rank {current_offset + 1}")

        for entry in entries:
            if collected >= max_characters:
                break

            character = entry.get('character', {})
            account = entry.get('account', {})

            char_name = character.get('name', '')
            account_name = account.get('name', '')

            if not char_name or not account_name:
                continue

            try:
                print(f"[INFO] [{collected + 1}/{max_characters}] Rank {entry.get('rank')}: {char_name} ({character.get('class')})")
            except UnicodeEncodeError:
                print(f"[INFO] [{collected + 1}/{max_characters}] Rank {entry.get('rank')}: [Unicode Name] ({character.get('class')})")

            # 캐릭터 아이템 가져오기
            items_data = get_character_items(char_name, account_name)
            if not items_data:
                private_count += 1

            # 패시브 스킬 가져오기
            passives_data = None
            if items_data:  # 공개 프로필인 경우만
                passives_data = get_character_passive_skills(char_name, account_name)

            # 빌드 데이터 파싱
            build = parse_build_data(entry, items_data, passives_data)
            builds.append(build)

            collected += 1

            # 진행 상황 저장 (100개마다)
            if collected % 100 == 0:
                print(f"[INFO] Progress checkpoint: {collected} builds collected")

        current_offset += len(entries)

        # 다음 배치로
        if len(entries) < batch_size:
            print("[INFO] Reached end of ladder")
            break

    print("=" * 60)
    print(f"Collection Summary:")
    print(f"  - Total builds collected: {collected}")
    print(f"  - Public profiles: {collected - private_count}")
    print(f"  - Private profiles: {private_count}")
    print(f"  - Public rate: {(collected - private_count) / collected * 100:.1f}%")
    print("=" * 60)

    return builds

def save_builds(builds: List[Dict], league: str):
    """
    빌드 데이터를 파일로 저장

    Args:
        builds: 빌드 데이터 리스트
        league: 리그 이름
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"builds_{league.replace(' ', '_').lower()}_{timestamp}.json"
    filepath = os.path.join(BUILD_DATA_DIR, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(builds, f, ensure_ascii=False, indent=2)
        print(f"[OK] Saved builds to: {filename}")

        # 인덱스 업데이트
        update_build_index(league, filename, len(builds))

    except Exception as e:
        print(f"[ERROR] Failed to save builds: {e}")

def update_build_index(league: str, filename: str, build_count: int):
    """빌드 인덱스 업데이트"""
    index = {}

    if os.path.exists(BUILD_INDEX_FILE):
        try:
            with open(BUILD_INDEX_FILE, 'r', encoding='utf-8') as f:
                index = json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load build index: {e}")

    if league not in index:
        index[league] = []

    index[league].append({
        "file": filename,
        "build_count": build_count,
        "collected_at": datetime.now().isoformat()
    })

    try:
        with open(BUILD_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        print(f"[OK] Updated build index")
    except Exception as e:
        print(f"[ERROR] Failed to save build index: {e}")

def analyze_builds(builds: List[Dict]) -> Dict[str, Any]:
    """
    수집된 빌드 분석

    Returns:
        분석 결과
    """
    analysis = {
        "total_builds": len(builds),
        "public_builds": sum(1 for b in builds if b['metadata']['profile_public']),
        "classes": {},
        "ascendancies": {},
        "popular_uniques": {},
        "popular_skills": {},
        "level_distribution": {
            "90-95": 0,
            "95-98": 0,
            "98-100": 0
        }
    }

    for build in builds:
        # 클래스 분포
        class_name = build['class']
        analysis['classes'][class_name] = analysis['classes'].get(class_name, 0) + 1

        # 어센던시 분포
        ascendancy = build['ascendancy']
        analysis['ascendancies'][ascendancy] = analysis['ascendancies'].get(ascendancy, 0) + 1

        # 레벨 분포
        level = build['level']
        if 90 <= level < 95:
            analysis['level_distribution']['90-95'] += 1
        elif 95 <= level < 98:
            analysis['level_distribution']['95-98'] += 1
        elif level >= 98:
            analysis['level_distribution']['98-100'] += 1

        # 유니크 아이템 (공개 프로필만)
        if build['metadata']['profile_public']:
            for unique in build['items']['unique_items']:
                analysis['popular_uniques'][unique] = analysis['popular_uniques'].get(unique, 0) + 1

            # 메인 스킬
            skill = build['items']['main_skill']
            if skill:
                analysis['popular_skills'][skill] = analysis['popular_skills'].get(skill, 0) + 1

    # 상위 10개씩만 유지
    analysis['popular_uniques'] = dict(sorted(analysis['popular_uniques'].items(), key=lambda x: x[1], reverse=True)[:10])
    analysis['popular_skills'] = dict(sorted(analysis['popular_skills'].items(), key=lambda x: x[1], reverse=True)[:10])

    return analysis

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='POE Ladder Build Fetcher')
    parser.add_argument('--league', type=str, default='Keepers', help='League name')
    parser.add_argument('--max', type=int, default=1000, help='Maximum characters to fetch')
    parser.add_argument('--offset', type=int, default=0, help='Starting rank offset')
    parser.add_argument('--analyze', action='store_true', help='Analyze collected builds')

    args = parser.parse_args()

    if args.analyze:
        # 분석 모드
        index_path = BUILD_INDEX_FILE
        if not os.path.exists(index_path):
            print("[ERROR] No build data found. Collect builds first.")
        else:
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)

            league = args.league
            if league not in index:
                print(f"[ERROR] No builds found for league '{league}'")
            else:
                latest_file = index[league][-1]['file']
                filepath = os.path.join(BUILD_DATA_DIR, latest_file)

                with open(filepath, 'r', encoding='utf-8') as f:
                    builds = json.load(f)

                analysis = analyze_builds(builds)
                print(json.dumps(analysis, indent=2, ensure_ascii=False))
    else:
        # 수집 모드
        builds = collect_builds_from_ladder(args.league, args.max, args.offset)

        if builds:
            save_builds(builds, args.league)

            # 간단한 분석 출력
            analysis = analyze_builds(builds)
            print("\n" + "=" * 60)
            print("Build Analysis")
            print("=" * 60)
            print(f"Total builds: {analysis['total_builds']}")
            print(f"Public profiles: {analysis['public_builds']}")
            print("\nTop 5 Ascendancies:")
            for asc, count in sorted(analysis['ascendancies'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {asc:30s} - {count:4d} ({count / analysis['total_builds'] * 100:.1f}%)")
            print("\nTop 5 Skills:")
            for skill, count in list(analysis['popular_skills'].items())[:5]:
                print(f"  {skill:30s} - {count:4d}")
            print("\nTop 5 Unique Items:")
            for item, count in list(analysis['popular_uniques'].items())[:5]:
                print(f"  {item:30s} - {count:4d}")
            print("=" * 60)
