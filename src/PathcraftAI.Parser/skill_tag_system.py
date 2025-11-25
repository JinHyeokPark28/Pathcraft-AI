#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Tag System
스킬의 태그를 기반으로 유사 스킬을 찾고, 레벨링 가이드를 검색
"""

import sys
import re
import json
import os
import requests
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

# 데이터 파일 경로
GAME_DATA_DIR = os.path.join(os.path.dirname(__file__), "game_data")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
GEMS_JSON_PATH = os.path.join(GAME_DATA_DIR, "gems.json")
GEM_LEVELS_PATH = os.path.join(DATA_DIR, "gem_levels.json")
QUEST_REWARDS_PATH = os.path.join(DATA_DIR, "quest_rewards.json")
VENDOR_RECIPES_PATH = os.path.join(DATA_DIR, "vendor_recipes.json")
TRANSITION_PATTERNS_PATH = os.path.join(DATA_DIR, "build_transition_patterns.json")
TRANSLATIONS_PATH = os.path.join(DATA_DIR, "merged_translations.json")


@dataclass
class SkillInfo:
    """스킬 정보"""
    name: str
    skill_id: str
    tags: List[str]
    required_level: int
    is_transfigured: bool = False


class SkillTagSystem:
    """스킬 태그 시스템 - gems.json에서 데이터 로드"""

    def __init__(self):
        self.SKILL_DATABASE = {}
        self.gem_levels = {}  # 젬 레벨 데이터 (poedb.tw)
        self.quest_rewards = {}  # 퀘스트 보상 데이터
        self.vendor_recipes = []  # 벤더 레시피
        self.transition_patterns = []  # 빌드 전환 패턴 (크롤링 데이터)
        self.translations = {}  # 영한 번역 데이터
        self.reverse_translations = {}  # 한영 역번역 데이터
        self._load_gem_data()
        self._load_poedb_data()
        self._load_transition_patterns()
        self._load_translations()

    def _load_translations(self):
        """한국어 번역 데이터 로드"""
        if not os.path.exists(TRANSLATIONS_PATH):
            print(f"[WARN] translations not found at {TRANSLATIONS_PATH}")
            return

        try:
            with open(TRANSLATIONS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # skills: 영어 -> 한국어
                self.translations = data.get("skills", {})
                # skills_kr: 한국어 -> 영어
                self.reverse_translations = {k.lower(): v for k, v in data.get("skills_kr", {}).items()}

            print(f"[INFO] Loaded {len(self.translations)} skill translations")

        except Exception as e:
            print(f"[WARN] Failed to load translations: {e}")

    def get_korean_name(self, english_name: str) -> str:
        """영어 스킬명을 한국어로 변환"""
        # 직접 매칭 시도
        result = self.translations.get(english_name)
        if result:
            return result

        # 대소문자 무관 매칭
        english_lower = english_name.lower()
        for key, value in self.translations.items():
            if key.lower() == english_lower:
                return value

        return english_name

    def get_english_name(self, korean_name: str) -> str:
        """한국어 스킬명을 영어로 변환"""
        return self.reverse_translations.get(korean_name.lower(), korean_name)

    def find_skill_by_korean_name(self, korean_name: str) -> Optional[SkillInfo]:
        """한국어 스킬명으로 스킬 검색"""
        english_name = self.get_english_name(korean_name)
        return self.find_skill_by_name(english_name)

    def _load_transition_patterns(self):
        """빌드 전환 패턴 데이터 로드 (Reddit/GitHub 크롤링 데이터)"""
        if not os.path.exists(TRANSITION_PATTERNS_PATH):
            print(f"[WARN] build_transition_patterns.json not found")
            return

        try:
            with open(TRANSITION_PATTERNS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.transition_patterns = data.get("patterns", [])

            print(f"[INFO] Loaded {len(self.transition_patterns)} build transition patterns")

        except Exception as e:
            print(f"[WARN] Failed to load transition patterns: {e}")

    def _get_no_transition_skills(self) -> Dict[str, Dict]:
        """전환 없이 Act부터 끝까지 사용 가능한 스킬 목록

        이 스킬들은 레벨링용 스킬이 따로 필요 없음
        """
        return {
            # Lightning
            "arc": {"available_level": 12, "reason": "Early access, strong scaling"},
            "spark": {"available_level": 1, "reason": "Available from Act 1"},
            "ball lightning": {"available_level": 28, "reason": "Strong from mid-acts"},
            "storm call": {"available_level": 12, "reason": "Good clear from early"},

            # Fire
            "fireball": {"available_level": 1, "reason": "Available from Act 1"},
            "flame surge": {"available_level": 12, "reason": "Early access"},
            "cremation": {"available_level": 28, "reason": "Strong from start"},

            # Cold
            "freezing pulse": {"available_level": 1, "reason": "Available from Act 1"},
            "ice spear": {"available_level": 12, "reason": "Early access"},

            # Chaos/DOT
            "essence drain": {"available_level": 12, "reason": "Strong leveling skill itself"},
            "bane": {"available_level": 24, "reason": "Self-sufficient from acquisition"},
            "blight": {"available_level": 1, "reason": "Available from Act 1"},
            "contagion": {"available_level": 4, "reason": "ED+Contagion combo"},

            # Bow
            "toxic rain": {"available_level": 12, "reason": "Strong leveling, no transition needed"},
            "caustic arrow": {"available_level": 1, "reason": "Available from Act 1"},
            "rain of arrows": {"available_level": 12, "reason": "Good clear from early"},

            # Melee
            "cleave": {"available_level": 1, "reason": "Available from Act 1"},
            "ground slam": {"available_level": 1, "reason": "Available from Act 1"},
            "sunder": {"available_level": 12, "reason": "Strong leveling skill"},
            "perforate": {"available_level": 1, "reason": "Available from Act 1"},
            "lacerate": {"available_level": 12, "reason": "Good clear from early"},
            "blade vortex": {"available_level": 12, "reason": "Strong scaling"},

            # Ranged Attack
            "spectral helix": {"available_level": 1, "reason": "Strong leveling skill itself"},

            # Minions
            "summon raging spirit": {"available_level": 4, "reason": "Core leveling skill"},
            "absolution": {"available_level": 12, "reason": "Self-sufficient minion"},
            "summon skeletons": {"available_level": 10, "reason": "Easy to level with"},
            "raise zombie": {"available_level": 1, "reason": "Available from Act 1"},

            # Traps/Mines
            "stormblast mine": {"available_level": 1, "reason": "Available from Act 1"},
            "explosive trap": {"available_level": 1, "reason": "Available from Act 1"},
        }

    def is_no_transition_skill(self, skill_name: str) -> bool:
        """스킬이 전환 없이 사용 가능한지 확인"""
        skill_lower = self._normalize_skill_name(skill_name)
        return skill_lower in self._get_no_transition_skills()

    def get_no_transition_info(self, skill_name: str) -> Optional[Dict]:
        """전환 불필요 스킬의 정보 반환"""
        skill_lower = self._normalize_skill_name(skill_name)
        no_transition = self._get_no_transition_skills()

        if skill_lower in no_transition:
            info = no_transition[skill_lower]
            skill_info = self.find_skill_by_name(skill_name)

            return {
                "skill": skill_name,
                "available_level": info["available_level"],
                "reason": info["reason"],
                "required_level": skill_info.required_level if skill_info else info["available_level"],
                "recommendation": f"Use {skill_name} from the start - no transition needed"
            }
        return None

    def _get_fallback_patterns(self) -> Dict[str, List[str]]:
        """크롤링 데이터가 부족할 때 사용할 기본 전환 패턴

        연구 문서 기반 - 커뮤니티에서 검증된 일반적인 레벨링 패턴
        """
        return {
            # Brands
            "penance brand": ["armageddon brand", "storm brand"],
            "storm brand": ["armageddon brand", "orb of storms"],
            "wintertide brand": ["armageddon brand", "storm brand"],

            # Fire spells
            "righteous fire": ["holy flame totem", "flame wall", "armageddon brand"],
            "fireball": ["rolling magma", "flame wall"],
            "blazing salvo": ["rolling magma", "arcanist brand"],
            "detonate dead": ["cremation", "volatile dead"],

            # Cold spells
            "ice nova": ["frostbolt", "freezing pulse"],
            "vortex": ["frostbolt", "freezing pulse"],
            "cold snap": ["frostbolt", "freezing pulse"],
            "glacial cascade": ["frostbolt", "freezing pulse"],

            # Lightning spells
            "spark": ["arc", "orb of storms"],
            "ball lightning": ["arc", "spark"],
            "arc": ["spark", "orb of storms"],
            "storm call": ["arc", "orb of storms"],

            # Chaos/DOT
            "bane": ["essence drain", "blight"],
            "essence drain": ["blight", "contagion"],
            "soulrend": ["essence drain", "blight"],

            # Bow attacks
            "tornado shot": ["rain of arrows", "burning arrow"],
            "lightning arrow": ["galvanic arrow", "rain of arrows"],
            "ice shot": ["rain of arrows", "burning arrow"],
            "toxic rain": ["caustic arrow", "rain of arrows"],
            "scourge arrow": ["caustic arrow", "toxic rain"],

            # Melee attacks
            "cyclone": ["cleave", "sunder", "ground slam"],
            "lacerate": ["cleave", "perforate"],
            "bladestorm": ["cleave", "perforate"],
            "earthquake": ["ground slam", "sunder"],
            "tectonic slam": ["ground slam", "sunder"],
            "ice crash": ["ground slam", "sunder"],
            "blade flurry": ["double strike", "cleave"],
            "reave": ["double strike", "cleave"],
            "lightning strike": ["spectral helix", "frost blades"],
            "frost blades": ["spectral helix", "molten strike"],
            "molten strike": ["spectral helix", "frost blades"],

            # Minions
            "summon skeletons": ["summon raging spirit", "absolution"],
            "raise spectre": ["summon raging spirit", "summon skeletons"],
            "raise zombie": ["summon raging spirit", "summon skeletons"],
            "dominating blow": ["absolution", "summon holy relic"],
            "herald of purity": ["absolution", "dominating blow"],

            # Traps/Mines
            "icicle mine": ["stormblast mine", "arc"],
            "pyroclast mine": ["stormblast mine", "rolling magma"],
        }

    def _normalize_skill_name(self, skill_name: str) -> str:
        """변형 스킬 이름을 기본 스킬 이름으로 정규화

        예: "Penance Brand of Dissipation" -> "penance brand"
        """
        skill_lower = skill_name.lower()

        # " of " 패턴으로 변형 스킬 감지
        if " of " in skill_lower:
            base_skill = skill_lower.split(" of ")[0].strip()
            return base_skill

        return skill_lower

    def get_leveling_skill_for_build(self, final_skill: str, include_korean: bool = True) -> List[Dict]:
        """최종 스킬에 대한 레벨링 스킬 추천

        Args:
            final_skill: 최종 빌드 스킬 (영어 또는 한국어)
            include_korean: 결과에 한국어 이름 포함 여부

        Returns:
            List of leveling skill recommendations with metadata
            또는 no_transition=True인 경우 해당 스킬을 그대로 사용하라는 추천
        """
        recommendations = []

        # 한국어 입력인 경우 영어로 변환
        original_name = final_skill
        if any('\uac00' <= c <= '\ud7a3' for c in final_skill):  # 한글 감지
            final_skill = self.get_english_name(final_skill)

        # 변형 스킬인 경우 기본 스킬로 정규화
        final_lower = self._normalize_skill_name(final_skill)
        is_transfigured = " of " in final_skill.lower()

        # 전환 불필요 스킬인지 먼저 확인
        if self.is_no_transition_skill(final_skill):
            no_trans_info = self.get_no_transition_info(final_skill)
            if no_trans_info:
                result = {
                    "skill": final_skill,
                    "count": 0,
                    "transition_point": "none",
                    "ascendancy": None,
                    "sources": ["no_transition"],
                    "is_for_transfigured": is_transfigured,
                    "no_transition": True,
                    "available_level": no_trans_info["available_level"],
                    "reason": no_trans_info["reason"]
                }
                if include_korean:
                    result["skill_kr"] = self.get_korean_name(final_skill)
                return [result]

        # 패턴에서 매칭되는 레벨링 스킬 찾기
        for pattern in self.transition_patterns:
            pattern_final = self._normalize_skill_name(pattern.get("final_skill", ""))

            # 정규화된 이름으로 매칭
            if pattern_final == final_lower or final_lower in pattern_final or pattern_final in final_lower:
                leveling_skill = pattern.get("leveling_skill", "")

                # 중복 확인
                existing = [r for r in recommendations if r["skill"].lower() == leveling_skill.lower()]
                if existing:
                    existing[0]["count"] += 1
                    existing[0]["sources"].append(pattern.get("source", "unknown"))
                else:
                    recommendations.append({
                        "skill": leveling_skill,
                        "count": 1,
                        "transition_point": pattern.get("transition_point", "maps_entry"),
                        "ascendancy": pattern.get("ascendancy"),
                        "sources": [pattern.get("source", "unknown")],
                        "is_for_transfigured": is_transfigured
                    })

        # 인기도순 정렬
        recommendations.sort(key=lambda x: x["count"], reverse=True)

        # 크롤링 데이터가 부족하면 폴백 패턴 사용
        if len(recommendations) < 2:
            fallback = self._get_fallback_patterns()
            if final_lower in fallback:
                for skill in fallback[final_lower]:
                    # 이미 있는지 확인
                    existing = [r for r in recommendations if r["skill"].lower() == skill.lower()]
                    if not existing:
                        recommendations.append({
                            "skill": skill.title(),
                            "count": 0,
                            "transition_point": "maps_entry",
                            "ascendancy": None,
                            "sources": ["fallback"],
                            "is_for_transfigured": is_transfigured
                        })

        # 한국어 이름 추가
        if include_korean:
            for rec in recommendations:
                rec["skill_kr"] = self.get_korean_name(rec["skill"])

        return recommendations

    def _get_4th_ascendancy_skills(self) -> Dict[str, Dict]:
        """4th ascendancy에서 전환해야 하는 스킬 목록

        이 스킬들은 특정 어센던시 노드에 의존하여 제대로 작동함
        """
        return {
            # Inquisitor - Righteous Providence, Inevitable Judgement 등
            "penance brand": {
                "ascendancy": "Inquisitor",
                "key_nodes": ["Inevitable Judgement", "Righteous Providence"],
                "reason": "Needs crit ignore resistance from Inevitable Judgement"
            },

            # Elementalist - Shaper of Flames, Heart of Destruction
            "ignite": {
                "ascendancy": "Elementalist",
                "key_nodes": ["Shaper of Flames", "Heart of Destruction"],
                "reason": "Needs guaranteed ignite and damage scaling"
            },

            # Necromancer - Bone Barrier, Unnatural Strength
            "raise spectre": {
                "ascendancy": "Necromancer",
                "key_nodes": ["Unnatural Strength", "Bone Barrier"],
                "reason": "Needs +2 spectre level for endgame spectres"
            },

            # Occultist - Void Beacon, Withering Presence
            "bane": {
                "ascendancy": "Occultist",
                "key_nodes": ["Void Beacon", "Withering Presence"],
                "reason": "Needs -chaos res and wither for damage"
            },

            # Assassin - Mistwalker, Opportunistic
            "blade vortex": {
                "ascendancy": "Assassin",
                "key_nodes": ["Mistwalker", "Opportunistic"],
                "reason": "Needs elusive and crit scaling"
            },

            # Slayer - Headsman, Bane of Legends
            "cyclone": {
                "ascendancy": "Slayer",
                "key_nodes": ["Headsman", "Bane of Legends"],
                "reason": "Needs culling and attack speed"
            },

            # Trickster - Ghost Dance, Escape Artist (for ES builds)
            "ethereal knives": {
                "ascendancy": "Trickster",
                "key_nodes": ["Ghost Dance", "Escape Artist"],
                "reason": "Needs ES recovery mechanics"
            },

            # Guardian - Time of Need, Radiant Crusade
            "herald of purity": {
                "ascendancy": "Guardian",
                "key_nodes": ["Radiant Crusade", "Time of Need"],
                "reason": "Needs minion damage from aura effect"
            },

            # Champion - Master of Metal, Fortitude
            "impale": {
                "ascendancy": "Champion",
                "key_nodes": ["Master of Metal", "Fortitude"],
                "reason": "Needs impale scaling and permanent fortify"
            },
        }

    def requires_4th_ascendancy(self, skill_name: str, ascendancy: str = None) -> Dict:
        """스킬이 4th ascendancy 이후 전환해야 하는지 확인

        Args:
            skill_name: 스킬 이름
            ascendancy: 어센던시 이름 (선택사항)

        Returns:
            {requires: bool, reason: str, key_nodes: list} or None
        """
        skill_lower = self._normalize_skill_name(skill_name)
        ascendancy_skills = self._get_4th_ascendancy_skills()

        if skill_lower in ascendancy_skills:
            info = ascendancy_skills[skill_lower]
            # 어센던시가 일치하는지 확인 (제공된 경우)
            if ascendancy and info.get("ascendancy", "").lower() != ascendancy.lower():
                # 다른 어센던시이므로 4th 필요 없음
                return {"requires": False, "reason": f"Not a {info.get('ascendancy')} build"}

            return {
                "requires": True,
                "ascendancy": info.get("ascendancy"),
                "key_nodes": info.get("key_nodes", []),
                "reason": info.get("reason"),
                "recommended_level": 75  # Uber lab completion
            }

        return {"requires": False}

    def get_transition_info(self, leveling_skill: str, final_skill: str, ascendancy: str = None) -> Dict:
        """레벨링 스킬에서 최종 스킬로의 전환 정보

        Args:
            leveling_skill: 레벨링 스킬 (예: "Armageddon Brand")
            final_skill: 최종 스킬 (예: "Penance Brand")
            ascendancy: 어센던시 이름 (선택사항, 4th 전환 감지에 사용)

        Returns:
            Transition info with recommended point and requirements
        """
        leveling_lower = leveling_skill.lower()
        final_lower = self._normalize_skill_name(final_skill)

        # 4th ascendancy 스킬인지 확인
        fourth_asc_info = self.requires_4th_ascendancy(final_skill, ascendancy)
        if fourth_asc_info and fourth_asc_info.get("requires"):
            transition_point = "4th_ascendancy"
            recommended_level = 75
        else:
            # 전환 시점 결정
            transition_point = "maps_entry"
            recommended_level = 70

            for pattern in self.transition_patterns:
                if (pattern.get("leveling_skill", "").lower() == leveling_lower and
                    self._normalize_skill_name(pattern.get("final_skill", "")) == final_lower):
                    transition_point = pattern.get("transition_point", "maps_entry")
                    break

            # 전환 시점에 따른 레벨 결정
            if transition_point == "4th_ascendancy":
                recommended_level = 75
            elif transition_point == "maps_entry":
                recommended_level = 68
            elif transition_point == "act_complete":
                recommended_level = 60
            elif transition_point == "specific_level":
                recommended_level = 70

        # 최종 스킬 정보
        final_skill_info = self.find_skill_by_name(final_skill)
        final_required_level = final_skill_info.required_level if final_skill_info else 1

        result = {
            "leveling_skill": leveling_skill,
            "final_skill": final_skill,
            "transition_point": transition_point,
            "recommended_level": recommended_level,
            "final_skill_required_level": final_required_level,
            "tips": self._get_transition_tips(leveling_skill, final_skill, transition_point)
        }

        # 4th ascendancy 정보 추가
        if fourth_asc_info and fourth_asc_info.get("requires"):
            result["4th_ascendancy_info"] = {
                "ascendancy": fourth_asc_info.get("ascendancy"),
                "key_nodes": fourth_asc_info.get("key_nodes"),
                "reason": fourth_asc_info.get("reason")
            }

        return result

    def _get_transition_tips(self, leveling_skill: str, final_skill: str, transition_point: str) -> List[str]:
        """전환 관련 팁 생성"""
        tips = []

        if transition_point == "4th_ascendancy":
            tips.append(f"Complete Uber Lab before switching to {final_skill}")
            tips.append("Ensure you have necessary gear for the final build")
        elif transition_point == "maps_entry":
            tips.append(f"Switch to {final_skill} when entering maps")
            tips.append("Have your endgame links ready")
        elif transition_point == "act_complete":
            tips.append(f"You can switch to {final_skill} after completing Act 10")

        # 스킬 타입별 팁
        leveling_lower = leveling_skill.lower()
        final_lower = final_skill.lower()

        if "brand" in leveling_lower and "brand" in final_lower:
            tips.append("Keep similar gem links - brands share support gems")
        elif "brand" in leveling_lower:
            tips.append("You may need different support gems for the final skill")

        return tips

    def get_archetype_for_skill(self, skill_name: str) -> str:
        """스킬의 아키타입 분류 (연구 문서 기반 클러스터링)

        Returns:
            archetype: spell_caster, attack_melee, attack_ranged, minion, dot, totem_trap_mine
        """
        skill_info = self.find_skill_by_name(skill_name)
        if not skill_info:
            return "unknown"

        tags = [t.lower() for t in skill_info.tags]

        # 태그 기반 아키타입 분류
        if "minion" in tags:
            return "minion"
        elif "totem" in tags or "trap" in tags or "mine" in tags:
            return "totem_trap_mine"
        elif "attack" in tags:
            if "bow" in tags or "projectile" in tags:
                return "attack_ranged"
            else:
                return "attack_melee"
        elif "spell" in tags:
            if "duration" in tags or any(t in tags for t in ["chaos", "fire", "cold"]):
                # DOT 스킬 확인
                dot_skills = ["righteous fire", "bane", "essence drain", "vortex", "cold snap"]
                if skill_name.lower() in dot_skills:
                    return "dot"
            return "spell_caster"

        return "spell_caster"  # 기본값

    def get_similar_builds_leveling(self, final_skill: str) -> List[Dict]:
        """유사 아키타입 빌드의 레벨링 패턴 추천 (협업 필터링 개념)

        같은 아키타입의 다른 빌드에서 사용하는 레벨링 스킬도 추천
        """
        archetype = self.get_archetype_for_skill(final_skill)
        recommendations = []

        # 아키타입별 공통 레벨링 스킬
        archetype_leveling = {
            "spell_caster": ["arc", "spark", "freezing pulse", "orb of storms"],
            "attack_melee": ["cleave", "ground slam", "sunder", "perforate"],
            "attack_ranged": ["rain of arrows", "burning arrow", "spectral helix"],
            "minion": ["summon raging spirit", "absolution"],
            "dot": ["holy flame totem", "essence drain", "blight"],
            "totem_trap_mine": ["holy flame totem", "stormblast mine"]
        }

        if archetype in archetype_leveling:
            for skill in archetype_leveling[archetype]:
                recommendations.append({
                    "skill": skill.title(),
                    "reason": f"Common {archetype.replace('_', ' ')} leveling skill",
                    "archetype": archetype
                })

        return recommendations

    def _load_gem_data(self):
        """gems.json에서 젬 데이터 로드"""
        if not os.path.exists(GEMS_JSON_PATH):
            print(f"[WARN] gems.json not found at {GEMS_JSON_PATH}")
            return

        try:
            with open(GEMS_JSON_PATH, 'r', encoding='utf-8') as f:
                gems_data = json.load(f)

            for gem_key, gem_info in gems_data.items():
                name = gem_info.get("name", "")
                if not name:
                    continue

                # 서포트 젬은 제외
                if gem_info.get("isSupport", False):
                    continue

                # SkillInfo 객체 생성
                skill_id = gem_key
                tags = gem_info.get("tags", [])

                # 기본값 (나중에 poedb 데이터로 업데이트)
                required_level = 1

                is_transfigured = " of " in name  # "Storm Brand of Indecision" 등

                self.SKILL_DATABASE[skill_id] = SkillInfo(
                    name=name,
                    skill_id=skill_id,
                    tags=tags,
                    required_level=required_level,
                    is_transfigured=is_transfigured
                )

            print(f"[INFO] Loaded {len(self.SKILL_DATABASE)} active skills from gems.json")

        except Exception as e:
            print(f"[ERROR] Failed to load gems.json: {e}")

    def _load_poedb_data(self):
        """poedb.tw 크롤링 데이터 로드 (gem_levels, quest_rewards, vendor_recipes)"""
        # 젬 레벨 데이터 로드
        if os.path.exists(GEM_LEVELS_PATH):
            try:
                with open(GEM_LEVELS_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.gem_levels = data.get("gems", {})

                # SKILL_DATABASE의 required_level 업데이트
                updated = 0
                for skill in self.SKILL_DATABASE.values():
                    # 정확히 일치하는 경우
                    if skill.name in self.gem_levels:
                        skill.required_level = self.gem_levels[skill.name].get("required_level", 1)
                        updated += 1
                    # Transfigured gem인 경우 기본 스킬 이름으로 시도
                    elif " of " in skill.name:
                        base_name = skill.name.split(" of ")[0]
                        if base_name in self.gem_levels:
                            skill.required_level = self.gem_levels[base_name].get("required_level", 1)
                            updated += 1

                print(f"[INFO] Updated {updated} gem levels from poedb.tw data")

            except Exception as e:
                print(f"[WARN] Failed to load gem_levels.json: {e}")

        # 퀘스트 보상 데이터 로드
        if os.path.exists(QUEST_REWARDS_PATH):
            try:
                with open(QUEST_REWARDS_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.quest_rewards = data.get("quests", [])

                print(f"[INFO] Loaded {len(self.quest_rewards)} quest rewards from poedb.tw")

            except Exception as e:
                print(f"[WARN] Failed to load quest_rewards.json: {e}")

        # 벤더 레시피 데이터 로드
        if os.path.exists(VENDOR_RECIPES_PATH):
            try:
                with open(VENDOR_RECIPES_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.vendor_recipes = data.get("recipes", [])

                print(f"[INFO] Loaded {len(self.vendor_recipes)} vendor recipes from poedb.tw")

            except Exception as e:
                print(f"[WARN] Failed to load vendor_recipes.json: {e}")

    def get_gem_quest_info(self, gem_name: str, class_name: str = "") -> Optional[Dict]:
        """젬을 얻을 수 있는 퀘스트 정보 반환 (대소문자 구분 없음)

        Note: quest_rewards.json 데이터가 부정확할 수 있으므로
        젬의 required_level과 퀘스트 Act를 비교하여 검증합니다.
        """
        gem_name_lower = gem_name.lower()

        # 젬의 required_level 가져오기
        gem_required_level = 1
        skill_info = self.find_skill_by_name(gem_name)
        if skill_info:
            gem_required_level = skill_info.required_level
        elif gem_name in self.gem_levels:
            gem_required_level = self.gem_levels[gem_name].get("required_level", 1)

        # Act별 최대 획득 가능 레벨 (보수적 추정)
        # POE에서 각 Act 완료 시 도달하는 대략적인 레벨
        act_level_map = {
            0: 1,    # Tutorial
            1: 12,   # Act 1
            2: 23,   # Act 2
            3: 33,   # Act 3
            4: 40,   # Act 4
            5: 45,   # Act 5
            6: 50,   # Act 6
            7: 55,   # Act 7
            8: 60,   # Act 8
            9: 64,   # Act 9
            10: 68   # Act 10
        }

        for quest in self.quest_rewards:
            rewards = quest.get("rewards", {})
            quest_act = quest.get("act", 0)

            # 해당 Act에서 얻을 수 있는 최대 젬 레벨
            max_gem_level = act_level_map.get(quest_act, 68)

            # 젬의 required_level이 해당 Act에서 얻을 수 있는 레벨보다 높으면 스킵
            if gem_required_level > max_gem_level:
                continue

            # 클래스별 또는 전체 클래스 검색
            if class_name and class_name in rewards:
                for gem in rewards[class_name]:
                    if gem.lower() == gem_name_lower:
                        return {
                            "quest": quest["name"],
                            "act": quest_act,
                            "class": class_name,
                            "gem_name": gem,  # 원본 이름 보존
                            "required_level": gem_required_level
                        }
            else:
                # 모든 클래스에서 검색
                for cls, gems in rewards.items():
                    for gem in gems:
                        if gem.lower() == gem_name_lower:
                            return {
                                "quest": quest["name"],
                                "act": quest_act,
                                "class": cls,
                                "gem_name": gem,  # 원본 이름 보존
                                "required_level": gem_required_level
                            }

        return None

    def get_leveling_recipes(self) -> List[Dict]:
        """레벨링에 유용한 벤더 레시피 반환"""
        useful_recipes = []
        useful_keywords = ["gem", "flask", "chromatic", "jeweller", "fusing", "level"]

        for recipe in self.vendor_recipes:
            result = recipe.get("result", "").lower()
            if any(kw in result for kw in useful_keywords):
                useful_recipes.append(recipe)

        return useful_recipes[:10]  # 상위 10개

    def get_leveling_skills_by_tag(self, tag: str) -> List[str]:
        """태그에 맞는 레벨링 스킬 추천 (동적 생성)"""
        result = []
        for skill_id, skill_info in self.SKILL_DATABASE.items():
            if tag in skill_info.tags:
                # 레벨링에 좋은 스킬 (레벨 요구 낮고, Vaal/변형 아닌 것)
                if skill_info.required_level <= 28 and not skill_info.is_transfigured:
                    if "vaal" not in skill_info.name.lower():
                        result.append(skill_id)
        return result[:5]  # 상위 5개만

    def get_skill_info(self, skill_id: str) -> Optional[SkillInfo]:
        """스킬 ID로 스킬 정보 가져오기"""
        return self.SKILL_DATABASE.get(skill_id)

    def get_skill_name(self, skill_id: str) -> str:
        """스킬 ID로 스킬 이름 가져오기"""
        skill = self.SKILL_DATABASE.get(skill_id)
        return skill.name if skill else skill_id

    def find_skill_by_name(self, name: str) -> Optional[SkillInfo]:
        """스킬 이름으로 스킬 정보 찾기"""
        name_lower = name.lower()

        # 1. 정확한 매칭 (최우선)
        for skill in self.SKILL_DATABASE.values():
            if skill.name.lower() == name_lower:
                return skill

        # 2. Transfigured gem 베이스 이름 매칭
        # "Arc of Oscillating"에서 "Arc" 검색 시 매칭
        for skill in self.SKILL_DATABASE.values():
            skill_lower = skill.name.lower()
            if " of " in skill_lower:
                base_skill = skill_lower.split(" of ")[0]
                if base_skill == name_lower:
                    return skill

        # 3. 역방향 부분 매칭 (스킬 이름이 검색 이름에 포함)
        # 예: "Penance Brand of Dissipation" 검색 시 "Penance Brand" 찾기
        for skill in self.SKILL_DATABASE.values():
            if skill.name.lower() in name_lower:
                return skill

        # 4. 단어 경계 부분 매칭 (substring이 단어로 시작/끝나는지 확인)
        # "Arc"가 "Arcane"과 매칭되지 않도록
        import re
        for skill in self.SKILL_DATABASE.values():
            skill_lower = skill.name.lower()
            # 검색어가 단어 경계에서 시작하는지 확인
            pattern = r'\b' + re.escape(name_lower) + r'\b'
            if re.search(pattern, skill_lower):
                return skill

        # 5. 일반 부분 매칭 (최후 수단)
        for skill in self.SKILL_DATABASE.values():
            if name_lower in skill.name.lower():
                return skill

        # 6. 베이스 스킬 이름 매칭 (변형 스킬 검색용)
        # "Skill of Variant" -> "Skill"
        if " of " in name_lower:
            base_name = name_lower.split(" of ")[0].strip()
            for skill in self.SKILL_DATABASE.values():
                if base_name in skill.name.lower():
                    return skill

        return None

    def get_similar_skills(self, skill_id: str, max_results: int = 5) -> List[SkillInfo]:
        """같은 태그를 가진 유사 스킬 찾기"""
        skill = self.get_skill_info(skill_id)
        if not skill:
            return []

        similar = []
        skill_tags = set(skill.tags)

        for other_id, other_skill in self.SKILL_DATABASE.items():
            if other_id == skill_id:
                continue

            other_tags = set(other_skill.tags)
            overlap = len(skill_tags & other_tags)

            if overlap >= 2:  # 최소 2개 태그 일치
                similar.append((other_skill, overlap))

        # 태그 일치 수로 정렬
        similar.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in similar[:max_results]]

    def get_leveling_skills(self, skill_id: str) -> List[SkillInfo]:
        """메인 스킬에 맞는 레벨링 스킬 추천"""
        skill = self.get_skill_info(skill_id)
        if not skill:
            return []

        recommended = set()

        # 태그 기반 추천 (동적)
        for tag in skill.tags:
            for rec_id in self.get_leveling_skills_by_tag(tag):
                if rec_id != skill_id:
                    rec_skill = self.get_skill_info(rec_id)
                    if rec_skill:
                        recommended.add(rec_skill.skill_id)

        # 레벨 순으로 정렬
        result = []
        for sid in recommended:
            skill_info = self.get_skill_info(sid)
            if skill_info:
                result.append(skill_info)

        result.sort(key=lambda x: x.required_level)
        return result

    def build_leveling_progression(self, target_skill_id: str) -> Dict:
        """타겟 스킬을 위한 레벨링 진행 생성"""
        target = self.get_skill_info(target_skill_id)
        if not target:
            return {}

        leveling_skills = self.get_leveling_skills(target_skill_id)

        progression = {
            "target_skill": target.name,
            "target_level": target.required_level,
            "tags": target.tags,
            "progression": []
        }

        # 레벨별 스킬 배치
        current_level = 1

        for skill in leveling_skills:
            if skill.required_level <= target.required_level:
                progression["progression"].append({
                    "level": skill.required_level,
                    "skill": skill.name,
                    "until_level": target.required_level if skill == leveling_skills[-1] else None
                })

        # 타겟 스킬 추가
        progression["progression"].append({
            "level": target.required_level,
            "skill": target.name,
            "note": "Switch to main skill"
        })

        return progression


class ActGuideSearcher:
    """액트 가이드 검색기"""

    # 클래스/어센던시 한국어 번역
    CLASS_TRANSLATIONS = {
        "Marauder": "마라우더",
        "Witch": "마녀",
        "Ranger": "레인저",
        "Duelist": "듀얼리스트",
        "Templar": "템플러",
        "Shadow": "쉐도우",
        "Scion": "시온"
    }

    ASCENDANCY_TRANSLATIONS = {
        # Marauder
        "Juggernaut": "저거너트",
        "Berserker": "버서커",
        "Chieftain": "치프틴",
        # Witch
        "Necromancer": "네크로맨서",
        "Elementalist": "엘리멘탈리스트",
        "Occultist": "오컬티스트",
        # Ranger
        "Deadeye": "데드아이",
        "Raider": "레이더",
        "Pathfinder": "패스파인더",
        # Duelist
        "Slayer": "슬레이어",
        "Gladiator": "글래디에이터",
        "Champion": "챔피언",
        # Templar
        "Inquisitor": "인퀴지터",
        "Hierophant": "하이에로펀트",
        "Guardian": "가디언",
        # Shadow
        "Assassin": "어쌔신",
        "Trickster": "트릭스터",
        "Saboteur": "사보추어",
        # Scion
        "Ascendant": "어센던트"
    }

    # 레벨링 장비 한국어 번역
    GEAR_TRANSLATIONS = {
        "Wanderlust boots": "방랑욕 장화",
        "Lifesprig wands": "생명나무 차원마법봉",
        "Praxis rings": "프락시스 반지",
        "Goldrim": "황금테",
        "Tabula Rasa": "백지상태"
    }

    def __init__(self, skill_system: SkillTagSystem):
        self.skill_system = skill_system
        self._load_item_translations()

    def _load_item_translations(self):
        """아이템 번역 데이터 로드"""
        self.item_translations = {}
        try:
            with open(TRANSLATIONS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.item_translations = data.get("items", {})
        except Exception as e:
            print(f"[WARN] Failed to load item translations: {e}")

    def search_guides(self, skill_name: str, class_name: str = "") -> Dict:
        """스킬에 대한 가이드 검색"""
        results = {
            "skill": skill_name,
            "class": class_name,
            "guides_found": [],
            "search_queries": []
        }

        # 검색 쿼리 생성
        queries = [
            f"POE {skill_name} leveling guide 3.27",
            f"POE {skill_name} {class_name} act guide",
            f"POE {skill_name} league starter guide",
        ]

        results["search_queries"] = queries

        # 여기서 실제로 검색을 수행할 수 있음
        # 현재는 쿼리만 생성

        return results

    def search_youtube_guides(self, skill_name: str, class_name: str = "") -> List[Dict]:
        """YouTube API로 가이드 검색 (API 키 없이 기본 검색)"""
        guides = []

        # YouTube Data API 없이 검색하려면 웹 스크래핑이 필요
        # 현재는 검색 URL만 제공

        return guides

    def check_guide_exists(self, skill_name: str, class_name: str = "") -> Dict:
        """가이드 존재 여부 확인"""
        result = {
            "skill": skill_name,
            "class": class_name,
            "has_leveling_guide": False,
            "has_endgame_guide": False,
            "recommended_sources": [],
            "alternative_builds": []
        }

        # 인기 빌드인지 확인 (태그 기반)
        skill_info = self.skill_system.find_skill_by_name(skill_name)

        if skill_info:
            # Brand 스킬은 일반적으로 가이드가 많음
            if "brand" in skill_info.tags:
                result["has_leveling_guide"] = True
                result["has_endgame_guide"] = True
                result["recommended_sources"] = [
                    "YouTube: Search for brand leveling guides",
                    "poe-vault.com: Velyna's Storm Brand guide",
                    "maxroll.gg: Brand build guides"
                ]

            # 유사 스킬 추천
            similar = self.skill_system.get_similar_skills(skill_info.skill_id)
            result["alternative_builds"] = [s.name for s in similar[:3]]

        return result

    def get_youtube_search_url(self, skill_name: str, class_name: str = "") -> str:
        """YouTube 검색 URL 생성"""
        query = f"POE {skill_name} {class_name} leveling guide 3.27".strip()
        encoded = query.replace(" ", "+")
        return f"https://www.youtube.com/results?search_query={encoded}"

    def get_reddit_search_url(self, skill_name: str) -> str:
        """Reddit 검색 URL 생성"""
        query = f"{skill_name} build guide"
        encoded = query.replace(" ", "+")
        return f"https://www.reddit.com/r/PathOfExileBuilds/search/?q={encoded}&restrict_sr=1"

    def get_poe_forum_search_url(self, skill_name: str, class_name: str = "") -> str:
        """POE Forum 검색 URL 생성"""
        # 클래스별 포럼 섹션
        class_forum_ids = {
            "Templar": "41",
            "Witch": "24",
            "Marauder": "261",
            "Ranger": "303",
            "Shadow": "436",
            "Duelist": "438",
            "Scion": "450"
        }

        forum_id = class_forum_ids.get(class_name, "")
        query = f"{skill_name}".replace(" ", "+")

        if forum_id:
            return f"https://www.pathofexile.com/forum/view-forum/{forum_id}?search={query}"
        else:
            return f"https://www.pathofexile.com/forum/search?q={query}"

    def generate_leveling_guide_summary(self, skill_name: str, class_name: str, ascendancy: str, korean: bool = False) -> Dict:
        """레벨링 가이드 요약 생성 - poedb.tw 데이터 사용

        Args:
            skill_name: 스킬 이름 (영어 또는 한국어)
            class_name: 클래스 이름
            ascendancy: 어센던시 이름
            korean: True면 한국어 가이드 출력
        """
        skill_info = self.skill_system.find_skill_by_name(skill_name)

        if not skill_info:
            return {"error": f"Skill not found: {skill_name}"}

        # 기본 레벨링 정보 생성 (WPF UI에서 기대하는 형식)
        summary = {
            "skill_name": skill_name,
            "class_name": class_name,
            "ascendancy": ascendancy,
            "tags": skill_info.tags,
            "skill_available_at": skill_info.required_level,
            "tips": [],
            "gem_progression": [],
            "leveling_gear": [],
            "ascendancy_order": [],
            "quest_info": None,
            "vendor_recipes": [],
            "transition_info": None  # 스킬 전환 정보
        }

        # 스킬 전환 정보 추가
        leveling_recommendations = self.skill_system.get_leveling_skill_for_build(skill_name)
        if leveling_recommendations:
            first_rec = leveling_recommendations[0]

            # no-transition 스킬인 경우
            if first_rec.get("no_transition"):
                # no-transition 스킬도 퀘스트 정보 추가
                skill_quest_info = self.skill_system.get_gem_quest_info(skill_name, class_name)
                summary["transition_info"] = {
                    "type": "no_transition",
                    "message": f"Use {skill_name} from Act start",
                    "available_level": first_rec.get("available_level"),
                    "reason": first_rec.get("reason"),
                    "skill_quest_info": skill_quest_info
                }
                if skill_quest_info:
                    summary["tips"].insert(0, f"Get {skill_name} from '{skill_quest_info['quest']}' (Act {skill_quest_info['act']})")
                    summary["tips"].insert(1, f"No leveling skill needed - use {skill_name} from level {first_rec.get('available_level', 1)}")
                else:
                    summary["tips"].insert(0, f"No leveling skill needed - use {skill_name} from level {first_rec.get('available_level', 1)}")
            else:
                # 전환 필요 스킬
                leveling_skill = first_rec.get("skill", "")
                transition_info = self.skill_system.get_transition_info(leveling_skill, skill_name, ascendancy)

                # 레벨링 스킬 퀘스트 정보 추가
                leveling_skill_quest = self.skill_system.get_gem_quest_info(leveling_skill, class_name)

                summary["transition_info"] = {
                    "type": "transition_required",
                    "leveling_skill": leveling_skill,
                    "leveling_skill_kr": first_rec.get("skill_kr"),
                    "leveling_skill_quest": leveling_skill_quest,
                    "alternatives": [r["skill"] for r in leveling_recommendations[1:3]],
                    "transition_point": transition_info.get("transition_point"),
                    "recommended_level": transition_info.get("recommended_level"),
                    "tips": transition_info.get("tips", [])
                }

                # 4th ascendancy 정보가 있으면 추가
                if "4th_ascendancy_info" in transition_info:
                    summary["transition_info"]["4th_ascendancy_info"] = transition_info["4th_ascendancy_info"]
                    asc_info = transition_info["4th_ascendancy_info"]
                    if leveling_skill_quest:
                        summary["tips"].insert(0, f"Get {leveling_skill} from '{leveling_skill_quest['quest']}' (Act {leveling_skill_quest['act']})")
                        summary["tips"].insert(1, f"Use {leveling_skill} until 4th Ascendancy ({asc_info['ascendancy']})")
                        summary["tips"].insert(2, f"Key nodes: {', '.join(asc_info['key_nodes'])}")
                    else:
                        summary["tips"].insert(0, f"Use {leveling_skill} until 4th Ascendancy ({asc_info['ascendancy']})")
                        summary["tips"].insert(1, f"Key nodes: {', '.join(asc_info['key_nodes'])}")
                else:
                    point = transition_info.get("transition_point", "maps")
                    level = transition_info.get("recommended_level", 68)
                    if leveling_skill_quest:
                        summary["tips"].insert(0, f"Get {leveling_skill} from '{leveling_skill_quest['quest']}' (Act {leveling_skill_quest['act']})")
                        summary["tips"].insert(1, f"Level with {leveling_skill}, switch to {skill_name} at level {level} ({point})")
                    else:
                        summary["tips"].insert(0, f"Level with {leveling_skill}, switch to {skill_name} at level {level} ({point})")

        # 퀘스트 정보 추가 (no-transition이 아닌 경우에만 팁 추가 - 중복 방지)
        quest_info = self.skill_system.get_gem_quest_info(skill_name, class_name)
        if quest_info:
            summary["quest_info"] = quest_info
            # no-transition이면 이미 위에서 팁 추가됨
            is_no_transition = summary.get("transition_info", {}).get("type") == "no_transition"
            if not is_no_transition:
                summary["tips"].append(f"Get {skill_name} from '{quest_info['quest']}' (Act {quest_info['act']})")

        # 레벨링 레시피 추가
        recipes = self.skill_system.get_leveling_recipes()
        summary["vendor_recipes"] = recipes[:5]

        # 젬 진행 생성 (퀘스트 보상 기반 또는 기본값)
        quest_progression = self._build_gem_progression(skill_info, class_name)
        if quest_progression:
            summary["gem_progression"] = quest_progression
        else:
            # 퀘스트 데이터가 없으면 기본 진행 사용
            summary["gem_progression"] = self._get_default_gem_progression(skill_info, skill_name)

        # 태그 기반 팁 생성
        summary["tips"].extend(self._generate_tag_tips(skill_info, skill_name))

        # 레벨링 장비 (공통)
        summary["leveling_gear"] = [
            {"level": 1, "item": "Wanderlust boots", "reason": "Cannot be frozen, movement speed"},
            {"level": 1, "item": "Lifesprig wands", "reason": "+1 to spell gems, spell damage"},
            {"level": 22, "item": "Praxis rings", "reason": "Mana cost reduction"},
            {"level": 24, "item": "Goldrim", "reason": "All resistances"},
            {"level": 32, "item": "Tabula Rasa", "reason": "6-link for main skill"}
        ]

        # 어센던시 순서
        summary["ascendancy_order"] = self._get_ascendancy_order(ascendancy)

        # 한국어 변환
        if korean:
            summary = self._convert_to_korean(summary)

        return summary

    def _convert_to_korean(self, summary: Dict) -> Dict:
        """가이드 요약을 한국어로 변환"""
        kr_summary = summary.copy()

        # 스킬 이름 변환 (Transfigured gem 처리)
        skill_name = summary.get("skill_name", "")
        skill_kr = self.skill_system.translations.get(skill_name)  # 직접 조회

        # Transfigured gem인 경우 기본 스킬 이름으로 시도
        if not skill_kr and " of " in skill_name:
            base_skill = skill_name.split(" of ")[0]
            base_kr = self.skill_system.translations.get(base_skill)
            suffix = skill_name.split(" of ")[1]
            # 접미사 번역
            suffix_translations = {
                "Dissipation": "소멸",
                "Power": "권능",
                "Indecision": "우유부단",
                "Arcing": "호",
                "Combustion": "점화",
            }
            suffix_kr = suffix_translations.get(suffix, suffix)
            if base_kr:
                skill_kr = f"{base_kr} ({suffix_kr})"

        if skill_kr:
            kr_summary["skill_name_kr"] = skill_kr
        else:
            kr_summary["skill_name_kr"] = skill_name

        # 클래스/어센던시 변환
        class_name = summary.get("class_name", "")
        ascendancy = summary.get("ascendancy", "")
        kr_summary["class_name_kr"] = self.CLASS_TRANSLATIONS.get(class_name, class_name)
        kr_summary["ascendancy_kr"] = self.ASCENDANCY_TRANSLATIONS.get(ascendancy, ascendancy)

        # 팁 한국어 변환
        kr_summary["tips_kr"] = []
        for tip in summary.get("tips", []):
            kr_tip = self._translate_tip(tip)
            kr_summary["tips_kr"].append(kr_tip)

        # 레벨링 장비 한국어 변환
        kr_summary["leveling_gear_kr"] = []
        for gear in summary.get("leveling_gear", []):
            item_name = gear.get("item", "")
            # 먼저 GEAR_TRANSLATIONS에서 찾고, 없으면 item_translations에서 찾음
            item_kr = self.GEAR_TRANSLATIONS.get(item_name)
            if not item_kr:
                item_kr = self.item_translations.get(item_name, item_name)

            reason_kr = self._translate_gear_reason(gear.get("reason", ""))
            kr_summary["leveling_gear_kr"].append({
                "level": gear.get("level"),
                "item": item_name,
                "item_kr": item_kr,
                "reason": gear.get("reason"),
                "reason_kr": reason_kr
            })

        # transition_info 한국어 변환
        if summary.get("transition_info"):
            trans = summary["transition_info"]
            trans_kr = trans.copy()

            if trans.get("type") == "no_transition":
                trans_kr["message_kr"] = self._translate_tip(trans.get("message", ""))
            else:
                # leveling_skill_kr는 이미 있음
                pass

            kr_summary["transition_info"] = trans_kr

        return kr_summary

    def _translate_tip(self, tip: str) -> str:
        """팁을 한국어로 번역"""
        result = tip

        # 먼저 스킬 이름을 찾아서 번역
        # 일반적인 스킬 이름 패턴 찾기
        import re

        # 스킬 이름 패턴 (대문자로 시작하는 단어들)
        # 긴 패턴 먼저 시도 (Armageddon Brand가 Brand보다 먼저)
        skill_patterns = [
            # 3단어 스킬
            r"Rain Of Arrows", r"Rain of Arrows", r"Ball Lightning",
            # Brand 스킬
            r"Armageddon Brand", r"Penance Brand", r"Storm Brand", r"Wintertide Brand",
            r"Brand Recall",
            # Trap 스킬
            r"Lightning Spire Trap", r"Explosive Trap", r"Bear Trap",
            # 2단어 스킬
            r"Tornado Shot", r"Caustic Arrow", r"Freezing Pulse",
            r"Essence Drain", r"Ground Slam", r"Toxic Rain", r"Scourge Arrow", r"Burning Arrow",
            r"Elemental Overload", r"Spell Echo",
            # 1단어 스킬
            r"Arc", r"Spark", r"Fireball", r"Contagion", r"Bane", r"Soulrend",
            r"Cyclone", r"Earthquake", r"Sunder",
        ]

        for pattern in skill_patterns:
            if pattern in result:
                # Rain Of Arrows -> Rain of Arrows로 정규화
                normalized = pattern.replace("Rain Of Arrows", "Rain of Arrows")
                skill_kr = self.skill_system.get_korean_name(normalized)
                if skill_kr:
                    result = result.replace(pattern, skill_kr)

        # 패턴 기반 번역
        translations = {
            "Get ": "획득: ",
            " from '": " - '",
            "' (Act ": "' (액트 ",
            "No leveling skill needed - use ": "레벨링 스킬 불필요 - ",
            " from level ": "를 레벨 ",
            "Level with ": "레벨링: ",
            ", switch to ": " → ",
            " at level ": " (레벨 ",
            "Use ": "사용: ",
            " until 4th Ascendancy": " → 4차 전직 후 전환",
            "Key nodes: ": "핵심 노드: ",
            "Brand builds": "낙인 빌드",
            "Use Elemental Overload": "정령 과부하 사용",
            "Get Runebinder": "룬바인더 획득",
            " for double brand damage": " (낙인 데미지 2배)",
            " for repositioning": " (위치 재조정용)",
            "Spell Echo": "주문 반향",
            "Cast speed": "시전 속도",
            "Herald of Ice": "얼음 전령",
            "Herald of Thunder": "천둥 전령",
            "Herald of Ash": "재 전령",
            "Herald of Purity": "순결의 전령",
            "Focus on life": "생명력 위주",
            "Focus on energy shield": "에너지 보호막 위주",
            "Use evasion": "회피 활용",
            "Use armor": "방어도 활용",
            "Lightning spells": "번개 주문",
            "Fire spells": "화염 주문",
            "Cold spells": "냉기 주문",
            "Chaos spells": "카오스 주문",
            "Physical spells": "물리 주문",
            "(maps_entry)": "(맵 진입 시)",
            "(maps)": "(맵)",
            "(act10)": "(액트 10)",
            "(Inquisitor)": "",  # 4차 전직에 이미 포함됨
            "(Elementalist)": "",
            "(Necromancer)": "",
            "(Occultist)": "",
        }

        for en, kr in translations.items():
            result = result.replace(en, kr)

        # 닫히지 않은 괄호 수정
        if result.count("(") > result.count(")"):
            result += ")"

        return result

    def _translate_gear_reason(self, reason: str) -> str:
        """장비 설명 한국어 번역"""
        translations = {
            "Cannot be frozen": "동결 면역",
            "movement speed": "이동 속도",
            "+1 to spell gems": "주문 젬 +1",
            "spell damage": "주문 피해",
            "Mana cost reduction": "마나 소모 감소",
            "All resistances": "모든 저항",
            "6-link for main skill": "주요 스킬용 6링크"
        }

        result = reason
        for en, kr in translations.items():
            result = result.replace(en, kr)

        return result

    def _build_gem_progression(self, skill_info: SkillInfo, class_name: str) -> List[Dict]:
        """퀘스트 보상 데이터 기반 젬 진행 생성 (태그 기반 필터링)"""
        progression = []
        quest_rewards = self.skill_system.quest_rewards

        if not quest_rewards:
            return []

        # 빌드 타입 결정 (spell/attack/minion)
        is_spell = "spell" in skill_info.tags
        is_attack = "attack" in skill_info.tags
        is_minion = "minion" in skill_info.tags
        is_brand = "brand" in skill_info.tags

        # 스펠 관련 키워드
        spell_keywords = ["brand", "storm", "orb", "wave", "freeze", "fire", "ice", "arc", "bolt",
                          "nova", "pulse", "blast", "ray", "cascade", "ball", "spark", "flame",
                          "cold", "lightning", "elemental", "curse", "mark", "herald"]
        # 어택 관련 키워드
        attack_keywords = ["slam", "strike", "cleave", "sweep", "cyclone", "crash", "blow",
                          "split", "chain", "steel", "blade", "hammer", "sunder", "rage"]
        # 서포트 젬 키워드
        support_keywords = ["support", "awakened"]
        # 미니언 키워드
        minion_keywords = ["summon", "minion", "zombie", "skeleton", "spectre", "golem"]

        # 클래스별 주요 퀘스트 보상 수집
        gems_by_level = {}

        for quest in quest_rewards:
            rewards = quest.get("rewards", {})

            # 클래스별 보상 확인
            class_rewards = rewards.get(class_name, [])
            if not class_rewards and rewards:
                # 첫 번째 클래스 보상 사용
                class_rewards = list(rewards.values())[0]

            for gem in class_rewards:
                gem_lower = gem.lower()

                # 태그에 맞는 젬만 필터링
                is_relevant = False

                if is_spell or is_brand:
                    # 스펠/브랜드 빌드: 스펠 젬만
                    if any(kw in gem_lower for kw in spell_keywords):
                        is_relevant = True
                    # 서포트 젬도 포함
                    if any(kw in gem_lower for kw in support_keywords):
                        is_relevant = True
                elif is_attack:
                    # 어택 빌드: 어택 젬만
                    if any(kw in gem_lower for kw in attack_keywords):
                        is_relevant = True
                elif is_minion:
                    # 미니언 빌드: 미니언 젬만
                    if any(kw in gem_lower for kw in minion_keywords):
                        is_relevant = True
                else:
                    # 기타: 모든 젬 포함
                    is_relevant = True

                if not is_relevant:
                    continue

                # 젬 레벨 정보 가져오기
                gem_level = 1
                if gem in self.skill_system.gem_levels:
                    gem_level = self.skill_system.gem_levels[gem].get("required_level", 1)

                if gem_level not in gems_by_level:
                    gems_by_level[gem_level] = []
                # 중복 방지
                if gem not in gems_by_level[gem_level]:
                    gems_by_level[gem_level].append(gem)

        # 레벨별로 정렬하여 진행 생성
        for level in sorted(gems_by_level.keys()):
            gems = gems_by_level[level][:3]  # 레벨당 최대 3개
            if gems:  # 빈 레벨 제외
                progression.append({
                    "level": level,
                    "gems": ", ".join(gems)
                })

        return progression[:8]  # 최대 8단계

    def _get_default_gem_progression(self, skill_info: SkillInfo, skill_name: str) -> List[Dict]:
        """기본 젬 진행 (폴백)"""
        if "brand" in skill_info.tags:
            return [
                {"level": 1, "gems": "Freezing Pulse, Frost Bomb"},
                {"level": 4, "gems": "Orb of Storms, Steelskin"},
                {"level": 12, "gems": "Storm Brand, Added Lightning"},
                {"level": 18, "gems": "Controlled Destruction, Brand Recall"},
                {"level": skill_info.required_level, "gems": f"{skill_name}, Inspiration"}
            ]
        elif "spell" in skill_info.tags:
            return [
                {"level": 1, "gems": "Freezing Pulse or Fireball"},
                {"level": 4, "gems": "Flame Wall, Steelskin"},
                {"level": 12, "gems": "Wave of Conviction"},
                {"level": skill_info.required_level, "gems": f"{skill_name}"}
            ]
        elif "attack" in skill_info.tags:
            return [
                {"level": 1, "gems": "Cleave or Ground Slam"},
                {"level": 4, "gems": "Ancestral Protector"},
                {"level": 12, "gems": "Sunder or Splitting Steel"},
                {"level": skill_info.required_level, "gems": f"{skill_name}"}
            ]
        else:
            return [
                {"level": 1, "gems": "Any starter skill"},
                {"level": skill_info.required_level, "gems": f"{skill_name}"}
            ]

    def _generate_tag_tips(self, skill_info: SkillInfo, skill_name: str) -> List[str]:
        """태그 기반 팁 생성"""
        tips = []

        if "brand" in skill_info.tags:
            tips.extend([
                "Get Runebinder for double brand damage",
                "Use Brand Recall for repositioning"
            ])
        if "totem" in skill_info.tags:
            tips.extend([
                "Multiple Totems Support for more damage",
                "Stay at safe distance while totems attack"
            ])
        if "minion" in skill_info.tags:
            tips.extend([
                "Focus on minion life and damage passives",
                "Use Convocation to reposition minions"
            ])
        if "trap" in skill_info.tags or "mine" in skill_info.tags:
            tips.extend([
                "Get trap/mine throwing speed early",
                "Use Multiple Traps/Minefield Support"
            ])

        return tips

    def _get_ascendancy_order(self, ascendancy: str) -> List[str]:
        """어센던시별 추천 순서"""
        orders = {
            "Inquisitor": [
                "Righteous Providence (crit chance)",
                "Inevitable Judgement (ignore resistances)",
                "Augury of Penitence (damage/defence)",
                "Sanctuary (block, life regen)"
            ],
            "Hierophant": [
                "Pursuit of Faith (brand attachment)",
                "Ritual of Awakening (more brands)",
                "Conviction of Power (charges)",
                "Divine Guidance (mana as ES)"
            ],
            "Necromancer": [
                "Mindless Aggression (minion speed/damage)",
                "Unnatural Strength (+2 minion gems)",
                "Bone Barrier (defences)",
                "Mistress of Sacrifice (offerings)"
            ],
            "Elementalist": [
                "Shaper of Flames (ignite)",
                "Mastermind of Discord (exposure)",
                "Heart of Destruction (more damage)",
                "Bastion of Elements (aegis)"
            ],
            "Champion": [
                "Unstoppable Hero (fortify)",
                "Master of Metal (impale)",
                "Inspirational (aura effect)",
                "First to Strike (adrenaline)"
            ],
            "Assassin": [
                "Mistwalker (elusive)",
                "Opportunistic (damage)",
                "Ambush and Assassinate (crit)",
                "Toxic Delivery (poison)"
            ]
        }

        return orders.get(ascendancy, [
            "First lab: Damage/utility",
            "Second lab: Defence",
            "Third lab: More damage",
            "Uber lab: Capstone"
        ])


def analyze_build_for_guide(pob_xml_path: str) -> Dict:
    """POB XML을 분석하여 가이드 정보 생성"""
    import xml.etree.ElementTree as ET

    with open(pob_xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    result = {
        "main_skill": None,
        "class": None,
        "ascendancy": None,
        "leveling_progression": None,
        "similar_skills": [],
        "search_urls": {}
    }

    # 클래스/어센던시 추출
    class_match = re.search(r'className="([^"]+)"', content)
    ascend_match = re.search(r'ascendClassName="([^"]+)"', content)

    result["class"] = class_match.group(1) if class_match else None
    result["ascendancy"] = ascend_match.group(1) if ascend_match else None

    # 메인 스킬 추출
    main_group_match = re.search(r'mainSocketGroup="(\d+)"', content)
    main_socket_group = int(main_group_match.group(1)) if main_group_match else 1

    # Skills 섹션에서 메인 스킬 찾기
    skills_match = re.search(r'<Skills[^>]*>(.*?)</Skills>', content, re.DOTALL)
    if skills_match:
        skills_text = skills_match.group(1)
        skill_groups = re.findall(r'<Skill[^/][^>]*>.*?</Skill>', skills_text, re.DOTALL)

        if main_socket_group <= len(skill_groups):
            main_skill_group = skill_groups[main_socket_group - 1]

            # 액티브 스킬 찾기 (서포트가 아닌 것)
            gems = re.findall(r'skillId="([^"]+)"[^>]*nameSpec="([^"]+)"', main_skill_group)

            for skill_id, name in gems:
                if "Support" not in skill_id:
                    result["main_skill"] = {
                        "name": name,
                        "skill_id": skill_id
                    }
                    break

    # 스킬 태그 시스템 사용
    if result["main_skill"]:
        skill_system = SkillTagSystem()
        skill_id = result["main_skill"]["skill_id"]

        # 스킬 정보
        skill_info = skill_system.get_skill_info(skill_id)
        if skill_info:
            result["main_skill"]["tags"] = skill_info.tags
            result["main_skill"]["required_level"] = skill_info.required_level

        # 레벨링 진행
        result["leveling_progression"] = skill_system.build_leveling_progression(skill_id)

        # 유사 스킬
        similar = skill_system.get_similar_skills(skill_id)
        result["similar_skills"] = [{"name": s.name, "tags": s.tags} for s in similar]

        # 검색 URL
        searcher = ActGuideSearcher(skill_system)
        skill_name = result["main_skill"]["name"]
        class_name = result["ascendancy"] or result["class"] or ""

        result["search_urls"] = {
            "youtube": searcher.get_youtube_search_url(skill_name, class_name),
            "reddit": searcher.get_reddit_search_url(skill_name)
        }

    return result


def main():
    """테스트"""
    # POB 분석
    pob_path = "d:/Pathcraft-AI/src/PathcraftAI.Parser/temp_penance_brand.xml"

    print("=" * 80)
    print("Build Analysis for Guide Generation")
    print("=" * 80)
    print()

    result = analyze_build_for_guide(pob_path)

    print(f"Class: {result['class']} / {result['ascendancy']}")
    print()

    if result["main_skill"]:
        print(f"Main Skill: {result['main_skill']['name']}")
        if "tags" in result["main_skill"]:
            print(f"Tags: {', '.join(result['main_skill']['tags'])}")
        if "required_level" in result["main_skill"]:
            print(f"Required Level: {result['main_skill']['required_level']}")
    print()

    # 레벨링 가이드 요약 생성
    skill_system = SkillTagSystem()
    searcher = ActGuideSearcher(skill_system)

    if result["main_skill"]:
        guide = searcher.generate_leveling_guide_summary(
            result["main_skill"]["name"],
            result["class"],
            result["ascendancy"]
        )

        print("=" * 80)
        print("LEVELING GUIDE")
        print("=" * 80)
        print()

        if guide.get("tips"):
            print("Tips:")
            for tip in guide["tips"]:
                print(f"  • {tip}")
            print()

        if guide.get("gem_progression"):
            print("Gem Progression:")
            for step in guide["gem_progression"]:
                level = step["level"]
                gems = step["gems"]  # Now it's a string, not a list
                print(f"  Lv {level}: {gems}")
            print()

        if guide.get("leveling_gear"):
            print("Leveling Gear:")
            for item in guide["leveling_gear"]:
                print(f"  Lv {item['level']}: {item['item']} - {item['reason']}")
            print()

        if guide.get("ascendancy_order"):
            print("Ascendancy Order:")
            for asc in guide["ascendancy_order"]:
                print(f"  {asc}")
            print()

    if result["similar_skills"]:
        print("Alternative Skills (same tags):")
        for skill in result["similar_skills"]:
            print(f"  - {skill['name']}")
    print()

    print("Search URLs:")
    for platform, url in result.get("search_urls", {}).items():
        print(f"  {platform}: {url}")

    # POE Forum URL 추가
    if result["main_skill"]:
        forum_url = searcher.get_poe_forum_search_url(
            result["main_skill"]["name"],
            result["class"]
        )
        print(f"  poe_forum: {forum_url}")


if __name__ == '__main__':
    main()
