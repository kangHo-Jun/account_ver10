# Architecture Decisions (ADR)

## ADR 1: Modularization of Ecount Automation
- **Status**: Completed
- **Context**: 현재 `main.py`에 모든 로직(로그인, 브라우저 관리, 데이터 파싱, 업로드)이 집중되어 있어 유지보수가 어렵습니다.
- **Decision**: 기능을 독립적인 모듈로 분리하여 V9 수준의 아키텍처로 업그레이드합니다.
- **Consequences**:
    - 코드 재사용성 향상
    - 테스트 용이성 증가
    - 에러 핸들링 고도화 가능

## ADR 2: Sleep Mode Prevention (Keep-Alive)
- **Status**: Proposed
- **Context**: PC가 절전 모드에 진입하면 백그라운드에서 실행 중인 자동화 프로세스가 중단되어 주기적인 작업(30분 간격)이 불가능해집니다.
- **Decision**: Windows API (`SetThreadExecutionState`)를 호출하여 애플리케이션이 실행 중인 동안 시스템이 절전 모드(System Sleep)로 진입하는 것을 방지합니다.
- **Consequences**:
    - 업무 시간 동안 중단 없는 자동화 보장.
    - 밤(업무 외 시간)에는 해당 설정을 해제하여 전력을 절약할 수 있도록 설계.
