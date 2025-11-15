# -*- coding: utf-8 -*-
"""
YouTube + POB Integration
YouTube에서 빌드를 검색하고 POB 링크를 파싱하여 완전한 빌드 데이터 추출
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import argparse

from youtube_build_collector import search_youtube_builds
from pob_parser import get_pob_code_from_url, decode_pob_code, parse_pob_xml

# .env 파일 지원
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def search_and_parse_builds(
    keyword: str,
    league_version: str = "3.27",
    max_results: int = 10,
    parse_pob: bool = True,
    api_key: Optional[str] = None
) -> List[Dict]:
    """
    YouTube에서 빌드 검색 + POB 파싱

    Args:
        keyword: 빌드 키워드
        league_version: 리그 버전
        max_results: 최대 결과 수
        parse_pob: POB 링크를 파싱할지 여부
        api_key: YouTube API 키

    Returns:
        파싱된 빌드 데이터 리스트
    """

    print("=" * 80)
    print("YOUTUBE + POB BUILD SEARCH")
    print("=" * 80)
    print(f"Keyword: {keyword}")
    print(f"League: {league_version}")
    print(f"Parse POB: {parse_pob}")
    print("=" * 80)
    print()

    # Step 1: YouTube 검색
    print("[STEP 1] Searching YouTube...")
    youtube_builds = search_youtube_builds(keyword, league_version, max_results, api_key)

    if not youtube_builds:
        print("[WARN] No YouTube builds found")
        return []

    print(f"[OK] Found {len(youtube_builds)} YouTube videos")
    print()

    # Step 2: POB 파싱
    parsed_builds = []

    if parse_pob:
        print("[STEP 2] Parsing POB links...")
        print()

        for i, build in enumerate(youtube_builds):
            video_title = build['title']
            pob_links = build.get('pob_links', [])

            print(f"[{i+1}/{len(youtube_builds)}] {video_title[:60]}...")
            print(f"         POB Links: {len(pob_links)}")

            if not pob_links:
                print(f"         [SKIP] No POB links")
                print()
                continue

            # 각 POB 링크 파싱
            for pob_url in pob_links:
                print(f"         [PARSE] {pob_url}")

                try:
                    # POB 코드 가져오기
                    pob_code = get_pob_code_from_url(pob_url)
                    if not pob_code:
                        print(f"         [ERROR] Could not fetch POB code")
                        continue

                    # 디코딩
                    xml_data = decode_pob_code(pob_code)
                    if not xml_data:
                        print(f"         [ERROR] Could not decode POB data")
                        continue

                    # 파싱
                    parsed_build = parse_pob_xml(xml_data, pob_url)
                    if not parsed_build:
                        print(f"         [ERROR] Could not parse POB XML")
                        continue

                    # YouTube 메타데이터 추가
                    parsed_build['youtube'] = {
                        'video_id': build['video_id'],
                        'title': build['title'],
                        'channel': build['channel'],
                        'url': build['url'],
                        'views': build['views'],
                        'likes': build.get('likes', 0),
                        'published_at': build['published_at']
                    }

                    parsed_builds.append(parsed_build)

                    build_name = parsed_build['meta']['build_name']
                    print(f"         [OK] {build_name}")

                except Exception as e:
                    print(f"         [ERROR] Failed to parse {pob_url}: {e}")

            print()

        print(f"[OK] Successfully parsed {len(parsed_builds)} POB builds")

    else:
        # POB 파싱 없이 YouTube 데이터만 반환
        parsed_builds = youtube_builds

    return parsed_builds


def save_parsed_builds(builds: List[Dict], keyword: str, output_dir: str = "build_data/parsed_builds"):
    """
    파싱된 빌드를 파일에 저장

    Args:
        builds: 파싱된 빌드 리스트
        keyword: 검색 키워드
        output_dir: 출력 디렉토리
    """

    os.makedirs(output_dir, exist_ok=True)

    # 파일명 생성
    import re
    safe_keyword = re.sub(r'[^\w\s-]', '', keyword).strip().replace(' ', '_')
    output_file = os.path.join(output_dir, f"{safe_keyword}_parsed.json")

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


def display_build_summary(builds: List[Dict]):
    """
    빌드 요약 정보 출력

    Args:
        builds: 빌드 리스트
    """

    print()
    print("=" * 80)
    print("BUILD SUMMARY")
    print("=" * 80)

    for i, build in enumerate(builds):
        meta = build.get('meta', {})
        youtube = build.get('youtube', {})

        print(f"\n[{i+1}] {meta.get('build_name', 'Unknown Build')}")
        print(f"    Class: {meta.get('class')} / {meta.get('ascendancy')}")
        print(f"    POB: {meta.get('pob_link', 'N/A')}")

        if youtube:
            print(f"    Video: {youtube.get('title', 'N/A')[:60]}...")
            print(f"    Channel: {youtube.get('channel', 'N/A')}")
            print(f"    Views: {youtube.get('views', 0):,}")
            print(f"    URL: {youtube.get('url', 'N/A')}")

        # 주요 스킬
        stages = build.get('progression_stages', [])
        if stages:
            gem_setups = stages[0].get('gem_setups', {})
            if gem_setups:
                first_skill = list(gem_setups.keys())[0] if gem_setups else "N/A"
                print(f"    Main Skill: {first_skill}")

        # 주요 아이템
        if stages:
            gear = stages[0].get('gear_recommendation', {})
            if gear:
                weapon_slot = gear.get('Weapon 1', {})
                if weapon_slot:
                    print(f"    Weapon: {weapon_slot.get('name', 'N/A')}")

    print()
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='YouTube + POB Build Search')
    parser.add_argument('--keyword', type=str, required=True, help='Build keyword')
    parser.add_argument('--league', type=str, default='3.27', help='League version')
    parser.add_argument('--max', type=int, default=10, help='Max results')
    parser.add_argument('--no-parse', action='store_true', help='Skip POB parsing')
    parser.add_argument('--api-key', type=str, default=None, help='YouTube API key')

    args = parser.parse_args()

    # 검색 및 파싱
    builds = search_and_parse_builds(
        keyword=args.keyword,
        league_version=args.league,
        max_results=args.max,
        parse_pob=not args.no_parse,
        api_key=args.api_key
    )

    if builds:
        # 저장
        save_parsed_builds(builds, args.keyword)

        # 요약 출력
        display_build_summary(builds)

        print()
        print(f"[OK] Total: {len(builds)} parsed builds")
    else:
        print("[WARN] No builds found")
