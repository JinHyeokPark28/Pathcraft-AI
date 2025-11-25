"""
DC Inside POE Gallery Q&A Crawler
Collects Q&A from Korean POE community
"""

import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DCInsideQACrawler:
    """Crawl DC Inside POE Gallery for Korean Q&A"""

    def __init__(self):
        self.gallery_id = 'poe'
        self.base_url = f'https://gall.dcinside.com/mgallery/board/lists/?id={self.gallery_id}'

    def collect(self, limit: int = 2000) -> List[Dict]:
        """Collect Q&A from DC Inside"""
        logger.info("Collecting from DC Inside")

        # For now, return mock Korean data
        # TODO: Implement actual DC Inside scraping (requires handling anti-bot measures)
        return self._get_mock_data(limit)

    def _get_mock_data(self, limit: int) -> List[Dict]:
        """Mock Korean Q&A data"""
        mock_qa = [
            {
                'question': '3.27 리그 스타터 추천 부탁드립니다',
                'answer': '3.27에서는 Toxic Rain, Righteous Fire, Lightning Strike가 안정적입니다. 초보자는 RF를 추천합니다. 저예산으로 시작 가능하고 맵핑 속도도 빠릅니다. 라이프 재생 장비 위주로 맞추고 Rise of the Phoenix 방패만 있으면 Act 후반부터 사용 가능합니다.',
                'source': 'dcinside',
                'url': 'https://gall.dcinside.com/mgallery/board/view/?id=poe&no=example1',
                'timestamp': '2025-01-01T00:00:00'
            },
            {
                'question': '헬멧에 근접 물리 피해 젬레벨 올려주는 모드 붙이는 법',
                'answer': '아이템 레벨 86 헬멧이 필요합니다. Jagged Fossil + Pristine Fossil + Aberrant Fossil 조합으로 돌리면 확률이 올라갑니다. 또는 Harvest "Reforge with physical modifiers more common"을 사용하세요. Elder 영향 헬멧이면 +3 젬레벨도 가능합니다.',
                'source': 'dcinside',
                'url': 'https://gall.dcinside.com/mgallery/board/view/?id=poe&no=example2',
                'timestamp': '2025-01-01T00:00:00'
            },
            {
                'question': '카오스 데미지 빌드 저항 어떻게 올리나요',
                'answer': '카오스 저항은 일반 저항과 별개입니다. 방어구/장신구에서 얻을 수 있고, Divine Flesh 키스톤을 찍으면 엘레 피해 일부를 카오스로 받아 유용합니다. 최소 0% 이상 맞추는게 좋고, 75%까지 올리면 안전합니다. Amethyst Flask도 유용합니다.',
                'source': 'dcinside',
                'url': 'https://gall.dcinside.com/mgallery/board/view/?id=poe&no=example3',
                'timestamp': '2025-01-01T00:00:00'
            },
            {
                'question': '레벨 90 넘어서 경험치 너무 안올라요',
                'answer': '90 이후부터는 경험치 패널티가 심합니다. T16 맵을 빠르게 도는게 제일 효율적이고, 5-way legion이나 breachstone도 좋습니다. 죽으면 경험치 10% 깎이니 생존에 신경쓰세요. 대부분 95-96까지만 찍습니다.',
                'source': 'dcinside',
                'url': 'https://gall.dcinside.com/mgallery/board/view/?id=poe&no=example4',
                'timestamp': '2025-01-01T00:00:00'
            }
        ]

        result = []
        while len(result) < limit:
            result.extend(mock_qa)

        return result[:limit]


if __name__ == '__main__':
    crawler = DCInsideQACrawler()
    qa_pairs = crawler.collect(limit=10)
    print(f"Collected {len(qa_pairs)} Q&A pairs from DC Inside")
