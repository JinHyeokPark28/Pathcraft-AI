#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze NeverSink filter and extract rules to JSON"""

import re
import json
from pathlib import Path

def parse_filter(filter_path):
    """Parse NeverSink filter file and extract rules"""

    with open(filter_path, 'r', encoding='utf-8') as f:
        content = f.read()

    result = {
        "currency_tiers": {},
        "divination_cards": {},
        "maps": {},
        "leveling": {},
        "quest_items": {},
        "links_sockets": {},
        "essences": {},
        "fragments": {},
        "unique_tiers": {}
    }

    # Extract currency tiers
    currency_patterns = [
        (r'\$tier->t1exalted.*?BaseType == ([^\n]+)', 't1_mirror_divine'),
        (r'\$tier->t2divine.*?BaseType == ([^\n]+)', 't2_exalted'),
        (r'\$tier->t3annul.*?BaseType == ([^\n]+)', 't3_annulment'),
        (r'\$tier->t4chaos.*?BaseType == ([^\n]+)', 't4_chaos'),
        (r'\$tier->t5alch.*?BaseType == ([^\n]+)', 't5_alchemy'),
        (r'\$tier->t6alt.*?BaseType == ([^\n]+)', 't6_alteration'),
        (r'\$tier->t7chance.*?BaseType == ([^\n]+)', 't7_chance'),
    ]

    for pattern, tier_name in currency_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            base_types = extract_base_types(match.group(1))
            result["currency_tiers"][tier_name] = base_types

    # Extract currency styling
    currency_style_patterns = [
        (r'\$type->currency \$tier->t1exalted.*?SetFontSize (\d+).*?SetTextColor ([^\n]+).*?SetBorderColor ([^\n]+).*?SetBackgroundColor ([^\n]+)', 't1_style'),
        (r'\$type->currency \$tier->t2divine.*?SetFontSize (\d+).*?SetTextColor ([^\n]+).*?SetBorderColor ([^\n]+).*?SetBackgroundColor ([^\n]+)', 't2_style'),
        (r'\$type->currency \$tier->t3annul.*?SetFontSize (\d+).*?SetTextColor ([^\n]+).*?SetBorderColor ([^\n]+).*?SetBackgroundColor ([^\n]+)', 't3_style'),
        (r'\$type->currency \$tier->t4chaos.*?SetFontSize (\d+).*?SetTextColor ([^\n]+).*?SetBorderColor ([^\n]+).*?SetBackgroundColor ([^\n]+)', 't4_style'),
    ]

    result["currency_styles"] = {}
    for pattern, style_name in currency_style_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            result["currency_styles"][style_name] = {
                "font_size": int(match.group(1)),
                "text_color": match.group(2).strip(),
                "border_color": match.group(3).strip(),
                "background_color": match.group(4).strip()
            }

    # Extract divination card tiers
    div_patterns = [
        (r'\$type->divination \$tier->t1\n.*?BaseType == ([^\n]+)', 't1_top'),
        (r'\$type->divination \$tier->t2\n.*?BaseType == ([^\n]+)', 't2_high'),
        (r'\$type->divination \$tier->t3\n.*?BaseType == ([^\n]+)', 't3_good'),
        (r'\$type->divination \$tier->t4\n.*?BaseType == ([^\n]+)', 't4_medium'),
        (r'\$type->divination \$tier->t5c\n.*?BaseType == ([^\n]+)', 't5_common'),
    ]

    for pattern, tier_name in div_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            base_types = extract_base_types(match.group(1))
            result["divination_cards"][tier_name] = base_types

    # Extract leveling flask rules
    flask_patterns = [
        (r'Life Flasks.*?BaseType "Small".*?AreaLevel <= (\d+)', 'life_flask_small'),
        (r'Life Flasks.*?BaseType "Medium".*?AreaLevel <= (\d+)', 'life_flask_medium'),
        (r'Life Flasks.*?BaseType "Large".*?AreaLevel <= (\d+)', 'life_flask_large'),
        (r'Life Flasks.*?BaseType "Greater".*?AreaLevel <= (\d+)', 'life_flask_greater'),
        (r'Life Flasks.*?BaseType "Grand".*?AreaLevel <= (\d+)', 'life_flask_grand'),
        (r'Life Flasks.*?BaseType "Giant".*?AreaLevel <= (\d+)', 'life_flask_giant'),
        (r'Life Flasks.*?BaseType "Colossal".*?AreaLevel <= (\d+)', 'life_flask_colossal'),
        (r'Life Flasks.*?BaseType "Sacred".*?AreaLevel <= (\d+)', 'life_flask_sacred'),
        (r'Life Flasks.*?BaseType "Hallowed".*?AreaLevel <= (\d+)', 'life_flask_hallowed'),
        (r'Life Flasks.*?BaseType "Sanctified".*?AreaLevel <= (\d+)', 'life_flask_sanctified'),
        (r'Life Flasks.*?BaseType "Divine".*?AreaLevel <= (\d+)', 'life_flask_divine'),
        (r'Life Flasks.*?BaseType "Eternal".*?AreaLevel <= (\d+)', 'life_flask_eternal'),
    ]

    result["leveling"]["life_flasks"] = {}
    for pattern, flask_name in flask_patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            result["leveling"]["life_flasks"][flask_name] = int(match.group(1))

    # Extract scroll styling
    scroll_match = re.search(
        r'BaseType == "Scroll of Wisdom".*?SetFontSize (\d+).*?SetTextColor ([^\n]+).*?SetBorderColor ([^\n]+).*?SetBackgroundColor ([^\n]+)',
        content, re.DOTALL
    )
    if scroll_match:
        result["leveling"]["scroll_style"] = {
            "font_size": int(scroll_match.group(1)),
            "text_color": scroll_match.group(2).strip(),
            "border_color": scroll_match.group(3).strip(),
            "background_color": scroll_match.group(4).strip()
        }

    # Extract quest item styling
    quest_match = re.search(
        r'Class == "Pantheon Souls" "Quest Items".*?SetFontSize (\d+).*?SetTextColor ([^\n]+).*?SetBorderColor ([^\n]+).*?SetBackgroundColor ([^\n]+)',
        content, re.DOTALL
    )
    if quest_match:
        result["quest_items"]["style"] = {
            "font_size": int(quest_match.group(1)),
            "text_color": quest_match.group(2).strip(),
            "border_color": quest_match.group(3).strip(),
            "background_color": quest_match.group(4).strip()
        }

    # Extract 6-link styling
    sixlink_match = re.search(
        r'LinkedSockets 6.*?Rarity Normal Magic Rare.*?SetFontSize (\d+).*?SetTextColor ([^\n]+).*?SetBorderColor ([^\n]+).*?SetBackgroundColor ([^\n]+)',
        content, re.DOTALL
    )
    if sixlink_match:
        result["links_sockets"]["six_link_style"] = {
            "font_size": int(sixlink_match.group(1)),
            "text_color": sixlink_match.group(2).strip(),
            "border_color": sixlink_match.group(3).strip(),
            "background_color": sixlink_match.group(4).strip()
        }

    # Extract gold tiers
    gold_patterns = [
        (r'BaseType == "Gold".*?StackSize >= 3001', 'gold_3000'),
        (r'BaseType == "Gold".*?StackSize >= 500', 'gold_500'),
        (r'BaseType == "Gold".*?StackSize >= 150', 'gold_150'),
        (r'BaseType == "Gold".*?StackSize >= 50', 'gold_50'),
    ]

    result["gold"] = {
        "tiers": {
            "3000+": {"stack_size": 3001, "font_size": 45, "effect": "Orange", "icon": "Yellow Cross"},
            "500+": {"stack_size": 500, "font_size": 45, "effect": "Orange Temp", "icon": "White Cross"},
            "150+": {"stack_size": 150, "font_size": 40, "icon": "Grey Cross"},
            "50+": {"stack_size": 50, "font_size": 40, "icon": "Grey Cross", "area_level": 68},
        }
    }

    # Extract essence tiers
    essence_match = re.search(
        r'BaseType "Muttering Essence of" "Wailing Essence of" "Weeping Essence of" "Whispering Essence of"',
        content
    )
    if essence_match:
        result["essences"]["leveling"] = [
            "Muttering Essence of",
            "Wailing Essence of",
            "Weeping Essence of",
            "Whispering Essence of"
        ]

    # Extract Harbinger currency
    harbinger_match = re.search(
        r'BaseType.*?"Harbinger\'s Shard".*?"Harbinger\'s Orb"',
        content
    )
    result["harbinger"] = {
        "shards": ["Harbinger's Shard", "Ancient Shard", "Annulment Shard", "Binding Shard", "Horizon Shard", "Exalted Shard"],
        "orbs": ["Harbinger's Orb", "Ancient Orb", "Orb of Horizons"]
    }

    return result


def extract_base_types(text):
    """Extract base types from a filter line"""
    # Find all quoted strings
    matches = re.findall(r'"([^"]+)"', text)
    return matches


def main():
    filter_path = Path(r"d:\Pathcraft-AI\Leveling 3.27 filter.filter")
    output_path = Path(r"d:\Pathcraft-AI\src\PathcraftAI.Parser\data\neversink_filter_rules.json")

    if not filter_path.exists():
        print(f"Filter not found: {filter_path}")
        return

    print("Analyzing NeverSink filter...")
    result = parse_filter(filter_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Saved to: {output_path}")

    # Print summary
    print("\n=== Summary ===")
    print(f"Currency tiers: {len(result['currency_tiers'])} tiers")
    print(f"Divination cards: {len(result['divination_cards'])} tiers")
    print(f"Life flask levels: {len(result['leveling'].get('life_flasks', {}))}")

    if result['currency_tiers']:
        for tier, items in result['currency_tiers'].items():
            print(f"  {tier}: {len(items)} items")


if __name__ == "__main__":
    main()
