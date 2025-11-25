"""
poedb.tw 크롤러
- 퀘스트 보상 (젬 획득 정보)
- 젬 required_level
- 벤더 레시피

사용법:
    python poedb_crawler.py --target quest_rewards
    python poedb_crawler.py --target gem_levels
    python poedb_crawler.py --target vendor_recipes
    python poedb_crawler.py --target all
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
import sys
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

# Selenium imports for dynamic content
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 설정
BASE_URL = "https://poedb.tw"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}
REQUEST_DELAY = 1.5  # 초 (서버 부담 방지)
DATA_DIR = Path(__file__).parent / "data"


def fetch_page(url: str) -> BeautifulSoup:
    """페이지 가져오기"""
    print(f"  Fetching: {url}")
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    time.sleep(REQUEST_DELAY)
    return BeautifulSoup(response.text, "html.parser")


def crawl_quest_rewards() -> Dict[str, Any]:
    """
    퀘스트 보상 크롤링
    - 각 액트별 퀘스트에서 얻는 젬
    - 클래스별 보상 차이
    """
    print("\n=== 퀘스트 보상 크롤링 시작 ===")

    import re

    quest_data = {
        "version": "3.25",
        "source": "poedb.tw",
        "classes": ["Marauder", "Witch", "Scion", "Ranger", "Duelist", "Shadow", "Templar"],
        "quests": []
    }

    # 영문 페이지 사용 (더 정확한 파싱)
    soup = fetch_page(f"{BASE_URL}/us/Quest")

    # 모든 테이블 검색
    tables = soup.find_all("table")
    print(f"  발견된 테이블: {len(tables)}개")

    for table_idx, table in enumerate(tables):
        # 헤더 행 찾기
        header_row = table.find("tr")
        if not header_row:
            continue

        headers = header_row.find_all(["th", "td"])
        header_texts = [h.get_text(strip=True) for h in headers]

        # 클래스 이름이 헤더에 있는지 확인
        if not any(cls in str(header_texts) for cls in ["Marauder", "Witch", "Ranger"]):
            continue

        print(f"  테이블 {table_idx}: 클래스별 보상 테이블 발견")

        # 데이터 행 처리
        rows = table.find_all("tr")[1:]  # 헤더 제외

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            # 첫 번째 셀: 퀘스트 정보
            quest_cell = cells[0]
            quest_link = quest_cell.find("a")

            if quest_link:
                quest_name = quest_link.get_text(strip=True)
            else:
                quest_name = quest_cell.get_text(strip=True)

            if not quest_name:
                continue

            # 액트 번호 추출
            cell_text = quest_cell.get_text()
            act_match = re.search(r'Act\s*(\d+)', cell_text)
            act_num = int(act_match.group(1)) if act_match else 0

            # 각 클래스별 보상 추출
            rewards_by_class = {}
            class_names = ["Marauder", "Witch", "Scion", "Ranger", "Duelist", "Shadow", "Templar"]

            for i, cell in enumerate(cells[1:]):
                if i >= len(class_names):
                    break

                class_name = class_names[i]
                gems = []

                # 셀 내의 모든 젬 링크 추출
                gem_links = cell.find_all("a")
                for gem_link in gem_links:
                    gem_name = gem_link.get_text(strip=True)
                    if gem_name and len(gem_name) > 1:
                        gems.append(gem_name)

                rewards_by_class[class_name] = gems

            if quest_name and rewards_by_class:
                quest_data["quests"].append({
                    "name": quest_name,
                    "act": act_num,
                    "rewards": rewards_by_class
                })

    print(f"수집된 퀘스트: {len(quest_data['quests'])}개")

    # 샘플 출력
    if quest_data["quests"]:
        sample = quest_data["quests"][0]
        print(f"  예시: {sample['name']} (Act {sample['act']})")
        for cls, gems in list(sample["rewards"].items())[:2]:
            print(f"    {cls}: {gems[:3]}...")

    return quest_data


def crawl_quest_rewards_alternative(soup: BeautifulSoup) -> Dict[str, Any]:
    """대안 파싱 방법 - 링크와 텍스트 기반"""
    import re

    quest_data = {
        "version": "3.25",
        "source": "poedb.tw",
        "quests": []
    }

    # 모든 링크에서 퀘스트 관련 정보 추출
    all_links = soup.find_all("a", href=True)

    current_quest = None
    current_act = 0

    for link in all_links:
        href = link.get("href", "")
        text = link.get_text(strip=True)

        # 퀘스트 링크 감지
        if "/kr/" in href and text:
            # 액트 번호 찾기 (링크 주변 텍스트)
            parent = link.parent
            if parent:
                parent_text = parent.get_text()
                act_match = re.search(r'Act\s*(\d+)', parent_text)
                if act_match:
                    current_act = int(act_match.group(1))

            # 퀘스트 이름인지 젬 이름인지 구분
            # 일반적으로 퀘스트는 더 긴 이름을 가짐
            if len(text) > 3:
                # 기존 퀘스트 저장
                if current_quest and current_quest.get("rewards"):
                    quest_data["quests"].append(current_quest)

                current_quest = {
                    "name": text,
                    "act": current_act,
                    "rewards": []
                }
            elif current_quest:
                # 젬으로 추가
                current_quest["rewards"].append(text)

    # 마지막 퀘스트 저장
    if current_quest and current_quest.get("rewards"):
        quest_data["quests"].append(current_quest)

    return quest_data


def extract_quest_rewards(soup: BeautifulSoup) -> List[Dict]:
    """퀘스트 페이지에서 보상 추출"""
    rewards = []

    # 보상 테이블 찾기
    tables = soup.find_all("table", class_="table")

    for table in tables:
        # 테이블 헤더 확인
        headers = table.find_all("th")
        header_text = " ".join([h.get_text(strip=True) for h in headers])

        # 젬 보상 테이블인지 확인
        if "Gem" not in header_text and "젬" not in header_text and "Reward" not in header_text:
            continue

        rows = table.find_all("tr")[1:]  # 헤더 제외

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue

            # 젬 이름 추출
            gem_link = cols[0].find("a")
            if gem_link:
                gem_name = gem_link.get_text(strip=True)

                # 클래스 정보 추출
                classes = []
                for col in cols[1:]:
                    class_text = col.get_text(strip=True)
                    if class_text and class_text not in ["", "-", "X"]:
                        # 클래스 이름 파싱
                        if "✓" in class_text or "O" in class_text:
                            # 열 헤더에서 클래스 이름 가져오기
                            col_idx = cols.index(col)
                            if col_idx < len(headers):
                                class_name = headers[col_idx].get_text(strip=True)
                                classes.append(class_name)

                rewards.append({
                    "gem": gem_name,
                    "classes": classes if classes else ["All"]
                })

    return rewards


def crawl_gem_levels() -> Dict[str, Any]:
    """
    젬 required_level 크롤링
    - 각 젬의 장착 가능 레벨
    - 태그 정보
    """
    print("\n=== 젬 레벨 데이터 크롤링 시작 ===")

    import re

    gem_data = {
        "version": "3.25",
        "source": "poedb.tw",
        "gems": {}
    }

    # 영문 스킬젬 목록 페이지 (더 정확한 파싱)
    soup = fetch_page(f"{BASE_URL}/us/Skill_Gems")

    # 테이블 기반 파싱
    tables = soup.find_all("table")
    print(f"  발견된 테이블: {len(tables)}개")

    for table in tables:
        # 링크 기반으로 젬 추출
        links = table.find_all("a", href=True)

        for link in links:
            href = link.get("href", "")

            # /us/ 경로의 젬 링크만
            if not href.startswith("/us/"):
                continue

            gem_name = link.get_text(strip=True)

            # 빈 이름이나 짧은 이름 제외
            if not gem_name or len(gem_name) < 3:
                continue

            # 중복 제외
            if gem_name in gem_data["gems"]:
                continue

            # 링크 다음 텍스트에서 레벨과 태그 추출
            next_sibling = link.next_sibling
            if next_sibling:
                sibling_text = str(next_sibling)

                # (레벨) 패턴 찾기
                level_match = re.search(r'\((\d+)\)', sibling_text)
                required_level = int(level_match.group(1)) if level_match else 1

                # 태그 추출 (레벨 다음 텍스트)
                tags_match = re.search(r'\(\d+\)([^(]+)', sibling_text)
                if tags_match:
                    tags_str = tags_match.group(1)
                    tags = [t.strip() for t in tags_str.split(",") if t.strip()]
                else:
                    tags = []
            else:
                required_level = 1
                tags = []

            gem_data["gems"][gem_name] = {
                "name": gem_name,
                "required_level": required_level,
                "tags": tags,
                "url": href
            }

    print(f"수집된 젬: {len(gem_data['gems'])}개")

    # 레벨별 통계
    level_counts = {}
    for gem in gem_data["gems"].values():
        lvl = gem["required_level"]
        level_counts[lvl] = level_counts.get(lvl, 0) + 1

    print(f"  레벨별 분포: {dict(sorted(level_counts.items()))}")

    # 결과 샘플 출력
    samples = list(gem_data["gems"].items())[:5]
    for name, info in samples:
        print(f"  예시: {name} - Lv.{info['required_level']}, 태그: {info['tags'][:3]}")

    return gem_data


def extract_gem_info(soup: BeautifulSoup, gem_name: str) -> Dict:
    """젬 상세 페이지에서 정보 추출"""
    info = {
        "name": gem_name,
        "required_level": 1,
        "str": 0,
        "dex": 0,
        "int": 0,
        "tags": []
    }

    # 정보 테이블 찾기
    info_table = soup.find("table", class_="table")
    if not info_table:
        return info

    rows = info_table.find_all("tr")

    for row in rows:
        cells = row.find_all(["th", "td"])
        if len(cells) < 2:
            continue

        label = cells[0].get_text(strip=True).lower()
        value = cells[1].get_text(strip=True)

        # 레벨 요구사항
        if "level" in label or "레벨" in label:
            try:
                # "Lv. 12" 또는 "12" 형식 처리
                level_num = ''.join(filter(str.isdigit, value))
                if level_num:
                    info["required_level"] = int(level_num)
            except:
                pass

        # 스탯 요구사항
        if "str" in label or "힘" in label:
            try:
                info["str"] = int(''.join(filter(str.isdigit, value)))
            except:
                pass

        if "dex" in label or "민첩" in label:
            try:
                info["dex"] = int(''.join(filter(str.isdigit, value)))
            except:
                pass

        if "int" in label or "지능" in label:
            try:
                info["int"] = int(''.join(filter(str.isdigit, value)))
            except:
                pass

        # 태그
        if "tag" in label or "태그" in label:
            tags = [t.strip() for t in value.split(",")]
            info["tags"] = tags

    return info


def crawl_vendor_recipes() -> Dict[str, Any]:
    """
    벤더 레시피 크롤링
    - 유용한 레시피 목록
    - 재료와 결과
    """
    print("\n=== 벤더 레시피 크롤링 시작 ===")

    recipe_data = {
        "version": "3.25",
        "source": "poedb.tw",
        "recipes": []
    }

    # 벤더 레시피 페이지
    soup = fetch_page(f"{BASE_URL}/kr/Vendor_recipe_system")

    # 레시피 테이블 찾기
    tables = soup.find_all("table", class_="table")

    for table in tables:
        rows = table.find_all("tr")

        # 헤더 확인
        headers = table.find_all("th")
        if not headers:
            continue

        for row in rows[1:]:  # 헤더 제외
            cols = row.find_all("td")
            if len(cols) < 2:
                continue

            # 결과물
            result = cols[0].get_text(strip=True)

            # 재료
            ingredients = cols[1].get_text(strip=True) if len(cols) > 1 else ""

            # 노트
            note = cols[2].get_text(strip=True) if len(cols) > 2 else ""

            if result:
                recipe_data["recipes"].append({
                    "result": result,
                    "ingredients": ingredients,
                    "note": note,
                    "category": categorize_recipe(result)
                })

    # 카테고리별 정렬
    recipe_data["recipes"].sort(key=lambda x: x["category"])

    print(f"총 {len(recipe_data['recipes'])}개 레시피 수집")

    return recipe_data


def categorize_recipe(result: str) -> str:
    """레시피 카테고리 분류"""
    result_lower = result.lower()

    if "gem" in result_lower or "젬" in result:
        return "gem"
    elif "currency" in result_lower or "화폐" in result:
        return "currency"
    elif "flask" in result_lower or "플라스크" in result:
        return "flask"
    elif "weapon" in result_lower or "무기" in result:
        return "weapon"
    elif "armour" in result_lower or "방어구" in result:
        return "armour"
    else:
        return "other"


def crawl_mod_pool() -> Dict[str, Any]:
    """
    아이템 모드풀 크롤링 (poedb.tw 사용)
    - 접두사/접미사 모드
    - 아이템 타입별 가능한 모드
    - 티어별 수치
    """
    print("\n=== 모드풀 데이터 크롤링 시작 (poedb.tw) ===")

    import re

    mod_data = {
        "version": "3.25",
        "source": "poedb.tw",
        "item_types": {},
        "all_mods": {}
    }

    # poedb.tw URL 패턴 - 속성별 분류
    # 방어구는 str/dex/int 및 하이브리드로 분류됨
    item_types = [
        # Helmets
        ("Helmets_str", "helmet_str"),
        ("Helmets_dex", "helmet_dex"),
        ("Helmets_int", "helmet_int"),
        ("Helmets_str_dex", "helmet_str_dex"),
        ("Helmets_str_int", "helmet_str_int"),
        ("Helmets_dex_int", "helmet_dex_int"),

        # Body Armours
        ("Body_Armours_str", "body_armour_str"),
        ("Body_Armours_dex", "body_armour_dex"),
        ("Body_Armours_int", "body_armour_int"),
        ("Body_Armours_str_dex", "body_armour_str_dex"),
        ("Body_Armours_str_int", "body_armour_str_int"),
        ("Body_Armours_dex_int", "body_armour_dex_int"),

        # Gloves
        ("Gloves_str", "gloves_str"),
        ("Gloves_dex", "gloves_dex"),
        ("Gloves_int", "gloves_int"),
        ("Gloves_str_dex", "gloves_str_dex"),
        ("Gloves_str_int", "gloves_str_int"),
        ("Gloves_dex_int", "gloves_dex_int"),

        # Boots
        ("Boots_str", "boots_str"),
        ("Boots_dex", "boots_dex"),
        ("Boots_int", "boots_int"),
        ("Boots_str_dex", "boots_str_dex"),
        ("Boots_str_int", "boots_str_int"),
        ("Boots_dex_int", "boots_dex_int"),

        # Shields
        ("Shields_str", "shield_str"),
        ("Shields_dex", "shield_dex"),
        ("Shields_int", "shield_int"),
        ("Shields_str_dex", "shield_str_dex"),
        ("Shields_str_int", "shield_str_int"),
        ("Shields_dex_int", "shield_dex_int"),

        # Accessories (속성 구분 없음)
        ("Belts", "belt"),
        ("Amulets", "amulet"),
        ("Rings", "ring"),
        ("Quivers", "quiver"),

        # Weapons
        ("Wands", "wand"),
        ("Sceptres", "sceptre"),
        ("Daggers", "dagger"),
        ("Rune_Daggers", "rune_dagger"),
        ("Claws", "claw"),
        ("One_Hand_Swords", "sword_1h"),
        ("Two_Hand_Swords", "sword_2h"),
        ("Thrusting_One_Hand_Swords", "rapier"),
        ("One_Hand_Axes", "axe_1h"),
        ("Two_Hand_Axes", "axe_2h"),
        ("One_Hand_Maces", "mace_1h"),
        ("Two_Hand_Maces", "mace_2h"),
        ("Bows", "bow"),
        ("Staves", "staff"),
        ("Warstaves", "warstaff")
    ]

    for poedb_page, item_type in item_types:
        print(f"  크롤링: {item_type}...")

        try:
            # poedb.tw URL 패턴
            url = f"{BASE_URL}/us/{poedb_page}#ModifiersCalc"
            response = requests.get(url, headers=HEADERS, timeout=30)

            if response.status_code != 200:
                print(f"    ⚠ 페이지 로드 실패: {poedb_page} ({response.status_code})")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            item_mods = []

            # poedb.tw 테이블 구조: table.table-hover.table-striped.orig
            # #ModifiersCalc 섹션 내의 테이블 찾기
            modifiers_section = soup.find(id="ModifiersCalc")

            if modifiers_section:
                tables = modifiers_section.find_all("table", class_="orig")
            else:
                # 폴백: 페이지 전체에서 orig 테이블 찾기
                tables = soup.find_all("table", class_="orig")

            for table in tables:
                # Caption에서 모드 패밀리 추출 (예: "Family: Strength")
                caption = table.find("caption")
                family = ""
                if caption:
                    family_text = caption.get_text(strip=True)
                    if ":" in family_text:
                        family = family_text.split(":", 1)[1].strip()
                    else:
                        family = family_text

                # 테이블 행 처리
                rows = table.find_all("tr")

                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) < 2:
                        continue

                    # TD[0]: 모드 이름
                    mod_cell = cells[0]
                    mod_name = mod_cell.get_text(strip=True)

                    if not mod_name or len(mod_name) < 2:
                        continue

                    # TD[1]: 아이템 레벨
                    ilvl = 1
                    if len(cells) > 1:
                        ilvl_text = cells[1].get_text(strip=True)
                        ilvl_match = re.search(r'(\d+)', ilvl_text)
                        if ilvl_match:
                            ilvl = int(ilvl_match.group(1))

                    # TD[2]: badges/tags
                    raw_tags = []
                    if len(cells) > 2:
                        badges = cells[2].find_all(class_="badge")
                        for badge in badges:
                            tag = badge.get("data-tag") or badge.get_text(strip=True)
                            if tag:
                                raw_tags.append(tag.lower())

                    # 모드 이름에서 효과 추출 (poedb는 이름에 효과가 포함됨)
                    effect = mod_name  # poedb에서는 이름이 효과 설명

                    # 태그 추출
                    tags = extract_mod_tags(effect)
                    if family:
                        tags.append(family.lower())

                    # 카테고리 결정 (영향력 기반)
                    category = "standard"
                    for tag in raw_tags:
                        if tag in ["shaper", "elder", "crusader", "redeemer", "hunter", "warlord"]:
                            category = tag
                            break

                    mod_entry = {
                        "name": mod_name,
                        "effect": effect,
                        "ilvl": ilvl,
                        "tags": list(set(tags + raw_tags)),
                        "family": family,
                        "category": category
                    }

                    item_mods.append(mod_entry)

                    # 전역 모드 데이터베이스에 추가
                    if mod_name not in mod_data["all_mods"]:
                        mod_data["all_mods"][mod_name] = {
                            "effect": effect,
                            "tags": list(set(tags + raw_tags)),
                            "item_types": [item_type],
                            "family": family,
                            "category": category
                        }
                    else:
                        if item_type not in mod_data["all_mods"][mod_name]["item_types"]:
                            mod_data["all_mods"][mod_name]["item_types"].append(item_type)

            mod_data["item_types"][item_type] = item_mods

            print(f"    ✓ {item_type}: {len(item_mods)}개 모드")

            # 요청 간 딜레이
            time.sleep(REQUEST_DELAY)

        except Exception as e:
            print(f"    ✗ 에러: {e}")
            import traceback
            traceback.print_exc()
            continue

    # 통계
    total_mods = sum(len(mods) for mods in mod_data["item_types"].values())

    print(f"\n총 모드 수집:")
    print(f"  - 총 모드: {total_mods}개")
    print(f"  - 고유 모드: {len(mod_data['all_mods'])}개")
    print(f"  - 아이템 타입: {len(mod_data['item_types'])}개")

    return mod_data


def extract_mod_tags(effect: str) -> List[str]:
    """모드 효과에서 태그 추출"""
    tags = []
    effect_lower = effect.lower()

    if "life" in effect_lower:
        tags.append("life")
    if "mana" in effect_lower:
        tags.append("mana")
    if "energy shield" in effect_lower:
        tags.append("energy_shield")
    if "resist" in effect_lower:
        tags.append("resistance")
    if "damage" in effect_lower:
        tags.append("damage")
    if "speed" in effect_lower:
        tags.append("speed")
    if "critical" in effect_lower:
        tags.append("critical")
    if "spell" in effect_lower:
        tags.append("spell")
    if "attack" in effect_lower:
        tags.append("attack")
    if "fire" in effect_lower:
        tags.append("fire")
    if "cold" in effect_lower:
        tags.append("cold")
    if "lightning" in effect_lower:
        tags.append("lightning")
    if "chaos" in effect_lower:
        tags.append("chaos")
    if "physical" in effect_lower:
        tags.append("physical")
    if "minion" in effect_lower:
        tags.append("minion")

    return tags


def get_important_mods_for_build(build_type: str) -> Dict[str, List[str]]:
    """
    빌드 타입에 따른 중요 모드 추출

    Args:
        build_type: spell, attack, minion, dot 등

    Returns:
        prefix와 suffix 중요 모드 목록
    """
    important_mods = {
        "prefix": [],
        "suffix": []
    }

    # 빌드 타입별 중요 키워드
    if build_type == "spell":
        important_mods["prefix"] = [
            "Spell Damage",
            "Fire Damage",
            "Cold Damage",
            "Lightning Damage",
            "Chaos Damage",
            "Gem Level",
            "Maximum Life",
            "Maximum Energy Shield"
        ]
        important_mods["suffix"] = [
            "Cast Speed",
            "Critical Strike Chance for Spells",
            "Critical Strike Multiplier",
            "Fire Resistance",
            "Cold Resistance",
            "Lightning Resistance",
            "Chaos Resistance"
        ]
    elif build_type == "attack":
        important_mods["prefix"] = [
            "Physical Damage",
            "Adds Physical Damage",
            "Elemental Damage with Attacks",
            "Maximum Life",
            "Accuracy Rating"
        ]
        important_mods["suffix"] = [
            "Attack Speed",
            "Critical Strike Chance",
            "Critical Strike Multiplier",
            "Accuracy Rating",
            "Fire Resistance",
            "Cold Resistance",
            "Lightning Resistance"
        ]
    elif build_type == "minion":
        important_mods["prefix"] = [
            "Minion Damage",
            "Minion Life",
            "Gem Level",
            "Maximum Life"
        ]
        important_mods["suffix"] = [
            "Minion Speed",
            "Minion Resistances",
            "Fire Resistance",
            "Cold Resistance",
            "Lightning Resistance"
        ]
    elif build_type == "dot":
        important_mods["prefix"] = [
            "Damage over Time",
            "Fire Damage",
            "Cold Damage",
            "Chaos Damage",
            "Maximum Life"
        ]
        important_mods["suffix"] = [
            "Damage over Time Multiplier",
            "Fire Resistance",
            "Cold Resistance",
            "Lightning Resistance",
            "Chaos Resistance"
        ]

    return important_mods


def save_data(data: Dict, filename: str):
    """데이터 저장"""
    filepath = DATA_DIR / filename

    # 디렉토리 생성
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    file_size = os.path.getsize(filepath) / 1024
    print(f"\n✓ 저장 완료: {filepath} ({file_size:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(description="poedb.tw 크롤러")
    parser.add_argument(
        "--target",
        choices=["quest_rewards", "gem_levels", "vendor_recipes", "mod_pool", "all"],
        default="all",
        help="크롤링 대상"
    )
    args = parser.parse_args()

    print("=" * 50)
    print("poedb.tw 크롤러 시작")
    print("=" * 50)

    if args.target in ["quest_rewards", "all"]:
        data = crawl_quest_rewards()
        save_data(data, "quest_rewards.json")

    if args.target in ["gem_levels", "all"]:
        data = crawl_gem_levels()
        save_data(data, "gem_levels.json")

    if args.target in ["vendor_recipes", "all"]:
        data = crawl_vendor_recipes()
        save_data(data, "vendor_recipes.json")

    if args.target in ["mod_pool", "all"]:
        data = crawl_mod_pool()
        save_data(data, "mod_pool.json")

    print("\n" + "=" * 50)
    print("크롤링 완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()
