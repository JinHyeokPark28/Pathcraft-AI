#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 가이드 테스트 스크립트
POB 코드를 파일에서 읽거나 직접 입력받아 테스트
"""

import sys
import os

# UTF-8 설정
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

from guide_generator import GuideGenerator


def test_with_pob_code(pob_code: str):
    """POB 코드로 테스트"""
    generator = GuideGenerator()
    guide = generator.generate_guide(pob_code)
    generator.print_guide(guide)

    # JSON으로도 저장
    import json
    output_path = os.path.join(os.path.dirname(__file__), "test_guide_output.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(guide, f, ensure_ascii=False, indent=2)
    print(f"\n[INFO] JSON 저장됨: {output_path}")


def test_sample_builds():
    """샘플 빌드들 테스트"""
    generator = GuideGenerator()

    samples = [
        {
            "name": "Penance Brand Inquisitor",
            "info": {
                "class": "Templar",
                "ascendancy": "Inquisitor",
                "main_skill": "Penance Brand",
                "skills": ["Penance Brand", "Brand Recall"],
                "level": 90
            }
        },
        {
            "name": "Arc Elementalist",
            "info": {
                "class": "Witch",
                "ascendancy": "Elementalist",
                "main_skill": "Arc",
                "skills": ["Arc", "Orb of Storms"],
                "level": 85
            }
        },
        {
            "name": "Cyclone Slayer",
            "info": {
                "class": "Duelist",
                "ascendancy": "Slayer",
                "main_skill": "Cyclone",
                "skills": ["Cyclone", "Leap Slam"],
                "level": 90
            }
        },
        {
            "name": "SRS Necromancer",
            "info": {
                "class": "Witch",
                "ascendancy": "Necromancer",
                "main_skill": "Summon Raging Spirit",
                "skills": ["Summon Raging Spirit", "Raise Zombie"],
                "level": 90
            }
        },
        {
            "name": "Toxic Rain Pathfinder",
            "info": {
                "class": "Ranger",
                "ascendancy": "Pathfinder",
                "main_skill": "Toxic Rain",
                "skills": ["Toxic Rain", "Wither"],
                "level": 90
            }
        }
    ]

    for sample in samples:
        print(f"\n{'='*60}")
        print(f"테스트: {sample['name']}")
        print('='*60)

        archetype = generator.detect_archetype(sample['info'])
        matching = generator.find_matching_build(sample['info'])

        print(f"  클래스: {sample['info']['class']} - {sample['info']['ascendancy']}")
        print(f"  메인 스킬: {sample['info']['main_skill']}")
        print(f"  감지된 아키타입: {archetype}")
        print(f"  매칭 템플릿: {'발견 - ' + matching.get('build_info', {}).get('name', '') if matching else '없음'}")


if __name__ == '__main__':
    # 커맨드라인 인자 확인
    if len(sys.argv) > 1:
        # 파일에서 POB 코드 읽기
        if os.path.exists(sys.argv[1]):
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                pob_code = f.read().strip()
            test_with_pob_code(pob_code)
        else:
            # 직접 POB 코드 입력
            test_with_pob_code(sys.argv[1])
    else:
        # 샘플 테스트
        print("사용법:")
        print("  python test_guide.py <pob_code>")
        print("  python test_guide.py <pob_file.txt>")
        print("\n샘플 빌드 테스트 실행...")
        test_sample_builds()
