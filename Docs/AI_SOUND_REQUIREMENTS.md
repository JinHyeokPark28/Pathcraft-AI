# PathcraftAI - AI 사운드 요구사항

> **작성일:** 2025-11-23
> **상태:** 대기 (추후 작업)

---

## 1. 개요

현재 filter_generator.py에서 `PlayAlertSound 1-16` (POE 기본 사운드)만 사용 중입니다.
커스텀 사운드 (`CustomAlertSound`)를 사용하려면 사운드 파일이 필요합니다.

**현재 상태:**
- 커스텀 사운드 코드는 비활성화 상태 (`if False`)
- POE 기본 사운드만 사용 중

---

## 2. 필요한 사운드 목록

### 2.1 빌드 아이템 사운드 (최고 우선순위)

| 파일명 | 용도 | 재생 시점 | 우선순위 |
|--------|------|-----------|----------|
| `build_unique.mp3` | 빌드에서 사용 중인 유니크 아이템 | 정확히 일치하는 유니크 드롭 | 높음 |
| `build_base.mp3` | 빌드 베이스 타입 + 인플루언스 | 빌드용 레어 베이스 드롭 | 높음 |
| `build_upgrade.mp3` | 업그레이드 가능한 아이템 | ilvl 82+ 빌드 베이스 | 중간 |

### 2.2 가치 기반 사운드

| 파일명 | 용도 | 재생 시점 | 우선순위 |
|--------|------|-----------|----------|
| `high_value.mp3` | 고가 유니크 (100+ chaos) | poe.ninja 기준 고가 드롭 | 높음 |
| `mid_value.mp3` | 중가 유니크 (20-100 chaos) | poe.ninja 기준 중가 드롭 | 중간 |
| `currency_top.mp3` | 최상위 커런시 | Divine, Mirror, Exalted 드롭 | 높음 |

### 2.3 일반 알림 사운드

| 파일명 | 용도 | 재생 시점 | 우선순위 |
|--------|------|-----------|----------|
| `six_link.mp3` | 6링크 아이템 | 6링크 드롭 | 높음 |
| `influenced.mp3` | 인플루언스 레어 | Shaper/Elder 등 드롭 | 중간 |
| `gem_quality.mp3` | 품질 젬 | 20+ 품질 젬 드롭 | 낮음 |

---

## 3. 사운드 사양

### 3.1 파일 형식
- **포맷:** MP3 또는 WAV
- **길이:** 0.5초 ~ 2초 (짧고 명확하게)
- **샘플레이트:** 44.1kHz
- **비트레이트:** 128kbps 이상

### 3.2 사운드 특성

| 우선순위 | 특성 | 예시 |
|----------|------|------|
| 높음 | 눈에 띄는, 독특한 | 차임벨, 팡파르 |
| 중간 | 명확하지만 덜 급한 | 부드러운 딩동 |
| 낮음 | 미묘한, 방해되지 않는 | 가벼운 클릭 |

### 3.3 권장 사항
- POE 기존 사운드와 구별 가능해야 함
- 반복 재생 시 피로하지 않아야 함
- 게임 사운드와 잘 어울려야 함

---

## 4. 구현 계획

### 4.1 파일 구조
```
src/PathcraftAI.Parser/sounds/
├── build_unique.mp3
├── build_base.mp3
├── build_upgrade.mp3
├── high_value.mp3
├── mid_value.mp3
├── currency_top.mp3
├── six_link.mp3
├── influenced.mp3
└── gem_quality.mp3
```

### 4.2 filter_generator.py 수정

현재 (비활성화):
```python
"    CustomAlertSound \"sounds\\build_item.mp3\"\n" if False else "",
```

활성화 시:
```python
"    CustomAlertSound \"sounds\\build_unique.mp3\"\n",
```

### 4.3 설치 경로
사용자가 필터 사용 시 사운드 파일도 함께 복사해야 함:
```
%userprofile%/Documents/My Games/Path of Exile/sounds/
```

---

## 5. 대안: POE 기본 사운드 매핑

커스텀 사운드 없이 사용할 경우 현재 매핑:

| 용도 | POE 사운드 | 설명 |
|------|------------|------|
| 빌드 유니크 | `PlayAlertSound 1 300` | 가장 눈에 띄는 사운드 |
| 고가 아이템 | `PlayAlertSound 6 300` | 특별한 느낌 |
| 인플루언스 | `PlayAlertSound 2 300` | 중요 알림 |
| 일반 | `PlayAlertSound 3-5` | 보통 알림 |

---

## 6. 작업 체크리스트

- [ ] 사운드 디자인/제작 (9개 파일)
- [ ] sounds 폴더 생성
- [ ] filter_generator.py 수정 (CustomAlertSound 활성화)
- [ ] 설치 가이드 문서 작성
- [ ] 테스트 (POE에서 실제 재생 확인)

---

## 7. 참고 자료

- [POE Wiki - Item Filter Guide](https://www.poewiki.net/wiki/Guide:Item_filter_guide)
- [FilterBlade Sound Pack](https://www.filterblade.xyz/)
- [NeverSink Filter Sounds](https://github.com/NeverSinkDev/NeverSink-Filter)

---

**Owner:** Shovel
**다음 리뷰:** Sprint Planning 시
