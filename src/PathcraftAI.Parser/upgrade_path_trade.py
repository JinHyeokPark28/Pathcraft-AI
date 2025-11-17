#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
업그레이드 경로 시각화 (POE Trade API 버전)
- 실제 거래소에서 구매 가능한 아이템 추천
- 예산 기반 단계별 업그레이드
- 우선순위: 저항 > DPS > 방어
"""

import json
import sys
import argparse
from typing import List, Dict
from poe_trade_api import POETradeAPI

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


class UpgradePathPlannerTrade:
    """POE Trade API 기반 업그레이드 플래너"""

    def __init__(self, budget_chaos: int = 100, league: str = "Standard"):
        self.budget_chaos = budget_chaos
        self.league = league
        self.trade_api = POETradeAPI(league=league)
        self.upgrade_steps = []

    def analyze_gaps(self, current_stats: Dict, target_stats: Dict) -> List[Dict]:
        """Gap 분석 및 우선순위 설정"""
        gaps = []

        # 1. 저항 Gap (최우선)
        resistances = [
            ('Fire', 'fire_res'),
            ('Cold', 'cold_res'),
            ('Lightning', 'lightning_res')
        ]

        for res_name, res_key in resistances:
            current = current_stats.get(res_key, 0)
            target = target_stats.get(res_key, 75)
            if current < target:
                gap = target - current
                gaps.append({
                    'priority': 1,
                    'category': 'Resistance',
                    'stat': res_name,
                    'current': current,
                    'target': target,
                    'gap': gap,
                    'severity': 'critical' if current < 60 else 'high'
                })

        # 2. DPS Gap
        current_dps = current_stats.get('dps', 0)
        target_dps = target_stats.get('dps', 0)
        if target_dps > current_dps and (target_dps - current_dps) > 10000:
            gaps.append({
                'priority': 2,
                'category': 'DPS',
                'stat': 'Total DPS',
                'current': current_dps,
                'target': target_dps,
                'gap': target_dps - current_dps,
                'severity': 'high'
            })

        # 3. Life/ES Gap
        current_life = current_stats.get('life', 0)
        target_life = target_stats.get('life', 0)
        current_es = current_stats.get('energy_shield', 0)
        target_es = target_stats.get('energy_shield', 0)

        if target_life > current_life and (target_life - current_life) > 500:
            gaps.append({
                'priority': 3,
                'category': 'Defense',
                'stat': 'Life',
                'current': current_life,
                'target': target_life,
                'gap': target_life - current_life,
                'severity': 'medium'
            })

        if target_es > current_es and (target_es - current_es) > 500:
            gaps.append({
                'priority': 3,
                'category': 'Defense',
                'stat': 'Energy Shield',
                'current': current_es,
                'target': target_es,
                'gap': target_es - current_es,
                'severity': 'medium'
            })

        # 우선순위, 심각도로 정렬
        gaps.sort(key=lambda x: (x['priority'], 0 if x['severity'] == 'critical' else 1))

        return gaps

    def generate_upgrade_steps(self, gaps: List[Dict]) -> List[Dict]:
        """Gap을 기반으로 단계별 업그레이드 계획 생성 (실제 거래소 아이템)"""
        steps = []
        remaining_budget = self.budget_chaos
        step_num = 1

        # Step 1: 저항 캡 (최우선)
        resistance_gaps = [g for g in gaps if g['category'] == 'Resistance']
        if resistance_gaps and remaining_budget >= 15:
            # 실제 거래소에서 저항 반지 검색
            rings = self.trade_api.search_resistance_ring(
                min_total_res=60,
                max_price=min(20, remaining_budget)
            )

            recommendations = []
            if rings:
                for ring in rings[:3]:
                    recommendations.append(
                        f"Buy: {ring['type']} - {ring['price_display']} (seller: {ring['seller']})"
                    )
                    recommendations.append(f"Whisper: {ring['whisper'][:100]}")
            else:
                recommendations = [
                    "Buy ring with Fire/Cold/Lightning Res + Life",
                    "Search trade site: \"resistance ring\" with 60+ total res",
                    "Budget: ~10-20c"
                ]

            steps.append({
                'step': step_num,
                'priority': 'Critical',
                'title': 'Cap Resistances',
                'cost_chaos': 15,
                'description': f'Fix {", ".join([g["stat"] for g in resistance_gaps])} resistances',
                'recommendations': recommendations,
                'impact': 'Survivability: High | Clear Speed: None',
                'trade_results': rings if rings else []
            })

            remaining_budget -= 15
            step_num += 1

        # Step 2: 6-Link (DPS 향상)
        dps_gaps = [g for g in gaps if g['category'] == 'DPS']
        if dps_gaps and remaining_budget >= 50:
            # 실제 거래소에서 6링크 검색
            bodies = self.trade_api.search_6link_body(
                max_price=min(60, remaining_budget)
            )

            recommendations = []
            if bodies:
                for body in bodies[:3]:
                    recommendations.append(
                        f"Buy: {body['type']} - {body['price_display']} (seller: {body['seller']})"
                    )
            else:
                recommendations = [
                    "Buy 6-link rare body armour with Life + Resistances",
                    "Alternative (Budget): Tabula Rasa (~1-2c) for temporary use",
                    "Search trade site: \"6 link body armour\""
                ]

            steps.append({
                'step': step_num,
                'priority': 'High',
                'title': 'Get 6-Link Setup',
                'cost_chaos': 50,
                'description': f'Increase DPS significantly',
                'recommendations': recommendations,
                'impact': 'DPS: Very High | Survivability: Medium',
                'trade_results': bodies if bodies else []
            })

            remaining_budget -= 50
            step_num += 1

        # Step 3: 무기 업그레이드
        if dps_gaps and remaining_budget >= 30:
            steps.append({
                'step': step_num,
                'priority': 'Medium',
                'title': 'Upgrade Weapon',
                'cost_chaos': 30,
                'description': 'Get better weapon with higher DPS',
                'recommendations': [
                    "For wand builds: High Attack Speed (1.5+) + Crit Chance (8%+)",
                    "For bow builds: High pDPS bow with attack speed",
                    "Search trade site with your specific weapon type"
                ],
                'impact': 'DPS: High | Survivability: None',
                'trade_results': []
            })

            remaining_budget -= 30
            step_num += 1

        # Step 4: 방어 업그레이드
        defense_gaps = [g for g in gaps if g['category'] == 'Defense']
        if defense_gaps and remaining_budget >= 15:
            defense_type = defense_gaps[0]['stat']
            steps.append({
                'step': step_num,
                'priority': 'Medium',
                'title': f'Increase {defense_type}',
                'cost_chaos': 15,
                'description': f'Add {defense_gaps[0]["gap"]:,.0f} {defense_type}',
                'recommendations': [
                    "Add defensive nodes on passive tree (free)",
                    "Upgrade gear with better defensive rolls",
                    "Focus on chest, helmet, shield slots"
                ],
                'impact': 'Survivability: High | DPS: None',
                'trade_results': []
            })

            remaining_budget -= 15
            step_num += 1

        return steps

    def print_upgrade_path(self, steps: List[Dict]):
        """업그레이드 경로 출력"""
        print("=" * 80)
        print(f"UPGRADE PATH (Budget: {self.budget_chaos} chaos)")
        print("=" * 80)
        print()

        total_cost = sum(step['cost_chaos'] for step in steps)
        print(f"Total Steps: {len(steps)}")
        print(f"Total Cost: {total_cost}c")
        print()

        for step in steps:
            print(f"Step {step['step']}: {step['title']} (Cost: {step['cost_chaos']}c)")
            print(f"  Priority: {step['priority']}")
            print(f"  → {step['description']}")
            print()

            for rec in step['recommendations']:
                print(f"     • {rec}")
            print()

            print(f"  Impact: {step['impact']}")
            print()
            print("-" * 80)
            print()

    def to_json(self, steps: List[Dict]) -> Dict:
        """JSON 출력용 데이터 생성"""
        total_cost = sum(step['cost_chaos'] for step in steps)

        # trade_results 제거 (너무 크므로)
        clean_steps = []
        for step in steps:
            clean_step = {k: v for k, v in step.items() if k != 'trade_results'}
            clean_steps.append(clean_step)

        return {
            'budget_chaos': self.budget_chaos,
            'total_steps': len(steps),
            'total_cost': total_cost,
            'upgrade_steps': clean_steps
        }


def main():
    parser = argparse.ArgumentParser(description='업그레이드 경로 생성기 (Trade API)')
    parser.add_argument('--budget', type=int, default=100, help='예산 (chaos orbs)')
    parser.add_argument('--league', type=str, default='Standard', help='League name')
    parser.add_argument('--pob', type=str, help='POB URL (목표 빌드)')
    parser.add_argument('--character', type=str, help='캐릭터 이름 (현재 빌드)')
    parser.add_argument('--mock', action='store_true', help='Mock 데이터 사용')
    parser.add_argument('--json', action='store_true', help='JSON 출력 모드')

    args = parser.parse_args()

    planner = UpgradePathPlannerTrade(
        budget_chaos=args.budget,
        league=args.league
    )

    # Mock 데이터 또는 실제 데이터
    if args.mock:
        # Mock 데이터
        current_stats = {
            'dps': 150000,
            'life': 1,
            'energy_shield': 4500,
            'fire_res': 45,
            'cold_res': 75,
            'lightning_res': 60,
            'chaos_res': -60
        }

        target_stats = {
            'dps': 570000,
            'life': 1,
            'energy_shield': 6600,
            'fire_res': 75,
            'cold_res': 75,
            'lightning_res': 75,
            'chaos_res': -60
        }
    elif args.pob and args.character:
        # TODO: 실제 데이터 로드
        print(json.dumps({"error": "POB integration not yet implemented. Use --mock for testing."}))
        return
    else:
        print(json.dumps({"error": "No data source specified. Use --mock for testing."}))
        return

    # Gap 분석
    gaps = planner.analyze_gaps(current_stats, target_stats)

    # 업그레이드 경로 생성
    steps = planner.generate_upgrade_steps(gaps)

    # 출력
    if args.json:
        output = planner.to_json(steps)
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        planner.print_upgrade_path(steps)


if __name__ == '__main__':
    main()
