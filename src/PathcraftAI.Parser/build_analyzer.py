# -*- coding: utf-8 -*-

"""
Build Analyzer - 수집된 빌드 데이터를 종합 분석하여 LLM 프롬프트 생성
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

# 데이터 디렉토리
REDDIT_BUILDS_DIR = os.path.join(os.path.dirname(__file__), "build_data", "reddit_builds")
GAME_DATA_DIR = os.path.join(os.path.dirname(__file__), "game_data")
PATCH_NOTES_DIR = os.path.join(os.path.dirname(__file__), "patch_notes")

def load_reddit_builds() -> List[Dict]:
    """Reddit에서 수집한 빌드 로드"""
    index_file = os.path.join(REDDIT_BUILDS_DIR, "index.json")

    if not os.path.exists(index_file):
        return []

    with open(index_file, 'r', encoding='utf-8') as f:
        index = json.load(f)

    builds = []
    for build_info in index.get('builds', []):
        build_file = os.path.join(REDDIT_BUILDS_DIR, build_info['build_file'])
        if os.path.exists(build_file):
            with open(build_file, 'r', encoding='utf-8') as f:
                builds.append(json.load(f))

    return builds

def load_item_data(item_name: str) -> Optional[Dict]:
    """특정 아이템의 poe.ninja 데이터 로드"""
    # unique_armours, unique_weapons 등에서 검색
    categories = ['unique_armours', 'unique_weapons', 'unique_accessories', 'unique_jewels']

    for category in categories:
        file_path = os.path.join(GAME_DATA_DIR, f"{category}.json")
        if not os.path.exists(file_path):
            continue

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data.get('items', []):
            if item_name.lower() in item['name'].lower():
                return item

    return None

def load_latest_patch_notes(count: int = 3) -> List[Dict]:
    """최신 패치 노트 로드"""
    index_file = os.path.join(PATCH_NOTES_DIR, "patch_index.json")

    if not os.path.exists(index_file):
        return []

    with open(index_file, 'r', encoding='utf-8') as f:
        index = json.load(f)

    # 날짜 순으로 정렬
    sorted_patches = sorted(
        index.items(),
        key=lambda x: x[1]['date'],
        reverse=True
    )[:count]

    patches = []
    for patch_id, info in sorted_patches:
        file_path = os.path.join(PATCH_NOTES_DIR, info['file'])
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                patches.append(json.load(f))

    return patches

def analyze_passive_tree_patterns(builds: List[Dict]) -> Dict[str, Any]:
    """
    여러 빌드의 패시브 트리 패턴 분석

    Returns:
        공통 패턴 정보
    """
    passive_trees = []
    ascendancies = {}

    for build in builds:
        # Ascendancy 분포
        asc = build.get('meta', {}).get('ascendancy', 'Unknown')
        ascendancies[asc] = ascendancies.get(asc, 0) + 1

        # Passive tree URL 수집
        for stage in build.get('progression_stages', []):
            tree_url = stage.get('passive_tree_url', '')
            if tree_url:
                passive_trees.append({
                    'url': tree_url,
                    'build_name': build.get('meta', {}).get('build_name', ''),
                    'ascendancy': asc
                })

    return {
        'ascendancy_distribution': ascendancies,
        'passive_trees': passive_trees,
        'total_builds': len(builds)
    }

def analyze_gem_patterns(builds: List[Dict]) -> Dict[str, Any]:
    """여러 빌드의 젬 사용 패턴 분석"""
    main_skills = {}
    support_gems = {}

    for build in builds:
        for stage in build.get('progression_stages', []):
            for skill_name, setup in stage.get('gem_setups', {}).items():
                links = setup.get('links', '')

                # 첫 번째 젬을 메인 스킬로 간주
                gems = [g.strip() for g in links.split(' - ')]
                if gems:
                    main_skill = gems[0]
                    main_skills[main_skill] = main_skills.get(main_skill, 0) + 1

                    # 서포트 젬들 카운트
                    for support in gems[1:]:
                        support_gems[support] = support_gems.get(support, 0) + 1

    # 상위 젬들만 반환
    top_skills = sorted(main_skills.items(), key=lambda x: x[1], reverse=True)[:5]
    top_supports = sorted(support_gems.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        'main_skills': [{'name': name, 'count': count} for name, count in top_skills],
        'popular_supports': [{'name': name, 'count': count} for name, count in top_supports]
    }

def analyze_gear_patterns(builds: List[Dict]) -> Dict[str, Any]:
    """여러 빌드의 장비 패턴 분석"""
    unique_items = {}

    for build in builds:
        for stage in build.get('progression_stages', []):
            gear = stage.get('gear_recommendation', {})
            for slot, item_info in gear.items():
                item_name = item_info.get('name', '')
                if item_name and item_name not in ['None', 'Unknown']:
                    unique_items[item_name] = unique_items.get(item_name, 0) + 1

    # 상위 아이템
    top_items = sorted(unique_items.items(), key=lambda x: x[1], reverse=True)[:15]

    return {
        'popular_uniques': [{'name': name, 'count': count} for name, count in top_items]
    }

def create_build_analysis_prompt(
    keyword: str,
    builds: List[Dict],
    item_data: Optional[Dict],
    patch_notes: List[Dict]
) -> str:
    """
    LLM에게 전달할 종합 분석 프롬프트 생성

    Args:
        keyword: 검색 키워드 (예: "Death's Oath")
        builds: 수집된 빌드 데이터
        item_data: poe.ninja 아이템 데이터
        patch_notes: 최신 패치 노트

    Returns:
        LLM 프롬프트 (마크다운 형식)
    """
    # 패턴 분석
    passive_analysis = analyze_passive_tree_patterns(builds)
    gem_analysis = analyze_gem_patterns(builds)
    gear_analysis = analyze_gear_patterns(builds)

    # 프롬프트 생성
    prompt = f"""# Path of Exile Build Analysis Request

## User Request
사용자가 요청한 빌드: **{keyword}**

## Current League Context
- **League**: Keepers (3.27 - Keepers of the Flame)
- **Date**: {datetime.now().strftime('%Y-%m-%d')}
- **Analysis Date**: {datetime.now().isoformat()}

---

## 1. Item Data from poe.ninja

"""

    if item_data:
        prompt += f"""### {item_data['name']}
- **Base Type**: {item_data.get('baseType', 'N/A')}
- **Level Required**: {item_data.get('levelRequired', 'N/A')}
- **Current Price**: {item_data.get('chaosValue', 0):.1f} chaos / {item_data.get('divineValue', 0):.2f} divine
- **Listings**: {item_data.get('listingCount', 0)} items available
- **Price Trend**: {item_data.get('sparkLine', {}).get('totalChange', 0):.1f}% change (7 days)

**Explicit Modifiers:**
"""
        for mod in item_data.get('explicitModifiers', []):
            prompt += f"- {mod.get('text', '')}\n"

        if item_data.get('mutatedModifiers'):
            prompt += "\n**Foulborn (Mutated) Modifiers:**\n"
            for mod in item_data['mutatedModifiers']:
                prompt += f"- {mod.get('text', '')}\n"
    else:
        prompt += f"*No item data found for '{keyword}'*\n"

    prompt += f"""

---

## 2. Community Builds Analysis ({len(builds)} builds collected)

### Ascendancy Distribution
"""
    for asc, count in passive_analysis['ascendancy_distribution'].items():
        percentage = (count / passive_analysis['total_builds']) * 100
        prompt += f"- **{asc}**: {count} builds ({percentage:.1f}%)\n"

    prompt += f"""
### Popular Main Skills
"""
    for skill in gem_analysis['main_skills']:
        prompt += f"- **{skill['name']}**: {skill['count']} builds\n"

    prompt += f"""
### Popular Support Gems
"""
    for support in gem_analysis['popular_supports'][:5]:
        prompt += f"- **{support['name']}**: {support['count']} occurrences\n"

    prompt += f"""
### Popular Unique Items
"""
    for item in gear_analysis['popular_uniques'][:10]:
        prompt += f"- **{item['name']}**: {item['count']} builds\n"

    prompt += f"""

---

## 3. Passive Tree URLs

"""
    for i, tree in enumerate(passive_analysis['passive_trees'][:5], 1):
        prompt += f"""
### Build {i}: {tree['build_name']} ({tree['ascendancy']})
**Passive Tree**: [{tree['url'][:80]}...]({tree['url']})
"""

    prompt += f"""

---

## 4. Detailed Build Examples

"""
    for i, build in enumerate(builds[:3], 1):
        meta = build.get('meta', {})
        source = build.get('source', {})
        reddit = source.get('reddit_post', {})

        prompt += f"""
### Build {i}: {meta.get('build_name', 'Unknown')}

**Reddit Post**: [{reddit.get('title', 'N/A')[:60]}...]({reddit.get('url', '')})
- Author: {reddit.get('author', 'N/A')}
- Upvotes: {reddit.get('score', 0)}
- POB Link: {source.get('pob_link', 'N/A')}

**Class/Ascendancy**: {meta.get('class', 'N/A')} / {meta.get('ascendancy', 'N/A')}
**Level**: {meta.get('build_name', 'N/A').split('Lvl ')[-1] if 'Lvl' in meta.get('build_name', '') else 'N/A'}

**Gem Setups:**
"""
        for stage in build.get('progression_stages', [])[:1]:
            for skill_name, setup in list(stage.get('gem_setups', {}).items())[:3]:
                prompt += f"- **{skill_name}**: {setup.get('links', 'N/A')}\n"

        prompt += f"""
**Key Gear:**
"""
        for stage in build.get('progression_stages', [])[:1]:
            gear = stage.get('gear_recommendation', {})
            for slot, item_info in list(gear.items())[:5]:
                item_name = item_info.get('name', 'N/A')
                if item_name and item_name not in ['None', 'Unknown']:
                    prompt += f"- **{slot}**: {item_name}\n"

    prompt += f"""

---

## 5. Recent Patch Notes Context

"""
    for patch in patch_notes[:3]:
        prompt += f"""
### {patch.get('patch_id', 'N/A')} - {patch.get('date', 'N/A')}
- **Title**: {patch.get('title', 'N/A')}
- **URL**: {patch.get('official_url', 'N/A')}
- **Community Reaction**: {patch.get('community_reaction', {}).get('upvotes', 0)} upvotes, {patch.get('community_reaction', {}).get('comments', 0)} comments

"""

    prompt += f"""

---

## Analysis Task

Based on the above data, please provide a comprehensive build guide for **{keyword}** optimized for the **Keepers (3.27)** league with the following sections:

### 1. Build Overview
- Summary of the build concept
- Strengths and weaknesses
- Recommended ascendancy (based on community data)
- Leveling difficulty and budget requirements

### 2. Passive Tree Recommendations
- Analyze the collected passive tree URLs
- Identify common keystones and clusters
- Recommend the most efficient path
- Highlight any variations based on budget/playstyle

### 3. Gem Setup
- Main skill gem links (6L priority)
- Essential support gems
- Utility skills and auras
- Alternative gem options

### 4. Gear Progression
- League start / budget gear (< 50 chaos total)
- Mid-tier upgrades (50-200 chaos)
- End-game BiS items
- Current market prices from poe.ninja data

### 5. Patch 3.27 Optimization
- How recent balance changes affect this build
- Any new mechanics or items to leverage
- Recommended adjustments for Keepers league

### 6. Leveling Guide
- Act 1-10 skill progression
- When to transition to main skill
- Key items to look for while leveling

### 7. Common Mistakes to Avoid
- Based on community feedback and build data

Please format the response in clear markdown with bullet points and numbered lists for readability.
"""

    return prompt

def generate_build_recommendation(keyword: str = "Death's Oath") -> str:
    """
    빌드 추천 리포트 생성

    Args:
        keyword: 검색 키워드

    Returns:
        LLM 프롬프트 (마크다운)
    """
    print(f"[INFO] Generating build analysis for: {keyword}")

    # 데이터 로드
    print("[INFO] Loading Reddit builds...")
    builds = load_reddit_builds()
    print(f"[OK] Loaded {len(builds)} builds")

    print(f"[INFO] Loading item data for '{keyword}'...")
    item_data = load_item_data(keyword)
    if item_data:
        print(f"[OK] Found item: {item_data['name']}")
    else:
        print(f"[WARN] No item data found for '{keyword}'")

    print("[INFO] Loading recent patch notes...")
    patch_notes = load_latest_patch_notes(count=3)
    print(f"[OK] Loaded {len(patch_notes)} patch notes")

    # 프롬프트 생성
    print("[INFO] Creating analysis prompt...")
    prompt = create_build_analysis_prompt(keyword, builds, item_data, patch_notes)

    return prompt

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Build Analyzer')
    parser.add_argument('--keyword', type=str, required=True, help='Build keyword (e.g., "Death\'s Oath")')
    parser.add_argument('--output', type=str, help='Output file for the analysis prompt')

    args = parser.parse_args()

    # 분석 생성
    prompt = generate_build_recommendation(keyword=args.keyword)

    # 출력
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print(f"\n[OK] Analysis saved to: {args.output}")
    else:
        print("\n" + "=" * 80)
        print("ANALYSIS PROMPT FOR LLM:")
        print("=" * 80)
        print(prompt)
        print("=" * 80)
