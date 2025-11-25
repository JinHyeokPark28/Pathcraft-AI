# -*- coding: utf-8 -*-
"""
POE Trade API Korean Data Fetcher
POE 공식 Trade API에서 한국어 데이터 수집

공식 API는 lang=ko 파라미터로 한국어 데이터를 제공합니다.
- /api/trade/data/stats - 스탯 번역
- /api/trade/data/items - 아이템 베이스 타입
- /api/trade/data/static - 화폐, 아이콘 등
"""

import os
import json
import time
import requests
from typing import Dict, List, Any, Optional


class POETradeKoreanFetcher:
    """POE Trade API에서 한국어 데이터를 가져오는 클래스"""

    def __init__(self, rate_limit_delay: float = 1.0):
        """
        Args:
            rate_limit_delay: API 호출 간 대기 시간 (초)
        """
        self.base_url = "https://www.pathofexile.com/api/trade/data"
        self.headers = {
            'User-Agent': 'PathcraftAI/1.0 (https://github.com/pathcraft-ai)',
            'Accept': 'application/json'
        }
        self.rate_limit_delay = rate_limit_delay

    def _make_request(self, endpoint: str, lang: str = 'ko') -> Optional[Dict]:
        """
        API 요청 수행

        Args:
            endpoint: API 엔드포인트 (예: 'stats', 'items')
            lang: 언어 코드 (기본값: 'ko')

        Returns:
            JSON 응답 데이터 또는 None
        """
        url = f"{self.base_url}/{endpoint}"
        params = {'lang': lang}

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] API 요청 실패 ({endpoint}): {e}")
            return None

    def get_korean_stats(self) -> Dict:
        """
        한국어 스탯 데이터 가져오기

        Returns:
            {
                "stats": {"영어": "한국어", ...},
                "stats_kr": {"한국어": "영어", ...},
                "stats_by_type": {"explicit": [...], "implicit": [...], ...}
            }
        """
        print("[INFO] 한국어 스탯 데이터 수집 중...")
        data = self._make_request('stats')

        if not data:
            return {}

        result = {
            "stats": {},
            "stats_kr": {},
            "stats_by_type": {}
        }

        for category in data.get('result', []):
            stat_type = category.get('label', 'unknown')
            entries = category.get('entries', [])

            if stat_type not in result['stats_by_type']:
                result['stats_by_type'][stat_type] = []

            for entry in entries:
                stat_id = entry.get('id', '')
                text = entry.get('text', '')

                if stat_id and text:
                    result['stats'][stat_id] = text
                    result['stats_kr'][text] = stat_id
                    result['stats_by_type'][stat_type].append({
                        'id': stat_id,
                        'text': text,
                        'type': entry.get('type', '')
                    })

        print(f"[OK] 스탯: {len(result['stats'])}개")
        return result

    def get_korean_items(self) -> Dict:
        """
        한국어 아이템 베이스 타입 데이터 가져오기

        Returns:
            {
                "items": {"영어": "한국어", ...},
                "items_kr": {"한국어": "영어", ...},
                "items_by_type": {"weapon": [...], "armour": [...], ...}
            }
        """
        print("[INFO] 한국어 아이템 데이터 수집 중...")
        data = self._make_request('items')

        if not data:
            return {}

        result = {
            "items": {},
            "items_kr": {},
            "items_by_type": {}
        }

        for category in data.get('result', []):
            item_type = category.get('label', 'unknown')
            entries = category.get('entries', [])

            if item_type not in result['items_by_type']:
                result['items_by_type'][item_type] = []

            for entry in entries:
                name = entry.get('name', '')
                text = entry.get('text', name)  # text가 없으면 name 사용
                item_type_detail = entry.get('type', '')

                if name:
                    # name이 영어, text가 한국어인 경우
                    result['items'][name] = text
                    result['items_kr'][text] = name

                    result['items_by_type'][item_type].append({
                        'name': name,
                        'text': text,
                        'type': item_type_detail,
                        'flags': entry.get('flags', {})
                    })

        print(f"[OK] 아이템: {len(result['items'])}개")
        return result

    def get_korean_static(self) -> Dict:
        """
        한국어 정적 데이터 (화폐, 카드 등) 가져오기

        Returns:
            {
                "currency": {...},
                "cards": {...},
                ...
            }
        """
        print("[INFO] 한국어 정적 데이터 수집 중...")
        data = self._make_request('static')

        if not data:
            return {}

        result = {
            "static": {},
            "static_kr": {},
            "static_by_type": {}
        }

        for category in data.get('result', []):
            static_type = category.get('id', 'unknown')
            label = category.get('label', static_type)
            entries = category.get('entries', [])

            if static_type not in result['static_by_type']:
                result['static_by_type'][static_type] = {
                    'label': label,
                    'items': []
                }

            for entry in entries:
                entry_id = entry.get('id', '')
                text = entry.get('text', '')
                image = entry.get('image', '')

                if entry_id and text:
                    result['static'][entry_id] = text
                    result['static_kr'][text] = entry_id

                    result['static_by_type'][static_type]['items'].append({
                        'id': entry_id,
                        'text': text,
                        'image': image
                    })

        print(f"[OK] 정적 데이터: {len(result['static'])}개")
        return result

    def get_leagues(self) -> List[Dict]:
        """현재 리그 목록 가져오기"""
        print("[INFO] 리그 목록 수집 중...")

        try:
            response = requests.get(
                "https://www.pathofexile.com/api/trade/data/leagues",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            leagues = data.get('result', [])
            print(f"[OK] 리그: {len(leagues)}개")
            return leagues
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] 리그 목록 가져오기 실패: {e}")
            return []

    def collect_all_korean_data(self, output_dir: str = './data') -> Dict:
        """
        모든 한국어 데이터 수집 및 저장

        Args:
            output_dir: 출력 디렉토리

        Returns:
            통합된 데이터
        """
        all_data = {
            "source": "poe-trade-api",
            "language": "ko",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # 스탯 데이터
        stats_data = self.get_korean_stats()
        all_data.update(stats_data)
        time.sleep(self.rate_limit_delay)

        # 아이템 데이터
        items_data = self.get_korean_items()
        all_data['items'] = items_data.get('items', {})
        all_data['items_kr'] = items_data.get('items_kr', {})
        all_data['items_by_type'] = items_data.get('items_by_type', {})
        time.sleep(self.rate_limit_delay)

        # 정적 데이터
        static_data = self.get_korean_static()
        all_data['static'] = static_data.get('static', {})
        all_data['static_kr'] = static_data.get('static_kr', {})
        all_data['static_by_type'] = static_data.get('static_by_type', {})
        time.sleep(self.rate_limit_delay)

        # 리그 목록
        leagues = self.get_leagues()
        all_data['leagues'] = leagues

        # 저장
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "poe_trade_korean.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        print(f"\n[완료] 저장됨: {output_file}")
        return all_data


def merge_translations(
    awakened_path: str,
    trade_api_path: str,
    poecharm_path: str = None,
    output_path: str = None
) -> Dict:
    """
    여러 소스의 번역 데이터를 병합

    우선순위: Trade API > Awakened > PoeCharm

    Args:
        awakened_path: Awakened POE Trade 번역 파일
        trade_api_path: POE Trade API 번역 파일
        poecharm_path: PoeCharm 번역 파일 (선택)
        output_path: 출력 파일 경로 (선택)

    Returns:
        병합된 번역 데이터
    """
    merged = {
        "source": "merged",
        "sources": [],
        "items": {},
        "items_kr": {},
        "stats": {},
        "stats_kr": {},
        "skills": {},
        "skills_kr": {},
    }

    # PoeCharm (가장 낮은 우선순위)
    if poecharm_path and os.path.exists(poecharm_path):
        with open(poecharm_path, 'r', encoding='utf-8') as f:
            poecharm = json.load(f)
        merged['sources'].append('poecharm')

        for key in ['items', 'items_kr', 'skills', 'skills_kr']:
            if key in poecharm:
                merged[key].update(poecharm[key])

    # Awakened POE Trade
    if os.path.exists(awakened_path):
        with open(awakened_path, 'r', encoding='utf-8') as f:
            awakened = json.load(f)
        merged['sources'].append('awakened-poe-trade')

        for key in ['items', 'items_kr', 'stats', 'stats_kr']:
            if key in awakened:
                merged[key].update(awakened[key])

    # Trade API (가장 높은 우선순위)
    if os.path.exists(trade_api_path):
        with open(trade_api_path, 'r', encoding='utf-8') as f:
            trade_api = json.load(f)
        merged['sources'].append('poe-trade-api')

        for key in ['items', 'items_kr', 'stats', 'stats_kr']:
            if key in trade_api:
                merged[key].update(trade_api[key])

    # 저장
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"[완료] 병합된 번역 저장됨: {output_path}")

    return merged


def main():
    import argparse

    parser = argparse.ArgumentParser(description='POE Trade API 한국어 데이터 수집')
    parser.add_argument('--output', type=str, default='./data',
                        help='출력 디렉토리')
    parser.add_argument('--merge', action='store_true',
                        help='기존 데이터와 병합')

    args = parser.parse_args()

    # 데이터 수집
    fetcher = POETradeKoreanFetcher()
    all_data = fetcher.collect_all_korean_data(args.output)

    # 병합 (옵션)
    if args.merge:
        awakened_path = os.path.join(args.output, "awakened_translations.json")
        trade_api_path = os.path.join(args.output, "poe_trade_korean.json")
        poecharm_path = os.path.join(args.output, "poe_translations.json")
        merged_path = os.path.join(args.output, "merged_translations.json")

        merge_translations(
            awakened_path,
            trade_api_path,
            poecharm_path,
            merged_path
        )

    # 통계 출력
    print("\n" + "=" * 50)
    print("[완료] POE Trade API 한국어 데이터 수집")
    print(f"  스탯: {len(all_data.get('stats', {}))}개")
    print(f"  아이템: {len(all_data.get('items', {}))}개")
    print(f"  정적 데이터: {len(all_data.get('static', {}))}개")
    print(f"  리그: {len(all_data.get('leagues', []))}개")
    print("=" * 50)


if __name__ == "__main__":
    main()
