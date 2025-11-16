"""
POEdb.tw Korean Translation Scraper
Extracts Korean-English translation pairs from poedb.tw

Strategy:
- poedb.tw uses URL pattern: /kr/{skill_name} and /us/{skill_name}
- Korean skill name is in page title: "한글명 - PoEDB"
- Scrape both /kr/ and /us/ versions to get pairs

Usage:
    python poedb_scraper.py --output poe_translations_full.json
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, List, Optional
import argparse


class POEDBScraper:
    """Scrape Korean-English translations from poedb.tw"""

    BASE_URL_KR = "https://poedb.tw/kr"
    BASE_URL_US = "https://poedb.tw/us"

    # List of popular skills to scrape
    SKILL_LIST = [
        # Attack skills
        "Kinetic_Blast", "Tornado_Shot", "Spectral_Throw", "Lightning_Arrow",
        "Ice_Shot", "Split_Arrow", "Frost_Blades", "Elemental_Hit",
        "Barrage", "Rain_of_Arrows", "Galvanic_Arrow", "Burning_Arrow",

        # Spell skills
        "Arc", "Fireball", "Ice_Nova", "Spark", "Lightning_Strike",
        "Frost_Bolt", "Ball_Lightning", "Glacial_Cascade", "Freezing_Pulse",
        "Flame_Surge", "Discharge", "Storm_Call", "Detonate_Dead",

        # Summoner
        "Summon_Skeleton", "Raise_Zombie", "Raise_Spectre", "Summon_Raging_Spirit",
        "Summon_Skitterbots", "Herald_of_Agony", "Dominating_Blow",

        # Totem
        "Siege_Ballista", "Ballista_Totem", "Spell_Totem", "Ancestral_Warchief",

        # Mine/Trap
        "Pyroclast_Mine", "Icicle_Mine", "Seismic_Trap", "Lightning_Trap",

        # Special builds
        "Righteous_Fire", "Death_Aura", "Caustic_Arrow", "Essence_Drain",
        "Bane", "Soulrend", "Vortex", "Cold_Snap",

        # Melee
        "Cyclone", "Lacerate", "Blade_Flurry", "Earthquake", "Ground_Slam",
        "Molten_Strike", "Glacial_Hammer", "Heavy_Strike", "Double_Strike",
        "Reave", "Blade_Vortex", "Ethereal_Knives",

        # Movement/Utility
        "Dash", "Flame_Dash", "Frostblink", "Whirling_Blades", "Leap_Slam",
        "Shield_Charge", "Smoke_Mine",

        # Auras
        "Hatred", "Anger", "Wrath", "Grace", "Determination", "Discipline",
        "Purity_of_Elements", "Purity_of_Fire", "Purity_of_Ice", "Purity_of_Lightning",
        "Vitality", "Clarity", "Haste", "Precision", "Pride", "Zealotry",
        "Malevolence",

        # Curses
        "Frostbite", "Flammability", "Conductivity", "Vulnerability", "Temporal_Chains",
        "Enfeeble", "Elemental_Weakness", "Despair", "Punishment", "Assassin's_Mark",
        "Poacher's_Mark", "Warlord's_Mark", "Projectile_Weakness",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def get_korean_name(self, skill_url_name: str) -> Optional[str]:
        """
        Get Korean skill name from poedb.tw/kr/{skill_url_name}

        Args:
            skill_url_name: URL-friendly skill name (e.g., "Siege_Ballista")

        Returns:
            Korean skill name or None
        """
        url = f"{self.BASE_URL_KR}/{skill_url_name}"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                print(f"   ❌ Failed to fetch {skill_url_name} (status {response.status_code})")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract from title: "한글명 - PoEDB, Path of Exile Wiki"
            title = soup.find('title')
            if not title:
                return None

            title_text = title.get_text()
            # Remove " - PoEDB, Path of Exile Wiki"
            korean_name = title_text.split(' - ')[0].strip()

            # Verify it's actually Korean (contains Hangul characters)
            if not any('\uAC00' <= char <= '\uD7A3' for char in korean_name):
                return None

            return korean_name

        except Exception as e:
            print(f"   ❌ Error fetching {skill_url_name}: {e}")
            return None

    def scrape_all_skills(self) -> Dict[str, str]:
        """
        Scrape all skills and return Korean->English mapping

        Returns:
            Dict mapping Korean name to English name
        """
        translations = {}

        print("="*60)
        print("POEdb.tw Korean Translation Scraper")
        print("="*60)
        print(f"Scraping {len(self.SKILL_LIST)} skills...")
        print()

        for i, skill in enumerate(self.SKILL_LIST, 1):
            english_name = skill.replace('_', ' ')
            print(f"[{i}/{len(self.SKILL_LIST)}] {english_name}...", end=' ')

            korean_name = self.get_korean_name(skill)
            if korean_name:
                translations[korean_name] = english_name
                print(f"✅ {korean_name}")
            else:
                print(f"❌ Failed")

            # Rate limiting: 1 request per second
            time.sleep(1)

        print()
        print("="*60)
        print(f"Successfully scraped {len(translations)} translations")
        print("="*60)

        return translations

    def save_to_json(self, translations: Dict[str, str], output_path: str):
        """Save translations to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved to {output_path}")

    def update_python_file(self, translations: Dict[str, str], output_path: str):
        """Generate Python dictionary for poe_translations.py"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('"""Auto-generated Korean-English skill translations"""\n\n')
            f.write('SKILL_NAMES_SCRAPED = {\n')

            for korean, english in sorted(translations.items()):
                f.write(f'    "{korean}": "{english}",\n')

            f.write('}\n')

        print(f"✅ Saved Python dict to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Scrape Korean translations from poedb.tw')
    parser.add_argument('--output', type=str, default='poe_translations_scraped.json',
                       help='Output JSON file path')
    parser.add_argument('--python', type=str, default='poe_translations_scraped.py',
                       help='Output Python file path')

    args = parser.parse_args()

    scraper = POEDBScraper()
    translations = scraper.scrape_all_skills()

    if translations:
        scraper.save_to_json(translations, args.output)
        scraper.update_python_file(translations, args.python)

        print()
        print("Sample translations:")
        for korean, english in list(translations.items())[:10]:
            print(f"  {korean} -> {english}")
    else:
        print("❌ No translations scraped")
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
