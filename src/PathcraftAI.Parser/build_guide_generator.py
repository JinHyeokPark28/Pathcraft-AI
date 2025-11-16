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
    tier: str = "free",
    user_id: Optional[str] = None,
    output_file: Optional[str] = None
) -> str:
    """
    LLM을 사용하여 빌드 가이드 생성 (3-Tier 하이브리드 모델)

    Args:
        keyword: 빌드 키워드 (예: "Mageblood", "Death's Oath")
        llm_provider: LLM 제공자 ("openai", "anthropic", "gemini", "mock")
        model: 사용할 모델 ("gpt-4", "claude-3-opus", "gemini-pro", etc.)
        api_key: API 키 (Free tier: 사용자 키 필수, Premium/Expert: 무시됨)
        tier: 사용자 Tier ("free", "premium", "expert")
        user_id: 사용자 ID (Premium/Expert tier 필수)
        output_file: 출력 파일 경로

    Returns:
        생성된 빌드 가이드 (markdown)
    """

    print("=" * 80)
    print("BUILD GUIDE GENERATOR WITH LLM (3-Tier Hybrid Model)")
    print("=" * 80)
    print(f"Keyword: {keyword}")
    print(f"Tier: {tier.upper()}")
    print(f"LLM Provider: {llm_provider}")
    print(f"Model: {model}")
    if user_id:
        print(f"User ID: {user_id}")
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

    # Step 2: LLM 호출 (Tier별 분기)
    print(f"[Step 2/3] Calling {llm_provider} {model}... (Tier: {tier})")

    # Tier별 로직
    if tier == "free":
        # Free tier: 사용자 API 키 필수
        print("[Tier: FREE] Using user-provided API key")

        if llm_provider == "mock":
            guide = generate_mock_guide(keyword, {})
            print("[OK] Mock guide generated (for testing)")

        elif llm_provider == "openai":
            if api_key is None:
                raise ValueError(
                    "Free tier requires user API key.\n"
                    "Get OpenAI key: https://platform.openai.com/api-keys\n"
                    "Cost: ~$0.01/analysis"
                )
            guide = call_openai(prompt, model, api_key)

        elif llm_provider == "anthropic":
            if api_key is None:
                raise ValueError(
                    "Free tier requires user API key.\n"
                    "Get Claude key: https://console.anthropic.com/\n"
                    "Cost: ~$0.02/analysis"
                )
            guide = call_anthropic(prompt, model, api_key)

        elif llm_provider == "gemini":
            if api_key is None:
                raise ValueError(
                    "Free tier requires user API key.\n"
                    "Get Gemini key: https://makersuite.google.com/ (FREE!)\n"
                    "Cost: FREE (60 requests/day)"
                )
            guide = call_gemini(prompt, model, api_key)

        else:
            raise ValueError(f"Unknown LLM provider: {llm_provider}")

    elif tier == "premium":
        # Premium tier: 월 20회 크레딧, 우리 API 키 사용
        print("[Tier: PREMIUM] Using PathcraftAI API credits")

        if user_id is None:
            raise ValueError("Premium tier requires user_id")

        # 크레딧 체크
        credits_remaining = check_premium_credits(user_id)
        if credits_remaining <= 0:
            raise ValueError(
                f"Premium credits exhausted (20/20 used this month).\n"
                f"Credits reset on: {get_credit_reset_date(user_id)}\n"
                f"Upgrade to Expert tier for unlimited AI!\n"
                f"Or use Free tier with your own API key."
            )

        print(f"[INFO] Premium credits: {credits_remaining}/20 remaining")

        # 우리 OpenAI API 키 사용
        our_api_key = os.environ.get('PATHCRAFT_OPENAI_KEY')
        if not our_api_key:
            raise ValueError(
                "Server configuration error: PATHCRAFT_OPENAI_KEY not set.\n"
                "Please contact support."
            )

        # Premium은 항상 GPT-4 사용
        guide = call_openai(prompt, "gpt-4", our_api_key)

        # 크레딧 차감
        deduct_premium_credit(user_id)
        print(f"[OK] Premium credit used. Remaining: {credits_remaining - 1}/20")

    elif tier == "expert":
        # Expert tier: Fine-tuned 무제한, 우리 API 키 사용
        print("[Tier: EXPERT] Using Fine-tuned POE Expert AI (unlimited)")

        if user_id is None:
            raise ValueError("Expert tier requires user_id")

        # 우리 OpenAI API 키 사용
        our_api_key = os.environ.get('PATHCRAFT_OPENAI_KEY')
        if not our_api_key:
            raise ValueError(
                "Server configuration error: PATHCRAFT_OPENAI_KEY not set.\n"
                "Please contact support."
            )

        # Fine-tuned 모델 사용
        fine_tuned_model = "ft:gpt-3.5-turbo:pathcraftai:poe-expert-v1"
        print(f"[INFO] Using Fine-tuned model: {fine_tuned_model}")

        guide = call_openai(prompt, fine_tuned_model, our_api_key)

        print(f"[OK] Expert tier: Fine-tuned POE Expert AI analysis complete")
        print(f"     Unlimited usage (no credits deducted)")

    else:
        raise ValueError(f"Invalid tier: {tier}. Must be 'free', 'premium', or 'expert'")

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
        print(f"[ERROR] Model {model} failed: {e}")

        # Fine-tuned 실패 시 GPT-4 Fallback
        if model.startswith("ft:"):
            print("[INFO] Fine-tuned model failed, falling back to gpt-4")
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a Path of Exile build guide expert. Create comprehensive, accurate build guides based on the provided data."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )
                guide = response.choices[0].message.content
                print(f"[OK] Fallback to GPT-4 successful")
                return guide
            except Exception as fallback_error:
                print(f"[ERROR] GPT-4 fallback also failed: {fallback_error}")

        # 최종 Fallback: Mock
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


def call_gemini(prompt: str, model: str, api_key: Optional[str]) -> str:
    """Google Gemini API 호출 (Free tier 추천!)"""
    try:
        import google.generativeai as genai
    except ImportError:
        print("[ERROR] google-generativeai package not installed.")
        print("       Run: pip install google-generativeai")
        print("[INFO] Falling back to mock guide")
        return generate_mock_guide("", {})

    if api_key is None:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            print("[ERROR] GEMINI_API_KEY not found in environment")
            print("[INFO] Get your FREE Gemini API key:")
            print("       https://makersuite.google.com/")
            print("       Daily limit: 60 requests (FREE!)")
            print("[INFO] Falling back to mock guide")
            return generate_mock_guide("", {})

    try:
        genai.configure(api_key=api_key)
        model_instance = genai.GenerativeModel(model)

        response = model_instance.generate_content(prompt)
        guide = response.text

        print(f"[OK] Gemini {model} response received")
        print(f"     Cost: FREE (Daily limit: 60 requests)")
        print(f"     Recommended for Free tier users!")

        return guide

    except Exception as e:
        print(f"[ERROR] Gemini API call failed: {e}")
        print("[INFO] Common issues:")
        print("       - Daily limit exceeded (60 requests/day)")
        print("       - Invalid API key")
        print("       - Region restrictions")
        print("[INFO] Falling back to mock guide")
        return generate_mock_guide("", {})


# ============================================================================
# Credit System Functions (Premium/Expert Tier)
# ============================================================================

def check_premium_credits(user_id: str) -> int:
    """
    Premium 크레딧 확인

    Args:
        user_id: 사용자 ID

    Returns:
        남은 크레딧 (0~20)

    Note:
        현재는 Mock 구현. 실제로는 SQLite DB 연동 필요.
        Phase 8 (C# WPF UI)에서 DB 구현 예정.
    """
    # TODO: 실제 DB 구현
    # 지금은 환경변수로 테스트
    mock_credits = os.environ.get(f'MOCK_CREDITS_{user_id}', '15')
    try:
        credits = int(mock_credits)
        return max(0, min(20, credits))  # 0~20 범위
    except ValueError:
        return 15  # 기본값: 15/20


def deduct_premium_credit(user_id: str):
    """
    Premium 크레딧 1개 차감

    Args:
        user_id: 사용자 ID

    Note:
        현재는 Mock 구현. 실제로는 SQLite DB 업데이트 필요.
        Phase 8 (C# WPF UI)에서 DB 구현 예정.
    """
    # TODO: 실제 DB 구현
    # 지금은 환경변수 업데이트 (테스트용)
    current_credits = check_premium_credits(user_id)
    new_credits = max(0, current_credits - 1)

    # 실제 구현 예시:
    # db = sqlite3.connect('pathcraft.db')
    # db.execute(
    #     "UPDATE users SET credits_remaining = ? WHERE user_id = ?",
    #     (new_credits, user_id)
    # )
    # db.commit()

    print(f"[DEBUG] Credits deducted for {user_id}: {current_credits} -> {new_credits}")


def get_credit_reset_date(user_id: str) -> str:
    """
    크레딧 리셋 날짜 반환 (매달 1일)

    Args:
        user_id: 사용자 ID

    Returns:
        리셋 날짜 문자열 (YYYY-MM-DD)

    Note:
        현재는 Mock 구현. 실제로는 DB에서 가져오기.
    """
    # TODO: 실제 DB 구현
    # 다음 달 1일 계산
    now = datetime.now()
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)

    return next_month.strftime('%Y-%m-%d')


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
    parser = argparse.ArgumentParser(
        description='Build Guide Generator with LLM (3-Tier Hybrid Model)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Free tier (Mock, no API key needed)
  python build_guide_generator.py --keyword "Death's Oath" --llm mock

  # Free tier (Gemini, FREE API key!)
  python build_guide_generator.py --keyword "Death's Oath" \\
      --llm gemini --model gemini-pro --api-key YOUR_GEMINI_KEY

  # Free tier (OpenAI, user's API key)
  python build_guide_generator.py --keyword "Death's Oath" \\
      --llm openai --model gpt-4 --api-key YOUR_OPENAI_KEY

  # Premium tier (our API, 20 credits/month)
  python build_guide_generator.py --keyword "Death's Oath" \\
      --tier premium --user-id user123

  # Expert tier (Fine-tuned, unlimited)
  python build_guide_generator.py --keyword "Death's Oath" \\
      --tier expert --user-id user456

Get FREE Gemini API key: https://makersuite.google.com/
        """
    )

    parser.add_argument('--keyword', type=str, required=True,
                       help='Build keyword (e.g., "Death\'s Oath", "Mageblood")')

    parser.add_argument('--llm', type=str, default='mock',
                       choices=['openai', 'anthropic', 'gemini', 'mock'],
                       help='LLM provider (free tier only)')

    parser.add_argument('--model', type=str, default='gpt-4',
                       help='Model name: gpt-4, claude-3-opus, gemini-pro, etc.')

    parser.add_argument('--api-key', type=str, default=None,
                       help='API key (free tier: required, premium/expert: ignored)')

    parser.add_argument('--tier', type=str, default='free',
                       choices=['free', 'premium', 'expert'],
                       help='User tier: free (user API key), premium ($2/month, 20 credits), expert ($5/month, unlimited)')

    parser.add_argument('--user-id', type=str, default=None,
                       help='User ID (required for premium/expert tiers)')

    parser.add_argument('--output', type=str, default=None,
                       help='Output file path (default: build_guides/{keyword}_guide.md)')

    args = parser.parse_args()

    # Validation
    if args.tier in ['premium', 'expert'] and args.user_id is None:
        parser.error(f"--user-id is required for {args.tier} tier")

    if args.tier == 'free' and args.llm not in ['mock'] and args.api_key is None:
        print(f"[WARNING] Free tier with {args.llm} requires --api-key")
        print(f"          Get your FREE Gemini key: https://makersuite.google.com/")
        print(f"          Or use --llm mock for testing")
        print()

    generate_build_guide_with_llm(
        keyword=args.keyword,
        llm_provider=args.llm,
        model=args.model,
        api_key=args.api_key,
        tier=args.tier,
        user_id=args.user_id,
        output_file=args.output
    )
