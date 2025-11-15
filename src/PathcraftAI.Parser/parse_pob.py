#!/usr/bin/env python3
"""Parse POB link and extract build information"""

import requests
import base64
import zlib
import xml.etree.ElementTree as ET

pob_url = "https://pobb.in/L_PjVQbio_WZ"

print(f"Fetching POB from: {pob_url}")
print("=" * 80)

# Fetch raw data
response = requests.get(f"{pob_url}/raw")
raw_data = response.text

print(f"[OK] Fetched {len(raw_data)} bytes")

# Decode base64
try:
    decoded = base64.urlsafe_b64decode(raw_data)
    print(f"[OK] Decoded base64: {len(decoded)} bytes")
except Exception as e:
    print(f"[ERROR] Base64 decode failed: {e}")
    exit(1)

# Decompress
try:
    xml_data = zlib.decompress(decoded)
    print(f"[OK] Decompressed XML: {len(xml_data)} bytes")
except Exception as e:
    print(f"[ERROR] Decompression failed: {e}")
    exit(1)

# Parse XML
try:
    root = ET.fromstring(xml_data)
    print(f"[OK] Parsed XML root: {root.tag}")
except Exception as e:
    print(f"[ERROR] XML parse failed: {e}")
    exit(1)

print()
print("=" * 80)
print("BUILD INFORMATION")
print("=" * 80)

# Extract build info
build = root.find('Build')
if build is not None:
    # Build name
    build_name = build.get('name', 'Unknown')
    print(f"Build Name: {build_name}")

    # Level
    level = build.get('level', 'Unknown')
    print(f"Level: {level}")

    # Class/Ascendancy
    class_name = build.get('className', 'Unknown')
    ascendancy = build.get('ascendClassName', 'Unknown')
    print(f"Class: {class_name}")
    print(f"Ascendancy: {ascendancy}")

    # Main skill
    main_socket = build.get('mainSocketGroup', '1')
    print(f"Main Socket Group: {main_socket}")

# Find all skills
print()
print("SKILLS:")
skills_section = root.find('.//Skills')
if skills_section is not None:
    for skill_set in skills_section.findall('SkillSet'):
        skill_set_id = skill_set.get('id', '?')
        for skill in skill_set.findall('Skill'):
            skill_enabled = skill.get('enabled', 'true')
            skill_label = skill.get('label', '')
            slot = skill.get('slot', '')

            # Get gems in this skill
            gems = []
            for gem in skill.findall('Gem'):
                gem_name = gem.get('nameSpec', gem.get('skillId', ''))
                gem_level = gem.get('level', '1')
                gem_quality = gem.get('quality', '0')
                gems.append(f"{gem_name} (L{gem_level}/Q{gem_quality})")

            if gems and skill_enabled == 'true':
                print(f"  [{skill_set_id}] {skill_label or slot}:")
                for gem in gems:
                    print(f"    - {gem}")

# Find account name if available
print()
print("=" * 80)
print("ACCOUNT INFO:")
notes = build.get('notes', '') if build is not None else ''
if 'account' in notes.lower() or 'profile' in notes.lower():
    print(f"Notes: {notes[:200]}")
else:
    print("No account info found in build notes")

# Try to find it in other places
import re
for element in root.iter():
    text = element.text or ''
    if 'pathofexile.com/account' in text or '/view-profile/' in text:
        # Try to extract account name
        match = re.search(r'/account/view-profile/([^/\s\"\']+)', text)
        if match:
            account_name = match.group(1)
            print(f"\n[FOUND] Account Name: {account_name}")
            break

print()

# Extract passive tree
print("=" * 80)
print("PASSIVE TREE ANALYSIS:")
print("=" * 80)

tree_section = root.find('.//Tree')
if tree_section is not None:
    # Get active spec
    active_spec = tree_section.get('activeSpec', '1')

    # Find the active spec
    for spec in tree_section.findall('Spec'):
        spec_id = spec.get('id', '')
        if spec_id == active_spec:
            nodes = spec.get('nodes', '')
            if nodes:
                node_list = nodes.split(',')
                print(f"Total Passive Points: {len(node_list)}")
                print(f"Active Spec ID: {spec_id}")
                print(f"\nPassive Node IDs (first 50):")
                print(', '.join(node_list[:50]))

                # Count ascendancy nodes (usually > 60000)
                ascendancy_nodes = [n for n in node_list if int(n) > 60000]
                print(f"\nAscendancy Points: {len(ascendancy_nodes)}/8")
                print(f"Ascendancy Node IDs: {', '.join(ascendancy_nodes)}")

# Extract keystones and notables
print()
print("KEYSTONES & NOTABLES:")

# POB doesn't store names directly, we need to match node IDs
# Let's at least get the structure
tree_url = tree_section.get('treeVersion', '') if tree_section is not None else ''
print(f"Tree Version: {tree_url}")

print()
