"""
Bilingual Map Checker (Korean + English)
Supports both Korean and English POE clients

Usage:
    # English client
    python bilingual_map_checker.py --pob-url https://pobb.in/xxx --map "English map text" --lang en

    # Korean client
    python bilingual_map_checker.py --pob-url https://pobb.in/xxx --map "한글 맵 텍스트" --lang kr
"""

import argparse
from pob_accuracy import extract_main_skill
from pob_parser import get_pob_code_from_url, decode_pob_code
from map_mod_analyzer import MapModAnalyzer, DangerLevel
from poe_translations import POETranslations


def bilingual_check_map(pob_url: str, map_clipboard: str, language: str = "en"):
    """
    Check map safety with bilingual support

    Args:
        pob_url: POB URL
        map_clipboard: Map item text (Korean or English)
        language: "kr" or "en"
    """
    is_korean = (language == "kr")

    if is_korean:
        print("="*60)
        print("스마트 맵 체커 (한국어)")
        print("="*60)
    else:
        print("="*60)
        print("Smart Map Checker (English)")
        print("="*60)

    # Step 1: Get POB data
    if is_korean:
        print("\n[1/4] POB 데이터 가져오는 중...")
    else:
        print("\n[1/4] Fetching POB data...")

    encoded_code = get_pob_code_from_url(pob_url)
    if not encoded_code:
        print("   ❌ Failed to fetch POB" if not is_korean else "   ❌ POB 가져오기 실패")
        return

    xml_string = decode_pob_code(encoded_code)
    if not xml_string:
        print("   ❌ Failed to decode POB" if not is_korean else "   ❌ POB 디코딩 실패")
        return

    print("   ✅ POB fetched successfully" if not is_korean else "   ✅ POB 가져오기 성공")

    # Step 2: Detect main skill
    if is_korean:
        print("\n[2/4] 메인 스킬 감지 중...")
    else:
        print("\n[2/4] Detecting main skill...")

    skill_data = extract_main_skill(xml_string)
    if skill_data['error']:
        print(f"   ❌ Error: {skill_data['error']}")
        return

    main_skill = skill_data['main_skill_name']

    # Translate to Korean if needed
    main_skill_display = main_skill
    if is_korean:
        korean_skill = POETranslations.translate_skill(main_skill, to_korean=True)
        if korean_skill:
            main_skill_display = f"{korean_skill} ({main_skill})"

    print(f"   ✅ " + ("메인 스킬: " if is_korean else "Main skill: ") + main_skill_display)

    # Step 3: Detect build type
    if is_korean:
        print("\n[3/4] 빌드 타입 감지 중...")
    else:
        print("\n[3/4] Detecting build type...")

    analyzer = MapModAnalyzer()
    build_type = analyzer.detect_build_from_skill(main_skill)

    # Translate build type if Korean
    build_type_display = build_type
    if is_korean:
        build_type_display = POETranslations.translate_build_type(build_type)

    print(f"   ✅ " + ("빌드 타입: " if is_korean else "Build type: ") + build_type_display)

    # Step 4: Analyze map
    if is_korean:
        print("\n[4/4] 맵 모드 분석 중...")
    else:
        print("\n[4/4] Analyzing map mods...")

    map_info = analyzer.parse_map_item(map_clipboard)
    if not map_info:
        print("   ❌ Not a valid map item" if not is_korean else "   ❌ 유효한 맵 아이템이 아닙니다")
        return

    print(f"   " + ("맵: " if is_korean else "Map: ") + map_info['name'])
    print(f"   " + ("모드 수: " if is_korean else "Mods: ") + str(len(map_info['mods'])))

    # Detect mods (support both languages)
    if is_korean:
        # Detect Korean mods
        detected_mod_types = set()
        for mod_text in map_info['mods']:
            kr_mods = POETranslations.detect_korean_map_mods(mod_text)
            detected_mod_types.update(kr_mods)

        # Convert to English mod format for analysis
        detected_mods = {mod_type: [mod_type] for mod_type in detected_mod_types}
    else:
        detected_mods = analyzer.detect_mod_types(map_info['mods'])

    # Analyze danger
    analysis = analyzer.analyze_danger(map_info['mods'], build_type)

    # Print results
    print("\n" + "="*60)
    print("결과" if is_korean else "RESULT")
    print("="*60)

    if is_korean:
        print(f"빌드: {main_skill_display} ({build_type_display})")
        print(f"맵: {map_info['name']}")
        print(f"\n위험도: {POETranslations.translate_danger_level(analysis['overall_level'].value).upper()}")
    else:
        print(f"Build: {main_skill} ({build_type})")
        print(f"Map: {map_info['name']}")
        print(f"\nDanger Level: {analysis['overall_level'].value.upper()}")

    # Print warnings
    if analysis['overall_level'] == DangerLevel.SAFE:
        print("\n✅ " + ("안전: 위험한 모드가 감지되지 않았습니다" if is_korean else "SAFE: No dangerous mods detected"))
    else:
        print()
        for warning in analysis['all_warnings']:
            if is_korean:
                # Get Korean description
                mod_desc = POETranslations.get_mod_description_kr(warning['mod_type'])
                level_emoji = {
                    'deadly': '🔴',
                    'dangerous': '🟠',
                    'warning': '🟡'
                }.get(warning['level'].value, '⚪')

                level_text = POETranslations.translate_danger_level(warning['level'].value).upper()
                print(f"{level_emoji} {level_text}: {mod_desc['name']}")
                if mod_desc['warning']:
                    print(f"   ⚠️  {mod_desc['warning']}")
            else:
                print(warning['message'])

    print("="*60)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Bilingual Map Checker (Korean + English)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # English client
  python bilingual_map_checker.py \\
      --pob-url https://pobb.in/wXVStDuZrqHX \\
      --map "Rarity: Rare..." \\
      --lang en

  # Korean client
  python bilingual_map_checker.py \\
      --pob-url https://pobb.in/wXVStDuZrqHX \\
      --map "희귀도: 희귀..." \\
      --lang kr
        """
    )

    parser.add_argument('--pob-url', type=str, required=True,
                       help='POB URL (e.g., https://pobb.in/xxx)')

    parser.add_argument('--map', type=str, required=True,
                       help='Map item text from clipboard')

    parser.add_argument('--lang', type=str, default='en', choices=['en', 'kr'],
                       help='Language: en (English) or kr (Korean)')

    args = parser.parse_args()

    bilingual_check_map(args.pob_url, args.map, args.lang)


if __name__ == '__main__':
    main()
