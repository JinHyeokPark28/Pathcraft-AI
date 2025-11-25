#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Guide Generator - 템플릿 기반 레벨링 가이드 생성
POB 코드를 입력받아 맞는 템플릿을 적용하여 가이드 출력
"""

import sys
import os
import json
import base64
import zlib
from typing import Dict, Any, Optional

# UTF-8 설정
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# 템플릿 경로
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "data", "guide_templates")
BUILDS_DIR = os.path.join(TEMPLATE_DIR, "builds")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


class KoreanTranslator:
    """POE 공식 한국어 번역 헬퍼"""

    def __init__(self):
        self.translations = {}
        self.reverse_translations = {}  # 한국어 -> 영어
        self._load_translations()

    def _load_translations(self):
        """번역 데이터 로드"""
        # awakened_translations.json이 가장 포괄적
        awakened_path = os.path.join(DATA_DIR, "awakened_translations.json")
        merged_path = os.path.join(DATA_DIR, "merged_translations.json")

        # awakened_translations 로드
        if os.path.exists(awakened_path):
            try:
                with open(awakened_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 스킬 젬 번역
                    if 'skills' in data:
                        for en, ko in data['skills'].items():
                            self.translations[en.lower()] = ko
                            self.reverse_translations[ko] = en
                    # 아이템 번역
                    if 'items' in data:
                        for en, ko in data['items'].items():
                            self.translations[en.lower()] = ko
                            self.reverse_translations[ko] = en
                    # 스탯/모드 번역
                    if 'mods' in data:
                        for en, ko in data['mods'].items():
                            self.translations[en.lower()] = ko
                    # 직접 매핑 (최상위 레벨)
                    for key, value in data.items():
                        if isinstance(value, str) and key not in ['source', 'version']:
                            self.translations[key.lower()] = value
            except Exception as e:
                print(f"[WARN] awakened_translations 로드 실패: {e}")

        # merged_translations 로드 (추가)
        if os.path.exists(merged_path):
            try:
                with open(merged_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # items 필드 (영어 -> 한국어)
                    if 'items' in data:
                        for en, ko in data['items'].items():
                            if en.lower() not in self.translations:
                                self.translations[en.lower()] = ko
                    # skills 필드 (영어 -> 한국어)
                    if 'skills' in data:
                        for en, ko in data['skills'].items():
                            if en.lower() not in self.translations:
                                self.translations[en.lower()] = ko
                    # items_kr 필드 (한국어 -> 영어, 반전 필요)
                    if 'items_kr' in data:
                        for ko, en in data['items_kr'].items():
                            if en.lower() not in self.translations:
                                self.translations[en.lower()] = ko
                                self.reverse_translations[ko] = en
                    # skills_kr 필드 (한국어 -> 영어, 반전 필요)
                    if 'skills_kr' in data:
                        for ko, en in data['skills_kr'].items():
                            if en.lower() not in self.translations:
                                self.translations[en.lower()] = ko
                                self.reverse_translations[ko] = en
                    # stats_kr 필드 (한국어 -> 영어, 반전 필요)
                    if 'stats_kr' in data:
                        for ko, en in data['stats_kr'].items():
                            if en.lower() not in self.translations:
                                self.translations[en.lower()] = ko
            except Exception as e:
                print(f"[WARN] merged_translations 로드 실패: {e}")

        # 수동 추가: 게임 메커니즘 용어
        self._add_game_terms()

    def _add_game_terms(self):
        """게임 메커니즘 관련 용어 추가"""
        game_terms = {
            # 리그 메커니즘
            "delirium": "환영",
            "blight": "역병",
            "breach": "균열",
            "abyss": "심연",
            "legion": "군단",
            "metamorph": "메타몰프",
            "ritual": "의식",
            "ultimatum": "결전",
            "expedition": "탐험",
            "heist": "강탈",
            "harvest": "수확",
            "incursion": "침입",
            "delve": "탐광",
            "betrayal": "배신",
            "synthesis": "합성",

            # 게임 용어
            "simulacrum": "복제된 영토",
            "scarab": "갑충석",
            "fossil": "화석",
            "resonator": "공명기",
            "essence": "에센스",
            "currency": "화폐",
            "fragment": "파편",
            "splinter": "조각",

            # 아이템 등급
            "normal": "일반",
            "magic": "마법",
            "rare": "희귀",
            "unique": "고유",

            # 속성
            "fire": "화염",
            "cold": "냉기",
            "lightning": "번개",
            "chaos": "카오스",
            "physical": "물리",

            # 방어
            "armour": "방어도",
            "evasion": "회피",
            "energy shield": "에너지 보호막",
            "life": "생명력",
            "mana": "마나",
            "resistance": "저항",

            # 공격/스펠
            "attack": "공격",
            "spell": "스펠",
            "minion": "소환수",
            "totem": "토템",
            "trap": "덫",
            "mine": "지뢰",

            # 기타
            "critical strike": "치명타",
            "critical": "치명타",
            "leech": "흡수",
            "regeneration": "재생",
            "flask": "플라스크",
            "aura": "오라",
            "curse": "저주",
            "herald": "전령",

            # 파밍 장소
            "map": "지도",
            "boss": "보스",
            "monster": "몬스터",
        }

        # 게임 용어는 공식 번역으로 덮어쓰기 (우선순위 높음)
        for en, ko in game_terms.items():
            self.translations[en] = ko

    def translate(self, text: str, keep_english: bool = False) -> str:
        """텍스트 번역

        Args:
            text: 번역할 텍스트
            keep_english: True면 "한국어 (English)" 형식으로 반환
        """
        if not text:
            return text

        # 정확한 매칭
        lower_text = text.lower()
        if lower_text in self.translations:
            ko = self.translations[lower_text]
            if keep_english:
                return f"{ko} ({text})"
            return ko

        # 부분 매칭 시도 (긴 것부터)
        result = text
        for en, ko in sorted(self.translations.items(), key=lambda x: len(x[0]), reverse=True):
            if en in lower_text:
                # 대소문자 무시하고 치환
                import re
                pattern = re.compile(re.escape(en), re.IGNORECASE)
                result = pattern.sub(ko, result)

        return result

    def translate_skill(self, skill_name: str) -> str:
        """스킬 이름 번역"""
        # 이미 "한국어 (English)" 형식이면 그대로 반환
        if " (" in skill_name and skill_name.endswith(")"):
            return skill_name
        return self.translate(skill_name, keep_english=True)

    def translate_item(self, item_name: str) -> str:
        """아이템 이름 번역"""
        # 이미 "한국어 (English)" 형식이면 그대로 반환
        if " (" in item_name and item_name.endswith(")"):
            return item_name
        return self.translate(item_name, keep_english=True)

    def extract_english_name(self, text: str) -> str:
        """'한국어 (English)' 형식에서 영어 이름 추출"""
        if " (" in text and text.endswith(")"):
            # "한국어 (English)" -> "English"
            start = text.rfind("(") + 1
            end = text.rfind(")")
            return text[start:end]
        return text


class GuideGenerator:
    """템플릿 기반 레벨링 가이드 생성기"""

    def __init__(self):
        self.translator = KoreanTranslator()
        self.common_template = self._load_template("common_template.json")
        self.archetypes = {
            "spell": self._load_template("archetype_spell.json"),
            "attack": self._load_template("archetype_attack.json"),
            "minion": self._load_template("archetype_minion.json"),
            "dot": self._load_template("archetype_dot.json")
        }
        self.builds = self._load_all_builds()

    def _load_template(self, filename: str) -> Dict:
        """템플릿 파일 로드"""
        path = os.path.join(TEMPLATE_DIR, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _load_all_builds(self) -> Dict[str, Dict]:
        """모든 빌드 템플릿 로드"""
        builds = {}
        if not os.path.exists(BUILDS_DIR):
            return builds

        for filename in os.listdir(BUILDS_DIR):
            if filename.endswith('.json'):
                path = os.path.join(BUILDS_DIR, filename)
                with open(path, 'r', encoding='utf-8') as f:
                    build_data = json.load(f)
                    build_key = filename.replace('.json', '')
                    builds[build_key] = build_data

        return builds

    def decode_pob_code(self, pob_code: str) -> Optional[str]:
        """POB 코드 디코딩"""
        try:
            # URL에서 코드 부분만 추출
            if "pastebin.com/" in pob_code:
                # pastebin은 직접 처리 불가, 코드만 필요
                print("[WARN] Pastebin URL은 지원하지 않습니다. POB 코드를 직접 입력하세요.")
                return None

            # Base64 디코딩
            pob_code = pob_code.strip().replace('-', '+').replace('_', '/')

            # 패딩 추가
            padding = 4 - len(pob_code) % 4
            if padding != 4:
                pob_code += '=' * padding

            decoded = base64.b64decode(pob_code)

            # zlib 압축 해제
            xml_data = zlib.decompress(decoded)
            return xml_data.decode('utf-8')

        except Exception as e:
            print(f"[ERROR] POB 코드 디코딩 실패: {e}")
            return None

    def extract_build_info(self, xml_content: str) -> Dict[str, Any]:
        """XML에서 빌드 정보 추출"""
        import re

        info = {
            "class": "Unknown",
            "ascendancy": "Unknown",
            "main_skill": "Unknown",
            "skills": [],
            "level": 1
        }

        # 클래스/아센던시 추출
        class_match = re.search(r'className="([^"]+)"', xml_content)
        if class_match:
            info["class"] = class_match.group(1)

        ascendancy_match = re.search(r'ascendClassName="([^"]+)"', xml_content)
        if ascendancy_match:
            info["ascendancy"] = ascendancy_match.group(1)

        # 레벨 추출
        level_match = re.search(r'level="(\d+)"', xml_content)
        if level_match:
            info["level"] = int(level_match.group(1))

        # 메인 스킬 추출 (mainSocketGroup에서)
        main_socket_match = re.search(r'mainSocketGroup="(\d+)"', xml_content)

        # 스킬 추출
        skill_pattern = r'<Skill[^>]*nameSpec="([^"]*)"[^>]*>'
        skills = re.findall(skill_pattern, xml_content)

        # enabled 스킬만 필터링
        enabled_pattern = r'<Skill[^>]*enabled="true"[^>]*nameSpec="([^"]*)"'
        enabled_skills = re.findall(enabled_pattern, xml_content)

        if enabled_skills:
            info["skills"] = list(set(enabled_skills))
            # 첫 번째 활성화된 스킬을 메인으로 (더 정확한 방법 필요)
            info["main_skill"] = enabled_skills[0] if enabled_skills else "Unknown"
        elif skills:
            info["skills"] = list(set(skills))
            info["main_skill"] = skills[0] if skills else "Unknown"

        return info

    def detect_archetype(self, build_info: Dict) -> str:
        """빌드 아키타입 감지"""
        main_skill = build_info.get("main_skill", "").lower()
        skills = [s.lower() for s in build_info.get("skills", [])]

        # 스펠 감지 키워드
        spell_keywords = ["brand", "spark", "arc", "fireball", "ice nova", "storm",
                         "orb", "wave", "blast", "pulse", "bolt", "nova"]

        # 소환 감지 키워드
        minion_keywords = ["zombie", "skeleton", "spectre", "golem", "animate",
                         "summon", "raise"]

        # 공격 감지 키워드
        attack_keywords = ["strike", "slam", "cleave", "sweep", "cyclone",
                         "blade", "arrow", "shot"]

        # DOT 감지 키워드
        dot_keywords = ["poison", "bleed", "ignite", "caustic", "essence drain",
                       "contagion", "blight", "toxic rain", "toxic", "venom"]

        # 메인 스킬 기반 감지
        for keyword in minion_keywords:
            if keyword in main_skill:
                return "minion"

        for keyword in dot_keywords:
            if keyword in main_skill:
                return "dot"

        for keyword in spell_keywords:
            if keyword in main_skill:
                return "spell"

        for keyword in attack_keywords:
            if keyword in main_skill:
                return "attack"

        # 기본값
        return "spell"

    def find_matching_build(self, build_info: Dict) -> Optional[Dict]:
        """빌드 정보와 매칭되는 템플릿 찾기"""
        main_skill = build_info.get("main_skill", "").lower()
        ascendancy = build_info.get("ascendancy", "").lower()

        for build_key, build_data in self.builds.items():
            build_main = build_data.get("build_info", {}).get("main_skill", "").lower()
            build_asc = build_data.get("build_info", {}).get("ascendancy", "").lower()

            # 메인 스킬과 아센던시 매칭
            if main_skill in build_main or build_main in main_skill:
                if ascendancy == build_asc:
                    return build_data

        return None

    def generate_guide(self, pob_code: str) -> Dict[str, Any]:
        """POB 코드로 가이드 생성"""
        # POB 디코딩
        xml_content = self.decode_pob_code(pob_code)
        if not xml_content:
            return {"error": "POB 코드 디코딩 실패"}

        # 빌드 정보 추출
        build_info = self.extract_build_info(xml_content)

        # 아키타입 감지
        archetype = self.detect_archetype(build_info)

        # 매칭되는 빌드 템플릿 찾기
        matching_build = self.find_matching_build(build_info)

        # 가이드 병합
        guide = {
            "build_info": build_info,
            "archetype": archetype,
            "has_specific_template": matching_build is not None
        }

        # 공통 템플릿 적용
        if self.common_template:
            guide["common"] = {
                "progression_stages": self.common_template.get("progression_stages"),
                "defense_framework": self.common_template.get("defense_framework"),
                "flask_progression": self.common_template.get("flask_progression"),
                "farming_spots": self.common_template.get("farming_spots")
            }

        # 아키타입 템플릿 적용
        archetype_template = self.archetypes.get(archetype)
        if archetype_template:
            guide["archetype_guide"] = {
                "mana_management": archetype_template.get("mana_management"),
                "damage_scaling": archetype_template.get("damage_scaling"),
                "support_gem_priority": archetype_template.get("support_gem_priority"),
                "aura_progression": archetype_template.get("aura_progression"),
                "unique_items_leveling": archetype_template.get("unique_items_leveling")
            }

        # 빌드 특화 템플릿 적용
        if matching_build:
            guide["build_specific"] = {
                "skill_progression": matching_build.get("skill_progression"),
                "passive_tree_priorities": matching_build.get("passive_tree_priorities"),
                "gear_progression": matching_build.get("gear_progression"),
                "gem_links_final": matching_build.get("gem_links_final"),
                "playstyle_tips": matching_build.get("playstyle_tips"),
                "common_mistakes": matching_build.get("common_mistakes")
            }

        return guide

    def generate_ui_compatible_guide(self, pob_code: str) -> Dict[str, Any]:
        """UI에서 사용하는 형식으로 가이드 생성"""
        guide = self.generate_guide(pob_code)

        if "error" in guide:
            return guide

        build_info = guide.get("build_info", {})
        archetype_guide = guide.get("archetype_guide", {})
        build_specific = guide.get("build_specific", {})
        common = guide.get("common", {})

        # 스킬 이름 번역
        main_skill = build_info.get("main_skill", "Unknown")
        translated_skill = self.translator.translate_skill(main_skill)

        # 스킬 태그 번역
        skills = build_info.get("skills", [])[:5]
        translated_skills = [self.translator.translate_skill(s) for s in skills]

        # UI가 기대하는 형식으로 변환
        ui_guide = {
            "skill_name": translated_skill,
            "skill_name_en": main_skill,
            "class_name": build_info.get("class", "Unknown"),
            "ascendancy": build_info.get("ascendancy", ""),
            "archetype": guide.get("archetype", "spell"),
            "tags": translated_skills,
            "tips": [],
            "gem_progression": [],
            "leveling_gear": [],
            "ascendancy_order": []
        }

        # 팁 생성
        tips = []

        # 아키타입별 팁 추가
        if archetype_guide:
            mana = archetype_guide.get("mana_management", {})
            if mana:
                early = mana.get("early_game", {})
                if early:
                    tips.append(f"초반 마나: {early.get('note', '')}")

            damage = archetype_guide.get("damage_scaling", {})
            if damage and "sources" in damage:
                tips.append(f"데미지 스케일링: {', '.join(damage['sources'][:3])}")

        # 공통 팁 추가
        if common:
            defense = common.get("defense_framework", {})
            if defense:
                res = defense.get("resistance_targets", {})
                if "act5_kitava" in res:
                    act5 = res["act5_kitava"]
                    tips.append(f"액트5 목표: 화염 {act5.get('fire', 0)}%, 냉기 {act5.get('cold', 0)}%, 번개 {act5.get('lightning', 0)}%")

        # 빌드 특화 팁
        if build_specific:
            playstyle = build_specific.get("playstyle_tips", {})
            if playstyle and "damage_rotation" in playstyle:
                rotation = playstyle["damage_rotation"]
                if rotation:
                    tips.append(f"로테이션: {rotation[0]}")

            mistakes = build_specific.get("common_mistakes", [])
            for mistake in mistakes[:2]:
                tips.append(f"주의: {mistake}")

        ui_guide["tips"] = tips

        # 젬 진행도 생성
        gem_prog = []
        if archetype_guide:
            support_priority = archetype_guide.get("support_gem_priority", {})
            damage_gems = support_priority.get("damage", [])
            if damage_gems:
                # 젬 이름 번역
                translated_gems = [self.translator.translate_skill(g) for g in damage_gems[:3]]
                gem_prog.append({"level": 1, "gems": ", ".join(translated_gems)})
                if len(damage_gems) > 3:
                    translated_gems = [self.translator.translate_skill(g) for g in damage_gems[3:6]]
                    gem_prog.append({"level": 38, "gems": ", ".join(translated_gems)})

        if build_specific:
            skill_prog = build_specific.get("skill_progression", {})
            for act, data in skill_prog.items():
                if isinstance(data, dict):
                    main = data.get("main_skill", {})
                    if isinstance(main, dict):
                        level_range = data.get("level_range", [1, 12])
                        links = main.get("links", [])
                        if links:
                            # 스킬과 링크 번역
                            skill_name = self.translator.translate_skill(main.get('name', ''))
                            translated_links = [self.translator.translate_skill(l) for l in links]
                            gem_prog.append({
                                "level": level_range[0] if level_range else 1,
                                "gems": f"{skill_name}: {', '.join(translated_links)}"
                            })

        ui_guide["gem_progression"] = sorted(gem_prog, key=lambda x: x["level"])

        # 레벨링 장비 생성
        leveling_gear = []
        if archetype_guide:
            unique_items = archetype_guide.get("unique_items_leveling", {})
            for slot, items in unique_items.items():
                if isinstance(items, list):
                    for item in items[:2]:
                        if isinstance(item, dict):
                            # 아이템 이름 번역
                            item_name = self.translator.translate_item(item.get("name", ""))
                            leveling_gear.append({
                                "level": item.get("level", 1),
                                "item": item_name,
                                "reason": item.get("note", "")
                            })

        ui_guide["leveling_gear"] = sorted(leveling_gear, key=lambda x: x["level"])

        # 아센던시 순서 (일반적인 순서)
        ui_guide["ascendancy_order"] = ["1st Lab (Normal)", "2nd Lab (Cruel)", "3rd Lab (Merciless)", "4th Lab (Eternal)"]

        return ui_guide

    def print_guide(self, guide: Dict) -> None:
        """가이드를 읽기 쉽게 출력"""
        if "error" in guide:
            print(f"오류: {guide['error']}")
            return

        print("\n" + "="*60)
        print("레벨링 가이드")
        print("="*60)

        # 빌드 정보
        build_info = guide.get("build_info", {})
        print(f"\n[빌드 정보]")
        print(f"  클래스: {build_info.get('class')} - {build_info.get('ascendancy')}")
        print(f"  메인 스킬: {build_info.get('main_skill')}")
        print(f"  아키타입: {guide.get('archetype')}")
        print(f"  특화 템플릿: {'있음' if guide.get('has_specific_template') else '없음 (일반 가이드 사용)'}")

        # 방어 목표
        if "common" in guide:
            defense = guide["common"].get("defense_framework", {})
            res_targets = defense.get("resistance_targets", {})

            print(f"\n[방어 목표]")
            for stage, targets in res_targets.items():
                if isinstance(targets, dict):
                    print(f"  {stage}:")
                    print(f"    저항: 화염 {targets.get('fire', 0)}%, 냉기 {targets.get('cold', 0)}%, 번개 {targets.get('lightning', 0)}%")

        # 아키타입 가이드
        if "archetype_guide" in guide:
            arch = guide["archetype_guide"]

            if arch.get("mana_management"):
                print(f"\n[마나 관리]")
                for stage, info in arch["mana_management"].items():
                    if isinstance(info, dict):
                        print(f"  {stage}: {info.get('method', '')} - {info.get('note', '')}")

            if arch.get("aura_progression"):
                print(f"\n[오라 진행]")
                for stage, auras in arch["aura_progression"].items():
                    if isinstance(auras, list):
                        print(f"  {stage}: {', '.join(auras)}")

        # 빌드 특화 가이드
        if "build_specific" in guide:
            specific = guide["build_specific"]

            # 스킬 진행
            if specific.get("skill_progression"):
                print(f"\n[스킬 진행]")
                for act, data in specific["skill_progression"].items():
                    if isinstance(data, dict):
                        main = data.get("main_skill", {})
                        if isinstance(main, dict):
                            print(f"  {act} ({data.get('level_range', [])})")
                            print(f"    메인: {main.get('name', '')} - {', '.join(main.get('links', []))}")

            # 플레이스타일 팁
            if specific.get("playstyle_tips"):
                tips = specific["playstyle_tips"]
                print(f"\n[플레이스타일]")

                if tips.get("damage_rotation"):
                    print("  데미지 로테이션:")
                    for step in tips["damage_rotation"]:
                        print(f"    {step}")

            # 흔한 실수
            if specific.get("common_mistakes"):
                print(f"\n[주의사항]")
                for mistake in specific["common_mistakes"]:
                    print(f"  - {mistake}")

        print("\n" + "="*60)


def main():
    """테스트 실행"""
    generator = GuideGenerator()

    print("="*60)
    print("PathcraftAI 레벨링 가이드 생성기 (테스트)")
    print("="*60)

    # 테스트용 POB 코드 입력
    print("\nPOB 코드를 입력하세요 (Ctrl+Z로 종료):")
    print("(pastebin URL은 지원하지 않습니다. POB에서 Export -> Copy to Clipboard)")

    try:
        pob_code = ""
        while True:
            try:
                line = input()
                pob_code += line
            except EOFError:
                break

        if pob_code.strip():
            guide = generator.generate_guide(pob_code.strip())
            generator.print_guide(guide)
        else:
            print("\n[테스트 모드] 샘플 빌드 정보로 실행...")

            # 샘플 테스트 (POB 코드 없이)
            sample_info = {
                "class": "Templar",
                "ascendancy": "Inquisitor",
                "main_skill": "Penance Brand",
                "skills": ["Penance Brand", "Brand Recall", "Flame Dash"],
                "level": 90
            }

            archetype = generator.detect_archetype(sample_info)
            matching = generator.find_matching_build(sample_info)

            print(f"\n[샘플 빌드 분석]")
            print(f"  아키타입: {archetype}")
            print(f"  매칭 템플릿: {'발견' if matching else '없음'}")

            if matching:
                print(f"  빌드 이름: {matching.get('build_info', {}).get('name', 'Unknown')}")

    except KeyboardInterrupt:
        print("\n\n종료됨")


if __name__ == '__main__':
    main()
