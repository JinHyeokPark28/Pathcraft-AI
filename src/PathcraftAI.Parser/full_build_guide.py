#!/usr/bin/env python3
"""Complete build guide: Pantheon, Gear, Passives, Next Steps"""

import requests
import base64
import zlib
import xml.etree.ElementTree as ET
import json

pob_url = "https://pobb.in/L_PjVQbio_WZ"

print("=" * 80)
print("KINETIC BLAST ELEMENTALIST - COMPLETE BUILD GUIDE")
print("=" * 80)
print()

# Fetch POB
response = requests.get(f"{pob_url}/raw")
decoded = base64.urlsafe_b64decode(response.text)
xml_data = zlib.decompress(decoded)
root = ET.fromstring(xml_data)

# 1. PANTHEON
print("=" * 80)
print("1. PANTHEON POWERS")
print("=" * 80)

config_section = root.find('.//Config')
if config_section is not None:
    # Find pantheon selections
    major_god = None
    minor_god = None

    for input_elem in config_section.findall('Input'):
        name = input_elem.get('name', '')
        if 'pantheonMajorGod' in name.lower() or 'majorgod' in name.lower():
            major_god = input_elem.get('string', '')
        elif 'pantheonMinorGod' in name.lower() or 'minorgod' in name.lower():
            minor_god = input_elem.get('string', '')

    print(f"Major God: {major_god or 'Not specified'}")
    print(f"Minor God: {minor_god or 'Not specified'}")

    # Common recommendations for Wander builds
    if not major_god and not minor_god:
        print("\n[RECOMMENDED FOR WANDER]:")
        print("  Major God: Soul of Lunaris (mapping) or Soul of Solaris (bossing)")
        print("    - Lunaris: Avoid projectiles + movement speed")
        print("    - Solaris: Physical damage reduction when solo")
        print()
        print("  Minor God: Soul of Shakari (chaos res) or Soul of Gruthkul (phys mitigation)")
        print("    - Shakari: Poison immunity + chaos res")
        print("    - Gruthkul: Physical damage reduction while moving")

print()

# 2. GEAR REQUIREMENTS
print("=" * 80)
print("2. GEAR REQUIREMENTS (BiS = Best in Slot)")
print("=" * 80)

items_section = root.find('.//Items')
if items_section is not None:
    item_set = items_section.find(".//ItemSet[@useSecondWeaponSet='false']")
    if item_set is not None:
        print("\nBiS Items from POB:")

        for slot in ['Weapon 1', 'Weapon 2', 'Helmet', 'Body Armour', 'Gloves', 'Boots', 'Belt', 'Ring 1', 'Ring 2', 'Amulet']:
            item = item_set.find(f"./Slot[@name='{slot}']")
            if item is not None and len(item) > 0:
                # Get first item in slot
                gear = item[0]
                item_text = gear.text or ''

                # Parse item name from POB format
                lines = item_text.split('\n')
                if lines:
                    # Usually format is: Rarity: X\nName\nBase Type
                    name = 'Unknown'
                    base = ''
                    is_unique = False

                    for i, line in enumerate(lines):
                        if 'Rarity:' in line:
                            if 'Unique' in line:
                                is_unique = True
                        elif i > 0 and not line.startswith('Rarity:') and line.strip():
                            if not name or name == 'Unknown':
                                name = line.strip()
                            elif not base:
                                base = line.strip()
                                break

                    if is_unique:
                        print(f"\n  [{slot}] {name} (UNIQUE)")
                        print(f"    Base: {base}")
                    elif name != 'Unknown':
                        print(f"\n  [{slot}] {name}")

print()

# 3. YOUR CURRENT GEAR vs POB
print("=" * 80)
print("3. YOUR CURRENT GEAR (Shovel_FuckingWand)")
print("=" * 80)

try:
    with open('poe_token.json', 'r') as f:
        token_data = json.load(f)

    from poe_oauth import get_character_items
    items = get_character_items(token_data['access_token'], 'Shovel_FuckingWand')
    equipment = items['character']['equipment']

    print("\nCurrent Unique Items:")
    uniques = [e for e in equipment if e.get('rarity') == 'Unique']
    for item in uniques:
        name = item.get('name', '')
        slot = item.get('inventoryId', '')
        print(f"  ✓ {name} ({slot})")

    print(f"\nTotal Unique Items: {len(uniques)}")

except Exception as e:
    print(f"Could not fetch current gear: {e}")

print()

# 4. FLASK SETUP
print("=" * 80)
print("4. FLASK SETUP")
print("=" * 80)

if item_set is not None:
    print("\nRecommended Flasks from POB:")
    for i in range(1, 6):
        flask = item_set.find(f"./Slot[@name='Flask {i}']")
        if flask is not None and len(flask) > 0:
            flask_item = flask[0]
            flask_text = flask_item.text or ''
            lines = flask_text.split('\n')

            flask_name = 'Unknown'
            for line in lines:
                if line.strip() and 'Rarity:' not in line and not line.startswith('Flask'):
                    flask_name = line.strip()
                    break

            print(f"  Flask {i}: {flask_name}")

print()

# 5. ASCENDANCY ORDER
print("=" * 80)
print("5. ASCENDANCY PRIORITY (Elementalist)")
print("=" * 80)

print("""
Recommended Order:
  1st Lab (Normal):     Mastermind of Discord
  2nd Lab (Cruel):      Shaper of Flames
  3rd Lab (Merciless):  Heart of Destruction
  4th Lab (Eternal):    Shaper of Winter OR Bastion of Elements

Your Current: 6/8 points allocated
Next Step: Complete Uber Lab for remaining 2 points!
""")

# 6. PASSIVE TREE PRIORITIES
print("=" * 80)
print("6. PASSIVE TREE PRIORITIES (Lv69 → Lv94)")
print("=" * 80)

tree_section = root.find('.//Tree')
if tree_section is not None:
    for spec in tree_section.findall('Spec'):
        nodes = spec.get('nodes', '')
        if nodes:
            node_list = nodes.split(',')

            # Categorize nodes
            keystones = []
            ascendancy = [n for n in node_list if int(n) > 60000]

            # Common keystone node IDs (approximate)
            keystone_ids = {
                '36634': 'Elemental Overload',
                '61834': 'Elemental Equilibrium',
                '11150': 'Point Blank',
                '2491': 'Resolute Technique',
                '55190': 'Perfect Agony',
            }

            print("\nYour Path:")
            print(f"  Total Points Needed: {len(node_list)} nodes")
            print(f"  Current Points: 98 nodes")
            print(f"  Missing: {len(node_list) - 98} points (get from leveling)")

            print("\n  Focus Areas:")
            print("    1. Spell/Elemental Damage nodes near Witch start")
            print("    2. Crit Chance + Crit Multi nodes")
            print("    3. Life nodes (aim for 4000+ life)")
            print("    4. Jewel sockets (for Cluster Jewels)")
            print("    5. Projectile damage nodes")

print()

# 7. NEXT STEPS
print("=" * 80)
print("7. IMMEDIATE NEXT STEPS")
print("=" * 80)

print("""
Priority Order:

  🔥 CRITICAL (Do First):
    1. Complete Uber Lab → Get 8/8 Ascendancy points
    2. Level to 75+ → Unlock T6+ maps
    3. Cap Elemental Resistances (75% Fire/Cold/Lightning)

  ⚡ HIGH PRIORITY:
    4. Upgrade weapon (wand with high attack speed + crit)
    5. Get 6-link body armour with life + resists
    6. Find/buy The Taming ring (you already have! ✓)
    7. Add Cluster Jewels (check POB for sockets)

  💎 MEDIUM PRIORITY:
    8. Quality all gems to 20%
    9. Level gems to 20, then corrupt for 21/20
    10. Get better flasks with useful mods
    11. Allocate all Mastery points

  📈 LONG TERM:
    12. Farm currency for expensive uniques
    13. Min-max rare gear (life, resist, crit, attack speed)
    14. Get Awakened support gems
    15. Optimize passive tree based on POB DPS

  💰 Currency Farming:
    - Run T10+ maps
    - Use Kirac missions
    - Complete Atlas passive tree
    - Run Heist/Expedition for raw currency
""")

print()
print("=" * 80)
print("Good luck exile! 🎮")
print("=" * 80)
