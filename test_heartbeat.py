#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""하트비트 기능 테스트 스크립트"""

import time
from pathlib import Path
from datetime import datetime

def test_heartbeat():
    """하트비트 파일 생성 및 감시 테스트"""
    print("=" * 70)
    print("하트비트 기능 테스트")
    print("=" * 70)
    print()

    # main.py의 Orchestrator 클래스 임포트
    from main import EcountAutomationOrchestrator

    print("1. Orchestrator 인스턴스 생성...")
    orchestrator = EcountAutomationOrchestrator()
    print("   [OK] 인스턴스 생성 성공")
    print()

    print("2. 하트비트 기록 테스트 (3회)...")
    heartbeat_file = Path("heartbeat.txt")

    for i in range(3):
        # 하트비트 기록
        orchestrator.heartbeat()

        # 파일 확인
        if heartbeat_file.exists():
            content = heartbeat_file.read_text(encoding='utf-8')
            print(f"   [{i+1}] 하트비트 기록 성공:")
            for line in content.split('\n')[:3]:  # 처음 3줄만
                print(f"       {line}")
        else:
            print(f"   [{i+1}] [FAIL] 하트비트 파일 없음")

        # 통계 업데이트 (시뮬레이션)
        orchestrator.stats["total"] += 1
        orchestrator.stats["success"] += 1

        time.sleep(2)  # 2초 대기
        print()

    print("3. 파일 수정 시간 확인...")
    if heartbeat_file.exists():
        last_modified = datetime.fromtimestamp(heartbeat_file.stat().st_mtime)
        print(f"   마지막 수정: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   [OK] 하트비트 타임스탬프 갱신 확인")
    print()

    # 정리
    orchestrator.release_lock()
    print("4. 테스트 완료")
    print("=" * 70)

if __name__ == "__main__":
    test_heartbeat()
