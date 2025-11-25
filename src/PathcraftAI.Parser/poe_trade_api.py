#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POE Trade API Integration
실제 거래소에서 구매 가능한 아이템 검색
"""

import sys
import time
import json
import requests
from typing import List, Dict, Optional, Tuple

# 한국어 스탯 매퍼 (지연 로딩)
_korean_stat_mapper = None

def get_korean_stat_mapper():
    """한국어 스탯 매퍼 지연 로딩"""
    global _korean_stat_mapper
    if _korean_stat_mapper is None:
        try:
            from korean_stat_mapper import KoreanStatMapper
            _korean_stat_mapper = KoreanStatMapper()
            _korean_stat_mapper.load()
        except Exception as e:
            print(f"[WARNING] Failed to load Korean stat mapper: {e}")
            _korean_stat_mapper = None
    return _korean_stat_mapper

# UTF-8 설정
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


class POETradeAPI:
    """POE Trade API 클라이언트"""

    # 키스톤 이름 → POE Trade 스탯 ID 매핑
    # Skin of the Lords가 부여하는 키스톤들
    KEYSTONE_STAT_IDS = {
        # 일반 키스톤
        "Acrobatics": "explicit.stat_2896346114",
        "Ancestral Bond": "explicit.stat_3266553979",
        "Arrow Dancing": "explicit.stat_3032386329",
        "Avatar of Fire": "explicit.stat_1263350427",
        "Blood Magic": "explicit.stat_1328136183",
        "Chaos Inoculation": "explicit.stat_2483795307",
        "Conduit": "explicit.stat_2461965203",
        "Crimson Dance": "explicit.stat_1579978679",
        "Divine Shield": "explicit.stat_3820016156",
        "Eldritch Battery": "explicit.stat_2461965203",
        "Elemental Equilibrium": "explicit.stat_3807731194",
        "Elemental Overload": "explicit.stat_1182648501",
        "Ghost Dance": "explicit.stat_4148815556",
        "Ghost Reaver": "explicit.stat_1448951389",
        "Glancing Blows": "explicit.stat_2896346114",
        "Hollow Palm Technique": "explicit.stat_322196132",
        "Imbalanced Guard": "explicit.stat_3693891908",
        "Inner Conviction": "explicit.stat_2856653653",
        "Iron Grip": "explicit.stat_3324362277",
        "Iron Reflexes": "explicit.stat_2480590696",
        "Iron Will": "explicit.stat_1314617696",
        "Lethe Shade": "explicit.stat_1260240043",
        "Magebane": "explicit.stat_1001829678",
        "Mind Over Matter": "explicit.stat_969865219",
        "Minion Instability": "explicit.stat_1778298516",
        "Mortal Conviction": "explicit.stat_2261614584",
        "Necromantic Aegis": "explicit.stat_3948776321",
        "Pain Attunement": "explicit.stat_4281867118",
        "Perfect Agony": "explicit.stat_1279106657",
        "Phase Acrobatics": "explicit.stat_1597063559",
        "Point Blank": "explicit.stat_3118675390",
        "Precise Technique": "explicit.stat_2260572615",
        "Resolute Technique": "explicit.stat_2899094186",
        "Runebinder": "explicit.stat_2419053278",
        "Supreme Ego": "explicit.stat_2461965203",
        "The Agnostic": "explicit.stat_654808123",
        "Unwavering Stance": "explicit.stat_3696241943",
        "Vaal Pact": "explicit.stat_2461965203",
        "Versatile Combatant": "explicit.stat_350598685",
        "Wicked Ward": "explicit.stat_1175385867",
        "Wind Dancer": "explicit.stat_2896346114",
        "Zealot's Oath": "explicit.stat_2101038468",
    }

    def __init__(self, league: str = "Keepers"):
        self.league = league
        self.base_url = "https://www.pathofexile.com/api/trade"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PathcraftAI/1.0 (contact: pathcraft@example.com)',
            'Content-Type': 'application/json'
        })
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  # 1초 대기 (Rate limit 방지)

    def _wait_for_rate_limit(self):
        """Rate limit 준수"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)

        self.last_request_time = time.time()

    def search_item(
        self,
        item_name: str,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        item_type: Optional[str] = None,
        stats: Optional[List[Dict]] = None,
        influence: Optional[str] = None,
        links: Optional[int] = None,
        sockets: Optional[int] = None,
        corrupted: Optional[bool] = None,
        foulborn: Optional[bool] = None,
        keystone: Optional[str] = None,
        limit: int = 10,
        # 추가 필터들
        ilvl_min: Optional[int] = None,
        ilvl_max: Optional[int] = None,
        quality_min: Optional[int] = None,
        armour_min: Optional[int] = None,
        evasion_min: Optional[int] = None,
        energy_shield_min: Optional[int] = None,
        dps_min: Optional[float] = None,
        pdps_min: Optional[float] = None,
        gem_level_min: Optional[int] = None,
        rarity: Optional[str] = None,
    ) -> List[Dict]:
        """
        아이템 검색

        Args:
            item_name: 아이템 이름
            min_price: 최소 가격 (chaos orbs)
            max_price: 최대 가격 (chaos orbs)
            item_type: 아이템 타입 (예: "Body Armour")
            stats: 요구 스탯 리스트
            influence: 영향력 (shaper, elder, crusader, redeemer, hunter, warlord)
            links: 최소 링크 수
            sockets: 최소 소켓 수
            corrupted: 부패 여부
            foulborn: Foulborn 여부 (Settlers 리그)
            keystone: 키스톤 이름 (Skin of the Lords 등)
            limit: 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        try:
            # 검색 쿼리 생성
            query = self._build_query(
                item_name=item_name,
                min_price=min_price,
                max_price=max_price,
                item_type=item_type,
                stats=stats,
                influence=influence,
                links=links,
                sockets=sockets,
                corrupted=corrupted,
                foulborn=foulborn,
                keystone=keystone,
                ilvl_min=ilvl_min,
                ilvl_max=ilvl_max,
                quality_min=quality_min,
                armour_min=armour_min,
                evasion_min=evasion_min,
                energy_shield_min=energy_shield_min,
                dps_min=dps_min,
                pdps_min=pdps_min,
                gem_level_min=gem_level_min,
                rarity=rarity,
            )

            # Rate limit 준수
            self._wait_for_rate_limit()

            # 검색 요청
            search_url = f"{self.base_url}/search/{self.league}"
            response = self.session.post(search_url, json=query)
            response.raise_for_status()

            search_data = response.json()
            search_id = search_data.get('id', '')
            result_ids = search_data.get('result', [])[:limit]

            if not result_ids:
                return []

            # 아이템 상세 정보 가져오기
            items = self._fetch_items(result_ids)

            # Trade URL 추가
            trade_url = f"https://www.pathofexile.com/trade/search/{self.league}/{search_id}" if search_id else ""
            for item in items:
                item['trade_url'] = trade_url

            return items

        except Exception as e:
            print(f"[ERROR] Trade search failed: {e}", file=sys.stderr)
            return []

    def get_trade_url(
        self,
        item_name: str = "",
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        item_type: Optional[str] = None,
        stats: Optional[List[Dict]] = None,
        influence: Optional[str] = None,
        links: Optional[int] = None,
        sockets: Optional[int] = None,
        corrupted: Optional[bool] = None,
        foulborn: Optional[bool] = None,
        keystone: Optional[str] = None,
        # 추가 필터들
        ilvl_min: Optional[int] = None,
        ilvl_max: Optional[int] = None,
        quality_min: Optional[int] = None,
        armour_min: Optional[int] = None,
        evasion_min: Optional[int] = None,
        energy_shield_min: Optional[int] = None,
        dps_min: Optional[float] = None,
        pdps_min: Optional[float] = None,
        gem_level_min: Optional[int] = None,
        gem_quality_min: Optional[int] = None,
        gem_alternate: Optional[int] = None,
        rarity: Optional[str] = None,
    ) -> Optional[str]:
        """
        검색 조건에 맞는 Trade URL 생성 (아이템 조회 없이)

        Returns:
            Trade URL 문자열 또는 None
        """
        try:
            # 검색 쿼리 생성
            query = self._build_query(
                item_name=item_name,
                min_price=min_price,
                max_price=max_price,
                item_type=item_type,
                stats=stats,
                influence=influence,
                links=links,
                sockets=sockets,
                corrupted=corrupted,
                foulborn=foulborn,
                keystone=keystone,
                ilvl_min=ilvl_min,
                ilvl_max=ilvl_max,
                quality_min=quality_min,
                armour_min=armour_min,
                evasion_min=evasion_min,
                energy_shield_min=energy_shield_min,
                dps_min=dps_min,
                pdps_min=pdps_min,
                gem_level_min=gem_level_min,
                gem_quality_min=gem_quality_min,
                gem_alternate=gem_alternate,
                rarity=rarity,
            )

            # Rate limit 준수
            self._wait_for_rate_limit()

            # 검색 요청
            search_url = f"{self.base_url}/search/{self.league}"
            response = self.session.post(search_url, json=query)
            response.raise_for_status()

            search_data = response.json()
            search_id = search_data.get('id', '')

            if search_id:
                return f"https://www.pathofexile.com/trade/search/{self.league}/{search_id}"

            return None

        except Exception as e:
            print(f"[ERROR] Get trade URL failed: {e}", file=sys.stderr)
            return None

    def search_unique_item_url(self, item_name: str, max_price: Optional[int] = None) -> Optional[str]:
        """
        유니크 아이템 검색 Trade URL 생성

        Args:
            item_name: 유니크 아이템 이름 (예: "Mageblood", "Headhunter")
            max_price: 최대 가격 (chaos)

        Returns:
            Trade URL
        """
        return self.get_trade_url(
            item_name=item_name,
            max_price=max_price
        )

    def search_stat_item_url(
        self,
        item_type: str,
        stat_requirements: List[Dict[str, any]],
        max_price: Optional[int] = None
    ) -> Optional[str]:
        """
        스탯 기반 아이템 검색 Trade URL 생성

        Args:
            item_type: 아이템 타입 (예: "Ring", "Belt", "Amulet")
            stat_requirements: 스탯 요구사항 리스트
                [{"id": "pseudo.pseudo_total_life", "min": 70}]
            max_price: 최대 가격 (chaos)

        Returns:
            Trade URL
        """
        stats = []
        for req in stat_requirements:
            stat = {"id": req.get("id", ""), "disabled": False}
            if "min" in req or "max" in req:
                stat["value"] = {}
                if "min" in req:
                    stat["value"]["min"] = req["min"]
                if "max" in req:
                    stat["value"]["max"] = req["max"]
            stats.append(stat)

        return self.get_trade_url(
            item_type=item_type,
            stats=stats,
            max_price=max_price
        )

    def _build_query(
        self,
        item_name: str,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        item_type: Optional[str] = None,
        stats: Optional[List[Dict]] = None,
        influence: Optional[str] = None,
        links: Optional[int] = None,
        sockets: Optional[int] = None,
        corrupted: Optional[bool] = None,
        foulborn: Optional[bool] = None,
        keystone: Optional[str] = None,
        # 추가 필터들
        ilvl_min: Optional[int] = None,
        ilvl_max: Optional[int] = None,
        quality_min: Optional[int] = None,
        quality_max: Optional[int] = None,
        # 방어구 필터
        armour_min: Optional[int] = None,
        evasion_min: Optional[int] = None,
        energy_shield_min: Optional[int] = None,
        # 무기 필터
        dps_min: Optional[float] = None,
        pdps_min: Optional[float] = None,
        edps_min: Optional[float] = None,
        crit_min: Optional[float] = None,
        aps_min: Optional[float] = None,
        # 젬 필터
        gem_level_min: Optional[int] = None,
        gem_quality_min: Optional[int] = None,
        gem_alternate: Optional[int] = None,  # 1=Anomalous, 2=Divergent, 3=Phantasmal
        # 희귀도
        rarity: Optional[str] = None,  # normal, magic, rare, unique
    ) -> Dict:
        """검색 쿼리 생성

        스탯 필터 형식:
        stats = [
            {"id": "explicit.stat_123", "min": 50, "max": 100},  # 명시 모드
            {"id": "implicit.stat_456", "min": 10},              # 암시 모드
            {"id": "crafted.stat_789", "min": 20},               # 제작 모드
            {"id": "enchant.stat_012", "min": 30},               # 인챈트
            {"id": "pseudo.pseudo_total_life", "min": 70},       # 가상 스탯
            {"id": "fractured.stat_345"},                        # 프랙처 모드
        ]

        모드 타입:
        - explicit: 명시 모드
        - implicit: 암시 모드
        - crafted: 제작 모드
        - enchant: 인챈트
        - pseudo: 가상 스탯 (총 저항, 총 생명력 등)
        - fractured: 프랙처 모드
        - veiled: 베일 모드
        - monster: 몬스터 모드
        """
        query = {
            "query": {
                "status": {"option": "online"},  # 온라인 판매자만
                "filters": {}
            },
            "sort": {"price": "asc"}  # 가격 오름차순
        }

        # 아이템 이름 필터
        if item_name:
            query["query"]["name"] = item_name

        # 아이템 타입/카테고리 필터
        # POE Trade API는 카테고리 방식으로 필터링
        CATEGORY_MAP = {
            # 방어구
            "Boots": "armour.boots",
            "Helmet": "armour.helmet",
            "Gloves": "armour.gloves",
            "Body Armour": "armour.chest",
            "Shield": "armour.shield",
            # 악세서리
            "Ring": "accessory.ring",
            "Amulet": "accessory.amulet",
            "Belt": "accessory.belt",
            # 무기
            "One Hand Sword": "weapon.onesword",
            "Two Hand Sword": "weapon.twosword",
            "One Hand Axe": "weapon.oneaxe",
            "Two Hand Axe": "weapon.twoaxe",
            "One Hand Mace": "weapon.onemace",
            "Two Hand Mace": "weapon.twomace",
            "Bow": "weapon.bow",
            "Staff": "weapon.staff",
            "Warstaff": "weapon.warstaff",
            "Claw": "weapon.claw",
            "Dagger": "weapon.dagger",
            "Rune Dagger": "weapon.runedagger",
            "Wand": "weapon.wand",
            "Sceptre": "weapon.sceptre",
            # 주얼
            "Jewel": "jewel",
            "Abyss Jewel": "jewel.abyss",
            "Cluster Jewel": "jewel.cluster",
            # 플라스크
            "Flask": "flask",
            "Life Flask": "flask.life",
            "Mana Flask": "flask.mana",
            "Utility Flask": "flask.utility",
        }

        if item_type:
            category = CATEGORY_MAP.get(item_type)
            if category:
                query["query"]["filters"]["type_filters"] = {
                    "filters": {
                        "category": {"option": category}
                    }
                }
            else:
                # 매핑에 없으면 직접 type으로 시도
                query["query"]["type"] = item_type

        # 가격 필터
        price_filter = {}
        if min_price is not None:
            price_filter["min"] = min_price
        if max_price is not None:
            price_filter["max"] = max_price

        if price_filter:
            query["query"]["filters"]["trade_filters"] = {
                "filters": {
                    "price": {
                        **price_filter,
                        "option": "chaos"
                    }
                }
            }

        # misc_filters (영향력, 부패, Foulborn 등)
        misc_filters = {}

        # 영향력 필터
        if influence:
            influence_map = {
                "shaper": "shaper_item",
                "elder": "elder_item",
                "crusader": "crusader_item",
                "redeemer": "redeemer_item",
                "hunter": "hunter_item",
                "warlord": "warlord_item",
                "synthesised": "synthesised_item",
                "fractured": "fractured_item"
            }
            if influence.lower() in influence_map:
                misc_filters[influence_map[influence.lower()]] = {"option": "true"}

        # 부패 필터
        if corrupted is not None:
            misc_filters["corrupted"] = {"option": "true" if corrupted else "false"}

        # Foulborn 필터 (Settlers 리그)
        if foulborn:
            misc_filters["foil_variation"] = {"option": 1}

        # 아이템 레벨 필터
        if ilvl_min is not None or ilvl_max is not None:
            ilvl_filter = {}
            if ilvl_min is not None:
                ilvl_filter["min"] = ilvl_min
            if ilvl_max is not None:
                ilvl_filter["max"] = ilvl_max
            misc_filters["ilvl"] = ilvl_filter

        # 퀄리티 필터
        if quality_min is not None or quality_max is not None:
            quality_filter = {}
            if quality_min is not None:
                quality_filter["min"] = quality_min
            if quality_max is not None:
                quality_filter["max"] = quality_max
            misc_filters["quality"] = quality_filter

        # 젬 레벨 필터
        if gem_level_min is not None:
            misc_filters["gem_level"] = {"min": gem_level_min}

        # 젬 퀄리티 필터
        if gem_quality_min is not None:
            misc_filters["gem_quality"] = {"min": gem_quality_min}

        # 이상 젬 타입 (1=Anomalous, 2=Divergent, 3=Phantasmal)
        if gem_alternate is not None:
            misc_filters["gem_alternate_quality"] = {"option": gem_alternate}

        if misc_filters:
            query["query"]["filters"]["misc_filters"] = {"filters": misc_filters}

        # 희귀도 필터 (기존 type_filters에 추가)
        if rarity:
            if "type_filters" not in query["query"]["filters"]:
                query["query"]["filters"]["type_filters"] = {"filters": {}}
            query["query"]["filters"]["type_filters"]["filters"]["rarity"] = {"option": rarity}

        # 방어구 필터
        armour_filters = {}
        if armour_min is not None:
            armour_filters["ar"] = {"min": armour_min}
        if evasion_min is not None:
            armour_filters["ev"] = {"min": evasion_min}
        if energy_shield_min is not None:
            armour_filters["es"] = {"min": energy_shield_min}

        if armour_filters:
            query["query"]["filters"]["armour_filters"] = {"filters": armour_filters}

        # 무기 필터
        weapon_filters = {}
        if dps_min is not None:
            weapon_filters["dps"] = {"min": dps_min}
        if pdps_min is not None:
            weapon_filters["pdps"] = {"min": pdps_min}
        if edps_min is not None:
            weapon_filters["edps"] = {"min": edps_min}
        if crit_min is not None:
            weapon_filters["crit"] = {"min": crit_min}
        if aps_min is not None:
            weapon_filters["aps"] = {"min": aps_min}

        if weapon_filters:
            query["query"]["filters"]["weapon_filters"] = {"filters": weapon_filters}

        # 소켓/링크 필터
        socket_filters = {}
        if links is not None:
            socket_filters["links"] = {"min": links}
        if sockets is not None:
            socket_filters["sockets"] = {"min": sockets}

        if socket_filters:
            query["query"]["filters"]["socket_filters"] = {"filters": socket_filters}

        # 스탯 필터
        stat_filters = []

        # 사용자 지정 스탯
        if stats and len(stats) > 0:
            stat_filters.extend(stats)

        # 키스톤 스탯 필터 (Skin of the Lords 등)
        if keystone:
            # 정확히 일치하는 키스톤 찾기
            keystone_stat_id = self.KEYSTONE_STAT_IDS.get(keystone)
            if keystone_stat_id:
                stat_filters.append({
                    "id": keystone_stat_id,
                    "disabled": False
                })
            else:
                # 부분 일치 시도
                for ks_name, ks_id in self.KEYSTONE_STAT_IDS.items():
                    if keystone.lower() in ks_name.lower() or ks_name.lower() in keystone.lower():
                        stat_filters.append({
                            "id": ks_id,
                            "disabled": False
                        })
                        break

        if stat_filters:
            query["query"]["stats"] = [{
                "type": "and",
                "filters": stat_filters
            }]

        return query

    def _fetch_items(self, item_ids: List[str]) -> List[Dict]:
        """아이템 상세 정보 가져오기"""
        try:
            # Rate limit 준수
            self._wait_for_rate_limit()

            # ID를 10개씩 묶어서 요청 (API 제한)
            item_ids_str = ','.join(item_ids[:10])
            fetch_url = f"{self.base_url}/fetch/{item_ids_str}"

            params = {"query": self.league}
            response = self.session.get(fetch_url, params=params)
            response.raise_for_status()

            fetch_data = response.json()
            results = fetch_data.get('result', [])

            items = []
            for result in results:
                item = self._parse_item(result)
                if item:
                    items.append(item)

            return items

        except Exception as e:
            print(f"[ERROR] Fetch items failed: {e}", file=sys.stderr)
            return []

    def _parse_item(self, result: Dict) -> Optional[Dict]:
        """아이템 데이터 파싱"""
        try:
            item_data = result.get('item', {})
            listing = result.get('listing', {})

            # 가격 정보
            price_data = listing.get('price', {})
            price_amount = price_data.get('amount', 0)
            price_currency = price_data.get('currency', 'chaos')

            # Chaos로 환산
            chaos_price = price_amount
            if price_currency == 'divine':
                chaos_price = price_amount * 110  # 대략적인 환율 (실시간 조회 필요)

            # 판매자 정보
            account = listing.get('account', {})
            seller_name = account.get('name', 'Unknown')
            character_name = account.get('lastCharacterName', '')

            # Whisper 메시지
            whisper = listing.get('whisper', '')

            return {
                'id': result.get('id', ''),
                'name': item_data.get('name', ''),
                'type': item_data.get('typeLine', ''),
                'price_chaos': chaos_price,
                'price_display': f"{price_amount} {price_currency}",
                'seller': seller_name,
                'character': character_name,
                'whisper': whisper,
                'item_level': item_data.get('ilvl', 0),
                'corrupted': item_data.get('corrupted', False),
                'identified': item_data.get('identified', True)
            }

        except Exception as e:
            print(f"[ERROR] Parse item failed: {e}", file=sys.stderr)
            return None

    def search_resistance_ring(
        self,
        min_total_res: int = 60,
        max_price: int = 20
    ) -> List[Dict]:
        """저항 반지 검색 (업그레이드용)"""
        stats = [
            {
                "id": "pseudo.pseudo_total_elemental_resistance",
                "value": {"min": min_total_res}
            }
        ]

        return self.search_item(
            item_name="",
            item_type="Ring",
            max_price=max_price,
            stats=stats,
            limit=5
        )

    def search_6link_body(
        self,
        max_price: int = 60
    ) -> List[Dict]:
        """6링크 방어구 검색"""
        stats = [
            {
                "id": "explicit.stat_1050105434",  # Sockets
                "value": {"min": 6}
            }
        ]

        return self.search_item(
            item_name="",
            item_type="Body Armour",
            max_price=max_price,
            stats=stats,
            limit=5
        )

    def search_high_es_helmet_url(
        self,
        min_es: int = 200,
        max_price: Optional[int] = None
    ) -> Optional[str]:
        """높은 ES 헬멧 검색 URL"""
        return self.get_trade_url(
            item_type="Helmet",
            energy_shield_min=min_es,
            max_price=max_price
        )

    def search_high_pdps_weapon_url(
        self,
        min_pdps: float = 400,
        weapon_type: str = "One Hand Sword",
        max_price: Optional[int] = None
    ) -> Optional[str]:
        """높은 pDPS 무기 검색 URL"""
        return self.get_trade_url(
            item_type=weapon_type,
            pdps_min=min_pdps,
            max_price=max_price
        )

    def search_gem_url(
        self,
        gem_name: str,
        min_level: int = 20,
        min_quality: int = 20,
        alternate_type: Optional[int] = None,  # 1=Anomalous, 2=Divergent, 3=Phantasmal
        max_price: Optional[int] = None
    ) -> Optional[str]:
        """젬 검색 URL"""
        return self.get_trade_url(
            item_name=gem_name,
            gem_level_min=min_level,
            gem_quality_min=min_quality,
            gem_alternate=alternate_type,
            max_price=max_price
        )

    def search_item_with_mod_url(
        self,
        item_type: str,
        mods: List[Dict[str, any]],
        max_price: Optional[int] = None,
        ilvl_min: Optional[int] = None
    ) -> Optional[str]:
        """특정 모드를 가진 아이템 검색 URL

        Args:
            item_type: 아이템 타입
            mods: 모드 리스트
                [
                    {"id": "explicit.stat_123", "min": 50},      # 명시
                    {"id": "implicit.stat_456", "min": 10},      # 암시
                    {"id": "crafted.stat_789"},                   # 제작
                    {"id": "fractured.stat_012", "min": 20},     # 프랙처
                ]
            max_price: 최대 가격
            ilvl_min: 최소 아이템 레벨

        Returns:
            Trade URL
        """
        stats = []
        for mod in mods:
            stat = {"id": mod.get("id", ""), "disabled": False}
            if "min" in mod or "max" in mod:
                stat["value"] = {}
                if "min" in mod:
                    stat["value"]["min"] = mod["min"]
                if "max" in mod:
                    stat["value"]["max"] = mod["max"]
            stats.append(stat)

        return self.get_trade_url(
            item_type=item_type,
            stats=stats,
            max_price=max_price,
            ilvl_min=ilvl_min
        )

    def search_korean_stats_url(
        self,
        item_type: Optional[str] = None,
        korean_stats: Optional[List[Dict]] = None,
        max_price: Optional[int] = None,
        ilvl_min: Optional[int] = None
    ) -> Optional[str]:
        """한국어 스탯 텍스트로 아이템 검색 URL 생성

        Args:
            item_type: 아이템 타입 (예: "Ring", "Helmet")
            korean_stats: 한국어 스탯 리스트
                [
                    {"text": "최대 생명력 +#", "min": 70},
                    {"text": "원소 저항 +#%", "min": 60},
                    {"text": "공격 속도 #% 증가", "min": 10},
                ]
            max_price: 최대 가격 (Chaos)
            ilvl_min: 최소 아이템 레벨

        Returns:
            Trade URL

        Example:
            api.search_korean_stats_url(
                item_type="Ring",
                korean_stats=[
                    {"text": "총 생명력", "min": 70},
                    {"text": "총 원소 저항", "min": 80}
                ],
                max_price=50
            )
        """
        if not korean_stats:
            return None

        mapper = get_korean_stat_mapper()
        if not mapper:
            print("[ERROR] Korean stat mapper not available")
            return None

        # 한국어 스탯을 Trade API 형식으로 변환
        stats = []
        for stat_req in korean_stats:
            korean_text = stat_req.get("text", "")
            mod_type = stat_req.get("mod_type", "explicit")

            # 스탯 ID 조회
            stat_id = mapper.get_trade_stat_id(korean_text, mod_type)
            if stat_id:
                stat = {"id": stat_id, "disabled": False}
                if "min" in stat_req or "max" in stat_req:
                    stat["value"] = {}
                    if "min" in stat_req:
                        stat["value"]["min"] = stat_req["min"]
                    if "max" in stat_req:
                        stat["value"]["max"] = stat_req["max"]
                stats.append(stat)
            else:
                print(f"[WARNING] Could not find stat ID for: {korean_text}")

        if not stats:
            print("[ERROR] No valid stats found")
            return None

        return self.get_trade_url(
            item_type=item_type,
            stats=stats,
            max_price=max_price,
            ilvl_min=ilvl_min
        )

    def search_with_shortcuts_url(
        self,
        item_type: Optional[str] = None,
        shortcuts: Optional[Dict[str, Dict]] = None,
        max_price: Optional[int] = None,
        ilvl_min: Optional[int] = None
    ) -> Optional[str]:
        """단축키로 빠르게 스탯 검색 URL 생성

        Args:
            item_type: 아이템 타입
            shortcuts: 단축키와 조건
                {
                    "life": {"min": 70},
                    "ele_res": {"min": 80},
                    "move_speed": {"min": 25}
                }
            max_price: 최대 가격
            ilvl_min: 최소 아이템 레벨

        Available shortcuts:
            life, mana, es, ele_res, chaos_res,
            str, dex, int, all_attr,
            attack_speed, cast_speed, crit_chance, crit_multi,
            phys_dmg, ele_dmg, spell_dmg,
            move_speed, gem_level, spell_gem, minion_gem

        Returns:
            Trade URL

        Example:
            api.search_with_shortcuts_url(
                item_type="Boots",
                shortcuts={
                    "life": {"min": 60},
                    "move_speed": {"min": 25},
                    "ele_res": {"min": 60}
                },
                max_price=100
            )
        """
        if not shortcuts:
            return None

        mapper = get_korean_stat_mapper()
        if not mapper:
            print("[ERROR] Korean stat mapper not available")
            return None

        common_stats = mapper.get_common_stats()
        stats = []

        for shortcut, conditions in shortcuts.items():
            stat_id = common_stats.get(shortcut)
            if stat_id:
                stat = {"id": stat_id, "disabled": False}
                if "min" in conditions or "max" in conditions:
                    stat["value"] = {}
                    if "min" in conditions:
                        stat["value"]["min"] = conditions["min"]
                    if "max" in conditions:
                        stat["value"]["max"] = conditions["max"]
                stats.append(stat)
            else:
                print(f"[WARNING] Unknown shortcut: {shortcut}")

        if not stats:
            print("[ERROR] No valid stats found")
            return None

        return self.get_trade_url(
            item_type=item_type,
            stats=stats,
            max_price=max_price,
            ilvl_min=ilvl_min
        )


def test_trade_search():
    """Trade API 테스트"""
    print("=" * 80)
    print("POE TRADE API TEST")
    print("=" * 80)
    print()

    api = POETradeAPI(league="Keepers")

    # 1. Trade URL 생성 테스트
    print("1. Testing Trade URL generation...")
    print("-" * 80)

    # 유니크 아이템 URL
    items_to_search = ["Mageblood", "Headhunter", "Aegis Aurora"]
    for item_name in items_to_search:
        url = api.search_unique_item_url(item_name)
        if url:
            print(f"  {item_name}: {url}")
        else:
            print(f"  {item_name}: Failed to generate URL")

    # 스탯 기반 아이템 URL
    print()
    stat_url = api.search_stat_item_url(
        item_type="Ring",
        stat_requirements=[
            {"id": "pseudo.pseudo_total_elemental_resistance", "min": 60},
            {"id": "pseudo.pseudo_total_life", "min": 50}
        ],
        max_price=30
    )
    if stat_url:
        print(f"  Resistance Ring (60+ res, 50+ life): {stat_url}")
    print()

    # 2. 저항 반지 검색
    print("2. Searching for resistance rings (max 20c)...")
    print("-" * 80)

    rings = api.search_resistance_ring(min_total_res=60, max_price=20)

    for i, item in enumerate(rings, 1):
        print(f"{i}. {item['type']}")
        print(f"   가격: {item['price_display']} (~{item['price_chaos']:.1f}c)")
        print(f"   판매자: {item['seller']} ({item['character']})")
        if item.get('trade_url'):
            print(f"   Trade URL: {item['trade_url']}")
        print()

    # 3. 6링크 검색
    print()
    print("3. Searching for 6-link body armours (max 60c)...")
    print("-" * 80)

    bodies = api.search_6link_body(max_price=60)

    for i, item in enumerate(bodies, 1):
        print(f"{i}. {item['type']}")
        print(f"   가격: {item['price_display']} (~{item['price_chaos']:.1f}c)")
        print(f"   판매자: {item['seller']} ({item['character']})")
        if item.get('trade_url'):
            print(f"   Trade URL: {item['trade_url']}")
        print()


if __name__ == '__main__':
    test_trade_search()
