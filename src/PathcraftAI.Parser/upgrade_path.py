#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
업그레이드 경로 시각화
- 예산 기반 단계별 업그레이드 추천
- POE.Ninja 가격 데이터 활용
- 우선순위: 저항 > DPS > 방어
"""

import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


class UpgradePathPlanner:
    def __init__(self, budget_chaos: int = 100):
        """
        Args:
            budget_chaos: 총 예산 (chaos orb)
        """
        self.budget_chaos = budget_chaos
        self.market_data = {}
        self.upgrade_steps = []

    def load_market_data(self, game_data_dir: str = "game_data"):
        """POE.Ninja 가격 데이터 로드"""
        print("=" * 80)
        print("LOADING MARKET DATA")
        print("=" * 80)
        print()

        data_dir = Path(game_data_dir)

        if not data_dir.exists():
            print(f"[ERROR] Market data not found: {game_data_dir}")
            print("[INFO] Run: python poe_ninja_fetcher.py --collect")
            return False

        # 유니크 무기, 방어구, 악세서리 로드
        categories = {
            'unique_weapons': 'unique_weapons.json',
            'unique_armours': 'unique_armours.json',
            'unique_accessories': 'unique_accessories.json',
            'unique_jewels': 'unique_jewels.json',
            'unique_flasks': 'unique_flasks.json'
        }

        total_items = 0

        for category, filename in categories.items():
            filepath = data_dir / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    items = data.get('items', [])

                    # 카테고리별로 아이템 저장
                    self.market_data[category] = items
                    total_items += len(items)

                    print(f"[OK] {category}: {len(items)} items")

        print()
        print(f"[OK] Total market items: {total_items}")
        print()

        return True

    def analyze_gaps(self, current_stats: Dict, target_stats: Dict) -> List[Dict]:
        """
        현재와 목표 사이의 Gap 분석 및 우선순위 설정

        우선순위:
        1. 저항 (75% 미만인 경우 최우선)
        2. DPS (10,000 이상 차이)
        3. Life/ES (500 이상 차이)
        4. 방어 메커니즘
        """
        gaps = []

        # 1. 저항 Gap (최우선)
        resistances = [
            ('Fire', 'fire_res'),
            ('Cold', 'cold_res'),
            ('Lightning', 'lightning_res')
        ]

        for res_name, res_key in resistances:
            current = current_stats.get(res_key, 0)
            target = target_stats.get(res_key, 75)  # 기본 목표 75%

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

        if target_dps - current_dps > 10000:
            gaps.append({
                'priority': 2,
                'category': 'DPS',
                'stat': 'Total DPS',
                'current': current_dps,
                'target': target_dps,
                'gap': target_dps - current_dps,
                'severity': 'high' if (target_dps - current_dps) > 100000 else 'medium'
            })

        # 3. Life/ES Gap
        current_life = current_stats.get('life', 0)
        target_life = target_stats.get('life', 0)

        if current_life > 1 and target_life - current_life > 500:  # CI 빌드 제외
            gaps.append({
                'priority': 3,
                'category': 'Defense',
                'stat': 'Life',
                'current': current_life,
                'target': target_life,
                'gap': target_life - current_life,
                'severity': 'medium'
            })

        current_es = current_stats.get('energy_shield', 0)
        target_es = target_stats.get('energy_shield', 0)

        if target_es - current_es > 500:
            gaps.append({
                'priority': 3,
                'category': 'Defense',
                'stat': 'Energy Shield',
                'current': current_es,
                'target': target_es,
                'gap': target_es - current_es,
                'severity': 'medium'
            })

        # 우선순위와 심각도로 정렬
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        gaps.sort(key=lambda x: (x['priority'], severity_order.get(x['severity'], 99)))

        return gaps

    def generate_upgrade_steps(self, gaps: List[Dict], current_stats: Dict) -> List[Dict]:
        """Gap을 기반으로 단계별 업그레이드 계획 생성"""
        steps = []
        remaining_budget = self.budget_chaos

        print("=" * 80)
        print(f"UPGRADE PATH (Budget: {self.budget_chaos} chaos)")
        print("=" * 80)
        print()

        step_num = 1

        # 1. 저항 캡핑 (최우선)
        resistance_gaps = [g for g in gaps if g['category'] == 'Resistance']

        if resistance_gaps:
            # 저항 부족한 것들 모아서 한 번에 해결
            uncapped_resistances = [g['stat'] for g in resistance_gaps]
            estimated_cost = 15  # 링/벨트 교체 비용 예상

            if remaining_budget >= estimated_cost:
                step = {
                    'step': step_num,
                    'priority': 'Critical',
                    'title': 'Cap Resistances',
                    'cost_chaos': estimated_cost,
                    'description': f"Fix {', '.join(uncapped_resistances)} resistances",
                    'recommendations': [
                        'Buy ring with Fire Res + Life (Vermillion Ring ilvl 75+)',
                        'Buy belt with Cold/Lightning Res + Life',
                        'Check POE.Ninja for affordable options (~5-10c each)'
                    ],
                    'impact': 'Survivability: High | Clear Speed: None'
                }
                steps.append(step)
                remaining_budget -= estimated_cost
                step_num += 1

        # 2. 6-Link 획득 (DPS 대폭 증가)
        dps_gap = next((g for g in gaps if g['category'] == 'DPS'), None)

        if dps_gap and remaining_budget >= 40:
            # 6-Link가 가장 큰 DPS 향상
            step = {
                'step': step_num,
                'priority': 'High',
                'title': 'Get 6-Link Setup',
                'cost_chaos': 50,
                'description': f"Increase DPS by ~{dps_gap['gap'] * 0.6:,.0f}",
                'recommendations': [
                    'Buy 6-link rare body armour with Life + Resistances',
                    'Alternative (Budget): Tabula Rasa (1-2c) for temporary use',
                    'Search POE.Ninja for body armours with 6 links (~40-60c)'
                ],
                'impact': 'DPS: Very High | Survivability: Medium'
            }
            steps.append(step)
            remaining_budget -= 50
            step_num += 1

        # 3. 무기 업그레이드 (추가 DPS 향상)
        if dps_gap and remaining_budget >= 30:
            step = {
                'step': step_num,
                'priority': 'Medium',
                'title': 'Upgrade Weapon',
                'cost_chaos': 30,
                'description': f"Increase DPS by ~{dps_gap['gap'] * 0.3:,.0f}",
                'recommendations': [
                    'For wand builds: High Attack Speed (1.5+) + Crit Chance (8%+)',
                    'For bow builds: High pDPS bow with attack speed',
                    'Check POE.Ninja for weapons in your price range'
                ],
                'impact': 'DPS: High | Survivability: None'
            }
            steps.append(step)
            remaining_budget -= 30
            step_num += 1

        # 4. Life/ES 증가 (방어력 강화)
        life_gap = next((g for g in gaps if g['stat'] == 'Life'), None)
        es_gap = next((g for g in gaps if g['stat'] == 'Energy Shield'), None)

        if (life_gap or es_gap) and remaining_budget >= 10:
            defense_type = 'Life' if life_gap else 'Energy Shield'
            gap_value = (life_gap or es_gap)['gap']

            step = {
                'step': step_num,
                'priority': 'Medium',
                'title': f'Increase {defense_type}',
                'cost_chaos': 15,
                'description': f'Add {gap_value:,} {defense_type}',
                'recommendations': [
                    f'Add {defense_type} nodes on passive tree (free)',
                    f'Upgrade gear with better {defense_type} rolls',
                    'Focus on chest, helmet, shield slots'
                ],
                'impact': 'Survivability: High | DPS: None'
            }
            steps.append(step)
            remaining_budget -= 15
            step_num += 1

        # 예산 부족 시 메시지
        if step_num == 1:
            print(f"[WARN] Budget too low ({self.budget_chaos}c) for significant upgrades")
            print("[INFO] Recommended minimum: 50 chaos")
            print()

        self.upgrade_steps = steps
        return steps

    def display_upgrade_path(self):
        """업그레이드 경로를 보기 좋게 출력"""
        if not self.upgrade_steps:
            print("[INFO] No upgrade steps generated")
            return

        print("=" * 80)
        print("UPGRADE PATH SUMMARY")
        print("=" * 80)
        print()

        total_cost = sum(step['cost_chaos'] for step in self.upgrade_steps)

        print(f"Total Cost: {total_cost} / {self.budget_chaos} chaos")
        print(f"Steps: {len(self.upgrade_steps)}")
        print()

        for step in self.upgrade_steps:
            print(f"Step {step['step']}: {step['title']} ({step['priority']} Priority)")
            print(f"  Cost: {step['cost_chaos']} chaos")
            print(f"  Goal: {step['description']}")
            print(f"  Impact: {step['impact']}")
            print()
            print("  Recommendations:")
            for rec in step['recommendations']:
                print(f"    • {rec}")
            print()

        print("=" * 80)

    def export_json(self) -> Dict:
        """JSON 형식으로 출력 (UI 연동용)"""
        return {
            'budget_chaos': self.budget_chaos,
            'total_steps': len(self.upgrade_steps),
            'total_cost': sum(step['cost_chaos'] for step in self.upgrade_steps),
            'upgrade_steps': self.upgrade_steps
        }


def main():
    parser = argparse.ArgumentParser(description='업그레이드 경로 생성기')
    parser.add_argument('--budget', type=int, default=100, help='예산 (chaos orbs)')
    parser.add_argument('--current-file', type=str, help='현재 캐릭터 stats JSON 파일')
    parser.add_argument('--target-file', type=str, help='목표 빌드 stats JSON 파일')
    parser.add_argument('--pob', type=str, help='POB URL (목표 빌드)')
    parser.add_argument('--character', type=str, help='캐릭터 이름 (현재 빌드)')
    parser.add_argument('--mock', action='store_true', help='Mock 데이터 사용')
    parser.add_argument('--json', action='store_true', help='JSON 출력 모드')

    args = parser.parse_args()

    planner = UpgradePathPlanner(budget_chaos=args.budget)

    # Market 데이터 로드
    if not args.json:
        planner.load_market_data()
    else:
        # JSON 모드일 때는 조용히 로드 (stderr로만 출력)
        import sys
        original_stdout = sys.stdout
        sys.stdout = sys.stderr
        planner.load_market_data()
        sys.stdout = original_stdout

    # Mock 또는 실제 데이터 로드
    if args.pob and args.character:
        # POB URL과 캐릭터 이름으로 비교 (compare_build.py 재사용)
        try:
            from compare_build import get_current_character_stats, get_pob_target_stats
            from poe_oauth import load_token

            if not args.json:
                print("Loading character data...")

            # 토큰 로드
            token_data = load_token()
            if not token_data:
                if args.json:
                    print(json.dumps({"error": "POE account not connected. Please run OAuth first."}))
                else:
                    print("[ERROR] POE account not connected")
                return

            current_stats = get_current_character_stats(token_data['access_token'], args.character)
            target_stats = get_pob_target_stats(args.pob, silent=args.json)

            if not current_stats or not target_stats:
                if args.json:
                    print(json.dumps({"error": "Failed to load character or POB data"}))
                else:
                    print("[ERROR] Failed to load character or POB data")
                return

        except Exception as e:
            if args.json:
                print(json.dumps({"error": str(e)}))
            else:
                print(f"[ERROR] Failed to load data: {e}")
            return
    elif args.mock:
        # Mock 데이터 (CI 빌드 예시)
        current_stats = {
            'dps': 150000,
            'life': 1,  # CI
            'energy_shield': 4500,
            'fire_res': 45,
            'cold_res': 75,
            'lightning_res': 60,
            'chaos_res': -60
        }

        target_stats = {
            'dps': 850000,
            'life': 1,  # CI
            'energy_shield': 6600,
            'fire_res': 75,
            'cold_res': 75,
            'lightning_res': 75,
            'chaos_res': -60
        }
    elif args.current_file and args.target_file:
        # 실제 파일에서 로드
        with open(args.current_file, 'r') as f:
            current_stats = json.load(f)

        with open(args.target_file, 'r') as f:
            target_stats = json.load(f)
    else:
        if args.json:
            print(json.dumps({"error": "No data source specified. Use --pob/--character, --current-file/--target-file, or --mock"}))
        else:
            print("[ERROR] No data source specified")
            print("[INFO] Use --pob <url> --character <name> OR --current-file <file> --target-file <file> OR --mock")
        return

    # Gap 분석
    gaps = planner.analyze_gaps(current_stats, target_stats)

    # 업그레이드 경로 생성
    steps = planner.generate_upgrade_steps(gaps, current_stats)

    # 출력
    if args.json:
        # JSON 모드
        result = planner.export_json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 텍스트 모드
        planner.display_upgrade_path()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Usage: python upgrade_path.py --budget <chaos> [--mock]")
        print()
        print("Example:")
        print("  python upgrade_path.py --budget 100 --mock")
        print("  python upgrade_path.py --budget 200 --current-file current.json --target-file target.json")
        sys.exit(1)

    main()
