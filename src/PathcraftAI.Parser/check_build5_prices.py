#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build #5 (Penance Brand Chieftain) 아이템 실제 가격 확인
"""

import sys
import time
from poe_trade_api import POETradeAPI

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

def main():
    print("=" * 80)
    print("Build #5: Penance Brand Chieftain - 실제 시장 가격 확인")
    print("=" * 80)
    print()

    # 현재 리그 - 여러 가능성 시도
    possible_leagues = [
        "Settlers",
        "Settlers of Kalguur",
        "Keepers",
        "Standard",
        "Hardcore"
    ]

    api = None
    working_league = None

    # 작동하는 리그 찾기
    print("리그 확인 중...")
    for league in possible_leagues:
        print(f"  시도: {league}")
        test_api = POETradeAPI(league=league)
        try:
            # 간단한 검색으로 테스트
            test_results = test_api.search_item(item_name="Nebulis", limit=1)
            if test_results is not None:  # 에러가 없으면
                api = test_api
                working_league = league
                print(f"  ✓ 작동하는 리그: {league}\n")
                break
        except:
            pass

    if not api:
        print("작동하는 리그를 찾을 수 없습니다.")
        return

    # 확인할 아이템 리스트 (Build #5: Penance Brand Chieftain)
    items_to_check = [
        # 핵심 유니크
        {"name": "Nebulis", "type": None, "influence": None, "links": None, "foulborn": False},
        {"name": "Skin of the Lords", "type": None, "influence": None, "links": 6, "foulborn": True},
        {"name": "The Surrender", "type": None, "influence": None, "links": None, "foulborn": False},
        {"name": "The Red Dream", "type": "Crimson Jewel", "influence": None, "links": None, "foulborn": False},
        # 기타 유니크
        {"name": "Replica Reckless Defence", "type": None, "influence": None, "links": None, "foulborn": False},
    ]

    total_min = 0
    total_max = 0

    for item_info in items_to_check:
        item_name = item_info["name"]
        item_type = item_info.get("type")
        influence = item_info.get("influence")
        links = item_info.get("links")
        foulborn = item_info.get("foulborn", False)

        # 검색 설명 생성
        search_desc = item_name
        if foulborn:
            search_desc += " (Foulborn)"
        if links:
            search_desc += f" ({links}L)"
        if influence:
            search_desc += f" ({influence})"

        print(f"\n검색 중: {search_desc}")
        print("-" * 80)

        try:
            results = api.search_item(
                item_name=item_name,
                item_type=item_type,
                influence=influence,
                links=links,
                foulborn=foulborn,
                limit=10
            )

            if not results:
                print("  매물 없음")
                continue

            # 가격 수집
            prices_chaos = []
            prices_divine = []

            for i, item in enumerate(results[:5], 1):
                price_display = item['price_display']
                price_chaos = item['price_chaos']

                print(f"  {i}. {price_display} ({price_chaos:.1f} Chaos)")

                # Divine/Chaos 구분
                if 'divine' in price_display.lower():
                    amount = float(price_display.split()[0])
                    prices_divine.append(amount)
                else:
                    prices_chaos.append(price_chaos)

            # 평균 가격 계산
            if prices_divine:
                avg_divine = sum(prices_divine) / len(prices_divine)
                min_divine = min(prices_divine)
                max_divine = max(prices_divine)
                print(f"\n  평균: {avg_divine:.2f} Divine (최저: {min_divine:.2f}, 최고: {max_divine:.2f})")
                total_min += min_divine
                total_max += max_divine
            elif prices_chaos:
                avg_chaos = sum(prices_chaos) / len(prices_chaos)
                min_chaos = min(prices_chaos)
                max_chaos = max(prices_chaos)
                avg_divine = avg_chaos / 100
                min_divine = min_chaos / 100
                max_divine = max_chaos / 100
                print(f"\n  평균: {avg_chaos:.1f} Chaos (~{avg_divine:.2f} Divine)")
                print(f"  최저: {min_chaos:.1f}c ({min_divine:.2f}d), 최고: {max_chaos:.1f}c ({max_divine:.2f}d)")
                total_min += min_divine
                total_max += max_divine

            time.sleep(2)  # Rate limiting

        except Exception as e:
            print(f"  오류: {e}")
            continue

    print("\n" + "=" * 80)
    print("총 예상 가격:")
    print(f"  최저가: {total_min:.2f} Divine")
    print(f"  최고가: {total_max:.2f} Divine")
    print(f"  평균: {(total_min + total_max) / 2:.2f} Divine")
    print("=" * 80)

if __name__ == '__main__':
    main()
