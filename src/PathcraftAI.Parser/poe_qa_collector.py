"""
POE Q&A Data Collector for Fine-tuning
Collects Q&A pairs from multiple sources for GPT-3.5 fine-tuning
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class POEQACollector:
    """Main collector that aggregates data from all sources"""

    def __init__(self, output_dir: str = "data/qa_dataset"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Track collection stats
        self.stats = {
            'reddit': 0,
            'wiki': 0,
            'forum': 0,
            'dcinside': 0,
            'youtube': 0,
            'templates': 0,
            'total': 0
        }

    def collect_all(self, target_count: int = 10000) -> Dict[str, Any]:
        """Collect Q&A pairs from all sources"""
        logger.info(f"Starting Q&A collection (target: {target_count})")

        all_qa_pairs = []

        # 1. Reddit r/pathofexile
        logger.info("Collecting from Reddit...")
        reddit_qa = self.collect_reddit(limit=3000)
        all_qa_pairs.extend(reddit_qa)
        self.stats['reddit'] = len(reddit_qa)

        # 2. POE Wiki
        logger.info("Collecting from POE Wiki...")
        wiki_qa = self.collect_wiki(limit=2000)
        all_qa_pairs.extend(wiki_qa)
        self.stats['wiki'] = len(wiki_qa)

        # 3. POE Forum
        logger.info("Collecting from POE Forum...")
        forum_qa = self.collect_forum(limit=2000)
        all_qa_pairs.extend(forum_qa)
        self.stats['forum'] = len(forum_qa)

        # 4. DC Inside
        logger.info("Collecting from DC Inside...")
        dcinside_qa = self.collect_dcinside(limit=2000)
        all_qa_pairs.extend(dcinside_qa)
        self.stats['dcinside'] = len(dcinside_qa)

        # 5. YouTube Comments
        logger.info("Collecting from YouTube...")
        youtube_qa = self.collect_youtube(limit=1000)
        all_qa_pairs.extend(youtube_qa)
        self.stats['youtube'] = len(youtube_qa)

        # 6. Template-generated Q&A (high quality)
        logger.info("Generating from templates...")
        template_qa = self.collect_templates(limit=5000)
        all_qa_pairs.extend(template_qa)
        self.stats['templates'] = len(template_qa)

        # Update total
        self.stats['total'] = len(all_qa_pairs)

        # Save raw data
        raw_file = os.path.join(self.output_dir, 'raw_qa_pairs.json')
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(all_qa_pairs, f, indent=2, ensure_ascii=False)

        logger.info(f"Collected {self.stats['total']} Q&A pairs")
        logger.info(f"Stats: {self.stats}")

        return {
            'qa_pairs': all_qa_pairs,
            'stats': self.stats,
            'output_file': raw_file
        }

    def collect_reddit(self, limit: int = 3000) -> List[Dict]:
        """Collect Q&A from Reddit r/pathofexile"""
        # Implementation will be in reddit_qa_crawler.py
        from reddit_qa_crawler import RedditQACrawler
        crawler = RedditQACrawler()
        return crawler.collect(limit=limit)

    def collect_wiki(self, limit: int = 2000) -> List[Dict]:
        """Collect Q&A from POE Wiki"""
        # Implementation will be in wiki_qa_crawler.py
        from wiki_qa_crawler import WikiQACrawler
        crawler = WikiQACrawler()
        return crawler.collect(limit=limit)

    def collect_forum(self, limit: int = 2000) -> List[Dict]:
        """Collect Q&A from POE Official Forum"""
        # Implementation will be in forum_qa_crawler.py
        from forum_qa_crawler import ForumQACrawler
        crawler = ForumQACrawler()
        return crawler.collect(limit=limit)

    def collect_dcinside(self, limit: int = 2000) -> List[Dict]:
        """Collect Q&A from DC Inside POE Gallery"""
        # Implementation will be in dcinside_qa_crawler.py
        from dcinside_qa_crawler import DCInsideQACrawler
        crawler = DCInsideQACrawler()
        return crawler.collect(limit=limit)

    def collect_youtube(self, limit: int = 1000) -> List[Dict]:
        """Collect Q&A from YouTube comments"""
        # Implementation will be in youtube_qa_crawler.py
        from youtube_qa_crawler import YouTubeQACrawler
        crawler = YouTubeQACrawler()
        return crawler.collect(limit=limit)

    def collect_templates(self, limit: int = 5000) -> List[Dict]:
        """Generate Q&A from templates"""
        from qa_template_generator import QATemplateGenerator
        generator = QATemplateGenerator()
        return generator.generate(count=limit)

    def clean_and_format(self, qa_pairs: List[Dict]) -> List[Dict]:
        """Clean and format data for fine-tuning"""
        cleaned = []

        for qa in qa_pairs:
            # Skip invalid entries
            if not qa.get('question') or not qa.get('answer'):
                continue

            # Skip too short entries
            if len(qa['question']) < 10 or len(qa['answer']) < 20:
                continue

            # Format for fine-tuning
            cleaned.append({
                'messages': [
                    {'role': 'system', 'content': 'You are an expert Path of Exile assistant.'},
                    {'role': 'user', 'content': qa['question']},
                    {'role': 'assistant', 'content': qa['answer']}
                ],
                'source': qa.get('source', 'unknown'),
                'url': qa.get('url', ''),
                'timestamp': qa.get('timestamp', '')
            })

        return cleaned

    def export_for_finetuning(self, qa_pairs: List[Dict], output_file: str = None):
        """Export data in OpenAI fine-tuning format (JSONL)"""
        if output_file is None:
            output_file = os.path.join(self.output_dir, 'finetuning_dataset.jsonl')

        cleaned = self.clean_and_format(qa_pairs)

        with open(output_file, 'w', encoding='utf-8') as f:
            for item in cleaned:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        logger.info(f"Exported {len(cleaned)} cleaned Q&A pairs to {output_file}")
        return output_file


def main():
    """Main execution"""
    collector = POEQACollector()

    # Collect data
    result = collector.collect_all(target_count=10000)

    # Export for fine-tuning
    finetuning_file = collector.export_for_finetuning(result['qa_pairs'])

    # Print summary
    print("\n" + "=" * 80)
    print("POE Q&A COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total Q&A pairs collected: {result['stats']['total']}")
    print(f"\nBreakdown:")
    print(f"  Reddit:     {result['stats']['reddit']}")
    print(f"  Wiki:       {result['stats']['wiki']}")
    print(f"  Forum:      {result['stats']['forum']}")
    print(f"  DC Inside:  {result['stats']['dcinside']}")
    print(f"  YouTube:    {result['stats']['youtube']}")
    print(f"  Templates:  {result['stats']['templates']}")
    print(f"\nOutput files:")
    print(f"  Raw data:        {result['output_file']}")
    print(f"  Fine-tuning:     {finetuning_file}")
    print("=" * 80)


if __name__ == '__main__':
    main()
