# -*- coding: utf-8 -*-
"""
Streamer Data Collector
YouTube API를 사용하여 스트리머 데이터 수집 및 Tier 기준 검증
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# .env 파일 지원
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 현재 지원 스트리머 목록 (확장된 버전)
STREAMERS = {
    # 영어 스트리머
    'english': [
        # =================================================================
        # Tier 1 예상 (50K+ 구독자)
        # =================================================================
        {'name': 'Zizaran', 'channel_id': None, 'expected_tier': 1},
        {'name': 'Mathil', 'channel_id': None, 'expected_tier': 1},
        {'name': 'Pohx', 'channel_id': None, 'expected_tier': 1},
        {'name': 'GhazzyTV', 'channel_id': None, 'expected_tier': 1},
        {'name': 'Subtractem', 'channel_id': None, 'expected_tier': 1},
        {'name': 'Palsteron', 'channel_id': None, 'expected_tier': 1},
        {'name': 'Grimro', 'channel_id': None, 'expected_tier': 1},  # Grimro (파밍 전문)
        {'name': 'Big Ducks', 'channel_id': None, 'expected_tier': 1},  # 빌드 가이드 전문
        {'name': 'Crouching_Tuna', 'channel_id': None, 'expected_tier': 1},  # 크래프팅 전문

        # =================================================================
        # Tier 2 예상 (10K+ 구독자)
        # =================================================================
        {'name': 'jungroan', 'channel_id': None, 'expected_tier': 2},
        {'name': 'Ruetoo', 'channel_id': None, 'expected_tier': 2},
        {'name': 'Goratha', 'channel_id': None, 'expected_tier': 2},
        {'name': 'Path of Matth', 'channel_id': None, 'expected_tier': 2},
        {'name': 'Steelmage', 'channel_id': None, 'expected_tier': 2},
        # Darkee, Lightee, Octavian0 - Twitch 전용 (YouTube 비활성)
        {'name': 'Imexile', 'channel_id': None, 'expected_tier': 2},
        {'name': 'CuteDog', 'channel_id': None, 'expected_tier': 2},
        {'name': 'Empyrean', 'channel_id': None, 'expected_tier': 2},
        {'name': 'RaizQT', 'channel_id': None, 'expected_tier': 2},  # 베테랑 스트리머
        {'name': 'Nugiyen', 'channel_id': None, 'expected_tier': 2},  # HC 전문
        {'name': 'Tarke Cat', 'channel_id': None, 'expected_tier': 2},  # 뉴스/분석
        {'name': 'Tripolar Bear', 'channel_id': None, 'expected_tier': 2},  # 가이드
        {'name': 'Fyregrass', 'channel_id': None, 'expected_tier': 2},  # 미니언 빌드
        {'name': 'FastAF', 'channel_id': None, 'expected_tier': 2},  # 스피드런
        {'name': 'Lolcohol', 'channel_id': None, 'expected_tier': 2},  # 빌드 가이드
        {'name': 'spicysushi', 'channel_id': None, 'expected_tier': 2},  # Maxroll 가이드
        {'name': 'fubgun', 'channel_id': None, 'expected_tier': 2},  # Twitch 인기

        # =================================================================
        # Tier 3 예상 (1K+ 구독자)
        # =================================================================
        {'name': 'tytykiller', 'channel_id': None, 'expected_tier': 3},
        {'name': 'Ben_PoE', 'channel_id': None, 'expected_tier': 3},  # @Ben_PoE
        {'name': 'Havoc616', 'channel_id': None, 'expected_tier': 3},
        {'name': 'Alkaizer', 'channel_id': None, 'expected_tier': 3},
        {'name': 'Waggle', 'channel_id': None, 'expected_tier': 3},
        {'name': 'Quin69', 'channel_id': None, 'expected_tier': 3},
        {'name': 'KobeBlackMamba', 'channel_id': None, 'expected_tier': 3},
        {'name': 'Snap OW', 'channel_id': None, 'expected_tier': 3},  # 빌드 가이드
        {'name': 'Badger', 'channel_id': None, 'expected_tier': 3},  # 파밍 가이드
        {'name': 'Balor Mage', 'channel_id': None, 'expected_tier': 3},  # SSF 전문
        {'name': 'Sirgog', 'channel_id': None, 'expected_tier': 3},  # 아이템 가이드
        {'name': 'Tuna', 'channel_id': None, 'expected_tier': 3},  # 크래프팅
        {'name': 'ds_lily', 'channel_id': None, 'expected_tier': 3},  # 레이서
        {'name': 'Ventrua', 'channel_id': None, 'expected_tier': 3},  # 빌드 가이드
        {'name': 'Asmodeus', 'channel_id': None, 'expected_tier': 3},  # HC 레이서
        {'name': 'Elesshar', 'channel_id': None, 'expected_tier': 3},  # 가이드
        {'name': 'DonTheCrown', 'channel_id': None, 'expected_tier': 3},  # 크래프팅
        {'name': 'Angry Roleplayer', 'channel_id': None, 'expected_tier': 3},  # 빌드
        {'name': 'Kay Gaming', 'channel_id': None, 'expected_tier': 3},  # 미니언 전문
        {'name': 'Wrecker of Days', 'channel_id': None, 'expected_tier': 3},  # 캐주얼 빌드
        {'name': 'ShakCentral', 'channel_id': None, 'expected_tier': 3},  # Cold DoT 전문
    ],

    # 한국어 스트리머
    'korean': [
        # =================================================================
        # Tier 1 예상 (50K+ 구독자)
        # =================================================================
        {'name': '게이머 비누', 'channel_id': None, 'expected_tier': 1},
        {'name': 'POEASY', 'channel_id': None, 'expected_tier': 1},
        {'name': '엠피스', 'channel_id': None, 'expected_tier': 1},

        # =================================================================
        # Tier 2 예상 (10K+ 구독자)
        # =================================================================
        {'name': '추봉이', 'channel_id': None, 'expected_tier': 2},
        {'name': '뀨튜브', 'channel_id': None, 'expected_tier': 2},
        {'name': '로나의 게임채널', 'channel_id': None, 'expected_tier': 2},
        {'name': '스테TV', 'channel_id': None, 'expected_tier': 2},
        {'name': '까까모리', 'channel_id': None, 'expected_tier': 2},
        {'name': '혜미 Ham', 'channel_id': None, 'expected_tier': 2},
        {'name': '스탠다드QK', 'channel_id': None, 'expected_tier': 2},
        {'name': '닛쿄', 'channel_id': None, 'expected_tier': 2},  # 팀 바이퍼, 액트마스터

        # =================================================================
        # Tier 3 예상 (1K+ 구독자)
        # =================================================================
        {'name': '개굴덱', 'channel_id': None, 'expected_tier': 3},
        {'name': '산들바람', 'channel_id': None, 'expected_tier': 3},
        {'name': '새봄추', 'channel_id': None, 'expected_tier': 3},  # PoE2 스트리머
        {'name': '풍월량', 'channel_id': None, 'expected_tier': 3},  # PoE2 스트리머
        {'name': '녹두로', 'channel_id': None, 'expected_tier': 3},  # PoE2 스트리머
        {'name': '옥냥이', 'channel_id': None, 'expected_tier': 3},  # PoE2 스트리머
    ]
}

# Tier 기준
TIER_CRITERIA = {
    1: {'min_subscribers': 50000, 'min_videos': 30, 'days': 90, 'min_avg_views': 5000},
    2: {'min_subscribers': 10000, 'min_videos': 15, 'days': 60, 'min_avg_views': 2000},
    3: {'min_subscribers': 1000, 'min_videos': 5, 'days': 30, 'min_avg_views': 500},
}


def get_channel_id(youtube, channel_name: str) -> Optional[str]:
    """채널명으로 채널 ID 검색"""
    try:
        search_response = youtube.search().list(
            q=channel_name,
            part='snippet',
            type='channel',
            maxResults=1
        ).execute()

        items = search_response.get('items', [])
        if items:
            return items[0]['snippet']['channelId']
        return None
    except Exception as e:
        print(f"[ERROR] Failed to get channel ID for {channel_name}: {e}", file=sys.stderr)
        return None


def get_channel_stats(youtube, channel_id: str) -> Optional[Dict]:
    """채널 통계 정보 가져오기"""
    try:
        channel_response = youtube.channels().list(
            part='statistics,snippet',
            id=channel_id
        ).execute()

        items = channel_response.get('items', [])
        if items:
            stats = items[0]['statistics']
            snippet = items[0]['snippet']
            return {
                'title': snippet['title'],
                'subscribers': int(stats.get('subscriberCount', 0)),
                'total_videos': int(stats.get('videoCount', 0)),
                'total_views': int(stats.get('viewCount', 0))
            }
        return None
    except Exception as e:
        print(f"[ERROR] Failed to get channel stats: {e}", file=sys.stderr)
        return None


def get_recent_videos(youtube, channel_id: str, days: int = 90) -> List[Dict]:
    """최근 N일 내 POE 관련 영상 가져오기"""
    try:
        published_after = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%dT00:00:00Z')

        # 채널의 업로드 재생목록 ID 가져오기
        channel_response = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()

        items = channel_response.get('items', [])
        if not items:
            return []

        uploads_playlist_id = items[0]['contentDetails']['relatedPlaylists']['uploads']

        # 재생목록에서 영상 가져오기
        videos = []
        next_page_token = None

        while True:
            playlist_response = youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()

            for item in playlist_response.get('items', []):
                published_at = item['snippet']['publishedAt']
                published_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))

                # 날짜 필터
                if published_date < datetime.now(published_date.tzinfo) - timedelta(days=days):
                    continue

                title = item['snippet']['title'].lower()
                description = item['snippet'].get('description', '').lower()

                # POE 관련 영상인지 확인
                poe_keywords = ['poe', 'path of exile', '패스오브엑자일', '패오엑', 'pob',
                               'build', '빌드', 'league', '리그', 'settlers', 'keepers']

                is_poe = any(kw in title or kw in description for kw in poe_keywords)

                if is_poe:
                    videos.append({
                        'video_id': item['contentDetails']['videoId'],
                        'title': item['snippet']['title'],
                        'published_at': published_at
                    })

            next_page_token = playlist_response.get('nextPageToken')
            if not next_page_token:
                break

        return videos

    except Exception as e:
        print(f"[ERROR] Failed to get recent videos: {e}", file=sys.stderr)
        return []


def get_video_stats(youtube, video_ids: List[str]) -> Dict[str, Dict]:
    """영상 통계 정보 가져오기 (조회수, 좋아요)"""
    stats = {}

    # YouTube API는 한 번에 50개까지만 처리
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        try:
            video_response = youtube.videos().list(
                part='statistics',
                id=','.join(batch)
            ).execute()

            for item in video_response.get('items', []):
                video_id = item['id']
                video_stats = item['statistics']
                stats[video_id] = {
                    'views': int(video_stats.get('viewCount', 0)),
                    'likes': int(video_stats.get('likeCount', 0))
                }
        except Exception as e:
            print(f"[ERROR] Failed to get video stats: {e}", file=sys.stderr)

    return stats


def determine_tier(subscribers: int, video_count: int, avg_views: float, days: int) -> int:
    """데이터 기반 Tier 결정"""
    # Tier 1 체크
    if (subscribers >= TIER_CRITERIA[1]['min_subscribers'] and
        video_count >= TIER_CRITERIA[1]['min_videos'] and
        avg_views >= TIER_CRITERIA[1]['min_avg_views']):
        return 1

    # Tier 2 체크
    if (subscribers >= TIER_CRITERIA[2]['min_subscribers'] and
        video_count >= TIER_CRITERIA[2]['min_videos'] and
        avg_views >= TIER_CRITERIA[2]['min_avg_views']):
        return 2

    # Tier 3 체크
    if (subscribers >= TIER_CRITERIA[3]['min_subscribers'] and
        video_count >= TIER_CRITERIA[3]['min_videos'] and
        avg_views >= TIER_CRITERIA[3]['min_avg_views']):
        return 3

    # 기준 미달
    return 0


def collect_streamer_data(api_key: Optional[str] = None) -> Dict:
    """모든 스트리머 데이터 수집"""

    if api_key is None:
        api_key = os.environ.get('YOUTUBE_API_KEY')

    if not api_key:
        print("[ERROR] YOUTUBE_API_KEY not found", file=sys.stderr)
        return {}

    try:
        from googleapiclient.discovery import build
    except ImportError:
        print("[ERROR] google-api-python-client not installed", file=sys.stderr)
        return {}

    youtube = build('youtube', 'v3', developerKey=api_key)

    results = {
        'collected_at': datetime.now().isoformat(),
        'english': [],
        'korean': [],
        'summary': {
            'total': 0,
            'tier_1': 0,
            'tier_2': 0,
            'tier_3': 0,
            'unqualified': 0
        }
    }

    # API 호출 카운터 (할당량 모니터링)
    api_calls = 0

    for lang in ['english', 'korean']:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Collecting {lang.upper()} streamers...", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)

        for streamer in STREAMERS[lang]:
            name = streamer['name']
            print(f"\n[INFO] Processing: {name}", file=sys.stderr)

            # 1. 채널 ID 찾기
            channel_id = get_channel_id(youtube, name)
            api_calls += 1

            if not channel_id:
                print(f"[WARN] Channel not found: {name}", file=sys.stderr)
                results[lang].append({
                    'name': name,
                    'status': 'not_found',
                    'expected_tier': streamer['expected_tier']
                })
                continue

            # 2. 채널 통계
            channel_stats = get_channel_stats(youtube, channel_id)
            api_calls += 1

            if not channel_stats:
                print(f"[WARN] Failed to get stats: {name}", file=sys.stderr)
                continue

            # 3. 최근 90일 POE 영상
            recent_videos = get_recent_videos(youtube, channel_id, days=90)
            api_calls += 2  # channel + playlist API

            # 4. 영상 조회수 통계
            avg_views = 0
            if recent_videos:
                video_ids = [v['video_id'] for v in recent_videos]
                video_stats = get_video_stats(youtube, video_ids)
                api_calls += (len(video_ids) // 50) + 1

                total_views = sum(s['views'] for s in video_stats.values())
                avg_views = total_views / len(video_stats) if video_stats else 0

            # 5. Tier 결정
            actual_tier = determine_tier(
                subscribers=channel_stats['subscribers'],
                video_count=len(recent_videos),
                avg_views=avg_views,
                days=90
            )

            streamer_data = {
                'name': name,
                'channel_id': channel_id,
                'channel_title': channel_stats['title'],
                'subscribers': channel_stats['subscribers'],
                'poe_videos_90d': len(recent_videos),
                'avg_views': round(avg_views),
                'expected_tier': streamer['expected_tier'],
                'actual_tier': actual_tier,
                'tier_match': actual_tier == streamer['expected_tier'],
                'status': 'qualified' if actual_tier > 0 else 'unqualified'
            }

            results[lang].append(streamer_data)

            # 통계 업데이트
            results['summary']['total'] += 1
            if actual_tier == 1:
                results['summary']['tier_1'] += 1
            elif actual_tier == 2:
                results['summary']['tier_2'] += 1
            elif actual_tier == 3:
                results['summary']['tier_3'] += 1
            else:
                results['summary']['unqualified'] += 1

            # 결과 출력
            tier_str = f"Tier {actual_tier}" if actual_tier > 0 else "Unqualified"
            match_str = "✓" if streamer_data['tier_match'] else "✗"

            print(f"       Subscribers: {channel_stats['subscribers']:,}", file=sys.stderr)
            print(f"       POE Videos (90d): {len(recent_videos)}", file=sys.stderr)
            print(f"       Avg Views: {avg_views:,.0f}", file=sys.stderr)
            print(f"       Expected: Tier {streamer['expected_tier']} | Actual: {tier_str} {match_str}", file=sys.stderr)

    results['api_calls'] = api_calls
    print(f"\n[INFO] Total API calls: {api_calls}", file=sys.stderr)

    return results


def save_results(results: Dict, output_file: str = "streamer_data.json"):
    """결과 저장"""
    output_path = os.path.join(os.path.dirname(__file__), "build_data", output_file)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Results saved to: {output_path}", file=sys.stderr)


def print_summary(results: Dict):
    """요약 출력"""
    print("\n" + "="*60, file=sys.stderr)
    print("SUMMARY", file=sys.stderr)
    print("="*60, file=sys.stderr)

    summary = results.get('summary', {})
    print(f"Total Streamers: {summary.get('total', 0)}", file=sys.stderr)
    print(f"  Tier 1: {summary.get('tier_1', 0)}", file=sys.stderr)
    print(f"  Tier 2: {summary.get('tier_2', 0)}", file=sys.stderr)
    print(f"  Tier 3: {summary.get('tier_3', 0)}", file=sys.stderr)
    print(f"  Unqualified: {summary.get('unqualified', 0)}", file=sys.stderr)

    # Tier 불일치 목록
    print("\n" + "-"*60, file=sys.stderr)
    print("TIER MISMATCHES:", file=sys.stderr)
    print("-"*60, file=sys.stderr)

    for lang in ['english', 'korean']:
        for s in results.get(lang, []):
            if s.get('status') == 'qualified' and not s.get('tier_match', True):
                print(f"  {s['name']}: Expected Tier {s['expected_tier']} → Actual Tier {s['actual_tier']}", file=sys.stderr)

    # 기준 미달 목록
    print("\n" + "-"*60, file=sys.stderr)
    print("UNQUALIFIED:", file=sys.stderr)
    print("-"*60, file=sys.stderr)

    for lang in ['english', 'korean']:
        for s in results.get(lang, []):
            if s.get('status') in ['unqualified', 'not_found']:
                reason = s.get('status', 'unknown')
                print(f"  {s['name']}: {reason}", file=sys.stderr)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Streamer Data Collector')
    parser.add_argument('--api-key', type=str, default=None, help='YouTube API key')
    parser.add_argument('--output', type=str, default='streamer_data.json', help='Output file name')

    args = parser.parse_args()

    print("="*60, file=sys.stderr)
    print("STREAMER DATA COLLECTOR", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print(f"Collecting data for {len(STREAMERS['english'])} English + {len(STREAMERS['korean'])} Korean streamers", file=sys.stderr)
    print("="*60, file=sys.stderr)

    results = collect_streamer_data(args.api_key)

    if results:
        save_results(results, args.output)
        print_summary(results)

        # JSON 출력 (stdout)
        print(json.dumps(results, indent=2, ensure_ascii=False))
