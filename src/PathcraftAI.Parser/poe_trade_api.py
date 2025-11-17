#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POE Trade API Integration
실제 거래소에서 구매 가능한 아이템 검색
"""

import sys
import time
import json
import requests
from typing import List, Dict, Optional

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


class POETradeAPI:
    """POE Trade API 클라이언트"""

    def __init__(self, league: str = "Keepers"):
        self.league = league
        self.base_url = "https://www.pathofexile.com/api/trade"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PathcraftAI/1.0 (contact: pathcraft@example.com)',
            'Content-Type': 'application/json'
        })
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  # 1초 대기 (Rate limit 방지)

    def _wait_for_rate_limit(self):
        """Rate limit 준수"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)

        self.last_request_time = time.time()

    def search_item(
        self,
        item_name: str,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        item_type: Optional[str] = None,
        stats: Optional[List[Dict]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        아이템 검색

        Args:
            item_name: 아이템 이름
            min_price: 최소 가격 (chaos orbs)
            max_price: 최대 가격 (chaos orbs)
            item_type: 아이템 타입 (예: "Body Armour")
            stats: 요구 스탯 리스트
            limit: 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        try:
            # 검색 쿼리 생성
            query = self._build_query(
                item_name=item_name,
                min_price=min_price,
                max_price=max_price,
                item_type=item_type,
                stats=stats
            )

            # Rate limit 준수
            self._wait_for_rate_limit()

            # 검색 요청
            search_url = f"{self.base_url}/search/{self.league}"
            response = self.session.post(search_url, json=query)
            response.raise_for_status()

            search_data = response.json()
            result_ids = search_data.get('result', [])[:limit]

            if not result_ids:
                return []

            # 아이템 상세 정보 가져오기
            items = self._fetch_items(result_ids)

            return items

        except Exception as e:
            print(f"[ERROR] Trade search failed: {e}", file=sys.stderr)
            return []

    def _build_query(
        self,
        item_name: str,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        item_type: Optional[str] = None,
        stats: Optional[List[Dict]] = None
    ) -> Dict:
        """검색 쿼리 생성"""
        query = {
            "query": {
                "status": {"option": "online"},  # 온라인 판매자만
                "filters": {}
            },
            "sort": {"price": "asc"}  # 가격 오름차순
        }

        # 아이템 이름 필터
        if item_name:
            query["query"]["name"] = item_name

        # 아이템 타입 필터
        if item_type:
            query["query"]["type"] = item_type

        # 가격 필터
        price_filter = {}
        if min_price is not None:
            price_filter["min"] = min_price
        if max_price is not None:
            price_filter["max"] = max_price

        if price_filter:
            query["query"]["filters"]["trade_filters"] = {
                "filters": {
                    "price": {
                        **price_filter,
                        "option": "chaos"
                    }
                }
            }

        # 스탯 필터
        if stats and len(stats) > 0:
            query["query"]["stats"] = [{
                "type": "and",
                "filters": stats
            }]

        return query

    def _fetch_items(self, item_ids: List[str]) -> List[Dict]:
        """아이템 상세 정보 가져오기"""
        try:
            # Rate limit 준수
            self._wait_for_rate_limit()

            # ID를 10개씩 묶어서 요청 (API 제한)
            item_ids_str = ','.join(item_ids[:10])
            fetch_url = f"{self.base_url}/fetch/{item_ids_str}"

            params = {"query": self.league}
            response = self.session.get(fetch_url, params=params)
            response.raise_for_status()

            fetch_data = response.json()
            results = fetch_data.get('result', [])

            items = []
            for result in results:
                item = self._parse_item(result)
                if item:
                    items.append(item)

            return items

        except Exception as e:
            print(f"[ERROR] Fetch items failed: {e}", file=sys.stderr)
            return []

    def _parse_item(self, result: Dict) -> Optional[Dict]:
        """아이템 데이터 파싱"""
        try:
            item_data = result.get('item', {})
            listing = result.get('listing', {})

            # 가격 정보
            price_data = listing.get('price', {})
            price_amount = price_data.get('amount', 0)
            price_currency = price_data.get('currency', 'chaos')

            # Chaos로 환산
            chaos_price = price_amount
            if price_currency == 'divine':
                chaos_price = price_amount * 110  # 대략적인 환율 (실시간 조회 필요)

            # 판매자 정보
            account = listing.get('account', {})
            seller_name = account.get('name', 'Unknown')
            character_name = account.get('lastCharacterName', '')

            # Whisper 메시지
            whisper = listing.get('whisper', '')

            return {
                'id': result.get('id', ''),
                'name': item_data.get('name', ''),
                'type': item_data.get('typeLine', ''),
                'price_chaos': chaos_price,
                'price_display': f"{price_amount} {price_currency}",
                'seller': seller_name,
                'character': character_name,
                'whisper': whisper,
                'item_level': item_data.get('ilvl', 0),
                'corrupted': item_data.get('corrupted', False),
                'identified': item_data.get('identified', True)
            }

        except Exception as e:
            print(f"[ERROR] Parse item failed: {e}", file=sys.stderr)
            return None

    def search_resistance_ring(
        self,
        min_total_res: int = 60,
        max_price: int = 20
    ) -> List[Dict]:
        """저항 반지 검색 (업그레이드용)"""
        stats = [
            {
                "id": "pseudo.pseudo_total_elemental_resistance",
                "value": {"min": min_total_res}
            }
        ]

        return self.search_item(
            item_name="",
            item_type="Ring",
            max_price=max_price,
            stats=stats,
            limit=5
        )

    def search_6link_body(
        self,
        max_price: int = 60
    ) -> List[Dict]:
        """6링크 방어구 검색"""
        stats = [
            {
                "id": "explicit.stat_1050105434",  # Sockets
                "value": {"min": 6}
            }
        ]

        return self.search_item(
            item_name="",
            item_type="Body Armour",
            max_price=max_price,
            stats=stats,
            limit=5
        )


def test_trade_search():
    """Trade API 테스트"""
    print("=" * 80)
    print("POE TRADE API TEST")
    print("=" * 80)
    print()

    api = POETradeAPI(league="Keepers")

    # 1. 저항 반지 검색
    print("1. Searching for resistance rings (max 20c)...")
    print("-" * 80)

    rings = api.search_resistance_ring(min_total_res=60, max_price=20)

    for i, item in enumerate(rings, 1):
        print(f"{i}. {item['type']}")
        print(f"   가격: {item['price_display']} (~{item['price_chaos']:.1f}c)")
        print(f"   판매자: {item['seller']} ({item['character']})")
        print(f"   Whisper: {item['whisper'][:80]}...")
        print()

    # 2. 6링크 검색
    print()
    print("2. Searching for 6-link body armours (max 60c)...")
    print("-" * 80)

    bodies = api.search_6link_body(max_price=60)

    for i, item in enumerate(bodies, 1):
        print(f"{i}. {item['type']}")
        print(f"   가격: {item['price_display']} (~{item['price_chaos']:.1f}c)")
        print(f"   판매자: {item['seller']} ({item['character']})")
        print()


if __name__ == '__main__':
    test_trade_search()
