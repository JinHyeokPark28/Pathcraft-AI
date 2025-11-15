# PathcraftAI 레벨링 가이드 구조

## 조사 결과: 주요 레벨링 가이드 사이트 분석

### 1. **Maxroll.gg 방식**
```
빌드 중심 가이드:
├── Overview (빌드 평가, 영상)
├── Build Information (메커니즘)
├── Leveling (1-70 진행)
│   ├── 진행도 슬라이더 (인터랙티브)
│   ├── 패시브 포인트 할당
│   ├── 젬 획득 위치
│   ├── 레벨별 장비 권장
│   └── 마일스톤별 팁
└── Progression (70+ 엔드게임)
```

**특징:**
- 인터랙티브 슬라이더로 레벨별 진행 추적
- 빌드별 최적화된 레벨링 경로
- Seamless experience 제공

---

### 2. **PoE Vault Quick Reference 방식**
```
Act별 체크리스트:
├── Act 1 (35 단계)
├── Act 2 (단계별 진행)
├── ...
└── Act 10

각 Act마다:
1. 퀘스트 순서
2. 웨이포인트 활용
3. Quicksilver Flask 등 핵심 보상
4. 포탈 활용 팁
```

**특징:**
- 빠른 참조용 체크리스트
- 퀘스트 순서만 집중
- 장비/스킬은 별도 가이드

---

### 3. **POE Wiki Acts Guide 방식**
```
전체 캠페인 흐름:
├── 필수 vs 선택 퀘스트
├── 패시브 포인트 퀘스트 목록
├── 각 Act 주요 보상
│   ├── Quicksilver Flask (Act 1)
│   ├── Skill Point (Act 2)
│   └── All Gems (Act 3 Siosa, Act 6 Lilly)
└── 레벨링 팁
    ├── 일반 몬스터 스킵
    ├── 블루 팩만 처치
    ├── 30% MS 부츠 확보
    └── 75% 저항 맞추기
```

**특징:**
- 핵심 정보 압축
- 효율성 집중
- 일반적인 팁 (빌드 무관)

---

## PathcraftAI 레벨링 시스템 설계

### 설계 목표
1. **사용자 현재 진행도 감지** → 자동으로 다음 단계 추천
2. **빌드별 최적화** → "Lightning Arrow 레벨링"과 "Death's Oath 레벨링"은 다름
3. **빠른 참조** → Act 중간에 "다음 뭐 하지?" 즉시 답변
4. **예측적 준비** → 사용자가 Act 3라면 Act 4-5 정보 미리 로드

---

### 레벨링 데이터 구조

```json
{
  "leveling_guide_template": {
    "metadata": {
      "guide_type": "generic" | "build_specific",
      "build_name": "Lightning Arrow Deadeye" | null,
      "updated_for_patch": "3.27"
    },
    "acts": {
      "act_1": {
        "level_range": "1-12",
        "key_quests": [
          {
            "quest_name": "Enemy at the Gate",
            "step": 1,
            "location": "The Twilight Strand",
            "reward": "Choose starting skill gem",
            "reward_gems": {
              "witch": ["Freezing Pulse", "Fireball"],
              "ranger": ["Split Arrow", "Caustic Arrow"],
              "...": "..."
            },
            "tips": "Kill Hillock, take portal back to town"
          },
          {
            "quest_name": "Mercy Mission",
            "step": 5,
            "location": "The Tidal Island",
            "reward": "Quicksilver Flask (필수!)",
            "tips": "Kill Hailrake, MUST GET THIS"
          }
        ],
        "skill_progression": {
          "level_1-4": {
            "main_skill": "Starting gem",
            "links": ["Starter + Added Fire/Cold"],
            "support_priority": "Damage"
          },
          "level_8-12": {
            "main_skill": "Upgrade to 2nd skill",
            "links": ["Main + Support + Support"],
            "example_melee": "Cleave + Added Fire + Melee Phys",
            "example_spell": "Freezing Pulse + Added Cold + Controlled Destruction"
          }
        },
        "gear_checkpoints": {
          "level_1": "Any weapon with +damage",
          "level_5": "Life on gear starts to matter",
          "level_10": "Try to get 3-link"
        },
        "waypoints": ["Lioneye's Watch", "The Coast", "The Mud Flats", "The Submerged Passage", "The Ledge", "The Climb"],
        "completion_criteria": "Kill Merveil"
      },
      "act_2": {
        "level_range": "12-20",
        "key_quests": [
          {
            "quest_name": "Through Sacred Ground",
            "step": 10,
            "reward": "Skill Point (패시브 포인트)",
            "tips": "Complete Crypt Trial for skill point from Yeena"
          }
        ],
        "skill_progression": {
          "level_12-16": "4-link if possible",
          "level_16-20": "Consider switching to endgame skill"
        }
      }
    }
  }
}
```

---

### 빌드별 레벨링 최적화 예시

#### Lightning Arrow Deadeye 레벨링

```json
{
  "build_specific_leveling": {
    "build_name": "Lightning Arrow Deadeye",
    "leveling_strategy": {
      "act_1-4": {
        "skill": "Caustic Arrow + Mirage Archer",
        "reason": "Lightning Arrow는 후반 장비 필요, CA가 초반 강함",
        "links": "Caustic Arrow - Void Manipulation - Efficacy - Mirage Archer"
      },
      "act_5-7": {
        "skill": "Still Caustic Arrow",
        "upgrade": "5-link 확보, Tabula 권장"
      },
      "act_8-10": {
        "skill": "Lightning Arrow로 전환 가능",
        "condition": "괜찮은 활 + Wrath 오라",
        "links": "Lightning Arrow - Trinity - Elemental Damage - Inspiration"
      }
    },
    "key_items": {
      "level_1": "Any bow",
      "level_10": "Silverbranch (1c)",
      "level_18": "Storm Cloud (5c)",
      "level_30": "Rare bow with +elemental damage",
      "level_50": "5-link bow or Tabula"
    }
  }
}
```

#### Death's Oath 레벨링

```json
{
  "build_specific_leveling": {
    "build_name": "Death's Oath Occultist",
    "leveling_strategy": {
      "act_1-5": {
        "skill": "Bane + Despair",
        "reason": "Death's Oath는 Lvl 62 아이템, Bane으로 레벨링",
        "links": "Bane - Despair - Efficacy - Void Manipulation"
      },
      "act_6-9": {
        "skill": "Essence Drain + Contagion",
        "upgrade": "더 빠른 클리어"
      },
      "level_62+": {
        "skill": "Death's Oath 착용 가능!",
        "note": "Death Aura가 자동으로 주변 적 처치",
        "links": "Death Aura - Void - Efficacy - Swift Affliction"
      }
    }
  }
}
```

---

### 사용자 진행도 추적 시스템

```
사용자 현재 상태:
- 레벨: 25
- 사용 스킬: Caustic Arrow
- 현재 Act: 3
- 메인 퀘스트: "Sever the Right Hand" (Act 3 보스전 직전)

    ↓ 시스템 판단

1. 현재 진행도:
   ✓ Act 3 중반 (83% 완료)
   ✓ Siosa에서 모든 젬 구매 가능 (알림!)
   ✓ 다음: Dominus 보스전

2. 추천 사항:
   ✓ "Siosa에게 가서 Lightning Arrow, Trinity 젬 구매하세요"
   ✓ "Dominus 전에 저항 50% 이상 맞추세요"
   ✓ "Act 4 들어가면 Quicksilver Flask 업그레이드 가능"

3. 빌드별 추천 (Lightning Arrow 목표):
   ✓ "아직 Caustic Arrow 유지하세요 (Lvl 28-35까지)"
   ✓ "Lvl 35부터 Lightning Arrow 전환 가능"
   ✓ "Storm Cloud 활(18레벨) 장착 시 전환 추천"
```

---

### 실시간 도움 알림 예시

```
[사용자가 Act 3 Siosa 근처 진입 감지]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 Tip: 모든 젬 구매 가능!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Siosa (Library NPC)에서 모든 젬을 구매할 수 있습니다.

Lightning Arrow 빌드 권장 구매:
✓ Lightning Arrow
✓ Trinity Support
✓ Elemental Damage with Attacks
✓ Inspiration Support

지금 구매하시겠습니까?
[구매 목록 저장] [나중에]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 레벨링 가이드 사전 수집 전략

### 1. 일반 레벨링 가이드 (빌드 무관)
```bash
# POE Wiki에서 퀘스트 보상 데이터 수집
python quest_rewards_collector.py

출력:
- build_data/leveling/quest_rewards.json
- build_data/leveling/passive_point_quests.json
- build_data/leveling/act_checkpoints.json
```

### 2. 빌드별 레벨링 경로
```bash
# 인기 빌드들의 레벨링 경로 분석
python build_leveling_analyzer.py --build "Lightning Arrow Deadeye"

출력:
- build_data/leveling/lightning_arrow_leveling.json
- 스킬 전환 타이밍
- 장비 업그레이드 시기
```

### 3. 레벨링 유니크 아이템 가이드
```
주요 레벨링 유니크:
├── Wanderlust (Lvl 1, MS 부츠)
├── Goldrim (Lvl 1, 올저항 헬멧)
├── Tabula Rasa (Lvl 1, 6-link)
├── Lifesprig (Lvl 1, 주문 무기)
├── Silverbranch (Lvl 1, 활)
├── Storm Cloud (Lvl 9, 활)
└── Poet's Pen (Lvl 12, 주문 자동 발동)

가격 데이터:
- poe.ninja API에서 실시간 가격
- "1c부터 시작 가능" 같은 가이드 제공
```

---

## 구현 우선순위

### Phase 1: 기본 레벨링 데이터 (필수)
- [ ] 퀘스트 보상 데이터베이스
- [ ] 패시브 포인트 퀘스트 목록
- [ ] Act별 핵심 체크리스트
- [ ] 일반적인 레벨링 팁

### Phase 2: 빌드별 최적화
- [ ] 인기 빌드 10개 레벨링 경로
- [ ] 스킬 전환 타이밍
- [ ] 장비 업그레이드 가이드

### Phase 3: 실시간 추적 (고급)
- [ ] 사용자 진행도 감지
- [ ] 자동 추천 알림
- [ ] 예측적 데이터 로딩

---

## 다음 단계

사용자님이 원하시는 방향:

1. **퀘스트 보상 데이터 수집기** 만들기?
   - POE Wiki에서 퀘스트 보상 크롤링
   - 모든 Act의 젬 보상 정리

2. **빌드별 레벨링 경로** 분석?
   - Reddit/포럼에서 레벨링 가이드 수집
   - "Lightning Arrow는 CA로 시작" 같은 패턴 추출

3. **레벨링 템플릿** 먼저 만들기?
   - 위 JSON 구조대로 템플릿 생성
   - 나중에 데이터 채우기

어떤 방향으로 진행할까요?
