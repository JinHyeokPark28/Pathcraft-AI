# -*- coding: utf-8 -*-
"""
Build Guide Generator with LLM Integration
실제 LLM을 사용하여 빌드 가이드 생성
"""

import json
import os
from datetime import datetime
from typing import Optional
import argparse

def generate_build_guide_with_llm(
    keyword: str,
    llm_provider: str = "openai",
    model: str = "gpt-4",
    api_key: Optional[str] = None,
    output_file: Optional[str] = None
) -> str:
    """
    LLM을 사용하여 빌드 가이드 생성

    Args:
        keyword: 빌드 키워드 (예: "Mageblood", "Death's Oath")
        llm_provider: LLM 제공자 ("openai", "anthropic", "mock")
        model: 사용할 모델 ("gpt-4", "claude-3-opus", etc.)
        api_key: API 키 (None이면 환경변수에서 읽음)
        output_file: 출력 파일 경로

    Returns:
        생성된 빌드 가이드 (markdown)
    """

    print("=" * 80)
    print("BUILD GUIDE GENERATOR WITH LLM")
    print("=" * 80)
    print(f"Keyword: {keyword}")
    print(f"LLM Provider: {llm_provider}")
    print(f"Model: {model}")
    print("=" * 80)
    print()

    # Step 1: 빌드 분석 프롬프트 생성
    print("[Step 1/3] Generating analysis prompt...")

    from build_analyzer import (
        load_reddit_builds,
        load_item_data,
        load_latest_patch_notes,
        create_build_analysis_prompt
    )

    # 데이터 로드
    builds = load_reddit_builds()
    item_data = load_item_data(keyword)
    patch_notes = load_latest_patch_notes(count=3)

    # 프롬프트 생성
    prompt = create_build_analysis_prompt(keyword, builds, item_data, patch_notes)

    # 임시 파일에 저장
    temp_prompt_file = f"temp_prompt_{keyword.replace(' ', '_')}.md"
    with open(temp_prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)

    print(f"[OK] Prompt generated: {len(prompt)} characters")
    print()

    # Step 2: LLM 호출
    print(f"[Step 2/3] Calling {llm_provider} {model}...")

    if llm_provider == "mock":
        # 테스트용 Mock 응답
        guide = generate_mock_guide(keyword, {})
        print("[OK] Mock guide generated (for testing)")

    elif llm_provider == "openai":
        guide = call_openai(prompt, model, api_key)

    elif llm_provider == "anthropic":
        guide = call_anthropic(prompt, model, api_key)

    else:
        raise ValueError(f"Unknown LLM provider: {llm_provider}")

    print()

    # Step 3: 결과 저장
    print("[Step 3/3] Saving build guide...")

    if output_file is None:
        output_file = f"build_guides/{keyword.replace(' ', '_')}_guide.md"

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(guide)

    print(f"[OK] Build guide saved to: {output_file}")
    print(f"     Length: {len(guide)} characters")
    print()

    # 임시 파일 삭제
    if os.path.exists(temp_prompt_file):
        os.remove(temp_prompt_file)

    return guide


def call_openai(prompt: str, model: str, api_key: Optional[str]) -> str:
    """OpenAI API 호출"""
    try:
        import openai
    except ImportError:
        print("[ERROR] openai package not installed. Run: pip install openai")
        return generate_mock_guide("", {})

    if api_key is None:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("[ERROR] OPENAI_API_KEY not found in environment")
            print("[INFO] Falling back to mock guide")
            return generate_mock_guide("", {})

    try:
        client = openai.OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a Path of Exile build guide expert. Create comprehensive, accurate build guides based on the provided data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        guide = response.choices[0].message.content
        print(f"[OK] OpenAI {model} response received")
        print(f"     Tokens used: {response.usage.total_tokens}")

        return guide

    except Exception as e:
        print(f"[ERROR] OpenAI API call failed: {e}")
        print("[INFO] Falling back to mock guide")
        return generate_mock_guide("", {})


def call_anthropic(prompt: str, model: str, api_key: Optional[str]) -> str:
    """Anthropic Claude API 호출"""
    try:
        import anthropic
    except ImportError:
        print("[ERROR] anthropic package not installed. Run: pip install anthropic")
        return generate_mock_guide("", {})

    if api_key is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print("[ERROR] ANTHROPIC_API_KEY not found in environment")
            print("[INFO] Falling back to mock guide")
            return generate_mock_guide("", {})

    try:
        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model=model,
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        guide = response.content[0].text
        print(f"[OK] Anthropic {model} response received")
        print(f"     Tokens used: ~{len(prompt.split()) + len(guide.split())}")

        return guide

    except Exception as e:
        print(f"[ERROR] Anthropic API call failed: {e}")
        print("[INFO] Falling back to mock guide")
        return generate_mock_guide("", {})


def generate_mock_guide(keyword: str, analysis_data: dict) -> str:
    """
    테스트용 Mock 빌드 가이드 생성
    실제 LLM 응답 형식을 시뮬레이션
    """

    guide = f"""# {keyword} Build Guide - Keepers League (3.27)

## Build Overview

This is a comprehensive build guide for **{keyword}** in the Keepers of the Flame league (Patch 3.27).

### Strengths
- High clear speed
- Strong single-target damage
- Good survivability with proper investment

### Weaknesses
- Requires specific unique items
- Can be expensive to fully min-max
- May struggle in early mapping without key items

### Recommended Ascendancy
Based on the ladder data analysis, the most popular ascendancy choices are:
1. **Pathfinder** (14% of builds)
2. **Ascendant** (14% of builds)
3. **Deadeye** (14% of builds)

### Budget Requirements
- **League Start**: 50-100 chaos (basic rare gear)
- **Mid-tier**: 200-500 chaos (some uniques)
- **End-game**: 5-20 divine (optimized gear)

---

## Passive Tree Recommendations

### Key Keystones
Based on analysis of top ladder builds:
- **Elemental Overload** or **Resolute Technique** (depending on build variant)
- **Acrobatics/Phase Acrobatics** (for evasion-based variants)
- **Point Blank** (for projectile builds)

### Cluster Jewels
Recommended cluster jewel notables:
- **Large Cluster**: Attack/Spell damage modifiers
- **Medium Cluster**: Life/ES, Ailment immunity
- **Small Cluster**: Resistance, Attributes

### Leveling Path
1. **Level 1-30**: Focus on life nodes and damage
2. **Level 30-60**: Pick up cluster jewel sockets
3. **Level 60+**: Fine-tune for end-game optimization

---

## Gem Setup

### Main Skill (6-Link Priority)

```
Main Skill - Support 1 - Support 2 - Support 3 - Support 4 - Support 5
```

**Alternatives**:
- For budget: Use 4-link or 5-link
- For min-max: Awakened versions of support gems

### Auras (3-4 total)

```
Aura 1 + Aura 2 + Enlighten (Level 3+)
Aura 3 (on life or mana)
```

### Utility Skills

```
Movement Skill - Faster Casting/Faster Attacks
Guard Skill (Molten Shell, Steelskin)
Curse (if not using curse on hit)
```

---

## Gear Progression

### League Start / Budget (< 50 chaos)

**Weapon**: Any rare with good DPS
**Body Armour**: Tabula Rasa or rare 5-link
**Helmet**: Rare with life + resistances
**Gloves**: Rare with life + resistances
**Boots**: Rare with life + movement speed + resistances
**Belt**: Rare with life + resistances
**Rings**: Rare with life + resistances
**Amulet**: Rare with life + damage stats

### Mid-tier (50-200 chaos)

**Weapon**: Upgrade to better rare or build-enabling unique
**Body Armour**: 6-link rare or unique
**Other slots**: Start adding build-specific uniques

### End-game BiS

Based on poe.ninja data and ladder analysis, key items include:
- **Mageblood** (~24,094 chaos / 213.60 divine) - If applicable
- Other build-specific uniques
- Well-rolled rares with optimal stats

---

## Patch 3.27 Keepers Optimization

### Recent Changes
Review patch notes 3.27.0c and 3.27.0b for:
- Skill balance changes
- Item modifier adjustments
- New league mechanics

### League Mechanic Integration
The Keepers of the Flame league introduces:
- New unique items to consider
- Specific encounter types that favor certain build styles
- Additional crafting opportunities

---

## Leveling Guide

### Act 1-4
**Main Skill**: Use generic leveling skill (varies by class)
**Key Quests**:
- Quicksilver Flask (Act 1 - The Tidal Island)
- All skill point quests

### Act 5-7
**Transition**: Start moving toward build-specific skills
**Resistances**: Maintain 75% elemental resistance cap

### Act 8-10
**Final Setup**: Switch to end-game skill setup
**Gear Check**: Upgrade to basic end-game gear

---

## Common Mistakes to Avoid

1. **Neglecting Resistances**: Always maintain 75% cap (or 76%+ with purity auras)
2. **Poor Flask Management**: Use instant recovery flasks and ailment immunity
3. **Ignoring Defense Layers**: Don't sacrifice all defense for damage
4. **Not Capping Accuracy** (for attack builds): Aim for 95%+ hit chance
5. **Skipping Quality on Gems**: 20% quality can make a significant difference

---

## Advanced Tips

### Min-Maxing Strategies
- Double-corrupt key items for additional power
- Use Forbidden Flame/Flesh for additional ascendancy notables
- Optimize cluster jewel stacking

### Endgame Content Suitability
- **Mapping**: ★★★★★ (5/5)
- **Bossing**: ★★★★☆ (4/5)
- **Delving**: ★★★★☆ (4/5)
- **Simulacrum**: ★★★☆☆ (3/5)

---

## Resources

- **POB Links**: Check build_data/reddit_builds/index.json for community builds
- **Ladder Characters**: See build_data/ladder_cache for top players
- **Price Tracking**: Use poe.ninja for real-time pricing

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**League**: Keepers (3.27 - Keepers of the Flame)
**Source**: PathcraftAI Build Guide Generator

*This is a mock guide for testing. For production, use real LLM integration.*
"""

    return guide


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build Guide Generator with LLM')
    parser.add_argument('--keyword', type=str, required=True, help='Build keyword')
    parser.add_argument('--llm', type=str, default='mock',
                       choices=['openai', 'anthropic', 'mock'],
                       help='LLM provider')
    parser.add_argument('--model', type=str, default='gpt-4',
                       help='Model name (gpt-4, claude-3-opus, etc.)')
    parser.add_argument('--api-key', type=str, default=None,
                       help='API key (optional, reads from env if not provided)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file path')

    args = parser.parse_args()

    generate_build_guide_with_llm(
        keyword=args.keyword,
        llm_provider=args.llm,
        model=args.model,
        api_key=args.api_key,
        output_file=args.output
    )
