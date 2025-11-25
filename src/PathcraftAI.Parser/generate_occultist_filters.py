#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Occultist build filters from POB links"""

import urllib.request
import base64
import zlib
import xml.etree.ElementTree as ET
import re
import sys
import json
from datetime import datetime
from pathlib import Path

def load_neversink_rules():
    """Load NeverSink filter rules from JSON"""
    json_path = Path(__file__).parent / "data" / "neversink_filter_rules.json"
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def load_neversink_base_filter():
    """Load NeverSink base filter file"""
    # Try multiple possible locations
    possible_paths = [
        Path(r"d:\Pathcraft-AI\Leveling 3.27 filter.filter"),
        Path(__file__).parent.parent.parent / "Leveling 3.27 filter.filter",
    ]

    for path in possible_paths:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()

    return None

def fetch_pob(pob_id):
    url = f'https://pobb.in/pob/{pob_id}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = response.read()
        decoded = base64.urlsafe_b64decode(data)
        return zlib.decompress(decoded).decode('utf-8')

def extract_flask_base(name):
    """Extract base type from flask name (remove prefixes/suffixes)"""
    # Flask base types
    flask_bases = [
        "Divine Life Flask", "Eternal Life Flask", "Hallowed Life Flask", "Sanctified Life Flask",
        "Divine Mana Flask", "Eternal Mana Flask", "Hallowed Mana Flask",
        "Quicksilver Flask", "Granite Flask", "Jade Flask", "Quartz Flask",
        "Amethyst Flask", "Ruby Flask", "Sapphire Flask", "Topaz Flask",
        "Diamond Flask", "Basalt Flask", "Stibnite Flask", "Sulphur Flask",
        "Silver Flask", "Bismuth Flask", "Aquamarine Flask", "Corundum Flask",
        "Gold Flask"
    ]

    for base in flask_bases:
        if base in name:
            return base
    return name

def parse_items(xml_data):
    root = ET.fromstring(xml_data)
    items_elem = root.find('Items')

    uniques = set()
    base_types = set()

    for item in items_elem.findall('Item'):
        item_text = item.text or ''

        # Parse rarity
        rarity_match = re.search(r'Rarity: (\w+)', item_text)
        if not rarity_match:
            continue
        rarity = rarity_match.group(1)

        # Parse base type
        lines = [l.strip() for l in item_text.strip().split('\n') if l.strip()]
        base_type = None

        for i, line in enumerate(lines):
            if line.startswith('Rarity:'):
                # For unique: name is next line, base type is after
                if rarity == 'UNIQUE' and i + 2 < len(lines):
                    base_type = lines[i + 2]
                # For rare: name is next, base type is after
                elif rarity == 'RARE' and i + 2 < len(lines):
                    base_type = lines[i + 2]
                # For magic/normal: base type is next
                elif i + 1 < len(lines):
                    base_type = lines[i + 1]
                break

        if base_type:
            # Clean base type
            base_type = re.sub(r'^(Superior |Synthesised |Fractured )', '', base_type)

            # Extract flask base type (remove prefix/suffix mods)
            if 'Flask' in base_type:
                base_type = extract_flask_base(base_type)

            # Fix Two-Stone Ring variants - remove element specifier
            if 'Two-Stone Ring' in base_type:
                base_type = 'Two-Stone Ring'

            if rarity == 'UNIQUE':
                uniques.add(base_type)
            base_types.add(base_type)

    return list(uniques), list(base_types)

def generate_filter(name, uniques, base_types, strictness, sound_dir='sounds/ko'):
    """Generate filter with NeverSink base + build-specific rules on top"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Load NeverSink base filter
    neversink_base = load_neversink_base_filter()

    lines = [
        '#' + '=' * 80,
        '# PathcraftAI Build Filter',
        '# Based on NeverSink with POB-specific highlighting',
        '#' + '=' * 80,
        f'# STRICTNESS: {strictness}',
        f'# GENERATED: {now}',
        '#' + '=' * 80,
        '',
        '# ' + '=' * 40,
        '# YOUR BUILD ITEMS - HIGHEST PRIORITY',
        '# (These rules override NeverSink below)',
        '# ' + '=' * 40,
        '',
    ]

    # Unique items
    if uniques:
        unique_str = ' '.join(f'"{u}"' for u in uniques)
        lines.extend([
            '# Build Unique Items - EXACT MATCH (Cyan/Magenta highlight)',
            'Show',
            '    Rarity Unique',
            f'    BaseType == {unique_str}',
            '    SetFontSize 45',
            '    SetTextColor 0 255 255 255',
            '    SetBorderColor 255 0 255 255',
            '    SetBackgroundColor 75 0 130 255',
            f'    CustomAlertSound "{sound_dir}/build_unique.mp3"',
            '    PlayEffect Purple',
            '    MinimapIcon 0 Purple Star',
            '',
        ])

    # Rare base types for crafting
    rare_bases = [b for b in base_types if b not in uniques]
    if rare_bases:
        base_str = ' '.join(f'"{b}"' for b in rare_bases)
        lines.extend([
            '# Build Rare/Magic Base Types - For crafting upgrades',
            'Show',
            f'    BaseType == {base_str}',
            '    Rarity <= Rare',
            '    ItemLevel >= 82',
            '    SetFontSize 45',
            '    SetTextColor 255 150 255 255',
            '    SetBorderColor 255 100 255 255',
            '    SetBackgroundColor 60 0 60 255',
            f'    CustomAlertSound "{sound_dir}/build_base.mp3"',
            '    PlayEffect Pink',
            '    MinimapIcon 0 Pink Diamond',
            '',
        ])

    # Influenced items
    all_bases = ' '.join(f'"{b}"' for b in base_types)
    lines.extend([
        '# Build Base Types with Influence - VERY IMPORTANT',
        'Show',
        '    HasInfluence Shaper Elder Crusader Redeemer Hunter Warlord',
        f'    BaseType == {all_bases}',
        '    Rarity <= Rare',
        '    SetFontSize 45',
        '    SetTextColor 255 255 0 255',
        '    SetBorderColor 255 200 0 255',
        '    SetBackgroundColor 100 75 0 255',
        f'    CustomAlertSound "{sound_dir}/influenced.mp3"',
        '    PlayEffect Yellow',
        '    MinimapIcon 0 Yellow Star',
        '',
    ])

    # High ilvl bases
    lines.extend([
        '# Build Base Types - High Item Level (82+)',
        'Show',
        f'    BaseType == {all_bases}',
        '    ItemLevel >= 82',
        '    Rarity <= Rare',
        '    SetFontSize 42',
        '    SetTextColor 255 255 119 255',
        '    SetBorderColor 255 255 0 255',
        '    SetBackgroundColor 60 60 0 255',
        '    PlayAlertSound 2 250',
        '    PlayEffect Yellow',
        '    MinimapIcon 1 Yellow Diamond',
        '',
    ])

    # Normal ilvl bases
    lines.extend([
        '# Build Base Types - Normal Item Level (75+)',
        'Show',
        f'    BaseType == {all_bases}',
        '    ItemLevel >= 75',
        '    Rarity <= Rare',
        '    SetFontSize 38',
        '    SetTextColor 200 200 100 255',
        '    SetBorderColor 200 200 0 255',
        '    MinimapIcon 2 Yellow Circle',
        '',
    ])

    # Add separator before NeverSink base
    lines.extend([
        '',
        '#' + '=' * 80,
        '# NEVERSINK BASE FILTER',
        '# All rules below are from NeverSink 3.27 Leveling filter',
        '#' + '=' * 80,
        '',
    ])

    # Add NeverSink base filter
    if neversink_base:
        # Remove the header comments from NeverSink to avoid confusion
        ns_lines = neversink_base.split('\n')
        # Skip initial comment block
        skip_header = True
        for line in ns_lines:
            if skip_header:
                if line.startswith('Show') or line.startswith('Hide'):
                    skip_header = False
                    lines.append(line)
            else:
                lines.append(line)
    else:
        lines.extend([
            '# WARNING: NeverSink base filter not found!',
            '# Please place "Leveling 3.27 filter.filter" in the project root',
            '',
        ])

    return '\n'.join(lines)

def main():
    # Process all three POBs
    pobs = [
        ('Occultist_Leveling', 'QLh2nmnu_A0z', 1),
        ('Occultist_MidMap', 'mtPM-uyatqSH', 2),
        ('Occultist_Endgame', 'ozmUjt87nmuS', 3),
    ]

    poe_folder = r'C:\Users\User\Documents\My Games\Path of Exile'

    for name, pob_id, strictness in pobs:
        print(f'Fetching {name}...', file=sys.stderr)
        xml = fetch_pob(pob_id)
        uniques, base_types = parse_items(xml)
        print(f'  {len(uniques)} uniques, {len(base_types)} base types', file=sys.stderr)

        filter_content = generate_filter(name, uniques, base_types, strictness)

        # Save to POE folder
        filepath = f'{poe_folder}\\{name}.filter'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(filter_content)
        print(f'  Saved: {filepath}', file=sys.stderr)

    print('Done!', file=sys.stderr)

if __name__ == '__main__':
    main()
