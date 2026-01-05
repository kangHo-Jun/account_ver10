# Architecture Decisions (ADR)

## ADR 1: Modularization of Ecount Automation
- **Status**: Proposed
- **Context**: 현재 `main.py`에 모든 로직(로그인, 브라우저 관리, 데이터 파싱, 업로드)이 집중되어 있어 유지보수가 어렵습니다.
- **Decision**: 기능을 독립적인 모듈로 분리하여 V9 수준의 아키텍처로 업그레이드합니다.
- **Consequences**:
    - 코드 재사용성 향상
    - 테스트 용이성 증가
    - 에러 핸들링 고도화 가능
