# -*- coding: utf-8 -*-
"""
Auto Recommendation Engine
사용자의 현재 리그/캐릭터 정보를 기반으로 자동으로 빌드 추천

OAuth 연동 시:
- account:profile: 계정 기본 정보
- account:characters: 캐릭터 정보 및 인벤토리
- account:stashes: 창고 정보 (소지 아이템 파악)
- account:leagues: 리그 정보

수동 모드 (OAuth 없이):
- 현재 리그 자동 감지
- 인기 빌드 추천
- 스트리머 빌드 추천
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import argparse

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

# 기존 모듈들은 직접 구현으로 대체 (import 순환 오류 방지)


def get_current_league() -> str:
    """
    현재 활성 리그 자동 감지

    Returns:
        현재 리그 이름 (예: "Keepers")
    """
    # poe.ninja 데이터에서 현재 리그 확인
    game_data_dir = os.path.join(os.path.dirname(__file__), "game_data")
    metadata_file = os.path.join(game_data_dir, "metadata.json")

    if os.path.exists(metadata_file):
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            return metadata.get('league', 'Keepers')

    # 기본값
    return "Keepers"


def detect_league_phase(league: str) -> str:
    """
    리그의 현재 단계 감지

    Returns:
        "pre_season": 시즌 시작 2주 전
        "early": 리그 시작 1주일 이내
        "mid": 리그 중반 (1주 ~ 1개월)
        "late": 리그 후반 (1개월 이상)
    """
    # game_data에서 리그 시작 날짜 확인
    game_data_dir = os.path.join(os.path.dirname(__file__), "game_data")
    metadata_file = os.path.join(game_data_dir, "metadata.json")

    if os.path.exists(metadata_file):
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            league_start = metadata.get('league_start_date')

            if league_start:
                try:
                    start_date = datetime.fromisoformat(league_start)
                    days_since_start = (datetime.now() - start_date).days

                    if days_since_start < -14:
                        return "pre_season"
                    elif days_since_start < 7:
                        return "early"
                    elif days_since_start < 30:
                        return "mid"
                    else:
                        return "late"
                except:
                    pass

    # 기본값: 중반으로 가정
    return "mid"


def load_user_characters_from_oauth() -> Optional[List[Dict]]:
    """
    OAuth 토큰에서 사용자 캐릭터 로드 (자동 갱신 포함)

    Returns:
        캐릭터 목록 또는 None
    """
    try:
        from poe_oauth import load_token, save_token, get_user_characters, refresh_access_token

        # 토큰 로드
        token_data = load_token()
        if not token_data:
            print("[WARNING] No OAuth token found. Please authenticate first.", file=sys.stderr)
            return None

        # 토큰 만료 확인 및 자동 갱신
        if 'expires_at' in token_data:
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            now = datetime.now()

            # 토큰이 만료되었거나 1시간 이내에 만료될 경우 갱신
            if now >= expires_at or (expires_at - now).total_seconds() < 3600:
                print(f"[INFO] Access token expired or expiring soon, refreshing...", file=sys.stderr)

                try:
                    # CLIENT_ID는 환경변수 또는 기본값 사용
                    client_id = os.environ.get('POE_CLIENT_ID', 'pathcraftai')
                    refresh_token = token_data.get('refresh_token')

                    if not refresh_token:
                        print("[WARNING] No refresh token found. Please re-authenticate.", file=sys.stderr)
                        return None

                    # 토큰 갱신
                    new_token_data = refresh_access_token(client_id, refresh_token)
                    save_token(new_token_data)
                    token_data = new_token_data

                except Exception as refresh_error:
                    print(f"[WARNING] Failed to refresh token: {refresh_error}", file=sys.stderr)
                    print("[INFO] Please re-authenticate using 'Connect POE Account' button", file=sys.stderr)
                    return None

        access_token = token_data.get('access_token')
        if not access_token:
            return None

        # 캐릭터 가져오기
        characters_data = get_user_characters(access_token)
        characters = characters_data.get('characters', [])

        if not characters:
            return None

        return characters

    except Exception as e:
        print(f"[WARNING] Failed to load user characters from OAuth: {e}", file=sys.stderr)
        return None


def get_auto_recommendations(
    league: Optional[str] = None,
    user_characters: Optional[List[Dict]] = None,
    max_builds: int = 10,
    include_streamers: bool = True,
    include_user_build_analysis: bool = True
) -> Dict:
    """
    자동 빌드 추천 시스템

    Args:
        league: 리그 이름 (None이면 자동 감지)
        user_characters: 사용자 캐릭터 목록 (OAuth 연동 시)
        max_builds: 최대 추천 빌드 수
        include_streamers: 스트리머 빌드 포함 여부
        include_user_build_analysis: 사용자 빌드 분석 포함 여부

    Returns:
        {
            "league": "Keepers",
            "league_phase": "mid",
            "user_build": {
                "character_name": "Shovel_Cats",
                "build_type": "Death's Oath Occultist",
                "main_skill": "Vaal Righteous Fire",
                "unique_items": [...],
                "upgrade_suggestions": [...]
            },
            "recommendations": [
                {
                    "category": "upgrades",
                    "title": "Recommended Upgrades for Your Build",
                    "builds": [...]
                },
                {
                    "category": "popular",
                    "title": "Most Popular Builds This Week",
                    "builds": [...]
                },
                {
                    "category": "streamer",
                    "title": "Top Streamer Builds",
                    "builds": [...]
                },
                {
                    "category": "meta",
                    "title": "Current Meta Builds",
                    "builds": [...]
                }
            ],
            "user_context": {
                "has_characters": True,
                "character_count": 3,
                "main_class": "Occultist"
            }
        }
    """

    print("=" * 80, file=sys.stderr)
    print("AUTO RECOMMENDATION ENGINE", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    print(file=sys.stderr)

    # 0. OAuth 토큰으로 사용자 캐릭터 자동 로드 (user_characters가 None인 경우)
    if user_characters is None:
        user_characters = load_user_characters_from_oauth()
        if user_characters:
            print(f"[INFO] Loaded {len(user_characters)} characters from OAuth token", file=sys.stderr)

    # 1. 리그 감지
    if not league:
        league = get_current_league()

    print(f"[INFO] Current League: {league}", file=sys.stderr)

    # 2. 리그 단계 감지
    league_phase = detect_league_phase(league)
    print(f"[INFO] League Phase: {league_phase}", file=sys.stderr)

    # 3. 사용자 컨텍스트 분석
    user_context = analyze_user_context(user_characters)
    print(f"[INFO] User Characters: {user_context['character_count']}", file=sys.stderr)

    # 3.5. 사용자 빌드 분석 (새로 추가)
    user_build_analysis = None
    if include_user_build_analysis and user_characters:
        try:
            from analyze_user_build import analyze_user_build_from_token
            print(f"[INFO] Analyzing your current build...", file=sys.stderr)
            # 이미 가져온 캐릭터 목록 전달 (Rate Limit 방지)
            user_build_analysis = analyze_user_build_from_token(user_characters)
            if user_build_analysis:
                print(f"[OK] Build analyzed: {user_build_analysis.get('build_type')}", file=sys.stderr)
        except Exception as e:
            print(f"[WARN] Failed to analyze user build: {e}", file=sys.stderr)

    print(file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    print(file=sys.stderr)

    # 4. 추천 빌드 수집
    recommendations = []

    # 4-1. 인기 빌드 (poe.ninja 기반)
    print("[PHASE 1/4] Loading popular builds from poe.ninja...", file=sys.stderr)
    popular_builds = get_popular_builds(league, limit=5)
    if popular_builds:
        recommendations.append({
            "category": "popular",
            "title": "🔥 Most Popular Builds This Week",
            "subtitle": f"Based on {league} ladder data",
            "builds": popular_builds,
            "count": len(popular_builds)
        })
        print(f"[OK] Found {len(popular_builds)} popular builds", file=sys.stderr)
    print(file=sys.stderr)

    # 4-2. 스트리머 빌드
    if include_streamers:
        print("[PHASE 2/4] Loading streamer builds...", file=sys.stderr)
        streamer_builds = get_streamer_builds_cached(league, limit=5)
        if streamer_builds:
            recommendations.append({
                "category": "streamer",
                "title": "⭐ Top Streamer Builds",
                "subtitle": "What pros are playing right now",
                "builds": streamer_builds,
                "count": len(streamer_builds)
            })
            print(f"[OK] Found {len(streamer_builds)} streamer builds", file=sys.stderr)
        print(file=sys.stderr)

    # 4-3. 메타 빌드 (현재 시즌 강력한 빌드들) - DISABLED (래더 데이터 로딩 너무 느림)
    # print("[PHASE 3/4] Loading meta builds...", file=sys.stderr)
    # meta_builds = get_meta_builds(league, league_phase, limit=5)
    # if meta_builds:
    #     recommendations.append({
    #         "category": "meta",
    #         "title": "💎 Current Meta Builds",
    #         "subtitle": f"Strongest builds for {league_phase} league",
    #         "builds": meta_builds,
    #         "count": len(meta_builds)
    #     })
    #     print(f"[OK] Found {len(meta_builds)} meta builds", file=sys.stderr)
    print(file=sys.stderr)

    # 4-3.5. 사용자 캐릭터 기반 추천 (OAuth 연동 시) - DISABLED (래더 데이터 사용)
    # if user_context.get('has_characters') and user_context.get('main_class'):
    #     print("[PHASE 3.5/4] Loading personalized builds based on your main character...", file=sys.stderr)
    #     personalized_builds = get_similar_class_builds(
    #         league,
    #         user_context['main_class'],
    #         limit=5
    #     )
    #     if personalized_builds:
    #         recommendations.insert(0, {
    #             "category": "personalized",
    #             "title": f"🎯 Recommended for Your {user_context['main_class']}",
    #             "subtitle": f"Based on your Lv{user_context.get('main_level', '?')} {user_context['main_class']}",
    #             "builds": personalized_builds,
    #             "count": len(personalized_builds)
    #         })
    #         print(f"[OK] Found {len(personalized_builds)} personalized builds", file=sys.stderr)
    #     print(file=sys.stderr)

    # 4-4. 리그 시작 전이라면 pre-season 빌드
    if league_phase == "pre_season":
        print("[PHASE 4/4] Loading pre-season practice builds...", file=sys.stderr)
        preseason_builds = get_preseason_practice_builds(league, limit=5)
        if preseason_builds:
            recommendations.insert(0, {
                "category": "preseason",
                "title": "🎯 Pre-Season Practice Builds",
                "subtitle": "What streamers are practicing before league start",
                "builds": preseason_builds,
                "count": len(preseason_builds)
            })
            print(f"[OK] Found {len(preseason_builds)} pre-season builds", file=sys.stderr)

    print(file=sys.stderr)
    print("=" * 80, file=sys.stderr)

    return {
        "league": league,
        "league_phase": league_phase,
        "user_build": user_build_analysis,
        "recommendations": recommendations,
        "user_context": user_context,
        "total_builds": sum(r['count'] for r in recommendations),
        "generated_at": datetime.now().isoformat()
    }


def get_personalized_recommendations(
    league: Optional[str] = None,
    reference_pob: Optional[str] = None,
    streamer_name: Optional[str] = None,
    max_builds: int = 10
) -> Dict:
    """
    맞춤 추천 빌드 가져오기

    Args:
        league: 리그 이름 (None이면 자동 감지)
        reference_pob: 참고하는 POB URL
        streamer_name: 참고하는 스트리머/유튜버 이름
        max_builds: 최대 빌드 수

    Returns:
        추천 결과 딕셔너리
    """

    print("=" * 80, file=sys.stderr)
    print("PERSONALIZED RECOMMENDATION ENGINE", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    print(file=sys.stderr)

    # 1. 리그 감지
    if not league:
        league = get_current_league()

    print(f"[INFO] Current League: {league}", file=sys.stderr)

    if reference_pob:
        print(f"[INFO] Reference POB: {reference_pob}", file=sys.stderr)
    if streamer_name:
        print(f"[INFO] Streamer Filter: {streamer_name}", file=sys.stderr)

    print(file=sys.stderr)

    # 2. 추천 빌드 수집
    recommendations = []

    # 2-1. 스트리머 필터링
    if streamer_name:
        print(f"[PHASE 1/2] Finding builds from {streamer_name}...", file=sys.stderr)
        streamer_builds = filter_builds_by_streamer(streamer_name, league, max_builds)
        if streamer_builds:
            recommendations.append({
                "category": "streamer_filtered",
                "title": f"⭐ {streamer_name}'s Builds",
                "subtitle": f"Latest builds from {streamer_name}",
                "builds": streamer_builds,
                "count": len(streamer_builds)
            })
            print(f"[OK] Found {len(streamer_builds)} builds from {streamer_name}", file=sys.stderr)
        else:
            print(f"[WARN] No builds found from {streamer_name}", file=sys.stderr)
        print(file=sys.stderr)

    # 2-2. POB 유사 빌드 검색
    if reference_pob:
        print(f"[PHASE 2/2] Finding similar builds to POB...", file=sys.stderr)
        similar_builds = find_similar_builds_to_pob(reference_pob, league, max_builds)
        if similar_builds:
            recommendations.append({
                "category": "similar",
                "title": "🎯 Similar Builds",
                "subtitle": "Builds similar to your reference POB",
                "builds": similar_builds,
                "count": len(similar_builds)
            })
            print(f"[OK] Found {len(similar_builds)} similar builds", file=sys.stderr)
        else:
            print(f"[WARN] No similar builds found", file=sys.stderr)
        print(file=sys.stderr)

    # 추천이 없으면 일반 인기 빌드 추가
    if not recommendations:
        print("[INFO] No personalized builds found, showing popular builds instead", file=sys.stderr)
        popular_builds = get_popular_builds(league, limit=max_builds)
        if popular_builds:
            recommendations.append({
                "category": "popular",
                "title": "🔥 Most Popular Builds",
                "subtitle": f"Top builds in {league}",
                "builds": popular_builds,
                "count": len(popular_builds)
            })

    print("=" * 80, file=sys.stderr)

    return {
        "league": league,
        "league_phase": "personalized",
        "reference_pob": reference_pob,
        "streamer_filter": streamer_name,
        "recommendations": recommendations,
        "total_builds": sum(r['count'] for r in recommendations),
        "generated_at": datetime.now().isoformat()
    }


def filter_builds_by_streamer(streamer_name: str, league: str, limit: int = 10) -> List[Dict]:
    """스트리머 이름으로 빌드 필터링"""

    # 스트리머 빌드 캐시에서 검색
    streamer_builds = get_streamer_builds_cached(league, limit=50)  # 더 많이 가져와서 필터링

    # 이름으로 필터링 (대소문자 무시, 부분 일치)
    filtered = []
    search_name = streamer_name.lower()

    for build in streamer_builds:
        streamer = build.get('streamer_name', '').lower()
        channel = build.get('channel', '').lower()

        if search_name in streamer or search_name in channel:
            filtered.append(build)
            if len(filtered) >= limit:
                break

    return filtered


def find_similar_builds_to_pob(pob_url: str, league: str, limit: int = 10) -> List[Dict]:
    """POB와 유사한 빌드 찾기"""

    try:
        # POB 분석
        from pob_xml_parser import fetch_pob_code, decode_pob, parse_pob_xml

        print(f"[INFO] Analyzing reference POB...", file=sys.stderr)
        pob_code = fetch_pob_code(pob_url)
        if not pob_code:
            print(f"[ERROR] Could not fetch POB code", file=sys.stderr)
            return []

        pob_xml = decode_pob(pob_code)
        if not pob_xml:
            print(f"[ERROR] Could not decode POB", file=sys.stderr)
            return []

        build_data = parse_pob_xml(pob_xml)
        if not build_data:
            print(f"[ERROR] Could not parse POB XML", file=sys.stderr)
            return []

        # 빌드 특징 추출
        ref_class = build_data.get('meta', {}).get('class', '')
        ref_ascendancy = build_data.get('meta', {}).get('ascendancy', '')
        ref_main_skill = build_data.get('meta', {}).get('main_skill', '')

        print(f"[INFO] Reference: {ref_class} / {ref_ascendancy} / {ref_main_skill}", file=sys.stderr)

        # 유사 빌드 검색 (인기 빌드 + 스트리머 빌드에서 검색)
        all_builds = []
        all_builds.extend(get_popular_builds(league, limit=50))
        all_builds.extend(get_streamer_builds_cached(league, limit=50))

        # 유사도 점수 계산
        similar_builds = []
        for build in all_builds:
            score = 0

            # 클래스 일치 (+3점)
            if build.get('class', '').lower() == ref_class.lower():
                score += 3

            # Ascendancy 일치 (+5점)
            if build.get('ascendancy_class', '').lower() == ref_ascendancy.lower():
                score += 5

            # 메인 스킬 일치 또는 유사 (+10점)
            build_skill = build.get('main_skill', '')
            if build_skill and ref_main_skill:
                if build_skill.lower() in ref_main_skill.lower() or ref_main_skill.lower() in build_skill.lower():
                    score += 10

            if score > 0:
                build['similarity_score'] = score
                similar_builds.append(build)

        # 점수 순 정렬
        similar_builds.sort(key=lambda b: b.get('similarity_score', 0), reverse=True)

        return similar_builds[:limit]

    except Exception as e:
        print(f"[ERROR] Failed to find similar builds: {e}", file=sys.stderr)
        return []


def analyze_user_context(characters: Optional[List[Dict]]) -> Dict:
    """사용자 캐릭터 정보 분석"""

    if not characters:
        return {
            "has_characters": False,
            "character_count": 0,
            "main_class": None
        }

    # 메인 캐릭터 선택 로직:
    # 1. 현재 리그 캐릭터 우선 (Standard 제외)
    # 2. 그 중 가장 높은 레벨
    # 3. 리그 캐릭터가 없으면 Standard에서 가장 높은 레벨
    league_chars = [c for c in characters if c.get('league') != 'Standard']

    if league_chars:
        main_char = max(league_chars, key=lambda c: c.get('level', 0))
    else:
        main_char = max(characters, key=lambda c: c.get('level', 0))

    return {
        "has_characters": True,
        "character_count": len(characters),
        "main_class": main_char.get('class'),
        "main_level": main_char.get('level')
    }


def get_popular_builds(league: str, limit: int = 5) -> List[Dict]:
    """
    POE.Ninja + YouTube 빌드 데이터베이스에서 인기 빌드 가져오기

    Returns:
        YouTube 빌드 목록 (POE.Ninja 데이터 기반 키워드)
    """

    # POE.Ninja + YouTube 통합 빌드 데이터베이스 로드
    build_data_file = os.path.join(
        os.path.dirname(__file__),
        "build_data",
        f"popular_builds_{league}.json"
    )

    if not os.path.exists(build_data_file):
        # Mock 데이터 반환 (테스트용)
        return [
            {
                "title": "Death's Oath Occultist",
                "channel": "Popular Build",
                "views": 0,
                "build_keyword": "Death's Oath",
                "source": "mock"
            },
            {
                "title": "Lightning Arrow Deadeye",
                "channel": "Popular Build",
                "views": 0,
                "build_keyword": "Lightning Arrow",
                "source": "mock"
            }
        ][:limit]

    with open(build_data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # YouTube 빌드 가져오기
    youtube_builds = data.get('youtube_builds', [])

    # views 기준으로 정렬 (인기도)
    builds_sorted = sorted(
        youtube_builds,
        key=lambda b: b.get('views', 0),
        reverse=True
    )

    # 빌드 정보 포맷 정리
    formatted_builds = []
    for build in builds_sorted[:limit]:
        formatted_builds.append({
            "title": build.get('title', 'Unknown Build'),
            "channel": build.get('channel', 'Unknown Channel'),
            "url": build.get('url', ''),
            "views": build.get('views', 0),
            "likes": build.get('likes', 0),
            "pob_links": build.get('pob_links', []),
            "build_keyword": build.get('build_keyword', ''),
            "published_at": build.get('published_at', ''),
            "source": "youtube"
        })

    return formatted_builds


def get_streamer_builds_cached(league: str, limit: int = 5) -> List[Dict]:
    """캐시된 스트리머 빌드 로드"""

    streamer_index = os.path.join(
        os.path.dirname(__file__),
        "build_data",
        "streamer_builds",
        f"index_{league}.json"
    )

    if not os.path.exists(streamer_index):
        return []

    with open(streamer_index, 'r', encoding='utf-8') as f:
        index = json.load(f)

    # 각 스트리머의 대표 빌드 하나씩 가져오기
    all_builds = []

    for streamer_name, info in index.get('streamers', {}).items():
        if not info['characters']:
            continue

        # 스트리머별 빌드 파일 로드
        streamer_file = os.path.join(
            os.path.dirname(__file__),
            "build_data",
            "streamer_builds",
            f"{streamer_name.replace(' ', '_')}_{league}.json"
        )

        if os.path.exists(streamer_file):
            with open(streamer_file, 'r', encoding='utf-8') as f:
                builds = json.load(f)
                if builds:
                    # 가장 높은 레벨의 빌드
                    top_build = max(builds, key=lambda b: b.get('level', 0))
                    top_build['streamer_name'] = streamer_name
                    all_builds.append(top_build)

    return all_builds[:limit]


def get_meta_builds(league: str, league_phase: str, limit: int = 5) -> List[Dict]:
    """현재 메타 빌드 가져오기"""

    # ladder cache에서 상위 랭커들의 빌드 가져오기
    ladder_cache_dir = os.path.join(
        os.path.dirname(__file__),
        "build_data",
        "ladder_cache"
    )

    if not os.path.exists(ladder_cache_dir):
        # Mock 데이터 반환 (테스트용)
        return [
            {
                "character_name": "ChaosKiller",
                "class": "Witch",
                "ascendancy_class": "Occultist",
                "rank": 5,
                "level": 98
            },
            {
                "character_name": "FastClearSpeed",
                "class": "Ranger",
                "ascendancy_class": "Deadeye",
                "rank": 12,
                "level": 97
            }
        ][:limit]

    # 최신 캐시 파일 찾기
    cache_files = [
        f for f in os.listdir(ladder_cache_dir)
        if f.endswith('.json') and league.lower() in f.lower()
    ]

    if not cache_files:
        return []

    # 가장 최근 파일
    latest_cache = max(
        cache_files,
        key=lambda f: os.path.getmtime(os.path.join(ladder_cache_dir, f))
    )

    cache_file = os.path.join(ladder_cache_dir, latest_cache)

    with open(cache_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    builds = data.get('builds', [])

    # 랭크 순 정렬
    builds_sorted = sorted(builds, key=lambda b: b.get('rank', 9999))

    return builds_sorted[:limit]


def get_preseason_practice_builds(league: str, limit: int = 5) -> List[Dict]:
    """시즌 시작 전 스트리머들의 연습 빌드"""

    # YouTube에서 "3.27 league start" 같은 키워드로 검색
    try:
        from youtube_build_collector import search_youtube_builds

        league_version = league.replace("Keepers", "3.27")  # 리그 버전 매핑

        preseason_keywords = [
            f"{league_version} league start",
            f"{league_version} league starter",
            f"{league_version} day 1 build"
        ]

        all_builds = []

        for keyword in preseason_keywords:
            try:
                builds = search_youtube_builds(
                    keyword=keyword,
                    league_version=league_version,
                    max_results=3
                )
                all_builds.extend(builds)

                if len(all_builds) >= limit:
                    break
            except:
                continue

        return all_builds[:limit]
    except ImportError:
        return []


def get_similar_class_builds(league: str, user_class: str, limit: int = 5) -> List[Dict]:
    """
    사용자의 메인 클래스와 유사한 빌드 추천

    Args:
        league: 리그 이름
        user_class: 사용자의 메인 캐릭터 클래스 (예: "Necromancer", "Occultist")
        limit: 최대 빌드 수

    Returns:
        유사한 클래스의 인기 빌드 목록
    """

    # ladder cache에서 같은 클래스 빌드 찾기
    ladder_cache_dir = os.path.join(
        os.path.dirname(__file__),
        "build_data",
        "ladder_cache"
    )

    if not os.path.exists(ladder_cache_dir):
        # Mock 데이터 반환 (사용자 클래스 기반)
        return [
            {
                "character_name": f"{user_class}_Build_1",
                "class": "Witch",
                "ascendancy_class": user_class,
                "rank": 15,
                "level": 96,
                "personalized": True
            },
            {
                "character_name": f"{user_class}_Build_2",
                "class": "Witch",
                "ascendancy_class": user_class,
                "rank": 28,
                "level": 95,
                "personalized": True
            }
        ][:limit]

    # 최신 캐시 파일 찾기
    cache_files = [
        f for f in os.listdir(ladder_cache_dir)
        if f.endswith('.json') and league.lower() in f.lower()
    ]

    if not cache_files:
        return []

    # 가장 최근 파일
    latest_cache = max(
        cache_files,
        key=lambda f: os.path.getmtime(os.path.join(ladder_cache_dir, f))
    )

    cache_file = os.path.join(ladder_cache_dir, latest_cache)

    with open(cache_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    builds = data.get('builds', [])

    # 같은 ascendancy class 필터링
    similar_builds = [
        b for b in builds
        if b.get('ascendancy_class', '').lower() == user_class.lower()
    ]

    # 랭크 순 정렬
    similar_builds_sorted = sorted(similar_builds, key=lambda b: b.get('rank', 9999))

    # personalized 플래그 추가
    for build in similar_builds_sorted:
        build['personalized'] = True

    return similar_builds_sorted[:limit]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Auto Recommendation Engine')
    parser.add_argument('--league', type=str, default=None, help='League name (auto-detect if not specified)')
    parser.add_argument('--json-output', action='store_true', help='Output JSON to stdout')
    parser.add_argument('--no-streamers', action='store_true', help='Disable streamer builds')
    parser.add_argument('--max', type=int, default=10, help='Max builds per category')
    parser.add_argument('--include-user-build-analysis', action='store_true', help='Include user build analysis in output')
    parser.add_argument('--reference-pob', type=str, default=None, help='Reference POB URL to find similar builds')
    parser.add_argument('--streamer', type=str, default=None, help='Streamer/YouTuber name to filter builds')

    args = parser.parse_args()

    # 맞춤 추천 모드 확인
    if args.reference_pob or args.streamer:
        # 맞춤 추천 모드
        result = get_personalized_recommendations(
            league=args.league,
            reference_pob=args.reference_pob,
            streamer_name=args.streamer,
            max_builds=args.max
        )
    else:
        # 일반 자동 추천
        result = get_auto_recommendations(
            league=args.league,
            user_characters=None,  # OAuth 연동 시 여기에 캐릭터 데이터 전달
            max_builds=args.max,
            include_streamers=not args.no_streamers
        )

    if args.json_output:
        # JSON 출력 (C# 통합용)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 일반 출력
        print(file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        print("RECOMMENDATIONS", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        print(file=sys.stderr)

        for rec in result['recommendations']:
            print(f"{rec['title']}", file=sys.stderr)
            print(f"  {rec['subtitle']}", file=sys.stderr)
            print(file=sys.stderr)

            for i, build in enumerate(rec['builds'], 1):
                # 빌드 이름 추출 (소스에 따라 다름)
                name = (
                    build.get('character_name') or
                    build.get('title') or
                    build.get('name') or
                    f"{build.get('class')} {build.get('ascendancy_class', '')}"
                )

                print(f"  {i}. {name}", file=sys.stderr)

                # 추가 정보
                if 'streamer_name' in build:
                    print(f"     Streamer: {build['streamer_name']}", file=sys.stderr)
                if 'rank' in build:
                    print(f"     Ladder Rank: #{build['rank']}", file=sys.stderr)
                if 'count' in build:
                    print(f"     Popularity: {build['count']} players", file=sys.stderr)
                if 'level' in build:
                    print(f"     Level: {build['level']}", file=sys.stderr)

            print(file=sys.stderr)

        print("=" * 80, file=sys.stderr)
        print(f"Total Recommendations: {result['total_builds']}", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
