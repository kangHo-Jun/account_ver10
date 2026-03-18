# Windows 작업 스케줄러 설정 가이드 (최종 버전)

## 개요
ERP 자동화 시스템을 Windows 작업 스케줄러로 완전히 제어합니다.
- 프로그램 내부에는 자동 종료 로직이 없음
- 시작/종료는 모두 스케줄러가 관리

---

## 필요한 작업

### 1. 시작 작업: "ERP 자동화 시작"
- **트리거**: 월~토 07:00
- **동작**: `C:\Users\DSAI\Desktop\회계_ERP\start_automation.bat`

### 2. 종료 작업 (평일): "ERP 자동화 종료 (평일)"
- **트리거**: 월~금 18:00
- **동작**: `C:\Users\DSAI\Desktop\회계_ERP\stop_automation.bat`

### 3. 종료 작업 (토요일): "ERP 자동화 종료 (토요일)"
- **트리거**: 토 14:00
- **동작**: `C:\Users\DSAI\Desktop\회계_ERP\stop_automation.bat`

---

## 설정 방법

### A. 기존 작업 삭제

```powershell
schtasks /delete /tn "ERP 자동화 일일 재시작" /f
```

### B. 시작 작업 생성 (월~토 07:00)

```powershell
schtasks /create /tn "ERP 자동화 시작" /tr "C:\Users\DSAI\Desktop\회계_ERP\start_automation.bat" /sc weekly /d MON,TUE,WED,THU,FRI,SAT /st 07:00 /ru "DESKTOP-67OI68H\DSAI" /rl HIGHEST
```

### C. 종료 작업 생성 (월~금 18:00)

```powershell
schtasks /create /tn "ERP 자동화 종료 (평일)" /tr "C:\Users\DSAI\Desktop\회계_ERP\stop_automation.bat" /sc weekly /d MON,TUE,WED,THU,FRI /st 18:00 /ru "DESKTOP-67OI68H\DSAI" /rl HIGHEST
```

### D. 종료 작업 생성 (토 14:00)

```powershell
schtasks /create /tn "ERP 자동화 종료 (토요일)" /tr "C:\Users\DSAI\Desktop\회계_ERP\stop_automation.bat" /sc weekly /d SAT /st 14:00 /ru "DESKTOP-67OI68H\DSAI" /rl HIGHEST
```

---

## 확인 방법

```powershell
# 모든 ERP 관련 작업 조회
schtasks /query /fo LIST /v | Select-String -Pattern "ERP" -Context 0,10

# 개별 작업 확인
schtasks /query /tn "ERP 자동화 시작" /fo LIST
schtasks /query /tn "ERP 자동화 종료 (평일)" /fo LIST
schtasks /query /tn "ERP 자동화 종료 (토요일)" /fo LIST
```

---

## 수동 테스트

### 시작 테스트
```powershell
schtasks /run /tn "ERP 자동화 시작"
```

### 종료 테스트
```powershell
schtasks /run /tn "ERP 자동화 종료 (평일)"
```

---

## 중복 실행 방지 설정

작업 스케줄러 GUI에서 각 작업의 속성 → 설정 탭:
- ☑ "작업이 이미 실행 중이면 새 인스턴스 시작 안 함"

---

## 예상 동작

**월~금:**
- 07:00: 프로그램 시작
- 07:00~17:50: 30분마다 자동화 사이클 실행
- 17:50~18:00: 업무 시간 외 대기
- 18:00: 프로그램 강제 종료

**토요일:**
- 07:00: 프로그램 시작
- 07:00~14:00: 30분마다 자동화 사이클 실행
- 14:00: 프로그램 강제 종료

**일요일:**
- 실행 안 함
