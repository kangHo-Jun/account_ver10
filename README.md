# Account Automation

> 이카운트 ERP 결제내역 자동 업로드 시스템 (Playwright 웹 자동화)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.40+-green.svg)](https://playwright.dev/)

## 🚀 주요 기능

- **완전 자동화**: 로그인부터 데이터 업로드까지 사용자 개입 없이 실행
- **웹 기반**: 엑셀 파일 다운로드 없이 웹 페이지에서 직접 데이터 읽기
- **중복 방지**: 이미 업로드된 데이터 자동 스킵
- **세션 관리**: 로그인 세션 저장으로 빠른 재실행

## 📋 실행 흐름

1. 🔐 이카운트 로그인 (세션 저장)
2. 📄 결제내역조회 페이지 이동
3. 🔘 '미반영' 필터 클릭
4. 📊 테이블 데이터 읽기
5. 🔄 입금보고서 형식으로 변환
6. 📋 클립보드 복사
7. 📄 입금보고서 페이지 이동
8. 📤 웹자료올리기 팝업 열기
9. ✅ 데이터 붙여넣기
10. 💾 F8 저장 (테스트 모드 OFF 시)

## 🛠️ 설치

```bash
# 1. 저장소 클론
git clone https://github.com/YOUR_USERNAME/Account_Automation.git
cd Account_Automation

# 2. 의존성 설치
pip install -r requirements.txt

# 3. Playwright 브라우저 설치
playwright install chromium

# 4. 설정 파일 생성
copy config.example.json config.json
# config.json에 실제 로그인 정보 입력
```

## ▶️ 실행

```bash
python main.py
```

## ⚙️ 설정

`config.json` 파일에서 다음 항목을 수정하세요:

```json
{
  "credentials": {
    "company_code": "YOUR_COMPANY_CODE",
    "username": "YOUR_USERNAME",
    "password": "YOUR_PASSWORD"
  },
  "test_mode": true
}
```

- `test_mode: true` - 붙여넣기까지만 실행 (F8 저장 안 함)
- `test_mode: false` - F8 저장까지 자동 실행

## 📁 프로젝트 구조

```
Account_Automation/
├── main.py                 # 메인 실행 파일
├── config.json             # 설정 파일 (Git 제외)
├── config.example.json     # 설정 예시
├── requirements.txt        # 의존성
├── .gitignore             # Git 제외 목록
├── sessions/              # 세션 저장 (자동 생성)
├── logs/                  # 로그 파일 (자동 생성)
└── uploaded_records.json  # 업로드 기록 (자동 생성)
```

## 🔒 보안

- `config.json`은 `.gitignore`에 포함되어 GitHub에 업로드되지 않습니다
- 로그인 정보는 로컬에만 저장됩니다
- 세션 파일도 Git에서 제외됩니다

## 📄 라이선스

MIT License
