# -*- coding: utf-8 -*-

"""
Build Search Manager
사용자 요청에 대해 다중 소스에서 빌드를 검색하고 관리
- 로컬 캐시 우선 검색 (즉시)
- 빠른 소스 검색 (5-10초)
- 백그라운드 추가 수집 (비동기)
"""

import json
import os
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import threading

# 기존 수집기들
from pob_link_collector import collect_builds_from_reddit
from ladder_cache_builder import search_cache
from poe_ninja_fetcher import load_item_data

CACHE_DIR = os.path.join(os.path.dirname(__file__), "build_data", "search_cache")
PRECACHED_BUILDS = os.path.join(os.path.dirname(__file__), "build_data", "precached_popular_builds.json")

class BuildSearchManager:
    """빌드 검색 및 캐시 관리"""

    def __init__(self):
        self.cache_dir = CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)

        # 인기 빌드 사전 로드
        self.popular_builds = self._load_popular_builds()

        # 아이템 데이터 로드
        self.item_data = load_item_data()

    def _load_popular_builds(self) -> Dict:
        """사전 수집된 인기 빌드 로드"""
        if os.path.exists(PRECACHED_BUILDS):
            with open(PRECACHED_BUILDS, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"builds": []}

    def search_builds(
        self,
        keyword: str,
        league: str = "Keepers",
        max_results: int = 10,
        background_collect: bool = True
    ) -> Dict:
        """
        빌드 검색 (다중 소스)

        Args:
            keyword: 검색 키워드 (예: "Death's Oath", "Lightning Arrow")
            league: 리그 이름
            max_results: 최대 결과 수
            background_collect: 백그라운드 추가 수집 여부

        Returns:
            {
                "status": "success",
                "source": "cache|reddit|ladder|mixed",
                "results": [...],
                "count": 3,
                "background_collecting": True|False,
                "message": "..."
            }
        """
        print(f"\n[SEARCH] Searching for: {keyword}")
        print("=" * 60)

        # Phase 1: 로컬 캐시 확인 (즉시)
        print("[Phase 1] Checking local cache...")
        cached_results = self._search_local_cache(keyword, league)

        if len(cached_results) >= 3:
            print(f"[OK] Found {len(cached_results)} builds in cache (instant)")

            result = {
                "status": "success",
                "source": "cache",
                "results": cached_results[:max_results],
                "count": len(cached_results[:max_results]),
                "background_collecting": False,
                "message": f"Found {len(cached_results)} builds from cache (instant)"
            }

            # 캐시가 오래되었으면 백그라운드 업데이트
            if self._is_cache_stale(keyword, league):
                if background_collect:
                    self._start_background_collection(keyword, league)
                    result["background_collecting"] = True
                    result["message"] += " - Updating in background..."

            return result

        # Phase 2: 빠른 소스 검색 (Reddit + 로컬 래더 캐시)
        print("[Phase 2] Searching fast sources (Reddit + Ladder cache)...")
        fast_results = []

        # 2-1. Reddit 검색 (빠름, 5-10초)
        print("  [2-1] Searching Reddit...")
        try:
            reddit_builds = collect_builds_from_reddit(max_builds=5, keyword=keyword)
            fast_results.extend(self._normalize_build_source(reddit_builds, "reddit"))
            print(f"  [OK] Found {len(reddit_builds)} from Reddit")
        except Exception as e:
            print(f"  [WARN] Reddit search failed: {e}")

        # 2-2. 로컬 래더 캐시 검색 (매우 빠름, < 1초)
        print("  [2-2] Searching ladder cache...")
        try:
            ladder_results = search_cache(league=league, item=keyword, limit=5)
            fast_results.extend(self._normalize_build_source(ladder_results, "ladder"))
            print(f"  [OK] Found {len(ladder_results)} from ladder cache")
        except Exception as e:
            print(f"  [WARN] Ladder cache search failed: {e}")

        # 결과 저장
        if fast_results:
            self._save_to_cache(keyword, league, fast_results)

        # Phase 3: 백그라운드 추가 수집 시작 (선택)
        if background_collect and len(fast_results) < 10:
            print("[Phase 3] Starting background collection...")
            self._start_background_collection(keyword, league)
            background_msg = f" - Collecting more builds in background (2-5 min)"
        else:
            background_msg = ""

        print("=" * 60)

        return {
            "status": "success" if fast_results else "partial",
            "source": "mixed",
            "results": fast_results[:max_results],
            "count": len(fast_results[:max_results]),
            "background_collecting": background_collect and len(fast_results) < 10,
            "message": f"Found {len(fast_results)} builds from Reddit + Ladder{background_msg}"
        }

    def _search_local_cache(self, keyword: str, league: str) -> List[Dict]:
        """로컬 캐시에서 검색"""
        cache_file = os.path.join(self.cache_dir, f"{keyword.replace(' ', '_')}_{league}.json")

        if not os.path.exists(cache_file):
            return []

        # 캐시 파일 읽기
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        return cache_data.get("builds", [])

    def _is_cache_stale(self, keyword: str, league: str, max_age_hours: int = 24) -> bool:
        """캐시가 오래되었는지 확인"""
        cache_file = os.path.join(self.cache_dir, f"{keyword.replace(' ', '_')}_{league}.json")

        if not os.path.exists(cache_file):
            return True

        # 파일 수정 시간 확인
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        age = datetime.now() - file_time

        return age > timedelta(hours=max_age_hours)

    def _save_to_cache(self, keyword: str, league: str, builds: List[Dict]):
        """검색 결과를 캐시에 저장"""
        cache_file = os.path.join(self.cache_dir, f"{keyword.replace(' ', '_')}_{league}.json")

        cache_data = {
            "metadata": {
                "keyword": keyword,
                "league": league,
                "cached_at": datetime.now().isoformat(),
                "build_count": len(builds)
            },
            "builds": builds
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        print(f"[CACHE] Saved {len(builds)} builds to cache")

    def _normalize_build_source(self, builds: List[Dict], source: str) -> List[Dict]:
        """빌드 데이터에 소스 정보 추가"""
        for build in builds:
            build['data_source'] = source
        return builds

    def _start_background_collection(self, keyword: str, league: str):
        """백그라운드에서 추가 빌드 수집"""
        def background_task():
            print(f"\n[BACKGROUND] Starting deep collection for {keyword}...")

            all_builds = []

            # 래더 깊이 스캔 (시간 소요)
            try:
                from ladder_item_filter import scan_ladder_for_item
                ladder_builds = scan_ladder_for_item(
                    league=league,
                    item_name=keyword,
                    max_characters=500,  # 500명 스캔
                    max_builds=20
                )
                all_builds.extend(self._normalize_build_source(ladder_builds, "ladder_deep"))
                print(f"[BACKGROUND] Found {len(ladder_builds)} from deep ladder scan")
            except Exception as e:
                print(f"[BACKGROUND] Ladder scan failed: {e}")

            # 공식 포럼 스캔 (TODO: 구현 필요)
            # try:
            #     forum_builds = search_poe_forum(keyword)
            #     all_builds.extend(self._normalize_build_source(forum_builds, "forum"))
            # except Exception as e:
            #     print(f"[BACKGROUND] Forum search failed: {e}")

            # 캐시 업데이트
            if all_builds:
                existing = self._search_local_cache(keyword, league)
                combined = existing + all_builds

                # 중복 제거 (POB 링크 기준)
                seen = set()
                unique_builds = []
                for build in combined:
                    pob_link = build.get('source', {}).get('pob_link') or build.get('pob_link')
                    if pob_link and pob_link not in seen:
                        seen.add(pob_link)
                        unique_builds.append(build)
                    elif not pob_link:
                        unique_builds.append(build)

                self._save_to_cache(keyword, league, unique_builds)
                print(f"[BACKGROUND] Collection complete! Total: {len(unique_builds)} builds")
            else:
                print(f"[BACKGROUND] No additional builds found")

        # 백그라운드 스레드 시작
        thread = threading.Thread(target=background_task, daemon=True)
        thread.start()
        print("[INFO] Background collection started (non-blocking)")

def quick_search_demo(keyword: str):
    """빠른 검색 데모"""
    manager = BuildSearchManager()

    result = manager.search_builds(
        keyword=keyword,
        league="Keepers",
        max_results=10,
        background_collect=True
    )

    print("\n" + "=" * 60)
    print("SEARCH RESULT:")
    print("=" * 60)
    print(f"Status: {result['status']}")
    print(f"Source: {result['source']}")
    print(f"Found: {result['count']} builds")
    print(f"Background collecting: {result['background_collecting']}")
    print(f"Message: {result['message']}")

    print("\nBuilds:")
    for i, build in enumerate(result['results'][:5], 1):
        name = build.get('meta', {}).get('build_name') or build.get('character_name', 'Unknown')
        source = build.get('data_source', 'unknown')
        print(f"  {i}. {name} (from {source})")

    if result['background_collecting']:
        print("\n[NOTE] Additional builds are being collected in background.")
        print("       Check cache in 2-5 minutes for updated results.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Build Search Manager')
    parser.add_argument('keyword', type=str, help='Search keyword (e.g., "Death\'s Oath")')
    parser.add_argument('--league', type=str, default='Keepers', help='League name')
    parser.add_argument('--no-background', action='store_true', help='Disable background collection')

    args = parser.parse_args()

    manager = BuildSearchManager()
    result = manager.search_builds(
        keyword=args.keyword,
        league=args.league,
        background_collect=not args.no_background
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
