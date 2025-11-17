# 🐛 Debugging Framework - 2시간 룰

## 📌 언제 사용하나?
- **2시간 이상** 같은 버그에 막혔을 때
- 여러 번 시도했지만 해결이 안 될 때
- 원인을 모르겠을 때

---

## 🚨 핵심 규칙

### ❌ 절대 금지
1. **Phase 2 완료 전까지 코드 수정 금지**
   - 증상만 확인하고 원인 파악 먼저
   - 추측으로 코드 변경하지 말 것

2. **Git 커밋 없이 파일 삭제 금지**
   - 삭제 전 반드시 `git status` 확인
   - 변경사항 있으면 커밋 먼저

### ✅ 필수 사항
1. **각 Phase 완료 시 시간 기록**
   - 시작 시간, 종료 시간 기록
   - 소요 시간 계산

2. **Phase 6 회고 반드시 작성**
   - 무엇이 문제였나?
   - 왜 2시간이나 걸렸나?
   - 다음엔 어떻게 방지할까?

---

## 📋 6 Phase Debugging Process

### Phase 1: 증상 수집 (Symptom Collection) ⏱️ 10분
**목표**: 문제를 정확히 파악하고 재현 가능한지 확인

**체크리스트**:
- [ ] 에러 메시지 전체 복사
- [ ] 스택 트레이스 확인
- [ ] 재현 단계 기록 (1, 2, 3...)
- [ ] 예상 동작 vs 실제 동작 비교
- [ ] 스크린샷/비디오 캡처

**예시**:
```
증상: 앱이 "Connect POE Account" 클릭 시 크래시
에러: NullReferenceException at MainWindow.xaml.cs:245
재현: 100% (매번 발생)
예상: OAuth 창이 열림
실제: 앱이 종료됨
```

**⏱️ 시작 시간**: ________
**⏱️ 종료 시간**: ________

---

### Phase 2: 원인 가설 (Root Cause Hypothesis) ⏱️ 15분
**목표**: 최소 3개 이상의 가능한 원인 나열

**⚠️ 코드 수정 금지! 아직 추측 단계입니다.**

**가설 템플릿**:
1. **가설 A**: [원인 설명]
   - 확률: ⭐⭐⭐⭐⭐ (높음/중간/낮음)
   - 검증 방법: [어떻게 확인?]

2. **가설 B**: [원인 설명]
   - 확률: ⭐⭐⭐
   - 검증 방법: [어떻게 확인?]

3. **가설 C**: [원인 설명]
   - 확률: ⭐⭐
   - 검증 방법: [어떻게 확인?]

**예시**:
```
가설 A: OAuthHandler가 null
  - 확률: ⭐⭐⭐⭐⭐
  - 검증: Debug.WriteLine으로 null 체크

가설 B: 환경변수 누락
  - 확률: ⭐⭐⭐
  - 검증: .env 파일 확인

가설 C: 라이브러리 버전 충돌
  - 확률: ⭐⭐
  - 검증: packages.config 확인
```

**⏱️ 시작 시간**: ________
**⏱️ 종료 시간**: ________

---

### Phase 3: 최소 재현 (Minimal Reproduction) ⏱️ 20분
**목표**: 버그를 가장 간단하게 재현하는 코드 작성

**체크리스트**:
- [ ] 불필요한 코드 제거
- [ ] 의존성 최소화
- [ ] 테스트 프로젝트 생성 (필요 시)
- [ ] 격리된 환경에서 재현 확인

**예시**:
```csharp
// BEFORE: 복잡한 전체 앱
MainWindow app = new MainWindow();
app.Show();

// AFTER: 최소 재현 코드
var handler = new OAuthHandler();
Debug.WriteLine($"Handler is null? {handler == null}");
handler.Authenticate(); // 여기서 크래시
```

**⏱️ 시작 시간**: ________
**⏱️ 종료 시간**: ________

---

### Phase 4: 원인 검증 (Verification) ⏱️ 15분
**목표**: Phase 2의 가설을 하나씩 검증

**방법**:
1. **로깅**: `Debug.WriteLine()`, `Console.WriteLine()`
2. **브레이크포인트**: Visual Studio Debugger
3. **파일 확인**: 설정 파일, JSON, .env
4. **프로세스 확인**: Task Manager, `ps aux`

**검증 결과**:
- [x] 가설 A: ✅ 맞음 - OAuthHandler가 실제로 null
- [ ] 가설 B: ❌ 틀림 - .env 파일 정상
- [ ] 가설 C: ⏭️ 검증 불필요 (A가 맞아서)

**⏱️ 시작 시간**: ________
**⏱️ 종료 시간**: ________

---

### Phase 5: 수정 및 테스트 (Fix & Test) ⏱️ 30분
**목표**: 검증된 원인을 수정하고 재현 안 되는지 확인

**수정 체크리스트**:
- [ ] 최소한의 변경 (1 file, 1 function)
- [ ] 주석으로 변경 이유 설명
- [ ] 기존 기능 영향 확인
- [ ] 최소 3번 재현 테스트
- [ ] Edge case 테스트

**수정 예시**:
```csharp
// BEFORE
public void ConnectAccount_Click(object sender, EventArgs e)
{
    _oauthHandler.Authenticate(); // NullReferenceException
}

// AFTER
public void ConnectAccount_Click(object sender, EventArgs e)
{
    // Fix: Initialize OAuthHandler if null (Issue #42)
    if (_oauthHandler == null)
    {
        _oauthHandler = new OAuthHandler();
    }

    _oauthHandler.Authenticate();
}
```

**테스트 결과**:
- [ ] 버그 재현 안 됨 (3/3)
- [ ] 기존 기능 정상 동작
- [ ] Edge case 통과

**⏱️ 시작 시간**: ________
**⏱️ 종료 시간**: ________

---

### Phase 6: 회고 및 예방 (Retrospective) ⏱️ 10분
**⚠️ 이 단계를 건너뛰지 마세요!**

**회고 질문**:
1. **무엇이 문제였나?**
   - 답: ______________________________________

2. **왜 2시간이나 걸렸나?**
   - 답: ______________________________________

3. **어느 Phase에서 시간을 가장 많이 썼나?**
   - 답: ______________________________________

4. **다음엔 어떻게 방지할까?**
   - 답: ______________________________________

5. **비슷한 버그가 또 생길 수 있나?**
   - 답: ______________________________________

**예방 조치**:
- [ ] Unit test 추가
- [ ] Null check 추가
- [ ] 문서 업데이트
- [ ] Linter rule 추가
- [ ] Code review 요청

**⏱️ 시작 시간**: ________
**⏱️ 종료 시간**: ________

---

## 🔍 자주 쓰는 디버깅 도구

### C# / WPF
```bash
# Visual Studio Debugger
F9: 브레이크포인트 설정
F5: 디버그 시작
F10: Step Over
F11: Step Into

# 콘솔 로그
Debug.WriteLine($"Value: {myVar}");
Console.WriteLine($"Error: {ex.Message}");

# 예외 중단
Debug > Windows > Exception Settings
```

### Python
```bash
# Print 디버깅
print(f"DEBUG: {variable}")

# PDB 디버거
import pdb; pdb.set_trace()

# 스택 트레이스
import traceback
traceback.print_exc()
```

### Git 안전 작업
```bash
# 변경사항 확인
git status
git diff

# 임시 저장
git stash

# 복원
git stash pop

# 파일 되돌리기
git restore <file>
```

---

## 📊 시간 추적 템플릿

```
버그 발견: 2025-11-18 14:30
Phase 1 (증상): 14:30 - 14:40 (10분)
Phase 2 (가설): 14:40 - 14:55 (15분)
Phase 3 (재현): 14:55 - 15:15 (20분)
Phase 4 (검증): 15:15 - 15:30 (15분)
Phase 5 (수정): 15:30 - 16:00 (30분)
Phase 6 (회고): 16:00 - 16:10 (10분)
총 소요 시간: 1시간 40분
```

---

## 🚀 빠른 체크리스트

막혔을 때 순서대로 확인:

1. [ ] 에러 메시지 전체를 읽었나?
2. [ ] 스택 트레이스를 확인했나?
3. [ ] 최근 변경사항이 뭔가?
4. [ ] 재현이 100% 가능한가?
5. [ ] 다른 환경에서도 재현되나?
6. [ ] 구글에 에러 메시지 검색했나?
7. [ ] 관련 이슈가 GitHub에 있나?
8. [ ] 로그 파일을 확인했나?
9. [ ] 설정 파일이 올바른가?
10. [ ] 의존성이 설치됐나?

---

## 💡 디버깅 원칙

### DO ✅
- 작은 단위로 테스트
- 로그를 많이 남기기
- 가설을 여러 개 세우기
- 최소 재현 코드 작성
- 회고 작성하기

### DON'T ❌
- 추측으로 코드 수정
- 여러 곳 동시에 변경
- 테스트 없이 커밋
- Phase 건너뛰기
- 회고 생략하기

---

## 📚 참고 자료

- [The Debugging Manifesto](https://jvns.ca/blog/2022/12/08/a-debugging-manifesto/)
- [Rubber Duck Debugging](https://en.wikipedia.org/wiki/Rubber_duck_debugging)
- [How to Debug Small Programs](https://ericlippert.com/2014/03/05/how-to-debug-small-programs/)

---

## 🤖 Claude Code에게

**2시간 이상 막혔을 때 자동 제안**:

```
⚠️ 2시간 이상 같은 버그에 막혔습니다.
DEBUGGING_FRAMEWORK.md를 사용해볼까요?

현재 상황:
- 버그: [증상]
- 시도한 방법: [시도 1, 2, 3]
- 소요 시간: 2시간 15분

Phase 1 (증상 수집)부터 시작하겠습니다.
```

---

**작성일**: 2025-11-18
**마지막 업데이트**: 2025-11-18
**버전**: 1.0
