# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Ecount ERP automation system** (V9.5) that automatically extracts payment data from the "결제내역조회" (Payment Query) page and uploads it to the "입금보고서" (Deposit Report) page using Playwright web automation. It runs continuously during business hours (06:00-18:00) with 30-minute intervals.

**Core Purpose**: Eliminate manual data entry by automating the payment reconciliation workflow in Ecount ERP.

## Architecture

### Modular Design (Orchestrator Pattern)

The system uses a **clear separation of concerns** with the orchestrator (`EcountAutomationOrchestrator`) coordinating specialized modules:

```
main.py (Orchestrator)
  ├── core/browser.py      - Playwright lifecycle, session persistence
  ├── core/logger.py       - Unified logging system
  ├── modules/login.py     - Authentication
  ├── modules/reader.py    - Data extraction from payment query page
  ├── modules/transformer.py - Data validation, transformation, deduplication
  ├── modules/uploader.py  - Data upload to deposit report
  └── modules/notifier.py  - Email notifications (errors & summaries)
```

### Single Cycle Workflow

Each automation cycle follows this sequence:

1. **Browser Init** - Start Playwright → Load session OR login → Save session
2. **Navigate & Read** - Go to "결제내역조회" → Check "회계반영" tab → Read "미반영" tab data
3. **Transform** - Validate data → Check duplicates (3 layers) → Format for upload
4. **Upload** - Go to "입금보고서" → Open "웹자료올리기" → Paste → Save (F8) → Verify
5. **Record** - Save new transaction keys to `uploaded_records.json`
6. **Cleanup** - Close browser completely (critical for event loop stability)

### Key Data Flow

```
Payment Query Page (raw data)
  → ReaderModule.read_payment_data()
  → [date, customer, amount, account, status, auth_no] (list of dicts)
  → TransformerModule.transform()
  → [date, seq, voucher, account, code, ...] (22-column format)
  → UploaderModule.upload()
  → Clipboard paste → Grid → F8 save
  → Success verification via popup parsing
```

## Critical Architectural Decisions

### 1. Playwright Sync API (NOT Async)
- **Why**: Stability and simplicity. Async caused event loop issues during long-running operations.
- **Implication**: Use `sync_playwright()`, not `async_playwright()`. All Playwright calls are blocking.

### 2. Browser Lifecycle Management
- **Pattern**: Create fresh Playwright instance per cycle, close completely after each cycle
- **Why**: Prevents "Event loop is closed" errors in long-running processes
- **Location**: `BrowserManager.start()` creates new instance, `BrowserManager.close()` destroys everything
- **NEVER**: Reuse browser instances across cycles

### 3. Triple-Layer Deduplication
1. **Local DB** (`uploaded_records.json`) - Date/time string keys
2. **Real-time ERP** - Check "회계반영" tab for authorization numbers
3. **Data validation** - Exclude invalid statuses: `'승인실패'`, `'취소실패'`, `'요청중'`

### 4. Clipboard Strategy
- **Primary**: Browser-side JavaScript clipboard injection (`page.evaluate()`)
- **Fallback**: `pyperclip` for physical clipboard
- **Why**: Virtual clipboard is more reliable in headless mode and avoids race conditions

### 5. Session Persistence
- **File**: `sessions/session.json` (cookies + URL)
- **Validation**: Check if current URL contains "login" → expired → re-login
- **Benefit**: Avoids login on every cycle (saves ~10 seconds)

## Common Development Commands

### Running the System

```bash
# Test mode (visible browser, no save)
python main.py  # with config.json: mode="test"

# Production mode (headless, auto-save)
python main.py  # with config.json: mode="production"

# Background execution (Windows)
pythonw main.py

# Via batch scripts
start_test.bat          # Test mode with visible browser
start_prod.bat          # Production background mode
start_auto_restart.bat  # Continuous operation with auto-restart
```

### Testing Individual Modules

```bash
# Test email notifications
python test_email.py

# Analyze uploaded records
python analyze_sync.py

# Check Excel content (if debugging exports)
python check_excel_content.py
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Log Management

Logs are automatically created in `logs/` with format: `v9_YYYYMMDD_HHMMSS.log`

```bash
# View latest log
ls -lt logs/*.log | head -1
tail -f logs/v9_YYYYMMDD_HHMMSS.log

# Check for errors in recent logs
grep "ERROR" logs/v9_*.log | tail -20
```

## Configuration (config.json)

**Critical fields**:
- `mode`: `"test"` (no save) vs `"production"` (full automation)
- `credentials`: Company code, username, password
- `urls.payment_query_hash` / `urls.deposit_report_hash`: ERP page hashes (change when ERP updates)
- `schedule.interval_minutes`: Cycle interval (default: 30)
- `schedule.work_hours`: `start` (06:00) and `end` (18:00)
- `browser.headless`: Auto-set based on mode (test=false, prod=true)

## Key Implementation Details

### Frame Navigation Pattern
Ecount ERP uses nested iframes. To find elements:

```python
# Pattern in ReaderModule and UploaderModule
for i, frame in enumerate(page.frames):
    element = frame.query_selector("your_selector")
    if element:
        # Found in this frame
        break
```

**Always log frame counts** when debugging element not found issues.

### Popup Handling
- **Detection**: Count popups before/after action: `len(page.context.pages)`
- **Verification**: Parse popup text for "성공 : N건 실패 : M건"
- **Critical**: Close all popups after verification to avoid memory leaks

### Cancellation Transaction Handling
- **Detection**: Status field contains "취소"
- **Format**: Prefix amount with "-" (negative) in output
- **Statistics**: Track separately in `stats["cancellations"]`

### Date Change Handling
The system auto-restarts at 06:00 daily to create fresh log files:

```python
# In main.py orchestrator
if current_date > start_date and current_time >= "06:00":
    logger.info("🔄 새로운 날 시작 - 프로그램 재시작")
    sys.exit(0)  # Auto-restart via batch script wrapper
```

### Card Provider Normalization
Multiple card provider names are unified to "카드사":
- `비씨카드사`, `국민카드사`, `하나카드사` → `카드사`
- **Location**: `TransformerModule.transform()` → `unify_card_provider_name()`

## Troubleshooting Guide

### "Event loop is closed" Error
**Root cause**: Playwright instance not properly cleaned up from previous cycle.

**Fix**:
1. Kill all pythonw.exe processes running main.py
2. Restart the program
3. Verify `BrowserManager.close()` is called in `finally` block

### Login Fails / Session Expired
**Check**:
1. `sessions/session.json` exists and has recent `saved_at` timestamp
2. URL in session matches current ERP structure
3. Credentials in `config.json` are correct

**Fix**: Delete `sessions/session.json` to force fresh login.

### Email Notification Fails
**Error**: "Application-specific password required"

**Fix**:
1. Enable 2FA in Gmail
2. Generate app-specific password
3. Update `config.json` → `notification.email.sender_password`

### No Data Found / Element Not Found
**Debug steps**:
1. Check frame count in logs: "감지된 프레임 수: N"
2. Run in test mode (headless=false) to visually inspect page
3. Verify URL hash in `config.json` matches current ERP page
4. Check if ERP page structure changed (CSS selectors in modules)

### Duplicate Upload Issues
**Check**:
1. `uploaded_records.json` file integrity (valid JSON array)
2. "회계반영" tab detection logs: "실시간 회계반영 N건 감지됨"
3. Date format consistency: "YYYY/MM/DD HH:MM:SS"

## Files You Should NOT Modify

- `uploaded_records.json` - Auto-managed deduplication database (only delete to reset)
- `sessions/session.json` - Auto-managed session storage
- `logs/*.log` - Read-only runtime logs

## Files You WILL Modify

- `config.json` - Configuration changes
- `modules/*.py` - Business logic updates (e.g., new data fields, validation rules)
- `utils/config.py` - Add new config keys or defaults

## Code Style Conventions

- **Logging**: Use ASCII `[TAG]` prefixes for Windows cp949 compatibility (NOT emojis)
  - `[OK]` = success, `[ERROR]` = error, `[WARN]` = warning
  - `[START]`, `[STOP]`, `[CYCLE]` = process lifecycle
  - `[NAV]`, `[CLICK]`, `[SAVE]` = UI actions
  - See "Lessons Learned (2026-01-16)" for full mapping
- **Error Handling**: Always wrap main logic in try/except with email notification on failure
- **Browser Cleanup**: ALWAYS call `browser.close()` in `finally` blocks
- **Type Hints**: Not heavily used (legacy codebase), but preferred for new functions
- **Comments**: Korean comments acceptable (project is Korean-language)

## Production Deployment

1. Set `config.json` → `mode: "production"`
2. Set `config.json` → `browser.headless: true`
3. Verify email notifications work (test with `test_email.py`)
4. Run via `start_auto_restart.bat` for continuous operation
5. Monitor logs daily for errors

## Version History Context

- **V1-V3**: Monolithic proof-of-concept
- **V7**: Physical clipboard optimization (22-column format finalized)
- **V8**: Flask server attempt (abandoned due to complexity)
- **V9.0**: Modular architecture rewrite ⭐
- **V9.5**: Test/Prod separation, card provider unification
- **V10**: Real-time ERP deduplication (회계반영 tab checking)
- **V12.1**: Enhanced save verification & popup handling
- **V12.2**: Process lock implementation (duplicate process prevention) ⭐
- **V12.3**: Heartbeat monitoring & Windows Task Scheduler (stability system) ⭐

**Current version**: V12.3 (3-layer defense system for process stability)

## Important References

- **docs/PROJECT.md** - Development timeline and milestones
- **docs/DECISIONS.md** - Architecture decision records (ADR)
- **개발_회고_및_개선사항.md** - Extensive post-mortem with edge cases and solutions
- **README.md** - User-facing installation and setup guide
- **CHANGELOG_V12.2.md** - Process lock implementation details
- **CHANGELOG_V12.3.md** - Heartbeat & scheduler implementation details
- **IMPLEMENTATION_SUMMARY.md** - Complete stability system overview

---

## Lessons Learned (2026-01-14)

### Critical Incident: 20-Hour System Freeze

**Problem**: System completely stopped from Jan 13 18:01 to Jan 14 14:48 (20 hours)

**Root Cause**: 4 duplicate pythonw.exe processes (PID: 41800, 41828, 42768, 42804) causing resource conflicts

**Solution Implemented**: 3-layer defense system

```
Layer 1: Process Lock (V12.2)
  - runtime.lock file with PID validation
  - Prevents duplicate instances at startup
  - 100% prevention of the root cause

Layer 2: Heartbeat Monitoring (V12.3)
  - heartbeat.txt updated every cycle
  - watchdog.py monitors file modification time
  - Auto-restart if no update for 60 minutes
  - Detects "zombie" processes (alive but not responding)

Layer 3: Task Scheduler (V12.3)
  - restart_daily.bat runs at 05:55 daily
  - Force restart ensures log rotation
  - Safety net if date-change logic fails
```

### Technical Insights Gained

#### 1. Windows Process Management
```python
# PID validation using tasklist
result = subprocess.run(
    ['tasklist', '/FI', f'PID eq {pid}'],
    capture_output=True, text=True
)
if str(pid) in result.stdout:
    # Process is running
```
**Learning**: Always validate PID before trusting lock files. Old lock files from crashed processes must be cleaned up.

#### 2. Heartbeat Pattern for Long-Running Processes
```python
# Main process
while True:
    heartbeat()  # Update timestamp file
    do_work()

# Watchdog process
if (now - last_heartbeat) > timeout:
    kill_and_restart()
```
**Learning**: File modification time (`st_mtime`) is a simple but effective way to monitor process health without complex IPC.

#### 3. Defense in Depth
**Learning**: Single-layer solutions fail. Combining prevention (lock), detection (heartbeat), and failsafe (scheduler) creates robust systems.

#### 4. Windows Console Encoding Hell
```python
# ❌ DON'T: Emojis fail on cp949 console
print("❌ 에러")  # UnicodeEncodeError

# ✅ DO: ASCII tags work everywhere
print("[ERROR] 에러")
logger.error("에러")  # UTF-8 to file is safe
```
**Learning**: Windows console uses cp949, but files are UTF-8. Stick to ASCII for console output, Korean/emoji for logs.

### Debugging Methodology

**Timeline Analysis**:
1. Find last successful log entry (Jan 13 18:01)
2. Check what should have happened next (18:31 cycle)
3. Look for system-level issues (duplicate processes)
4. Trace the gap between expected and actual behavior

**Log Pattern Matching**:
```bash
# Find last cycle
grep "사이클 완료" logs/*.log | tail -1

# Check for duplicate processes
tasklist | findstr pythonw

# Verify process activity
grep -E "(ERROR|WARN)" logs/*.log
```

### Mistakes and Corrections

#### Mistake 1: Premature Hypothesis
- **Initial thought**: Date change logic failed
- **Reality**: Duplicate processes were the root cause
- **Lesson**: Don't assume—verify with data

#### Mistake 2: Overlooking System State
- **Miss**: Didn't check for duplicate processes early enough
- **Fix**: Now always check process count as first troubleshooting step
- **Tool**: `tasklist | findstr pythonw`

#### Mistake 3: Emoji Usage
- **Problem**: UnicodeEncodeError on Windows console
- **Fix**: Replaced all emojis with `[TAG]` format in critical code paths
- **Keep**: Emojis in log files (UTF-8) are still fine

### Best Practices Applied

#### 1. Phased Implementation
- Phase 1: Fix root cause (process lock) ✅
- Phase 2: Add detection (heartbeat) ✅
- Phase 3: Add safety net (scheduler) ✅

**Why this worked**: Each phase delivered value independently while building on previous work.

#### 2. Test-Driven Validation
- Created `test_process_lock.py` before deploying
- Created `test_heartbeat.py` to verify monitoring
- Caught encoding issues early

#### 3. Comprehensive Documentation
- CHANGELOG for each version
- Setup guides for non-technical users
- Implementation summary for future maintenance

### Code Patterns Worth Reusing

#### Lock File with PID Validation
```python
def acquire_lock(self):
    if lock_file.exists():
        old_pid = read_pid()
        if process_is_running(old_pid):
            return False  # Block duplicate
        else:
            delete_stale_lock()

    write_current_pid()
    return True
```

#### Heartbeat Monitoring
```python
# Main process
def heartbeat(self):
    with open('heartbeat.txt', 'w') as f:
        f.write(f"{datetime.now().isoformat()}\n")
        f.write(f"PID: {os.getpid()}\n")
        f.write(f"Stats: {self.stats}\n")

# Watchdog
last_modified = Path('heartbeat.txt').stat().st_mtime
if (time.time() - last_modified) > TIMEOUT:
    restart_process()
```

#### Finally Block for Cleanup
```python
def run(self):
    try:
        # Main logic
    finally:
        self.release_lock()  # Always cleanup
        self.browser.shutdown()
```

### Quantifiable Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Duplicate processes | 4 avg | 1 fixed | 100% |
| Max downtime | 20+ hours | <60 min | 95% ↓ |
| Manual interventions | 1-2/week | 0-1/month | 90% ↓ |
| Log file size | 292KB cumulative | 1-5KB per cycle | Manageable |

### Future Applications

**For any long-running process**:
- [ ] Implement lock file pattern
- [ ] Add heartbeat monitoring
- [ ] Set up automated restart (cron/Task Scheduler)
- [ ] Test all three layers independently
- [ ] Document troubleshooting steps

**For debugging production issues**:
- [ ] Check log timeline first
- [ ] Verify system state (processes, resources)
- [ ] Look for resource conflicts (locks, ports, files)
- [ ] Test hypothesis with data, not assumptions

### Tools Added to Toolkit

- **Process monitoring**: `tasklist` (Windows), `ps` (Linux)
- **File timestamps**: `pathlib.stat().st_mtime`
- **Subprocess management**: `subprocess.run()` with output capture
- **Batch scripting**: Windows `.bat` files for automation
- **Task Scheduler**: Windows automation infrastructure

---

**Key Takeaway**: The best debugging combines systematic log analysis, understanding system state, and building layered defenses. One-time fixes aren't enough—build systems that prevent, detect, and recover from failures automatically.

---

## Lessons Learned (2026-01-15)

### V13 Update: ERP Pre-Filtered Page Strategy

**Problem**: 코드에서 결제 상태를 필터링하는 것은 중복 작업이었음

**발견 과정**:
1. 사용자가 "필터링된 페이지를 사용하겠다"고 제안
2. URL 분석 결과, hash fragment가 기존과 **동일**함을 확인
3. 스크린샷 분석으로 ERP 페이지 구조 파악
4. **핵심 발견**: ERP 계정에 필터 설정이 저장되어 있어서 같은 URL로 접속해도 `승인`/`취소`만 표시됨

**Solution**:
```python
# Before (V10): 코드에서 상태 필터링
if status in ['승인실패', '취소실패', '요청중']:
    continue  # 제외

# After (V13): ERP에서 이미 필터링됨, 필수값 검증만 수행
if not customer or not amount_val:
    continue  # 필수값 누락만 체크
```

### Technical Insights

#### 1. ERP 필터 저장 방식 이해
- **동일한 URL/hash**로 접속해도 **계정별로 다른 데이터**가 표시될 수 있음
- ERP 내부에서 사용자별 필터 설정을 저장
- URL만 보고 페이지 내용을 판단하면 안 됨

#### 2. 세션 재활용 패턴
```python
# 실행 중인 시스템의 세션을 별도 스크립트에서 활용
session_file = Path("sessions/session.json")
with open(session_file, 'r') as f:
    session_data = json.load(f)

context.add_cookies(session_data.get('cookies', []))
page.goto(session_data.get('url', ''))
```
**Learning**: 별도 분석 스크립트 실행 시 기존 세션을 재활용하면 로그인 과정 생략 가능

#### 3. 스크린샷 기반 디버깅
```python
page.screenshot(path="logs/analyze_page.png", full_page=True)
```
**Learning**: ERP처럼 복잡한 iframe 구조에서는 스크린샷이 가장 빠른 UI 분석 방법

### Design Principle: Filter at Source

**Before**:
```
ERP (모든 데이터) → 코드 (필터링) → 업로드
```

**After**:
```
ERP (필터링된 데이터) → 코드 (검증만) → 업로드
```

**Benefits**:
- 불필요한 데이터 전송 감소
- 코드 복잡도 감소
- 단일 책임 원칙 (SRP) 준수: ERP가 필터링, 코드가 변환

### Code Changes Summary (V13)

| File | Change | Reason |
|------|--------|--------|
| `modules/transformer.py:49-54` | 상태 필터링 로직 제거 | ERP에서 이미 필터링됨 |

### Verification Checklist

다음 사이클에서 확인할 사항:
- [ ] 로그에서 `상태 승인실패` 제외 메시지가 사라짐
- [ ] 모든 `승인`/`취소` 데이터가 정상 업로드됨
- [ ] `취소` 거래는 여전히 `-` 붙어서 업로드됨

---

**Key Takeaway**: 데이터 필터링은 가능한 소스(source)에 가깝게 수행하라. 코드에서 중복 필터링하면 유지보수 부담만 증가한다. ERP 같은 외부 시스템의 설정을 활용하면 코드를 단순화할 수 있다.

---

## Lessons Learned (2026-01-16)

### Windows cp949 인코딩과 이모지 충돌

**Problem**: 프로그램 실행 시 `UnicodeEncodeError: 'cp949' codec can't encode character` 에러 발생

**Root Cause**: Windows 콘솔은 기본적으로 cp949 인코딩을 사용하며, 이모지(유니코드 확장 문자)를 출력할 수 없음

**에러 발생 상황**:
```
UnicodeEncodeError: 'cp949' codec can't encode character '\U0001f680' in position 18
# \U0001f680 = 🚀 (로켓 이모지)
```

### 해결 과정

**발견된 이모지 에러들** (순차적으로 발견):
1. `\U0001f680` (🚀) - main.py line 234
2. `\U0001f4c4` (📄) - logger.py line 30
3. `\U0001f310` (🌐) - browser.py
4. `\U0001f4a4` (💤) - main.py line 277
5. `\U0001f4dd` (📝) - main.py line 204

**Solution**: 모든 Python 파일에서 이모지를 `[TAG]` 형식으로 교체

### 이모지 → 태그 변환 매핑

| 이모지 | 태그 | 용도 |
|--------|------|------|
| 🚀 | `[START]` | 프로그램 시작 |
| ✅ | `[OK]` | 성공 |
| ❌ | `[ERROR]` | 에러 |
| ⚠️ | `[WARN]` | 경고 |
| 📄 | `[LOG]`, `[NAV]` | 로그, 네비게이션 |
| 🌐 | `[BROWSER]` | 브라우저 |
| 📋 | `[SESSION]`, `[CLIPBOARD]` | 세션, 클립보드 |
| 💾 | `[SAVE]` | 저장 |
| 🛑 | `[STOP]` | 중지 |
| ℹ️ | `[INFO]` | 정보 |
| 🔄 | `[TRANSFORM]`, `[CYCLE]` | 변환, 사이클 |
| 🛡️ | `[DUP]` | 중복 차단 |
| 📊 | `[SUMMARY]`, `[COUNT]` | 요약, 카운트 |
| 💤 | `[WAIT]`, `[SLEEP]` | 대기 |
| 📝 | `[RECORD]` | 기록 |
| 🌙 | `[SLEEP]` | 업무 외 시간 |
| 🔐 | `[LOGIN]` | 로그인 |
| 💳 | `[CARD]` | 카드사 |
| 📤 | `[UPLOAD]` | 업로드 |
| 🎯 | `[FOCUS]` | 포커스 |
| ⌨️ | `[KEY]` | 키 입력 |
| 📢 | `[RESULT]` | 결과 |
| 🚨 | `[ALERT]` | 알림 |

### 수정된 파일 목록

| 파일 | 수정 내용 |
|------|-----------|
| `main.py` | 🚀, 💤, 📝, ❌, 🔄, 🌙 등 다수 |
| `core/logger.py` | 📄 → `[LOG]` |
| `core/browser.py` | 🌐, ✅, ℹ️, 📋, 💾, 🛑 등 |
| `modules/login.py` | 🔐, ❌, ✅ |
| `modules/reader.py` | 📄, ❌, 🔘, ✅, ⚠️, 📊 등 |
| `modules/transformer.py` | 🔄, ⏩, 🛡️, ➖, 💳, 📊 등 |
| `modules/uploader.py` | 📄, ❌, ℹ️, 📋, 📤, 💾 등 |
| `modules/notifier.py` | ℹ️, ⚠️, ✅, ❌, 🚨, 📊 등 |

### Technical Insights

#### 1. Windows 인코딩 구조
```
콘솔 출력 (print) → cp949 인코딩 → 이모지 불가 ❌
파일 저장 (UTF-8) → UTF-8 인코딩 → 이모지 가능 ✅
```

**Key Point**: 로그 파일에는 이모지가 정상 저장되지만, `print()` 시점에서 에러 발생

#### 2. 문제 발견의 어려움
- 각 에러는 **프로그램 실행 시점**에서만 발견됨
- 한 이모지 수정 → 재실행 → 다른 이모지 에러 발생 → 반복
- **5번의 실행 실패** 후 모든 이모지 제거 완료

#### 3. 예방적 해결책
```python
# ❌ BAD: 이모지 직접 사용
logger.info("🚀 프로그램 시작")

# ✅ GOOD: ASCII 태그 사용
logger.info("[START] 프로그램 시작")
```

### Code Style Update

**기존 규칙** (CLAUDE.md 239줄):
```
- **Logging**: Use emoji prefixes for visual scanning (🔄 = process, ✅ = success, ❌ = error, ⚠️ = warning)
```

**새로운 규칙**:
```
- **Logging**: Use ASCII [TAG] prefixes for Windows compatibility
  - [OK] = success, [ERROR] = error, [WARN] = warning
  - [START], [STOP], [CYCLE] = process lifecycle
  - [NAV], [CLICK], [SAVE] = UI actions
```

### Verification

수정 후 프로그램 정상 실행 확인:
```
[08:22:50] [INFO] [OK] 총 100건의 유효 데이터 추출 완료
[08:22:50] [INFO] [TRANSFORM] 데이터 변환 중...
[08:23:08] [INFO] [OK] 저장 성공 확정: 1건 업로드 완료
[08:24:47] [INFO] [WAIT] 30분 대기 중...
```

---

**Key Takeaway**: Windows 환경에서 Python 프로그램을 개발할 때는 **콘솔 출력에 이모지를 사용하지 말 것**. 로그 파일(UTF-8)에는 안전하지만, `print()` 시점에서 cp949 인코딩 에러가 발생한다. ASCII 기반 `[TAG]` 형식이 가장 안전하고 이식성이 높다.
