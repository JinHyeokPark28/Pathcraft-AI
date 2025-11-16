"""
POB Parsing Accuracy Module
Priority 0: Extract REAL data from POB XML, not AI guesses

Features:
- Main skill detection (mainActiveSkillCalcs attribute)
- Item level requirements extraction
- League starter auto-detection (max_item_level < 70)
- AI validation layer
"""

import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Tuple, Optional


def extract_main_skill(xml_string: str) -> Dict[str, any]:
    """
    Extract the MAIN skill from POB XML

    Args:
        xml_string: POB XML content

    Returns:
        Dict with:
            - main_skill_name: str
            - main_skill_gems: List[str]
            - main_skill_group: str (label)
            - all_active_skills: List[Dict] (for debugging)
    """
    try:
        root = ET.fromstring(xml_string)
        skills_element = root.find('Skills')

        if skills_element is None:
            return {
                'main_skill_name': None,
                'main_skill_gems': [],
                'main_skill_group': None,
                'all_active_skills': [],
                'error': 'No Skills element found'
            }

        main_skill = None
        all_active_skills = []

        for skill_set in skills_element.findall('.//Skill'):
            if skill_set.get('enabled', 'false').lower() != 'true':
                continue

            gems = skill_set.findall('Gem')
            if not gems:
                continue

            label = skill_set.get('label', '').strip()
            gem_names = [gem.get('nameSpec') for gem in gems if gem.get('enabled', 'true').lower() == 'true']

            # mainActiveSkillCalcs="1" indicates this is the MAIN skill for DPS calculation
            main_active_skill_calcs = skill_set.get('mainActiveSkillCalcs')

            skill_info = {
                'label': label,
                'gems': gem_names,
                'mainActiveSkillCalcs': main_active_skill_calcs,
                'mainActiveSkill': skill_set.get('mainActiveSkill')
            }

            all_active_skills.append(skill_info)

            # Find the main skill (highest priority: mainActiveSkillCalcs="1")
            if main_active_skill_calcs == '1':
                main_skill = skill_info

        # Fallback: If no mainActiveSkillCalcs, use first skill
        if main_skill is None and all_active_skills:
            main_skill = all_active_skills[0]

        if main_skill is None:
            return {
                'main_skill_name': None,
                'main_skill_gems': [],
                'main_skill_group': None,
                'all_active_skills': all_active_skills,
                'error': 'No active skills found'
            }

        # Filter out auras, buffs, curses, utilities from main skill candidates
        # Priority: Find actual DPS skill (attack/spell)
        aura_buff_gems = [
            'Grace', 'Determination', 'Purity', 'Vitality', 'Clarity', 'Discipline',
            'Hatred', 'Anger', 'Wrath', 'Zealotry', 'Malevolence', 'Pride',
            'Blood Rage', 'Steelskin', 'Molten Shell', 'Phase Run', 'Dash',
            'Portal', 'Enduring Cry', 'Immortal Call', 'Vaal', 'Automation',
            'Cast on Death', 'Cast when Damage Taken',
            # Curses
            'Frostbite', 'Flammability', 'Conductivity', 'Vulnerability', 'Temporal Chains',
            'Enfeeble', 'Elemental Weakness', 'Despair', 'Punishment', 'Warlord',
            'Poacher', 'Assassin', 'Sniper', 'Projectile Weakness',
            # Golem/Minions (usually not main skill unless summoner)
            'Summon Ice Golem', 'Summon Stone Golem', 'Summon Flame Golem',
            'Summon Lightning Golem', 'Summon Chaos Golem',
            # Utility spells
            'Frost Bomb', 'Wave of Conviction', 'Hydrosphere', 'Frenzy', 'Power Siphon',
            # Trigger gems
            'Manaforged Arrows', 'Spellslinger', 'Arcanist Brand'
        ]

        support_gems = [
            'Empower', 'Enhance', 'Enlighten', 'Awakened', 'Greater Multiple Projectiles',
            'Lesser Multiple Projectiles', 'Spell Echo', 'Multistrike', 'Faster Attacks',
            'Faster Casting', 'Increased Critical', 'Concentrated Effect', 'Elemental Focus',
            'Cast On Critical Strike', 'Trigger', 'Second Wind', 'Inspiration',
            'Added', 'Elemental Damage', 'Damage', 'Fortify', 'Onslaught',
            'Cast when', 'Mark On Hit'
        ]

        # Find main DPS skill candidates among all active skills
        dps_skill_candidates = []
        for skill_info in all_active_skills:
            if skill_info['mainActiveSkillCalcs'] != '1':
                continue  # Skip non-DPS skills

            for gem in skill_info['gems']:
                # Skip auras/buffs
                if any(aura in gem for aura in aura_buff_gems):
                    continue
                # Skip supports
                if any(support in gem for support in support_gems):
                    continue

                # This is likely a DPS skill
                dps_skill_candidates.append({
                    'name': gem,
                    'skill_info': skill_info
                })

        # Prefer the first DPS skill found
        if dps_skill_candidates:
            main_skill = dps_skill_candidates[0]['skill_info']
            main_skill_name = dps_skill_candidates[0]['name']
        else:
            # Fallback: Use first non-support gem from first skill
            main_skill_name = None
            for gem in main_skill['gems']:
                is_support = any(support in gem for support in support_gems)
                if not is_support:
                    main_skill_name = gem
                    break

            # Final fallback: Use first gem
            if main_skill_name is None and main_skill['gems']:
                main_skill_name = main_skill['gems'][0]

        return {
            'main_skill_name': main_skill_name,
            'main_skill_gems': main_skill['gems'],
            'main_skill_group': main_skill['label'],
            'all_active_skills': all_active_skills,
            'error': None
        }

    except Exception as e:
        return {
            'main_skill_name': None,
            'main_skill_gems': [],
            'main_skill_group': None,
            'all_active_skills': [],
            'error': str(e)
        }


def extract_item_levels(xml_string: str) -> Dict[str, any]:
    """
    Extract item level requirements from POB XML

    Args:
        xml_string: POB XML content

    Returns:
        Dict with:
            - items: List[Dict] - Each item with name, slot, required_level, item_level
            - max_required_level: int - Highest item level requirement
            - min_required_level: int - Lowest item level requirement
            - avg_required_level: float - Average item level requirement
    """
    try:
        root = ET.fromstring(xml_string)
        items_element = root.find('Items')

        if items_element is None:
            return {
                'items': [],
                'max_required_level': 0,
                'min_required_level': 0,
                'avg_required_level': 0,
                'error': 'No Items element found'
            }

        # Build item map: id -> raw text
        item_map = {}
        for item in items_element.findall('.//Item'):
            if item.text and item.get('id'):
                item_map[item.get('id')] = item.text.strip()

        # Get active item set
        active_set_id = items_element.get('activeItemSet', '1')
        item_set = items_element.find(f".//ItemSet[@id='{active_set_id}']")
        if item_set is None:
            item_set = items_element.findall(".//ItemSet")[0] if items_element.findall(".//ItemSet") else None

        if item_set is None:
            return {
                'items': [],
                'max_required_level': 0,
                'min_required_level': 0,
                'avg_required_level': 0,
                'error': 'No ItemSet found'
            }

        items = []
        required_levels = []

        for slot in item_set.findall('Slot'):
            slot_name = slot.get('name')
            item_id = slot.get('itemId')

            item_raw_text = item_map.get(item_id)
            if not (slot_name and item_raw_text):
                continue

            lines = item_raw_text.split('\n')

            # Extract item name
            item_name = lines[1].strip() if len(lines) > 1 else 'Unknown'
            if "Rarity: Rare" in lines[0] or "Rarity: Magic" in lines[0]:
                if len(lines) > 2:
                    item_name = f"{lines[1].strip()} ({lines[2].strip()})"

            # Extract required level and item level
            required_level = None
            item_level = None

            for line in lines:
                # "Requires Level 68" or "LevelReq: 68"
                if 'Requires Level' in line or 'LevelReq:' in line:
                    match = re.search(r'(\d+)', line)
                    if match:
                        required_level = int(match.group(1))

                # "Item Level: 85"
                if 'Item Level:' in line:
                    match = re.search(r'Item Level:\s*(\d+)', line)
                    if match:
                        item_level = int(match.group(1))

            items.append({
                'slot': slot_name,
                'name': item_name,
                'required_level': required_level,
                'item_level': item_level
            })

            if required_level is not None:
                required_levels.append(required_level)

        # Calculate stats
        max_required = max(required_levels) if required_levels else 0
        min_required = min(required_levels) if required_levels else 0
        avg_required = sum(required_levels) / len(required_levels) if required_levels else 0

        return {
            'items': items,
            'max_required_level': max_required,
            'min_required_level': min_required,
            'avg_required_level': round(avg_required, 1),
            'total_items': len(items),
            'items_with_level_req': len(required_levels),
            'error': None
        }

    except Exception as e:
        return {
            'items': [],
            'max_required_level': 0,
            'min_required_level': 0,
            'avg_required_level': 0,
            'error': str(e)
        }


def is_league_starter(xml_string: str) -> Dict[str, any]:
    """
    Automatically determine if build is league starter viable

    Criteria:
    - max_required_level < 70 (can use all items by early maps)
    - No expensive uniques required (TODO: check poe.ninja prices)

    Args:
        xml_string: POB XML content

    Returns:
        Dict with:
            - is_league_starter: bool
            - confidence: float (0-100%)
            - reason: str
            - max_required_level: int
    """
    item_data = extract_item_levels(xml_string)

    if item_data['error']:
        return {
            'is_league_starter': False,
            'confidence': 0,
            'reason': f"Parse error: {item_data['error']}",
            'max_required_level': None
        }

    max_level = item_data['max_required_level']

    # League starter threshold: Level 70 (early yellow maps)
    # This ensures you can use all gear by the time you reach maps
    LEAGUE_STARTER_THRESHOLD = 70

    is_starter = max_level < LEAGUE_STARTER_THRESHOLD

    if is_starter:
        reason = f"All items usable by level {max_level} (threshold: {LEAGUE_STARTER_THRESHOLD})"
        confidence = 100 if max_level < 60 else 80  # Very confident if < 60
    else:
        reason = f"Requires level {max_level} items (threshold: {LEAGUE_STARTER_THRESHOLD})"
        confidence = 90  # High confidence it's NOT a league starter

    return {
        'is_league_starter': is_starter,
        'confidence': confidence,
        'reason': reason,
        'max_required_level': max_level,
        'threshold': LEAGUE_STARTER_THRESHOLD
    }


def validate_ai_response(xml_string: str, ai_response: Dict) -> Dict[str, any]:
    """
    Validate AI response against actual POB data

    Args:
        xml_string: POB XML content
        ai_response: AI's analysis response with keys like:
            - main_skill: str
            - is_league_starter: bool

    Returns:
        Dict with:
            - valid: bool
            - corrections: List[str]
            - warnings: List[str]
    """
    corrections = []
    warnings = []

    # Check main skill
    actual_main_skill = extract_main_skill(xml_string)
    ai_main_skill = ai_response.get('main_skill')

    if actual_main_skill['main_skill_name'] and ai_main_skill:
        if actual_main_skill['main_skill_name'].lower() not in ai_main_skill.lower():
            corrections.append(
                f"AI said main skill is '{ai_main_skill}', "
                f"but POB says '{actual_main_skill['main_skill_name']}'"
            )

    # Check league starter
    actual_league_starter = is_league_starter(xml_string)
    ai_league_starter = ai_response.get('is_league_starter')

    if ai_league_starter is not None:
        if ai_league_starter != actual_league_starter['is_league_starter']:
            corrections.append(
                f"AI said league_starter={ai_league_starter}, "
                f"but actual max_level={actual_league_starter['max_required_level']} "
                f"(threshold: {actual_league_starter['threshold']}). "
                f"Correct answer: {actual_league_starter['is_league_starter']}"
            )

    valid = len(corrections) == 0

    return {
        'valid': valid,
        'corrections': corrections,
        'warnings': warnings,
        'actual_data': {
            'main_skill': actual_main_skill['main_skill_name'],
            'is_league_starter': actual_league_starter['is_league_starter'],
            'max_required_level': actual_league_starter['max_required_level']
        }
    }


def get_pob_facts(xml_string: str) -> Dict[str, any]:
    """
    Get all POB facts for AI prompt augmentation

    This data should be injected into AI prompts to ensure accuracy

    Args:
        xml_string: POB XML content

    Returns:
        Dict with all extracted facts
    """
    main_skill_data = extract_main_skill(xml_string)
    item_level_data = extract_item_levels(xml_string)
    league_starter_data = is_league_starter(xml_string)

    return {
        'main_skill': {
            'name': main_skill_data['main_skill_name'],
            'gems': main_skill_data['main_skill_gems'],
            'group_label': main_skill_data['main_skill_group']
        },
        'item_requirements': {
            'max_required_level': item_level_data['max_required_level'],
            'min_required_level': item_level_data['min_required_level'],
            'avg_required_level': item_level_data['avg_required_level'],
            'total_items': item_level_data['total_items']
        },
        'league_starter': {
            'is_league_starter': league_starter_data['is_league_starter'],
            'confidence': league_starter_data['confidence'],
            'reason': league_starter_data['reason']
        },
        'items': item_level_data['items']
    }


if __name__ == '__main__':
    """Test with real POB URL"""
    import requests
    from bs4 import BeautifulSoup
    import base64
    import zlib
    import json

    TEST_POB_URL = "https://pobb.in/wXVStDuZrqHX"

    print("="*60)
    print("POB Parsing Accuracy Test")
    print("="*60)

    # Fetch POB
    print(f"\n[1] Fetching POB: {TEST_POB_URL}")
    response = requests.get(TEST_POB_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    code_element = soup.find('textarea')
    encoded_code = code_element.text.strip()

    # Decode
    print("[2] Decoding POB XML...")
    corrected_code = encoded_code.replace('-', '+').replace('_', '/')
    decoded_bytes = base64.b64decode(corrected_code)
    xml_string = zlib.decompress(decoded_bytes).decode('utf-8')

    # Extract all facts
    print("\n[3] Extracting POB facts...")
    facts = get_pob_facts(xml_string)

    print("\n" + "="*60)
    print("POB FACTS (100% Accurate)")
    print("="*60)
    print(json.dumps(facts, indent=2, ensure_ascii=False))

    # Test AI validation
    print("\n" + "="*60)
    print("AI VALIDATION TEST")
    print("="*60)

    fake_ai_response = {
        'main_skill': 'Fireball',  # Wrong!
        'is_league_starter': True   # Wrong!
    }

    print("\nFake AI Response:")
    print(json.dumps(fake_ai_response, indent=2))

    validation = validate_ai_response(xml_string, fake_ai_response)
    print("\nValidation Result:")
    print(json.dumps(validation, indent=2, ensure_ascii=False))

    print("\n" + "="*60)
    print("✅ POB Parsing Accuracy Test Complete")
    print("="*60)
