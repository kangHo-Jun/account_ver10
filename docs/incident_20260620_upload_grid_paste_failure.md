# Incident Record - 2026-06-20 Upload Grid Paste Failure

## Summary
- On 2026-06-20, repeated alert mails were sent with:
  - `[ERROR] cycle error: upload process error`
  - `Exception: upload process error`
- User-reported alert times:
  - `2026-06-20 08:52:53`
  - `2026-06-20 17:38:48`
- The failure was not caused by login or payment query navigation.
- The direct cause was that the ECOUNT `BulkUploadForm` upload grid did not accept the pasted rows, but the automation still proceeded to press `F8`.

## Evidence
- `logs/v9_20260620_082013.log`
  - `08:51:50` summary: `IN 199`, `OUT 2`, `SKIP 197`
  - `08:52:00` `Control+V` executed
  - `08:52:04` grid data not detected after paste, fallback type attempted
  - `08:52:34` `F8` save executed
  - `08:52:53` result text was the upload form/help page, not a normal success popup
  - `08:52:53` upload failure detected
- `logs/v9_20260620_170558.log`
  - `17:37:45` summary: `IN 209`, `OUT 12`, `SKIP 197`
  - `17:37:55` `Control+V` executed
  - `17:37:58` grid data not detected after paste, fallback type attempted
  - `17:38:29` `F8` save executed
  - `17:38:47` result text was the upload form/help page, not a normal success popup
  - `17:38:48` upload failure detected
- Screenshot:
  - `logs/upload_fail_1781944727.png`
  - The first required date cell was still empty and highlighted as required, confirming the upload grid had not received row data.

## Data Recovery
- On 2026-06-22 07:13, the backlog was processed successfully.
- `logs/v9_20260620_173850.log`:
  - `07:12:53` summary: `IN 195`, `OUT 14`, `SKIP 181`
  - `07:13:14` result popup: success `14`, failure `0`
  - `07:13:17` 14 upload records saved
- `uploaded_records.json` after recovery:
  - 2026/06/20 records: `12`
  - 2026/06/22 records: `2`
- Conclusion: the 2026-06-20 unprocessed data visible to the automation was recovered without duplicate marking.

## Root Cause
- Existing upload flow only checked once whether the first pasted value appeared in the upload grid.
- If it was not detected, the code attempted a keyboard `type()` fallback.
- The code did not re-verify the grid after the fallback.
- Therefore, an empty/invalid upload grid could still reach the `F8` save step.
- ECOUNT then returned/displayed the upload form content instead of a normal success/failure result popup.

## Fix Applied on 2026-06-22
- Pre-fix checkpoint commit:
  - `751de77 checkpoint: before upload guard fix`
- Fix commit:
  - `f0834aa fix: block empty upload grid saves`
- Modified file:
  - `modules/uploader.py`
- Changes:
  - Added upload grid focus helper.
  - Added paste verification based on the first expected upload-cell value.
  - Added up to 3 paste attempts.
  - Kept keyboard `type()` fallback, but now verifies after fallback.
  - Blocks `F8` save when the grid still appears empty after retries.
  - Treats missing save result popup as failure, not success.
  - Verifies that success count equals the expected upload row count.

## Verification
- Syntax check passed:
  - `.venv\Scripts\python.exe -m py_compile modules\uploader.py main.py`
- Production process was restarted after code change.
  - Old PID: `220712`
  - New PID: `255276`
- First cycle after restart:
  - `logs/v9_20260622_072036.log`
  - ERP shell ready
  - payment query read completed
  - `IN 195`, `OUT 0`, `SKIP 195`
  - browser cleanup completed normally

## Follow-Up
- The fix prevents the dangerous path where `F8` is pressed while the upload grid is empty.
- A future improvement may suppress repeated email alerts for the same unchanged upload failure batch.
