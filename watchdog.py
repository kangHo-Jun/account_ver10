#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
하트비트 감시 스크립트 (Watchdog)
- heartbeat.txt 파일을 주기적으로 확인
- 1시간 이상 업데이트 없으면 프로세스 정지로 판단
- 알림 또는 자동 재시작 수행
"""

import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# 설정
HEARTBEAT_FILE = Path("heartbeat.txt")
CHECK_INTERVAL = 300  # 5분마다 체크
TIMEOUT_MINUTES = 60  # 60분 동안 업데이트 없으면 정지로 판단

def check_heartbeat():
    """하트비트 파일 확인"""
    if not HEARTBEAT_FILE.exists():
        return None, "하트비트 파일이 없습니다"

    try:
        # 파일 수정 시간 확인
        last_modified = datetime.fromtimestamp(HEARTBEAT_FILE.stat().st_mtime)
        time_diff = datetime.now() - last_modified

        # 파일 내용 읽기
        with open(HEARTBEAT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        return time_diff, content
    except Exception as e:
        return None, f"하트비트 파일 읽기 실패: {e}"

def kill_and_restart():
    """프로세스 종료 및 재시작"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 프로세스 재시작 시도...")

    try:
        # 모든 pythonw 프로세스 종료
        subprocess.run(['taskkill', '/F', '/IM', 'pythonw.exe', '/T'],
                      capture_output=True, text=True)
        print("  - 기존 프로세스 종료 완료")

        # 5초 대기
        time.sleep(5)

        # 프로그램 재시작
        subprocess.Popen(['pythonw', 'main.py'],
                        creationflags=subprocess.CREATE_NO_WINDOW)
        print("  - 새 프로세스 시작 완료")

        return True
    except Exception as e:
        print(f"  - 재시작 실패: {e}")
        return False

def main():
    """메인 감시 루프"""
    print("=" * 70)
    print("하트비트 감시 프로그램 시작")
    print(f"- 체크 간격: {CHECK_INTERVAL}초")
    print(f"- 타임아웃: {TIMEOUT_MINUTES}분")
    print("=" * 70)
    print()

    consecutive_errors = 0

    while True:
        try:
            time_diff, content = check_heartbeat()
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if time_diff is None:
                print(f"[{now_str}] [ERROR] {content}")
                consecutive_errors += 1

                # 3회 연속 에러 시 재시작 시도
                if consecutive_errors >= 3:
                    print(f"[{now_str}] [ALERT] 연속 {consecutive_errors}회 에러 - 재시작 시도")
                    if kill_and_restart():
                        consecutive_errors = 0
                        time.sleep(60)  # 재시작 후 1분 대기
            else:
                consecutive_errors = 0

                if time_diff > timedelta(minutes=TIMEOUT_MINUTES):
                    # 타임아웃 발생
                    print(f"[{now_str}] [ALERT] 프로세스 정지 감지!")
                    print(f"  - 마지막 업데이트: {time_diff.total_seconds()/60:.1f}분 전")
                    print(f"  - 내용:\n{content}")
                    print()

                    # 자동 재시작
                    if kill_and_restart():
                        time.sleep(60)  # 재시작 후 1분 대기
                else:
                    # 정상 작동
                    print(f"[{now_str}] [OK] 프로세스 정상 작동 (마지막 업데이트: {time_diff.total_seconds():.0f}초 전)")

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n감시 프로그램 종료")
            break
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] 예외 발생: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
