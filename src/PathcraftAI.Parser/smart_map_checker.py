"""
Smart Map Checker
Combines POB accuracy + Map Mod analyzer for automatic build detection

Usage:
    python smart_map_checker.py --pob-url https://pobb.in/xxx --map-clipboard "map text"
"""

import argparse
from pob_accuracy import extract_main_skill
from pob_parser import get_pob_code_from_url, decode_pob_code
from map_mod_analyzer import MapModAnalyzer


def smart_check_map(pob_url: str, map_clipboard: str):
    """
    Automatically detect build from POB and check map safety

    Args:
        pob_url: POB URL (e.g., https://pobb.in/xxx)
        map_clipboard: Map item text from clipboard
    """
    print("="*60)
    print("Smart Map Checker")
    print("="*60)

    # Step 1: Get POB data
    print("\n[1/4] Fetching POB data...")
    encoded_code = get_pob_code_from_url(pob_url)
    if not encoded_code:
        print("   ❌ Failed to fetch POB")
        return

    xml_string = decode_pob_code(encoded_code)
    if not xml_string:
        print("   ❌ Failed to decode POB")
        return

    print("   ✅ POB fetched successfully")

    # Step 2: Detect main skill
    print("\n[2/4] Detecting main skill...")
    skill_data = extract_main_skill(xml_string)
    if skill_data['error']:
        print(f"   ❌ Error: {skill_data['error']}")
        return

    main_skill = skill_data['main_skill_name']
    print(f"   ✅ Main skill: {main_skill}")

    # Step 3: Detect build type
    print("\n[3/4] Detecting build type...")
    analyzer = MapModAnalyzer()
    build_type = analyzer.detect_build_from_skill(main_skill)
    print(f"   ✅ Build type: {build_type}")

    # Step 4: Analyze map
    print("\n[4/4] Analyzing map mods...")
    map_info = analyzer.parse_map_item(map_clipboard)
    if not map_info:
        print("   ❌ Not a valid map item")
        return

    print(f"   Map: {map_info['name']}")
    print(f"   Mods: {len(map_info['mods'])}")

    analysis = analyzer.analyze_danger(map_info['mods'], build_type)

    print("\n" + "="*60)
    print("RESULT")
    print("="*60)
    print(f"Build: {main_skill} ({build_type})")
    print(f"Map: {map_info['name']}")
    print(f"\nDanger Level: {analysis['overall_level'].value.upper()}")
    print("\n" + analyzer.format_warning(analysis))
    print("="*60)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Smart Map Checker - Auto-detect build and check map safety',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python smart_map_checker.py \\
      --pob-url https://pobb.in/wXVStDuZrqHX \\
      --map-clipboard "$(pbpaste)"
        """
    )

    parser.add_argument('--pob-url', type=str, required=True,
                       help='POB URL (e.g., https://pobb.in/xxx)')

    parser.add_argument('--map-clipboard', type=str, required=True,
                       help='Map item text from clipboard')

    args = parser.parse_args()

    smart_check_map(args.pob_url, args.map_clipboard)


if __name__ == '__main__':
    main()
