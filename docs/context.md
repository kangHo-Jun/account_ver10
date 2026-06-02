# Context

Last updated: 2026-06-01 08:07 KST
Project: Ecount ERP automation (`c:\Users\DSAI\Desktop\회계_ERP`)

## 1) Current system status
- Automation process: running (`pythonw.exe` observed, latest PID seen: 33296)
- Heartbeat: recovered and updating (was stuck at 07:37, then updated to 07:56)
- Watchdog: reconfigured and manually relaunched during recovery
- Operational verdict: currently normal

## 2) Incident summary (this session)
- Failure window identified from logs:
  - Last pre-failure log: `v9_20260529_094413.log` (2026-05-29 09:44)
  - Next log after outage: `v9_20260601_071002.log` (2026-06-01 07:10)
- Missing processing during outage was replayed after recovery.
- Replay result:
  - First recovery cycle uploaded 48 rows
  - Second validation cycle uploaded 1 row
  - Total replayed: 49 rows

## 3) What was changed

### A. Startup hardening
File: `start_automation.bat`
- Added delayed expansion and startup checks
- Added stale `runtime.lock` validation/removal
- Added pre-start chrome cleanup (`taskkill /IM chrome.exe /T`)
- Preserved duplicate-run guard for `pythonw.exe`
- Added explicit startup verification output

### B. Watchdog hardening
File: `watchdog.py`
- Check interval: `300s -> 120s`
- Stale threshold: `60m -> 15m`
- Restart path now cleans:
  - `pythonw.exe`
  - `chrome.exe`
  - stale `runtime.lock`
- Keeps restart cooldown after recovery

### C. Watchdog launcher
File: `start_watchdog.bat`
- Added venv fallback order:
  1. `.\venv\Scripts\python.exe`
  2. `.\.venv\Scripts\python.exe`
  3. `python`
- Launches `watchdog.py` from project root

### D. Documentation
File: `docs/자동화실패보고서_v1.md`
- Added section `9. 장애 추가 분석 (2026-05-29 ~ 2026-06-01)`
- Included root cause, impact, replay outcome, and prevention actions

## 4) Known environment constraints
- `schtasks /Create ...` failed repeatedly with `Access is denied` in current shell context.
- As workaround, Startup-folder autostart path was used/verified by user.
- PowerShell profile execution-policy warning appears in this environment and is non-blocking for app runtime.

## 5) How to operate now

### Quick health check
```powershell
dir .\heartbeat.txt
tasklist | findstr /I "pythonw.exe"
```

### If stalled (heartbeat not updating for >15m)
```powershell
taskkill /F /IM pythonw.exe /T
taskkill /F /IM chrome.exe /T
del .\runtime.lock -ErrorAction SilentlyContinue
del .\heartbeat.txt -ErrorAction SilentlyContinue
.\start_automation.bat
Start-Process -WindowStyle Hidden -FilePath "C:\Users\DSAI\Desktop\회계_ERP\venv\Scripts\python.exe" -ArgumentList "C:\Users\DSAI\Desktop\회계_ERP\watchdog.py"
```

## 6) Open follow-ups (recommended next dev tasks)
1. Make watchdog singleton (prevent duplicate watchdog instances reliably).
2. Add explicit watchdog log file (separate from main logs) for easier diagnostics.
3. Add automatic alert when heartbeat age > 15m (email/slack).
4. Add command to verify startup-autorun registration health (Startup shortcut + process check).
5. Normalize doc encoding across `docs/*.md` to UTF-8 and remove mojibake.

## 7) Resume checklist for next developer
- Confirm `pythonw.exe` is running.
- Confirm `heartbeat.txt` is updating every loop.
- Run one forced health cycle only if stale detected.
- Review latest logs under `logs/` for `[ERROR]`, `[STOP]`, and summary `IN/OUT/SKIP`.
- Continue from follow-up items in section 6.

## 8) 2026-06-02 Incident Record (Today)

### Summary
- At 2026-06-02 07:06 KST, system was confirmed stalled.
- `pythonw.exe` was not running at first check.
- `heartbeat.txt` and logs had stopped after the prior day (`2026-06-01 16:13`).

### Root Cause Analysis (based on evidence)
1. Immediate stop point on 2026-06-01:
   - Last active cycle completed successfully in `v9_20260601_161219.log`.
   - Follow-up wait log `v9_20260601_161343.log` was written, then no further cycle logs.
2. Most likely cause:
   - Process terminated externally during wait window (not a clear in-app exception crash).
3. Supporting evidence:
   - No definitive `pythonw` crash signature was found in queried Windows Application/System logs for that window.

### Recovery Actions Performed Today
1. Cleanup:
   - Removed stale `runtime.lock`
   - Removed stale `heartbeat.txt`
   - Cleared stale processes where applicable
2. Restart:
   - Re-ran `start_automation.bat`
   - Re-launched `watchdog.py`
3. Verification:
   - `pythonw.exe` resumed
   - `heartbeat.txt` updated again
   - New logs were created (`v9_20260602_070906.log`, `v9_20260602_070951.log`, `v9_20260602_071114.log`)

### Data Replay Result (after 2026-06-01 16:13 stall)
- Forced replay cycle on 2026-06-02 processed missing items.
- Confirmed additional upload: `OUT 2` (from `v9_20260602_070951.log`).

### Hardening Applied Today
1. `start_automation.bat` stabilized to avoid batch parse edge case (`. was unexpected at this time`).
2. `watchdog.py` enhanced with restart audit logging:
   - Planned log file path: `logs/watchdog_events_YYYYMMDD.log`
   - Records restart reason, timing, and kill/restart outcome.
3. Noted caution:
   - Avoid broad `taskkill /IM python.exe /T` in future, as it can kill unrelated Python tooling.

### Current Operational Status (after recovery)
- Automation: running
- Heartbeat: updating
- Replay: completed for detected missing items

## 9) 2026-06-02 08:14 Stall Follow-Up

- A second stall was diagnosed after `v9_20260602_081402.log`.
- The 08:14 cycle had completed successfully and entered normal 30-minute wait.
- The main process then disappeared during the wait window; `runtime.lock` still pointed to stale PID `113412`.
- Recovery at 12:16 restarted the main automation as PID `83884`.
- Recovery cycle uploaded 13 pending rows successfully at 12:18.
- Watchdog was relaunched and confirmed writing `logs/watchdog_events_20260602.log`.
- Watchdog stale threshold was adjusted from 15 minutes to 45 minutes because the normal automation interval is 30 minutes.
- Full incident record: `docs/incident_20260602_0814_stall.md`
