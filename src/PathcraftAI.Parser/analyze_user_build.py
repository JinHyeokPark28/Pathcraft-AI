# -*- coding: utf-8 -*-
"""
User Build Analyzer
사용자의 현재 빌드를 분석하여 아이템, 스킬, 빌드 타입을 파악
"""

import json
import os
import sys
from typing import Dict, List, Optional
from collections import Counter

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


def analyze_user_build(access_token: str, character_name: str) -> Dict:
    """
    사용자의 빌드 분석

    Args:
        access_token: OAuth 액세스 토큰
        character_name: 분석할 캐릭터 이름

    Returns:
        {
            "character_name": "Shovel_Spectre",
            "class": "Necromancer",
            "level": 93,
            "league": "Keepers",
            "build_type": "Death's Oath Occultist",
            "main_skill": "Vaal Righteous Fire",
            "support_skills": ["Increased Area of Effect", ...],
            "unique_items": [
                {
                    "name": "Death's Oath",
                    "slot": "BodyArmour",
                    "chaos_value": 564.0
                },
                ...
            ],
            "total_unique_value": 2500.0,
            "upgrade_suggestions": [...]
        }
    """

    from poe_oauth import get_character_items

    print("=" * 80)
    print("USER BUILD ANALYZER")
    print("=" * 80)
    print(f"Character: {character_name}")
    print()

    # 1. 캐릭터 아이템 가져오기
    print("[1/4] Fetching character items...")
    try:
        character_data = get_character_items(access_token, character_name)
    except Exception as e:
        print(f"[ERROR] Failed to fetch character items: {e}")
        return {}

    character_info = character_data.get('character', {})
    # POE API returns items in 'character.equipment' field
    items = character_info.get('equipment', [])

    print(f"[OK] {character_info.get('name')} Lv{character_info.get('level')} {character_info.get('class')}")
    print(f"[OK] Found {len(items)} items")
    print()

    # 2. 유니크 아이템 추출
    print("[2/4] Analyzing unique items...")
    unique_items = extract_unique_items(items)
    print(f"[OK] Found {len(unique_items)} unique items")

    for item in unique_items[:5]:
        print(f"  - {item['name']} ({item['slot']})")
    print()

    # 3. 메인 스킬 파악
    print("[3/4] Identifying main skill...")
    main_skill, support_gems = identify_main_skill(items)

    if main_skill:
        print(f"[OK] Main Skill: {main_skill}")
        print(f"[OK] Support Gems: {', '.join(support_gems[:3])}")
    else:
        print("[WARN] No main skill identified")
    print()

    # 4. 빌드 타입 추론
    print("[4/4] Determining build type...")
    build_type = determine_build_type(unique_items, main_skill, character_info.get('class'))
    print(f"[OK] Build Type: {build_type}")
    print()

    # 5. 아이템 가치 계산 (POE.Ninja 데이터 기반)
    total_value = calculate_item_value(unique_items)

    # 6. 업그레이드 제안
    upgrade_suggestions = suggest_upgrades(unique_items, build_type)

    print("=" * 80)
    print("BUILD ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Build Type: {build_type}")
    print(f"Main Skill: {main_skill or 'Unknown'}")
    print(f"Unique Items: {len(unique_items)}")
    print(f"Total Value: ~{total_value:.1f} chaos")
    print("=" * 80)
    print()

    return {
        "character_name": character_info.get('name'),
        "class": character_info.get('class'),
        "level": character_info.get('level'),
        "league": character_info.get('league'),
        "build_type": build_type,
        "main_skill": main_skill,
        "support_skills": support_gems,
        "unique_items": unique_items,
        "total_unique_value": total_value,
        "upgrade_suggestions": upgrade_suggestions
    }


def extract_unique_items(items: List[Dict]) -> List[Dict]:
    """아이템 목록에서 유니크 아이템만 추출"""

    unique_items = []

    for item in items:
        # frameType: 3 = unique, rarity: 'Unique'
        if item.get('frameType') == 3 or item.get('rarity') == 'Unique':
            # For unique items, 'name' field contains the unique name, 'typeLine' contains base type
            unique_name = item.get('name', '')
            base_type = item.get('typeLine', '')
            # Use unique name if available, otherwise fall back to base type
            display_name = unique_name if unique_name else base_type
            slot = item.get('inventoryId', 'Unknown')

            unique_items.append({
                "name": display_name,
                "base_type": base_type,
                "slot": slot,
                "sockets": item.get('sockets', []),
                "socketed_items": item.get('socketedItems', [])
            })

    return unique_items


def identify_main_skill(items: List[Dict]) -> tuple[Optional[str], List[str]]:
    """
    메인 스킬 젬 파악

    Returns:
        (main_skill_name, [support_gem_names])
    """

    # 6링크 아이템 찾기
    six_link_items = []

    for item in items:
        sockets = item.get('sockets', [])

        # 6링크 확인
        if len(sockets) >= 6:
            # 모든 소켓이 같은 그룹인지 확인
            group_ids = [s.get('group') for s in sockets]
            if len(set(group_ids)) == 1:  # 모두 같은 그룹
                six_link_items.append(item)

    # 6링크가 없으면 가장 많은 링크 찾기
    if not six_link_items:
        max_links = 0
        for item in items:
            sockets = item.get('sockets', [])
            if sockets:
                groups = {}
                for socket in sockets:
                    group = socket.get('group', 0)
                    groups[group] = groups.get(group, 0) + 1

                max_group_size = max(groups.values()) if groups else 0
                if max_group_size > max_links:
                    max_links = max_group_size
                    six_link_items = [item]

    # 소켓된 젬 분석
    main_skill = None
    support_gems = []

    for item in six_link_items:
        socketed_items = item.get('socketedItems', [])

        for gem in socketed_items:
            gem_name = gem.get('typeLine', '')
            is_support = gem.get('support', False)

            if not is_support and not main_skill:
                # 메인 스킬 (non-support)
                main_skill = gem_name
            elif is_support:
                support_gems.append(gem_name)

    return main_skill, support_gems


def determine_build_type(unique_items: List[Dict], main_skill: Optional[str], char_class: str) -> str:
    """
    빌드 타입 추론

    우선순위:
    1. 빌드 정의 유니크 아이템 (Death's Oath, Mjölner 등)
    2. 메인 스킬
    3. 클래스
    """

    # 빌드 정의 아이템
    build_defining_items = {
        "Death's Oath": "Death's Oath",
        "Mjölner": "Mjölner",
        "Mageblood": "Mageblood",
        "Covenant": "The Covenant",
        "Squire": "The Squire",
        "Headhunter": "Headhunter",
        "Dawnbreaker": "Dawnbreaker"
    }

    # 유니크 아이템 확인
    for item in unique_items:
        item_name = item['name']
        for keyword, build_name in build_defining_items.items():
            if keyword.lower() in item_name.lower():
                return f"{build_name} {char_class}"

    # 메인 스킬 기반
    if main_skill:
        # 스킬 이름 정리
        skill_name = main_skill.replace("Vaal ", "").replace(" Support", "")
        return f"{skill_name} {char_class}"

    # 기본: 클래스 이름만
    return f"{char_class} Build"


def calculate_item_value(unique_items: List[Dict]) -> float:
    """
    유니크 아이템의 총 가치 계산 (POE.Ninja 데이터 기반)
    """

    # POE.Ninja 데이터 로드
    game_data_dir = os.path.join(os.path.dirname(__file__), "game_data")

    # 유니크 무기
    weapons_file = os.path.join(game_data_dir, "unique_weapons.json")
    armours_file = os.path.join(game_data_dir, "unique_armours.json")
    accessories_file = os.path.join(game_data_dir, "unique_accessories.json")

    price_map = {}

    # 가격 정보 로드
    for filepath in [weapons_file, armours_file, accessories_file]:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get('items', []):
                    name = item.get('name', '')
                    chaos_value = item.get('chaosValue', 0)
                    price_map[name.lower()] = chaos_value

    # 유저 아이템 가격 합산
    total_value = 0.0

    for item in unique_items:
        item_name = item['name'].lower()
        if item_name in price_map:
            total_value += price_map[item_name]

    return total_value


def suggest_upgrades(unique_items: List[Dict], build_type: str) -> List[Dict]:
    """
    빌드 업그레이드 제안

    Returns:
        [
            {
                "item_name": "Mageblood",
                "reason": "Best in slot for most builds",
                "chaos_value": 23350
            },
            ...
        ]
    """

    suggestions = []

    # 현재 소지 아이템 이름 목록
    current_items = [item['name'].lower() for item in unique_items]

    # 빌드별 핵심 아이템
    build_recommendations = {
        "Death's Oath": ["Presence of Chayula", "Atziri's Step"],
        "Mjölner": ["Mageblood", "Impossible Escape"],
        "RF": ["Melding of the Flesh", "Aegis Aurora"],
        "Default": ["Mageblood", "Headhunter"]
    }

    # 빌드 타입에서 키워드 추출
    build_key = "Default"
    for key in build_recommendations.keys():
        if key in build_type:
            build_key = key
            break

    recommended_items = build_recommendations[build_key]

    # POE.Ninja에서 가격 정보 로드
    game_data_dir = os.path.join(os.path.dirname(__file__), "game_data")

    price_map = {}
    for filename in ["unique_weapons.json", "unique_armours.json", "unique_accessories.json"]:
        filepath = os.path.join(game_data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get('items', []):
                    name = item.get('name', '')
                    chaos_value = item.get('chaosValue', 0)
                    price_map[name] = chaos_value

    # 추천 아이템 중 아직 안 가진 것
    for item_name in recommended_items:
        if item_name.lower() not in current_items:
            suggestions.append({
                "item_name": item_name,
                "reason": f"Recommended upgrade for {build_type}",
                "chaos_value": price_map.get(item_name, 0)
            })

    return suggestions[:3]  # 상위 3개만


def analyze_user_build_from_token() -> Optional[Dict]:
    """
    저장된 OAuth 토큰에서 사용자 빌드 분석
    """

    from poe_oauth import load_token, get_user_characters

    # 토큰 로드
    token = load_token()
    if not token:
        print("[ERROR] No OAuth token found. Please authenticate first.")
        return None

    access_token = token.get('access_token')

    # 캐릭터 목록 가져오기
    try:
        characters_data = get_user_characters(access_token)
        characters = characters_data.get('characters', [])
    except Exception as e:
        print(f"[ERROR] Failed to get characters: {e}")
        return None

    if not characters:
        print("[ERROR] No characters found")
        return None

    # 메인 캐릭터 (가장 높은 레벨)
    main_char = max(characters, key=lambda c: c.get('level', 0))
    character_name = main_char.get('name')

    print(f"[INFO] Analyzing main character: {character_name} Lv{main_char.get('level')} {main_char.get('class')}")
    print()

    # 빌드 분석
    return analyze_user_build(access_token, character_name)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Analyze user build from POE character')
    parser.add_argument('--character', type=str, help='Character name (optional, uses highest level if not specified)')
    parser.add_argument('--json-output', action='store_true', help='Output JSON format')

    args = parser.parse_args()

    # OAuth 토큰에서 자동 분석
    build_analysis = analyze_user_build_from_token()

    if build_analysis:
        if args.json_output:
            print(json.dumps(build_analysis, ensure_ascii=False, indent=2))
        else:
            print()
            print("=" * 80)
            print("YOUR CURRENT BUILD")
            print("=" * 80)
            print(f"Character: {build_analysis['character_name']} Lv{build_analysis['level']}")
            print(f"Class: {build_analysis['class']}")
            print(f"League: {build_analysis['league']}")
            print(f"Build Type: {build_analysis['build_type']}")
            print(f"Main Skill: {build_analysis['main_skill'] or 'Unknown'}")
            print()
            print(f"Unique Items ({len(build_analysis['unique_items'])}):")
            for item in build_analysis['unique_items'][:10]:
                print(f"  - {item['name']} ({item['slot']})")
            print()
            print(f"Total Estimated Value: ~{build_analysis['total_unique_value']:.0f} chaos")
            print()

            if build_analysis['upgrade_suggestions']:
                print("Recommended Upgrades:")
                for suggestion in build_analysis['upgrade_suggestions']:
                    print(f"  - {suggestion['item_name']} (~{suggestion['chaos_value']:.0f}c): {suggestion['reason']}")

            print("=" * 80)
