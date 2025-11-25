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


def apply_build_filters(
    recommendations: List[Dict],
    char_class: Optional[str] = None,
    sort_order: str = "views",
    budget: Optional[int] = None
) -> List[Dict]:
    """
    빌드 추천 결과에 필터 적용

    Args:
        recommendations: 추천 카테고리 목록
        char_class: 클래스 필터 (예: "Witch", "Shadow")
        sort_order: 정렬 기준 ("views", "date", "likes", "price")
        budget: 최대 예산 (chaos)

    Returns:
        필터링된 추천 목록
    """
    filtered_recommendations = []

    # 클래스 → 어센던시 매핑
    CLASS_ASCENDANCIES = {
        "witch": ["occultist", "necromancer", "elementalist"],
        "shadow": ["assassin", "saboteur", "trickster"],
        "ranger": ["deadeye", "raider", "pathfinder"],
        "duelist": ["slayer", "gladiator", "champion"],
        "marauder": ["juggernaut", "berserker", "chieftain"],
        "templar": ["inquisitor", "hierophant", "guardian"],
        "scion": ["ascendant"]
    }

    for category in recommendations:
        builds = category.get("builds", [])

        # 클래스 필터
        if char_class:
            class_lower = char_class.lower()
            # 어센던시 목록 생성
            ascendancies = CLASS_ASCENDANCIES.get(class_lower, [class_lower])

            filtered_builds = []
            for b in builds:
                # 기존 필드 체크
                match = (
                    class_lower in (b.get("class", "") or "").lower()
                    or class_lower in (b.get("ascendancy", "") or "").lower()
                    or class_lower in (b.get("ascendancy_class", "") or "").lower()
                )

                # title에서 클래스/어센던시 찾기
                title = (b.get("title", "") or "").lower()
                if not match:
                    for asc in ascendancies:
                        if asc in title:
                            match = True
                            break

                # build_keyword에서도 찾기
                keyword = (b.get("build_keyword", "") or "").lower()
                if not match and keyword:
                    for asc in ascendancies:
                        if asc in keyword:
                            match = True
                            break

                if match:
                    filtered_builds.append(b)

            builds = filtered_builds

        # 예산 필터 (estimated_cost 또는 budget 필드)
        if budget:
            filtered_builds = []
            for b in builds:
                cost = b.get("estimated_cost") or b.get("budget") or b.get("price")
                if cost is None:
                    # 가격 정보 없으면 포함 (기본적으로)
                    filtered_builds.append(b)
                elif cost <= budget:
                    filtered_builds.append(b)
            builds = filtered_builds

        # 정렬
        if sort_order == "views":
            builds = sorted(builds, key=lambda b: b.get("views", 0) or 0, reverse=True)
        elif sort_order == "date":
            builds = sorted(builds, key=lambda b: b.get("published_at", "") or "", reverse=True)
        elif sort_order == "likes":
            builds = sorted(builds, key=lambda b: b.get("likes", 0) or 0, reverse=True)
        elif sort_order == "price":
            builds = sorted(builds, key=lambda b: (b.get("estimated_cost") or b.get("budget") or 0))

        # 필터링된 결과가 있으면 추가
        if builds:
            filtered_recommendations.append({
                **category,
                "builds": builds,
                "count": len(builds)
            })

    return filtered_recommendations


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
    include_user_build_analysis: bool = True,
    char_class: Optional[str] = None,
    sort_order: str = "views",
    budget: Optional[int] = None
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

    # 필터 적용
    if char_class or budget or sort_order != "views":
        print(f"[FILTER] Applying filters: class={char_class}, budget={budget}, sort={sort_order}", file=sys.stderr)
        recommendations = apply_build_filters(
            recommendations,
            char_class=char_class,
            sort_order=sort_order,
            budget=budget
        )

    # Divine/Chaos 환율 및 예산 구간 가져오기
    divine_rate = 150.0  # 기본값
    budget_tiers = []
    try:
        from poe_ninja_api import POENinjaAPI
        ninja_api = POENinjaAPI(league=league)
        divine_rate = ninja_api.get_divine_chaos_rate()
        budget_tiers = ninja_api.get_budget_tiers(league_phase)
        print(f"[INFO] Divine rate: {divine_rate:.1f}c", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] Failed to get Divine rate: {e}", file=sys.stderr)
        # 기본 예산 구간 사용
        budget_tiers = [
            {"label": "전체", "chaos_value": None},
            {"label": "~50c", "chaos_value": 50},
            {"label": "~100c", "chaos_value": 100},
            {"label": "~1 div", "chaos_value": int(divine_rate)},
            {"label": "~3 div", "chaos_value": int(divine_rate * 3)},
            {"label": "~5 div", "chaos_value": int(divine_rate * 5)},
        ]

    return {
        "league": league,
        "league_phase": league_phase,
        "user_build": user_build_analysis,
        "recommendations": recommendations,
        "user_context": user_context,
        "total_builds": sum(r['count'] for r in recommendations),
        "generated_at": datetime.now().isoformat(),
        "filters": {
            "class": char_class,
            "sort": sort_order,
            "budget": budget
        },
        "currency": {
            "divine_chaos_rate": divine_rate,
            "budget_tiers": budget_tiers
        }
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
    """스트리머 이름 또는 스킬/아이템으로 빌드 검색"""

    # =============================================================================
    # STREAMER SELECTION CRITERIA (스트리머 선정 기준)
    # =============================================================================
    #
    # Tier 1 (핵심 스트리머):
    #   - 구독자: 50,000+
    #   - 최근 3개월 내 POE 영상: 30개+
    #   - 평균 조회수: 5,000+
    #   - 예: Zizaran, Mathil, 게이머 비누
    #
    # Tier 2 (활성 스트리머):
    #   - 구독자: 10,000+
    #   - 최근 2개월 내 POE 영상: 15개+
    #   - 평균 조회수: 2,000+
    #   - 예: GhazzyTV, POEASY, 엠피스
    #
    # Tier 3 (커뮤니티 스트리머):
    #   - 구독자: 1,000+
    #   - 최근 1개월 내 POE 영상: 5개+
    #   - 평균 조회수: 500+
    #   - 예: 커뮤니티 추천
    #
    # 자동 제외 기준:
    #   - 90일 이상 POE 영상 없음
    #   - 구독자 1,000 미만
    #   - POE 콘텐츠 비중 10% 미만
    #   - 리그 시작 후 2주 내 영상 0개
    #
    # 참고: 활발한 스트리머 업로드 패턴
    #   - Zizaran: 리그 시작 시 일 3-5개, 평상시 주 5-10개
    #   - Mathil: 리그 기간 주 10-15개
    #   - GhazzyTV: 주 5-7개 (가이드 위주)
    #   - 한국 유튜버: 주 2-5개 (상대적으로 적음)
    #
    # 분기별 리뷰: 매 분기 첫째 주 리뷰 (1월, 4월, 7월, 10월)
    # =============================================================================

    STREAMER_CRITERIA = {
        'tier_1': {
            'min_subscribers': 50000,
            'min_videos_90d': 30,
            'min_avg_views': 5000,
            'description': '핵심 스트리머 (Zizaran, Mathil, 게이머 비누)'
        },
        'tier_2': {
            'min_subscribers': 10000,
            'min_videos_60d': 15,
            'min_avg_views': 2000,
            'description': '활성 스트리머 (GhazzyTV, POEASY, 엠피스)'
        },
        'tier_3': {
            'min_subscribers': 1000,
            'min_videos_30d': 5,
            'min_avg_views': 500,
            'description': '커뮤니티 스트리머'
        }
    }

    # 유명 스트리머 이름 -> POE 계정 매핑
    STREAMER_ACCOUNTS = {
        'pohx': 'Pohx',
        'zizaran': 'Zizaran',
        'mathil': 'Mathil',
        'empyrean': 'Empyrian',
        'ghazzy': 'GhazzyTV',
        'subtractem': 'Subtractem',
        'jungroan': 'jungroan',
        'ruetoo': 'RueToo',
        'palsteron': 'Palsteron',
        'goratha': 'Goratha',
        'path of matth': 'pathofmatth',
        'tytykiller': 'tytykiller',
        'steelmage': 'Steelmage',
        'darkee': 'Darkee',
        'lightee': 'Lightee7',
        'ben': 'Ben_',
        'imexile': 'imexile',
    }

    # 유명 스트리머 이름 -> YouTube 채널명 매핑
    # 마지막 리뷰: 2025-11-21 (데이터 수집 기반)
    STREAMER_YOUTUBE_CHANNELS = {
        # =====================================================================
        # TIER 1: 핵심 스트리머 (50K+ 구독자, 3개월 30+ 영상, 5K+ 조회수)
        # 실제 데이터 기반 (2025-11-21 수집)
        # =====================================================================
        'zizaran': 'Zizaran',           # 325K subs, 72 videos, 49K views
        'pohx': 'Pohx',                 # 138K subs, 62 videos, 18K views, RF 전문
        'ghazzy': 'GhazzyTV',           # 145K subs, 67 videos, 44K views, 미니언 전문
        'palsteron': 'Palsteron',       # 95K subs, 57 videos, 54K views, 리그스타터 전문
        'jungroan': 'jungroan',         # 96K subs, 30 videos, 43K views
        'empyrean': 'Empyrean',         # 192K subs, 67 videos, 52K views, 그룹 파밍
        'fastaf': 'FastAF',             # 100K subs, 41 videos, 10K views
        'lolcohol': 'Lolcohol',         # 63K subs, 97 videos, 21K views
        'fubgun': 'Fubgun',             # 121K subs, 103 videos, 56K views
        'sirgog': 'sirgog',             # 55K subs, 56 videos, 16K views
        'ds_lily': 'ds lily',           # 72K subs, 83 videos, 16K views
        'lily': 'ds lily',

        # =====================================================================
        # TIER 2: 활성 스트리머 (10K+ 구독자, 2개월 15+ 영상, 2K+ 조회수)
        # =====================================================================
        'mathil': 'Mathilification',    # 186K subs, 20 videos, 31K views
        'crouching_tuna': 'Crouching_Tuna',  # 55K subs, 22 videos, 19K views
        'ruetoo': 'Ruetoo',             # 42K subs, 24 videos, 51K views
        'steelmage': 'Steelmage',       # 49K subs, 21 videos, 26K views, 레이스 전문
        'spicysushi': 'Spicysushi PoE', # 53K subs, 20 videos, 106K views
        'havoc': 'havoc616 VODS',       # 21K subs, 21 videos, 17K views, 레이스 전문
        'havoc616': 'havoc616 VODS',
        'alkaizer': 'AlkaizerSenpai',   # 69K subs, 29 videos, 29K views
        'waggle': 'Dsfarblarwaggle',    # 17K subs, 21 videos, 6K views
        'balormage': 'BalorMage',       # 30K subs, 19 videos, 19K views
        'balor mage': 'BalorMage',
        'donthecrown': 'DonTheCrown',   # 55K subs, 29 videos, 4K views
        'don the crown': 'DonTheCrown',

        # =====================================================================
        # TIER 3: 커뮤니티 스트리머 (1K+ 구독자, 1개월 5+ 영상, 500+ 조회수)
        # 또는 높은 조회수/구독자지만 영상이 적은 경우
        # =====================================================================
        'goratha': 'Goratha',           # 41K subs, 14 videos, 46K views
        'imexile': 'Imexile',           # 18K subs, 10 videos, 47K views
        'cutedog': 'CuteDog_',          # 45K subs, 12 videos, 9K views
        'raizqt': 'RaizQT',             # 57K subs, 10 videos, 9K views
        'nugiyen': 'nugiyen',           # 19K subs, 6 videos, 5K views
        'tytykiller': 'Tytykiller',     # 36K subs, 5 videos, 25K views, 레이스 전문
        'quin69': 'Quin69TV',           # 93K subs, 14 videos, 34K views
        'kay gaming': 'Kay Gaming',     # 56K subs, 11 videos, 5K views
        'kay': 'Kay Gaming',

        # Twitch 전용 (YouTube 비활성) - 참고용
        # 'darkee', 'lightee', 'octavian0', 'ben' - Twitch에서만 활동

        # =====================================================================
        # 한국인 스트리머/유튜버 (실제 데이터 기반 2025-11-21)
        # =====================================================================

        # TIER 1: 핵심 (50K+ 구독자, 30+ 영상)
        '게이머비누': '게이머비누Gamerbinu',  # 79K subs, 70 videos, 27K views
        '게이머 비누': '게이머비누Gamerbinu',
        'gamer binu': '게이머비누Gamerbinu',
        '비누': '게이머비누Gamerbinu',

        '포이지': 'PoEasy 쉽고 편한 게임 채널',  # 83K subs, 46 videos, 18K views
        'poeasy': 'PoEasy 쉽고 편한 게임 채널',

        # TIER 2: 활성 (10K+ 구독자, 15+ 영상)
        '추봉이': '추봉이',              # 36K subs, 33 videos, 12K views
        'chubong': '추봉이',

        '뀨튜브': 'KKYU TUBE',           # 33K subs, 42 videos, 12K views
        'ggyu': 'KKYU TUBE',

        '로나': '로나의 게임 채널 Ronatube',  # 23K subs, 34 videos, 4K views
        '로나의 게임채널': '로나의 게임 채널 Ronatube',

        '스테tv': '스테TV',              # 24K subs, 55 videos, 6K views
        '스테': '스테TV',
        'ste': '스테TV',

        '까까모리': '까까모리',          # 22K subs, 159 videos, 3K views
        'kkakkamori': '까까모리',

        '개굴덱': '개굴덱',              # 35K subs, 41 videos, 41K views (Tier 2로 승격)
        'gaeguldek': '개굴덱',

        # TIER 3: 커뮤니티 (활동 중이지만 영상 적음)
        '엠피스': '엠피스 AMPHIS',       # 62K subs, 11 videos, 27K views
        'mpis': '엠피스 AMPHIS',

        '혜미': '혜미 Ham',              # 20K subs, 6 videos, 8K views
        '혜미ham': '혜미 Ham',
        'hyemi': '혜미 Ham',

        '스탠다드qk': '스텐다드StandardQK',  # 14K subs, 13 videos, 5K views
        '스탠다드': '스텐다드StandardQK',
        'standardqk': '스텐다드StandardQK',
    }

    # 스킬/아이템 키워드 매핑 (POE 커뮤니티 약어 포함)
    SKILL_KEYWORDS = {
        # RF / Fire DoT
        'rf': 'Righteous Fire',
        'righteous fire': 'Righteous Fire',
        'death aura': 'Death Aura',
        'deaths oath': 'Death Aura',
        "death's oath": 'Death Aura',

        # Melee
        'boneshatter': 'Boneshatter',
        'cyclone': 'Cyclone',
        'eq': 'Earthquake',
        'earthquake': 'Earthquake',
        'ls': 'Lightning Strike',
        'lightning strike': 'Lightning Strike',
        'gh': 'Glacial Hammer',
        'glacial hammer': 'Glacial Hammer',
        'flicker': 'Flicker Strike',
        'flicker strike': 'Flicker Strike',
        'shield crush': 'Shield Crush',
        'spectral helix': 'Spectral Helix',
        'sst': 'Spectral Shield Throw',
        'spectral shield throw': 'Spectral Shield Throw',
        'reave': 'Reave',
        'lacerate': 'Lacerate',
        'blade flurry': 'Blade Flurry',

        # Bow
        'ts': 'Tornado Shot',
        'tornado shot': 'Tornado Shot',
        'la': 'Lightning Arrow',
        'lightning arrow': 'Lightning Arrow',
        'ea': 'Explosive Arrow',
        'explosive arrow': 'Explosive Arrow',
        'ca': 'Caustic Arrow',
        'caustic arrow': 'Caustic Arrow',
        'ice shot': 'Ice Shot',
        'roa': 'Rain of Arrows',
        'rain of arrows': 'Rain of Arrows',
        'scourge arrow': 'Scourge Arrow',
        'ballista': 'Ballista Totem',

        # Spell - Cold
        'fp': 'Freezing Pulse',
        'freezing pulse': 'Freezing Pulse',
        'ice nova': 'Ice Nova',
        'ice spear': 'Ice Spear',
        'eow': 'Eye of Winter',
        'eye of winter': 'Eye of Winter',
        'creeping frost': 'Creeping Frost',
        'vortex': 'Vortex',
        'cold snap': 'Cold Snap',

        # Spell - Lightning
        'spark': 'Spark',
        'arc': 'Arc',
        'oos': 'Orb of Storms',
        'orb of storms': 'Orb of Storms',
        'storm call': 'Storm Call',
        'ball lightning': 'Ball Lightning',
        'bl': 'Ball Lightning',
        'crackling lance': 'Crackling Lance',

        # Spell - Fire
        'fb': 'Flameblast',
        'flameblast': 'Flameblast',
        'fireball': 'Fireball',
        'dd': 'Detonate Dead',
        'detonate dead': 'Detonate Dead',
        'cremation': 'Cremation',
        'incinerate': 'Incinerate',

        # Spell - Chaos/Physical
        'ed': 'Essence Drain',
        'essence drain': 'Essence Drain',
        'contagion': 'Contagion',
        'bane': 'Bane',
        'ek': 'Ethereal Knives',
        'ethereal knives': 'Ethereal Knives',
        'bv': 'Blade Vortex',
        'blade vortex': 'Blade Vortice',
        'bb': 'Blade Blast',
        'blade blast': 'Blade Blast',
        'bf': 'Bladefall',
        'bladefall': 'Bladefall',
        'fr': 'Forbidden Rite',
        'forbidden rite': 'Forbidden Rite',
        'cf': 'Corrupting Fever',
        'corrupting fever': 'Corrupting Fever',
        'pc': 'Poisonous Concoction',
        'poisonous concoction': 'Poisonous Concoction',

        # Minions
        'minion': None,  # 특수 검색
        'spectre': 'Raise Spectre',
        'raise spectre': 'Raise Spectre',
        'zombie': 'Raise Zombie',
        'raise zombie': 'Raise Zombie',
        'skeleton': 'Summon Skeletons',
        'summon skeletons': 'Summon Skeletons',
        'srs': 'Summon Raging Spirit',
        'summon raging spirit': 'Summon Raging Spirit',
        'ag': 'Animate Guardian',
        'animate guardian': 'Animate Guardian',
        'aw': 'Animate Weapon',
        'animate weapon': 'Animate Weapon',
        'golem': 'Summon Stone Golem',
        'carrion golem': 'Summon Carrion Golem',
        'absolution': 'Absolution',

        # Traps/Mines
        'seismic trap': 'Seismic Trap',
        'exsanguinate': 'Exsanguinate',
        'lightning trap': 'Lightning Trap',
        'arc mine': 'Arc',
        'icicle mine': 'Icicle Mine',
        'pyroclast mine': 'Pyroclast Mine',

        # Totems
        'hft': 'Holy Flame Totem',
        'holy flame totem': 'Holy Flame Totem',
        'ancestral warchief': 'Ancestral Warchief',
        'earthbreaker': 'Earthbreaker',

        # Other
        'aa': 'Arctic Armour',
        'arctic armour': 'Arctic Armour',
        'ms': 'Molten Shell',
        'molten shell': 'Molten Shell',
        'pb': 'Petrified Blood',
        'petrified blood': 'Petrified Blood',
        'coc': 'Cast On Critical Strike',
        'cast on crit': 'Cast On Critical Strike',
        'cwdt': 'Cast when Damage Taken',
        'discharge': 'Discharge',
        'flamewall': 'Flame Wall',
        'herald': None,  # 특수 검색
        'aura': None,  # 특수 검색
    }

    # 아이템 키워드 매핑
    ITEM_KEYWORDS = {
        "death's oath": "Death's Oath",
        'deaths oath': "Death's Oath",
        'mageblood': 'Mageblood',
        'headhunter': 'Headhunter',
        'hh': 'Headhunter',
        'ashes': 'Ashes of the Stars',
        'nimis': 'Nimis',
        'aegis aurora': 'Aegis Aurora',
        'aegis': 'Aegis Aurora',
        'melding': 'Melding of the Flesh',
    }

    search_term = streamer_name.lower().strip()
    filtered = []

    # 한국어 번역 데이터 로드
    translations = load_korean_translations()

    # 0. 한국어 검색어를 영어로 변환
    if translations and search_term in [kr.lower() for kr in translations.get('skills_kr', {}).keys()]:
        # 한국어 스킬명 찾기
        for kr_name, en_name in translations.get('skills_kr', {}).items():
            if kr_name.lower() == search_term:
                search_term = en_name.lower()
                print(f"[INFO] Korean to English: {kr_name} -> {en_name}", file=sys.stderr)
                break

    # 1. 스트리머 이름 -> YouTube 채널 검색 (우선순위 최상위)
    if search_term in STREAMER_YOUTUBE_CHANNELS:
        channel_name = STREAMER_YOUTUBE_CHANNELS[search_term]
        print(f"[INFO] Searching YouTube for streamer: {channel_name}", file=sys.stderr)

        try:
            from youtube_build_collector import search_youtube_builds

            # 리그 버전 추출 (Keepers -> 3.27)
            league_version = "3.27"  # 기본값
            if "keepers" in league.lower():
                league_version = "3.27"

            # YouTube에서 해당 채널의 빌드 검색
            # POB 링크 없어도 결과 반환하도록 수정
            from googleapiclient.discovery import build as youtube_build
            import os

            api_key = os.environ.get('YOUTUBE_API_KEY')
            if api_key:
                try:
                    youtube = youtube_build('youtube', 'v3', developerKey=api_key)

                    # 채널명으로 직접 검색
                    # 한국어 채널인지 확인
                    is_korean = any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in channel_name)

                    if is_korean:
                        # 한국어 채널: POE 또는 패스오브엑자일 사용
                        search_query = f"{channel_name} POE 빌드"
                        relevance_lang = 'ko'
                    else:
                        search_query = f"{channel_name} poe {league_version} build"
                        relevance_lang = 'en'

                    print(f"[INFO] Searching YouTube: {search_query}", file=sys.stderr)

                    # 최근 영상만 검색
                    from datetime import datetime, timedelta
                    # 한국어 채널은 더 넓은 범위 (6개월), 영어는 2개월
                    days_back = 180 if is_korean else 60
                    published_after = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%dT00:00:00Z')

                    search_response = youtube.search().list(
                        q=search_query,
                        part='id,snippet',
                        maxResults=limit * 2,  # 필터링 후 줄어들 수 있어서 더 많이 검색
                        type='video',
                        order='date',  # 최신순으로 정렬
                        publishedAfter=published_after,  # 최근 2개월 영상만
                        relevanceLanguage=relevance_lang
                    ).execute()

                    for item in search_response.get('items', []):
                        video_id = item['id']['videoId']
                        snippet = item['snippet']

                        # 비디오 상세 정보 가져오기
                        video_response = youtube.videos().list(
                            part='snippet,statistics',
                            id=video_id
                        ).execute()

                        if not video_response.get('items'):
                            continue

                        video_data = video_response['items'][0]
                        description = video_data['snippet']['description']
                        statistics = video_data['statistics']

                        # POB 링크 추출 (없어도 OK)
                        from youtube_build_collector import extract_pob_links
                        pob_links = extract_pob_links(description)

                        # 썸네일 URL 추출
                        thumbnails = video_data['snippet'].get('thumbnails', {})
                        thumbnail_url = (
                            thumbnails.get('medium', {}).get('url') or
                            thumbnails.get('default', {}).get('url') or
                            f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                        )

                        # 채널명이 일치하는 영상을 우선적으로 추가
                        build_channel_lower = snippet['channelTitle'].lower()
                        channel_name_lower = channel_name.lower()

                        is_exact_channel = (
                            channel_name_lower in build_channel_lower or
                            build_channel_lower in channel_name_lower
                        )

                        build_data = {
                            'title': snippet['title'],
                            'channel': snippet['channelTitle'],
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'thumbnail': thumbnail_url,
                            'views': int(statistics.get('viewCount', 0)),
                            'likes': int(statistics.get('likeCount', 0)),
                            'pob_links': pob_links,
                            'published_at': snippet['publishedAt'],
                            'source': 'youtube',
                            'streamer_name': streamer_name,
                            'is_exact_channel': is_exact_channel
                        }

                        if is_exact_channel:
                            # 정확한 채널은 앞에 추가
                            filtered.insert(0, build_data)
                        else:
                            filtered.append(build_data)

                    # limit 초과 시 정확한 채널 우선 유지
                    if len(filtered) > limit:
                        # is_exact_channel True인 것 우선 정렬
                        filtered.sort(key=lambda x: (not x.get('is_exact_channel', False), -x.get('views', 0)))
                        filtered = filtered[:limit]

                    if filtered:
                        print(f"[OK] Found {len(filtered)} YouTube videos for {channel_name}", file=sys.stderr)
                        return filtered

                except Exception as e:
                    print(f"[WARN] Direct YouTube search failed: {e}", file=sys.stderr)

            # API 키 없거나 직접 검색 실패시 기존 search_youtube_builds 사용
            youtube_builds = search_youtube_builds(
                keyword=channel_name,
                league_version=league_version,
                max_results=limit,
                use_cache=True
            )

            for build in youtube_builds:
                # 채널명이 일치하는지 확인 (대소문자 무시)
                build_channel = build.get('channel', '').lower()
                if channel_name.lower() in build_channel or build_channel in channel_name.lower():
                    filtered.append({
                        'title': build.get('title', 'Unknown'),
                        'channel': build.get('channel', ''),
                        'url': build.get('url', ''),
                        'thumbnail': build.get('thumbnail', ''),
                        'views': build.get('views', 0),
                        'likes': build.get('likes', 0),
                        'pob_links': build.get('pob_links', []),
                        'published_at': build.get('published_at', ''),
                        'source': 'youtube',
                        'streamer_name': streamer_name
                    })
                else:
                    # 채널이 다르더라도 검색 결과에 포함 (관련 빌드)
                    filtered.append({
                        'title': build.get('title', 'Unknown'),
                        'channel': build.get('channel', ''),
                        'url': build.get('url', ''),
                        'thumbnail': build.get('thumbnail', ''),
                        'views': build.get('views', 0),
                        'likes': build.get('likes', 0),
                        'pob_links': build.get('pob_links', []),
                        'published_at': build.get('published_at', ''),
                        'source': 'youtube',
                        'streamer_name': streamer_name
                    })

                if len(filtered) >= limit:
                    break

            if filtered:
                print(f"[OK] Found {len(filtered)} YouTube builds for {channel_name}", file=sys.stderr)
                return filtered

        except Exception as e:
            print(f"[WARN] YouTube search failed: {e}", file=sys.stderr)

    # 2. poe.ninja 계정 검색 (YouTube 결과 없을 때 fallback)
    if not filtered and search_term in STREAMER_ACCOUNTS:
        account_name = STREAMER_ACCOUNTS[search_term]
        print(f"[INFO] Searching for streamer account on poe.ninja: {account_name}", file=sys.stderr)
        # poe.ninja에서 해당 계정의 빌드 찾기
        try:
            from poe_ninja_build_scraper import fetch_poe_ninja_builds
            builds = fetch_poe_ninja_builds(league=league, limit=100)
            for build in builds:
                acc = build.get('account', {}).get('name', '').lower()
                if account_name.lower() in acc:
                    filtered.append({
                        'character_name': build.get('name', 'Unknown'),
                        'class': build.get('class', 'Unknown'),
                        'level': build.get('level', 100),
                        'main_skill': build.get('mainSkill', 'Unknown'),
                        'account_name': build.get('account', {}).get('name', ''),
                        'depth': build.get('depth-solo', 0),
                        'pob_code': '',
                        'source': 'poe.ninja',
                        'streamer_name': streamer_name
                    })
                    if len(filtered) >= limit:
                        break
        except Exception as e:
            print(f"[ERROR] Failed to search streamer on poe.ninja: {e}", file=sys.stderr)

    # 3. 스킬 키워드 검색
    if not filtered and search_term in SKILL_KEYWORDS:
        skill_name = SKILL_KEYWORDS[search_term]
        if skill_name:
            print(f"[INFO] Searching for skill: {skill_name}", file=sys.stderr)
            try:
                from poe_ninja_build_scraper import fetch_poe_ninja_builds
                builds = fetch_poe_ninja_builds(league=league, skill=skill_name, limit=limit)
                for build in builds:
                    filtered.append({
                        'character_name': build.get('name', 'Unknown'),
                        'class': build.get('class', 'Unknown'),
                        'level': build.get('level', 100),
                        'main_skill': skill_name,
                        'account_name': build.get('account', {}).get('name', ''),
                        'depth': build.get('depth-solo', 0),
                        'pob_code': '',
                        'source': 'poe.ninja',
                    })
            except Exception as e:
                print(f"[ERROR] Failed to search skill: {e}", file=sys.stderr)

    # 4. 아이템 키워드 검색
    if not filtered and search_term in ITEM_KEYWORDS:
        item_name = ITEM_KEYWORDS[search_term]
        print(f"[INFO] Searching for item: {item_name}", file=sys.stderr)
        try:
            from poe_ninja_build_scraper import fetch_poe_ninja_builds
            builds = fetch_poe_ninja_builds(league=league, item=item_name, limit=limit)
            for build in builds:
                filtered.append({
                    'character_name': build.get('name', 'Unknown'),
                    'class': build.get('class', 'Unknown'),
                    'level': build.get('level', 100),
                    'main_skill': build.get('mainSkill', 'Unknown'),
                    'account_name': build.get('account', {}).get('name', ''),
                    'depth': build.get('depth-solo', 0),
                    'pob_code': '',
                    'source': 'poe.ninja',
                    'item_filter': item_name
                })
        except Exception as e:
            print(f"[ERROR] Failed to search item: {e}", file=sys.stderr)

    # 5. 직접 스킬/아이템 이름 검색 (키워드 매핑에 없는 경우)
    if not filtered:
        print(f"[INFO] Direct search for: {search_term}", file=sys.stderr)
        try:
            from poe_ninja_build_scraper import fetch_poe_ninja_builds
            # 스킬로 먼저 시도
            builds = fetch_poe_ninja_builds(league=league, skill=streamer_name, limit=limit)
            if not builds:
                # 아이템으로 시도
                builds = fetch_poe_ninja_builds(league=league, item=streamer_name, limit=limit)

            for build in builds:
                filtered.append({
                    'character_name': build.get('name', 'Unknown'),
                    'class': build.get('class', 'Unknown'),
                    'level': build.get('level', 100),
                    'main_skill': build.get('mainSkill', 'Unknown'),
                    'account_name': build.get('account', {}).get('name', ''),
                    'depth': build.get('depth-solo', 0),
                    'pob_code': '',
                    'source': 'poe.ninja',
                })
        except Exception as e:
            print(f"[ERROR] Failed direct search: {e}", file=sys.stderr)

    # 6. 기존 캐시 검색 (fallback)
    if not filtered:
        streamer_builds = get_streamer_builds_cached(league, limit=50)
        for build in streamer_builds:
            streamer = build.get('streamer_name', '').lower()
            channel = build.get('channel', '').lower()
            if search_term in streamer or search_term in channel:
                filtered.append(build)
                if len(filtered) >= limit:
                    break

    return filtered


def find_similar_builds_to_pob(pob_url: str, league: str, limit: int = 10) -> List[Dict]:
    """POB와 유사한 빌드 찾기"""

    try:
        # POB 분석
        from pob_parser import get_pob_code_from_url, decode_pob_code, parse_pob_xml

        print(f"[INFO] Analyzing reference POB...", file=sys.stderr)

        # POB 코드 가져오기 (file://, pobb.in, pastebin 지원)
        pob_code = get_pob_code_from_url(pob_url)
        if not pob_code:
            print(f"[ERROR] Could not fetch POB code from URL", file=sys.stderr)
            return []

        # XML 직접 로드인 경우 (로컬 파일에서 읽음)
        if pob_code.startswith("__XML_DIRECT__"):
            pob_xml = pob_code[14:]  # __XML_DIRECT__ 제거
            print(f"[INFO] Loaded POB XML from local file", file=sys.stderr)
        else:
            # XML 디코딩
            pob_xml = decode_pob_code(pob_code)

        if not pob_xml:
            print(f"[ERROR] Could not decode POB", file=sys.stderr)
            return []

        # POB 파싱
        build_data = parse_pob_xml(pob_xml, pob_url)
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


def load_korean_translations() -> Dict:
    """한국어 번역 데이터 로드

    우선순위:
    1. merged_translations.json (병합된 최신 데이터)
    2. poe_translations.json (PoeCharm 데이터)
    """
    data_dir = os.path.join(os.path.dirname(__file__), "data")

    # 병합된 파일 우선
    translation_files = [
        os.path.join(data_dir, "merged_translations.json"),
        os.path.join(data_dir, "poe_translations.json"),
    ]

    for translations_file in translation_files:
        if os.path.exists(translations_file):
            try:
                with open(translations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[INFO] Loaded translations from {os.path.basename(translations_file)}", file=sys.stderr)
                    return data
            except Exception as e:
                print(f"[WARN] Failed to load {translations_file}: {e}", file=sys.stderr)
                continue

    return {}


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
    parser.add_argument('--class', type=str, default=None, dest='char_class', help='Filter by class (Witch, Shadow, etc.)')
    parser.add_argument('--sort', type=str, default='views', choices=['views', 'date', 'likes', 'price'], help='Sort order')
    parser.add_argument('--budget', type=int, default=None, help='Max budget in chaos orbs')
    parser.add_argument('--hardcore', action='store_true', help='Use Hardcore league prices')

    args = parser.parse_args()

    # 하드코어 모드면 리그 이름 앞에 "Hardcore " 추가
    if args.hardcore and args.league:
        if not args.league.startswith("Hardcore"):
            args.league = f"Hardcore {args.league}"
    elif args.hardcore:
        # 리그가 자동 감지되면 나중에 하드코어 접두사 추가
        pass  # get_auto_recommendations에서 처리

    # 리그 자동 감지 시 하드코어 처리
    league = args.league
    if league is None:
        league = get_current_league()
        if args.hardcore and not league.startswith("Hardcore"):
            league = f"Hardcore {league}"

    # 맞춤 추천 모드 확인
    if args.reference_pob or args.streamer:
        # 맞춤 추천 모드
        result = get_personalized_recommendations(
            league=league,
            reference_pob=args.reference_pob,
            streamer_name=args.streamer,
            max_builds=args.max
        )
    else:
        # 일반 자동 추천
        result = get_auto_recommendations(
            league=league,
            user_characters=None,  # OAuth 연동 시 여기에 캐릭터 데이터 전달
            max_builds=args.max,
            include_streamers=not args.no_streamers,
            char_class=args.char_class,
            sort_order=args.sort,
            budget=args.budget
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
