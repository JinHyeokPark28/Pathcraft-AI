# -*- coding: utf-8 -*-
"""
POE Translation Auto-Update Pipeline
POE 패치 감지 및 번역 데이터 자동 갱신

기능:
- POE 패치 버전 확인
- 번역 데이터 자동 수집 및 병합
- 캐시 관리 (24시간 유효)
"""

import os
import sys
import json
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

# 같은 디렉토리의 모듈 임포트
from awakened_translation_extractor import extract_all_awakened_translations
from poe_trade_korean_fetcher import POETradeKoreanFetcher, merge_translations


class TranslationUpdatePipeline:
    """번역 데이터 자동 업데이트 파이프라인"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "data")

        self.data_dir = data_dir
        self.cache_file = os.path.join(data_dir, "update_cache.json")
        self.version_file = os.path.join(data_dir, "poe_version.json")

        # 출력 파일들
        self.awakened_file = os.path.join(data_dir, "awakened_translations.json")
        self.trade_api_file = os.path.join(data_dir, "poe_trade_korean.json")
        self.poecharm_file = os.path.join(data_dir, "poe_translations.json")
        self.merged_file = os.path.join(data_dir, "merged_translations.json")

        os.makedirs(data_dir, exist_ok=True)

    def get_current_league(self) -> Optional[str]:
        """현재 리그 이름 가져오기"""
        try:
            response = requests.get(
                "https://www.pathofexile.com/api/trade/data/leagues",
                headers={'User-Agent': 'PathcraftAI/1.0'},
                timeout=10
            )
            response.raise_for_status()
            leagues = response.json().get('result', [])

            # 현재 시즌 리그 찾기 (Standard, Hardcore 제외)
            for league in leagues:
                league_id = league.get('id', '')
                if league_id and league_id not in ['Standard', 'Hardcore']:
                    if 'SSF' not in league_id and 'Ruthless' not in league_id:
                        return league_id

            return leagues[0]['id'] if leagues else None
        except Exception as e:
            print(f"[WARN] Failed to get current league: {e}", file=sys.stderr)
            return None

    def get_poe_patch_version(self) -> Optional[str]:
        """POE 패치 버전 확인 (현재 리그 기반)"""
        try:
            # 현재 리그를 버전 식별자로 사용
            league = self.get_current_league()
            if league:
                return league

            # 백업: 공식 API에서 리그 목록의 해시
            response = requests.get(
                "https://www.pathofexile.com/api/trade/data/leagues",
                headers={'User-Agent': 'PathcraftAI/1.0'},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # 리그 목록의 해시를 버전으로 사용
            leagues_str = json.dumps(data.get('result', []), sort_keys=True)
            return hashlib.md5(leagues_str.encode()).hexdigest()[:8]
        except Exception as e:
            print(f"[WARN] Failed to get POE version: {e}", file=sys.stderr)
            return None

    def load_cache(self) -> Dict:
        """캐시 파일 로드"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_cache(self, cache: Dict):
        """캐시 파일 저장"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

    def is_cache_valid(self, cache_hours: int = 24) -> bool:
        """캐시 유효성 확인"""
        cache = self.load_cache()
        last_update = cache.get('last_update')

        if not last_update:
            return False

        try:
            last_dt = datetime.fromisoformat(last_update)
            now = datetime.now()
            return (now - last_dt) < timedelta(hours=cache_hours)
        except:
            return False

    def needs_update(self, force: bool = False) -> Tuple[bool, str]:
        """업데이트 필요 여부 확인

        Returns:
            (needs_update, reason)
        """
        if force:
            return True, "Forced update"

        # 캐시 유효성 확인
        if not self.is_cache_valid():
            return True, "Cache expired (24h)"

        # 병합 파일 존재 확인
        if not os.path.exists(self.merged_file):
            return True, "Merged file not found"

        # POE 버전 변경 확인
        cache = self.load_cache()
        current_version = self.get_poe_patch_version()
        cached_version = cache.get('poe_version')

        if current_version and current_version != cached_version:
            return True, f"POE version changed: {cached_version} -> {current_version}"

        return False, "Cache is valid"

    def update_awakened_data(self) -> bool:
        """Awakened POE Trade 데이터 업데이트"""
        print("[INFO] Updating Awakened POE Trade data...", file=sys.stderr)

        try:
            translations = extract_all_awakened_translations()

            with open(self.awakened_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, ensure_ascii=False, indent=2)

            print(f"[OK] Awakened data: {len(translations.get('items', {}))} items, "
                  f"{len(translations.get('stats', {}))} stats", file=sys.stderr)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to update Awakened data: {e}", file=sys.stderr)
            return False

    def update_trade_api_data(self) -> bool:
        """POE Trade API 데이터 업데이트"""
        print("[INFO] Updating POE Trade API data...", file=sys.stderr)

        try:
            fetcher = POETradeKoreanFetcher(rate_limit_delay=1.5)
            all_data = fetcher.collect_all_korean_data(self.data_dir)

            print(f"[OK] Trade API data: {len(all_data.get('stats', {}))} stats, "
                  f"{len(all_data.get('items', {}))} items", file=sys.stderr)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to update Trade API data: {e}", file=sys.stderr)
            return False

    def merge_all_data(self) -> bool:
        """모든 데이터 병합"""
        print("[INFO] Merging all translation data...", file=sys.stderr)

        try:
            merged = merge_translations(
                self.awakened_file,
                self.trade_api_file,
                self.poecharm_file,
                self.merged_file
            )

            print(f"[OK] Merged data: {len(merged.get('items', {}))} items, "
                  f"{len(merged.get('stats', {}))} stats, "
                  f"{len(merged.get('skills', {}))} skills", file=sys.stderr)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to merge data: {e}", file=sys.stderr)
            return False

    def run_update(self, force: bool = False) -> bool:
        """전체 업데이트 실행

        Args:
            force: 강제 업데이트 여부

        Returns:
            업데이트 성공 여부
        """
        needs_update, reason = self.needs_update(force)

        if not needs_update:
            print(f"[INFO] No update needed: {reason}", file=sys.stderr)
            return True

        print(f"[INFO] Starting update: {reason}", file=sys.stderr)
        print("=" * 50, file=sys.stderr)

        success = True

        # 1. Awakened POE Trade 데이터
        if not self.update_awakened_data():
            success = False

        # 2. POE Trade API 데이터
        if not self.update_trade_api_data():
            success = False

        # 3. 데이터 병합
        if success and not self.merge_all_data():
            success = False

        # 캐시 업데이트
        if success:
            cache = {
                'last_update': datetime.now().isoformat(),
                'poe_version': self.get_poe_patch_version(),
                'current_league': self.get_current_league(),
            }
            self.save_cache(cache)

        print("=" * 50, file=sys.stderr)
        if success:
            print("[완료] Translation update completed successfully", file=sys.stderr)
        else:
            print("[경고] Translation update completed with errors", file=sys.stderr)

        return success

    def get_status(self) -> Dict:
        """현재 상태 조회"""
        cache = self.load_cache()

        status = {
            'last_update': cache.get('last_update', 'Never'),
            'poe_version': cache.get('poe_version', 'Unknown'),
            'current_league': cache.get('current_league', 'Unknown'),
            'cache_valid': self.is_cache_valid(),
            'files': {}
        }

        # 파일 상태
        for name, path in [
            ('awakened', self.awakened_file),
            ('trade_api', self.trade_api_file),
            ('poecharm', self.poecharm_file),
            ('merged', self.merged_file),
        ]:
            if os.path.exists(path):
                stat = os.stat(path)
                status['files'][name] = {
                    'exists': True,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            else:
                status['files'][name] = {'exists': False}

        return status


def main():
    import argparse

    parser = argparse.ArgumentParser(description='POE 번역 데이터 자동 업데이트')
    parser.add_argument('--force', action='store_true', help='강제 업데이트')
    parser.add_argument('--status', action='store_true', help='현재 상태 조회')
    parser.add_argument('--output', type=str, default='./data', help='출력 디렉토리')

    args = parser.parse_args()

    pipeline = TranslationUpdatePipeline(args.output)

    if args.status:
        status = pipeline.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return

    # 업데이트 실행
    success = pipeline.run_update(force=args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
