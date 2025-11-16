"""
POEdb.tw Mass Scraper - Extract 30,000+ Korean translations
Scrapes ALL skills, items, mods, and game data from poedb.tw

Target:
- 550+ skill gems
- 1000+ unique items
- 500+ map mods
- 200+ keystones/notables
- 1000+ base items
- Total: 30,000+ translations

Usage:
    python poedb_mass_scraper.py --output poe_kr_full.json --workers 10
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, List, Optional, Set
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from tqdm import tqdm
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class POEDBMassScraper:
    """Mass scrape Korean-English translations from poedb.tw"""

    BASE_URL_KR = "https://poedb.tw/kr"
    BASE_URL_US = "https://poedb.tw/us"

    def __init__(self, workers: int = 10):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.workers = workers
        self.translations = {}
        self.failed_urls = []

    def extract_korean_name(self, url_path: str) -> Optional[str]:
        """
        Extract Korean name from poedb.tw/kr/{url_path}

        Args:
            url_path: URL path (e.g., "Siege_Ballista")

        Returns:
            Korean name or None
        """
        url = f"{self.BASE_URL_KR}/{url_path}"

        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title')
            if not title:
                return None

            title_text = title.get_text()
            korean_name = title_text.split(' - ')[0].strip()

            # Verify it's Korean (contains Hangul)
            if not any('\uAC00' <= char <= '\uD7A3' for char in korean_name):
                return None

            return korean_name

        except Exception as e:
            logger.debug(f"Error fetching {url_path}: {e}")
            return None

    def scrape_skill_gems(self) -> Dict[str, str]:
        """Scrape all skill gems (550+ skills)"""
        logger.info("Fetching skill gem list...")

        # Get skill list page
        url = f"{self.BASE_URL_KR}/Skill_Gems"
        response = self.session.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract all skill gem URLs
        skill_urls = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/kr/') and len(href) > 4:
                skill_name = href.replace('/kr/', '')
                # Filter out non-skill pages
                if not any(x in skill_name.lower() for x in ['category', 'search', 'index', 'list']):
                    skill_urls.add(skill_name)

        logger.info(f"Found {len(skill_urls)} skill gem URLs")

        # Parallel scraping
        translations = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.extract_korean_name, url): url for url in skill_urls}

            with tqdm(total=len(skill_urls), desc="Scraping skills") as pbar:
                for future in as_completed(futures):
                    url = futures[future]
                    try:
                        korean_name = future.result()
                        if korean_name:
                            english_name = url.replace('_', ' ')
                            translations[korean_name] = english_name
                    except Exception as e:
                        logger.debug(f"Failed {url}: {e}")
                        self.failed_urls.append(url)
                    finally:
                        pbar.update(1)
                        time.sleep(0.1)  # Rate limiting

        logger.info(f"Scraped {len(translations)} skill gems")
        return translations

    def scrape_unique_items(self) -> Dict[str, str]:
        """Scrape unique items (1000+ items)"""
        logger.info("Fetching unique items list...")

        # Categories to scrape
        categories = [
            'Unique_Weapons', 'Unique_Armours', 'Unique_Accessories',
            'Unique_Flasks', 'Unique_Jewels', 'Unique_Maps'
        ]

        all_items = set()
        for category in categories:
            try:
                url = f"{self.BASE_URL_KR}/{category}"
                response = self.session.get(url, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')

                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('/kr/') and len(href) > 4:
                        item_name = href.replace('/kr/', '')
                        if not any(x in item_name.lower() for x in ['category', 'search', 'index', 'list']):
                            all_items.add(item_name)

                logger.info(f"Found {len(all_items)} items in {category}")
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Failed to fetch {category}: {e}")

        logger.info(f"Found {len(all_items)} total unique items")

        # Parallel scraping
        translations = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.extract_korean_name, url): url for url in all_items}

            with tqdm(total=len(all_items), desc="Scraping unique items") as pbar:
                for future in as_completed(futures):
                    url = futures[future]
                    try:
                        korean_name = future.result()
                        if korean_name:
                            english_name = url.replace('_', ' ')
                            translations[korean_name] = english_name
                    except Exception as e:
                        logger.debug(f"Failed {url}: {e}")
                        self.failed_urls.append(url)
                    finally:
                        pbar.update(1)
                        time.sleep(0.1)

        logger.info(f"Scraped {len(translations)} unique items")
        return translations

    def scrape_base_items(self) -> Dict[str, str]:
        """Scrape base item types (1000+ base items)"""
        logger.info("Fetching base items list...")

        categories = [
            'Weapons', 'Armours', 'Accessories', 'Flasks', 'Maps', 'Currency'
        ]

        all_items = set()
        for category in categories:
            try:
                url = f"{self.BASE_URL_KR}/{category}"
                response = self.session.get(url, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')

                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('/kr/') and len(href) > 4:
                        item_name = href.replace('/kr/', '')
                        if not any(x in item_name.lower() for x in ['category', 'search', 'index', 'list']):
                            all_items.add(item_name)

                logger.info(f"Found {len(all_items)} items in {category}")
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Failed to fetch {category}: {e}")

        logger.info(f"Found {len(all_items)} total base items")

        # Parallel scraping
        translations = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.extract_korean_name, url): url for url in all_items}

            with tqdm(total=len(all_items), desc="Scraping base items") as pbar:
                for future in as_completed(futures):
                    url = futures[future]
                    try:
                        korean_name = future.result()
                        if korean_name:
                            english_name = url.replace('_', ' ')
                            translations[korean_name] = english_name
                    except Exception as e:
                        logger.debug(f"Failed {url}: {e}")
                        self.failed_urls.append(url)
                    finally:
                        pbar.update(1)
                        time.sleep(0.1)

        logger.info(f"Scraped {len(translations)} base items")
        return translations

    def scrape_passive_skills(self) -> Dict[str, str]:
        """Scrape passive tree keystones and notables (500+ passives)"""
        logger.info("Scraping passive skills...")

        # Get passive tree data
        url = f"{self.BASE_URL_KR}/Passive_Skill"
        translations = {}

        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract passive skill names from tables
            for table in soup.find_all('table'):
                for row in table.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        # Look for Korean-English pairs
                        korean_text = cells[0].get_text(strip=True)
                        english_text = cells[1].get_text(strip=True)

                        if korean_text and any('\uAC00' <= char <= '\uD7A3' for char in korean_text):
                            translations[korean_text] = english_text

        except Exception as e:
            logger.warning(f"Failed to scrape passive skills: {e}")

        logger.info(f"Scraped {len(translations)} passive skills")
        return translations

    def scrape_map_mods(self) -> Dict[str, str]:
        """Scrape map mod translations (prefix/suffix affixes)"""
        logger.info("Scraping map mods...")

        url = f"{self.BASE_URL_KR}/Mods"
        translations = {}

        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract mod names from tables
            for table in soup.find_all('table'):
                for row in table.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        korean_text = cells[0].get_text(strip=True)
                        english_text = cells[1].get_text(strip=True)

                        if korean_text and any('\uAC00' <= char <= '\uD7A3' for char in korean_text):
                            translations[korean_text] = english_text

        except Exception as e:
            logger.warning(f"Failed to scrape map mods: {e}")

        logger.info(f"Scraped {len(translations)} map mods")
        return translations

    def scrape_atlas_passives(self) -> Dict[str, str]:
        """Scrape Atlas passive tree translations"""
        logger.info("Scraping Atlas passives...")

        url = f"{self.BASE_URL_KR}/Atlas"
        translations = {}

        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract Atlas passive names
            for table in soup.find_all('table'):
                for row in table.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        korean_text = cells[0].get_text(strip=True)
                        english_text = cells[1].get_text(strip=True)

                        if korean_text and any('\uAC00' <= char <= '\uD7A3' for char in korean_text):
                            translations[korean_text] = english_text

        except Exception as e:
            logger.warning(f"Failed to scrape Atlas passives: {e}")

        logger.info(f"Scraped {len(translations)} Atlas passives")
        return translations

    def scrape_item_mods(self) -> Dict[str, str]:
        """Scrape item mod translations (all affixes)"""
        logger.info("Scraping item mods...")

        categories = ['Prefix', 'Suffix']
        all_mods = {}

        for category in categories:
            try:
                url = f"{self.BASE_URL_KR}/{category}"
                response = self.session.get(url, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')

                for table in soup.find_all('table'):
                    for row in table.find_all('tr'):
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            korean_text = cells[0].get_text(strip=True)
                            english_text = cells[1].get_text(strip=True)

                            if korean_text and any('\uAC00' <= char <= '\uD7A3' for char in korean_text):
                                all_mods[korean_text] = english_text

                logger.info(f"Found {len(all_mods)} mods in {category}")
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Failed to fetch {category}: {e}")

        logger.info(f"Scraped {len(all_mods)} item mods total")
        return all_mods

    def scrape_all(self) -> Dict[str, str]:
        """Scrape everything (30,000+ translations)"""
        all_translations = {}

        # 1. Skill gems (550+)
        logger.info("=" * 60)
        logger.info("STEP 1/8: Scraping skill gems...")
        logger.info("=" * 60)
        skill_translations = self.scrape_skill_gems()
        all_translations.update(skill_translations)

        # 2. Unique items (1000+)
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2/8: Scraping unique items...")
        logger.info("=" * 60)
        unique_translations = self.scrape_unique_items()
        all_translations.update(unique_translations)

        # 3. Base items (1000+)
        logger.info("\n" + "=" * 60)
        logger.info("STEP 3/8: Scraping base items...")
        logger.info("=" * 60)
        base_translations = self.scrape_base_items()
        all_translations.update(base_translations)

        # 4. Passive skills (500+)
        logger.info("\n" + "=" * 60)
        logger.info("STEP 4/8: Scraping passive skills...")
        logger.info("=" * 60)
        passive_translations = self.scrape_passive_skills()
        all_translations.update(passive_translations)

        # 5. Map mods
        logger.info("\n" + "=" * 60)
        logger.info("STEP 5/8: Scraping map mods...")
        logger.info("=" * 60)
        map_mod_translations = self.scrape_map_mods()
        all_translations.update(map_mod_translations)

        # 6. Atlas passives
        logger.info("\n" + "=" * 60)
        logger.info("STEP 6/8: Scraping Atlas passives...")
        logger.info("=" * 60)
        atlas_translations = self.scrape_atlas_passives()
        all_translations.update(atlas_translations)

        # 7. Item mods (prefix/suffix)
        logger.info("\n" + "=" * 60)
        logger.info("STEP 7/8: Scraping item mods...")
        logger.info("=" * 60)
        item_mod_translations = self.scrape_item_mods()
        all_translations.update(item_mod_translations)

        # 8. Summary
        logger.info("\n" + "=" * 60)
        logger.info("SCRAPING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Skill gems:      {len(skill_translations):5d}")
        logger.info(f"Unique items:    {len(unique_translations):5d}")
        logger.info(f"Base items:      {len(base_translations):5d}")
        logger.info(f"Passive skills:  {len(passive_translations):5d}")
        logger.info(f"Map mods:        {len(map_mod_translations):5d}")
        logger.info(f"Atlas passives:  {len(atlas_translations):5d}")
        logger.info(f"Item mods:       {len(item_mod_translations):5d}")
        logger.info("-" * 60)
        logger.info(f"TOTAL:           {len(all_translations):5d}")
        logger.info(f"Failed URLs:     {len(self.failed_urls):5d}")
        logger.info("=" * 60)

        return all_translations

    def save_to_json(self, translations: Dict[str, str], output_path: str):
        """Save translations to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(translations, f, ensure_ascii=False, indent=2, sort_keys=True)
        logger.info(f"✅ Saved {len(translations)} translations to {output_path}")

    def save_to_python(self, translations: Dict[str, str], output_path: str):
        """Generate Python dictionary"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('"""Auto-generated Korean-English POE translations"""\n\n')
            f.write(f'# Total: {len(translations)} translations\n\n')
            f.write('POE_TRANSLATIONS_FULL = {\n')

            for korean, english in sorted(translations.items()):
                f.write(f'    "{korean}": "{english}",\n')

            f.write('}\n')

        logger.info(f"✅ Saved Python dict to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Mass scrape Korean translations from poedb.tw')
    parser.add_argument('--output', type=str, default='poe_kr_full.json',
                       help='Output JSON file path')
    parser.add_argument('--python', type=str, default='poe_kr_full.py',
                       help='Output Python file path')
    parser.add_argument('--workers', type=int, default=10,
                       help='Number of parallel workers (default: 10)')
    parser.add_argument('--skills-only', action='store_true',
                       help='Only scrape skill gems (fast test)')

    args = parser.parse_args()

    scraper = POEDBMassScraper(workers=args.workers)

    if args.skills_only:
        logger.info("Running in SKILLS-ONLY mode (fast test)")
        translations = scraper.scrape_skill_gems()
    else:
        logger.info("Running FULL scraping (30,000+ translations)")
        translations = scraper.scrape_all()

    if translations:
        scraper.save_to_json(translations, args.output)
        scraper.save_to_python(translations, args.python)

        print()
        print("Sample translations:")
        for korean, english in list(translations.items())[:20]:
            print(f"  {korean:30s} -> {english}")
    else:
        logger.error("❌ No translations scraped")
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
