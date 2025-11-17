#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""POE.Ninja 시장 가격 확인"""

import sys
import json
import os

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

def check_market_prices():
    """시장 가격 확인"""
    data_dir = 'game_data'

    print('=' * 80)
    print('POE.NINJA 실시간 시장 가격 (Keepers League)')
    print('=' * 80)
    print()

    # 유니크 무기
    weapons_file = os.path.join(data_dir, 'unique_weapons.json')
    if os.path.exists(weapons_file):
        with open(weapons_file, 'r', encoding='utf-8') as f:
            weapons_data = json.load(f)

        weapons = weapons_data.get('items', [])
        print(f'📊 총 {len(weapons)}개 유니크 무기 가격 수집됨')
        print()

        # 가격 순 정렬
        sorted_weapons = sorted(
            [w for w in weapons if w.get('chaosValue', 0) > 0],
            key=lambda x: x.get('chaosValue', 0),
            reverse=True
        )

        print('💰 가격 TOP 10 (비싼 순):')
        print('-' * 80)
        for i, item in enumerate(sorted_weapons[:10], 1):
            name = item.get('name', 'Unknown')
            base = item.get('baseType', '')
            chaos = item.get('chaosValue', 0)
            divine = item.get('divineValue', 0)

            print(f'{i}. {name}')
            print(f'   타입: {base}')
            print(f'   가격: {chaos:,.1f}c = {divine:.2f}div')
            print()

    # 유니크 방어구
    armours_file = os.path.join(data_dir, 'unique_armours.json')
    if os.path.exists(armours_file):
        with open(armours_file, 'r', encoding='utf-8') as f:
            armours_data = json.load(f)

        armours = armours_data.get('items', [])
        print(f'🛡️  총 {len(armours)}개 유니크 방어구 가격 수집됨')
        print()

        # 가격 순 정렬
        sorted_armours = sorted(
            [a for a in armours if a.get('chaosValue', 0) > 0],
            key=lambda x: x.get('chaosValue', 0),
            reverse=True
        )

        print('💰 방어구 TOP 5 (비싼 순):')
        print('-' * 80)
        for i, item in enumerate(sorted_armours[:5], 1):
            name = item.get('name', 'Unknown')
            base = item.get('baseType', '')
            chaos = item.get('chaosValue', 0)
            divine = item.get('divineValue', 0)

            print(f'{i}. {name}')
            print(f'   타입: {base}')
            print(f'   가격: {chaos:,.1f}c = {divine:.2f}div')
            print()

    # 저렴한 아이템도 확인
    print('=' * 80)
    print('🔍 1-10 Chaos 가격대 인기 아이템 (초보자 추천)')
    print('-' * 80)

    budget_items = [
        w for w in weapons
        if 1 <= w.get('chaosValue', 0) <= 10
    ]

    budget_items.sort(key=lambda x: x.get('chaosValue', 0))

    for i, item in enumerate(budget_items[:10], 1):
        name = item.get('name', 'Unknown')
        base = item.get('baseType', '')
        chaos = item.get('chaosValue', 0)

        print(f'{i}. {name} ({base}): {chaos:.1f}c')

if __name__ == '__main__':
    check_market_prices()
