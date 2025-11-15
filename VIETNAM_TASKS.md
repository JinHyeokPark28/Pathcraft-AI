# 베트남에서 할 작업 목록

**작성일**: 2025-01-16
**예상 작업 기간**: 3-5일
**우선순위**: 🔥 높음 / ⚡ 중간 / 💡 낮음

---

## 🚀 시작하기 전에

### 1. 환경 설정 확인
```bash
# 프로젝트 폴더로 이동
cd C:\Users\vnddn\OneDrive\Desktop\프로그래밍자료\Unity\PathcraftAI

# Git 최신 상태 확인
git pull

# Python 가상환경 활성화
cd src/PathcraftAI.Parser
.venv/Scripts/activate

# 필요한 패키지 확인
pip list | findstr "requests pobapi anthropic"
```

### 2. 데이터 확인
```bash
# POE.Ninja 데이터 있는지 확인
dir game_data

# 33,831개 아이템 있어야 함
.venv/Scripts/python.exe poe_ninja_fetcher.py --stats
```

### 3. OAuth 토큰 확인
```bash
# 토큰 파일 존재 확인
dir poe_token.json

# 토큰 유효성 테스트
.venv/Scripts/python.exe test_oauth.py
```

---

## 🔥 최우선 작업 (Day 1)

### Task 1: POB DPS 계산 통합
**목표**: POB 내부 계산식으로 실제 DPS, Life, ES 수치 추출

**현재 문제**:
- 지금은 POB에서 스킬, 아이템만 읽음
- DPS, 방어 수치 계산 안 함

**해야 할 일**:
1. POB XML에서 `<Build>` 섹션 Calcs 데이터 추출
2. Player stats 파싱 (TotalDPS, Life, ES, Armour 등)
3. `smart_build_analyzer.py`에 통합

**참고 코드**:
```python
# POB XML 구조 예시
build = root.find('.//Build')
if build is not None:
    # Player stats
    player = build.find('.//PlayerStat')
    if player is not None:
        total_dps = player.get('TotalDPS', 0)
        life = player.get('Life', 0)
        es = player.get('EnergyShield', 0)
```

**테스트**:
```bash
.venv/Scripts/python.exe smart_build_analyzer.py
# 출력에 DPS, Life, ES 표시되어야 함
```

**예상 시간**: 2-3시간

---

### Task 2: 현재 캐릭터 vs POB 비교 대시보드
**목표**: 현재 상태와 목표 빌드를 한눈에 비교

**출력 예시**:
```
=================================================
CURRENT vs TARGET COMPARISON
=================================================
                Current    Target    Gap
DPS:            15,000    85,000   -70,000 ⚠️
Life:            2,800     4,500    -1,700 ⚠️
ES:                  0         0         0 ✓
Fire Res:           45%       75%      -30% ⚠️
Cold Res:           75%       75%        0% ✓
Lightning Res:      60%       75%      -15% ⚠️

Priority Upgrades:
  1. Get 6-link body armour (+50,000 DPS)
  2. Cap Fire Resistance (ring/belt upgrade)
  3. Add Life nodes (+1,000 HP)
```

**구현**:
1. POB 수치 파싱
2. 현재 캐릭터 수치 API로 가져오기
3. 비교 및 우선순위 계산
4. Markdown 테이블 출력

**파일**: `compare_build.py` (신규 생성)

**예상 시간**: 2-3시간

---

## ⚡ 고우선순위 (Day 2)

### Task 3: UI에 빌드 비교 표시
**목표**: WPF UI에 Current vs Target 비교 표시

**작업**:
1. `MainWindow.xaml`에 비교 섹션 추가
2. C#에서 Python 스크립트 호출
3. JSON 결과 파싱 및 UI 업데이트

**XAML 추가 위치**: "Your Current Build" 섹션 아래

**예시 UI**:
```xml
<Border x:Name="BuildComparisonSection" Grid.Row="2">
    <DataGrid x:Name="ComparisonGrid" ItemsSource="{Binding Comparison}">
        <DataGrid.Columns>
            <DataGridTextColumn Header="Stat" Binding="{Binding Name}"/>
            <DataGridTextColumn Header="Current" Binding="{Binding Current}"/>
            <DataGridTextColumn Header="Target" Binding="{Binding Target}"/>
            <DataGridTextColumn Header="Gap" Binding="{Binding Gap}"/>
        </DataGrid.Columns>
    </DataGrid>
</Border>
```

**예상 시간**: 3-4시간

---

### Task 4: YouTube API 연동 및 빌드 데이터 수집
**목표**: YouTube에서 인기 빌드 영상 자동 수집

**준비 사항**:
1. YouTube API 키 발급
   - https://console.cloud.google.com/
   - YouTube Data API v3 활성화
   - API 키 생성

2. 환경변수 설정
   ```bash
   # .env 파일 생성
   echo YOUTUBE_API_KEY=your_api_key_here > .env
   ```

**실행**:
```bash
.venv/Scripts/python.exe popular_build_collector.py --league Keepers --version 3.27
```

**확인**:
```bash
dir build_data
# popular_builds_Keepers.json 파일 생성되어야 함
```

**예상 시간**: 1-2시간 (API 키 발급 포함)

---

## 💡 중간 우선순위 (Day 3-4)

### Task 5: 업그레이드 경로 시각화
**목표**: 단계별 업그레이드 순서 추천

**예시**:
```
=================================================
UPGRADE PATH (Budget: 100 chaos)
=================================================

Step 1: Cap Resistances (Cost: 15c)
  → Buy ring with Fire Res + Life
  → Recommended: Vermillion Ring (ilvl 75+)
  → Market price: ~5-10c

Step 2: Get 6-Link (Cost: 50c)
  → Buy 6-link rare body armour
  → Required stats: Life, Resistances
  → Alternative: Use Tabula Rasa (1c) temporarily

Step 3: Upgrade Weapon (Cost: 30c)
  → Buy wand with:
    - High Attack Speed (1.5+)
    - Crit Chance (8%+)
    - Added Elemental Damage
  → Market listings: [link]
```

**구현**:
1. 가격 예산 기반 업그레이드 계산
2. 우선순위 알고리즘 (저항 > DPS > 방어)
3. POE.Ninja에서 실제 거래 가능한 아이템 링크

**파일**: `upgrade_path.py` (신규)

**예상 시간**: 3-4시간

---

### Task 6: 패시브 트리 추천 강화
**목표**: 다음 찍어야 할 노드 순서 제시

**현재 문제**:
- "29개 포인트 부족" 정도만 알려줌
- 어떤 노드부터 찍어야 하는지 모름

**개선**:
1. POB 패시브 순서 분석
2. 현재 트리와 차이점 계산
3. Lv69→94 레벨업 시뮬레이션
4. 단계별 추천

**출력 예시**:
```
=================================================
PASSIVE TREE ROADMAP (Lv69 → Lv94)
=================================================

Level 70-75 (6 points):
  ✓ Prioritize: Life nodes near Witch start
  → Recommended path: Coordination → Blood Siphon → Written in Blood
  → Gain: +150 Life, +10% Spell Damage

Level 76-80 (5 points):
  ✓ Prioritize: Crit Multi clusters
  → Recommended path: Throatseeker → Assassination
  → Gain: +60% Crit Multi

Level 81-85 (5 points):
  ✓ Add: Jewel socket (for Cluster Jewel)
  → Location: Near Witch start
  → Cost: 3 points
```

**예상 시간**: 4-5시간

---

### Task 7: 자동 업데이트 스케줄러
**목표**: 매일 자동으로 POE.Ninja 데이터 갱신

**방법 1**: Windows Task Scheduler
```batch
@echo off
cd C:\Users\vnddn\OneDrive\Desktop\프로그래밍자료\Unity\PathcraftAI\src\PathcraftAI.Parser
.venv\Scripts\python.exe poe_ninja_fetcher.py --collect --league Keepers
```

**방법 2**: Python 스케줄러
```python
import schedule
import time

def update_data():
    # POE.Ninja 데이터 수집
    pass

schedule.every().day.at("03:00").do(update_data)

while True:
    schedule.run_pending()
    time.sleep(3600)
```

**예상 시간**: 1-2시간

---

## 🎨 UI/UX 개선 (Day 4-5)

### Task 8: 빌드 카드 UI 개선
**목표**: 추천 빌드를 더 보기 좋게 표시

**추가 요소**:
- [ ] POE.Ninja 아이템 아이콘 표시
- [ ] YouTube 썸네일 표시
- [ ] 빌드 가격대 태그 (Budget/Mid-tier/High-end)
- [ ] POB 링크 버튼
- [ ] 클릭 시 YouTube 영상 재생

**XAML 예시**:
```xml
<Border Style="{StaticResource BuildCard}">
    <Grid>
        <Image Source="{Binding Thumbnail}" Width="200"/>
        <TextBlock Text="{Binding BuildName}" FontSize="16"/>
        <TextBlock Text="{Binding Price}" Foreground="Gold"/>
        <Button Content="Open POB" Click="OpenPOB_Click"/>
        <Button Content="Watch Video" Click="WatchVideo_Click"/>
    </Grid>
</Border>
```

**예상 시간**: 3-4시간

---

### Task 9: 에러 핸들링 개선
**목표**: 사용자 친화적인 에러 메시지

**개선 사항**:
1. Rate Limit 에러 → "잠시 후 다시 시도해주세요 (30초 대기)"
2. Privacy 설정 에러 → "POE 설정에서 캐릭터 공개 설정을 확인해주세요"
3. 네트워크 에러 → "인터넷 연결을 확인해주세요"
4. API 키 없음 → "YouTube API 키를 설정해주세요"

**구현**:
```csharp
// MainWindow.xaml.cs
private void ShowFriendlyError(Exception ex)
{
    string message = ex.Message;

    if (ex is HttpRequestException && message.Contains("429"))
    {
        message = "POE API 요청 제한에 도달했습니다.\n30초 후 다시 시도해주세요.";
    }
    else if (message.Contains("privacy"))
    {
        message = "캐릭터 아이템이 비공개 상태입니다.\n\nPOE 웹사이트에서:\n1. My Account → Privacy 설정\n2. 'Hide characters' 체크 해제\n3. 저장 후 다시 시도";
    }

    MessageBox.Show(message, "알림", MessageBoxButton.OK, MessageBoxImage.Information);
}
```

**예상 시간**: 2-3시간

---

## 🧪 테스트 및 검증 (Day 5)

### Task 10: 통합 테스트
**체크리스트**:
- [ ] OAuth 로그인 → 캐릭터 목록 로드
- [ ] 빌드 분석 → 정확한 아이템/스킬 표시
- [ ] POB 비교 → DPS/Life/저항 수치 정확
- [ ] 가격 계산 → POE.Ninja 최신 데이터 반영
- [ ] 판테온 추천 → 키스톤 고려
- [ ] UI 반응성 → 3초 이내 로딩

**테스트 시나리오**:
1. 앱 실행 → "Connect POE Account" 클릭
2. OAuth 인증 완료
3. "Refresh Recommendations" 클릭
4. "Your Current Build" 섹션 확인
5. "Build Comparison" 섹션 확인
6. 추천 빌드 클릭 → YouTube 영상 재생

**예상 시간**: 2-3시간

---

## 📝 문서화 (지속적)

### Task 11: 사용자 가이드 작성
**파일**: `Docs/USER_GUIDE.md`

**내용**:
1. 설치 및 설정
2. POE 계정 연동 방법
3. 빌드 분석 사용법
4. 추천 시스템 이해하기
5. 트러블슈팅

### Task 12: 개발자 문서 업데이트
**파일**: `Docs/DEVELOPER.md`

**내용**:
1. 프로젝트 구조
2. API 문서
3. 빌드 및 배포
4. 코드 스타일 가이드

---

## 🐛 알려진 이슈 해결

### Issue 1: Currency 데이터 없음
**문제**: POE.Ninja에서 Keepers 리그 Currency 데이터 없음

**해결 방법**:
1. Standard 리그 데이터 사용
2. 또는 수동으로 currency.json 생성
3. Divine/Exalt/Chaos 환율만이라도 하드코딩

### Issue 2: Rate Limit 429
**문제**: POE API 요청 너무 많이 하면 차단

**해결 방법**:
1. 요청 간 최소 2초 대기
2. 캐싱 시스템 구현
3. 에러 발생 시 exponential backoff

### Issue 3: POB 계산 부정확
**문제**: POB XML에 일부 수치 없음

**해결 방법**:
1. POB Community Fork 사용
2. 직접 계산 로직 구현
3. 근사치 사용 (예: DPS 범위 표시)

---

## 🎯 마일스톤

### Milestone 1: 빌드 비교 시스템 완성 (Day 1-2)
- [x] POB DPS 계산
- [ ] Current vs Target 비교
- [ ] UI 통합

### Milestone 2: 데이터 수집 자동화 (Day 2-3)
- [x] POE.Ninja 수집
- [ ] YouTube API 연동
- [ ] 자동 업데이트 스케줄러

### Milestone 3: UX 개선 (Day 3-5)
- [ ] 업그레이드 경로
- [ ] 패시브 트리 가이드
- [ ] 에러 핸들링
- [ ] 빌드 카드 UI

### Milestone 4: 테스트 및 배포 준비 (Day 5)
- [ ] 통합 테스트
- [ ] 문서화
- [ ] 버그 수정

---

## 📞 긴급 상황 대응

### Git 문제
```bash
# 변경사항 백업
git stash

# 최신 코드 받기
git pull

# 백업 복원
git stash pop
```

### Python 환경 문제
```bash
# 가상환경 재생성
cd src/PathcraftAI.Parser
rm -rf .venv
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```

### OAuth 토큰 만료
```bash
# 토큰 재발급
rm poe_token.json
.venv/Scripts/python.exe test_oauth.py
```

---

## 💾 백업 권장사항

### 중요 파일
- `poe_token.json` (OAuth 토큰)
- `game_data/` (POE.Ninja 데이터)
- `build_data/` (YouTube 빌드 데이터)
- `.env` (API 키)

### 백업 명령
```bash
# 전체 백업
git add .
git commit -m "backup: Before Vietnam trip"
git push

# 데이터 폴더 백업 (Git에 안 올림)
tar -czf game_data_backup.tar.gz game_data/
```

---

## 📊 작업 시간 예상

| 작업 | 예상 시간 | 우선순위 |
|------|----------|----------|
| POB DPS 계산 | 2-3h | 🔥 |
| 빌드 비교 대시보드 | 2-3h | 🔥 |
| UI 비교 섹션 | 3-4h | 🔥 |
| YouTube API | 1-2h | ⚡ |
| 업그레이드 경로 | 3-4h | ⚡ |
| 패시브 트리 추천 | 4-5h | ⚡ |
| 자동 업데이트 | 1-2h | ⚡ |
| UI 개선 | 3-4h | 💡 |
| 에러 핸들링 | 2-3h | 💡 |
| 테스트 | 2-3h | 💡 |

**총 예상 시간**: 23-33시간 (3-5일)

---

## 🎉 완료 기준

### 최소 요구사항 (MVP)
- [ ] POB와 현재 빌드 비교 표시
- [ ] 실시간 가격 기반 업그레이드 추천
- [ ] 키스톤 고려한 판테온 추천
- [ ] YouTube 빌드 영상 연동

### 이상적 목표
- [ ] 단계별 업그레이드 경로
- [ ] 패시브 트리 로드맵
- [ ] 자동 데이터 갱신
- [ ] 완성도 높은 UI/UX

---

## 📚 참고 자료

### 코드 예제
- `smart_build_analyzer.py` - 스마트 분석기 참고
- `poe_oauth.py` - API 호출 패턴
- `MainWindow.xaml.cs` - UI 통합 방법

### 외부 문서
- [POB Community Fork](https://github.com/PathOfBuildingCommunity/PathOfBuilding)
- [POE API Docs](https://www.pathofexile.com/developer/docs)
- [.NET MAUI WPF](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/)

---

**베트남에서 화이팅! 🇻🇳**

문제 생기면:
1. `PROGRESS_SUMMARY.md` 참고
2. Git 로그 확인
3. 백업 복원
4. Claude에게 물어보기

**다음 커밋 시**:
```bash
git add .
git commit -m "feat: [작업 내용]"
git push
```
