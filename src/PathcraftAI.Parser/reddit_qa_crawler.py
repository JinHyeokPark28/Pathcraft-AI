"""
Reddit r/pathofexile Q&A Crawler
Collects Q&A pairs from Reddit discussions
"""

import os
import json
import time
import logging
from typing import List, Dict
from datetime import datetime

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    logging.warning("praw not installed. Run: pip install praw")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedditQACrawler:
    """Crawl r/pathofexile for Q&A pairs"""

    def __init__(self):
        self.subreddit_name = 'pathofexile'
        self.reddit = None

        # Initialize Reddit API
        if PRAW_AVAILABLE:
            self._init_reddit()

    def _init_reddit(self):
        """Initialize Reddit API client"""
        # Check for credentials
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT', 'PathcraftAI:v1.0')

        if not client_id or not client_secret:
            logger.warning("Reddit API credentials not found")
            logger.info("Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
            logger.info("Get credentials from: https://www.reddit.com/prefs/apps")
            return

        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            logger.info("Reddit API initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API: {e}")

    def collect(self, limit: int = 3000) -> List[Dict]:
        """Collect Q&A pairs from Reddit"""
        if not PRAW_AVAILABLE or not self.reddit:
            logger.warning("Reddit API not available, using mock data")
            return self._get_mock_data(limit)

        qa_pairs = []

        try:
            subreddit = self.reddit.subreddit(self.subreddit_name)

            # Search for common question patterns
            search_queries = [
                'how to',
                'what is',
                'why does',
                'best way to',
                'help with',
                'question about',
                'new player',
                'build guide',
                'league starter',
                'currency farming'
            ]

            for query in search_queries:
                logger.info(f"Searching Reddit: '{query}'")

                # Search submissions
                for submission in subreddit.search(query, limit=limit // len(search_queries)):
                    # Extract Q&A from post and top comments
                    qa_data = self._extract_qa_from_submission(submission)
                    qa_pairs.extend(qa_data)

                    # Rate limiting
                    time.sleep(0.5)

                    if len(qa_pairs) >= limit:
                        break

                if len(qa_pairs) >= limit:
                    break

        except Exception as e:
            logger.error(f"Error collecting from Reddit: {e}")

        logger.info(f"Collected {len(qa_pairs)} Q&A pairs from Reddit")
        return qa_pairs[:limit]

    def _extract_qa_from_submission(self, submission) -> List[Dict]:
        """Extract Q&A pairs from a Reddit submission"""
        qa_pairs = []

        try:
            # Main post as question
            question = submission.title

            # Get top comments as answers
            submission.comments.replace_more(limit=0)  # Remove "more comments"

            for comment in submission.comments[:5]:  # Top 5 comments
                if comment.score >= 2 and len(comment.body) >= 50:  # Quality filter
                    qa_pairs.append({
                        'question': question,
                        'answer': comment.body,
                        'source': 'reddit',
                        'url': f"https://reddit.com{submission.permalink}",
                        'score': comment.score,
                        'timestamp': datetime.fromtimestamp(submission.created_utc).isoformat()
                    })

            # If post has detailed selftext, use it as context
            if submission.selftext and len(submission.selftext) > 100:
                # Use selftext as extended question
                extended_q = f"{question}\n\nDetails: {submission.selftext[:500]}"

                for comment in submission.comments[:3]:
                    if comment.score >= 5 and len(comment.body) >= 100:
                        qa_pairs.append({
                            'question': extended_q,
                            'answer': comment.body,
                            'source': 'reddit',
                            'url': f"https://reddit.com{submission.permalink}",
                            'score': comment.score,
                            'timestamp': datetime.fromtimestamp(submission.created_utc).isoformat()
                        })

        except Exception as e:
            logger.debug(f"Error extracting Q&A: {e}")

        return qa_pairs

    def _get_mock_data(self, limit: int) -> List[Dict]:
        """Return mock data for testing"""
        logger.info("Using mock Reddit data")

        mock_qa = [
            {
                'question': 'What is the best league starter build for 3.27?',
                'answer': 'For 3.27, I recommend Toxic Rain Pathfinder or Righteous Fire Juggernaut. Both are very forgiving for new players and can scale well into endgame with minimal investment. Toxic Rain needs a 5-link bow and some life/chaos res gear. RF needs life regen gear and rise of the phoenix shield.',
                'source': 'reddit',
                'url': 'https://reddit.com/r/pathofexile/example1',
                'score': 42,
                'timestamp': '2025-01-01T00:00:00'
            },
            {
                'question': 'How do I craft +1 to level of all spell skill gems on a weapon?',
                'answer': 'Use an Orb of Alteration until you hit +1 to level of all spell skill gems (prefix). Then you can craft "Cannot roll attack modifiers" and slam an Exalted Orb to guarantee +1 to level of all chaos/fire/cold/lightning spell skill gems. Alternatively, use Harvest "Reforge with caster modifiers more common" for a higher chance.',
                'source': 'reddit',
                'url': 'https://reddit.com/r/pathofexile/example2',
                'score': 156,
                'timestamp': '2025-01-02T00:00:00'
            },
            {
                'question': 'Why am I dying so much in red maps?',
                'answer': 'Most common reasons: 1) Not enough life/ES (aim for 4.5k+ life or 6k+ ES), 2) Uncapped resistances (must be 75%+ for ele res, chaos can be negative but positive is better), 3) No defensive layers (armour, evasion, block, dodge), 4) Standing still too much (learn boss mechanics), 5) Not upgrading flasks (use utility flasks with immune to bleeding/freeze).',
                'source': 'reddit',
                'url': 'https://reddit.com/r/pathofexile/example3',
                'score': 89,
                'timestamp': '2025-01-03T00:00:00'
            }
        ]

        # Duplicate mock data to reach limit
        result = []
        while len(result) < limit:
            result.extend(mock_qa)

        return result[:limit]


if __name__ == '__main__':
    crawler = RedditQACrawler()
    qa_pairs = crawler.collect(limit=100)

    print(f"\nCollected {len(qa_pairs)} Q&A pairs")
    print("\nSample:")
    if qa_pairs:
        sample = qa_pairs[0]
        print(f"Q: {sample['question'][:100]}...")
        print(f"A: {sample['answer'][:100]}...")
