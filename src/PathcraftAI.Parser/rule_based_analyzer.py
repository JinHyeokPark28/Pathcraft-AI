# -*- coding: utf-8 -*-
"""
Rule-Based Build Analyzer
AI API 키 없이도 빌드 분석을 제공하는 규칙 기반 분석기
"""

import json
import sys
from typing import Dict, List
import argparse

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


class RuleBasedAnalyzer:
    """
    규칙 기반 빌드 분석기

    AI API 없이도 다음 분석 제공:
    - DPS 평가 (티어 시스템)
    - 생존력 평가 (Life/ES/저항)
    - 빌드 밸런스 분석
    - 개선 제안 (우선순위 기반)
    """

    def __init__(self):
        # DPS 티어 (3.27 기준)
        self.dps_tiers = {
            'god': 50_000_000,      # 5천만+ DPS
            'excellent': 10_000_000, # 1천만+ DPS
            'good': 5_000_000,       # 500만+ DPS
            'average': 1_000_000,    # 100만+ DPS
            'low': 500_000,          # 50만+ DPS
            'very_low': 100_000      # 10만+ DPS
        }

        # Life/ES 티어
        self.life_tiers = {
            'excellent': 6000,
            'good': 4500,
            'average': 3500,
            'low': 2500
        }

        self.es_tiers = {
            'excellent': 8000,
            'good': 6000,
            'average': 4000,
            'low': 2000
        }

    def analyze_build(self, build_data: Dict) -> Dict:
        """
        빌드 데이터 분석

        Args:
            build_data: {
                'dps': int,
                'life': int,
                'energy_shield': int,
                'fire_res': int,
                'cold_res': int,
                'lightning_res': int,
                'chaos_res': int,
                'main_skill': str,
                'class': str,
                'keystones': List[str]
            }

        Returns:
            분석 결과 (마크다운 형식)
        """

        dps = build_data.get('dps', 0)
        life = build_data.get('life', 0)
        es = build_data.get('energy_shield', 0)
        main_skill = build_data.get('main_skill', 'Unknown')
        poe_class = build_data.get('class', 'Unknown')

        # 분석 결과 생성
        analysis_lines = []

        analysis_lines.append("## 🤖 빌드 분석 (Rule-Based)")
        analysis_lines.append("")

        # 1. DPS 평가
        dps_tier, dps_comment = self._analyze_dps(dps, main_skill)
        analysis_lines.append(f"### ⚔️ 화력 평가: **{dps_tier.upper()}**")
        analysis_lines.append(f"- DPS: **{dps:,}**")
        analysis_lines.append(f"- {dps_comment}")
        analysis_lines.append("")

        # 2. 생존력 평가
        defense_tier, defense_comment = self._analyze_defense(life, es, build_data)
        analysis_lines.append(f"### 🛡️ 생존력 평가: **{defense_tier.upper()}**")
        analysis_lines.append(f"- Life: **{life:,}** / ES: **{es:,}**")
        analysis_lines.append(f"- {defense_comment}")
        analysis_lines.append("")

        # 3. 저항 체크
        res_issues = self._check_resistances(build_data)
        if res_issues:
            analysis_lines.append("### ⚠️ 저항 이슈")
            for issue in res_issues:
                analysis_lines.append(f"- {issue}")
            analysis_lines.append("")
        else:
            analysis_lines.append("### ✅ 저항: 모두 캡 도달")
            analysis_lines.append("")

        # 4. 빌드 밸런스
        balance_score, balance_comment = self._analyze_balance(dps, life, es)
        analysis_lines.append(f"### ⚖️ 밸런스: **{balance_score}/10**")
        analysis_lines.append(f"- {balance_comment}")
        analysis_lines.append("")

        # 5. 개선 제안
        suggestions = self._generate_suggestions(build_data, dps_tier, defense_tier, res_issues)
        if suggestions:
            analysis_lines.append("### 💡 개선 제안 (우선순위 순)")
            for i, suggestion in enumerate(suggestions, 1):
                analysis_lines.append(f"{i}. {suggestion}")
            analysis_lines.append("")

        # 6. 빌드 평가 요약
        overall_grade = self._calculate_overall_grade(dps_tier, defense_tier, res_issues, balance_score)
        analysis_lines.append(f"### 🏆 종합 평가: **{overall_grade}**")
        analysis_lines.append("")
        analysis_lines.append("---")
        analysis_lines.append("*이 분석은 규칙 기반 시스템으로 생성되었습니다. AI 분석을 원하시면 API 키를 설정해주세요.*")

        return {
            'provider': 'rule-based',
            'model': 'PathcraftAI Rule Engine v1.0',
            'analysis': '\n'.join(analysis_lines),
            'elapsed_seconds': 0.0,
            'input_tokens': 0,
            'output_tokens': 0
        }

    def _analyze_dps(self, dps: int, skill: str) -> tuple:
        """DPS 평가"""
        if dps >= self.dps_tiers['god']:
            return 'god', f"{skill} 빌드로 최상급 화력입니다. 모든 컨텐츠 클리어 가능합니다."
        elif dps >= self.dps_tiers['excellent']:
            return 'excellent', f"매우 높은 DPS입니다. 엔드게임 보스도 쉽게 처리할 수 있습니다."
        elif dps >= self.dps_tiers['good']:
            return 'good', f"준수한 화력입니다. T16 맵과 기본 보스는 문제없습니다."
        elif dps >= self.dps_tiers['average']:
            return 'average', f"평균적인 DPS입니다. 화력 업그레이드를 고려해보세요."
        elif dps >= self.dps_tiers['low']:
            return 'low', f"낮은 DPS입니다. 무기나 젬 업그레이드가 시급합니다."
        else:
            return 'very_low', f"매우 낮은 DPS입니다. 빌드 재검토가 필요합니다."

    def _analyze_defense(self, life: int, es: int, build_data: Dict) -> tuple:
        """생존력 평가"""
        total_ehp = life + es

        # Life 빌드
        if life > es * 2:
            if life >= self.life_tiers['excellent']:
                return 'excellent', f"Life 빌드로 매우 높은 생존력을 보유하고 있습니다."
            elif life >= self.life_tiers['good']:
                return 'good', f"준수한 Life입니다. 엔드게임에서 안정적입니다."
            elif life >= self.life_tiers['average']:
                return 'average', f"평균적인 Life입니다. 추가 Life 노드를 고려하세요."
            else:
                return 'low', f"Life가 부족합니다. 최소 {self.life_tiers['average']:,} Life를 목표로 하세요."

        # ES 빌드
        elif es > life * 2:
            if es >= self.es_tiers['excellent']:
                return 'excellent', f"ES 빌드로 매우 높은 보호막을 보유하고 있습니다."
            elif es >= self.es_tiers['good']:
                return 'good', f"준수한 ES입니다. CI 빌드로 안정적입니다."
            elif es >= self.es_tiers['average']:
                return 'average', f"평균적인 ES입니다. ES 장비 업그레이드를 고려하세요."
            else:
                return 'low', f"ES가 부족합니다. 최소 {self.es_tiers['average']:,} ES를 목표로 하세요."

        # 하이브리드
        else:
            if total_ehp >= 10000:
                return 'excellent', f"하이브리드 빌드로 Life+ES 합산 {total_ehp:,}의 높은 생존력입니다."
            elif total_ehp >= 7000:
                return 'good', f"하이브리드 빌드로 준수한 생존력입니다."
            else:
                return 'average', f"하이브리드 빌드입니다. Life 또는 ES 중 하나에 집중하는 것을 권장합니다."

    def _check_resistances(self, build_data: Dict) -> List[str]:
        """저항 체크"""
        issues = []

        fire_res = build_data.get('fire_res', 0)
        cold_res = build_data.get('cold_res', 0)
        lightning_res = build_data.get('lightning_res', 0)
        chaos_res = build_data.get('chaos_res', -60)

        if fire_res < 75:
            issues.append(f"🔥 Fire Resistance: {fire_res}% (캡: 75%) - **{75 - fire_res}% 부족**")

        if cold_res < 75:
            issues.append(f"❄️ Cold Resistance: {cold_res}% (캡: 75%) - **{75 - cold_res}% 부족**")

        if lightning_res < 75:
            issues.append(f"⚡ Lightning Resistance: {lightning_res}% (캡: 75%) - **{75 - lightning_res}% 부족**")

        if chaos_res < 0:
            issues.append(f"☠️ Chaos Resistance: {chaos_res}% - 카오스 데미지에 취약합니다 (권장: 0% 이상)")

        return issues

    def _analyze_balance(self, dps: int, life: int, es: int) -> tuple:
        """빌드 밸런스 평가"""
        total_ehp = life + es

        # DPS:EHP 비율 계산
        if total_ehp == 0:
            return 0, "생존력이 0입니다. 빌드를 재검토하세요."

        dps_per_ehp = dps / total_ehp

        # 이상적인 비율: 500~2000 DPS per EHP
        if 500 <= dps_per_ehp <= 2000:
            score = 10
            comment = "화력과 생존력의 균형이 완벽합니다."
        elif 300 <= dps_per_ehp < 500 or 2000 < dps_per_ehp <= 3000:
            score = 8
            comment = "전반적으로 균형잡힌 빌드입니다."
        elif 100 <= dps_per_ehp < 300:
            score = 6
            comment = "생존력에 비해 화력이 부족합니다. 무기/젬 업그레이드를 우선하세요."
        elif 3000 < dps_per_ehp <= 5000:
            score = 6
            comment = "화력에 비해 생존력이 부족합니다. Life/ES 증가가 필요합니다."
        elif dps_per_ehp < 100:
            score = 4
            comment = "화력이 매우 부족합니다. 빌드 DPS를 크게 올려야 합니다."
        else:
            score = 4
            comment = "Glass Cannon 빌드입니다. 생존력을 대폭 강화해야 합니다."

        return score, comment

    def _generate_suggestions(self, build_data: Dict, dps_tier: str, defense_tier: str, res_issues: List[str]) -> List[str]:
        """개선 제안 생성 (우선순위 순)"""
        suggestions = []

        # 1순위: 저항 캡
        if res_issues:
            suggestions.append("**저항 캡 맞추기** - 생존의 기본입니다. 링/목걸이/벨트에서 저항을 확보하세요.")

        # 2순위: 심각한 생존력 부족
        if defense_tier == 'low':
            life = build_data.get('life', 0)
            es = build_data.get('energy_shield', 0)
            if life > es:
                suggestions.append(f"**Life 증가** - 현재 {life:,}입니다. 패시브 트리에서 Life 노드를 추가로 확보하세요.")
            else:
                suggestions.append(f"**ES 증가** - 현재 {es:,}입니다. ES% 장비로 업그레이드하세요.")

        # 3순위: DPS 부족
        if dps_tier in ['low', 'very_low']:
            suggestions.append("**무기 업그레이드** - DPS가 낮습니다. 더 높은 DPS 무기로 교체하세요.")
            suggestions.append("**젬 레벨/품질** - 메인 스킬 젬을 21레벨 23품질로 업그레이드하세요.")

        # 4순위: 평균적인 DPS 개선
        if dps_tier == 'average':
            suggestions.append("**크리티컬 확률 증가** - 크리티컬 빌드라면 크리 확률을 높이세요.")
            suggestions.append("**Aura 최적화** - Hatred, Wrath 등 DPS aura를 활성화하세요.")

        # 5순위: 생존력 추가 개선
        if defense_tier in ['average', 'good'] and not res_issues:
            chaos_res = build_data.get('chaos_res', -60)
            if chaos_res < 0:
                suggestions.append("**Chaos 저항 확보** - 현재 카오스 저항이 음수입니다. 0% 이상을 목표로 하세요.")

        # 6순위: 고급 최적화
        if dps_tier in ['good', 'excellent', 'god'] and defense_tier in ['good', 'excellent']:
            suggestions.append("**Cluster Jewel 추가** - 추가 DPS와 유틸리티를 위한 클러스터 주얼을 고려하세요.")
            suggestions.append("**Awakened Gem** - 메인 서포트 젬을 Awakened 버전으로 업그레이드하세요.")

        return suggestions

    def _calculate_overall_grade(self, dps_tier: str, defense_tier: str, res_issues: List[str], balance_score: int) -> str:
        """종합 평가 등급"""
        # 점수 계산
        dps_scores = {'god': 10, 'excellent': 9, 'good': 7, 'average': 5, 'low': 3, 'very_low': 1}
        defense_scores = {'excellent': 10, 'good': 7, 'average': 5, 'low': 2}

        dps_score = dps_scores.get(dps_tier, 5)
        defense_score = defense_scores.get(defense_tier, 5)
        res_penalty = min(len(res_issues) * 2, 6)  # 저항 이슈당 -2점 (최대 -6)

        total_score = (dps_score + defense_score + balance_score - res_penalty) / 3

        if total_score >= 9:
            return "S급 (완성도 높은 빌드)"
        elif total_score >= 7.5:
            return "A급 (우수한 빌드)"
        elif total_score >= 6:
            return "B급 (준수한 빌드)"
        elif total_score >= 4.5:
            return "C급 (평균적인 빌드)"
        elif total_score >= 3:
            return "D급 (개선 필요)"
        else:
            return "F급 (재검토 필요)"


def main():
    parser = argparse.ArgumentParser(description='Rule-Based Build Analyzer')
    parser.add_argument('--pob', type=str, help='POB URL (optional)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--mock', action='store_true', help='Use mock data for testing')

    args = parser.parse_args()

    analyzer = RuleBasedAnalyzer()

    # Mock 데이터 (테스트용)
    if args.mock or not args.pob:
        build_data = {
            'dps': 3_500_000,
            'life': 4200,
            'energy_shield': 500,
            'fire_res': 75,
            'cold_res': 75,
            'lightning_res': 75,
            'chaos_res': -20,
            'main_skill': 'Lightning Arrow',
            'class': 'Deadeye',
            'keystones': ['Point Blank', 'Far Shot']
        }
    else:
        # POB에서 데이터 로드 (실제 구현 시)
        try:
            from smart_build_analyzer import SmartBuildAnalyzer
            pob_analyzer = SmartBuildAnalyzer(args.pob)
            pob_analyzer.fetch_pob()
            build_data = pob_analyzer.extract_stats()
        except Exception as e:
            print(json.dumps({"error": f"Failed to load POB: {str(e)}"}))
            return

    # 분석 실행
    result = analyzer.analyze_build(build_data)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result['analysis'])


if __name__ == "__main__":
    main()
