#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""1월 13일 로그 분석 스크립트"""

import re
from collections import Counter, defaultdict
from datetime import datetime

def analyze_jan13_logs():
    log_file = 'logs/v9_20260107_100044.log'

    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 통계 변수
    jan13_data = []
    cycles_completed = []
    warnings = []
    errors = []
    uploads = []

    for line in lines:
        # 1월 13일 데이터 처리 건수
        if '2026/01/13' in line:
            jan13_data.append(line)

            # 승인번호 누락 경고
            if '⚠️ 승인번호를 가져오지 못함' in line:
                match = re.search(r'일시: (2026/01/13 .*?) / 고객: ([^)]+)', line)
                if match:
                    warnings.append({
                        'time': match.group(1),
                        'customer': match.group(2)
                    })

        # 사이클 완료
        if '✅ 사이클 완료' in line:
            match = re.search(r'\[(\d{2}:\d{2}:\d{2})\].*?완료 \((\d+)건', line)
            if match:
                cycles_completed.append({
                    'time': match.group(1),
                    'count': int(match.group(2))
                })

        # 에러
        if '[ERROR]' in line:
            errors.append(line)

        # 업로드 성공
        if '✅ 저장 성공 확정' in line:
            match = re.search(r'(\d+)건 업로드', line)
            if match:
                uploads.append(int(match.group(1)))

    # 결과 출력
    print("=" * 70)
    print("[1\uc6d4 13\uc77c \ub85c\uadf8 \ubd84\uc11d \ub9ac\ud3ec\ud2b8]")
    print("=" * 70)
    print()

    print("[1] \uae30\ubcf8 \ud1b5\uacc4")
    print(f"  • 1월 13일 관련 로그 라인: {len(jan13_data)}건")
    print(f"  • 총 완료된 사이클: {len(cycles_completed)}건")
    print(f"  • 총 업로드 건수: {sum(uploads)}건")
    print(f"  • 총 에러 발생: {len(errors)}건")
    print()

    print("[2] \uc2b9\uc778\ubc88\ud638 \ub204\ub77d \uacbd\uace0 (1\uc6d4 13\uc77c)")
    print(f"  • 총 {len(warnings)}건")
    print()

    # 시간대별 분석
    if warnings:
        hour_counter = defaultdict(list)
        for w in warnings:
            hour = w['time'].split()[1].split(':')[0]
            hour_counter[hour].append(w['customer'])

        print("  시간대별 분포:")
        for hour in sorted(hour_counter.keys()):
            customers = hour_counter[hour]
            print(f"    {hour}시: {len(customers)}건")
            for customer in customers[:3]:  # 상위 3개만 표시
                print(f"      - {customer}")
            if len(customers) > 3:
                print(f"      ... 외 {len(customers)-3}건")
        print()

    # 사이클 처리량 통계
    if cycles_completed:
        total_processed = sum(c['count'] for c in cycles_completed)
        avg_per_cycle = total_processed / len(cycles_completed)

        print("[3] \uc0ac\uc774\ud074 \ucc98\ub9ac \ud1b5\uacc4")
        print(f"  • 총 처리 건수: {total_processed}건")
        print(f"  • 평균 사이클당 처리: {avg_per_cycle:.1f}건")
        print(f"  • 최대 처리량: {max(c['count'] for c in cycles_completed)}건")
        print(f"  • 최소 처리량: {min(c['count'] for c in cycles_completed)}건")
        print()

    # 에러 분석
    if errors:
        print("[4] \uc5d0\ub7ec \ub85c\uadf8")
        for error in errors[:5]:
            print(f"  {error.strip()}")
        if len(errors) > 5:
            print(f"  ... 외 {len(errors)-5}건")
        print()

    # 승인번호 누락 고객 통계
    if warnings:
        customer_counter = Counter([w['customer'] for w in warnings])
        print("[5] \uc2b9\uc778\ubc88\ud638 \ub204\ub77d \ube48\ub3c4 \ub192\uc740 \uace0\uac1d (Top 10)")
        for customer, count in customer_counter.most_common(10):
            print(f"  • {customer}: {count}건")
        print()

    print("=" * 70)
    print("[\ubd84\uc11d \uc644\ub8cc]")
    print("=" * 70)

if __name__ == "__main__":
    analyze_jan13_logs()
