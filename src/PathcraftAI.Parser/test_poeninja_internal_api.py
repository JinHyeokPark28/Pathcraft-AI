# -*- coding: utf-8 -*-
"""
poe.ninja 내부 API 탐색
브라우저 개발자 도구에서 확인한 실제 API 엔드포인트 테스트
"""

import requests
import json

# poe.ninja가 내부적으로 사용할 가능성이 있는 API 엔드포인트들
POSSIBLE_ENDPOINTS = [
    # Next.js API routes
    "https://poe.ninja/api/data/poe1/builds",
    "https://poe.ninja/api/poe1/builds",
    "https://poe.ninja/api/builds",

    # 내부 데이터 API
    "https://poe.ninja/_next/data/builds/keepers.json",
    "https://poe.ninja/api/data/builds/keepers",

    # GraphQL 가능성
    "https://poe.ninja/graphql",
    "https://poe.ninja/api/graphql",
]

print("[INFO] Testing poe.ninja internal API endpoints...")
print("=" * 60)

for endpoint in POSSIBLE_ENDPOINTS:
    print(f"\n[TEST] {endpoint}")

    try:
        # GET 요청
        response = requests.get(endpoint, timeout=5, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://poe.ninja/poe1/builds/keepers'
        })

        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            print(f"  [OK] SUCCESS!")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")

            # JSON 파싱 시도
            try:
                data = response.json()
                print(f"  Data keys: {list(data.keys())[:10]}")

                # 파일로 저장
                filename = endpoint.replace('https://', '').replace('/', '_').replace(':', '') + '.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"  Saved to: {filename}")

            except json.JSONDecodeError:
                print(f"  Response (first 200 chars): {response.text[:200]}")

        elif response.status_code == 404:
            print(f"  [FAIL] 404 Not Found")

        elif response.status_code == 403:
            print(f"  [BLOCKED] 403 Forbidden")

        else:
            print(f"  Response: {response.text[:200]}")

    except requests.exceptions.Timeout:
        print(f"  [TIMEOUT] Request timed out")

    except requests.exceptions.ConnectionError:
        print(f"  [ERROR] Connection Error")

    except Exception as e:
        print(f"  [ERROR] {e}")

print("\n" + "=" * 60)
print("[INFO] Testing complete")
print("\n[NOTE] If no endpoints work, we must use:")
print("   1. Web scraping with Selenium/Playwright")
print("   2. OR build our own cache from POE Official API")
