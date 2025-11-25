"""
YouTube Comments Q&A Crawler
Collects Q&A from POE YouTube video comments
"""

import os
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YouTubeQACrawler:
    """Crawl YouTube comments for Q&A"""

    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')

    def collect(self, limit: int = 1000) -> List[Dict]:
        """Collect Q&A from YouTube comments"""
        logger.info("Collecting from YouTube")

        if not self.api_key:
            logger.warning("YOUTUBE_API_KEY not found, using mock data")
            return self._get_mock_data(limit)

        # TODO: Implement actual YouTube API comments collection
        return self._get_mock_data(limit)

    def _get_mock_data(self, limit: int) -> List[Dict]:
        """Mock YouTube Q&A data"""
        mock_qa = [
            {
                'question': 'Can this build do uber bosses on low budget?',
                'answer': 'Not really, you need specific uniques like Mageblood or Squire for uber content. But you can farm regular bosses and T16 maps comfortably with 50-100 divines investment. Focus on getting your core items first, then save up for the big ticket upgrades.',
                'source': 'youtube',
                'url': 'https://youtube.com/watch?v=example1',
                'timestamp': '2025-01-01T00:00:00'
            },
            {
                'question': 'What order should I upgrade my gear?',
                'answer': 'Priority: 1) Weapon (biggest DPS increase), 2) 6-link body armor, 3) Life/resist boots/gloves/helm, 4) Belt and jewelry for resistances, 5) Cluster jewels, 6) Luxury items like Mageblood. Always cap your resistances at 75% first before anything else.',
                'source': 'youtube',
                'url': 'https://youtube.com/watch?v=example2',
                'timestamp': '2025-01-01T00:00:00'
            },
            {
                'question': 'Is this build good for mapping or bossing?',
                'answer': 'This is primarily a mapper. Clear speed is amazing but single target is mediocre. For bosses you\'ll want to swap to a different skill or invest heavily in single target scaling. Good for farming currency in maps then use that to fund a boss killer.',
                'source': 'youtube',
                'url': 'https://youtube.com/watch?v=example3',
                'timestamp': '2025-01-01T00:00:00'
            }
        ]

        result = []
        while len(result) < limit:
            result.extend(mock_qa)

        return result[:limit]


if __name__ == '__main__':
    crawler = YouTubeQACrawler()
    qa_pairs = crawler.collect(limit=10)
    print(f"Collected {len(qa_pairs)} Q&A pairs from YouTube")
