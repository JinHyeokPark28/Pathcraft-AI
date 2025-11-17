#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빌드 비교 대시보드
현재 캐릭터 vs POB 목표 빌드 비교

사용법:
    python compare_build.py --pob https://pobb.in/xxx --character YourCharName
"""

import json
import sys
import argparse
from typing import Dict, Optional
from smart_build_analyzer import SmartBuildAnalyzer
from poe_oauth import get_character_items

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


def get_current_character_stats(access_token: str, character_name: str) -> Dict:
    """
    현재 캐릭터의 통계 가져오기

    Returns:
        {
            'life': 2800,
            'es': 0,
            'fire_res': 45,
            'cold_res': 75,
            'lightning_res': 60,
            'chaos_res': -60
        }
    """
    print(f"[1/3] Fetching current character: {character_name}...")

    try:
        character_data = get_character_items(access_token, character_name)
        character_info = character_data.get('character', {})

        # POE API는 통계를 직접 제공하지 않으므로,
        # 아이템에서 추정하거나 기본값 사용
        # TODO: 실제 구현에서는 아이템 파싱 필요

        print(f"  ✓ Character loaded: Lv{character_info.get('level')} {character_info.get('class')}")

        # 임시: 기본값 반환 (나중에 실제 파싱 구현)
        return {
            'life': 0,  # 아이템 파싱 필요
            'es': 0,
            'dps': 0,
            'fire_res': 0,
            'cold_res': 0,
            'lightning_res': 0,
            'chaos_res': 0,
        }

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {}


def get_pob_target_stats(pob_url: str) -> Dict:
    """
    POB 목표 빌드의 통계 가져오기
    """
    print(f"[2/3] Fetching POB target build...")

    analyzer = SmartBuildAnalyzer(pob_url, character_name=None)
    analyzer.fetch_pob()
    analyzer.extract_pob_stats()

    print(f"  ✓ POB stats extracted")

    return analyzer.pob_stats


def calculate_gap(current: float, target: float) -> tuple:
    """
    현재와 목표의 차이 계산

    Returns:
        (gap_value, status_icon)
    """
    gap = current - target

    if gap >= 0:
        return (gap, "✓")
    else:
        return (gap, "⚠️")


def compare_builds(current_stats: Dict, target_stats: Dict):
    """
    현재 vs 목표 비교 대시보드 출력
    """
    print("\n[3/3] Generating comparison dashboard...")
    print()

    print("=" * 80)
    print("CURRENT vs TARGET COMPARISON")
    print("=" * 80)
    print()

    # 헤더
    print(f"{'Stat':<20} {'Current':>15} {'Target':>15} {'Gap':>15} {'Status':>8}")
    print("-" * 80)

    # DPS
    current_dps = current_stats.get('dps', 0)
    target_dps = target_stats.get('dps', 0)
    gap_dps, status = calculate_gap(current_dps, target_dps)

    print(f"{'DPS':<20} {current_dps:>15,.0f} {target_dps:>15,.0f} {gap_dps:>15,.0f} {status:>8}")

    # Life
    current_life = current_stats.get('life', 0)
    target_life = target_stats.get('life', 0)
    gap_life, status = calculate_gap(current_life, target_life)

    print(f"{'Life':<20} {current_life:>15,} {target_life:>15,} {gap_life:>15,} {status:>8}")

    # Energy Shield
    current_es = current_stats.get('energy_shield', 0)
    target_es = target_stats.get('energy_shield', 0)
    gap_es, status = calculate_gap(current_es, target_es)

    print(f"{'Energy Shield':<20} {current_es:>15,} {target_es:>15,} {gap_es:>15,} {status:>8}")

    print()

    # Resistances
    print("RESISTANCES:")
    print("-" * 80)

    resistances = [
        ('Fire Res', 'fire_res'),
        ('Cold Res', 'cold_res'),
        ('Lightning Res', 'lightning_res'),
        ('Chaos Res', 'chaos_res'),
    ]

    for res_name, res_key in resistances:
        current_res = current_stats.get(res_key, 0)
        target_res = target_stats.get(res_key, 0)
        gap_res, status = calculate_gap(current_res, target_res)

        # 저항은 % 표시
        print(f"{res_name:<20} {current_res:>14}% {target_res:>14}% {gap_res:>14}% {status:>8}")

    print()
    print("=" * 80)

    # Priority Upgrades 계산
    print("\n🎯 PRIORITY UPGRADES:")
    print("-" * 80)

    priorities = []

    # DPS 부족
    if gap_dps < 0 and abs(gap_dps) > 10000:
        priorities.append(f"1. Increase DPS ({abs(gap_dps):,.0f} needed)")
        priorities.append(f"   → Get 6-link setup or better weapon")

    # Life 부족
    if gap_life < 0 and abs(gap_life) > 500:
        priorities.append(f"2. Increase Life ({abs(gap_life):,} HP needed)")
        priorities.append(f"   → Add Life nodes on passive tree or better gear")

    # 저항 부족
    uncapped_res = []
    for res_name, res_key in resistances[:3]:  # Fire, Cold, Lightning만
        current_res = current_stats.get(res_key, 0)
        target_res = target_stats.get(res_key, 75)  # 기본 목표 75%

        if current_res < target_res:
            uncapped_res.append((res_name, target_res - current_res))

    if uncapped_res:
        priorities.append(f"3. Cap Resistances:")
        for res_name, gap in uncapped_res:
            priorities.append(f"   → {res_name}: +{gap}% needed")

    if priorities:
        for priority in priorities:
            print(priority)
    else:
        print("✓ Build is at target level!")

    print()


def main():
    parser = argparse.ArgumentParser(description='현재 캐릭터 vs POB 목표 비교')
    parser.add_argument('--pob', required=True, help='POB 링크 (예: https://pobb.in/xxx)')
    parser.add_argument('--character', default='TestChar', help='캐릭터 이름')
    parser.add_argument('--token-file', default='poe_token.json', help='OAuth 토큰 파일')
    parser.add_argument('--mock', action='store_true', help='Mock 데이터 사용 (테스트용)')

    args = parser.parse_args()

    print("=" * 80)
    print("BUILD COMPARISON DASHBOARD")
    print("=" * 80)
    print()

    # Mock 모드
    if args.mock:
        print("🧪 Using MOCK data for testing...\n")

        # Mock 현재 캐릭터 통계 (낮은 수치)
        current_stats = {
            'dps': 150000,
            'life': 1,  # CI 빌드
            'energy_shield': 4500,
            'fire_res': 45,
            'cold_res': 75,
            'lightning_res': 60,
            'chaos_res': -60,
        }

    else:
        # OAuth 토큰 로드
        try:
            with open(args.token_file, 'r') as f:
                token_data = json.load(f)
                access_token = token_data['access_token']
        except FileNotFoundError:
            print(f"❌ Token file not found: {args.token_file}")
            print("Run: python test_oauth.py")
            print("\nTip: Use --mock flag for testing without token")
            return
        except KeyError:
            print(f"❌ Invalid token file format")
            return

        # 1. 현재 캐릭터 통계
        current_stats = get_current_character_stats(access_token, args.character)

    # 2. POB 목표 통계
    target_stats = get_pob_target_stats(args.pob)

    # 3. 비교 대시보드
    if current_stats and target_stats:
        compare_builds(current_stats, target_stats)
    else:
        print("❌ Failed to fetch stats")


if __name__ == '__main__':
    # 테스트용 기본값
    if len(sys.argv) == 1:
        print("Usage: python compare_build.py --pob <pob_url> --character <char_name>")
        print()
        print("Example:")
        print("  python compare_build.py --pob https://pobb.in/L_PjVQbio_WZ --character Shovel_FuckingWand")
        sys.exit(1)

    main()
