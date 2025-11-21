# -*- coding: utf-8 -*-
"""
AI Build Analyzer
Claude API와 OpenAI API를 사용하여 POE 빌드 분석
"""

import json
import os
import sys
from typing import Dict, List, Optional
import time

# Windows 콘솔 UTF-8 인코딩 설정
if sys.platform == 'win32':
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass  # 실패해도 계속 진행

# .env 파일 지원
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def analyze_build_with_claude(build_data: Dict, api_key: Optional[str] = None) -> Dict:
    """
    Claude API를 사용하여 빌드 분석

    Args:
        build_data: POB 파싱된 빌드 데이터
        api_key: Claude API 키

    Returns:
        분석 결과 딕셔너리
    """

    if api_key is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        print("[WARN] ANTHROPIC_API_KEY not found")
        return {"error": "No Claude API key"}

    try:
        import anthropic
    except ImportError:
        print("[ERROR] anthropic package not installed")
        print("[INFO] Run: pip install anthropic")
        return {"error": "anthropic package not installed"}

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # 빌드 데이터를 프롬프트로 변환
        meta = build_data.get('meta', {})
        stages = build_data.get('progression_stages', [])

        if not stages:
            return {"error": "No build stages found"}

        stage = stages[0]
        gem_setups = stage.get('gem_setups', {})
        gear = stage.get('gear_recommendation', {})

        # 프롬프트 작성
        prompt = f"""You are a Path of Exile build expert. Analyze the following build:

**Build Name:** {meta.get('build_name', 'Unknown')}
**Class/Ascendancy:** {meta.get('class')} / {meta.get('ascendancy')}
**POB Link:** {meta.get('pob_link')}

**Main Skill Gems:**
"""

        # 처음 3개 스킬만
        for i, (label, setup) in enumerate(list(gem_setups.items())[:3]):
            prompt += f"\n{i+1}. {label}: {setup.get('links', 'N/A')}"

        prompt += "\n\n**Key Gear:**\n"

        # 주요 장비
        for slot, item in list(gear.items())[:8]:
            prompt += f"- {slot}: {item.get('name', 'N/A')}\n"

        prompt += """

Please provide a detailed analysis in the following format:

1. **Build Overview** (2-3 sentences)
   - What is this build's main concept?
   - What playstyle does it support?

2. **Strengths** (3-4 bullet points)
   - What does this build do well?

3. **Weaknesses** (3-4 bullet points)
   - What are the main drawbacks?

4. **Recommended For** (2 sentences)
   - Who should play this build?
   - Budget level (league starter / mid-budget / high-budget)

5. **Key Synergies** (2-3 bullet points)
   - Important item/gem/passive interactions

Please respond in Korean (한국어)."""

        print("[INFO] Calling Claude API...")
        start_time = time.time()

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        elapsed = time.time() - start_time

        analysis = message.content[0].text

        return {
            "provider": "claude",
            "model": "claude-3-5-sonnet-20241022",
            "analysis": analysis,
            "elapsed_seconds": round(elapsed, 2),
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens
        }

    except Exception as e:
        print(f"[ERROR] Claude API failed: {e}")
        return {"error": str(e)}


def analyze_build_with_openai(build_data: Dict, api_key: Optional[str] = None) -> Dict:
    """
    OpenAI GPT API를 사용하여 빌드 분석

    Args:
        build_data: POB 파싱된 빌드 데이터
        api_key: OpenAI API 키

    Returns:
        분석 결과 딕셔너리
    """

    if api_key is None:
        api_key = os.environ.get('OPENAI_API_KEY')

    if not api_key:
        print("[WARN] OPENAI_API_KEY not found")
        return {"error": "No OpenAI API key"}

    try:
        from openai import OpenAI
    except ImportError:
        print("[ERROR] openai package not installed")
        print("[INFO] Run: pip install openai")
        return {"error": "openai package not installed"}

    try:
        client = OpenAI(api_key=api_key)

        # 빌드 데이터를 프롬프트로 변환
        meta = build_data.get('meta', {})
        stages = build_data.get('progression_stages', [])

        if not stages:
            return {"error": "No build stages found"}

        stage = stages[0]
        gem_setups = stage.get('gem_setups', {})
        gear = stage.get('gear_recommendation', {})

        # 프롬프트 작성 (Claude와 동일)
        prompt = f"""You are a Path of Exile build expert. Analyze the following build:

**Build Name:** {meta.get('build_name', 'Unknown')}
**Class/Ascendancy:** {meta.get('class')} / {meta.get('ascendancy')}
**POB Link:** {meta.get('pob_link')}

**Main Skill Gems:**
"""

        for i, (label, setup) in enumerate(list(gem_setups.items())[:3]):
            prompt += f"\n{i+1}. {label}: {setup.get('links', 'N/A')}"

        prompt += "\n\n**Key Gear:**\n"

        for slot, item in list(gear.items())[:8]:
            prompt += f"- {slot}: {item.get('name', 'N/A')}\n"

        prompt += """

Please provide a detailed analysis in the following format:

1. **Build Overview** (2-3 sentences)
   - What is this build's main concept?
   - What playstyle does it support?

2. **Strengths** (3-4 bullet points)
   - What does this build do well?

3. **Weaknesses** (3-4 bullet points)
   - What are the main drawbacks?

4. **Recommended For** (2 sentences)
   - Who should play this build?
   - Budget level (league starter / mid-budget / high-budget)

5. **Key Synergies** (2-3 bullet points)
   - Important item/gem/passive interactions

Please respond in Korean (한국어)."""

        print("[INFO] Calling OpenAI API...")
        start_time = time.time()

        response = client.chat.completions.create(
            model="gpt-4o",  # 최신 GPT-4 모델
            messages=[
                {"role": "system", "content": "You are a Path of Exile build analysis expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )

        elapsed = time.time() - start_time

        analysis = response.choices[0].message.content

        return {
            "provider": "openai",
            "model": "gpt-4o",
            "analysis": analysis,
            "elapsed_seconds": round(elapsed, 2),
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens
        }

    except Exception as e:
        print(f"[ERROR] OpenAI API failed: {e}")
        return {"error": str(e)}


def analyze_build_with_gemini(build_data: Dict, api_key: Optional[str] = None) -> Dict:
    """
    Google Gemini API를 사용하여 빌드 분석

    Args:
        build_data: POB 파싱된 빌드 데이터
        api_key: Gemini API 키

    Returns:
        분석 결과 딕셔너리
    """

    if api_key is None:
        api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')

    if not api_key:
        print("[WARN] GOOGLE_API_KEY not found")
        return {"error": "No Gemini API key"}

    try:
        import google.generativeai as genai
    except ImportError:
        print("[ERROR] google-generativeai package not installed")
        print("[INFO] Run: pip install google-generativeai")
        return {"error": "google-generativeai package not installed"}

    try:
        genai.configure(api_key=api_key)

        # 빌드 데이터를 프롬프트로 변환
        build_info = build_data.get('build_info', {})
        stats = build_data.get('defensive_stats', {})
        offense = build_data.get('offensive_stats', {})
        stage = build_data.get('mid_game', {})
        gear = stage.get('gear_recommendation', {})

        # 프롬프트 작성 (Claude/OpenAI와 동일)
        prompt = f"""You are a Path of Exile build expert. Analyze the following build:

Build Name: {build_info.get('name', 'Unknown')}
Class: {build_info.get('class', 'Unknown')}
Level: {build_info.get('level', 0)}
Main Skill: {build_info.get('main_skill', 'Unknown')}

Defensive Stats:
- Life: {stats.get('life', 0)}
- Energy Shield: {stats.get('energy_shield', 0)}
- Armour: {stats.get('armour', 0)}
- Evasion: {stats.get('evasion', 0)}
- Fire Res: {stats.get('fire_resistance', 0)}%
- Cold Res: {stats.get('cold_resistance', 0)}%
- Lightning Res: {stats.get('lightning_resistance', 0)}%
- Chaos Res: {stats.get('chaos_resistance', 0)}%

Offensive Stats:
- Combined DPS: {offense.get('combined_dps', 0)}

Please provide a concise analysis in 3-4 bullet points covering:
1. Build strengths
2. Potential weaknesses or areas to improve
3. Recommended upgrades or changes
4. Overall viability rating (1-10)

Please respond in Korean (한국어)."""

        print("[INFO] Calling Gemini API...")
        start_time = time.time()

        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)

        elapsed = time.time() - start_time
        analysis = response.text

        # 토큰 정보 가져오기 (가능한 경우)
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata'):
            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)

        return {
            "provider": "gemini",
            "model": "gemini-1.5-pro",
            "analysis": analysis,
            "elapsed_seconds": round(elapsed, 2),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }

    except Exception as e:
        print(f"[ERROR] Gemini API failed: {e}")
        return {"error": str(e)}


def generate_upgrade_guide(build_data: Dict, budget: int = 1000, league: str = "Settlers") -> Dict:
    """
    빌드 업그레이드 가이드 생성

    Args:
        build_data: POB 파싱된 빌드 데이터
        budget: 목표 예산 (Chaos)
        league: 리그 이름

    Returns:
        업그레이드 로드맵
    """
    try:
        from build_guide_system import BuildGuideSystem
        guide_system = BuildGuideSystem(league=league)
        return guide_system.generate_upgrade_roadmap(build_data, current_budget=0, target_budget=budget)
    except Exception as e:
        print(f"[ERROR] Guide generation failed: {e}", file=sys.stderr)
        return {"error": str(e)}


def compare_analyses(claude_result: Dict, openai_result: Dict):
    """
    두 AI의 분석 결과를 비교하여 출력

    Args:
        claude_result: Claude 분석 결과
        openai_result: OpenAI 분석 결과
    """

    print("\n" + "=" * 80)
    print("AI BUILD ANALYSIS COMPARISON")
    print("=" * 80)

    # Claude 결과
    print("\n" + "-" * 80)
    print("CLAUDE ANALYSIS")
    print("-" * 80)

    if "error" in claude_result:
        print(f"[ERROR] {claude_result['error']}")
    else:
        print(f"Model: {claude_result.get('model')}")
        print(f"Time: {claude_result.get('elapsed_seconds')}s")
        print(f"Tokens: {claude_result.get('input_tokens')} in / {claude_result.get('output_tokens')} out")
        print("\n" + claude_result.get('analysis', ''))

    # OpenAI 결과
    print("\n" + "-" * 80)
    print("OPENAI GPT ANALYSIS")
    print("-" * 80)

    if "error" in openai_result:
        print(f"[ERROR] {openai_result['error']}")
    else:
        print(f"Model: {openai_result.get('model')}")
        print(f"Time: {openai_result.get('elapsed_seconds')}s")
        print(f"Tokens: {openai_result.get('input_tokens')} in / {openai_result.get('output_tokens')} out")
        print("\n" + openai_result.get('analysis', ''))

    # 비교 요약
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    if "error" not in claude_result and "error" not in openai_result:
        print(f"Claude: {claude_result.get('elapsed_seconds')}s, {claude_result.get('output_tokens')} tokens")
        print(f"OpenAI: {openai_result.get('elapsed_seconds')}s, {openai_result.get('output_tokens')} tokens")

        if claude_result.get('elapsed_seconds', 999) < openai_result.get('elapsed_seconds', 999):
            print("\n⚡ Claude was faster")
        else:
            print("\n⚡ OpenAI was faster")


if __name__ == "__main__":
    import argparse
    from pob_parser import get_pob_code_from_url, decode_pob_code, parse_pob_xml

    parser = argparse.ArgumentParser(description='AI Build Analyzer')
    parser.add_argument('--pob', '--pob-url', dest='pob_url', type=str, help='POB URL to analyze')
    parser.add_argument('--pob-code', dest='pob_code', type=str, help='POB code directly (base64 encoded)')
    parser.add_argument('--provider', type=str, choices=['claude', 'openai', 'gemini', 'both', 'rule-based', 'guide'], default='both', help='AI provider or guide mode')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--budget', type=int, default=1000, help='Target budget in chaos (for guide mode)')
    parser.add_argument('--league', type=str, default='Settlers', help='League name (for guide mode)')

    args = parser.parse_args()

    # POB 데이터 가져오기
    if not args.pob_url and not args.pob_code:
        if args.json:
            print(json.dumps({"error": "Either --pob or --pob-code is required"}))
        else:
            print("[ERROR] Either --pob or --pob-code is required")
        exit(1)

    try:
        # POB 코드 직접 제공 시
        if args.pob_code:
            if not args.json:
                print("[INFO] Using provided POB code")
            pob_code = args.pob_code
        # POB URL에서 가져오기
        else:
            if not args.json:
                print(f"[INFO] Fetching POB data from: {args.pob_url}")
            pob_code = get_pob_code_from_url(args.pob_url)

        if not pob_code:
            if args.json:
                print(json.dumps({"error": "Could not fetch POB code"}))
            else:
                print("[ERROR] Could not fetch POB code")
            exit(1)

        # XML 직접 로드인 경우 (로컬 파일에서 읽음)
        if pob_code.startswith("__XML_DIRECT__"):
            xml_data = pob_code[14:]  # __XML_DIRECT__ 제거
            if not args.json:
                print("[INFO] Loaded POB XML from local file")
        else:
            xml_data = decode_pob_code(pob_code)
            if not xml_data:
                if args.json:
                    print(json.dumps({"error": "Could not decode POB data"}))
                else:
                    print("[ERROR] Could not decode POB data")
                exit(1)

        pob_url = args.pob_url if args.pob_url else "direct_input"
        build_data = parse_pob_xml(xml_data, pob_url)
        if not build_data:
            if args.json:
                print(json.dumps({"error": "Could not parse POB XML"}))
            else:
                print("[ERROR] Could not parse POB XML")
            exit(1)

        if not args.json:
            print(f"[OK] Build loaded: {build_data['meta']['build_name']}")
            print()

        # AI 분석
        if args.provider == 'guide':
            # 업그레이드 가이드 모드
            guide_result = generate_upgrade_guide(build_data, args.budget, args.league)

            if args.json:
                print(json.dumps(guide_result, ensure_ascii=False, indent=2))
            else:
                # 텍스트 출력
                if "error" in guide_result:
                    print(f"[ERROR] {guide_result['error']}")
                else:
                    print("=" * 80)
                    print(f"BUILD UPGRADE ROADMAP: {guide_result['build_name']}")
                    print("=" * 80)
                    print(f"Divine Rate: {guide_result['divine_rate']}c")
                    print(f"Target Budget: {args.budget}c")
                    print()

                    for tier in guide_result.get('tiers', []):
                        print("-" * 80)
                        print(f"[{tier['tier_name']}] {tier['budget_range']}")
                        print(f"Total Cost: {tier['total_cost_formatted']}")
                        print("-" * 80)

                        for i, upgrade in enumerate(tier['upgrades'], 1):
                            print(f"\n  {i}. [{upgrade['priority']}] {upgrade['slot']}")
                            print(f"     현재: {upgrade['current_item']}")
                            print(f"     목표: {upgrade['target_item']}")
                            print(f"     가격: {upgrade['price_formatted']}")
                            print(f"     이유: {upgrade['reason']}")
                            if upgrade.get('dps_gain_percent'):
                                print(f"     예상 DPS 증가: +{upgrade['dps_gain_percent']}%")
                            if upgrade.get('ehp_gain'):
                                print(f"     예상 EHP 증가: +{upgrade['ehp_gain']}")

                        print()

        elif args.provider == 'rule-based':
            # Rule-based 분석 (API 키 불필요)
            from rule_based_analyzer import RuleBasedAnalyzer
            analyzer = RuleBasedAnalyzer()

            # POB 데이터를 rule-based analyzer 형식으로 변환
            stats_data = {
                'dps': build_data.get('stats', {}).get('total_dps', 0),
                'life': build_data.get('stats', {}).get('life', 0),
                'energy_shield': build_data.get('stats', {}).get('es', 0),
                'fire_res': build_data.get('stats', {}).get('fire_res', 0),
                'cold_res': build_data.get('stats', {}).get('cold_res', 0),
                'lightning_res': build_data.get('stats', {}).get('lightning_res', 0),
                'chaos_res': build_data.get('stats', {}).get('chaos_res', -60),
                'main_skill': build_data.get('meta', {}).get('main_skill', 'Unknown'),
                'class': build_data.get('meta', {}).get('poe_class', 'Unknown'),
                'keystones': build_data.get('passive_tree', {}).get('keystones', [])
            }

            result = analyzer.analyze_build(stats_data)

            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("\n" + result.get('analysis', str(result)))
        else:
            # AI 분석 (Claude/OpenAI/Gemini)
            if args.provider in ['claude', 'both']:
                claude_result = analyze_build_with_claude(build_data)
            else:
                claude_result = {"error": "Not requested"}

            if args.provider in ['openai', 'both']:
                openai_result = analyze_build_with_openai(build_data)
            else:
                openai_result = {"error": "Not requested"}

            if args.provider == 'gemini':
                gemini_result = analyze_build_with_gemini(build_data)
            else:
                gemini_result = {"error": "Not requested"}

            # 결과 출력
            if args.json:
                # JSON 모드: 단일 provider 결과만 출력
                if args.provider == 'claude':
                    print(json.dumps(claude_result, ensure_ascii=False, indent=2))
                elif args.provider == 'openai':
                    print(json.dumps(openai_result, ensure_ascii=False, indent=2))
                elif args.provider == 'gemini':
                    print(json.dumps(gemini_result, ensure_ascii=False, indent=2))
                else:
                    # both인 경우 claude 우선
                    print(json.dumps(claude_result if "error" not in claude_result else openai_result, ensure_ascii=False, indent=2))
            else:
                # 텍스트 모드: 기존 출력
                if args.provider == 'both':
                    compare_analyses(claude_result, openai_result)
                elif args.provider == 'claude':
                    print("\n" + claude_result.get('analysis', str(claude_result)))
                elif args.provider == 'openai':
                    print("\n" + openai_result.get('analysis', str(openai_result)))
                elif args.provider == 'gemini':
                    print("\n" + gemini_result.get('analysis', str(gemini_result)))

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"[ERROR] {e}")
        exit(1)
