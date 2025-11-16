"""
PathcraftAI Auto Patch Monitoring System
"살아있는 AI" - Living AI that stays up-to-date with POE patches

Monitors:
- Twitter (@pathofexile)
- Reddit (r/pathofexile)
- POE Official Homepage RSS
- YouTube (GGG Channel)

Cost: ~$3/month
Update Speed: 3-7 days faster than competitors
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Video content extraction
from video_transcript import extract_video_content

# OpenAI for patch analysis
from openai import OpenAI

# Twitter API
try:
    import tweepy
except ImportError:
    tweepy = None

# Reddit API
try:
    import praw
except ImportError:
    praw = None

# RSS Feed Parser
try:
    import feedparser
except ImportError:
    feedparser = None

# YouTube API
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PatchMonitor:
    """
    Auto Patch Monitoring System for POE

    GGG 공식 발표 타이밍에 맞춰 자동으로 패치 감지 및 분석
    """

    def __init__(
        self,
        youtube_api_key: Optional[str] = None,
        twitter_bearer_token: Optional[str] = None,
        reddit_client_id: Optional[str] = None,
        reddit_client_secret: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        db_path: str = "patch_monitor.db"
    ):
        """
        Initialize Patch Monitor

        Args:
            youtube_api_key: YouTube Data API v3 key
            twitter_bearer_token: Twitter API v2 Bearer Token
            reddit_client_id: Reddit OAuth client ID
            reddit_client_secret: Reddit OAuth client secret
            openai_api_key: OpenAI API key for GPT-4 analysis
            db_path: SQLite database path for tracking processed patches
        """
        # Load from environment if not provided
        self.youtube_api_key = youtube_api_key or os.environ.get('YOUTUBE_API_KEY')
        self.twitter_bearer_token = twitter_bearer_token or os.environ.get('TWITTER_BEARER_TOKEN')
        self.reddit_client_id = reddit_client_id or os.environ.get('REDDIT_CLIENT_ID')
        self.reddit_client_secret = reddit_client_secret or os.environ.get('REDDIT_CLIENT_SECRET')
        self.openai_api_key = openai_api_key or os.environ.get('PATHCRAFT_OPENAI_KEY')

        self.db_path = db_path
        self.processed_patches = self._load_processed_patches()

        # Initialize API clients
        self._init_clients()

    def _init_clients(self):
        """Initialize API clients"""
        # YouTube
        if self.youtube_api_key:
            self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
        else:
            self.youtube = None
            logger.warning("YouTube API key not provided")

        # Twitter
        if self.twitter_bearer_token and tweepy:
            self.twitter = tweepy.Client(bearer_token=self.twitter_bearer_token)
        else:
            self.twitter = None
            logger.warning("Twitter API not available")

        # Reddit
        if self.reddit_client_id and self.reddit_client_secret and praw:
            self.reddit = praw.Reddit(
                client_id=self.reddit_client_id,
                client_secret=self.reddit_client_secret,
                user_agent='PathcraftAI Patch Monitor v1.0'
            )
        else:
            self.reddit = None
            logger.warning("Reddit API not available")

        # OpenAI
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
            logger.warning("OpenAI API key not provided")

    def _load_processed_patches(self) -> Dict[str, Any]:
        """Load processed patches from database"""
        db_file = Path(self.db_path)
        if db_file.exists():
            try:
                with open(db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load processed patches: {e}")
                return {}
        return {}

    def _save_processed_patches(self):
        """Save processed patches to database"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.processed_patches, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save processed patches: {e}")

    def monitor_youtube(self, hours_ago: int = 24) -> List[Dict[str, Any]]:
        """
        Monitor GGG YouTube channel for new patch videos

        Args:
            hours_ago: Check videos from last N hours

        Returns:
            List of new patch videos
        """
        if not self.youtube:
            logger.warning("YouTube API not available")
            return []

        try:
            logger.info(f"[YouTube] Checking GGG channel for videos in last {hours_ago} hours")

            # GGG official channel ID
            channel_id = "UC0cmyGhMARccWBw0EZP-G_Q"

            # Calculate time threshold
            published_after = (datetime.utcnow() - timedelta(hours=hours_ago)).isoformat() + 'Z'

            request = self.youtube.search().list(
                part='snippet',
                channelId=channel_id,
                publishedAfter=published_after,
                type='video',
                maxResults=10,
                order='date'
            )
            response = request.execute()

            new_videos = []
            for item in response.get('items', []):
                video_id = item['id']['videoId']
                title = item['snippet']['title']
                description = item['snippet']['description']

                # Check if it's a patch video (contains version number)
                if self._is_patch_video(title, description):
                    if video_id not in self.processed_patches:
                        logger.info(f"[YouTube] 🆕 New patch video: {title}")
                        new_videos.append({
                            'source': 'youtube',
                            'video_id': video_id,
                            'title': title,
                            'description': description,
                            'url': f'https://www.youtube.com/watch?v={video_id}',
                            'published_at': item['snippet']['publishedAt']
                        })

            return new_videos

        except Exception as e:
            logger.error(f"[YouTube] Error: {e}")
            return []

    def monitor_twitter(self, hours_ago: int = 24) -> List[Dict[str, Any]]:
        """
        Monitor @pathofexile Twitter for patch announcements

        Args:
            hours_ago: Check tweets from last N hours

        Returns:
            List of new patch tweets
        """
        if not self.twitter:
            logger.warning("Twitter API not available")
            return []

        try:
            logger.info(f"[Twitter] Checking @pathofexile for tweets in last {hours_ago} hours")

            # Get recent tweets from @pathofexile
            tweets = self.twitter.get_users_tweets(
                id='17469764',  # @pathofexile user ID
                max_results=10,
                tweet_fields=['created_at', 'text'],
                start_time=(datetime.utcnow() - timedelta(hours=hours_ago)).isoformat() + 'Z'
            )

            new_tweets = []
            if tweets.data:
                for tweet in tweets.data:
                    tweet_id = tweet.id
                    text = tweet.text

                    # Check if it's a patch announcement
                    if self._is_patch_announcement(text):
                        if str(tweet_id) not in self.processed_patches:
                            logger.info(f"[Twitter] 🆕 New patch tweet: {text[:50]}...")
                            new_tweets.append({
                                'source': 'twitter',
                                'tweet_id': tweet_id,
                                'text': text,
                                'url': f'https://twitter.com/pathofexile/status/{tweet_id}',
                                'created_at': tweet.created_at.isoformat()
                            })

            return new_tweets

        except Exception as e:
            logger.error(f"[Twitter] Error: {e}")
            return []

    def monitor_reddit(self, hours_ago: int = 24) -> List[Dict[str, Any]]:
        """
        Monitor r/pathofexile for GGG patch posts

        Args:
            hours_ago: Check posts from last N hours

        Returns:
            List of new patch posts
        """
        if not self.reddit:
            logger.warning("Reddit API not available")
            return []

        try:
            logger.info(f"[Reddit] Checking r/pathofexile for posts in last {hours_ago} hours")

            subreddit = self.reddit.subreddit('pathofexile')
            new_posts = []

            for post in subreddit.new(limit=50):
                # Check if posted within time window
                post_time = datetime.fromtimestamp(post.created_utc)
                if post_time < datetime.utcnow() - timedelta(hours=hours_ago):
                    break

                # Check if it's a GGG official post and patch-related
                if post.author and post.author.name in ['Bex_GGG', 'Community_Team']:
                    if self._is_patch_announcement(post.title):
                        post_id = post.id
                        if post_id not in self.processed_patches:
                            logger.info(f"[Reddit] 🆕 New patch post: {post.title}")
                            new_posts.append({
                                'source': 'reddit',
                                'post_id': post_id,
                                'title': post.title,
                                'text': post.selftext,
                                'url': f'https://reddit.com{post.permalink}',
                                'created_at': post_time.isoformat()
                            })

            return new_posts

        except Exception as e:
            logger.error(f"[Reddit] Error: {e}")
            return []

    def monitor_rss(self) -> List[Dict[str, Any]]:
        """
        Monitor POE official homepage RSS feed

        Returns:
            List of new patch posts
        """
        if not feedparser:
            logger.warning("feedparser not available")
            return []

        try:
            logger.info("[RSS] Checking POE official news feed")

            feed_url = "https://www.pathofexile.com/news/rss"
            feed = feedparser.parse(feed_url)

            new_posts = []
            for entry in feed.entries[:10]:
                title = entry.title
                link = entry.link
                published = entry.get('published', '')

                # Check if it's a patch announcement
                if self._is_patch_announcement(title):
                    entry_id = link
                    if entry_id not in self.processed_patches:
                        logger.info(f"[RSS] 🆕 New patch post: {title}")
                        new_posts.append({
                            'source': 'rss',
                            'entry_id': entry_id,
                            'title': title,
                            'url': link,
                            'published_at': published
                        })

            return new_posts

        except Exception as e:
            logger.error(f"[RSS] Error: {e}")
            return []

    def _is_patch_video(self, title: str, description: str) -> bool:
        """Check if YouTube video is a patch video"""
        patch_keywords = [
            'patch', 'update', 'hotfix', 'balance', 'changes',
            '3.27', '3.28', '3.29', 'poe 2', 'path of exile 2'
        ]
        text = (title + ' ' + description).lower()
        return any(keyword in text for keyword in patch_keywords)

    def _is_patch_announcement(self, text: str) -> bool:
        """Check if text is a patch announcement"""
        patch_keywords = [
            'patch', 'hotfix', 'update', 'balance changes',
            '3.27', '3.28', '3.29', 'deployed', 'maintenance'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in patch_keywords)

    def analyze_patch(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze patch using GPT-4

        Args:
            news_item: News item from monitoring sources

        Returns:
            Analysis result with:
                - is_patch: bool
                - severity: str (critical | major | minor | hotfix)
                - impact: List[str] (skills, items, mechanics affected)
                - summary: str
        """
        if not self.openai_client:
            logger.warning("OpenAI API not available for analysis")
            return {
                'is_patch': True,
                'severity': 'unknown',
                'impact': [],
                'summary': 'No AI analysis available'
            }

        try:
            # Extract content
            content = ""
            if news_item['source'] == 'youtube':
                # Extract video content with 3-stage fallback
                video_result = extract_video_content(news_item['url'], self.youtube_api_key, self.openai_api_key)
                if video_result['success']:
                    content = video_result['content']
                    logger.info(f"[AI Analysis] Extracted video content using {video_result['method']}")
                else:
                    content = news_item.get('description', '')
            elif news_item['source'] == 'twitter':
                content = news_item['text']
            elif news_item['source'] == 'reddit':
                content = news_item['title'] + '\n\n' + news_item.get('text', '')
            elif news_item['source'] == 'rss':
                content = news_item['title']

            # GPT-4 analysis
            prompt = f"""Analyze this Path of Exile patch announcement:

{content}

Provide analysis in JSON format:
{{
    "is_patch": true/false,
    "severity": "critical|major|minor|hotfix",
    "impact": ["affected skills", "affected items", "affected mechanics"],
    "summary": "Brief summary of changes"
}}

Focus on:
- Build-affecting changes (skills, items, passives)
- Meta shifts
- Bug fixes vs balance changes
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a POE patch analysis expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            analysis = json.loads(response.choices[0].message.content)
            logger.info(f"[AI Analysis] Patch severity: {analysis.get('severity')}")

            return analysis

        except Exception as e:
            logger.error(f"[AI Analysis] Error: {e}")
            return {
                'is_patch': True,
                'severity': 'unknown',
                'impact': [],
                'summary': f'Analysis failed: {str(e)}'
            }

    def monitor_all_sources(self, hours_ago: int = 24) -> List[Dict[str, Any]]:
        """
        Monitor all sources for new patches

        Args:
            hours_ago: Check last N hours

        Returns:
            List of all new patch announcements
        """
        logger.info("="*60)
        logger.info("Starting patch monitoring cycle")
        logger.info(f"Time window: Last {hours_ago} hours")
        logger.info("="*60)

        all_news = []

        # Monitor YouTube
        all_news.extend(self.monitor_youtube(hours_ago))

        # Monitor Twitter
        all_news.extend(self.monitor_twitter(hours_ago))

        # Monitor Reddit
        all_news.extend(self.monitor_reddit(hours_ago))

        # Monitor RSS
        all_news.extend(self.monitor_rss())

        logger.info(f"\nFound {len(all_news)} new patch announcements")

        # Analyze each patch
        for news_item in all_news:
            logger.info(f"\nAnalyzing: {news_item.get('title', news_item.get('text', 'Unknown'))[:50]}...")
            analysis = self.analyze_patch(news_item)
            news_item['analysis'] = analysis

            # Mark as processed
            item_id = news_item.get('video_id') or news_item.get('tweet_id') or news_item.get('post_id') or news_item.get('entry_id')
            if item_id:
                self.processed_patches[str(item_id)] = {
                    'processed_at': datetime.utcnow().isoformat(),
                    'source': news_item['source'],
                    'severity': analysis.get('severity')
                }

        # Save processed patches
        self._save_processed_patches()

        return all_news

    def should_update_pathcraft(self, analysis: Dict[str, Any]) -> bool:
        """
        Determine if PathcraftAI should auto-update based on patch analysis

        Args:
            analysis: Patch analysis from GPT-4

        Returns:
            True if auto-update should trigger
        """
        severity = analysis.get('severity', 'unknown')
        impact = analysis.get('impact', [])

        # Critical or Major patches with build impact
        if severity in ['critical', 'major']:
            build_keywords = ['skill', 'item', 'passive', 'ascendancy', 'gem', 'unique']
            if any(keyword in ' '.join(impact).lower() for keyword in build_keywords):
                logger.info(f"[Auto-Update] ✅ Triggering update (severity: {severity})")
                return True

        logger.info(f"[Auto-Update] ⏸️ No update needed (severity: {severity})")
        return False

    def send_discord_notification(
        self,
        webhook_url: str,
        news_items: List[Dict[str, Any]]
    ):
        """
        Send Discord webhook notification for new patches

        Args:
            webhook_url: Discord webhook URL
            news_items: List of news items with analysis
        """
        try:
            import requests

            for item in news_items:
                analysis = item.get('analysis', {})
                severity = analysis.get('severity', 'unknown')
                summary = analysis.get('summary', 'No summary available')
                impact = ', '.join(analysis.get('impact', []))

                # Severity emoji
                severity_emoji = {
                    'critical': '🔴',
                    'major': '🟠',
                    'minor': '🟡',
                    'hotfix': '🔧',
                    'unknown': '⚪'
                }.get(severity, '⚪')

                # Build embed
                embed = {
                    "title": f"{severity_emoji} POE Patch Detected",
                    "description": item.get('title', item.get('text', 'Unknown'))[:200],
                    "url": item.get('url', ''),
                    "color": {
                        'critical': 0xFF0000,  # Red
                        'major': 0xFFA500,     # Orange
                        'minor': 0xFFFF00,     # Yellow
                        'hotfix': 0x00FF00,    # Green
                        'unknown': 0x808080    # Gray
                    }.get(severity, 0x808080),
                    "fields": [
                        {
                            "name": "Severity",
                            "value": severity.upper(),
                            "inline": True
                        },
                        {
                            "name": "Source",
                            "value": item.get('source', 'Unknown').upper(),
                            "inline": True
                        },
                        {
                            "name": "Impact",
                            "value": impact if impact else 'None specified',
                            "inline": False
                        },
                        {
                            "name": "Summary",
                            "value": summary[:1024],
                            "inline": False
                        }
                    ],
                    "footer": {
                        "text": "PathcraftAI Auto Patch Monitor"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }

                payload = {
                    "username": "PathcraftAI Patch Monitor",
                    "avatar_url": "https://web.poecdn.com/image/favicon/ogimage.png",
                    "embeds": [embed]
                }

                response = requests.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()

                logger.info(f"[Discord] ✅ Notification sent: {severity} patch")

        except Exception as e:
            logger.error(f"[Discord] ❌ Failed to send notification: {e}")


def main():
    """Test patch monitoring"""
    import argparse

    parser = argparse.ArgumentParser(description='PathcraftAI Patch Monitor')
    parser.add_argument('--hours', type=int, default=24, help='Monitor last N hours (default: 24)')
    parser.add_argument('--discord-webhook', type=str, help='Discord webhook URL for notifications')
    args = parser.parse_args()

    monitor = PatchMonitor()

    # Monitor last N hours
    news = monitor.monitor_all_sources(hours_ago=args.hours)

    print("\n" + "="*60)
    print("Patch Monitoring Results")
    print("="*60)

    for item in news:
        print(f"\nSource: {item['source']}")
        print(f"Title: {item.get('title', item.get('text', 'N/A'))[:100]}")
        print(f"Severity: {item['analysis'].get('severity')}")
        print(f"Impact: {', '.join(item['analysis'].get('impact', []))}")
        print(f"Summary: {item['analysis'].get('summary')}")
        print(f"URL: {item.get('url')}")

        if monitor.should_update_pathcraft(item['analysis']):
            print("⚡ AUTO-UPDATE TRIGGERED")

    print("="*60)

    # Send Discord notification if webhook provided
    if args.discord_webhook and news:
        print("\n[Discord] Sending notifications...")
        monitor.send_discord_notification(args.discord_webhook, news)
        print("[Discord] ✅ Notifications sent")


if __name__ == '__main__':
    main()
