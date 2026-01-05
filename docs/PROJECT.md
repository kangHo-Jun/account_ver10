# Account Automation Project

## Overview
이카운트 ERP의 결제 내역을 자동으로 조회하여 입금 보고서로 업로드하는 자동화 시스템입니다.
Playwright를 사용하여 웹 기반으로 동작하며, 엑셀 다운로드 과정 없이 직접 데이터를 처리합니다.

## Tech Stack
- Language: Python 3.8+
- Library: Playwright (Web Automation), pyperclip (Clipboard Integration)
- Target: Ecount ERP

## Key Features
1. 자동 로그인 및 세션 관리
2. 결제내역조회 페이지 데이터 파싱
3. 입금보고서 형식으로의 데이터 변환 및 중복 제거
4. 웹자료올리기를 통한 자동 데이터 업로드

## Development History (Timeline)

| Version | Period | Key Updates & Milestones |
| :--- | :--- | :--- |
| **V1 ~ V3** | Early 2025 | 프로젝트 초기화 및 기초 자동화 로직 수립 (Monolithic) |
| **V7** | Late 2025 | 22컬럼 데이터 규격 확정 및 물리적(Physical) 붙여넣기 메커니즘 최적화 |
| **V8** | 2025-12 | Flask Server 기반 자동화 도입 및 데이터 처리 속도 향상 |
| **V9.0** | 2026-01 | **Modular Architecture** 전환, **Playwright** 기반 웹 자동화 고도화 |
| **V9.5** | **Current** | 환경 분리(Test/Prod), 카드사 명칭 통일 및 중복 헤더 필터링 로직 반영 |
