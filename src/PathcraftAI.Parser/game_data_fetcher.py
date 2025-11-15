# -*- coding: utf-8 -*-

"""
POB (Path of Building) 게임 데이터 다운로더
POB GitHub에서 게임 데이터를 다운로드하여 JSON으로 변환
"""

import requests
import json
import os
import re
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import slpp
    SLPP_AVAILABLE = True
except ImportError:
    SLPP_AVAILABLE = False
    print("[Warning] slpp not installed. Lua parsing unavailable.")

# POB GitHub Data URL
POB_DATA_BASE_URL = "https://raw.githubusercontent.com/PathOfBuildingCommunity/PathOfBuilding/master/src/Data"
POB_VERSION_FILE = "https://raw.githubusercontent.com/PathOfBuildingCommunity/PathOfBuilding/master/src/manifest.xml"

HEADERS = {'User-Agent': 'PathcraftAI/1.0'}

# 게임 데이터 저장 디렉토리
GAME_DATA_DIR = os.path.join(os.path.dirname(__file__), "game_data")
METADATA_FILE = os.path.join(GAME_DATA_DIR, "metadata.json")

# 다운로드할 데이터 파일 목록
DATA_FILES = {
    "uniques": "Uniques.lua",
    "gems": "Gems.lua",
    "bases": "Bases.lua",
    "skills": "Skills.lua",
    "classes": "Classes.lua",
    "tree_3_0": "3_0/Tree.lua"
}

def ensure_game_data_dir():
    """게임 데이터 저장 디렉토리 생성"""
    if not os.path.exists(GAME_DATA_DIR):
        os.makedirs(GAME_DATA_DIR)
        print(f"[INFO] Created directory: {GAME_DATA_DIR}")

def download_file(url: str) -> Optional[str]:
    """
    URL에서 파일 다운로드

    Args:
        url: 다운로드할 URL

    Returns:
        파일 내용 (텍스트)
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[ERROR] Failed to download {url}: {e}")
        return None

def simple_lua_to_dict(lua_content: str) -> Dict[str, Any]:
    """
    간단한 Lua 테이블을 Python dict로 변환
    slpp 라이브러리 사용 또는 수동 파싱

    Args:
        lua_content: Lua 코드 문자열

    Returns:
        Python dictionary
    """
    if SLPP_AVAILABLE:
        try:
            # slpp로 Lua 파싱
            # "return { ... }" 형식 추출
            match = re.search(r'return\s*(\{.*\})', lua_content, re.DOTALL)
            if match:
                lua_table = match.group(1)
                data = slpp.slpp.decode(lua_table)
                return data
        except Exception as e:
            print(f"[WARN] slpp parsing failed: {e}")

    # Fallback: 간단한 수동 파싱 (제한적)
    print("[WARN] Using fallback Lua parser (limited functionality)")
    return {"_raw": lua_content[:1000], "_note": "Lua parsing requires slpp library"}

def extract_unique_items(lua_content: str) -> Dict[str, Any]:
    """
    Uniques.lua에서 유니크 아이템 추출

    Returns:
        {
            "item_name": {
                "type": "Helmet",
                "stats": [...],
                ...
            }
        }
    """
    data = simple_lua_to_dict(lua_content)

    # POB Uniques 구조: { new("ItemName", "BaseType", { ... }) }
    # 간단한 정규식으로 이름만 추출 (완전한 파싱은 복잡함)
    unique_items = {}

    # 정규식으로 new("ItemName", ...) 패턴 찾기
    pattern = r'new\("([^"]+)",\s*"([^"]+)"'
    matches = re.findall(pattern, lua_content)

    for item_name, base_type in matches:
        unique_items[item_name] = {
            "name": item_name,
            "base_type": base_type,
            "source": "pob"
        }

    return unique_items

def extract_skill_gems(lua_content: str) -> Dict[str, Any]:
    """
    Gems.lua에서 스킬 젬 추출

    Returns:
        {
            "gem_name": {
                "level_data": [...],
                "quality_stats": [...],
                ...
            }
        }
    """
    gems = {}

    # 간단한 정규식으로 젬 이름 추출
    # gems["GemName"] = { ... }
    pattern = r'\["([^"]+)"\]\s*=\s*\{'
    matches = re.findall(pattern, lua_content)

    for gem_name in matches:
        gems[gem_name] = {
            "name": gem_name,
            "source": "pob"
        }

    return gems

def download_pob_data() -> bool:
    """
    POB GitHub에서 모든 게임 데이터 다운로드

    Returns:
        성공 여부
    """
    ensure_game_data_dir()

    print("=" * 60)
    print("POB Game Data Downloader")
    print("=" * 60)

    metadata = {
        "version": "unknown",
        "downloaded_at": datetime.now().isoformat(),
        "files": {}
    }

    # 각 데이터 파일 다운로드
    for data_name, file_path in DATA_FILES.items():
        url = f"{POB_DATA_BASE_URL}/{file_path}"
        print(f"[INFO] Downloading {data_name}: {file_path}")

        content = download_file(url)
        if not content:
            print(f"[ERROR] Failed to download {data_name}")
            continue

        # Lua를 JSON으로 변환
        if data_name == "uniques":
            parsed_data = extract_unique_items(content)
        elif data_name == "gems":
            parsed_data = extract_skill_gems(content)
        else:
            # 기본 파싱
            parsed_data = simple_lua_to_dict(content)

        # JSON 파일로 저장
        output_file = os.path.join(GAME_DATA_DIR, f"{data_name}.json")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=2)

            item_count = len(parsed_data) if isinstance(parsed_data, dict) else 0
            print(f"[OK] Saved {data_name}.json ({item_count} entries)")

            metadata["files"][data_name] = {
                "file": f"{data_name}.json",
                "entries": item_count,
                "source_url": url
            }
        except Exception as e:
            print(f"[ERROR] Failed to save {data_name}.json: {e}")

    # 메타데이터 저장
    try:
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"[OK] Saved metadata.json")
    except Exception as e:
        print(f"[ERROR] Failed to save metadata: {e}")

    print("=" * 60)
    print(f"Download Summary:")
    print(f"  - Files downloaded: {len(metadata['files'])}")
    print(f"  - Total entries: {sum(f['entries'] for f in metadata['files'].values())}")
    print(f"  - Data directory: {GAME_DATA_DIR}")
    print("=" * 60)

    return len(metadata['files']) > 0

def load_game_data(data_type: str) -> Optional[Dict]:
    """
    로컬에 저장된 게임 데이터 로드

    Args:
        data_type: 데이터 타입 (uniques, gems, bases 등)

    Returns:
        게임 데이터 딕셔너리
    """
    file_path = os.path.join(GAME_DATA_DIR, f"{data_type}.json")

    if not os.path.exists(file_path):
        print(f"[WARN] {data_type}.json not found. Run --download first.")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {data_type}.json: {e}")
        return None

def get_metadata() -> Optional[Dict]:
    """메타데이터 로드"""
    if not os.path.exists(METADATA_FILE):
        return None

    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load metadata: {e}")
        return None

def check_data_integrity() -> bool:
    """
    게임 데이터 무결성 검사

    Returns:
        데이터가 유효한지 여부
    """
    metadata = get_metadata()
    if not metadata:
        print("[ERROR] No metadata found. Data not downloaded.")
        return False

    print("=" * 60)
    print("Data Integrity Check")
    print("=" * 60)
    print(f"Downloaded at: {metadata.get('downloaded_at', 'Unknown')}")
    print(f"Version: {metadata.get('version', 'Unknown')}")
    print()

    all_valid = True
    for data_name, info in metadata.get('files', {}).items():
        file_path = os.path.join(GAME_DATA_DIR, info['file'])
        exists = os.path.exists(file_path)
        status = "[OK]" if exists else "[MISSING]"
        print(f"{status} {data_name:15s} - {info['entries']:4d} entries")

        if not exists:
            all_valid = False

    print("=" * 60)

    # 최소 데이터 개수 검증
    expected_minimums = {
        "uniques": 100,   # 최소 100개 이상의 유니크
        "gems": 50        # 최소 50개 이상의 젬
    }

    for data_name, min_count in expected_minimums.items():
        if data_name in metadata.get('files', {}):
            actual = metadata['files'][data_name]['entries']
            if actual < min_count:
                print(f"[WARN] {data_name} has only {actual} entries (expected >={min_count})")
                all_valid = False

    if all_valid:
        print("[OK] All data files are valid")
    else:
        print("[ERROR] Some data files are missing or incomplete")

    return all_valid

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='POB Game Data Fetcher')
    parser.add_argument('--download', action='store_true', help='Download all game data from POB')
    parser.add_argument('--check', action='store_true', help='Check data integrity')
    parser.add_argument('--stats', action='store_true', help='Show data statistics')
    parser.add_argument('--load', type=str, help='Load specific data type (uniques, gems, etc.)')

    args = parser.parse_args()

    if args.download:
        success = download_pob_data()
        if success:
            check_data_integrity()

    elif args.check:
        check_data_integrity()

    elif args.stats:
        metadata = get_metadata()
        if metadata:
            print(json.dumps(metadata, indent=2, ensure_ascii=False))
        else:
            print("[ERROR] No data found. Run --download first.")

    elif args.load:
        data = load_game_data(args.load)
        if data:
            print(f"Loaded {len(data)} entries from {args.load}.json")
            # 처음 3개 항목만 출력
            for i, (key, value) in enumerate(list(data.items())[:3]):
                print(f"\n{key}:")
                print(json.dumps(value, indent=2, ensure_ascii=False))
        else:
            print(f"[ERROR] Failed to load {args.load}")

    else:
        parser.print_help()
