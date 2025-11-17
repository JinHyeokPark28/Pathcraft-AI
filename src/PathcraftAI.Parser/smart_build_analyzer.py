#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import sys
from pathlib import Path

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

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
        self.pob_stats = {}  # POB 통계 (DPS, Life, ES 등)

    def fetch_pob(self):
        """POB 데이터 가져오기"""
        print("[INFO] Fetching POB data...")
        response = requests.get(f"{self.pob_url}/raw")

        # Base64 padding 수정
        raw_data = response.text
        missing_padding = len(raw_data) % 4
        if missing_padding:
            raw_data += '=' * (4 - missing_padding)

        decoded = base64.urlsafe_b64decode(raw_data)
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

    def extract_pob_stats(self):
        """POB XML에서 통계 추출 (DPS, Life, ES, 저항 등)"""
        print("📊 Extracting POB Stats...")

        build = self.root.find('.//Build')
        if build is None:
            print("⚠ No build data\n")
            return

        # PlayerStat 섹션에서 stat들을 추출
        stats = {}
        for player_stat in build.findall('.//PlayerStat'):
            stat_name = player_stat.get('stat')
            stat_value = player_stat.get('value')

            if stat_name and stat_value:
                try:
                    # 숫자로 변환 시도
                    float_value = float(stat_value)

                    # infinity 체크
                    if float_value == float('inf') or float_value == float('-inf'):
                        stats[stat_name] = float_value
                    elif '.' in stat_value or 'e' in stat_value.lower():
                        stats[stat_name] = float_value
                    else:
                        stats[stat_name] = int(float_value)
                except (ValueError, TypeError, OverflowError):
                    stats[stat_name] = stat_value

        # 주요 통계만 self.pob_stats에 저장
        self.pob_stats = {
            'dps': stats.get('TotalDPS', 0),
            'combined_dps': stats.get('CombinedDPS', 0),
            'life': stats.get('Life', 0),
            'energy_shield': stats.get('EnergyShield', 0),
            'mana': stats.get('Mana', 0),
            'total_ehp': stats.get('TotalEHP', 0),
            'armour': stats.get('Armour', 0),
            'evasion': stats.get('Evasion', 0),
            'block': stats.get('EffectiveBlockChance', 0),
            'spell_block': stats.get('EffectiveSpellBlockChance', 0),
            'fire_res': stats.get('FireResist', 0),
            'cold_res': stats.get('ColdResist', 0),
            'lightning_res': stats.get('LightningResist', 0),
            'chaos_res': stats.get('ChaosResist', 0),
        }

        print("  ✓ Stats extracted")
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

    def display_pob_stats(self):
        """POB 통계를 보기 좋게 출력"""
        if not self.pob_stats:
            return

        print("=" * 80)
        print("📊 POB BUILD STATS")
        print("=" * 80)
        print()

        # DPS
        print("⚔️ OFFENSE:")
        dps = self.pob_stats.get('dps', 0)
        combined_dps = self.pob_stats.get('combined_dps', 0)

        if combined_dps > dps:
            print(f"  Total DPS:     {dps:,.0f}")
            print(f"  Combined DPS:  {combined_dps:,.0f} (includes minions/totems)")
        else:
            print(f"  Total DPS:     {dps:,.0f}")
        print()

        # Defense
        print("🛡️ DEFENSE:")
        life = self.pob_stats.get('life', 0)
        es = self.pob_stats.get('energy_shield', 0)
        ehp = self.pob_stats.get('total_ehp', 0)

        print(f"  Life:          {life:,}")
        print(f"  Energy Shield: {es:,}")
        if ehp > 0:
            print(f"  Total EHP:     {ehp:,.0f}")

        armour = self.pob_stats.get('armour', 0)
        evasion = self.pob_stats.get('evasion', 0)
        block = self.pob_stats.get('block', 0)
        spell_block = self.pob_stats.get('spell_block', 0)

        if armour > 0:
            print(f"  Armour:        {armour:,}")
        if evasion > 0:
            print(f"  Evasion:       {evasion:,}")
        if block > 0:
            print(f"  Block:         {block}%")
        if spell_block > 0:
            print(f"  Spell Block:   {spell_block}%")
        print()

        # Resistances
        print("🔥 RESISTANCES:")
        fire = self.pob_stats.get('fire_res', 0)
        cold = self.pob_stats.get('cold_res', 0)
        lightning = self.pob_stats.get('lightning_res', 0)
        chaos = self.pob_stats.get('chaos_res', 0)

        def res_status(value):
            if value >= 75:
                return "✓"
            elif value >= 0:
                return "⚠"
            else:
                return "✗"

        print(f"  Fire:          {fire}% {res_status(fire)}")
        print(f"  Cold:          {cold}% {res_status(cold)}")
        print(f"  Lightning:     {lightning}% {res_status(lightning)}")
        print(f"  Chaos:         {chaos}% {res_status(chaos)}")
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
        self.extract_pob_stats()  # 새로 추가: POB 통계 추출
        self.display_pob_stats()  # 새로 추가: 통계 출력
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