# -*- coding: utf-8 -*-

"""
poe.ninja API Fetcher
Complete POE game data collection from poe.ninja API
"""

import requests
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# poe.ninja API Configuration
POE_NINJA_BASE = "https://poe.ninja/api/data"
POE_NINJA_BUILDS = "https://poe.ninja/api/data/GetBuildOverview"
IMAGE_CDN_BASE = "https://web.poecdn.com"
HEADERS = {'User-Agent': 'PathcraftAI/1.0'}

# Data Storage
GAME_DATA_DIR = os.path.join(os.path.dirname(__file__), "game_data")
IMAGES_DIR = os.path.join(GAME_DATA_DIR, "images")
METADATA_FILE = os.path.join(GAME_DATA_DIR, "poe_ninja_metadata.json")

# Available Item Categories
ITEM_CATEGORIES = {
    # Unique Items
    "unique_weapons": "UniqueWeapon",
    "unique_armours": "UniqueArmour",
    "unique_accessories": "UniqueAccessory",
    "unique_flasks": "UniqueFlask",
    "unique_jewels": "UniqueJewel",
    "unique_maps": "UniqueMap",
    "unique_relics": "UniqueRelic",

    # Currency & Fragments
    "currency": "Currency",
    "fragments": "Fragment",
    "divination_cards": "DivinationCard",
    "oils": "Oil",
    "incubators": "Incubator",
    "scarabs": "Scarab",
    "fossils": "Fossil",
    "resonators": "Resonator",
    "essences": "Essence",
    "vials": "Vial",

    # Gems
    "skill_gems": "SkillGem",

    # Base Items
    "base_types": "BaseType",

    # Maps
    "maps": "Map",
    "blighted_maps": "BlightedMap",
    "blight_ravaged_maps": "BlightRavagedMap",

    # Beasts
    "beasts": "Beast",

    # Delirium
    "delirium_orbs": "DeliriumOrb",

    # Catalysts
    "catalysts": "Catalyst",

    # Invitations
    "invitations": "Invitation",

    # Memories
    "memories": "Memory",

    # Tattoos
    "tattoos": "Tattoo",

    # Omens
    "omens": "Omen",

    # Coffins
    "coffins": "Coffin"
}

def ensure_directories():
    """Create necessary directories"""
    os.makedirs(GAME_DATA_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    print(f"[INFO] Directories ready: {GAME_DATA_DIR}")

def get_current_leagues() -> List[str]:
    """
    Get current active leagues from poe.ninja

    Returns:
        List of league names (e.g., ['Settlers', 'Hardcore Settlers', 'Standard'])
    """
    try:
        # poe.ninja itemoverview endpoint를 사용하여 활성 리그 확인
        url = "https://poe.ninja/api/data/itemoverview"

        # Note: poe.ninja는 짧은 리그 이름 사용
        # 2025년 11월 기준: Keepers (3.27 - Keepers of the Flame) 현재 활성
        test_leagues = [
            'Keepers',              # Current challenge league (3.27)
            'Hardcore Keepers',
            'SSF Keepers',
            'HC SSF Keepers',
            'Ruthless Keepers',
            'HC Ruthless Keepers',
            'SSF R Keepers',
            'HC SSF R Keepers',
            'Standard',
            'Hardcore'
        ]

        active_leagues = []
        for league in test_leagues:
            try:
                test_response = requests.get(
                    url,
                    params={'type': 'UniqueWeapon', 'league': league},
                    headers=HEADERS,
                    timeout=5
                )
                # 데이터가 있으면 활성 리그로 간주
                if test_response.status_code == 200:
                    data = test_response.json()
                    if data.get('lines') and len(data['lines']) > 0:
                        active_leagues.append(league)
            except:
                continue

        if active_leagues:
            print(f"[INFO] Found active leagues: {', '.join(active_leagues)}")
            return active_leagues

    except Exception as e:
        print(f"[WARN] Failed to fetch leagues: {e}")

    # Fallback: Standard is always available
    return ['Standard']

def get_latest_temp_league() -> str:
    """
    Get the latest temporary league (challenge league)

    Returns:
        League name (e.g., 'Settlers')
    """
    leagues = get_current_leagues()

    # Filter out permanent leagues
    temp_leagues = [l for l in leagues if l not in ['Standard', 'Hardcore']
                    and 'Hardcore' not in l]

    if temp_leagues:
        return temp_leagues[0]

    # Fallback to Standard if no temp league found
    return 'Standard'

def fetch_category_data(league: str, category_key: str, category_type: str) -> Optional[Dict[str, Any]]:
    """
    Fetch data for a specific category from poe.ninja

    Args:
        league: League name (e.g., 'Standard')
        category_key: Internal category key (e.g., 'unique_weapons')
        category_type: poe.ninja API type (e.g., 'UniqueWeapon')

    Returns:
        API response data or None
    """
    url = f"{POE_NINJA_BASE}/itemoverview"
    params = {
        'league': league,
        'type': category_type
    }

    try:
        print(f"[INFO] Fetching {category_key} ({category_type})...")
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        lines = data.get('lines', [])
        print(f"[OK] {category_key}: {len(lines)} items")

        return {
            'category': category_key,
            'type': category_type,
            'league': league,
            'items': lines,
            'fetched_at': datetime.now().isoformat()
        }

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"[SKIP] {category_key}: Not available for {league}")
        else:
            print(f"[ERROR] {category_key}: HTTP {e.response.status_code}")
        return None
    except Exception as e:
        print(f"[ERROR] {category_key}: {e}")
        return None

def fetch_build_overview(league: str = 'Standard', overview: str = 'delirium') -> Optional[Dict[str, Any]]:
    """
    Fetch build overview data from poe.ninja

    Args:
        league: League name
        overview: Overview type (delirium, heist, etc.)

    Returns:
        Build overview data with character details
    """
    params = {
        'league': league,
        'overview': overview
    }

    try:
        print(f"[INFO] Fetching build overview for {league} ({overview})...")
        response = requests.get(POE_NINJA_BUILDS, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        builds = data.get('builds', [])
        print(f"[OK] Build overview: {len(builds)} characters")

        return {
            'league': league,
            'overview': overview,
            'builds': builds,
            'fetched_at': datetime.now().isoformat()
        }

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"[SKIP] Build overview: Not available for {league}")
        else:
            print(f"[ERROR] Build overview: HTTP {e.response.status_code}")
        return None
    except Exception as e:
        print(f"[ERROR] Build overview: {e}")
        return None

def analyze_builds_by_item(builds_data: Dict, item_name: str) -> Dict[str, Any]:
    """
    Analyze builds that use a specific item

    Args:
        builds_data: Build overview data
        item_name: Item name to search for (e.g., "Death's Oath")

    Returns:
        Analysis results
    """
    if not builds_data or 'builds' not in builds_data:
        return {}

    matching_builds = []
    for build in builds_data['builds']:
        # Check all equipped items
        items = build.get('items', [])
        if any(item_name.lower() in item.get('name', '').lower() for item in items):
            matching_builds.append(build)

    if not matching_builds:
        return {
            'item': item_name,
            'count': 0,
            'message': f"No builds found using {item_name}"
        }

    # Analyze patterns
    ascendancies = {}
    main_skills = {}
    common_items = {}
    levels = []

    for build in matching_builds:
        # Ascendancy distribution
        asc = build.get('class', 'Unknown')
        ascendancies[asc] = ascendancies.get(asc, 0) + 1

        # Main skill distribution
        skill = build.get('mainSkill', {}).get('name', 'Unknown')
        main_skills[skill] = main_skills.get(skill, 0) + 1

        # Common items
        for item in build.get('items', []):
            name = item.get('name', '')
            if name and name.lower() != item_name.lower():
                common_items[name] = common_items.get(name, 0) + 1

        # Level distribution
        level = build.get('level', 0)
        if level:
            levels.append(level)

    # Sort by frequency
    top_ascendancies = sorted(ascendancies.items(), key=lambda x: x[1], reverse=True)[:5]
    top_skills = sorted(main_skills.items(), key=lambda x: x[1], reverse=True)[:5]
    top_items = sorted(common_items.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        'item': item_name,
        'total_builds': len(matching_builds),
        'ascendancies': [{'name': name, 'count': count, 'percentage': round(count/len(matching_builds)*100, 1)}
                         for name, count in top_ascendancies],
        'main_skills': [{'name': name, 'count': count, 'percentage': round(count/len(matching_builds)*100, 1)}
                        for name, count in top_skills],
        'common_items': [{'name': name, 'count': count, 'percentage': round(count/len(matching_builds)*100, 1)}
                         for name, count in top_items],
        'average_level': round(sum(levels) / len(levels), 1) if levels else 0,
        'min_level': min(levels) if levels else 0,
        'max_level': max(levels) if levels else 0
    }

def download_image(image_url: str, category: str) -> Optional[str]:
    """
    Download image from CDN

    Args:
        image_url: Full or relative image URL
        category: Category name for organizing images

    Returns:
        Local file path or None
    """
    try:
        # Handle relative URLs
        if image_url.startswith('/'):
            full_url = f"{IMAGE_CDN_BASE}{image_url}"
        else:
            full_url = image_url

        # Create category directory
        category_dir = os.path.join(IMAGES_DIR, category)
        os.makedirs(category_dir, exist_ok=True)

        # Generate filename from URL
        filename = image_url.split('/')[-1].split('?')[0]  # Remove query params
        if not filename:
            return None

        local_path = os.path.join(category_dir, filename)

        # Skip if already downloaded
        if os.path.exists(local_path):
            return local_path

        # Download image
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        with open(local_path, 'wb') as f:
            f.write(response.content)

        return local_path

    except Exception as e:
        print(f"[WARN] Failed to download image {image_url}: {e}")
        return None

def download_images_parallel(items: List[Dict], category: str, max_workers: int = 10) -> int:
    """
    Download images in parallel

    Args:
        items: List of items with 'icon' field
        category: Category name
        max_workers: Number of parallel downloads

    Returns:
        Number of successfully downloaded images
    """
    image_urls = [item.get('icon') for item in items if item.get('icon')]

    if not image_urls:
        return 0

    print(f"[INFO] Downloading {len(image_urls)} images for {category}...")

    downloaded = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_image, url, category): url for url in image_urls}

        for future in as_completed(futures):
            if future.result():
                downloaded += 1

    print(f"[OK] Downloaded {downloaded}/{len(image_urls)} images for {category}")
    return downloaded

def collect_all_data(league: str = 'Standard', download_images_flag: bool = False, collect_builds: bool = True) -> Dict[str, Any]:
    """
    Collect all game data from poe.ninja

    Args:
        league: League name
        download_images_flag: Whether to download item images
        collect_builds: Whether to collect build overview data

    Returns:
        Collection metadata
    """
    ensure_directories()

    print("=" * 60)
    print("poe.ninja Data Collector")
    print("=" * 60)
    print(f"League: {league}")
    print(f"Categories: {len(ITEM_CATEGORIES)}")
    print(f"Build data: {'Yes' if collect_builds else 'No'}")
    print("=" * 60)

    metadata = {
        "version": "1.0",
        "collected_at": datetime.now().isoformat(),
        "league": league,
        "categories": {},
        "builds": None,
        "statistics": {
            "total_items": 0,
            "total_images": 0,
            "total_builds": 0,
            "successful_categories": 0,
            "failed_categories": 0
        }
    }

    # Fetch all categories
    for category_key, category_type in ITEM_CATEGORIES.items():
        data = fetch_category_data(league, category_key, category_type)

        if not data:
            metadata['statistics']['failed_categories'] += 1
            continue

        # Save category data
        output_file = os.path.join(GAME_DATA_DIR, f"{category_key}.json")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            item_count = len(data['items'])
            metadata['categories'][category_key] = {
                'file': f"{category_key}.json",
                'type': category_type,
                'item_count': item_count,
                'fetched_at': data['fetched_at']
            }

            metadata['statistics']['total_items'] += item_count
            metadata['statistics']['successful_categories'] += 1

            # Download images if enabled
            if download_images_flag:
                downloaded = download_images_parallel(data['items'], category_key)
                metadata['categories'][category_key]['images_downloaded'] = downloaded
                metadata['statistics']['total_images'] += downloaded

        except Exception as e:
            print(f"[ERROR] Failed to save {category_key}: {e}")
            metadata['statistics']['failed_categories'] += 1

        # Rate limiting
        time.sleep(0.5)

    # Collect build overview data
    if collect_builds:
        print()
        print("=" * 60)
        print("Collecting Build Overview Data")
        print("=" * 60)

        builds_data = fetch_build_overview(league)
        if builds_data:
            # Save build overview
            builds_file = os.path.join(GAME_DATA_DIR, "builds_overview.json")
            try:
                with open(builds_file, 'w', encoding='utf-8') as f:
                    json.dump(builds_data, f, ensure_ascii=False, indent=2)

                build_count = len(builds_data['builds'])
                metadata['builds'] = {
                    'file': 'builds_overview.json',
                    'build_count': build_count,
                    'fetched_at': builds_data['fetched_at']
                }
                metadata['statistics']['total_builds'] = build_count
                print(f"[OK] Saved builds_overview.json ({build_count} characters)")

            except Exception as e:
                print(f"[ERROR] Failed to save builds data: {e}")

    # Save metadata
    try:
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"[OK] Metadata saved")
    except Exception as e:
        print(f"[ERROR] Failed to save metadata: {e}")

    # Summary
    print("=" * 60)
    print("Collection Summary:")
    print(f"  - Successful categories: {metadata['statistics']['successful_categories']}")
    print(f"  - Failed categories: {metadata['statistics']['failed_categories']}")
    print(f"  - Total items: {metadata['statistics']['total_items']}")
    print(f"  - Total builds: {metadata['statistics']['total_builds']}")
    if download_images_flag:
        print(f"  - Total images: {metadata['statistics']['total_images']}")
    print(f"  - Data directory: {GAME_DATA_DIR}")
    print("=" * 60)

    return metadata

def load_category_data(category: str) -> Optional[Dict]:
    """
    Load category data from local storage

    Args:
        category: Category key (e.g., 'unique_weapons')

    Returns:
        Category data or None
    """
    file_path = os.path.join(GAME_DATA_DIR, f"{category}.json")

    if not os.path.exists(file_path):
        print(f"[WARN] {category}.json not found. Run --collect first.")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {category}: {e}")
        return None

def get_metadata() -> Optional[Dict]:
    """Load collection metadata"""
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
    Check data integrity and completeness

    Returns:
        True if data is valid
    """
    metadata = get_metadata()
    if not metadata:
        print("[ERROR] No metadata found. Run --collect first.")
        return False

    print("=" * 60)
    print("Data Integrity Check")
    print("=" * 60)
    print(f"Collected at: {metadata.get('collected_at', 'Unknown')}")
    print(f"League: {metadata.get('league', 'Unknown')}")
    print()

    all_valid = True
    for category, info in metadata.get('categories', {}).items():
        file_path = os.path.join(GAME_DATA_DIR, info['file'])
        exists = os.path.exists(file_path)
        status = "[OK]" if exists else "[MISSING]"

        item_count = info['item_count']
        images = info.get('images_downloaded', 0)
        print(f"{status} {category:25s} - {item_count:5d} items, {images:5d} images")

        if not exists:
            all_valid = False

    print("=" * 60)

    # Minimum expected items per category
    expected_minimums = {
        "unique_weapons": 100,
        "unique_armours": 100,
        "currency": 10,
        "skill_gems": 200
    }

    for category, min_count in expected_minimums.items():
        if category in metadata.get('categories', {}):
            actual = metadata['categories'][category]['item_count']
            if actual < min_count:
                print(f"[WARN] {category} has only {actual} items (expected >={min_count})")
                all_valid = False

    if all_valid:
        print("[OK] All data files are valid and complete")
    else:
        print("[ERROR] Some data files are missing or incomplete")

    return all_valid

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='poe.ninja Game Data Fetcher')
    parser.add_argument('--collect', action='store_true', help='Collect all game data')
    parser.add_argument('--league', type=str, help='League name (default: auto-detect latest temp league)')
    parser.add_argument('--no-images', action='store_true', help='Skip image downloads')
    parser.add_argument('--no-builds', action='store_true', help='Skip build overview collection')
    parser.add_argument('--check', action='store_true', help='Check data integrity')
    parser.add_argument('--stats', action='store_true', help='Show collection statistics')
    parser.add_argument('--load', type=str, help='Load specific category data')
    parser.add_argument('--analyze-item', type=str, help='Analyze builds using specific item (e.g., "Death\'s Oath")')
    parser.add_argument('--show-leagues', action='store_true', help='Show currently active leagues')

    args = parser.parse_args()

    if args.show_leagues:
        leagues = get_current_leagues()
        latest = get_latest_temp_league()
        print("=" * 60)
        print("Active Leagues:")
        for league in leagues:
            marker = " [LATEST TEMP]" if league == latest else ""
            print(f"  - {league}{marker}")
        print("=" * 60)

    elif args.collect:
        # Auto-detect league if not specified
        league = args.league if args.league else get_latest_temp_league()
        print(f"[INFO] Using league: {league}")

        download_images = not args.no_images
        collect_builds = not args.no_builds
        metadata = collect_all_data(
            league=league,
            download_images_flag=download_images,
            collect_builds=collect_builds
        )
        if metadata:
            check_data_integrity()

    elif args.check:
        check_data_integrity()

    elif args.stats:
        metadata = get_metadata()
        if metadata:
            print(json.dumps(metadata, indent=2, ensure_ascii=False))
        else:
            print("[ERROR] No data found. Run --collect first.")

    elif args.load:
        data = load_category_data(args.load)
        if data:
            print(f"Loaded {len(data['items'])} items from {args.load}")
            # Show first 3 items
            for i, item in enumerate(data['items'][:3]):
                print(f"\n{i+1}. {item.get('name', 'Unknown')}:")
                print(json.dumps(item, indent=2, ensure_ascii=False))
        else:
            print(f"[ERROR] Failed to load {args.load}")

    elif args.analyze_item:
        # Load builds data
        builds_file = os.path.join(GAME_DATA_DIR, "builds_overview.json")
        if not os.path.exists(builds_file):
            print("[ERROR] No builds data found. Run --collect first.")
        else:
            try:
                with open(builds_file, 'r', encoding='utf-8') as f:
                    builds_data = json.load(f)

                print("=" * 60)
                print(f"Analyzing builds using: {args.analyze_item}")
                print("=" * 60)

                analysis = analyze_builds_by_item(builds_data, args.analyze_item)
                print(json.dumps(analysis, indent=2, ensure_ascii=False))

            except Exception as e:
                print(f"[ERROR] Failed to analyze: {e}")

    else:
        parser.print_help()
