"""
Build Pattern Crawler - 빌드 전환 패턴 수집기

Reddit, 디시인사이드, GitHub에서 레벨링 → 최종 빌드 전환 패턴을 수집합니다.
"""

import json
import re
import time
import base64
import sys
import io
from datetime import datetime
from pathlib import Path
from typing import Optional
import requests
from bs4 import BeautifulSoup

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Constants
DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = DATA_DIR / "build_transition_patterns.json"

# Rate limits
REDDIT_DELAY = 1.0  # 1 request per second (60/min limit)
DCINSIDE_DELAY = 0.5
GITHUB_DELAY = 2.0  # More conservative for GitHub

# POB code pattern
POB_PATTERN = re.compile(r'(?:pastebin\.com/\w+|poe\.?b(?:in)?\.party/[\w-]+|[A-Za-z0-9+/=]{50,})')

# Common leveling skills mapping (expanded)
LEVELING_SKILLS = {
    # Brands
    "armageddon brand": ["penance brand", "storm brand", "wintertide brand", "penance brand of dissipation"],
    "storm brand": ["penance brand", "arc", "spark", "penance brand of dissipation"],
    "stormblast mine": ["icicle mine", "pyroclast mine", "arc", "ball lightning"],
    "wintertide brand": ["vortex", "cold snap"],

    # Spells - Fire
    "rolling magma": ["fireball", "flame surge", "blazing salvo", "detonate dead"],
    "flame wall": ["fireball", "righteous fire"],
    "arcanist brand": ["blazing salvo", "fireball"],
    "cremation": ["detonate dead"],

    # Spells - Cold
    "freezing pulse": ["ice nova", "cold snap", "vortex", "vaal ice nova"],
    "frostbolt": ["ice nova", "vortex"],
    "ice spear": ["ice nova"],

    # Spells - Lightning
    "arc": ["storm brand", "spark", "ball lightning", "vaal spark"],
    "spark": ["vaal spark", "arc", "ball lightning"],
    "orb of storms": ["arc", "spark", "ball lightning"],
    "storm call": ["arc"],

    # Spells - Chaos/Phys
    "essence drain": ["bane", "soulrend"],
    "blight": ["bane", "essence drain"],

    # Totems
    "holy flame totem": ["righteous fire", "flame surge", "cremation"],
    "freezing pulse totem": ["ice nova", "glacial cascade"],

    # Attacks - Melee
    "splitting steel": ["lancing steel", "shattering steel", "spectral throw"],
    "cleave": ["cyclone", "lacerate", "bladestorm"],
    "ground slam": ["earthquake", "tectonic slam", "ice crash"],
    "sunder": ["earthquake", "cyclone"],
    "sweep": ["cyclone", "bladestorm"],
    "perforate": ["lacerate", "bladestorm"],
    "double strike": ["blade flurry", "reave"],

    # Attacks - Ranged
    "spectral helix": ["lightning strike", "frost blades", "molten strike"],
    "rain of arrows": ["tornado shot", "lightning arrow", "ice shot"],
    "burning arrow": ["tornado shot", "lightning arrow"],
    "galvanic arrow": ["lightning arrow", "tornado shot"],
    "caustic arrow": ["toxic rain", "scourge arrow"],

    # Minions
    "summon raging spirit": ["summon skeletons", "raise zombie", "raise spectre"],
    "absolution": ["dominating blow", "herald of purity"],
    "summon holy relic": ["dominating blow"],
    "animate weapon": ["summon skeletons"],
}

# Final skills that typically need leveling alternatives (expanded)
FINAL_BUILD_SKILLS = [
    # Brands
    "penance brand", "penance brand of dissipation", "storm brand", "wintertide brand",
    # Fire
    "righteous fire", "fireball", "blazing salvo", "flame surge", "detonate dead",
    # Cold
    "vortex", "cold snap", "ice nova", "vaal ice nova", "glacial cascade",
    # Lightning
    "spark", "vaal spark", "arc", "ball lightning", "storm call",
    # Chaos
    "bane", "essence drain", "soulrend",
    # Bow
    "tornado shot", "lightning arrow", "ice shot", "toxic rain", "scourge arrow",
    # Melee
    "cyclone", "lacerate", "bladestorm", "earthquake", "tectonic slam", "ice crash",
    "blade flurry", "reave", "lightning strike", "frost blades", "molten strike",
    # Minions
    "summon skeletons", "raise spectre", "raise zombie", "dominating blow", "herald of purity",
    # Totems/Traps/Mines
    "icicle mine", "pyroclast mine",
]


class BuildPatternCrawler:
    """빌드 전환 패턴 수집기"""

    def __init__(self):
        self.patterns = []
        self.stats = {
            "reddit": {"posts_scanned": 0, "patterns_found": 0},
            "dcinside": {"posts_scanned": 0, "patterns_found": 0},
            "github": {"repos_scanned": 0, "patterns_found": 0},
        }
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PathcraftAI/1.0 (Build Pattern Collector)"
        })

    def save_patterns(self):
        """수집된 패턴을 JSON으로 저장"""
        # Filter out invalid patterns
        valid_patterns = []
        invalid_words = ["on popular", "guide", "build", "video", "index", "link"]

        for pattern in self.patterns:
            leveling = pattern.get("leveling_skill", "").lower()
            final = pattern.get("final_skill", "").lower()

            # Skip if leveling skill contains invalid words
            if any(word in leveling for word in invalid_words):
                continue
            # Skip if skills are the same
            if leveling == final:
                continue
            # Skip if skill name is too short
            if len(leveling) < 3 or len(final) < 3:
                continue

            valid_patterns.append(pattern)

        # Remove duplicates
        seen = set()
        unique_patterns = []
        for p in valid_patterns:
            key = (p["leveling_skill"].lower(), p["final_skill"].lower())
            if key not in seen:
                seen.add(key)
                unique_patterns.append(p)

        output = {
            "version": "1.0",
            "updated": datetime.now().isoformat(),
            "stats": self.stats,
            "total_patterns": len(unique_patterns),
            "patterns": unique_patterns
        }

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n✅ 저장 완료: {OUTPUT_FILE}")
        print(f"   총 {len(self.patterns)}개 패턴 수집")

    def extract_skills_from_text(self, text: str) -> list:
        """텍스트에서 스킬 이름 추출"""
        text_lower = text.lower()
        found_skills = []

        # Valid skill names for validation
        all_valid_skills = set()
        for leveling in LEVELING_SKILLS.keys():
            all_valid_skills.add(leveling)
        for finals in LEVELING_SKILLS.values():
            for final in finals:
                all_valid_skills.add(final)
        for skill in FINAL_BUILD_SKILLS:
            all_valid_skills.add(skill)

        # Check for leveling skills
        for leveling, finals in LEVELING_SKILLS.items():
            if leveling in text_lower:
                for final in finals:
                    if final in text_lower:
                        found_skills.append({
                            "leveling_skill": leveling.title(),
                            "final_skill": final.title()
                        })

        # Check for explicit leveling patterns with known skills only
        leveling_patterns = [
            r"level(?:ing)?\s+(?:with|as|using)\s+([\w\s]+?)(?:\s+(?:until|then|before|->))",
            r"([\w\s]+?)\s+(?:for|during|in)\s+(?:acts?|leveling)",
            r"(?:acts?|leveling).*?:\s*([\w\s]+?)(?:\s*(?:->|→|to)\s*)([\w\s]+)",
        ]

        for pattern in leveling_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if isinstance(match, tuple):
                    leveling_candidate = match[0].strip()
                    final_candidate = match[1].strip() if len(match) > 1 else None
                else:
                    leveling_candidate = match.strip()
                    final_candidate = None

                # Only add if leveling skill is in valid skills list
                if leveling_candidate in all_valid_skills:
                    # Find what final skill this might transition to
                    for final_skill in FINAL_BUILD_SKILLS:
                        if final_skill in text_lower and final_skill != leveling_candidate:
                            found_skills.append({
                                "leveling_skill": leveling_candidate.title(),
                                "final_skill": final_skill.title()
                            })
                            break

        return found_skills

    def extract_pob_code(self, text: str) -> Optional[str]:
        """텍스트에서 POB 코드 추출"""
        match = POB_PATTERN.search(text)
        if match:
            return match.group(0)
        return None

    # ==================== Reddit Crawler ====================

    def crawl_reddit(self, subreddit: str = "PathOfExileBuilds", limit: int = 100):
        """Reddit에서 빌드 가이드 수집 (OAuth 없이 JSON API 사용)"""
        print(f"\n🔍 Reddit r/{subreddit} 크롤링 시작...")

        base_url = f"https://www.reddit.com/r/{subreddit}"

        # Search queries for build guides with leveling info
        search_queries = [
            "leveling guide",
            "league starter",
            "act to maps",
            "leveling setup",
            "level with",
            "transition to",
            "armageddon brand",
            "penance brand",
            "storm brand",
            "rolling magma",
            "spectral helix",
            "lightning strike",
            "spark leveling",
            "arc leveling",
            "ground slam earthquake",
            "freezing pulse ice nova",
        ]

        posts_processed = set()

        for query in search_queries:
            try:
                # Use Reddit's JSON API
                search_url = f"{base_url}/search.json"
                params = {
                    "q": query,
                    "restrict_sr": "on",
                    "sort": "relevance",
                    "limit": 25,  # Max per query
                    "t": "all"  # All time
                }

                response = self.session.get(search_url, params=params, timeout=10)

                if response.status_code == 429:  # Rate limited
                    print(f"   ⚠️ Rate limited, waiting...")
                    time.sleep(60)
                    continue

                if response.status_code != 200:
                    print(f"   ⚠️ Error {response.status_code} for query: {query}")
                    continue

                data = response.json()
                posts = data.get("data", {}).get("children", [])

                for post in posts:
                    post_data = post.get("data", {})
                    post_id = post_data.get("id")

                    if post_id in posts_processed:
                        continue
                    posts_processed.add(post_id)

                    title = post_data.get("title", "")
                    selftext = post_data.get("selftext", "")
                    url = f"https://reddit.com{post_data.get('permalink', '')}"

                    full_text = f"{title}\n{selftext}"

                    # Extract patterns
                    skills = self.extract_skills_from_text(full_text)
                    pob_code = self.extract_pob_code(full_text)

                    for skill_pair in skills:
                        pattern = {
                            "final_skill": skill_pair["final_skill"],
                            "leveling_skill": skill_pair["leveling_skill"],
                            "class": self._extract_class(full_text),
                            "ascendancy": self._extract_ascendancy(full_text),
                            "transition_point": self._guess_transition_point(full_text),
                            "source": "reddit",
                            "url": url,
                            "pob_code": pob_code
                        }
                        self.patterns.append(pattern)
                        self.stats["reddit"]["patterns_found"] += 1

                    self.stats["reddit"]["posts_scanned"] += 1

                time.sleep(REDDIT_DELAY)

            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue

        print(f"   ✅ Reddit: {self.stats['reddit']['posts_scanned']}개 포스트 스캔, "
              f"{self.stats['reddit']['patterns_found']}개 패턴 발견")

    # ==================== DCInside Crawler ====================

    def crawl_dcinside(self, gallery_id: str = "pathofexile", limit: int = 100):
        """디시인사이드 갤러리에서 빌드 가이드 수집"""
        print(f"\n🔍 디시인사이드 {gallery_id} 갤러리 크롤링 시작...")

        # POE 마이너 갤러리 URL
        base_url = "https://gall.dcinside.com/mgallery/board/lists"

        # Search keywords
        search_keywords = ["레벨링", "액트", "가이드", "빌드", "낙인", "추천"]

        posts_processed = set()
        page = 1
        max_pages = max(1, limit // 20)  # ~20 posts per page, minimum 1

        for keyword in search_keywords[:3]:  # Limit to 3 keywords
            page = 1
            while page <= max_pages:
                try:
                    params = {
                        "id": gallery_id,
                        "s_type": "search_subject_memo",
                        "s_keyword": keyword,
                        "page": page
                    }

                    response = self.session.get(base_url, params=params, timeout=10)

                    if response.status_code != 200:
                        print(f"   ⚠️ Error {response.status_code}")
                        break

                    soup = BeautifulSoup(response.text, "html.parser")

                    # Find post links
                    posts = soup.select("tr.ub-content")

                    if not posts:
                        break

                    for post in posts:
                        try:
                            # Get post number
                            num_elem = post.select_one("td.gall_num")
                            if not num_elem:
                                continue

                            post_num = num_elem.get_text(strip=True)
                            if not post_num.isdigit():
                                continue

                            if post_num in posts_processed:
                                continue
                            posts_processed.add(post_num)

                            # Get title
                            title_elem = post.select_one("td.gall_tit a")
                            if not title_elem:
                                continue

                            title = title_elem.get_text(strip=True)
                            post_url = f"https://gall.dcinside.com/mgallery/board/view/?id={gallery_id}&no={post_num}"

                            # Fetch post content
                            time.sleep(DCINSIDE_DELAY)
                            post_response = self.session.get(post_url, timeout=10)

                            if post_response.status_code != 200:
                                continue

                            post_soup = BeautifulSoup(post_response.text, "html.parser")
                            content_elem = post_soup.select_one("div.write_div")

                            if not content_elem:
                                continue

                            content = content_elem.get_text(separator="\n", strip=True)
                            full_text = f"{title}\n{content}"

                            # Extract Korean skill patterns
                            skills = self._extract_korean_skills(full_text)
                            pob_code = self.extract_pob_code(full_text)

                            for skill_pair in skills:
                                pattern = {
                                    "final_skill": skill_pair["final_skill"],
                                    "leveling_skill": skill_pair["leveling_skill"],
                                    "class": self._extract_class(full_text),
                                    "ascendancy": self._extract_ascendancy(full_text),
                                    "transition_point": self._guess_transition_point(full_text),
                                    "source": "dcinside",
                                    "url": post_url,
                                    "pob_code": pob_code
                                }
                                self.patterns.append(pattern)
                                self.stats["dcinside"]["patterns_found"] += 1

                            self.stats["dcinside"]["posts_scanned"] += 1

                        except Exception as e:
                            continue

                    page += 1
                    time.sleep(DCINSIDE_DELAY)

                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    break

        print(f"   ✅ 디시인사이드: {self.stats['dcinside']['posts_scanned']}개 포스트 스캔, "
              f"{self.stats['dcinside']['patterns_found']}개 패턴 발견")

    def _extract_korean_skills(self, text: str) -> list:
        """한국어 텍스트에서 스킬 패턴 추출"""
        found_skills = []

        # Korean skill name mappings
        korean_skills = {
            # Brands
            "종말의 낙인": "Armageddon Brand",
            "아마겟돈 낙인": "Armageddon Brand",
            "속죄의 낙인": "Penance Brand",
            "소실속낙": "Penance Brand of Dissipation",
            "폭풍 낙인": "Storm Brand",
            "겨울 조류의 낙인": "Wintertide Brand",

            # Spells
            "구르는 마그마": "Rolling Magma",
            "얼음 창": "Freezing Pulse",
            "전기불꽃": "Arc",
            "불꽃탄": "Fireball",
            "전광석화": "Spark",
            "정의의 화염 토템": "Holy Flame Totem",
            "정화의 불꽃": "Righteous Fire",

            # Attacks
            "강철 가르기": "Splitting Steel",
            "회전베기": "Cyclone",
            "양손베기": "Cleave",
            "지면 강타": "Ground Slam",
            "지진": "Earthquake",
            "유령 나선": "Spectral Helix",
            "번개 타격": "Lightning Strike",

            # Minions
            "분노하는 영혼 소환": "Summon Raging Spirit",
            "해골 소환": "Summon Skeletons",
            "사면": "Absolution",
        }

        # Look for patterns like "액트: X, 맵: Y" or "레벨링: X -> Y"
        patterns = [
            r"액트[:\s]*([가-힣\s]+)[,\s]*(?:맵|이후)[:\s]*([가-힣\s]+)",
            r"레벨링[:\s]*([가-힣\s]+)[→\->]+\s*([가-힣\s]+)",
            r"([가-힣\s]+)으?로\s*레벨링.*?([가-힣\s]+)으?로\s*전환",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                leveling_kr, final_kr = match[0].strip(), match[1].strip()

                # Convert to English
                leveling_en = None
                final_en = None

                for kr, en in korean_skills.items():
                    if kr in leveling_kr:
                        leveling_en = en
                    if kr in final_kr:
                        final_en = en

                if leveling_en and final_en:
                    found_skills.append({
                        "leveling_skill": leveling_en,
                        "final_skill": final_en
                    })

        # Also check for direct mentions
        for kr_leveling, en_leveling in korean_skills.items():
            if kr_leveling in text:
                for kr_final, en_final in korean_skills.items():
                    if kr_final in text and kr_leveling != kr_final:
                        # Check if they appear in leveling -> final context
                        if any(word in text for word in ["레벨링", "액트", "전환", "이후"]):
                            found_skills.append({
                                "leveling_skill": en_leveling,
                                "final_skill": en_final
                            })

        # Remove duplicates
        seen = set()
        unique_skills = []
        for skill in found_skills:
            key = (skill["leveling_skill"], skill["final_skill"])
            if key not in seen:
                seen.add(key)
                unique_skills.append(skill)

        return unique_skills

    # ==================== GitHub Crawler ====================

    def crawl_github(self, limit: int = 50):
        """GitHub에서 POE 빌드 가이드 저장소 검색"""
        print(f"\n🔍 GitHub 크롤링 시작...")

        # Search for POE build repositories
        search_url = "https://api.github.com/search/repositories"

        queries = [
            "path of exile build guide",
            "poe leveling guide",
            "poe build pob",
        ]

        repos_processed = set()

        for query in queries:
            try:
                params = {
                    "q": query,
                    "sort": "updated",
                    "order": "desc",
                    "per_page": min(limit // len(queries), 30)
                }

                response = self.session.get(search_url, params=params, timeout=10)

                if response.status_code == 403:  # Rate limited
                    print(f"   ⚠️ GitHub rate limited")
                    break

                if response.status_code != 200:
                    continue

                data = response.json()
                repos = data.get("items", [])

                for repo in repos:
                    repo_name = repo.get("full_name")

                    if repo_name in repos_processed:
                        continue
                    repos_processed.add(repo_name)

                    # Get README
                    readme_url = f"https://api.github.com/repos/{repo_name}/readme"
                    time.sleep(GITHUB_DELAY)

                    readme_response = self.session.get(readme_url, timeout=10)

                    if readme_response.status_code != 200:
                        continue

                    readme_data = readme_response.json()
                    content = readme_data.get("content", "")

                    try:
                        readme_text = base64.b64decode(content).decode("utf-8")
                    except:
                        continue

                    # Extract patterns
                    skills = self.extract_skills_from_text(readme_text)
                    pob_code = self.extract_pob_code(readme_text)

                    for skill_pair in skills:
                        pattern = {
                            "final_skill": skill_pair["final_skill"],
                            "leveling_skill": skill_pair["leveling_skill"],
                            "class": self._extract_class(readme_text),
                            "ascendancy": self._extract_ascendancy(readme_text),
                            "transition_point": self._guess_transition_point(readme_text),
                            "source": "github",
                            "url": repo.get("html_url"),
                            "pob_code": pob_code
                        }
                        self.patterns.append(pattern)
                        self.stats["github"]["patterns_found"] += 1

                    self.stats["github"]["repos_scanned"] += 1

                time.sleep(GITHUB_DELAY)

            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue

        print(f"   ✅ GitHub: {self.stats['github']['repos_scanned']}개 저장소 스캔, "
              f"{self.stats['github']['patterns_found']}개 패턴 발견")

    # ==================== Helper Methods ====================

    def _extract_class(self, text: str) -> Optional[str]:
        """텍스트에서 클래스 추출"""
        classes = [
            "Marauder", "Templar", "Witch", "Duelist", "Ranger", "Shadow", "Scion"
        ]
        text_lower = text.lower()
        for cls in classes:
            if cls.lower() in text_lower:
                return cls
        return None

    def _extract_ascendancy(self, text: str) -> Optional[str]:
        """텍스트에서 전직 추출"""
        ascendancies = [
            # Marauder
            "Juggernaut", "Berserker", "Chieftain",
            # Templar
            "Inquisitor", "Hierophant", "Guardian",
            # Witch
            "Necromancer", "Elementalist", "Occultist",
            # Duelist
            "Slayer", "Gladiator", "Champion",
            # Ranger
            "Deadeye", "Raider", "Pathfinder",
            # Shadow
            "Assassin", "Trickster", "Saboteur",
            # Scion
            "Ascendant"
        ]
        text_lower = text.lower()
        for asc in ascendancies:
            if asc.lower() in text_lower:
                return asc
        return None

    def _guess_transition_point(self, text: str) -> str:
        """텍스트에서 전환 시점 추측"""
        text_lower = text.lower()

        if any(word in text_lower for word in ["4th ascendancy", "uber lab", "4차 전직"]):
            return "4th_ascendancy"
        elif any(word in text_lower for word in ["maps", "mapping", "맵", "맵핑"]):
            return "maps_entry"
        elif any(word in text_lower for word in ["act 10", "act10", "10막"]):
            return "act_complete"
        elif any(word in text_lower for word in ["level 70", "level 80", "70레벨", "80레벨"]):
            return "specific_level"

        return "maps_entry"  # Default

    def run_all(self, reddit_limit: int = 100, dcinside_limit: int = 50, github_limit: int = 30):
        """모든 크롤러 실행"""
        print("=" * 50)
        print("빌드 전환 패턴 수집기 시작")
        print("=" * 50)

        # Run crawlers
        self.crawl_reddit(limit=reddit_limit)
        self.crawl_dcinside(limit=dcinside_limit)
        self.crawl_github(limit=github_limit)

        # Save results
        self.save_patterns()

        # Print summary
        print("\n" + "=" * 50)
        print("수집 결과 요약")
        print("=" * 50)
        print(f"Reddit: {self.stats['reddit']['posts_scanned']}개 스캔 → "
              f"{self.stats['reddit']['patterns_found']}개 패턴")
        print(f"디시인사이드: {self.stats['dcinside']['posts_scanned']}개 스캔 → "
              f"{self.stats['dcinside']['patterns_found']}개 패턴")
        print(f"GitHub: {self.stats['github']['repos_scanned']}개 스캔 → "
              f"{self.stats['github']['patterns_found']}개 패턴")
        print(f"\n총 {len(self.patterns)}개 패턴 수집 완료")

        return self.patterns


if __name__ == "__main__":
    crawler = BuildPatternCrawler()
    patterns = crawler.run_all(
        reddit_limit=100,
        dcinside_limit=50,
        github_limit=30
    )
