#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국어 스탯 검색 테스트
"""

import sys

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

from poe_trade_api import POETradeAPI


def test_korean_stat_search():
    """한국어 스탯 검색 테스트"""
    print("=" * 80)
    print("한국어 스탯 검색 테스트")
    print("=" * 80)
    print()

    api = POETradeAPI(league="Keepers")

    # 1. 한국어 스탯 텍스트로 검색
    print("1. 한국어 스탯 텍스트 검색")
    print("-" * 80)

    url = api.search_korean_stats_url(
        item_type="Ring",
        korean_stats=[
            {"text": "총 생명력", "min": 60},
            {"text": "총 원소 저항", "min": 80}
        ],
        max_price=50
    )
    if url:
        print(f"  반지 (생명력 60+, 원소저항 80+): {url}")
    else:
        print("  URL 생성 실패")
    print()

    # 2. 단축키 검색
    print("2. 단축키 검색")
    print("-" * 80)

    url = api.search_with_shortcuts_url(
        item_type="Boots",
        shortcuts={
            "life": {"min": 60},
            "move_speed": {"min": 25},
            "ele_res": {"min": 60}
        },
        max_price=100
    )
    if url:
        print(f"  부츠 (생명력, 이속, 저항): {url}")
    else:
        print("  URL 생성 실패")
    print()

    # 3. 헬멧 검색
    print("3. 헬멧 검색 (에실, 생명력, 저항)")
    print("-" * 80)

    url = api.search_with_shortcuts_url(
        item_type="Helmet",
        shortcuts={
            "es": {"min": 100},
            "life": {"min": 50},
            "ele_res": {"min": 60}
        },
        max_price=150
    )
    if url:
        print(f"  ES 헬멧: {url}")
    else:
        print("  URL 생성 실패")
    print()

    # 4. 무기 검색
    print("4. 무기 검색 (물리 피해, 공격 속도)")
    print("-" * 80)

    url = api.search_with_shortcuts_url(
        item_type="One Hand Sword",
        shortcuts={
            "phys_dmg": {"min": 100},
            "attack_speed": {"min": 10},
            "crit_chance": {"min": 20}
        },
        max_price=200
    )
    if url:
        print(f"  한손검: {url}")
    else:
        print("  URL 생성 실패")
    print()

    # 5. 주문 피해 증가 아뮬렛
    print("5. 캐스터 아뮬렛")
    print("-" * 80)

    url = api.search_with_shortcuts_url(
        item_type="Amulet",
        shortcuts={
            "spell_dmg": {"min": 20},
            "cast_speed": {"min": 10},
            "mana": {"min": 50},
            "crit_multi": {"min": 20}
        },
        max_price=300
    )
    if url:
        print(f"  캐스터 아뮬렛: {url}")
    else:
        print("  URL 생성 실패")
    print()

    print("=" * 80)
    print("테스트 완료")
    print("=" * 80)


if __name__ == "__main__":
    test_korean_stat_search()
