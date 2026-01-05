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
