# 🐍 Python Logging Rules for PathcraftAI

## ⚠️ 절대 규칙 (MUST FOLLOW)

### ❌ 절대 금지
```python
# ❌ DON'T: stdout으로 로그 출력
print("Processing data...")
print(f"[INFO] Found {count} items")
print("[ERROR] Failed to load")
```

**이유**: C#에서 stdout을 JSON으로 파싱하기 때문에, 로그가 섞이면 파싱 실패!

---

### ✅ 올바른 방법

#### **1. JSON 출력만 stdout 사용**
```python
import json

result = {"status": "success", "data": [...]}
print(json.dumps(result, ensure_ascii=False))  # ✅ OK
```

#### **2. 로그는 반드시 stderr 사용**
```python
# 방법 A: file=sys.stderr 사용
import sys
print("[INFO] Processing...", file=sys.stderr)

# 방법 B: logger 사용 (권장)
from log_manager import get_logger
logger = get_logger("MyScript")
logger.info("Processing...")
logger.error("Failed to load")
```

---

## 🔧 log_manager 사용법

### 기본 사용
```python
from log_manager import get_logger

logger = get_logger("BuildAnalyzer")

logger.info("Starting analysis...")
logger.warn("No data found, using defaults")
logger.error("Failed to connect to API")
logger.debug("Raw data: {...}")
logger.section("PHASE 1: Data Collection")
```

### 출력 예시
```
[14:23:45] [INFO] [BuildAnalyzer] Starting analysis...
[14:23:46] [WARN] [BuildAnalyzer] No data found, using defaults
[14:23:47] [ERROR] [BuildAnalyzer] Failed to connect to API
```

---

## 📋 체크리스트

새로운 Python 스크립트 작성 시:

- [ ] `from log_manager import get_logger` 임포트
- [ ] `logger = get_logger("ScriptName")` 초기화
- [ ] 모든 `print()`를 `logger.info()` 등으로 교체
- [ ] JSON 출력만 `print(json.dumps(...))`로 stdout 사용
- [ ] `file=sys.stderr` 없는 print문 제거

---

## 🚨 Pre-commit Hook

자동 검사를 위해 다음 hook 설정:

```bash
# .git/hooks/pre-commit
#!/bin/bash
python src/PathcraftAI.Parser/check_print_statements.py
```

---

## 🐛 트러블슈팅

### Q: "Additional text encountered after finished reading JSON content" 에러
**A**: Python 스크립트가 stdout으로 로그를 출력하고 있습니다.

**해결**:
1. 해당 Python 파일 열기
2. 모든 `print("...")` → `logger.info("...")` 변경
3. JSON 출력만 `print(json.dumps(...))`로 남기기

### Q: Logger import 에러
**A**: `log_manager.py`가 같은 디렉토리에 있는지 확인

```bash
cd src/PathcraftAI.Parser
ls log_manager.py
```

---

## 📚 관련 파일

- [log_manager.py](./log_manager.py) - 로거 구현
- [check_print_statements.py](./check_print_statements.py) - 자동 검사 스크립트 (생성 예정)
- [DEBUGGING_FRAMEWORK.md](../../DEBUGGING_FRAMEWORK.md) - 디버깅 가이드

---

**작성일**: 2025-11-18
**최종 업데이트**: 2025-11-18
**버전**: 1.0
