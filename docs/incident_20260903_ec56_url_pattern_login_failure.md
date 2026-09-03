# Incident Record - 2026-09-03 ERP URL Pattern Login Failure

## Summary
- User-reported alert:
  - `[ERROR] cycle error: login failure`
  - `Exception: login failure`
  - Alert time: `2026-09-03 17:13:12`
- The alert message was generic (`main.py:181 raise Exception("로그인 실패")`), so the true cause was not visible from the email alone.
- Actual cause: ECOUNT changed the post-login redirect path from `ec5/view/erp` to `ec56/view/erp`. The ERP shell loaded correctly every time, but `core/browser.py` only recognized the hardcoded `ec5/view/erp` substring, so every fresh login was misclassified as a failure.
- This was **not** related to the earlier-discussed "다른 컴퓨터 동시 로그인" popup theory. That is a separate, second issue (see Follow-Up).

## Scope / Impact
- Last fully successful cycle: `2026-09-02 15:38:01` (session reuse, `ec5/view/erp`).
- `ec56` first appeared on the next fresh login, in `logs/v9_20260902_174508.log` (cycle at `2026-09-03 07:05:11`), after the previous saved `ec5` session expired.
- From `2026-09-03 07:05:11` through `2026-09-04 07:44` (before the fix landed), **every single cycle failed** with the same `ERP shell load failed after login` error — roughly 38 hours, ~45 consecutive failed cycles, one alert email per cycle.
- No payment data was uploaded to the deposit report during this window. All of it was recovered automatically once the fix landed (see Verification), because the reader always re-queries the full `미반영` list rather than tracking an offset.

## Evidence
- `logs/v9_20260903_164119.log` (contains the reported `17:13:12` alert):
  - `17:12:07` login succeeded (left `login.ecount.com`)
  - `17:12:12` new-device popup not present, continuing
  - `17:13:12` `ERP shell not ready (current URL: https://loginab.ecount.com/ec56/view/erp?...)` — frames show the real ERP shell content (`about:blank` helper frames alongside it), i.e. the page had actually loaded.
  - `17:13:12` `ERP shell load failed after login` → `로그인 실패` exception raised
- `grep -l "ec56/view/erp" logs/*.log` first hit: `logs/v9_20260902_174508.log`, none before.
- `grep -c "ERP shell ready" logs/v9_20260903_*.log` / `v9_20260904_*.log`: `0` across every file until the fix.

## Root Cause
Four locations in `core/browser.py` matched the ERP shell URL with the literal substring `"ec5/view/erp"`:
- `ERP_BASE_URL` constant (used to rebuild a direct shell URL from the session cookie)
- `get_erp_frame()`
- `_is_bad_session_url()`
- `wait_for_erp_shell()`

`"ec5/view/erp"` is not a substring of `"ec56/view/erp"` (the character after `ec5` is `6`, not `/`), so none of these checks recognized the new redirect target. The polling loop in `wait_for_erp_shell()` ran for the full 60s timeout believing the shell was still loading, then gave up and raised the generic login-failure exception even though the shell had loaded within a few seconds.

## Fix Applied on 2026-09-04
- Modified file: `core/browser.py`
- Added `ERP_SHELL_PATTERN = re.compile(r"ec\d+/view/erp")` and replaced all three substring checks (`get_erp_frame`, `_is_bad_session_url`, `wait_for_erp_shell`) with a regex match against this pattern, so any future `ecNN` redirect target (not just `ec56`) is recognized without another code change.
- Updated `ERP_BASE_URL` from the stale `ec5` path to `ec56`, matching the current known-good cookie-recovery fallback target.
- Syntax verified: `.venv\Scripts\python.exe -c "import py_compile; py_compile.compile('core/browser.py', doraise=True)"`.

## Verification
- The running orchestrator process had been alive continuously since `2026-08-14 18:00:05` (`tasklist` confirmed `Session Name: Services`, `Session# 0` — a Task Scheduler / service-session process), so the source fix did not take effect until the process was restarted. Killing it required an elevated (Administrator) PowerShell window because a standard user session gets `Access is denied` against a Session 0 process.
- Old PID: `21652` → New PID: `41100` (restarted via `.venv\Scripts\pythonw.exe main.py`, the known-good virtual environment — see Follow-Up).
- First cycle after restart, `logs/v9_20260904_074729.log`:
  - `07:48:16` `[OK] ERP shell ready (URL: https://loginab.ecount.com/ec56/view/erp?...)`
  - Summary: `IN 206`, `OUT 40`, `SKIP 166` (local duplicates)
  - `07:50:50` save result popup: `성공 : 40건 실패 : 0건`
  - Backlog recovered spanned `2026-09-03 06:44` through `2026-09-04` morning — the full outage window, with zero duplicate/lost records.

## Follow-Up (not yet fixed)
1. **Duplicate/broken virtual environment.** The project has two venvs: `.venv/` (working, has the bundled Playwright `node.exe`, actually used by the long-running production process) and `venv/` (missing `node.exe`, cannot launch a browser at all — confirmed via `python -m playwright --version` failing with `WinError 2`). `start_prod.bat` still references the non-dot `venv`. This should be cleaned up (delete the broken `venv/`, fix `start_prod.bat` / `watchdog.py` to reference `.venv` explicitly) before it causes a future restart to silently fail.
2. **Daily auto-restart not actually firing.** CLAUDE.md documents a 06:00 date-change restart, but the process ran unrestarted for 21 days (`2026-08-14` → `2026-09-04`). Worth auditing why `sys.exit(0)` isn't being hit or why the external wrapper isn't relaunching it — this is also why the `ec56` fix required a manual, elevated restart instead of picking up automatically.
3. **No handling for the "동일 ID 접속중" (concurrent session) confirmation popup.** Reproduced live during this incident's diagnostics: a manual one-off login collided with the still-nominally-active production session (because `BrowserManager.close()` never performs an explicit logout, only closes the local browser) and the login hung on the `app.login/erp_login` handoff page for the full 60s timeout — the same symptom as the original 2026-08-19 incident. No code in the repo handles this popup (no `page.on("dialog")`, no in-page "확인" button click). Two possible approaches to discuss: (a) explicit logout in `close()` to avoid leaving a dangling session, and/or (b) detect the popup and skip the cycle gracefully (never auto-confirm it, since auto-confirming would forcibly kick out a legitimate human session).
