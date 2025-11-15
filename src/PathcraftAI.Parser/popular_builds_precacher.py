# -*- coding: utf-8 -*-

"""
Popular Builds Pre-cacher
애플리케이션 설치 시 함께 제공할 인기 빌드 사전 수집

수집 대상:
1. 메타 빌드 Top 20 (각 어센던시별 인기 빌드)
2. 레벨링 빌드 (초보자용)
3. 저예산 스타터 빌드
4. 엔드게임 빌드
"""

import json
import os
from typing import List, Dict
from datetime import datetime

# 3.27 Keepers 리그 인기 빌드 키워드
POPULAR_BUILD_KEYWORDS = {
    "meta_builds": [
        "Lightning Arrow",
        "Kinetic Fusillade",
        "Righteous Fire",
        "Summon Raging Spirit",
        "Cold DoT",
        "Poison Spark",
        "Toxic Rain",
        "Explosive Arrow",
        "Reap",
        "Arc Totems"
    ],
    "starter_builds": [
        "Holy Flame Totem",
        "Splitting Steel",
        "Spectral Helix",
        "Bane Occultist",
        "Armageddon Brand",
        "Essence Drain Contagion"
    ],
    "unique_item_builds": [
        "Death's Oath",
        "Nimis",
        "Squire",
        "Mageblood",
        "Headhunter"
    ],
    "ascendancy_popular": {
        "Juggernaut": ["Righteous Fire", "Boneshatter"],
        "Berserker": ["Lightning Strike", "Splitting Steel"],
        "Chieftain": ["Righteous Fire Totem", "Slam"],
        "Slayer": ["Flicker Strike", "Cyclone"],
        "Gladiator": ["Lacerate", "Shield Crush"],
        "Champion": ["Spectral Helix", "Lightning Strike"],
        "Assassin": ["Poison Spark", "Blade Vortex"],
        "Saboteur": ["Trap", "Mine"],
        "Trickster": ["Cold DoT", "Caustic Arrow"],
        "Necromancer": ["Summon Raging Spirit", "Skeleton Mages"],
        "Occultist": ["Cold DoT", "Bane", "Death's Oath"],
        "Elementalist": ["Kinetic Fusillade", "Ignite"],
        "Deadeye": ["Lightning Arrow", "Tornado Shot"],
        "Raider": ["Elemental Hit", "Lightning Strike"],
        "Pathfinder": ["Poison", "Caustic Arrow"],
        "Inquisitor": ["Righteous Fire", "Spark"],
        "Guardian": ["Herald Stacker", "Aura Bot"],
        "Hierophant": ["Totem", "Archmage"],
        "Ascendant": ["Aura Stacker", "Spark"]
    }
}

OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__),
    "build_data",
    "precached_popular_builds.json"
)

def collect_popular_builds(max_per_category: int = 3) -> Dict:
    """
    인기 빌드 사전 수집

    Args:
        max_per_category: 카테고리당 최대 수집 빌드 수

    Returns:
        사전 수집된 빌드 데이터
    """
    from pob_link_collector import collect_builds_from_reddit
    from ladder_cache_builder import search_cache

    print("=" * 80)
    print("POPULAR BUILDS PRE-CACHING")
    print("=" * 80)
    print(f"This will collect popular builds for instant delivery to users.")
    print(f"Estimated time: 10-30 minutes")
    print("=" * 80)

    all_builds = {
        "metadata": {
            "collected_at": datetime.now().isoformat(),
            "league": "Keepers",
            "patch": "3.27",
            "purpose": "Pre-cached popular builds for instant user delivery"
        },
        "builds_by_category": {}
    }

    total_collected = 0

    # 1. 메타 빌드 수집
    print("\n[1/4] Collecting META builds...")
    meta_builds = []
    for i, keyword in enumerate(POPULAR_BUILD_KEYWORDS["meta_builds"][:10], 1):
        print(f"\n  [{i}/10] {keyword}...")
        try:
            builds = collect_builds_from_reddit(max_builds=max_per_category, keyword=keyword)
            for build in builds:
                build['category'] = 'meta'
                build['keyword'] = keyword
            meta_builds.extend(builds)
            print(f"  [OK] Collected {len(builds)} builds")
        except Exception as e:
            print(f"  [ERROR] Failed: {e}")

    all_builds["builds_by_category"]["meta"] = meta_builds
    total_collected += len(meta_builds)
    print(f"\n[META] Total: {len(meta_builds)} builds")

    # 2. 스타터 빌드 수집
    print("\n[2/4] Collecting STARTER builds...")
    starter_builds = []
    for i, keyword in enumerate(POPULAR_BUILD_KEYWORDS["starter_builds"], 1):
        print(f"\n  [{i}/{len(POPULAR_BUILD_KEYWORDS['starter_builds'])}] {keyword}...")
        try:
            builds = collect_builds_from_reddit(max_builds=max_per_category, keyword=keyword)
            for build in builds:
                build['category'] = 'starter'
                build['keyword'] = keyword
            starter_builds.extend(builds)
            print(f"  [OK] Collected {len(builds)} builds")
        except Exception as e:
            print(f"  [ERROR] Failed: {e}")

    all_builds["builds_by_category"]["starter"] = starter_builds
    total_collected += len(starter_builds)
    print(f"\n[STARTER] Total: {len(starter_builds)} builds")

    # 3. 유니크 아이템 빌드 수집
    print("\n[3/4] Collecting UNIQUE ITEM builds...")
    unique_builds = []
    for i, keyword in enumerate(POPULAR_BUILD_KEYWORDS["unique_item_builds"][:5], 1):
        print(f"\n  [{i}/5] {keyword}...")
        try:
            builds = collect_builds_from_reddit(max_builds=max_per_category, keyword=keyword)
            for build in builds:
                build['category'] = 'unique_item'
                build['keyword'] = keyword
            unique_builds.extend(builds)
            print(f"  [OK] Collected {len(builds)} builds")
        except Exception as e:
            print(f"  [ERROR] Failed: {e}")

    all_builds["builds_by_category"]["unique_item"] = unique_builds
    total_collected += len(unique_builds)
    print(f"\n[UNIQUE] Total: {len(unique_builds)} builds")

    # 4. 어센던시별 인기 빌드 (샘플)
    print("\n[4/4] Collecting ASCENDANCY-specific builds (sample)...")
    ascendancy_builds = {}
    sample_ascendancies = ["Juggernaut", "Necromancer", "Occultist", "Deadeye", "Assassin"]

    for i, asc in enumerate(sample_ascendancies, 1):
        print(f"\n  [{i}/{len(sample_ascendancies)}] {asc}...")
        asc_keywords = POPULAR_BUILD_KEYWORDS["ascendancy_popular"].get(asc, [])

        builds_for_asc = []
        for keyword in asc_keywords[:2]:  # 어센던시당 2개 키워드만
            try:
                builds = collect_builds_from_reddit(max_builds=2, keyword=f"{asc} {keyword}")
                for build in builds:
                    build['category'] = 'ascendancy'
                    build['ascendancy'] = asc
                    build['keyword'] = keyword
                builds_for_asc.extend(builds)
            except Exception as e:
                print(f"    [WARN] {keyword}: {e}")

        ascendancy_builds[asc] = builds_for_asc
        total_collected += len(builds_for_asc)
        print(f"  [OK] {asc}: {len(builds_for_asc)} builds")

    all_builds["builds_by_category"]["ascendancy"] = ascendancy_builds

    # 저장
    all_builds["metadata"]["total_builds"] = total_collected

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_builds, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("PRE-CACHING COMPLETE!")
    print("=" * 80)
    print(f"Total builds collected: {total_collected}")
    print(f"Saved to: {OUTPUT_FILE}")
    print("\nBreakdown:")
    print(f"  - Meta builds: {len(meta_builds)}")
    print(f"  - Starter builds: {len(starter_builds)}")
    print(f"  - Unique item builds: {len(unique_builds)}")
    print(f"  - Ascendancy builds: {sum(len(b) for b in ascendancy_builds.values())}")
    print("\n[NOTE] These builds will be included in the application installation")
    print("       for instant delivery to users on first search.")
    print("=" * 80)

    return all_builds

def create_leveling_guide_template():
    """레벨링 가이드 템플릿 생성"""
    leveling_guide = {
        "metadata": {
            "purpose": "Leveling guides for Acts 1-10",
            "created_at": datetime.now().isoformat()
        },
        "guides": {
            "melee_physical": {
                "name": "Physical Melee Leveling",
                "skills": ["Cleave", "Sunder", "Lacerate"],
                "act_progression": {
                    "Act 1": "Use Cleave + Added Fire",
                    "Act 2-3": "Switch to Sunder",
                    "Act 4-6": "Add Ancestral Protector",
                    "Act 7-10": "Lacerate or build-specific skill"
                },
                "key_items": ["Prismatic Eclipse", "Geoffri's Baptism", "Tabula Rasa"]
            },
            "spell_fire": {
                "name": "Fire Spell Leveling",
                "skills": ["Freezing Pulse", "Fireball", "Flameblast"],
                "act_progression": {
                    "Act 1": "Freezing Pulse",
                    "Act 2-4": "Switch to Fireball + Herald of Ash",
                    "Act 5-10": "Build-specific spell"
                },
                "key_items": ["Wanderlust", "Goldrim", "Tabula Rasa"]
            },
            "minion": {
                "name": "Minion Leveling",
                "skills": ["Summon Raging Spirit", "Summon Skeletons"],
                "act_progression": {
                    "Act 1": "SRS from quest",
                    "Act 2-10": "SRS + Minion Damage + Melee Splash"
                },
                "key_items": ["Tabula Rasa", "Bones of Ullr", "Sidhebreath"]
            },
            "bow": {
                "name": "Bow/Projectile Leveling",
                "skills": ["Toxic Rain", "Caustic Arrow", "Split Arrow"],
                "act_progression": {
                    "Act 1": "Split Arrow + Pierce",
                    "Act 2-10": "Toxic Rain + Mirage Archer"
                },
                "key_items": ["Silverbranch", "Hyrri's Bite", "Tabula Rasa"]
            }
        }
    }

    leveling_file = os.path.join(
        os.path.dirname(__file__),
        "build_data",
        "leveling_guides.json"
    )

    with open(leveling_file, 'w', encoding='utf-8') as f:
        json.dump(leveling_guide, f, ensure_ascii=False, indent=2)

    print(f"[OK] Leveling guide template created: {leveling_file}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Popular Builds Pre-cacher')
    parser.add_argument('--collect', action='store_true', help='Collect popular builds')
    parser.add_argument('--max-per-category', type=int, default=3, help='Max builds per category')
    parser.add_argument('--leveling-guide', action='store_true', help='Create leveling guide template')

    args = parser.parse_args()

    if args.collect:
        collect_popular_builds(max_per_category=args.max_per_category)
    elif args.leveling_guide:
        create_leveling_guide_template()
    else:
        parser.print_help()