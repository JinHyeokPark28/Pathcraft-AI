# PathcraftAI Electron Module

POE Trade 가격 조회를 위한 Electron 서브프로세스 모듈입니다.

## 특징

- **Lazy Loading**: 필요할 때만 프로세스 시작
- **메모리 모니터링**: 800MB 임계치 초과 시 자동 정리/종료
- **자동 종료**: 5분 미사용 시 자동 종료
- **3단계 캐시**: Hot/Warm/Cold 캐시 시스템
- **JSON-RPC IPC**: TCP 기반 통신 (port 47851)

## 설치

```bash
cd src/PathcraftAI.Electron
npm install
```

## 실행

### 독립 실행 (개발용)

```bash
npm start
```

### C# 앱에서 실행

`ElectronService.cs`를 통해 자동으로 관리됩니다.

```csharp
var electronService = new ElectronService();

// Electron 시작 (Lazy Loading)
await electronService.StartAsync();

// Trade 창 표시
await electronService.ShowWindowAsync();

// 아이템 검색
await electronService.SearchAsync("Keepers", itemName: "Headhunter");

// 메모리 사용량 확인
var (heap, total) = await electronService.GetMemoryUsageAsync() ?? (0, 0);
Console.WriteLine($"Memory: {total}MB");

// 종료
await electronService.ShutdownAsync();
```

## IPC API

### 연결

- **Port**: 47851
- **Protocol**: JSON-RPC 2.0 over TCP
- **Delimiter**: `\n` (newline)

### 메서드

| 메서드 | 파라미터 | 설명 |
|--------|----------|------|
| `ping` | - | 연결 상태 확인 |
| `show` | - | 창 표시 |
| `hide` | - | 창 숨기기 |
| `navigate` | `{ url }` | URL로 이동 |
| `search` | `{ league, itemName, queryId, ... }` | 아이템 검색 |
| `getMemory` | - | 메모리 사용량 조회 |
| `getCache` | - | 캐시 상태 조회 |
| `clearCache` | - | 캐시 초기화 |
| `setCache` | `{ key, value }` | 캐시 항목 설정 |
| `getCacheItem` | `{ key }` | 캐시 항목 조회 |
| `setLeague` | `{ league }` | 리그 설정 |
| `shutdown` | - | 모듈 종료 |

### 예시

**요청:**
```json
{"jsonrpc":"2.0","id":1,"method":"search","params":{"league":"Keepers","itemName":"Headhunter"}}
```

**응답:**
```json
{"jsonrpc":"2.0","id":1,"result":{"success":true,"url":"https://www.pathofexile.com/trade/search/Keepers"}}
```

## 설정

`src/main.js`에서 설정 변경 가능:

```javascript
const CONFIG = {
    IPC_PORT: 47851,
    MEMORY_CHECK_INTERVAL: 30000,  // 30초
    MEMORY_THRESHOLD_MB: 800,       // 800MB
    IDLE_TIMEOUT_MS: 5 * 60 * 1000, // 5분
    CACHE_CLEANUP_INTERVAL: 60000   // 1분
};
```

## 캐시 시스템

3단계 캐시로 메모리 효율적 관리:

- **Hot**: 최근 1분 이내 접근
- **Warm**: 1-5분 사이 접근
- **Cold**: 5분 이상 미접근 (30분 후 삭제)

메모리 임계치 초과 시:
1. Cold/Warm 캐시 삭제
2. 가비지 컬렉션 실행
3. 여전히 높으면 프로세스 종료

## 개발

### 빌드

```bash
npm run build:win
```

### 디버그 로그

프로세스 시작 시 콘솔에 다음 정보 출력:
- IPC Port
- Memory Threshold
- Idle Timeout

## 의존성

- Node.js 18+
- Electron 28+
- electron-store (설정 저장)

## 문제 해결

### IPC 연결 실패

1. 포트 47851이 사용 중인지 확인
2. Electron 프로세스가 실행 중인지 확인
3. 방화벽 설정 확인 (localhost)

### 메모리 초과 종료

- 캐시 사용량 확인: `getCache` 메서드
- 수동 캐시 정리: `clearCache` 메서드
- 임계치 조정: `MEMORY_THRESHOLD_MB` 변경

### 자동 종료됨

- `IDLE_TIMEOUT_MS` 값 증가
- 주기적으로 `ping` 요청으로 활성 상태 유지
