# -*- coding: utf-8 -*-
"""이메일 발송 테스트 스크립트"""
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from modules.notifier import NotifierModule

# 테스트 통계
test_stats = {
    'total': 10,
    'success': 9,
    'failure': 1,
    'count': 25
}

notifier = NotifierModule()

print("=" * 60)
print("이메일 발송 테스트 시작")
print("=" * 60)
print(f"발신: {notifier.sender}")
print(f"수신: {notifier.recipient}")
print(f"활성화: {notifier.enabled}")
print()

# 일일 요약 리포트 발송
result = notifier.send_summary_notification(test_stats)

if result:
    print("이메일 발송 성공!")
    print(f"{notifier.recipient}의 받은편지함을 확인하세요.")
else:
    print("이메일 발송 실패")
    print("로그를 확인하세요.")

print("=" * 60)
