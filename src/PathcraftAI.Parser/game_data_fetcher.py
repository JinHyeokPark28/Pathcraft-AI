# -*- coding: utf-8 -*-

"""
POB (Path of Building) 게임 데이터 다운로더
POB GitHub에서 게임 데이터를 다운로드하여 JSON으로 변환
"""

import requests
import json
import os
import re
import subprocess
import glob
from typing import Dict, Any, Optional, List
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
POB_REPO_URL = "https://github.com/PathOfBuildingCommunity/PathOfBuilding.git"

HEADERS = {'User-Agent': 'PathcraftAI/1.0'}

# 게임 데이터 저장 디렉토리
GAME_DATA_DIR = os.path.join(os.path.dirname(__file__), "game_data")
POB_REPO_DIR = os.path.join(os.path.dirname(__file__), "pob_repo")
POB_DATA_DIR = os.path.join(POB_REPO_DIR, "src", "Data")
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

    POB 형식: [[ItemName\nBaseType\nVariant: ...\nRequires Level X\n...]]

    Returns:
        {
            "item_name": {
                "name": "The Anvil",
                "base_type": "Amber Amulet",
                "level_req": 45,
                "implicits": [...],
                "mods": [...],
                "source": "pob"
            }
        }
    """
    unique_items = {}

    # [[ ... ]] 블록 추출
    pattern = r'\[\[(.*?)\]\]'
    matches = re.findall(pattern, lua_content, re.DOTALL)

    for item_block in matches:
        lines = [line.strip() for line in item_block.strip().split('\n') if line.strip()]

        if len(lines) < 2:
            continue

        item_name = lines[0]
        base_type = lines[1]

        item_data = {
            "name": item_name,
            "base_type": base_type,
            "source": "pob"
        }

        mods = []
        implicits = []
        implicit_count = 0

        for line in lines[2:]:
            # Variant 처리
            if line.startswith("Variant:"):
                if "variants" not in item_data:
                    item_data["variants"] = []
                item_data["variants"].append(line.replace("Variant:", "").strip())

            # 레벨 요구사항
            elif "Requires Level" in line or "LevelReq:" in line:
                level_match = re.search(r'(\d+)', line)
                if level_match:
                    item_data["level_req"] = int(level_match.group(1))

            # Implicits 카운트
            elif line.startswith("Implicits:"):
                implicit_match = re.search(r'(\d+)', line)
                if implicit_match:
                    implicit_count = int(implicit_match.group(1))

            # Source
            elif line.startswith("Source:"):
                item_data["source_info"] = line.replace("Source:", "").strip()

            # 일반 모드 라인
            elif not line.startswith("--"):
                # {tags:...} 제거
                clean_line = re.sub(r'\{[^}]+\}', '', line).strip()
                if clean_line:
                    if implicit_count > 0:
                        implicits.append(clean_line)
                        implicit_count -= 1
                    else:
                        mods.append(clean_line)

        if implicits:
            item_data["implicits"] = implicits
        if mods:
            item_data["mods"] = mods

        # 이름을 키로 사용
        unique_items[item_name] = item_data

    return unique_items

def extract_skill_gems(lua_content: str) -> Dict[str, Any]:
    """
    Gems.lua에서 스킬 젬 추출 (태그, 레벨 요구사항 포함)

    Returns:
        {
            "gem_id": {
                "name": "Fireball",
                "tags": ["spell", "projectile", "area", "fire"],
                "tagString": "Projectile, Spell, AoE, Fire",
                "reqStr": 0,
                "reqDex": 0,
                "reqInt": 100,
                "naturalMaxLevel": 20,
                "color": "intelligence",
                "isSupport": False,
                "isVaal": False
            }
        }
    """
    gems = {}

    # 젬 블록 추출: 각 젬은 { 로 시작하고 }, 로 끝남
    # name = "..." 패턴으로 블록 시작점 찾기
    # 블록 끝은 다음 블록 시작 전까지

    # 모든 name = "..." 위치 찾기
    name_pattern = r'name\s*=\s*"([^"]+)"'
    name_matches = list(re.finditer(name_pattern, lua_content))

    for i, name_match in enumerate(name_matches):
        gem_name = name_match.group(1)
        start_pos = name_match.start()

        # 다음 젬 시작 위치 또는 파일 끝
        if i + 1 < len(name_matches):
            end_pos = name_matches[i + 1].start()
        else:
            end_pos = len(lua_content)

        gem_content = lua_content[start_pos:end_pos]

        # gameId 추출
        game_id_match = re.search(r'gameId\s*=\s*"([^"]+)"', gem_content)
        gem_id = game_id_match.group(1) if game_id_match else gem_name

        gem_data = {
            "gem_id": gem_id,
            "name": gem_name,
            "source": "pob"
        }

        # tagString 추출 (읽기 쉬운 태그)
        tag_string_match = re.search(r'tagString\s*=\s*"([^"]*)"', gem_content)
        if tag_string_match:
            gem_data["tagString"] = tag_string_match.group(1)
            # tagString에서 태그 리스트 생성
            tags = [t.strip().lower() for t in tag_string_match.group(1).split(',') if t.strip()]
            gem_data["tags"] = tags
        else:
            gem_data["tags"] = []
            gem_data["tagString"] = ""

        # 스탯 요구사항 추출
        req_str = re.search(r'reqStr\s*=\s*(\d+)', gem_content)
        req_dex = re.search(r'reqDex\s*=\s*(\d+)', gem_content)
        req_int = re.search(r'reqInt\s*=\s*(\d+)', gem_content)

        gem_data["reqStr"] = int(req_str.group(1)) if req_str else 0
        gem_data["reqDex"] = int(req_dex.group(1)) if req_dex else 0
        gem_data["reqInt"] = int(req_int.group(1)) if req_int else 0

        # 젬 색상 결정 (주요 스탯 기반)
        if gem_data["reqInt"] > gem_data["reqStr"] and gem_data["reqInt"] > gem_data["reqDex"]:
            gem_data["color"] = "blue"
        elif gem_data["reqDex"] > gem_data["reqStr"]:
            gem_data["color"] = "green"
        elif gem_data["reqStr"] > 0:
            gem_data["color"] = "red"
        else:
            gem_data["color"] = "white"

        # naturalMaxLevel 추출
        max_level = re.search(r'naturalMaxLevel\s*=\s*(\d+)', gem_content)
        gem_data["naturalMaxLevel"] = int(max_level.group(1)) if max_level else 20

        # 서포트 젬 여부
        gem_data["isSupport"] = "support" in gem_data["tagString"].lower() or "Support" in gem_data.get("name", "")

        # Vaal 젬 여부
        gem_data["isVaal"] = "vaal" in gem_data.get("name", "").lower() or "vaalGem" in gem_content

        # 젬 ID에서 간단한 키 생성
        simple_id = gem_id.split("/")[-1].replace("SkillGem", "").replace("SupportGem", "")
        gems[simple_id] = gem_data

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

# =============================================================================
# POB Repository Clone/Update Functions
# =============================================================================

def clone_pob_repo() -> bool:
    """
    POB GitHub 저장소를 클론 또는 업데이트

    Returns:
        성공 여부
    """
    print("=" * 60)
    print("POB Repository Clone/Update")
    print("=" * 60)

    if os.path.exists(POB_REPO_DIR):
        # 이미 존재하면 pull
        print(f"[INFO] Repository exists at {POB_REPO_DIR}")
        print("[INFO] Pulling latest changes...")

        try:
            result = subprocess.run(
                ["git", "pull"],
                cwd=POB_REPO_DIR,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                print(f"[OK] Pull successful")
                print(result.stdout)
                return True
            else:
                print(f"[ERROR] Pull failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("[ERROR] Git pull timed out")
            return False
        except Exception as e:
            print(f"[ERROR] Git pull failed: {e}")
            return False
    else:
        # 새로 클론
        print(f"[INFO] Cloning POB repository...")
        print(f"[INFO] This may take a few minutes...")

        try:
            # 얕은 클론으로 속도 향상 (히스토리 제한)
            result = subprocess.run(
                ["git", "clone", "--depth", "1", POB_REPO_URL, POB_REPO_DIR],
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode == 0:
                print(f"[OK] Clone successful")
                print(f"[OK] Repository saved to: {POB_REPO_DIR}")
                return True
            else:
                print(f"[ERROR] Clone failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("[ERROR] Git clone timed out")
            return False
        except Exception as e:
            print(f"[ERROR] Git clone failed: {e}")
            return False

def get_pob_version() -> str:
    """POB 버전 정보 가져오기"""
    manifest_path = os.path.join(POB_REPO_DIR, "src", "manifest.xml")

    if not os.path.exists(manifest_path):
        return "unknown"

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 버전 추출
        match = re.search(r'<Version\s+number="([^"]+)"', content)
        if match:
            return match.group(1)
    except:
        pass

    return "unknown"

# =============================================================================
# Extended Data Extraction Functions
# =============================================================================

def extract_mod_data(lua_content: str, file_name: str = "") -> Dict[str, Any]:
    """
    ModItem.lua, ModFlask.lua 등에서 모드 데이터 추출

    POB 형식: ["ModId"] = { type = "Suffix", affix = "of the Brute", "+(8-12) to Strength", statOrder = { 1090 }, level = 1, group = "Strength", weightKey = { "ring", "amulet", ... }, weightVal = { 1000, 1000, ... }, modTags = { "attribute" }, },

    Returns:
        {
            "mod_id": {
                "type": "Prefix" or "Suffix",
                "affix": "Glinting",
                "stats": ["Adds 1 to 2 Physical Damage"],
                "level": 5,
                "group": "AddedPhysicalDamage",
                "tags": ["physical_damage", "damage"],
                "weight_keys": ["claw", "dagger"],
                "weight_vals": [1000, 1000]
            }
        }
    """
    mods = {}

    # 각 줄을 처리 (한 줄에 하나의 모드)
    for line in lua_content.split('\n'):
        line = line.strip()
        if not line.startswith('["'):
            continue

        # 모드 ID 추출
        mod_id_match = re.match(r'\["([^"]+)"\]\s*=\s*\{(.+)\},?\s*$', line)
        if not mod_id_match:
            continue

        mod_id = mod_id_match.group(1)
        mod_content = mod_id_match.group(2)

        mod_data = {
            "mod_id": mod_id,
            "source": file_name
        }

        # type (Prefix/Suffix)
        type_match = re.search(r'type\s*=\s*"([^"]+)"', mod_content)
        if type_match:
            mod_data["type"] = type_match.group(1)

        # affix 이름
        affix_match = re.search(r'affix\s*=\s*"([^"]*)"', mod_content)
        if affix_match:
            mod_data["affix"] = affix_match.group(1)

        # 모드 텍스트 (따옴표로 감싸진 문자열 중 키=값 형태가 아닌 것)
        # 예: "+(8-12) to Strength"
        stat_texts = []
        for m in re.finditer(r'"([^"]+)"', mod_content):
            text = m.group(1)
            # 키=값 형태가 아닌 독립적인 문자열 (앞에 = 가 없음)
            start = m.start()
            if start > 0 and mod_content[start-1] != '=' and mod_content[start-2:start] != '= ':
                # affix, type, group 값이 아닌지 확인
                if text not in [mod_data.get("type", ""), mod_data.get("affix", "")]:
                    # weightKey, modTags 안의 값이 아닌지 확인
                    if not any(text == k for k in ["ring", "amulet", "belt", "default", "attribute", "resource", "life", "mana", "damage", "physical", "attack", "caster", "speed", "critical"]):
                        stat_texts.append(text)

        # 더 정확한 스탯 추출: 괄호나 숫자 포함된 것
        stats = []
        for text in stat_texts:
            if any(c in text for c in ['(', '+', '-', '%']) or any(c.isdigit() for c in text):
                stats.append(text)
        if stats:
            mod_data["stats"] = stats

        # level
        level_match = re.search(r'level\s*=\s*(\d+)', mod_content)
        if level_match:
            mod_data["level"] = int(level_match.group(1))

        # group
        group_match = re.search(r'group\s*=\s*"([^"]+)"', mod_content)
        if group_match:
            mod_data["group"] = group_match.group(1)

        # statOrder (stat IDs)
        stat_order_match = re.search(r'statOrder\s*=\s*\{([^}]+)\}', mod_content)
        if stat_order_match:
            stat_ids = re.findall(r'\d+', stat_order_match.group(1))
            mod_data["stat_order"] = [int(sid) for sid in stat_ids]

        # modTags
        mod_tags_match = re.search(r'modTags\s*=\s*\{([^}]+)\}', mod_content)
        if mod_tags_match:
            tags = re.findall(r'"([^"]+)"', mod_tags_match.group(1))
            mod_data["tags"] = tags

        # weightKey (item types)
        weight_key_match = re.search(r'weightKey\s*=\s*\{([^}]+)\}', mod_content)
        if weight_key_match:
            keys = re.findall(r'"([^"]+)"', weight_key_match.group(1))
            mod_data["weight_keys"] = keys

        # weightVal
        weight_val_match = re.search(r'weightVal\s*=\s*\{([^}]+)\}', mod_content)
        if weight_val_match:
            vals = re.findall(r'\d+', weight_val_match.group(1))
            mod_data["weight_vals"] = [int(v) for v in vals]

        mods[mod_id] = mod_data

    return mods

def extract_item_bases(lua_content: str, category: str = "") -> Dict[str, Any]:
    """
    베이스 아이템 데이터 추출 (Bases/*.lua)

    Returns:
        {
            "base_name": {
                "name": "Vaal Regalia",
                "type": "Body Armour",
                "implicit": [...],
                "req": {"level": 68, "es": 194}
            }
        }
    """
    bases = {}

    # 베이스 아이템 패턴
    pattern = r'\["([^"]+)"\]\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'
    matches = re.finditer(pattern, lua_content, re.DOTALL)

    for match in matches:
        base_name = match.group(1)
        base_content = match.group(2)

        base_data = {
            "name": base_name,
            "category": category
        }

        # type
        type_match = re.search(r'type\s*=\s*"([^"]+)"', base_content)
        if type_match:
            base_data["type"] = type_match.group(1)

        # implicit
        implicit_match = re.search(r'implicit\s*=\s*"([^"]*)"', base_content)
        if implicit_match:
            base_data["implicit"] = implicit_match.group(1)

        # 요구사항
        req = {}
        req_level = re.search(r'req\s*=\s*\{[^}]*level\s*=\s*(\d+)', base_content)
        if req_level:
            req["level"] = int(req_level.group(1))

        req_str = re.search(r'req\s*=\s*\{[^}]*str\s*=\s*(\d+)', base_content)
        if req_str:
            req["str"] = int(req_str.group(1))

        req_dex = re.search(r'req\s*=\s*\{[^}]*dex\s*=\s*(\d+)', base_content)
        if req_dex:
            req["dex"] = int(req_dex.group(1))

        req_int = re.search(r'req\s*=\s*\{[^}]*int\s*=\s*(\d+)', base_content)
        if req_int:
            req["int"] = int(req_int.group(1))

        if req:
            base_data["req"] = req

        bases[base_name] = base_data

    return bases

def extract_pantheons(lua_content: str) -> Dict[str, Any]:
    """
    판테온 데이터 추출
    """
    pantheons = {}

    # 판테온 패턴
    pattern = r'\["([^"]+)"\]\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'
    matches = re.finditer(pattern, lua_content, re.DOTALL)

    for match in matches:
        name = match.group(1)
        content = match.group(2)

        pantheon_data = {"name": name}

        # souls
        souls_match = re.search(r'souls\s*=\s*(\d+)', content)
        if souls_match:
            pantheon_data["souls"] = int(souls_match.group(1))

        # mods
        mods = re.findall(r'"([^"]+)"', content)
        if mods:
            pantheon_data["mods"] = mods

        pantheons[name] = pantheon_data

    return pantheons

def extract_essence(lua_content: str) -> Dict[str, Any]:
    """
    에센스 데이터 추출
    """
    essences = {}

    pattern = r'\["([^"]+)"\]\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'
    matches = re.finditer(pattern, lua_content, re.DOTALL)

    for match in matches:
        name = match.group(1)
        content = match.group(2)

        essence_data = {"name": name}

        # tier
        tier_match = re.search(r'tier\s*=\s*(\d+)', content)
        if tier_match:
            essence_data["tier"] = int(tier_match.group(1))

        # mods for different item types
        mod_pattern = r'(\w+)\s*=\s*"([^"]+)"'
        for mod_match in re.finditer(mod_pattern, content):
            essence_data[mod_match.group(1)] = mod_match.group(2)

        essences[name] = essence_data

    return essences

def extract_stat_descriptions(lua_content: str) -> Dict[str, Any]:
    """
    스탯 설명 데이터 추출 (StatDescriptions/*.lua)

    Returns:
        {
            "stat_id": {
                "id": 1482,
                "text": ["+# to maximum Life"],
                "negated": False
            }
        }
    """
    stats = {}

    # 스탯 설명 패턴은 복잡한 Lua 구조
    # 간단한 패턴으로 주요 데이터 추출

    # 스탯 ID와 텍스트 매핑
    pattern = r'\[(\d+)\]\s*=\s*\{[^}]*text\s*=\s*"([^"]+)"'
    matches = re.finditer(pattern, lua_content)

    for match in matches:
        stat_id = match.group(1)
        text = match.group(2)

        stats[stat_id] = {
            "id": int(stat_id),
            "text": text
        }

    return stats

def parse_all_pob_data() -> bool:
    """
    POB 저장소의 모든 데이터를 파싱하여 JSON으로 저장

    Returns:
        성공 여부
    """
    if not os.path.exists(POB_DATA_DIR):
        print(f"[ERROR] POB Data directory not found: {POB_DATA_DIR}")
        print("[ERROR] Run --clone first to download POB repository")
        return False

    ensure_game_data_dir()

    print("=" * 60)
    print("POB Full Data Parser")
    print("=" * 60)

    pob_version = get_pob_version()
    print(f"[INFO] POB Version: {pob_version}")
    print()

    metadata = {
        "version": pob_version,
        "parsed_at": datetime.now().isoformat(),
        "files": {}
    }

    # 1. 젬 데이터 (기존)
    print("[1/8] Parsing Gems.lua...")
    gems_path = os.path.join(POB_DATA_DIR, "Gems.lua")
    if os.path.exists(gems_path):
        with open(gems_path, 'r', encoding='utf-8') as f:
            gems = extract_skill_gems(f.read())
        save_json("gems.json", gems, metadata)

    # 2. 유니크 아이템
    print("[2/8] Parsing Uniques.lua...")
    uniques_path = os.path.join(POB_DATA_DIR, "Uniques")
    if os.path.exists(uniques_path):
        all_uniques = {}
        for lua_file in glob.glob(os.path.join(uniques_path, "*.lua")):
            with open(lua_file, 'r', encoding='utf-8') as f:
                uniques = extract_unique_items(f.read())
                all_uniques.update(uniques)
        save_json("uniques.json", all_uniques, metadata)

    # 3. 모드 데이터
    print("[3/8] Parsing Mod files...")
    mod_files = [
        "ModItem.lua", "ModFlask.lua", "ModJewel.lua",
        "ModJewelAbyss.lua", "ModJewelCluster.lua",
        "ModVeiled.lua", "ModMaster.lua"
    ]
    all_mods = {}
    for mod_file in mod_files:
        mod_path = os.path.join(POB_DATA_DIR, mod_file)
        if os.path.exists(mod_path):
            with open(mod_path, 'r', encoding='utf-8') as f:
                mods = extract_mod_data(f.read(), mod_file)
                all_mods.update(mods)
                print(f"  - {mod_file}: {len(mods)} mods")
    save_json("mods.json", all_mods, metadata)

    # 4. 아이템 베이스
    print("[4/8] Parsing Base items...")
    bases_dir = os.path.join(POB_DATA_DIR, "Bases")
    all_bases = {}
    if os.path.exists(bases_dir):
        for lua_file in glob.glob(os.path.join(bases_dir, "**", "*.lua"), recursive=True):
            category = os.path.basename(os.path.dirname(lua_file))
            with open(lua_file, 'r', encoding='utf-8') as f:
                bases = extract_item_bases(f.read(), category)
                all_bases.update(bases)
        print(f"  - Total: {len(all_bases)} bases")
    save_json("item_bases.json", all_bases, metadata)

    # 5. 판테온
    print("[5/8] Parsing Pantheons.lua...")
    pantheon_path = os.path.join(POB_DATA_DIR, "Pantheons.lua")
    if os.path.exists(pantheon_path):
        with open(pantheon_path, 'r', encoding='utf-8') as f:
            pantheons = extract_pantheons(f.read())
        save_json("pantheons.json", pantheons, metadata)

    # 6. 에센스
    print("[6/8] Parsing Essence.lua...")
    essence_path = os.path.join(POB_DATA_DIR, "Essence.lua")
    if os.path.exists(essence_path):
        with open(essence_path, 'r', encoding='utf-8') as f:
            essences = extract_essence(f.read())
        save_json("essence.json", essences, metadata)

    # 7. 클러스터 주얼
    print("[7/8] Parsing ClusterJewels.lua...")
    cluster_path = os.path.join(POB_DATA_DIR, "ClusterJewels.lua")
    if os.path.exists(cluster_path):
        with open(cluster_path, 'r', encoding='utf-8') as f:
            cluster = simple_lua_to_dict(f.read())
        save_json("cluster_jewels.json", cluster, metadata)

    # 8. 스탯 설명
    print("[8/8] Parsing StatDescriptions...")
    stat_desc_dir = os.path.join(POB_DATA_DIR, "StatDescriptions")
    all_stats = {}
    if os.path.exists(stat_desc_dir):
        for lua_file in glob.glob(os.path.join(stat_desc_dir, "*.lua")):
            with open(lua_file, 'r', encoding='utf-8') as f:
                stats = extract_stat_descriptions(f.read())
                all_stats.update(stats)
        print(f"  - Total: {len(all_stats)} stat descriptions")
    save_json("stat_descriptions.json", all_stats, metadata)

    # 메타데이터 저장
    try:
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"[OK] Saved metadata.json")
    except Exception as e:
        print(f"[ERROR] Failed to save metadata: {e}")

    print()
    print("=" * 60)
    print("Parse Summary:")
    print(f"  - Files generated: {len(metadata['files'])}")
    print(f"  - Total entries: {sum(f.get('entries', 0) for f in metadata['files'].values())}")
    print(f"  - Data directory: {GAME_DATA_DIR}")
    print("=" * 60)

    return True

def save_json(filename: str, data: Dict, metadata: Dict):
    """JSON 파일 저장 헬퍼"""
    output_path = os.path.join(GAME_DATA_DIR, filename)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        entries = len(data) if isinstance(data, dict) else 0
        print(f"[OK] Saved {filename} ({entries} entries)")

        metadata["files"][filename.replace(".json", "")] = {
            "file": filename,
            "entries": entries
        }
    except Exception as e:
        print(f"[ERROR] Failed to save {filename}: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='POB Game Data Fetcher')
    parser.add_argument('--download', action='store_true', help='Download basic game data from POB (legacy)')
    parser.add_argument('--clone', action='store_true', help='Clone or update POB repository')
    parser.add_argument('--update', action='store_true', help='Update POB repository (same as --clone)')
    parser.add_argument('--parse-all', action='store_true', help='Parse all POB data to JSON')
    parser.add_argument('--check', action='store_true', help='Check data integrity')
    parser.add_argument('--stats', action='store_true', help='Show data statistics')
    parser.add_argument('--load', type=str, help='Load specific data type (uniques, gems, mods, etc.)')

    args = parser.parse_args()

    if args.clone or args.update:
        success = clone_pob_repo()
        if success:
            print()
            print("[INFO] Repository ready. Run --parse-all to extract data.")

    elif args.parse_all:
        success = parse_all_pob_data()
        if success:
            check_data_integrity()

    elif args.download:
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
            print("[ERROR] No data found. Run --clone and --parse-all first.")

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
        print()
        print("Usage examples:")
        print("  1. First time setup:")
        print("     python game_data_fetcher.py --clone")
        print("     python game_data_fetcher.py --parse-all")
        print()
        print("  2. Update after POB patch:")
        print("     python game_data_fetcher.py --update")
        print("     python game_data_fetcher.py --parse-all")
        print()
        print("  3. Check data:")
        print("     python game_data_fetcher.py --check")
        print("     python game_data_fetcher.py --load mods")
