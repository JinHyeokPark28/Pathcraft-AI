# -*- coding: utf-8 -*-

"""
POB Link Collector from Reddit Build Guides
Reddit 빌드 가이드에서 POB 링크를 추출하고 완전한 빌드 데이터 수집
"""

import requests
import json
import os
import re
import time
from typing import List, Dict, Optional, Any
from datetime import datetime

# 기존 모듈 import
from pob_parser import get_pob_code_from_url, decode_pob_code, parse_pob_xml

# Reddit API
REDDIT_API_BASE = "https://www.reddit.com"
SUBREDDIT = "pathofexile"
HEADERS = {'User-Agent': 'PathcraftAI/1.0'}

# 빌드 데이터 저장 디렉토리
REDDIT_BUILDS_DIR = os.path.join(os.path.dirname(__file__), "build_data", "reddit_builds")
INDEX_FILE = os.path.join(REDDIT_BUILDS_DIR, "index.json")

# POB 링크 패턴
POB_LINK_PATTERNS = {
    'pobb_in': r'(?:https?://)?(?:www\.)?pobb\.in/([a-zA-Z0-9_-]+)',
    'pastebin': r'(?:https?://)?(?:www\.)?pastebin\.com/(?:raw/)?([a-zA-Z0-9]+)',
    'poe_ninja': r'(?:https?://)?poe\.ninja/pob/([a-zA-Z0-9]+)'
}

def ensure_reddit_builds_dir():
    """Reddit 빌드 저장 디렉토리 생성"""
    if not os.path.exists(REDDIT_BUILDS_DIR):
        os.makedirs(REDDIT_BUILDS_DIR)
        print(f"[INFO] Created directory: {REDDIT_BUILDS_DIR}")

def search_reddit_build_guides(limit: int = 50, keyword: str = None) -> List[Dict]:
    """
    Reddit에서 빌드 가이드 검색

    Args:
        limit: 최대 검색 결과 수
        keyword: 검색 키워드 (예: "Death's Oath", "Kinetic Fusillade")

    Returns:
        빌드 가이드 게시글 리스트
    """
    url = f"{REDDIT_API_BASE}/r/{SUBREDDIT}/search.json"

    # 여러 검색어로 검색
    if keyword:
        queries = [
            f'{keyword} build POB',
            f'{keyword} build guide',
            f'{keyword} pobb.in',
            f'{keyword} 3.27'
        ]
    else:
        queries = [
            'flair:"Guide" build 3.27',
            'flair:"Build" POB Keepers',
            'build guide pastebin',
            'build guide pobb.in'
        ]

    all_posts = []

    for query in queries:
        params = {
            'q': query,
            'restrict_sr': 'on',
            'sort': 'new',
            'limit': limit,
            't': 'month'  # 최근 1개월
        }

        try:
            print(f"[INFO] Searching Reddit: {query}")
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            posts = data.get('data', {}).get('children', [])
            for child in posts:
                post_data = child.get('data', {})
                if post_data and is_build_guide(post_data):
                    all_posts.append(post_data)

            time.sleep(1)  # Rate limiting

        except Exception as e:
            print(f"[WARN] Failed to search '{query}': {e}")

    # 중복 제거 (post id 기준)
    unique_posts = {post['id']: post for post in all_posts}.values()
    posts_list = list(unique_posts)

    # 점수 순으로 정렬
    posts_list.sort(key=lambda x: x.get('score', 0), reverse=True)

    print(f"[INFO] Found {len(posts_list)} unique build guide posts")
    return posts_list

def is_build_guide(post: Dict) -> bool:
    """
    빌드 가이드 게시글인지 확인

    Args:
        post: Reddit 게시글 데이터

    Returns:
        빌드 가이드 여부
    """
    title = post.get('title', '').lower()
    link_flair = (post.get('link_flair_text') or '').lower()
    selftext = post.get('selftext', '').lower()

    # 빌드 가이드 키워드
    build_keywords = ['build', 'guide', 'pob', 'pastebin', 'pobb.in']
    has_keyword = any(kw in title or kw in selftext for kw in build_keywords)

    # Flair 확인
    is_guide_flair = 'guide' in link_flair or 'build' in link_flair

    # 최소 점수 (품질 보장)
    min_score = post.get('score', 0) >= 5

    return (has_keyword or is_guide_flair) and min_score

def extract_pob_links(text: str) -> List[str]:
    """
    텍스트에서 POB 링크 추출

    Args:
        text: 게시글 본문 또는 댓글

    Returns:
        POB 링크 리스트 (정규화된 URL)
    """
    links = []

    # pobb.in
    matches = re.findall(POB_LINK_PATTERNS['pobb_in'], text, re.IGNORECASE)
    for code in matches:
        links.append(f"https://pobb.in/{code}")

    # pastebin
    matches = re.findall(POB_LINK_PATTERNS['pastebin'], text, re.IGNORECASE)
    for code in matches:
        links.append(f"https://pastebin.com/raw/{code}")

    # poe.ninja/pob (리다이렉트되지만 일단 추가)
    matches = re.findall(POB_LINK_PATTERNS['poe_ninja'], text, re.IGNORECASE)
    for code in matches:
        links.append(f"https://poe.ninja/pob/{code}")

    # 중복 제거
    return list(set(links))

def extract_pob_links_from_post(post: Dict) -> List[str]:
    """
    Reddit 게시글에서 모든 POB 링크 추출

    Args:
        post: Reddit 게시글 데이터

    Returns:
        POB 링크 리스트
    """
    links = []

    # 본문에서 추출
    selftext = post.get('selftext', '')
    links.extend(extract_pob_links(selftext))

    # URL 필드에서 추출 (링크 게시글인 경우)
    url = post.get('url', '')
    if 'pobb.in' in url or 'pastebin.com' in url:
        links.extend(extract_pob_links(url))

    return list(set(links))

def download_and_parse_pob(pob_url: str) -> Optional[Dict]:
    """
    POB 링크에서 빌드 데이터 다운로드 및 파싱

    Args:
        pob_url: POB 링크 (pobb.in, pastebin)

    Returns:
        파싱된 빌드 데이터
    """
    try:
        print(f"  [INFO] Downloading POB: {pob_url}")

        # POB 코드 가져오기 (기존 함수 재사용)
        pob_code = get_pob_code_from_url(pob_url)
        if not pob_code:
            print(f"  [ERROR] Failed to get POB code from {pob_url}")
            return None

        # POB 코드 디코딩
        xml_string = decode_pob_code(pob_code)
        if not xml_string:
            print(f"  [ERROR] Failed to decode POB code")
            return None

        # XML 파싱 (pob_url도 전달)
        build_data = parse_pob_xml(xml_string, pob_url)
        if not build_data:
            print(f"  [ERROR] Failed to parse POB XML")
            return None

        # 원본 링크 추가
        build_data['source'] = {
            'type': 'reddit_guide',
            'pob_link': pob_url,
            'collected_at': datetime.now().isoformat()
        }

        print(f"  [OK] Parsed build: {build_data.get('meta', {}).get('build_name', 'Unknown')}")
        return build_data

    except Exception as e:
        print(f"  [ERROR] Failed to download/parse POB: {e}")
        return None

def collect_builds_from_reddit(max_builds: int = 10, keyword: str = None) -> List[Dict]:
    """
    Reddit에서 POB 빌드 수집

    Args:
        max_builds: 수집할 최대 빌드 수
        keyword: 검색 키워드 (예: "Death's Oath")

    Returns:
        빌드 데이터 리스트
    """
    ensure_reddit_builds_dir()

    print("=" * 60)
    if keyword:
        print(f"Collecting POB Builds: {keyword}")
    else:
        print(f"Collecting POB Builds from Reddit Build Guides")
    print("=" * 60)

    # Reddit 검색
    posts = search_reddit_build_guides(limit=50, keyword=keyword)

    builds = []
    processed_links = set()

    for post in posts:
        if len(builds) >= max_builds:
            break

        title = post.get('title', '')
        author = post.get('author', '')
        score = post.get('score', 0)
        permalink = post.get('permalink', '')

        print(f"\n[INFO] Processing: {title[:60]}...")
        print(f"       Author: {author}, Score: {score}")

        # POB 링크 추출
        pob_links = extract_pob_links_from_post(post)

        if not pob_links:
            print(f"  [WARN] No POB links found in post")
            continue

        print(f"  [INFO] Found {len(pob_links)} POB link(s)")

        # 각 POB 링크 다운로드 및 파싱
        for pob_link in pob_links:
            if len(builds) >= max_builds:
                break

            # 중복 체크
            if pob_link in processed_links:
                print(f"  [SKIP] Already processed: {pob_link}")
                continue

            processed_links.add(pob_link)

            # 다운로드 및 파싱
            build_data = download_and_parse_pob(pob_link)

            if build_data:
                # Reddit 메타데이터 추가
                build_data['source']['reddit_post'] = {
                    'title': title,
                    'author': author,
                    'score': score,
                    'url': f"{REDDIT_API_BASE}{permalink}"
                }

                builds.append(build_data)
                print(f"  [OK] Build {len(builds)}/{max_builds} collected")

            # Rate limiting
            time.sleep(1)

    print("\n" + "=" * 60)
    print(f"Collection Summary:")
    print(f"  - Posts processed: {len(posts)}")
    print(f"  - Builds collected: {len(builds)}")
    print(f"  - Unique POB links: {len(processed_links)}")
    print("=" * 60)

    return builds

def save_builds(builds: List[Dict]):
    """
    빌드 데이터를 파일로 저장

    Args:
        builds: 빌드 데이터 리스트
    """
    if not builds:
        print("[WARN] No builds to save")
        return

    # 개별 빌드 파일 저장
    index_data = {
        "collection_metadata": {
            "collected_at": datetime.now().isoformat(),
            "league": "Keepers",
            "patch": "3.27",
            "total_builds": len(builds),
            "source": "reddit_guides"
        },
        "builds": []
    }

    for i, build in enumerate(builds, 1):
        build_id = f"build_{i:04d}"
        filename = f"{build_id}.json"
        filepath = os.path.join(REDDIT_BUILDS_DIR, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(build, f, ensure_ascii=False, indent=2)

            print(f"[OK] Saved: {filename}")

            # 인덱스에 추가
            index_entry = {
                "build_id": build_id,
                "build_file": filename,
                "build_name": build.get('meta', {}).get('build_name', 'Unknown'),
                "class": build.get('meta', {}).get('class', 'Unknown'),
                "ascendancy": build.get('meta', {}).get('ascendancy', 'Unknown'),
                "pob_link": build.get('source', {}).get('pob_link', ''),
                "reddit_post": build.get('source', {}).get('reddit_post', {}),
                "has_passive_tree": 'tree' in build.get('overview', {}),
                "status": "parsed_success"
            }
            index_data['builds'].append(index_entry)

        except Exception as e:
            print(f"[ERROR] Failed to save {filename}: {e}")

    # 인덱스 저장
    try:
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Saved index: {INDEX_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to save index: {e}")

def show_collection_stats():
    """수집된 빌드 통계 출력"""
    if not os.path.exists(INDEX_FILE):
        print("[INFO] No collection found")
        return

    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index = json.load(f)

        metadata = index.get('collection_metadata', {})
        builds = index.get('builds', [])

        print("=" * 60)
        print("Reddit Build Collection Stats")
        print("=" * 60)
        print(f"Collected at: {metadata.get('collected_at', 'Unknown')}")
        print(f"League: {metadata.get('league', 'Unknown')}")
        print(f"Patch: {metadata.get('patch', 'Unknown')}")
        print(f"Total builds: {metadata.get('total_builds', 0)}")
        print()

        # 어센던시 분포
        ascendancies = {}
        for build in builds:
            asc = build.get('ascendancy', 'Unknown')
            ascendancies[asc] = ascendancies.get(asc, 0) + 1

        print("Ascendancy Distribution:")
        for asc, count in sorted(ascendancies.items(), key=lambda x: x[1], reverse=True):
            print(f"  {asc:30s} - {count:2d}")

        print("\nBuilds with passive trees:")
        tree_count = sum(1 for b in builds if b.get('has_passive_tree', False))
        print(f"  {tree_count}/{len(builds)} builds")

        print("\nRecent builds:")
        for build in builds[:5]:
            print(f"  {build['build_id']}: {build['build_name'][:50]}")
            print(f"    - {build['class']} ({build['ascendancy']})")
            print(f"    - Reddit: {build.get('reddit_post', {}).get('score', 0)} upvotes")

        print("=" * 60)

    except Exception as e:
        print(f"[ERROR] Failed to load stats: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='POB Link Collector from Reddit')
    parser.add_argument('--collect', action='store_true', help='Collect builds from Reddit')
    parser.add_argument('--limit', type=int, default=10, help='Maximum builds to collect (default: 10)')
    parser.add_argument('--keyword', type=str, help='Search keyword (e.g., "Death\'s Oath")')
    parser.add_argument('--stats', action='store_true', help='Show collection statistics')

    args = parser.parse_args()

    if args.collect:
        builds = collect_builds_from_reddit(max_builds=args.limit, keyword=args.keyword)
        if builds:
            save_builds(builds)
    elif args.stats:
        show_collection_stats()
    else:
        parser.print_help()
