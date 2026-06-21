# Project History & Change Log

## 2026-06-22
- Investigated repeated 2026-06-20 upload-process alert mails.
- Confirmed cause: ECOUNT bulk upload grid did not receive pasted rows, but the previous flow could still press `F8`.
- Confirmed recovery: 2026-06-20 backlog `12` rows were uploaded successfully on 2026-06-22 07:13, together with 2026-06-22 `2` rows.
- Added upload-grid paste verification and save blocking in `modules/uploader.py`.
- Commits:
  - `751de77 checkpoint: before upload guard fix`
  - `f0834aa fix: block empty upload grid saves`
- Incident record: `docs/incident_20260620_upload_grid_paste_failure.md`.

## 2026-06-08
- Rechecked the 2026-06-06 payment-query failure alert.
- Confirmed cause: ERP payment query grid did not load after login/menu navigation, triggering `결제조회 페이지 이동 실패`.
- Added pagination-enabled ERP `미반영` read verification.
- Current ERP `미반영` recheck found `2026/06/06` rows: `0`.
- Incident record: `docs/incident_20260608_0606_recheck.md`.

## 2026-04-01
- **v1 Baseline 설정**
  - 초기 소스 코드 백업 및 버전 관리 기준 수립.
- **취소 거래 처리 로직 수정**
  - **버그:** 취소 건이 양수로 업로드되는 문제 해결.
  - **수정:** 상태 값 추출 컬럼 변경 (`SETL_STAT_NM` → `SETL_STATUS_TYPE`).
  - **결과:** 취소 건(-100원 등) 정상 업로드 확인.
- **Chrome 좀비 프로세스 누수 수정**
  - **문제:** 사이클 종료 후 Chrome 프로세스가 남는 현상 발견.
  - **수정:** `core/browser.py`에 시작 전 사전 정리 및 종료 시 `taskkill` 강제 종료 로직 추가.
  - **결과:** 장기 실행 안정성 확보 및 메모리 관리 효율화.

## 2026-02-11
- 시스템 장애 복구 (2/10 오전 발생 건).
- 환경 정비 (잔류 프로세스 정리 및 락 파일 제거).
- `start_prod.bat` 재실행 확인.

## 2026-01-05
- 프로젝트 초기화 및 GitHub 저장소 복구.
- 환경 구성 (`main.py`, `config.json` 등).
- 문서화 시작 (`PROJECT.md`, `SESSION.md`, `DECISIONS.md`).
