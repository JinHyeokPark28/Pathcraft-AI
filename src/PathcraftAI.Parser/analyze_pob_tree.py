#!/usr/bin/env python3
"""Analyze POB passive tree and compare with current character"""

import requests
import base64
import zlib
import xml.etree.ElementTree as ET
import json

pob_url = "https://pobb.in/L_PjVQbio_WZ"

print("Fetching and parsing POB...")
response = requests.get(f"{pob_url}/raw")
decoded = base64.urlsafe_b64decode(response.text)
xml_data = zlib.decompress(decoded)
root = ET.fromstring(xml_data)

print("=" * 80)
print("POB PASSIVE TREE ANALYSIS")
print("=" * 80)

# Save full XML for inspection
with open('pob_full.xml', 'wb') as f:
    f.write(xml_data)
print("[DEBUG] Full XML saved to pob_full.xml")

# Find tree data
for elem in root.iter():
    if 'Tree' in elem.tag or 'tree' in elem.tag.lower():
        print(f"\nFound element: {elem.tag}")
        print(f"Attributes: {elem.attrib}")

        # Check for Spec elements
        for spec in elem:
            if 'Spec' in spec.tag:
                print(f"\n  Spec {spec.get('id', '?')}:")
                print(f"    Title: {spec.get('title', 'N/A')}")
                nodes = spec.get('nodes', '')
                if nodes:
                    node_list = nodes.split(',')
                    print(f"    Total nodes: {len(node_list)}")

                    # Separate by type
                    start_nodes = []
                    ascendancy = []
                    regular = []

                    for node in node_list:
                        n = int(node)
                        if n < 10:  # Class start
                            start_nodes.append(node)
                        elif n > 60000:  # Ascendancy
                            ascendancy.append(node)
                        else:
                            regular.append(node)

                    print(f"    Start node: {start_nodes}")
                    print(f"    Regular passives: {len(regular)}")
                    print(f"    Ascendancy points: {len(ascendancy)}/8")

                    # Get mastery effects
                    masteries = spec.get('masteryEffects', '')
                    if masteries:
                        mastery_list = masteries.split(',')
                        print(f"    Masteries allocated: {len(mastery_list)}")

# Now let's try to get your current tree from POE API
print()
print("=" * 80)
print("YOUR CURRENT PASSIVE TREE")
print("=" * 80)

try:
    with open('poe_token.json', 'r') as f:
        token_data = json.load(f)

    access_token = token_data['access_token']

    # Get character passives
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }

    import time
    time.sleep(2)  # Rate limit

    char_response = requests.get(
        'https://www.pathofexile.com/character-window/get-passive-skills',
        headers=headers,
        params={
            'character': 'Shovel_FuckingWand',
            'realm': 'pc'
        }
    )

    if char_response.status_code == 200:
        passive_data = char_response.json()

        hashes = passive_data.get('hashes', [])
        print(f"Your allocated passives: {len(hashes)}")
        print(f"Points used: {passive_data.get('points_used', 0)}")

        # Separate by type
        ascendancy = [h for h in hashes if h > 60000]
        regular = [h for h in hashes if h < 60000 and h > 10]

        print(f"Regular passives: {len(regular)}")
        print(f"Ascendancy points: {len(ascendancy)}/8")

        # Save for comparison
        with open('current_passives.json', 'w') as f:
            json.dump(passive_data, f, indent=2)
        print("\n[DEBUG] Your passives saved to current_passives.json")

    else:
        print(f"[ERROR] Failed to get passives: {char_response.status_code}")
        print(f"Response: {char_response.text[:200]}")

except Exception as e:
    print(f"[ERROR] Could not fetch current tree: {e}")

print()
