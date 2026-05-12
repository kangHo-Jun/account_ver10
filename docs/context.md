# Context

## 현재 깃 상태

- 브랜치: master
- 최신 커밋: ff2ddf4 feat: PG 결제대행사매출조회 자동화 추가 - 2시간 주기

## 오늘 개발 내용

- PG 결제대행사매출조회 자동화 추가
- `modules/pg_reader.py`, `modules/pg_transformer.py` 생성
- `main.py` 2시간 PG 사이클 추가

## 현재 문제점

- PG 팝업 `적용` 버튼 클릭 실패
- `.venv` vs 시스템 Python 환경 혼재
- `start_automation.bat` 환경 정리 필요

## 앞으로 해야할 일

- PG 팝업 셀렉터 실사이트 테스트 및 수정
- `start_automation.bat` 환경 통일
- PG 사이클 테스트 완료 후 운영 적용
