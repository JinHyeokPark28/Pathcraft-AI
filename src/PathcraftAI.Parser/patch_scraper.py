# -*- coding: utf-8 -*-

"""
Path of Exile 1 Patch Notes Scraper
Reddit API를 사용하여 r/pathofexile에서 공식 패치 노트 수집
"""

import requests
import json
import os
import re
import sys
from datetime import datetime
from typing import List, Dict, Optional

# Reddit JSON API 사용 (API key 불필요)
REDDIT_API_BASE = "https://www.reddit.com"
SUBREDDIT = "pathofexile"
HEADERS = {'User-Agent': 'PathcraftAI/1.0'}

# 패치 노트 저장 디렉토리
PATCH_NOTES_DIR = os.path.join(os.path.dirname(__file__), "patch_notes")
PATCH_INDEX_FILE = os.path.join(PATCH_NOTES_DIR, "patch_index.json")

def ensure_patch_notes_dir():
    """패치 노트 저장 디렉토리 생성"""
    if not os.path.exists(PATCH_NOTES_DIR):
        os.makedirs(PATCH_NOTES_DIR)
        print(f"[INFO] Created directory: {PATCH_NOTES_DIR}")

def search_patch_notes(query: str = "patch notes", limit: int = 100) -> List[Dict]:
    """
    Reddit에서 패치 노트 검색

    Args:
        query: 검색 쿼리
        limit: 최대 결과 수 (최대 100)

    Returns:
        검색된 게시글 리스트
    """
    url = f"{REDDIT_API_BASE}/r/{SUBREDDIT}/search.json"
    params = {
        'q': f'flair:"GGG" OR flair:"News" {query}',
        'restrict_sr': 'on',
        'sort': 'new',
        'limit': limit
    }

    try:
        print(f"[INFO] Searching Reddit: {query} (limit={limit})")
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        posts = []
        for child in data.get('data', {}).get('children', []):
            post_data = child.get('data', {})
            posts.append(post_data)

        print(f"[INFO] Found {len(posts)} posts")
        return posts

    except Exception as e:
        print(f"[ERROR] Failed to search Reddit: {e}")
        return []

def extract_patch_version(title: str) -> Optional[str]:
    """
    게시글 제목에서 패치 버전 추출

    예: "3.23.0 Patch Notes" -> "3.23.0"
         "Path of Exile: Affliction - 3.23.0 Patch Notes" -> "3.23.0"
    """
    # 패턴: X.XX.X 형식의 버전 번호
    pattern = r'(\d+\.\d+\.\d+[a-z]?)'
    match = re.search(pattern, title, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def is_patch_note_post(post: Dict) -> bool:
    """
    게시글이 패치 노트인지 확인

    Args:
        post: Reddit 게시글 데이터

    Returns:
        패치 노트 여부
    """
    title = post.get('title', '').lower()
    link_flair_text = (post.get('link_flair_text') or '').lower()

    # 제목에 "patch notes" 포함 또는 GGG/News flair
    is_patch_note = (
        'patch notes' in title or
        'patch note' in title or
        link_flair_text in ['ggg', 'news', 'official']
    )

    # 제외 키워드 (토론, 질문 등 제외)
    exclude_keywords = ['question', 'discussion', 'suggestion', 'when', 'prediction']
    has_exclude = any(kw in title for kw in exclude_keywords)

    return is_patch_note and not has_exclude

def parse_patch_note(post: Dict) -> Optional[Dict]:
    """
    Reddit 게시글을 패치 노트 구조로 파싱

    Args:
        post: Reddit 게시글 데이터

    Returns:
        패치 노트 JSON 구조
    """
    title = post.get('title', '')
    version = extract_patch_version(title)

    if not version:
        print(f"[WARN] No version found in title: {title}")
        return None

    # Reddit 게시글 URL
    permalink = post.get('permalink', '')
    url = f"{REDDIT_API_BASE}{permalink}"

    # 게시글 본문 (selftext)
    body = post.get('selftext', '')

    # 외부 링크 (GGG 공식 포럼 링크 등)
    external_url = post.get('url', '')
    if external_url and 'pathofexile.com' in external_url:
        official_url = external_url
    else:
        official_url = ""

    # 생성일자
    created_utc = post.get('created_utc', 0)
    date = datetime.fromtimestamp(created_utc).strftime('%Y-%m-%d')

    # 커뮤니티 반응
    score = post.get('score', 0)
    num_comments = post.get('num_comments', 0)

    patch_note = {
        "patch_id": version,
        "date": date,
        "title": title,
        "reddit_url": url,
        "official_url": official_url,
        "body": body[:500],  # 처음 500자만 저장 (미리보기)
        "full_text_url": official_url if official_url else url,
        "community_reaction": {
            "upvotes": score,
            "comments": num_comments
        },
        "metadata": {
            "collected_at": datetime.now().isoformat(),
            "source": "reddit",
            "subreddit": SUBREDDIT
        }
    }

    return patch_note

def save_patch_note(patch_note: Dict) -> bool:
    """
    패치 노트를 JSON 파일로 저장

    Args:
        patch_note: 패치 노트 데이터

    Returns:
        저장 성공 여부
    """
    patch_id = patch_note['patch_id']
    filename = f"patch_{patch_id.replace('.', '_')}.json"
    filepath = os.path.join(PATCH_NOTES_DIR, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(patch_note, f, ensure_ascii=False, indent=2)
        print(f"[OK] Saved: {filename}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save {filename}: {e}")
        return False

def load_patch_index() -> Dict[str, Dict]:
    """
    패치 노트 인덱스 로드

    Returns:
        {patch_id: {date, title, file}} 형식의 딕셔너리
    """
    if not os.path.exists(PATCH_INDEX_FILE):
        return {}

    try:
        with open(PATCH_INDEX_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to load patch index: {e}")
        return {}

def save_patch_index(index: Dict[str, Dict]):
    """패치 노트 인덱스 저장"""
    try:
        with open(PATCH_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        print(f"[OK] Patch index updated: {len(index)} patches")
    except Exception as e:
        print(f"[ERROR] Failed to save patch index: {e}")

def collect_all_patch_notes(max_posts: int = 500):
    """
    Reddit에서 모든 패치 노트 수집

    Args:
        max_posts: 검색할 최대 게시글 수
    """
    ensure_patch_notes_dir()

    print("=" * 60)
    print("Path of Exile Patch Notes Collector")
    print("=" * 60)

    # 기존 인덱스 로드
    patch_index = load_patch_index()
    print(f"[INFO] Existing patches in index: {len(patch_index)}")

    # Reddit에서 패치 노트 검색
    collected = 0
    skipped = 0

    # 여러 검색어로 나눠서 검색 (Reddit API limit=100)
    search_queries = [
        "patch notes",
        "balance changes",
        "hotfix"
    ]

    all_posts = []
    for query in search_queries:
        posts = search_patch_notes(query, limit=100)
        all_posts.extend(posts)

    # 중복 제거 (post id 기준)
    unique_posts = {post['id']: post for post in all_posts}.values()
    print(f"[INFO] Total unique posts: {len(unique_posts)}")

    for post in unique_posts:
        if not is_patch_note_post(post):
            continue

        patch_note = parse_patch_note(post)
        if not patch_note:
            continue

        patch_id = patch_note['patch_id']

        # 이미 수집된 패치는 건너뛰기
        if patch_id in patch_index:
            skipped += 1
            continue

        # 패치 노트 저장
        if save_patch_note(patch_note):
            patch_index[patch_id] = {
                "date": patch_note['date'],
                "title": patch_note['title'],
                "file": f"patch_{patch_id.replace('.', '_')}.json"
            }
            collected += 1

    # 인덱스 저장
    save_patch_index(patch_index)

    print("=" * 60)
    print(f"Collection Summary:")
    print(f"  - New patches collected: {collected}")
    print(f"  - Already existing: {skipped}")
    print(f"  - Total patches: {len(patch_index)}")
    print("=" * 60)

def get_latest_patch() -> Optional[Dict]:
    """
    가장 최신 패치 노트 반환

    Returns:
        최신 패치 노트 데이터
    """
    patch_index = load_patch_index()
    if not patch_index:
        return None

    # 날짜 기준 정렬
    sorted_patches = sorted(
        patch_index.items(),
        key=lambda x: x[1]['date'],
        reverse=True
    )

    if not sorted_patches:
        return None

    patch_id, info = sorted_patches[0]
    filepath = os.path.join(PATCH_NOTES_DIR, info['file'])

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load patch {patch_id}: {e}")
        return None

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='POE Patch Notes Scraper')
    parser.add_argument('--collect', action='store_true', help='Collect all patch notes')
    parser.add_argument('--latest', action='store_true', help='Show latest patch')
    parser.add_argument('--stats', action='store_true', help='Show collection statistics')

    args = parser.parse_args()

    if args.collect:
        collect_all_patch_notes()
    elif args.latest:
        latest = get_latest_patch()
        if latest:
            print(json.dumps(latest, indent=2, ensure_ascii=False))
        else:
            print("[INFO] No patches found")
    elif args.stats:
        patch_index = load_patch_index()
        print(f"Total patches: {len(patch_index)}")
        if patch_index:
            print("\nRecent patches:")
            sorted_patches = sorted(
                patch_index.items(),
                key=lambda x: x[1]['date'],
                reverse=True
            )[:10]
            for patch_id, info in sorted_patches:
                print(f"  {patch_id:12s} - {info['date']} - {info['title'][:50]}")
    else:
        parser.print_help()
