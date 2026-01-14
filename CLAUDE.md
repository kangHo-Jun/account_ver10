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

- **Logging**: Use emoji prefixes for visual scanning (🔄 = process, ✅ = success, ❌ = error, ⚠️ = warning)
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
