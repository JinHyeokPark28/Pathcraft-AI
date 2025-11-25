# -*- coding: utf-8 -*-
"""
Awakened POE Trade Korean Translation Extractor
Awakened POE Trade의 한국어 데이터에서 번역 매핑 추출

이 스크립트는 tools/awakened-poe-trade/renderer/public/data/ko/ 디렉토리의
ndjson 파일들을 파싱하여 영어-한국어 번역 매핑을 생성합니다.
"""

import os
import json
from typing import Dict, List, Any


def extract_items_translations(items_path: str) -> Dict[str, Dict]:
    """
    items.ndjson에서 아이템 번역 추출

    Returns:
        {
            "items": {"영어": "한국어", ...},
            "items_kr": {"한국어": "영어", ...},
            "items_by_namespace": {"UNIQUE": {...}, "GEM": {...}, ...}
        }
    """
    translations = {
        "items": {},
        "items_kr": {},
        "items_by_namespace": {}
    }

    if not os.path.exists(items_path):
        print(f"[WARN] 파일을 찾을 수 없음: {items_path}")
        return translations

    with open(items_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue

            try:
                item = json.loads(line)
                en_name = item.get('refName', '')
                kr_name = item.get('name', '')
                namespace = item.get('namespace', 'UNKNOWN')

                if en_name and kr_name:
                    translations['items'][en_name] = kr_name
                    translations['items_kr'][kr_name] = en_name

                    # 네임스페이스별 분류
                    if namespace not in translations['items_by_namespace']:
                        translations['items_by_namespace'][namespace] = {}
                    translations['items_by_namespace'][namespace][en_name] = kr_name

            except json.JSONDecodeError as e:
                print(f"[WARN] JSON 파싱 오류: {e}")
                continue

    return translations


def extract_stats_translations(stats_path: str) -> Dict[str, Dict]:
    """
    stats.ndjson에서 스탯 번역 추출

    Returns:
        {
            "stats": {"영어": "한국어", ...},
            "stats_kr": {"한국어": "영어", ...},
            "stats_trade_ids": {"stat_id": {"en": "...", "kr": "..."}, ...}
        }
    """
    translations = {
        "stats": {},
        "stats_kr": {},
        "stats_trade_ids": {}
    }

    if not os.path.exists(stats_path):
        print(f"[WARN] 파일을 찾을 수 없음: {stats_path}")
        return translations

    with open(stats_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue

            try:
                stat = json.loads(line)
                en_ref = stat.get('ref', '')
                matchers = stat.get('matchers', [])
                trade_ids = stat.get('trade', {}).get('ids', {})

                if not en_ref or not matchers:
                    continue

                # 첫 번째 매처에서 한국어 번역 추출
                kr_text = ''
                for matcher in matchers:
                    if 'string' in matcher:
                        kr_text = matcher['string']
                        break

                if kr_text:
                    translations['stats'][en_ref] = kr_text
                    translations['stats_kr'][kr_text] = en_ref

                    # Trade ID와 번역 매핑
                    for id_type, ids in trade_ids.items():
                        for stat_id in ids:
                            translations['stats_trade_ids'][stat_id] = {
                                'en': en_ref,
                                'kr': kr_text
                            }

            except json.JSONDecodeError as e:
                print(f"[WARN] JSON 파싱 오류: {e}")
                continue

    return translations


def extract_all_awakened_translations(awakened_data_dir: str = None) -> Dict:
    """
    Awakened POE Trade의 모든 한국어 데이터 추출

    Args:
        awakened_data_dir: Awakened POE Trade 한국어 데이터 디렉토리
                          기본값: tools/awakened-poe-trade/renderer/public/data/ko

    Returns:
        통합된 번역 데이터
    """
    if awakened_data_dir is None:
        # 기본 경로 설정
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        awakened_data_dir = os.path.join(
            project_root,
            "tools",
            "awakened-poe-trade",
            "renderer",
            "public",
            "data",
            "ko"
        )

    print(f"[INFO] Awakened POE Trade 데이터 디렉토리: {awakened_data_dir}")

    all_translations = {
        "source": "awakened-poe-trade",
        "version": "latest",
        "items": {},
        "items_kr": {},
        "items_by_namespace": {},
        "stats": {},
        "stats_kr": {},
        "stats_trade_ids": {},
    }

    # 아이템 번역 추출
    items_path = os.path.join(awakened_data_dir, "items.ndjson")
    items_data = extract_items_translations(items_path)
    all_translations['items'] = items_data['items']
    all_translations['items_kr'] = items_data['items_kr']
    all_translations['items_by_namespace'] = items_data['items_by_namespace']
    print(f"[OK] 아이템: {len(all_translations['items'])}개")

    # 스탯 번역 추출
    stats_path = os.path.join(awakened_data_dir, "stats.ndjson")
    stats_data = extract_stats_translations(stats_path)
    all_translations['stats'] = stats_data['stats']
    all_translations['stats_kr'] = stats_data['stats_kr']
    all_translations['stats_trade_ids'] = stats_data['stats_trade_ids']
    print(f"[OK] 스탯: {len(all_translations['stats'])}개")

    # 네임스페이스 통계
    print("\n[네임스페이스별 아이템 수]")
    for ns, items in sorted(all_translations['items_by_namespace'].items()):
        print(f"  {ns}: {len(items)}개")

    return all_translations


def merge_with_existing(new_data: Dict, existing_path: str) -> Dict:
    """
    기존 번역 데이터와 병합
    새 데이터가 우선순위를 가짐 (덮어쓰기)
    """
    if not os.path.exists(existing_path):
        return new_data

    with open(existing_path, 'r', encoding='utf-8') as f:
        existing = json.load(f)

    # 기존 데이터에 새 데이터 병합
    for key in ['items', 'items_kr', 'stats', 'stats_kr']:
        if key in new_data and key in existing:
            existing[key].update(new_data[key])
        elif key in new_data:
            existing[key] = new_data[key]

    # 새 데이터 소스 정보 추가
    existing['awakened_source'] = new_data.get('source', 'awakened-poe-trade')

    return existing


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Awakened POE Trade 한국어 번역 추출')
    parser.add_argument('--awakened-dir', type=str,
                        help='Awakened POE Trade 한국어 데이터 디렉토리')
    parser.add_argument('--output', type=str, default='./data',
                        help='출력 디렉토리')
    parser.add_argument('--merge', type=str,
                        help='기존 번역 파일과 병합')

    args = parser.parse_args()

    # 번역 추출
    translations = extract_all_awakened_translations(args.awakened_dir)

    # 기존 데이터와 병합 (옵션)
    if args.merge and os.path.exists(args.merge):
        print(f"\n[INFO] 기존 데이터와 병합: {args.merge}")
        translations = merge_with_existing(translations, args.merge)

    # 저장
    os.makedirs(args.output, exist_ok=True)
    output_file = os.path.join(args.output, "awakened_translations.json")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)

    # 통계 출력
    print("\n" + "=" * 50)
    print("[완료] Awakened POE Trade 번역 데이터 저장됨")
    print(f"  파일: {output_file}")
    print(f"  아이템: {len(translations.get('items', {}))}개")
    print(f"  스탯: {len(translations.get('stats', {}))}개")
    print("=" * 50)


if __name__ == "__main__":
    main()
