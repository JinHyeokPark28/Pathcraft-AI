#!/usr/bin/env python3
"""Quick character analysis without rate limit issues"""

import json
from poe_oauth import get_character_items

# Load cached token
with open('poe_token.json', 'r') as f:
    token_data = json.load(f)

access_token = token_data['access_token']
character_name = 'Shovel_FuckingWand'

print(f"Analyzing {character_name}...")
print("=" * 80)

# Get character items
data = get_character_items(access_token, character_name)
char = data['character']
equipment = char.get('equipment', [])

print(f"Character: {char['name']} Lv{char['level']} {char['class']}")
print(f"League: {char['league']}")
print(f"Total Items: {len(equipment)}")
print()

# Find unique items
uniques = [e for e in equipment if e.get('rarity') == 'Unique']
print(f"Unique Items ({len(uniques)}):")
for item in uniques:
    name = item.get('name', '')
    base = item.get('typeLine', '')
    slot = item.get('inventoryId', '')
    print(f"  - {name} ({base}) - {slot}")
print()

# Find 6-link
six_links = []
for item in equipment:
    sockets = item.get('sockets', [])
    if len(sockets) >= 6:
        # Check if all in same group
        groups = [s.get('group') for s in sockets]
        if len(set(groups)) == 1:
            six_links.append(item)

print(f"6-Link Items: {len(six_links)}")
for item in six_links:
    name = item.get('name', '') or item.get('typeLine', '')
    print(f"\n  {name}:")

    gems = item.get('socketedItems', [])
    print(f"  Socketed Gems ({len(gems)}):")

    active_gems = [g for g in gems if not g.get('support')]
    support_gems = [g for g in gems if g.get('support')]

    for gem in active_gems:
        print(f"    [ACTIVE] {gem.get('typeLine')}")

    for gem in support_gems:
        print(f"    [SUPPORT] {gem.get('typeLine')}")

print()
print("=" * 80)

# Look for other high-link items (4-5 link)
four_plus_links = []
for item in equipment:
    sockets = item.get('sockets', [])
    if 4 <= len(sockets) < 6:
        groups = [s.get('group') for s in sockets]
        max_link = max([groups.count(g) for g in set(groups)]) if groups else 0
        if max_link >= 4:
            four_plus_links.append((item, max_link))

if four_plus_links:
    print(f"4+ Link Items: {len(four_plus_links)}")
    for item, link_count in four_plus_links:
        name = item.get('name', '') or item.get('typeLine', '')
        gems = item.get('socketedItems', [])
        if gems:
            print(f"\n  {name} ({link_count}-link):")
            active = [g for g in gems if not g.get('support')]
            if active:
                print(f"    Main: {active[0].get('typeLine')}")

print()
print("=" * 80)
print("ALL SOCKETED GEMS:")
print("=" * 80)

for item in equipment:
    gems = item.get('socketedItems', [])
    if gems:
        slot = item.get('inventoryId', 'Unknown')
        name = item.get('name', '') or item.get('typeLine', '')
        sockets = len(item.get('sockets', []))

        print(f"\n[{slot}] {name} ({sockets} sockets):")

        active_gems = [g for g in gems if not g.get('support')]
        support_gems = [g for g in gems if g.get('support')]

        for gem in active_gems:
            level = gem.get('level', '?')
            print(f"  [ACTIVE] {gem.get('typeLine')} (Lv{level})")

        for gem in support_gems:
            level = gem.get('level', '?')
            print(f"  [SUPPORT] {gem.get('typeLine')} (Lv{level})")
