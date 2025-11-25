#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POE.Ninja API Client with Caching
실제 시장 가격 데이터 확인 (캐싱 지원)
"""

import sys
import os
import requests
import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


class PriceCache:
    """파일 기반 가격 캐시 시스템"""

    def __init__(self, cache_dir: str = None, ttl_seconds: int = 3600):
        """
        Args:
            cache_dir: 캐시 디렉토리 경로 (None이면 기본 경로 사용)
            ttl_seconds: 캐시 유효 시간 (기본 1시간)
        """
        if cache_dir is None:
            # 기본 캐시 디렉토리
            script_dir = Path(__file__).parent
            cache_dir = script_dir / "build_data" / "ninja_cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()

    def _get_cache_path(self, key: str) -> Path:
        """캐시 파일 경로 반환"""
        # 안전한 파일명으로 변환
        safe_key = key.replace("/", "_").replace(":", "_").replace("?", "_")
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[Dict]:
        """캐시에서 데이터 가져오기

        Returns:
            캐시된 데이터 또는 None (만료되었거나 없는 경우)
        """
        cache_path = self._get_cache_path(key)

        with self._lock:
            if not cache_path.exists():
                return None

            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                # TTL 확인
                cached_time = cache_data.get('timestamp', 0)
                if time.time() - cached_time > self.ttl_seconds:
                    return None  # 만료됨

                return cache_data.get('data')

            except Exception as e:
                print(f"[WARN] Cache read error for {key}: {e}", file=sys.stderr)
                return None

    def set(self, key: str, data: Dict) -> None:
        """캐시에 데이터 저장"""
        cache_path = self._get_cache_path(key)

        cache_data = {
            'timestamp': time.time(),
            'data': data
        }

        with self._lock:
            try:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False)
            except Exception as e:
                print(f"[WARN] Cache write error for {key}: {e}", file=sys.stderr)

    def is_valid(self, key: str) -> bool:
        """캐시가 유효한지 확인"""
        return self.get(key) is not None

    def clear(self) -> None:
        """모든 캐시 삭제"""
        with self._lock:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except Exception:
                    pass

    def get_age(self, key: str) -> Optional[float]:
        """캐시 나이 (초) 반환"""
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            return time.time() - cache_data.get('timestamp', 0)
        except Exception:
            return None


class POENinjaAPI:
    """POE.Ninja API 클라이언트 (캐싱 지원)"""

    def __init__(self, league: str = "Settlers", use_cache: bool = True, cache_ttl: int = 3600):
        """
        Args:
            league: 리그 이름
            use_cache: 캐시 사용 여부 (기본 True)
            cache_ttl: 캐시 유효 시간 초 (기본 1시간)
        """
        self.league = league
        self.base_url = "https://poe.ninja/api/data"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PathcraftAI/1.0'
        })
        self._divine_chaos_rate = None
        self.use_cache = use_cache
        self._cache = PriceCache(ttl_seconds=cache_ttl) if use_cache else None
        self._all_prices_cache = None  # 메모리 캐시
        self._background_refresh_thread = None

    def _get_cache_key(self, data_type: str) -> str:
        """캐시 키 생성"""
        return f"{self.league}_{data_type}"

    def preload_cache(self, background: bool = True) -> None:
        """모든 가격 데이터를 미리 로드

        Args:
            background: True면 백그라운드에서 로드
        """
        if background:
            if self._background_refresh_thread and self._background_refresh_thread.is_alive():
                return  # 이미 실행 중

            self._background_refresh_thread = threading.Thread(
                target=self._load_all_prices,
                daemon=True
            )
            self._background_refresh_thread.start()
        else:
            self._load_all_prices()

    def _load_all_prices(self) -> None:
        """모든 가격 데이터 로드 (내부 메서드)"""
        try:
            print("[INFO] Loading poe.ninja price data...", file=sys.stderr)

            # Divine 환율 먼저
            self.get_divine_chaos_rate()

            # 모든 아이템 타입 로드
            types_to_load = [
                ("Currency", "currencyoverview"),
                ("UniqueWeapon", "itemoverview"),
                ("UniqueArmour", "itemoverview"),
                ("UniqueAccessory", "itemoverview"),
                ("UniqueJewel", "itemoverview"),
                ("UniqueFlask", "itemoverview"),
            ]

            for item_type, endpoint in types_to_load:
                cache_key = self._get_cache_key(item_type)

                # 캐시가 유효하면 스킵
                if self._cache and self._cache.is_valid(cache_key):
                    continue

                try:
                    url = f"{self.base_url}/{endpoint}"
                    params = {
                        "league": self.league,
                        "type": item_type,
                        "language": "en"
                    }

                    response = self.session.get(url, params=params, timeout=15)
                    response.raise_for_status()

                    data = response.json()
                    if self._cache:
                        self._cache.set(cache_key, data)

                    # 요청 간격 (rate limiting)
                    time.sleep(0.5)

                except Exception as e:
                    print(f"[WARN] Failed to load {item_type}: {e}", file=sys.stderr)

            print("[INFO] Price data loaded successfully", file=sys.stderr)

        except Exception as e:
            print(f"[ERROR] Failed to preload cache: {e}", file=sys.stderr)

    def get_all_unique_prices(self) -> Dict[str, float]:
        """모든 유니크 아이템 가격 가져오기 (캐시 사용)

        Returns:
            {아이템이름: chaos가격} 딕셔너리
        """
        # 메모리 캐시 확인
        if self._all_prices_cache is not None:
            return self._all_prices_cache

        all_prices = {}

        # 각 타입별로 캐시에서 가져오기
        for item_type in ["UniqueWeapon", "UniqueArmour", "UniqueAccessory", "UniqueJewel", "UniqueFlask"]:
            cache_key = self._get_cache_key(item_type)

            # 캐시에서 가져오기
            if self._cache:
                cached_data = self._cache.get(cache_key)
                if cached_data:
                    prices = self._parse_item_prices(cached_data)
                    all_prices.update(prices)
                    continue

            # 캐시 없으면 API 호출
            try:
                prices = self._get_prices_by_type(item_type)
                all_prices.update(prices)
            except Exception as e:
                print(f"[WARN] Failed to get {item_type} prices: {e}", file=sys.stderr)

        self._all_prices_cache = all_prices
        return all_prices

    def _parse_item_prices(self, data: Dict) -> Dict[str, float]:
        """API 응답에서 가격 파싱"""
        prices = {}
        lines = data.get('lines', [])

        for item in lines:
            name = item.get('name', '')
            base_type = item.get('baseType', '')
            chaos_value = item.get('chaosValue', 0)

            # 이름만 사용 (검색 편의) - 소문자
            if chaos_value > 0:
                prices[name.lower()] = chaos_value

            # 풀네임도 저장 (정확한 매칭) - 소문자
            if base_type:
                full_name = f"{name}, {base_type}"
                if chaos_value > 0:
                    prices[full_name.lower()] = chaos_value

        return prices

    def get_unique_with_base_types(self) -> Dict[str, Dict]:
        """유니크 아이템의 이름, 베이스타입, 가격 정보 반환 (필터 생성용)

        Returns:
            {원본이름: {'base_type': 베이스타입, 'price': 가격}} 딕셔너리
        """
        result = {}

        # 여러 유니크 카테고리
        item_types = [
            ('UniqueWeapon', 'weapon'),
            ('UniqueArmour', 'armour'),
            ('UniqueAccessory', 'accessory'),
            ('UniqueFlask', 'flask'),
            ('UniqueJewel', 'jewel'),
        ]

        for api_type, _ in item_types:
            try:
                url = f"{self.base_url}/itemoverview"
                params = {
                    'league': self.league,
                    'type': api_type
                }

                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()

                data = response.json()
                if data and 'lines' in data:
                    for item in data['lines']:
                        name = item.get('name', '')
                        base_type = item.get('baseType', '')
                        chaos_value = item.get('chaosValue', 0)

                        if name and chaos_value > 0:
                            result[name] = {
                                'base_type': base_type,
                                'price': chaos_value
                            }

            except Exception as e:
                print(f"[WARN] Failed to get {api_type}: {e}", file=sys.stderr)

        return result

    def get_item_price(self, item_name: str) -> Optional[float]:
        """특정 아이템 가격 조회 (캐시 사용)

        Args:
            item_name: 아이템 이름

        Returns:
            Chaos 단위 가격 또는 None
        """
        all_prices = self.get_all_unique_prices()
        item_name_lower = item_name.lower()

        # 정확한 매칭
        if item_name_lower in all_prices:
            return all_prices[item_name_lower]

        # 부분 매칭
        for name, price in all_prices.items():
            if item_name_lower in name or name in item_name_lower:
                return price

        return None

    def get_divine_chaos_rate(self) -> float:
        """Divine Orb의 Chaos 환율 가져오기 (캐시 사용)

        Returns:
            1 Divine = X Chaos (예: 150.0)
        """
        if self._divine_chaos_rate is not None:
            return self._divine_chaos_rate

        # 캐시에서 먼저 확인
        cache_key = self._get_cache_key("Currency")
        if self._cache:
            cached_data = self._cache.get(cache_key)
            if cached_data:
                lines = cached_data.get('lines', [])
                for item in lines:
                    if item.get('currencyTypeName') == 'Divine Orb':
                        self._divine_chaos_rate = item.get('chaosEquivalent', 150.0)
                        return self._divine_chaos_rate

        # 캐시 없으면 API 호출
        try:
            url = f"{self.base_url}/currencyoverview"
            params = {
                "league": self.league,
                "type": "Currency",
                "language": "en"
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 캐시에 저장
            if self._cache:
                self._cache.set(cache_key, data)

            lines = data.get('lines', [])

            for item in lines:
                if item.get('currencyTypeName') == 'Divine Orb':
                    self._divine_chaos_rate = item.get('chaosEquivalent', 150.0)
                    return self._divine_chaos_rate

            # Divine Orb를 못 찾으면 기본값
            self._divine_chaos_rate = 150.0
            return self._divine_chaos_rate

        except Exception as e:
            print(f"[ERROR] Failed to get Divine rate: {e}", file=sys.stderr)
            self._divine_chaos_rate = 150.0
            return self._divine_chaos_rate

    def chaos_to_divine(self, chaos: float) -> float:
        """Chaos를 Divine으로 변환"""
        rate = self.get_divine_chaos_rate()
        return chaos / rate if rate > 0 else 0

    def divine_to_chaos(self, divine: float) -> float:
        """Divine을 Chaos로 변환"""
        rate = self.get_divine_chaos_rate()
        return divine * rate

    def format_price(self, chaos_value: float, prefer_divine: bool = False) -> str:
        """가격을 적절한 형식으로 표시

        Args:
            chaos_value: Chaos 단위 가격
            prefer_divine: Divine 단위 선호 여부 (리그 후반기)

        Returns:
            포맷된 가격 문자열 (예: "50c", "3d 45c", "0.3 div")
        """
        rate = self.get_divine_chaos_rate()
        divine_value = chaos_value / rate if rate > 0 else 0

        # Divine 선호 또는 1 Divine 이상인 경우
        if prefer_divine or divine_value >= 1:
            divine_int = int(divine_value)
            remaining_chaos = int(chaos_value - (divine_int * rate))

            if remaining_chaos > 0:
                # 3d 45c 형식
                return f"{divine_int}d {remaining_chaos}c"
            else:
                # 정확히 나누어 떨어지면 3d
                return f"{divine_int}d"
        elif divine_value >= 0.1:
            return f"{divine_value:.1f} div"
        else:
            # Chaos 표시
            if chaos_value >= 1000:
                return f"{chaos_value/1000:.1f}k c"
            else:
                return f"{int(chaos_value)}c"

    def format_budget_label(self, chaos_value: int, force_chaos: bool = False) -> str:
        """예산 필터용 라벨 포맷

        Args:
            chaos_value: Chaos 단위 가격
            force_chaos: True면 Chaos 단위로만 표시

        Returns:
            포맷된 예산 라벨 (예: "~50c", "~3d", "~3d 45c")
        """
        if force_chaos:
            return f"~{chaos_value}c"

        rate = self.get_divine_chaos_rate()
        divine_value = chaos_value / rate if rate > 0 else 0

        if divine_value >= 1:
            divine_int = int(round(divine_value))  # 반올림
            remaining_chaos = int(chaos_value - (divine_int * rate))

            # 나머지가 작으면 무시 (반올림 오차)
            if abs(remaining_chaos) < 5:
                return f"~{divine_int}d"
            elif remaining_chaos > 0:
                return f"~{divine_int}d {remaining_chaos}c"
            else:
                return f"~{divine_int}d"
        elif divine_value >= 0.05:  # 0.1d도 표시하기 위해 0.05로 낮춤
            return f"~{divine_value:.1f}d"
        else:
            return f"~{chaos_value}c"

    def get_budget_tiers(self, league_phase: str = "mid") -> List[Dict]:
        """리그 페이즈에 따른 예산 구간 반환

        Args:
            league_phase: "early", "mid", "late"

        Returns:
            예산 구간 리스트:
            {
                "label": "~1d",              # UI 표시용 (예: ~3d 45c)
                "chaos_value": 131,          # 실제 필터링 값
                "tooltip": "0.1d = 13c..."   # 호버 시 표시
            }
        """
        rate = self.get_divine_chaos_rate()

        # Divine 환산표 (호버 시 표시)
        div_conversion = (
            f"0.1d = {int(rate * 0.1)}c\n"
            f"0.3d = {int(rate * 0.3)}c\n"
            f"0.5d = {int(rate * 0.5)}c\n"
            f"1d = {int(rate)}c\n"
            f"3d = {int(rate * 3)}c\n"
            f"5d = {int(rate * 5)}c\n"
            f"10d = {int(rate * 10)}c"
        )

        # 예산 구간 정의 (chaos 값)
        if league_phase == "early":
            chaos_values = [None, 10, 30, 50, 100, int(rate * 0.3), int(rate * 0.5), int(rate)]
        elif league_phase == "late":
            chaos_values = [None, int(rate * 0.1), int(rate * 0.3), int(rate * 0.5),
                          int(rate), int(rate * 3), int(rate * 5), int(rate * 10)]
        else:  # mid
            chaos_values = [None, 50, 100, int(rate * 0.5), int(rate),
                          int(rate * 3), int(rate * 5)]

        # Divine 배수 값들 (이것들은 Divine으로 표시)
        divine_multiples = {
            int(rate * 0.1), int(rate * 0.3), int(rate * 0.5),
            int(rate), int(rate * 3), int(rate * 5), int(rate * 10)
        }

        tiers = []
        for cv in chaos_values:
            if cv is None:
                tiers.append({"label": "전체", "chaos_value": None, "tooltip": ""})
            else:
                # Divine 배수면 Divine으로, 아니면 Chaos로 표시
                is_divine_multiple = cv in divine_multiples
                force_chaos = not is_divine_multiple
                label = self.format_budget_label(cv, force_chaos=force_chaos)
                # Divine 단위면 환산표 툴팁 추가
                tooltip = div_conversion if is_divine_multiple else ""
                tiers.append({"label": label, "chaos_value": cv, "tooltip": tooltip})

        return tiers

    def get_unique_item_prices(self) -> Dict[str, float]:
        """유니크 아이템 가격 가져오기"""
        try:
            url = f"{self.base_url}/itemoverview"
            params = {
                "league": self.league,
                "type": "UniqueJewel",
                "language": "en"
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            lines = data.get('lines', [])

            prices = {}
            for item in lines:
                name = item.get('name', '')
                chaos_value = item.get('chaosValue', 0)
                divine_value = item.get('divineValue', 0)

                if divine_value > 0:
                    prices[name] = divine_value
                elif chaos_value > 0:
                    prices[name] = chaos_value / 100  # Chaos를 Divine으로 변환

            return prices

        except Exception as e:
            print(f"[ERROR] Failed to get prices: {e}", file=sys.stderr)
            return {}

    def get_unique_weapon_prices(self) -> Dict[str, float]:
        """유니크 무기 가격"""
        return self._get_prices_by_type("UniqueWeapon")

    def get_unique_armour_prices(self) -> Dict[str, float]:
        """유니크 방어구 가격"""
        return self._get_prices_by_type("UniqueArmour")

    def get_unique_accessory_prices(self) -> Dict[str, float]:
        """유니크 액세서리 가격"""
        return self._get_prices_by_type("UniqueAccessory")

    def _get_prices_by_type(self, item_type: str) -> Dict[str, float]:
        """타입별 가격 조회 (캐시 사용)"""
        # 캐시 확인
        cache_key = self._get_cache_key(item_type)
        if self._cache:
            cached_data = self._cache.get(cache_key)
            if cached_data:
                return self._parse_item_prices_divine(cached_data)

        # 캐시 없으면 API 호출
        try:
            url = f"{self.base_url}/itemoverview"
            params = {
                "league": self.league,
                "type": item_type,
                "language": "en"
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 캐시에 저장
            if self._cache:
                self._cache.set(cache_key, data)

            return self._parse_item_prices_divine(data)

        except Exception as e:
            print(f"[ERROR] Failed to get {item_type} prices: {e}", file=sys.stderr)
            return {}

    def _parse_item_prices_divine(self, data: Dict) -> Dict[str, float]:
        """API 응답에서 Divine 단위 가격 파싱"""
        lines = data.get('lines', [])
        prices = {}

        for item in lines:
            name = item.get('name', '')
            base_type = item.get('baseType', '')
            chaos_value = item.get('chaosValue', 0)
            divine_value = item.get('divineValue', 0)

            # 이름 + 베이스 타입 조합
            full_name = f"{name}, {base_type}" if base_type else name

            if divine_value > 0:
                prices[full_name] = divine_value
            elif chaos_value > 0:
                prices[full_name] = chaos_value / 100

        return prices

    def search_item(self, item_name: str) -> Optional[Dict]:
        """아이템 검색"""
        # 모든 카테고리에서 검색
        all_prices = {}
        all_prices.update(self.get_unique_weapon_prices())
        all_prices.update(self.get_unique_armour_prices())
        all_prices.update(self.get_unique_accessory_prices())
        all_prices.update(self.get_unique_item_prices())

        # 아이템 이름으로 검색
        item_name_lower = item_name.lower()
        matches = []

        for name, price in all_prices.items():
            if item_name_lower in name.lower():
                matches.append({
                    'name': name,
                    'divine_price': price,
                    'chaos_price': price * 100
                })

        # 가격순 정렬
        matches.sort(key=lambda x: x['divine_price'])

        return matches


def test_poe_ninja():
    """POE.Ninja API 테스트"""
    print("=" * 80)
    print("POE.Ninja API 가격 확인 (캐싱 테스트)")
    print("=" * 80)
    print()

    # 캐시 사용 API 생성
    api = POENinjaAPI(league="Keepers", use_cache=True, cache_ttl=3600)

    # Divine 환율 확인
    print("Divine 환율 가져오기...")
    start = time.time()
    divine_rate = api.get_divine_chaos_rate()
    elapsed = time.time() - start
    print(f"Divine Rate: {divine_rate}c (소요: {elapsed:.2f}s)")
    print()

    # 첫 번째 조회 (캐시 생성 또는 API 호출)
    print("첫 번째 가격 조회...")
    start = time.time()
    all_prices = api.get_all_unique_prices()
    elapsed = time.time() - start
    print(f"총 아이템 수: {len(all_prices)} (소요: {elapsed:.2f}s)")
    print()

    # 두 번째 조회 (캐시에서 로드)
    print("두 번째 가격 조회 (캐시에서)...")
    api2 = POENinjaAPI(league="Keepers", use_cache=True)
    start = time.time()
    all_prices2 = api2.get_all_unique_prices()
    elapsed = time.time() - start
    print(f"총 아이템 수: {len(all_prices2)} (소요: {elapsed:.2f}s)")
    print()

    # 특정 아이템 가격 조회
    items_to_check = [
        "Nebulis",
        "Skin of the Lords",
        "The Surrender",
        "Aegis Aurora",
        "Mageblood",
    ]

    print("아이템별 가격:")
    print("-" * 80)
    for item_name in items_to_check:
        price = api.get_item_price(item_name)
        if price:
            if price >= divine_rate:
                div_price = price / divine_rate
                print(f"  {item_name}: {price:.0f}c ({div_price:.1f}d)")
            else:
                print(f"  {item_name}: {price:.0f}c")
        else:
            print(f"  {item_name}: 가격 없음")


def test_cache_preload():
    """캐시 프리로드 테스트"""
    print("=" * 80)
    print("캐시 프리로드 테스트")
    print("=" * 80)
    print()

    api = POENinjaAPI(league="Keepers", use_cache=True)

    print("백그라운드 프리로드 시작...")
    api.preload_cache(background=True)

    # 프리로드 완료 대기
    print("프리로드 완료 대기 중...")
    time.sleep(10)

    # 캐시에서 빠르게 조회
    print("\n캐시에서 조회:")
    start = time.time()
    all_prices = api.get_all_unique_prices()
    elapsed = time.time() - start
    print(f"총 아이템 수: {len(all_prices)} (소요: {elapsed:.3f}s)")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--preload', action='store_true', help='Test cache preload')
    args = parser.parse_args()

    if args.preload:
        test_cache_preload()
    else:
        test_poe_ninja()
