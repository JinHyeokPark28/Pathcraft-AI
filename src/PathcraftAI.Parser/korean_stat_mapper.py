"""
Korean Stat to Trade API Stat ID Mapper

한국어 스탯 텍스트를 POE Trade API의 stat ID로 변환하는 모듈입니다.
Awakened POE Trade의 stats.ndjson 데이터를 기반으로 합니다.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher


class KoreanStatMapper:
    """한국어 스탯 텍스트를 Trade API stat ID로 변환하는 매퍼"""

    def __init__(self):
        self.korean_to_stat: Dict[str, Dict] = {}  # 한국어 -> stat info
        self.english_to_stat: Dict[str, Dict] = {}  # 영어 ref -> stat info
        self.pseudo_stats: Dict[str, str] = {}  # 자주 사용하는 pseudo stat 매핑
        self._loaded = False

    def load(self, stats_ndjson_path: Optional[str] = None) -> bool:
        """스탯 매핑 데이터 로드

        Args:
            stats_ndjson_path: stats.ndjson 파일 경로. None이면 기본 경로 사용

        Returns:
            로드 성공 여부
        """
        if stats_ndjson_path is None:
            # 기본 경로: tools/awakened-poe-trade/renderer/public/data/ko/stats.ndjson
            base_path = Path(__file__).parent.parent.parent / "tools" / "awakened-poe-trade" / "renderer" / "public" / "data" / "ko" / "stats.ndjson"
            stats_ndjson_path = str(base_path)

        try:
            with open(stats_ndjson_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    data = json.loads(line)

                    # resolve가 있는 경우 첫 번째 줄에서 여러 스탯 처리
                    if "resolve" in data:
                        for stat in data.get("stats", []):
                            self._process_stat_entry(stat)
                    else:
                        self._process_stat_entry(data)

            self._build_pseudo_stat_shortcuts()
            self._loaded = True
            return True

        except Exception as e:
            print(f"[ERROR] Failed to load stats mapping: {e}")
            return False

    def _process_stat_entry(self, stat: Dict):
        """개별 스탯 엔트리 처리"""
        ref = stat.get("ref", "")
        trade_ids = stat.get("trade", {}).get("ids", {})
        matchers = stat.get("matchers", [])

        stat_info = {
            "ref": ref,
            "trade_ids": trade_ids,
            "matchers": matchers,
            "better": stat.get("better", 0)  # 1: 높을수록 좋음, -1: 낮을수록 좋음
        }

        # 영어 ref로 매핑
        if ref:
            self.english_to_stat[ref.lower()] = stat_info

        # 한국어 매처로 매핑
        for matcher in matchers:
            korean_text = matcher.get("string", "")
            if korean_text:
                # 정규화된 키 생성 (공백, # 제거)
                normalized = self._normalize_text(korean_text)
                self.korean_to_stat[normalized] = stat_info

    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화 (검색용)"""
        # 숫자 플레이스홀더 통일
        text = re.sub(r'#~#', '#', text)
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text).strip()
        return text.lower()

    def _build_pseudo_stat_shortcuts(self):
        """자주 사용하는 pseudo stat 바로가기 생성"""
        self.pseudo_stats = {
            # 생명력/마나/에너지 실드
            "총 생명력": "pseudo.pseudo_total_life",
            "총 최대 생명력": "pseudo.pseudo_total_life",
            "총 마나": "pseudo.pseudo_total_mana",
            "총 최대 마나": "pseudo.pseudo_total_mana",
            "총 에너지 실드": "pseudo.pseudo_total_energy_shield",
            "총 최대 에너지 실드": "pseudo.pseudo_total_energy_shield",

            # 저항
            "총 원소 저항": "pseudo.pseudo_total_elemental_resistance",
            "총 화염 저항": "pseudo.pseudo_total_fire_resistance",
            "총 냉기 저항": "pseudo.pseudo_total_cold_resistance",
            "총 번개 저항": "pseudo.pseudo_total_lightning_resistance",
            "총 카오스 저항": "pseudo.pseudo_total_chaos_resistance",

            # 능력치
            "총 힘": "pseudo.pseudo_total_strength",
            "총 민첩": "pseudo.pseudo_total_dexterity",
            "총 지능": "pseudo.pseudo_total_intelligence",
            "총 모든 능력치": "pseudo.pseudo_total_all_attributes",

            # 속도
            "총 공격 속도": "pseudo.pseudo_total_attack_speed",
            "총 시전 속도": "pseudo.pseudo_total_cast_speed",
            "이동 속도": "pseudo.pseudo_increased_movement_speed",

            # 피해
            "총 물리 피해 증가": "pseudo.pseudo_increased_physical_damage",
            "총 원소 피해 증가": "pseudo.pseudo_increased_elemental_damage",
            "총 주문 피해 증가": "pseudo.pseudo_increased_spell_damage",

            # 치명타
            "전역 치명타 확률": "pseudo.pseudo_global_critical_strike_chance",
            "전역 치명타 배율": "pseudo.pseudo_global_critical_strike_multiplier",

            # 젬 레벨
            "총 젬 레벨": "pseudo.pseudo_total_additional_gem_levels",
            "총 주문 젬 레벨": "pseudo.pseudo_total_additional_spell_gem_levels",
            "총 소환수 젬 레벨": "pseudo.pseudo_total_additional_minion_gem_levels",

            # 기타
            "생명력 재생": "pseudo.pseudo_total_life_regen",
            "아이템 희귀도": "pseudo.pseudo_increased_rarity",
        }

    def get_trade_stat_id(self, korean_text: str, mod_type: str = "explicit") -> Optional[str]:
        """한국어 스탯 텍스트를 Trade API stat ID로 변환

        Args:
            korean_text: 한국어 스탯 텍스트
            mod_type: 모드 타입 (explicit, implicit, crafted, enchant, pseudo, fractured)

        Returns:
            Trade API stat ID 또는 None
        """
        if not self._loaded:
            self.load()

        # 1. pseudo stat 바로가기 확인
        normalized = self._normalize_text(korean_text)
        for key, stat_id in self.pseudo_stats.items():
            if key in normalized:
                return stat_id

        # 2. 정확한 한국어 매칭
        if normalized in self.korean_to_stat:
            stat_info = self.korean_to_stat[normalized]
            trade_ids = stat_info.get("trade_ids", {})

            # 요청한 mod_type의 ID 반환
            if mod_type in trade_ids:
                ids = trade_ids[mod_type]
                return ids[0] if ids else None

            # mod_type이 없으면 첫 번째 타입의 ID 반환
            for type_ids in trade_ids.values():
                if type_ids:
                    return type_ids[0]

        # 3. 부분 매칭 (fuzzy search)
        best_match = self._fuzzy_match(normalized)
        if best_match:
            stat_info = best_match
            trade_ids = stat_info.get("trade_ids", {})
            if mod_type in trade_ids and trade_ids[mod_type]:
                return trade_ids[mod_type][0]
            for type_ids in trade_ids.values():
                if type_ids:
                    return type_ids[0]

        return None

    def _fuzzy_match(self, text: str, threshold: float = 0.7) -> Optional[Dict]:
        """유사한 스탯 텍스트 찾기"""
        best_ratio = 0
        best_match = None

        for key, stat_info in self.korean_to_stat.items():
            ratio = SequenceMatcher(None, text, key).ratio()
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = stat_info

        return best_match

    def get_stat_ids_for_search(self, korean_stats: List[str], mod_type: str = "explicit") -> List[Dict]:
        """여러 한국어 스탯을 Trade 검색용 형식으로 변환

        Args:
            korean_stats: 한국어 스탯 텍스트 리스트
            mod_type: 기본 모드 타입

        Returns:
            Trade API 검색에 사용할 스탯 필터 리스트
            [{"id": "explicit.stat_xxx", "min": None, "max": None}, ...]
        """
        result = []
        for stat_text in korean_stats:
            # 숫자 값 추출
            min_val, max_val = self._extract_values(stat_text)

            # stat ID 가져오기
            stat_id = self.get_trade_stat_id(stat_text, mod_type)
            if stat_id:
                entry = {"id": stat_id}
                if min_val is not None:
                    entry["min"] = min_val
                if max_val is not None:
                    entry["max"] = max_val
                result.append(entry)

        return result

    def _extract_values(self, text: str) -> Tuple[Optional[float], Optional[float]]:
        """텍스트에서 숫자 값 추출"""
        # 범위 값: "10~20" 또는 "10 ~ 20"
        range_match = re.search(r'(\d+(?:\.\d+)?)\s*[~-]\s*(\d+(?:\.\d+)?)', text)
        if range_match:
            return float(range_match.group(1)), float(range_match.group(2))

        # 단일 값: "+50" 또는 "50%"
        single_match = re.search(r'[+-]?(\d+(?:\.\d+)?)', text)
        if single_match:
            return float(single_match.group(1)), None

        return None, None

    def search_by_english(self, english_ref: str, mod_type: str = "explicit") -> Optional[str]:
        """영어 ref 텍스트로 stat ID 검색

        Args:
            english_ref: 영어 스탯 참조 텍스트
            mod_type: 모드 타입

        Returns:
            Trade API stat ID
        """
        if not self._loaded:
            self.load()

        normalized = english_ref.lower()

        if normalized in self.english_to_stat:
            stat_info = self.english_to_stat[normalized]
            trade_ids = stat_info.get("trade_ids", {})

            if mod_type in trade_ids and trade_ids[mod_type]:
                return trade_ids[mod_type][0]

        return None

    def get_common_stats(self) -> Dict[str, str]:
        """자주 사용하는 스탯 ID 사전 반환"""
        return {
            # 방어
            "life": "pseudo.pseudo_total_life",
            "mana": "pseudo.pseudo_total_mana",
            "es": "pseudo.pseudo_total_energy_shield",
            "ele_res": "pseudo.pseudo_total_elemental_resistance",
            "chaos_res": "pseudo.pseudo_total_chaos_resistance",

            # 능력치
            "str": "pseudo.pseudo_total_strength",
            "dex": "pseudo.pseudo_total_dexterity",
            "int": "pseudo.pseudo_total_intelligence",
            "all_attr": "pseudo.pseudo_total_all_attributes",

            # 공격
            "attack_speed": "pseudo.pseudo_total_attack_speed",
            "cast_speed": "pseudo.pseudo_total_cast_speed",
            "crit_chance": "pseudo.pseudo_global_critical_strike_chance",
            "crit_multi": "pseudo.pseudo_global_critical_strike_multiplier",

            # 피해
            "phys_dmg": "pseudo.pseudo_increased_physical_damage",
            "ele_dmg": "pseudo.pseudo_increased_elemental_damage",
            "spell_dmg": "pseudo.pseudo_increased_spell_damage",

            # 이동
            "move_speed": "pseudo.pseudo_increased_movement_speed",

            # 젬
            "gem_level": "pseudo.pseudo_total_additional_gem_levels",
            "spell_gem": "pseudo.pseudo_total_additional_spell_gem_levels",
            "minion_gem": "pseudo.pseudo_total_additional_minion_gem_levels",
        }

    def print_stat_info(self, korean_text: str):
        """스탯 정보 디버깅용 출력"""
        if not self._loaded:
            self.load()

        normalized = self._normalize_text(korean_text)

        print(f"\n=== Stat Info for: {korean_text} ===")
        print(f"Normalized: {normalized}")

        if normalized in self.korean_to_stat:
            stat_info = self.korean_to_stat[normalized]
            print(f"English ref: {stat_info.get('ref', 'N/A')}")
            print(f"Trade IDs: {json.dumps(stat_info.get('trade_ids', {}), indent=2)}")
        else:
            # fuzzy match 시도
            best_match = self._fuzzy_match(normalized)
            if best_match:
                print(f"Fuzzy match found:")
                print(f"English ref: {best_match.get('ref', 'N/A')}")
                print(f"Trade IDs: {json.dumps(best_match.get('trade_ids', {}), indent=2)}")
            else:
                print("No match found")


# 싱글톤 인스턴스
_mapper_instance = None

def get_stat_mapper() -> KoreanStatMapper:
    """전역 매퍼 인스턴스 반환"""
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = KoreanStatMapper()
        _mapper_instance.load()
    return _mapper_instance


if __name__ == "__main__":
    # 테스트
    mapper = KoreanStatMapper()
    if mapper.load():
        print(f"Loaded {len(mapper.korean_to_stat)} Korean stats")
        print(f"Loaded {len(mapper.english_to_stat)} English refs")

        # 테스트 케이스
        test_stats = [
            "최대 생명력 +#",
            "원소 저항 +#%",
            "공격 속도 #% 증가",
            "주문 피해 #% 증가",
            "총 생명력",  # pseudo stat shortcut
            "도끼 공격 시 물리 피해 #~# 추가",
        ]

        print("\n=== Test Results ===")
        for stat in test_stats:
            stat_id = mapper.get_trade_stat_id(stat)
            print(f"{stat} -> {stat_id}")
