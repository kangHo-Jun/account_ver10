# 2026-06-02 08:14 Automation Stall Incident

## Summary

- Incident time: 2026-06-02 08:14 KST
- Detection time: 2026-06-02 12:12 KST
- Affected system: Ecount ERP automation
- Status after recovery: recovered and running
- Recovery result: 13 pending rows uploaded successfully at 12:18

## What Happened

The automation did not fail during an upload or browser operation. The 08:14 log shows a normal cycle completion:

- `v9_20260602_074238.log`
  - 08:13:58: save result confirmed, 3 rows uploaded
  - 08:14:00: cycle completed
  - 08:14:02: browser and Playwright cleanup completed
- `v9_20260602_081402.log`
  - 08:14:02: entered the normal 30-minute wait state

The next cycle should have started around 08:44, but no new automation log or heartbeat update was written after 08:14.

## Evidence

- `heartbeat.txt` was stuck at `2026-06-02T08:12:38`.
- `runtime.lock` contained PID `113412`.
- PID `113412` was no longer running at diagnosis time.
- The latest automation log before recovery was `v9_20260602_081402.log`, containing only the 30-minute wait line.
- No application traceback or `[ERROR]` entry was found at the stop point.
- `logs/watchdog_events_20260602.log` did not exist before recovery, so watchdog was not providing usable recovery/audit coverage at the time of failure.

## Root Cause

The immediate cause was that the main automation process exited or was terminated while it was in the normal wait window after a successful cycle.

The root operational weakness was watchdog coverage:

1. Watchdog was not confirmed running before the incident.
2. Watchdog logging was not available before recovery.
3. The watchdog stale threshold had been set to 15 minutes, while the main automation normally sleeps for 30 minutes between cycles. This could cause false-positive restarts during healthy operation.

Because of this, the stale heartbeat was not automatically recovered after the main process stopped.

## Recovery Actions

Performed on 2026-06-02 around 12:16 KST:

1. Confirmed the stale state:
   - `heartbeat.txt` was stale.
   - `runtime.lock` pointed to a non-running PID.
   - No active `pythonw.exe` existed for PID `113412`.
2. Removed stale runtime files:
   - `runtime.lock`
   - `heartbeat.txt`
3. Restarted the automation with `start_automation.bat`.
4. Relaunched watchdog.
5. Verified recovery:
   - Main automation PID: `83884`
   - New heartbeat: `2026-06-02T12:16:44`
   - Recovery log: `v9_20260602_121644.log`
   - Upload result: 13 rows uploaded successfully at 12:18
   - Follow-up wait log: `v9_20260602_121809.log`

## Fixes Applied

### Watchdog Timeout Adjusted

File: `watchdog.py`

- Before: `TIMEOUT_MINUTES = 15`
- After: `TIMEOUT_MINUTES = 45`

Reason:

- The main automation interval is 30 minutes.
- A 15-minute watchdog threshold is shorter than normal healthy idle time.
- A 45-minute threshold allows one full wait interval plus buffer, while still detecting real stalls.

### Watchdog Audit Logging Confirmed

After relaunch, watchdog logging was confirmed:

- `logs/watchdog_events_20260602.log`
- 12:20:23: watchdog started
- check interval: 120 seconds
- stale timeout: 45 minutes
- heartbeat age checks continued normally

## Current State After Fix

- Main automation is running.
- `runtime.lock` points to PID `83884`.
- Watchdog is running and logging.
- The system is in the expected 30-minute wait state after the 12:18 successful cycle.

## Follow-Up Recommendations

1. Make watchdog a singleton so duplicate watchdog processes cannot run.
2. Add a single health-check command that prints:
   - main PID
   - watchdog PID
   - heartbeat age
   - latest log file
3. Confirm Windows Startup or Task Scheduler starts both:
   - `start_automation.bat`
   - `start_watchdog.bat`
4. Avoid killing broad `python.exe` processes during recovery because unrelated Python tools may be running.
