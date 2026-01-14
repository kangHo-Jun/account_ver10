#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""1월 14일 로그 통합 분석 스크립트 (재시작 전후 비교 포함)"""

import re
from collections import Counter, defaultdict
from datetime import datetime

def normalize_customer_name(customer):
    """고객명 정규화 (감사합니다 패턴 통합)"""
    if '감사합니다' in customer:
        return '감사합니다 (전화번호 패턴)'
    return customer

def analyze_jan14_logs():
    log_files = [
        'logs/v9_20260107_100044.log',  # 재시작 전
        'logs/v9_20260114_144847.log'   # 재시작 후
    ]

    # 전체 데이터 수집
    all_lines = []
    jan14_data = []
    cycles_completed = []
    warnings = []
    errors = []
    uploads = []

    restart_detected = False
    restart_time = None

    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                all_lines.extend(lines)

                # 재시작 감지 (새 로그 파일 시작 시)
                if 'v9_20260114' in log_file:
                    restart_detected = True
                    for line in lines:
                        if '시스템 재시작' in line or '웹 자동화 V9.5 실행' in line:
                            match = re.search(r'\[(\d{2}:\d{2}:\d{2})\]', line)
                            if match:
                                restart_time = match.group(1)
                                break
                    if not restart_time:
                        restart_time = "14:48:47"  # 로그 파일명 기준

                for line in lines:
                    # 1월 14일 데이터
                    if '2026/01/14' in line:
                        jan14_data.append(line)

                        # 승인번호 누락 경고
                        if '승인번호를 가져오지 못함' in line:
                            match = re.search(r'일시: (2026/01/14 .*?) / 고객: ([^)]+)', line)
                            if match:
                                warnings.append({
                                    'time': match.group(1),
                                    'customer': normalize_customer_name(match.group(2)),
                                    'log_file': log_file
                                })

                    # 새 로그 파일은 전체가 1월 14일 데이터
                    if 'v9_20260114' in log_file:
                        # 사이클 완료
                        if '사이클 완료' in line:
                            match = re.search(r'\[(\d{2}:\d{2}:\d{2})\].*?완료 \((\d+)건', line)
                            if match:
                                cycles_completed.append({
                                    'time': match.group(1),
                                    'count': int(match.group(2)),
                                    'log_file': log_file
                                })

                        # 에러
                        if '[ERROR]' in line:
                            errors.append({'line': line, 'log_file': log_file})

                        # 업로드 성공
                        if '저장 성공 확정' in line:
                            match = re.search(r'(\d+)건 업로드', line)
                            if match:
                                uploads.append({'count': int(match.group(1)), 'log_file': log_file})
                    else:
                        # 구 로그 파일: 14:47 사이클이 1월 14일 마지막 사이클
                        if '사이클 완료' in line:
                            match = re.search(r'\[(\d{2}:\d{2}:\d{2})\].*?완료 \((\d+)건', line)
                            if match:
                                time_str = match.group(1)
                                # 14:47 사이클은 1월 14일 (로그에서 확인됨)
                                if time_str.startswith('14:47'):
                                    cycles_completed.append({
                                        'time': match.group(1),
                                        'count': int(match.group(2)),
                                        'log_file': log_file
                                    })

        except FileNotFoundError:
            print(f"경고: {log_file} 파일을 찾을 수 없습니다.")
            continue

    # 재시작 전후 분리
    cycles_before = [c for c in cycles_completed if 'v9_20260107' in c['log_file']]
    cycles_after = [c for c in cycles_completed if 'v9_20260114' in c['log_file']]

    warnings_before = [w for w in warnings if 'v9_20260107' in w['log_file']]
    warnings_after = [w for w in warnings if 'v9_20260114' in w['log_file']]

    # 현재 시간
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    # 결과 출력
    print("=" * 70)
    print("[1\uc6d4 14\uc77c \ub85c\uadf8 \ubd84\uc11d \ub9ac\ud3ec\ud2b8]")
    print(f"\ubd84\uc11d \uc2dc\uac04: {now.strftime('%Y-%m-%d %H:%M')}")
    print("\ubd84\uc11d \ubc94\uc704: 06:00 ~ \ud604\uc7ac (\uc5c5\ubb34 \uc2dc\uac04 \uc911)")
    print("=" * 70)
    print()

    print("[1] \uae30\ubcf8 \ud1b5\uacc4")
    print(f"  1\uc6d4 14\uc77c \uad00\ub828 \ub85c\uadf8 \ub77c\uc778: {len(jan14_data)}\uac74")
    print(f"  \ucd1d \uc644\ub8cc\ub41c \uc0ac\uc774\ud074: {len(cycles_completed)}\uac74")
    total_uploads = sum(c['count'] for c in cycles_completed)
    uploads_before = sum(c['count'] for c in cycles_before)
    uploads_after = sum(c['count'] for c in cycles_after)
    print(f"  \ucd1d \uc5c5\ub85c\ub4dc \uac74\uc218: {total_uploads}\uac74 (\uc7ac\uc2dc\uc791 \uc804: {uploads_before}\uac74, \uc7ac\uc2dc\uc791 \ud6c4: {uploads_after}\uac74)")
    print(f"  \ucd1d \uc5d0\ub7ec \ubc1c\uc0dd: {len(errors)}\uac74")
    print()

    print("[2] \uc2b9\uc778\ubc88\ud638 \ub204\ub77d \uacbd\uace0")
    print(f"  \ucd1d {len(warnings)}\uac74")
    if warnings:
        hour_counter = defaultdict(lambda: {'오전': 0, '오후': 0})
        for w in warnings:
            time_str = w['time']
            if '\uc624\uc804' in time_str:
                hour = time_str.split()[1].split(':')[0]
                hour_counter[hour]['\uc624\uc804'] += 1
            elif '\uc624\ud6c4' in time_str:
                hour = time_str.split()[1].split(':')[0]
                hour_counter[hour]['\uc624\ud6c4'] += 1

        morning_count = sum(w['time'].count('\uc624\uc804') for w in warnings)
        afternoon_count = sum(w['time'].count('\uc624\ud6c4') for w in warnings)

        print(f"  \uc2dc\uac04\ub300\ubcc4 \ubd84\ud3ec:")
        print(f"    \uc624\uc804 (06:00-12:00): {morning_count}\uac74")
        print(f"    \uc624\ud6c4 (12:00-{current_time}): {afternoon_count}\uac74")
    print()

    if cycles_completed:
        avg = total_uploads / len(cycles_completed)
        print("[3] \uc0ac\uc774\ud074 \ucc98\ub9ac \ud1b5\uacc4")
        print(f"  \ucd1d \ucc98\ub9ac: {total_uploads}\uac74")
        print(f"  \ud3c9\uade0: {avg:.1f}\uac74/\uc0ac\uc774\ud074")
        print(f"  \ucd5c\ub300: {max(c['count'] for c in cycles_completed)}\uac74")
        print(f"  \ucd5c\uc18c: {min(c['count'] for c in cycles_completed)}\uac74")
        print()

    print("[4] \uc8fc\uc694 \uc2dc\uc2a4\ud15c \uc774\ubca4\ud2b8")
    if cycles_before:
        last_cycle_before = max(cycles_before, key=lambda x: x['time'])
        print(f"  {last_cycle_before['time']} - \ub9c8\uc9c0\ub9c9 \uc815\uc0c1 \uc0ac\uc774\ud074 \uc644\ub8cc ({last_cycle_before['count']}\uac74 \uc5c5\ub85c\ub4dc)")
    if restart_time:
        print(f"  14:47~14:48 - \uc2dc\uc2a4\ud15c \uc885\ub8cc/\uc7ac\uc2dc\uc791 (Event loop \uc624\ub958 \ud574\uacb0)")
        print(f"  {restart_time} - \uc2dc\uc2a4\ud15c \uc7ac\uc2dc\uc791 (V9.5 production \ubaa8\ub4dc)")
    if cycles_after:
        first_cycle_after = min(cycles_after, key=lambda x: x['time'])
        print(f"  {first_cycle_after['time']} - \uc7ac\uc2dc\uc791 \ud6c4 \uccab \uc0ac\uc774\ud074 \uc644\ub8cc ({first_cycle_after['count']}\uac74 \uc5c5\ub85c\ub4dc)")
        # 다음 사이클 예상 (30분 간격)
        last_time = datetime.strptime(first_cycle_after['time'], '%H:%M:%S')
        next_time = datetime(now.year, now.month, now.day, last_time.hour, last_time.minute)
        from datetime import timedelta
        next_time += timedelta(minutes=30)
        print(f"  {next_time.strftime('%H:%M')} - \ub2e4\uc74c \uc0ac\uc774\ud074 \uc608\uc0c1 \uc2dc\uac04")
    print()

    if warnings:
        customer_counter = Counter([w['customer'] for w in warnings])
        print("[5] \uc2b9\uc778\ubc88\ud638 \ub204\ub77d \ube48\ub3c4 Top 10")
        for i, (customer, count) in enumerate(customer_counter.most_common(10), 1):
            print(f"  {i}. {customer}: {count}\uac74")
        print()

    print("[6] \ud604\uc7ac \uc0c1\ud0dc")
    print("  \uc2dc\uc2a4\ud15c \uc0c1\ud0dc: \uc815\uc0c1 \uc791\ub3d9 \uc911")
    if cycles_after:
        last_cycle = max(cycles_after, key=lambda x: x['time'])
        print(f"  \ub9c8\uc9c0\ub9c9 \uc0ac\uc774\ud074: {last_cycle['time']} ({last_cycle['count']}\uac74 \ucc98\ub9ac)")
    print("  \ub300\uae30 \ubaa8\ub4dc: 30\ubd84 \uac04\uaca9 \uc790\ub3d9 \uc2e4\ud589")
    print()

    print("[7] \uc7ac\uc2dc\uc791 \uc804\ud6c4 \ube44\uad50")
    print(f"  \uc7ac\uc2dc\uc791 \uc804 (06:00~14:47):")
    print(f"    - \uc0ac\uc774\ud074 \uc218: {len(cycles_before)}\uac74")
    print(f"    - \uc5c5\ub85c\ub4dc \uac74\uc218: {uploads_before}\uac74")
    print(f"    - \uc2b9\uc778\ubc88\ud638 \ub204\ub77d: {len(warnings_before)}\uac74")
    print(f"  \uc7ac\uc2dc\uc791 \ud6c4 (14:48~{current_time}):")
    print(f"    - \uc0ac\uc774\ud074 \uc218: {len(cycles_after)}\uac74")
    print(f"    - \uc5c5\ub85c\ub4dc \uac74\uc218: {uploads_after}\uac74")
    print(f"    - \uc2b9\uc778\ubc88\ud638 \ub204\ub77d: {len(warnings_after)}\uac74")
    print(f"    - \uc0c1\ud0dc: \uc815\uc0c1")
    print()

    print("=" * 70)
    print("[\ubd84\uc11d \uc644\ub8cc]")
    print("=" * 70)

if __name__ == "__main__":
    analyze_jan14_logs()
