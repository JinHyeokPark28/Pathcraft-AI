# -*- coding: utf-8 -*-
"""
POE Translation Extractor
GGPK 파일에서 한국어/영어 번역 데이터 추출

사용법:
    python poe_translation_extractor.py --poe-path "C:\Program Files (x86)\Steam\steamapps\common\Path of Exile"
"""

import os
import json
import argparse
from typing import Dict, List, Optional

def find_poe_installation() -> Optional[str]:
    """POE 설치 경로 자동 탐지"""
    possible_paths = [
        # Steam
        r"C:\Program Files (x86)\Steam\steamapps\common\Path of Exile",
        r"D:\Steam\steamapps\common\Path of Exile",
        r"E:\Steam\steamapps\common\Path of Exile",
        r"F:\Steam\steamapps\common\Path of Exile",
        # Standalone
        r"C:\Program Files (x86)\Grinding Gear Games\Path of Exile",
        r"C:\Program Files\Grinding Gear Games\Path of Exile",
        r"D:\Games\Path of Exile",
        r"C:\Games\Path of Exile",
        r"D:\Path of Exile",
    ]

    for path in possible_paths:
        ggpk_path = os.path.join(path, "Content.ggpk")
        if os.path.exists(ggpk_path):
            return path

    return None


def extract_translations(poe_path: str, output_dir: str) -> Dict:
    """
    GGPK에서 번역 데이터 추출

    PyPoE가 필요합니다: pip install PyPoE
    """
    try:
        from PyPoE.poe.file.ggpk import GGPKFile
        from PyPoE.poe.file.dat import DatFile, RelationalReader
        from PyPoE.poe.file.translations import TranslationFileCache
    except ImportError:
        print("[ERROR] PyPoE가 설치되지 않았습니다.")
        print("        pip install PyPoE")
        return {}

    ggpk_path = os.path.join(poe_path, "Content.ggpk")
    if not os.path.exists(ggpk_path):
        print(f"[ERROR] Content.ggpk를 찾을 수 없습니다: {ggpk_path}")
        return {}

    print(f"[INFO] GGPK 파일 로딩: {ggpk_path}")
    print("[INFO] 이 작업은 몇 분이 걸릴 수 있습니다...")

    # GGPK 읽기
    ggpk = GGPKFile()
    ggpk.read(ggpk_path)
    ggpk.directory_build()

    translations = {
        "skills": {},           # 스킬 젬 (영어 -> 한국어)
        "skills_kr": {},        # 스킬 젬 (한국어 -> 영어)
        "support_gems": {},     # 서포트 젬
        "mods": {},             # 아이템 모드
        "map_mods": {},         # 지도 모드
        "uniques": {},          # 유니크 아이템
        "base_items": {},       # 기본 아이템
        "passives": {},         # 패시브 스킬
        "keystones": {},        # 키스톤
        "stats": {},            # 스탯 번역
    }

    # 영어 데이터 먼저 로드
    print("[INFO] 영어 데이터 추출 중...")
    en_skills = extract_dat_file(ggpk, "Data/ActiveSkills.dat")
    en_gems = extract_dat_file(ggpk, "Data/SkillGems.dat")

    # 한국어 데이터 로드
    print("[INFO] 한국어 데이터 추출 중...")
    kr_skills = extract_dat_file(ggpk, "Data/Korean/ActiveSkills.dat")
    kr_gems = extract_dat_file(ggpk, "Data/Korean/SkillGems.dat")

    # 스킬 매핑
    if en_skills and kr_skills:
        for i, en_skill in enumerate(en_skills):
            if i < len(kr_skills):
                en_name = en_skill.get('DisplayedName', '')
                kr_name = kr_skills[i].get('DisplayedName', '')
                if en_name and kr_name:
                    translations["skills"][en_name] = kr_name
                    translations["skills_kr"][kr_name] = en_name

    # 결과 저장
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "poe_translations.json")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)

    print(f"[OK] 번역 데이터 저장: {output_file}")
    print(f"     스킬: {len(translations['skills'])}개")

    return translations


def extract_dat_file(ggpk, dat_path: str) -> List[Dict]:
    """DAT 파일에서 데이터 추출"""
    try:
        from PyPoE.poe.file.dat import DatFile

        node = ggpk[dat_path]
        if node is None:
            print(f"[WARN] 파일을 찾을 수 없음: {dat_path}")
            return []

        dat = DatFile()
        dat.read(node.record.extract())

        # 데이터를 딕셔너리 리스트로 변환
        result = []
        for row in dat.reader:
            row_dict = {}
            for spec in dat.reader.specification:
                try:
                    row_dict[spec['key']] = row[spec['key']]
                except:
                    pass
            result.append(row_dict)

        return result
    except Exception as e:
        print(f"[ERROR] DAT 추출 실패 ({dat_path}): {e}")
        return []


def create_skill_mapping_manual() -> Dict:
    """
    수동으로 작성한 주요 스킬 한국어 매핑
    PyPoE 없이도 사용 가능
    """
    return {
        # 영어 -> 한국어
        "skills": {
            # Fire
            "Righteous Fire": "정의의 화염",
            "Flameblast": "화염 폭발",
            "Fireball": "화염구",
            "Incinerate": "소각",
            "Flame Surge": "화염 쇄도",
            "Fire Trap": "화염 덫",
            "Flamethrower Trap": "화염방사기 덫",
            "Cremation": "화장",
            "Detonate Dead": "시체 폭발",

            # Cold
            "Freezing Pulse": "얼음 칼날",
            "Ice Nova": "얼음 회오리",
            "Ice Spear": "얼음 창",
            "Arctic Breath": "극한의 숨결",
            "Vortex": "소용돌이",
            "Cold Snap": "한파",
            "Creeping Frost": "서리 덩굴",
            "Eye of Winter": "겨울의 눈",

            # Lightning
            "Arc": "전기불꽃",
            "Spark": "불꽃",
            "Lightning Strike": "번개 타격",
            "Storm Call": "폭풍의 부름",
            "Ball Lightning": "구형 번개",
            "Orb of Storms": "폭풍의 구",
            "Crackling Lance": "갈라지는 창",
            "Storm Brand": "폭풍 낙인",

            # Chaos/Physical
            "Essence Drain": "정수 흡수",
            "Contagion": "전염",
            "Bane": "파멸",
            "Blight": "역병",
            "Blade Vortex": "칼날 소용돌이",
            "Ethereal Knives": "영체 칼날",
            "Bladefall": "칼날비",
            "Blade Blast": "칼날 폭발",
            "Forbidden Rite": "금단의 의식",
            "Corrupting Fever": "부패의 열기",

            # Bow
            "Tornado Shot": "회오리 사격",
            "Lightning Arrow": "번개 화살",
            "Ice Shot": "얼음 화살",
            "Explosive Arrow": "폭발 화살",
            "Rain of Arrows": "화살비",
            "Caustic Arrow": "부식성 화살",
            "Scourge Arrow": "재앙의 화살",
            "Galvanic Arrow": "전기 화살",

            # Melee
            "Cyclone": "회전 베기",
            "Earthquake": "지진",
            "Ground Slam": "대지 강타",
            "Tectonic Slam": "지각 강타",
            "Sunder": "분쇄",
            "Boneshatter": "뼛조각 타격",
            "Lightning Strike": "번개 타격",
            "Molten Strike": "용암 타격",
            "Frost Blades": "서리 칼날",
            "Wild Strike": "야생 타격",
            "Flicker Strike": "점멸 타격",
            "Double Strike": "이중 타격",
            "Lacerate": "절개",
            "Reave": "베어가르기",
            "Blade Flurry": "칼날 선풍",
            "Spectral Throw": "환영 무기 투척",
            "Spectral Helix": "환영 회전투척",
            "Shield Crush": "방패 분쇄",
            "Spectral Shield Throw": "환영 방패 투척",

            # Minions
            "Raise Zombie": "좀비 소환",
            "Raise Spectre": "환령 소환",
            "Summon Skeletons": "해골 소환",
            "Summon Raging Spirit": "분노하는 영혼 소환",
            "Animate Guardian": "수호자 소환",
            "Animate Weapon": "무기 소환",
            "Summon Carrion Golem": "사체 골렘 소환",
            "Summon Stone Golem": "돌 골렘 소환",
            "Absolution": "죄사함",

            # Totems
            "Holy Flame Totem": "신성한 화염 토템",
            "Ancestral Warchief": "선조의 전쟁추장",
            "Ancestral Protector": "선조의 수호자",

            # Traps/Mines
            "Seismic Trap": "지진 덫",
            "Exsanguinate": "방혈",
            "Lightning Trap": "번개 덫",
            "Icicle Mine": "고드름 지뢰",
            "Pyroclast Mine": "화산탄 지뢰",

            # Other
            "Death Aura": "죽음의 오라",
            "Discharge": "방출",
            "Cast when Damage Taken": "피해 시 시전",
            "Cast On Critical Strike": "치명타 시 시전",
        },

        # 한국어 -> 영어 (역방향)
        "skills_kr": {}
    }


def build_reverse_mapping(translations: Dict) -> Dict:
    """영어->한국어 매핑에서 한국어->영어 역매핑 생성"""
    if "skills" in translations:
        translations["skills_kr"] = {v: k for k, v in translations["skills"].items()}
    return translations


def main():
    parser = argparse.ArgumentParser(description='POE 번역 데이터 추출')
    parser.add_argument('--poe-path', type=str, help='POE 설치 경로')
    parser.add_argument('--output', type=str, default='./data', help='출력 디렉토리')
    parser.add_argument('--manual', action='store_true', help='수동 매핑만 사용 (PyPoE 없이)')

    args = parser.parse_args()

    if args.manual:
        print("[INFO] 수동 매핑 생성 중...")
        translations = create_skill_mapping_manual()
        translations = build_reverse_mapping(translations)

        os.makedirs(args.output, exist_ok=True)
        output_file = os.path.join(args.output, "poe_translations.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)

        print(f"[OK] 수동 매핑 저장: {output_file}")
        print(f"     스킬: {len(translations['skills'])}개")
        return

    # POE 경로 확인
    poe_path = args.poe_path
    if not poe_path:
        poe_path = find_poe_installation()
        if not poe_path:
            print("[ERROR] POE 설치 경로를 찾을 수 없습니다.")
            print("        --poe-path 옵션으로 경로를 지정해주세요.")
            print("        또는 --manual 옵션으로 수동 매핑을 사용하세요.")
            return

    print(f"[INFO] POE 경로: {poe_path}")

    # 번역 추출
    extract_translations(poe_path, args.output)


if __name__ == "__main__":
    main()
