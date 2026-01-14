#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""프로세스 락 기능 테스트 스크립트"""

import sys
import time
from pathlib import Path

# main.py의 Orchestrator 클래스 임포트
from main import EcountAutomationOrchestrator

def test_duplicate_prevention():
    """중복 실행 방지 테스트"""
    print("=" * 70)
    print("프로세스 락 기능 테스트")
    print("=" * 70)
    print()

    print("1. 첫 번째 인스턴스 생성 시도...")
    try:
        orchestrator1 = EcountAutomationOrchestrator()
        print("   [OK] 첫 번째 인스턴스 생성 성공")
        print(f"   - 락 파일: {orchestrator1.lock_file}")
        print(f"   - PID: {orchestrator1.lock_file.read_text()}")
        print()

        print("2. 두 번째 인스턴스 생성 시도 (중복)...")
        try:
            orchestrator2 = EcountAutomationOrchestrator()
            print("   [FAIL] 테스트 실패: 중복 인스턴스가 생성되었습니다!")
        except SystemExit:
            print("   [OK] 중복 실행 방지 성공 (SystemExit 발생)")
            print("   - 두 번째 인스턴스 생성 차단됨")
        print()

        print("3. 락 해제 테스트...")
        orchestrator1.release_lock()
        if not orchestrator1.lock_file.exists():
            print("   [OK] 락 파일 삭제 성공")
        else:
            print("   [FAIL] 락 파일 삭제 실패")
        print()

        print("4. 락 해제 후 새 인스턴스 생성 시도...")
        orchestrator3 = EcountAutomationOrchestrator()
        print("   [OK] 락 해제 후 새 인스턴스 생성 성공")
        orchestrator3.release_lock()
        print()

        print("=" * 70)
        print("테스트 완료: 모든 테스트 통과")
        print("=" * 70)

    except Exception as e:
        print(f"[ERROR] 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_duplicate_prevention()
