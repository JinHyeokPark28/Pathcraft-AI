# -*- coding: utf-8 -*-
"""
YouTube Build Collector
YouTube에서 POE 빌드 가이드를 검색하고 POB 링크를 추출
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
import argparse

# .env 파일 지원
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv가 없어도 환경변수는 사용 가능

def load_from_cache(keyword: str, league_version: str) -> Optional[List[Dict]]:
    """
    캐시에서 YouTube 빌드 로드 (24시간 유효)

    Args:
        keyword: 빌드 키워드
        league_version: 리그 버전

    Returns:
        캐시된 빌드 리스트 (없거나 만료되면 None)
    """
    cache_dir = os.path.join(os.path.dirname(__file__), "build_data", "youtube_cache")
    os.makedirs(cache_dir, exist_ok=True)

    # 파일명에서 특수문자 제거
    safe_keyword = re.sub(r'[^\w\s-]', '', keyword).strip().replace(' ', '_')
    cache_file = os.path.join(cache_dir, f"{safe_keyword}_{league_version}.json")

    if not os.path.exists(cache_file):
        return None

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 캐시 시간 확인 (24시간)
        cached_at = datetime.fromisoformat(data['cached_at'])
        age_hours = (datetime.now() - cached_at).total_seconds() / 3600

        if age_hours > 24:
            print(f"[CACHE] Expired ({age_hours:.1f}h old)")
            return None

        print(f"[CACHE] Found ({age_hours:.1f}h old)")
        return data['builds']

    except Exception as e:
        print(f"[CACHE] Error loading cache: {e}")
        return None

def save_to_cache(keyword: str, league_version: str, builds: List[Dict]):
    """
    YouTube 빌드를 캐시에 저장

    Args:
        keyword: 빌드 키워드
        league_version: 리그 버전
        builds: 빌드 리스트
    """
    cache_dir = os.path.join(os.path.dirname(__file__), "build_data", "youtube_cache")
    os.makedirs(cache_dir, exist_ok=True)

    safe_keyword = re.sub(r'[^\w\s-]', '', keyword).strip().replace(' ', '_')
    cache_file = os.path.join(cache_dir, f"{safe_keyword}_{league_version}.json")

    try:
        data = {
            'keyword': keyword,
            'league_version': league_version,
            'cached_at': datetime.now().isoformat(),
            'builds': builds
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[CACHE] Saved {len(builds)} builds for {keyword}")

    except Exception as e:
        print(f"[CACHE] Error saving cache: {e}")

def search_youtube_builds(
    keyword: str,
    league_version: str = "3.27",
    max_results: int = 10,
    api_key: Optional[str] = None,
    use_cache: bool = True
) -> List[Dict]:
    """
    YouTube에서 빌드 검색

    Args:
        keyword: 빌드 키워드 (예: "Death's Oath")
        league_version: 리그 버전 (예: "3.27")
        max_results: 최대 결과 수
        api_key: YouTube API 키 (None이면 환경변수에서 읽음)
        use_cache: 캐시 사용 여부 (24시간 캐시)

    Returns:
        빌드 정보 리스트
    """

    print("=" * 80)
    print("YOUTUBE BUILD COLLECTOR")
    print("=" * 80)
    print(f"Search Query: poe {league_version} {keyword}")
    print(f"Max Results: {max_results}")
    print("=" * 80)
    print()

    # 캐시 확인 (API 할당량 절약)
    if use_cache:
        cached = load_from_cache(keyword, league_version)
        if cached:
            print(f"[CACHE] Using cached results for {keyword}")
            return cached[:max_results]

    # API 키 확인 (인자 > 환경변수 > .env)
    if api_key is None:
        api_key = os.environ.get('YOUTUBE_API_KEY')

    if not api_key:
        print("[ERROR] YOUTUBE_API_KEY not found")
        print("[INFO] Please set YOUTUBE_API_KEY environment variable")
        print("[INFO] Get your API key from: https://console.cloud.google.com/apis/credentials")
        return []

    try:
        from googleapiclient.discovery import build
    except ImportError:
        print("[ERROR] google-api-python-client not installed")
        print("[INFO] Run: pip install google-api-python-client")
        return []

    try:
        # YouTube API 클라이언트 생성
        youtube = build('youtube', 'v3', developerKey=api_key)

        # 검색 쿼리
        search_query = f"poe {league_version} {keyword} build guide"

        print(f"[INFO] Searching YouTube for: {search_query}")

        # 검색 실행
        search_response = youtube.search().list(
            q=search_query,
            part='id,snippet',
            maxResults=max_results,
            type='video',
            order='relevance',
            relevanceLanguage='en'
        ).execute()

        builds = []

        for item in search_response.get('items', []):
            video_id = item['id']['videoId']
            snippet = item['snippet']

            # 비디오 상세 정보 가져오기 (description 포함)
            video_response = youtube.videos().list(
                part='snippet,statistics',
                id=video_id
            ).execute()

            if not video_response.get('items'):
                continue

            video_data = video_response['items'][0]
            description = video_data['snippet']['description']
            statistics = video_data['statistics']

            # POB 링크 추출
            pob_links = extract_pob_links(description)

            if pob_links:
                # 썸네일 URL 추출 (medium: 320x180)
                thumbnails = video_data['snippet'].get('thumbnails', {})
                thumbnail_url = (
                    thumbnails.get('medium', {}).get('url') or
                    thumbnails.get('default', {}).get('url') or
                    f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                )

                build = {
                    'video_id': video_id,
                    'title': snippet['title'],
                    'channel': snippet['channelTitle'],
                    'published_at': snippet['publishedAt'],
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'thumbnail': thumbnail_url,
                    'views': int(statistics.get('viewCount', 0)),
                    'likes': int(statistics.get('likeCount', 0)),
                    'pob_links': pob_links,
                    'description_snippet': description[:500],
                    'source': 'youtube'
                }
                builds.append(build)

                print(f"[FOUND] {snippet['title'][:60]}...")
                print(f"        Channel: {snippet['channelTitle']}")
                print(f"        POB Links: {len(pob_links)}")
                print()

        print(f"[OK] Found {len(builds)} videos with POB links")

        # API 호출 성공 시 캐시에 저장
        if use_cache and builds:
            save_to_cache(keyword, league_version, builds)

        return builds

    except Exception as e:
        print(f"[ERROR] YouTube API call failed: {e}")
        return []


def extract_pob_links(text: str) -> List[str]:
    """
    텍스트에서 POB 링크 추출

    Args:
        text: 검색할 텍스트

    Returns:
        POB 링크 리스트
    """

    pob_patterns = [
        r'https?://pobb\.in/[A-Za-z0-9_-]+',
        r'https?://pastebin\.com/[A-Za-z0-9]+',
        r'https?://poe\.ninja/pob/[A-Za-z0-9]+',
    ]

    links = []

    for pattern in pob_patterns:
        matches = re.findall(pattern, text)
        links.extend(matches)

    # 중복 제거
    return list(set(links))




def save_youtube_builds(builds: List[Dict], keyword: str, output_dir: str = "build_data/youtube_builds"):
    """
    YouTube 빌드를 파일에 저장

    Args:
        builds: 빌드 리스트
        keyword: 검색 키워드
        output_dir: 출력 디렉토리
    """

    os.makedirs(output_dir, exist_ok=True)

    # 파일명에서 특수문자 제거
    safe_keyword = re.sub(r'[^\w\s-]', '', keyword).strip().replace(' ', '_')
    output_file = os.path.join(output_dir, f"{safe_keyword}_youtube.json")

    data = {
        'metadata': {
            'keyword': keyword,
            'collection_date': datetime.now().isoformat(),
            'total_builds': len(builds)
        },
        'builds': builds
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print()
    print(f"[OK] Saved to: {output_file}")
    print(f"     Total builds: {len(builds)}")


def search_and_save(keyword: str, league_version: str = "3.27", max_results: int = 10, api_key: Optional[str] = None):
    """
    YouTube 검색 및 저장
    """

    builds = search_youtube_builds(keyword, league_version, max_results, api_key)

    if builds:
        save_youtube_builds(builds, keyword)

        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Keyword: {keyword}")
        print(f"League: {league_version}")
        print(f"Results: {len(builds)}")
        print(f"Total POB Links: {sum(len(b['pob_links']) for b in builds)}")
        print()

        return builds
    else:
        print("[WARN] No builds found")
        return []


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='YouTube Build Collector')
    parser.add_argument('--keyword', type=str, required=True, help='Build keyword')
    parser.add_argument('--league', type=str, default='3.27', help='League version')
    parser.add_argument('--max', type=int, default=10, help='Max results')
    parser.add_argument('--api-key', type=str, default=None, help='YouTube API key')

    args = parser.parse_args()

    search_and_save(args.keyword, args.league, args.max, args.api_key)
