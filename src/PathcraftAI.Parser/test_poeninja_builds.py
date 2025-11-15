# -*- coding: utf-8 -*-
"""poe.ninja Build API 테스트"""

import requests
import json

# poe.ninja의 실제 빌드 API 테스트
url = 'https://poe.ninja/api/data/GetBuildOverview'
params = {
    'overview': 'keepers',
    'type': 'exp'
}

print('[INFO] Testing poe.ninja build API...')
response = requests.get(url, params=params, timeout=10)
print(f'[INFO] Status: {response.status_code}')

if response.status_code == 200:
    data = response.json()
    builds = data.get('builds', [])
    print(f'[OK] Found {len(builds)} builds')

    # Death's Oath 사용자 찾기
    deaths_oath_builds = []
    for build in builds:
        items = build.get('items', [])
        for item in items:
            if 'Death' in item.get('name', '') and 'Oath' in item.get('name', ''):
                deaths_oath_builds.append(build)
                break

    print(f'[FOUND] {len(deaths_oath_builds)} Deaths Oath builds')

    if deaths_oath_builds:
        print('\nFirst 5 Deaths Oath users:')
        for i, build in enumerate(deaths_oath_builds[:5], 1):
            char_name = build.get('name', 'Unknown')
            char_class = build.get('class', 'Unknown')
            level = build.get('level', 0)
            account = build.get('account', {}).get('name', 'Unknown')
            main_skill = build.get('mainSkill', {}).get('name', 'Unknown')
            print(f'{i}. {char_name} - {char_class} Lvl {level}')
            print(f'   Account: {account}')
            print(f'   Main Skill: {main_skill}')
            print()

        # 샘플 빌드 상세 정보
        print('Sample build details:')
        sample = deaths_oath_builds[0]
        print(json.dumps(sample, indent=2, ensure_ascii=False))
else:
    print(f'[ERROR] Failed: {response.text[:200]}')
