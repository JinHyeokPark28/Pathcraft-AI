# -*- coding: utf-8 -*-
"""
POE Translation Extractor from PoeCharm/POB Translation Files
PoeCharm의 한국어 번역 CSV 파일에서 번역 데이터 추출

사용법:
    python poe_pob_translation_extractor.py --translate-path "C:\\Users\\User\\Desktop\\PoeCharm3-20250414\\Data\\Translate\\ko-KR"
"""

import os
import csv
import json
import argparse
from typing import Dict, List

def parse_csv_translations(file_path: str) -> Dict[str, str]:
    """CSV 파일에서 영어->한국어 번역 추출"""
    translations = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    en_text = row[0].strip()
                    kr_text = row[1].strip()
                    if en_text and kr_text:
                        translations[en_text] = kr_text
    except Exception as e:
        print(f"[WARN] Failed to parse {file_path}: {e}")

    return translations


def extract_all_translations(translate_dir: str) -> Dict:
    """모든 번역 파일에서 데이터 추출"""

    all_translations = {
        "skills": {},           # 스킬 젬 (영어 -> 한국어)
        "skills_kr": {},        # 스킬 젬 (한국어 -> 영어)
        "items": {},            # 아이템
        "items_kr": {},
        "passives": {},         # 패시브
        "passives_kr": {},
        "mods": {},             # 모드
        "mods_kr": {},
        "base_types": {},       # 기본 타입
        "base_types_kr": {},
        "uniques": {},          # 유니크
        "uniques_kr": {},
        "misc": {},             # 기타
        "misc_kr": {},
    }

    # 파일별 매핑
    file_mappings = {
        "Items_Gems.txt.csv": "skills",
        "Gems_tag.csv": "skills",
        "BaseType.csv": "base_types",
        "Uniques.txt.csv": "uniques",
        "WeaponUnique.csv": "uniques",
        "passiveTree.csv": "passives",
        "statDescriptions.csv": "mods",
        "stats_words_prefix.csv": "mods",
        "stats_words_suffix.csv": "mods",
        "Items_Armour.txt.csv": "items",
        "Items_Weapons.txt.csv": "items",
        "Items_Accessories.txt.csv": "items",
        "Items_Jewels.txt.csv": "items",
    }

    print(f"[INFO] 번역 디렉토리: {translate_dir}")

    # 각 파일 처리
    for filename, category in file_mappings.items():
        file_path = os.path.join(translate_dir, filename)
        if os.path.exists(file_path):
            translations = parse_csv_translations(file_path)
            all_translations[category].update(translations)
            print(f"[OK] {filename}: {len(translations)}개 항목")
        else:
            print(f"[SKIP] {filename} 없음")

    # 나머지 CSV 파일도 처리 (misc로)
    for filename in os.listdir(translate_dir):
        if filename.endswith('.csv') and filename not in file_mappings:
            file_path = os.path.join(translate_dir, filename)
            translations = parse_csv_translations(file_path)
            all_translations["misc"].update(translations)

    # 역방향 매핑 생성 (한국어 -> 영어)
    for category in ["skills", "items", "passives", "mods", "base_types", "uniques", "misc"]:
        kr_category = f"{category}_kr"
        all_translations[kr_category] = {v: k for k, v in all_translations[category].items()}

    return all_translations


def main():
    parser = argparse.ArgumentParser(description='PoeCharm 번역 데이터 추출')
    parser.add_argument('--translate-path', type=str,
                        default=r"C:\Users\User\Desktop\PoeCharm3-20250414\Data\Translate\ko-KR",
                        help='PoeCharm 번역 디렉토리 경로')
    parser.add_argument('--output', type=str, default='./data', help='출력 디렉토리')

    args = parser.parse_args()

    if not os.path.exists(args.translate_path):
        print(f"[ERROR] 번역 디렉토리를 찾을 수 없습니다: {args.translate_path}")
        return

    # 번역 추출
    translations = extract_all_translations(args.translate_path)

    # 저장
    os.makedirs(args.output, exist_ok=True)
    output_file = os.path.join(args.output, "poe_translations.json")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)

    # 통계 출력
    print("\n" + "=" * 50)
    print("[완료] 번역 데이터 저장됨")
    print(f"  파일: {output_file}")
    print(f"  스킬: {len(translations['skills'])}개")
    print(f"  아이템: {len(translations['items'])}개")
    print(f"  패시브: {len(translations['passives'])}개")
    print(f"  모드: {len(translations['mods'])}개")
    print(f"  기본 타입: {len(translations['base_types'])}개")
    print(f"  유니크: {len(translations['uniques'])}개")
    print(f"  기타: {len(translations['misc'])}개")
    print("=" * 50)


if __name__ == "__main__":
    main()
