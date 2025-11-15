#!/usr/bin/env python3
"""
스마트 빌드 분석기
- POB에서 키스톤, DPS, 방어 수치 추출
- POE.Ninja 실시간 가격으로 장비 평가
- 빌드 특성에 맞는 맞춤형 추천
"""

import requests
import base64
import zlib
import xml.etree.ElementTree as ET
import json
from pathlib import Path

# POB Keystone Node IDs (from POE passive tree data)
KEYSTONE_IDS = {
    '36634': 'Elemental Overload',
    '61834': 'Elemental Equilibrium',
    '11150': 'Point Blank',
    '2491': 'Resolute Technique',
    '55190': 'Perfect Agony',
    '6230': 'Vaal Pact',
    '32932': 'Chaos Inoculation',  # CI
    '26725': 'Eldritch Battery',    # EB
    '7960': 'Mind Over Matter',     # MoM
    '36678': 'Acrobatics',
    '61666': 'Iron Reflexes',
    '24970': 'Ghost Reaver',
    '11420': 'Avatar of Fire',
    '48768': 'Pain Attunement',     # Low Life
}

class SmartBuildAnalyzer:
    def __init__(self, pob_url, character_name=None):
        self.pob_url = pob_url
        self.character_name = character_name
        self.pob_data = {}
        self.keystones = []
        self.defense_type = None
        self.damage_type = None
        self.market_prices = {}

    def fetch_pob(self):
        """POB 데이터 가져오기"""
        print("[INFO] Fetching POB data...")
        response = requests.get(f"{self.pob_url}/raw")
        decoded = base64.urlsafe_b64decode(response.text)
        xml_data = zlib.decompress(decoded)
        self.root = ET.fromstring(xml_data)
        print("[OK] POB loaded\n")

    def analyze_keystones(self):
        """키스톤 패시브 확인"""
        print("[ANALYSIS] Keystones...")

        tree = self.root.find('.//Tree')
        if tree is None:
            print("⚠ No tree data found\n")
            return

        for spec in tree.findall('Spec'):
            nodes = spec.get('nodes', '')
            if nodes:
                node_list = nodes.split(',')

                for node_id in node_list:
                    if node_id in KEYSTONE_IDS:
                        keystone_name = KEYSTONE_IDS[node_id]
                        self.keystones.append(keystone_name)
                        print(f"  ✓ {keystone_name}")

        if not self.keystones:
            print("  No keystones allocated")
        print()

    def analyze_defense(self):
        """방어 메커니즘 분석"""
        print("🛡️ Analyzing Defense Type...")

        build = self.root.find('.//Build')
        if build is None:
            print("⚠ No build data\n")
            return

        # Check for CI
        if 'Chaos Inoculation' in self.keystones:
            self.defense_type = 'CI (Energy Shield)'
            print(f"  Defense: {self.defense_type}")
            print("  → Life: 1 (fixed)")
            print("  → Chaos Damage: IMMUNE")
            print()
            return

        # Check for Low Life
        if 'Pain Attunement' in self.keystones:
            self.defense_type = 'Low Life (ES + Life Reservation)'
            print(f"  Defense: {self.defense_type}")
            print()
            return

        # Check for MoM
        if 'Mind Over Matter' in self.keystones:
            self.defense_type = 'Life + MoM (Mana)'
            print(f"  Defense: {self.defense_type}")
            print("  → 30% damage taken from Mana")
            print()
            return

        # Default: Life-based
        self.defense_type = 'Life-based'
        print(f"  Defense: {self.defense_type}")
        print()

    def load_market_prices(self):
        """POE.Ninja 가격 데이터 로드"""
        print("💰 Loading Market Prices...")

        data_dir = Path('game_data')
        if not data_dir.exists():
            print("  ⚠ No market data found. Run: python poe_ninja_fetcher.py --collect")
            print()
            return

        # Load unique items
        unique_files = [
            'unique_weapons.json',
            'unique_armours.json',
            'unique_accessories.json'
        ]

        total_items = 0
        for filename in unique_files:
            filepath = data_dir / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    items = data.get('items', [])

                    for item in items:
                        name = item.get('name', '')
                        chaos_value = item.get('chaosValue', 0)
                        self.market_prices[name] = chaos_value

                    total_items += len(items)

        print(f"  ✓ Loaded {total_items} item prices")
        print()

    def recommend_pantheon(self):
        """빌드 특성에 맞는 판테온 추천"""
        print("=" * 80)
        print("🛡️ PANTHEON RECOMMENDATIONS (맞춤형)")
        print("=" * 80)
        print()

        # Major God
        print("Major God (주신):")
        print("  Soul of Lunaris - 맵핑용 (회피, 이동속도)")
        print("  Soul of Solaris - 보스용 (단일 대상 피해 감소)")
        print()

        # Minor God - 빌드에 따라 다름
        print("Minor God (부신):")

        if 'Chaos Inoculation' in self.keystones:
            print("  ⚠ You have CHAOS INOCULATION")
            print("  → Already IMMUNE to Chaos Damage!")
            print("  → DON'T use Soul of Shakari (카오스 면역 중복)")
            print()
            print("  ✓ RECOMMENDED:")
            print("    - Soul of Gruthkul (이동 중 물리 피해 감소)")
            print("    - Soul of Ralakesh (출혈 면역, 물리 피해 감소)")
        else:
            print("  ✓ RECOMMENDED:")
            print("    - Soul of Shakari (독 면역, 카오스 저항 +5%)")
            print("    - Soul of Gruthkul (이동 중 물리 피해 감소)")

        print()

    def analyze_current_gear(self):
        """현재 장비 분석 (POE API)"""
        if not self.character_name:
            return

        print("=" * 80)
        print(f"📦 YOUR CURRENT GEAR: {self.character_name}")
        print("=" * 80)
        print()

        try:
            with open('poe_token.json', 'r') as f:
                token_data = json.load(f)

            from poe_oauth import get_character_items
            items = get_character_items(token_data['access_token'], self.character_name)
            equipment = items['character']['equipment']

            uniques = [e for e in equipment if e.get('rarity') == 'Unique']

            total_value = 0
            print("Unique Items:")
            for item in uniques:
                name = item.get('name', '')
                slot = item.get('inventoryId', '')

                # Get price from POE.Ninja
                chaos_value = self.market_prices.get(name, 0)
                total_value += chaos_value

                if chaos_value > 0:
                    print(f"  {name} ({slot})")
                    print(f"    → Market Price: ~{chaos_value:.1f}c")
                else:
                    print(f"  {name} ({slot})")
                    print(f"    → Market Price: Unknown (check manually)")

            print()
            print(f"Total Gear Value: ~{total_value:.0f} chaos")

            if total_value > 1000:
                print("💎 High-value setup!")
            elif total_value > 100:
                print("⚡ Mid-tier setup")
            else:
                print("📈 Budget-friendly setup")

        except Exception as e:
            print(f"⚠ Could not fetch current gear: {e}")

        print()

    def run_analysis(self):
        """전체 분석 실행"""
        self.fetch_pob()
        self.analyze_keystones()
        self.analyze_defense()
        self.load_market_prices()
        self.recommend_pantheon()
        self.analyze_current_gear()

        print("=" * 80)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 80)


if __name__ == '__main__':
    analyzer = SmartBuildAnalyzer(
        pob_url="https://pobb.in/L_PjVQbio_WZ",
        character_name="Shovel_FuckingWand"
    )
    analyzer.run_analysis()