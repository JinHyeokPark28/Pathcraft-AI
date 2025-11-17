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
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
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
    parser.add_argument('--pob', '--pob-url', dest='pob_url', type=str, required=True, help='POB URL to analyze')
    parser.add_argument('--provider', type=str, choices=['claude', 'openai', 'both', 'rule-based'], default='both', help='AI provider')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    # POB 데이터 가져오기
    if not args.json:
        print(f"[INFO] Fetching POB data from: {args.pob_url}")

    try:
        pob_code = get_pob_code_from_url(args.pob_url)
        if not pob_code:
            if args.json:
                print(json.dumps({"error": "Could not fetch POB code"}))
            else:
                print("[ERROR] Could not fetch POB code")
            exit(1)

        xml_data = decode_pob_code(pob_code)
        if not xml_data:
            if args.json:
                print(json.dumps({"error": "Could not decode POB data"}))
            else:
                print("[ERROR] Could not decode POB data")
            exit(1)

        build_data = parse_pob_xml(xml_data, args.pob_url)
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
        if args.provider == 'rule-based':
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
            # AI 분석 (Claude/OpenAI)
            if args.provider in ['claude', 'both']:
                claude_result = analyze_build_with_claude(build_data)
            else:
                claude_result = {"error": "Not requested"}

            if args.provider in ['openai', 'both']:
                openai_result = analyze_build_with_openai(build_data)
            else:
                openai_result = {"error": "Not requested"}

            # 결과 출력
            if args.json:
                # JSON 모드: 단일 provider 결과만 출력
                if args.provider == 'claude':
                    print(json.dumps(claude_result, ensure_ascii=False, indent=2))
                elif args.provider == 'openai':
                    print(json.dumps(openai_result, ensure_ascii=False, indent=2))
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

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"[ERROR] {e}")
        exit(1)
