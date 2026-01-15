import json
from pathlib import Path
from core.logger import logger

class TransformerModule:
    def __init__(self):
        self.records_file = Path("uploaded_records.json")

    def load_uploaded_records(self) -> set:
        if self.records_file.exists():
            try:
                with open(self.records_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except:
                return set()
        return set()

    def save_uploaded_records(self, records: set):
        with open(self.records_file, 'w', encoding='utf-8') as f:
            json.dump(list(records), f, ensure_ascii=False, indent=2)

    def transform(self, raw_data: list, reflected_nos: set = None) -> tuple:
        """입금보고서 형식으로 변환 + 실시간/로컬 중복 체크"""
        logger.info("[TRANSFORM] 데이터 변환 중...")

        uploaded_records = self.load_uploaded_records()
        logger.info(f"   기존 업로드 기록: {len(uploaded_records)}건")

        paste_rows = []
        new_record_keys = []

        # 통계 추적
        stats = {
            'total_raw': len(raw_data),
            'excluded_invalid': 0,
            'excluded_duplicate_local': 0,
            'excluded_duplicate_erp': 0,
            'cancellations': 0,
            'normal_transactions': 0
        }

        for row in raw_data:
            record_key = row['date_raw']
            auth_no = row.get('auth_no', '')
            status = row.get('status', '')
            customer = row.get('customer', '')
            amount_val = row.get('amount', '')

            # [V13] 필수값(금액/고객명) 누락 검증만 수행
            # 참고: ERP 페이지에서 이미 '승인/취소'만 필터링되어 표시됨 (계정 설정)
            if not customer or not amount_val:
                logger.info(f"   [SKIP] 데이터 제외: 필수값 누락 (일시: {record_key})")
                stats['excluded_invalid'] += 1
                continue

            # 1. 로컬 기록 대조 (작업 일시 기준)
            if record_key in uploaded_records:
                stats['excluded_duplicate_local'] += 1
                continue

            # 2. 실시간 ERP '회계반영' 내역 대조 (승인번호 기준)
            if reflected_nos and auth_no and auth_no in reflected_nos:
                logger.info(f"   [DUP] 실시간 중복 차단: 승인번호 {auth_no} (이미 회계반영됨)")
                stats['excluded_duplicate_erp'] += 1
                continue

            if not auth_no:
                logger.warning(f"   [WARN] 승인번호를 가져오지 못함 (일시: {record_key} / 고객: {customer})")

            # 날짜 변환 (ERP 표준 / 형식으로 복구)
            date_part = row['date_raw'].split(' ')[0] # 2026/01/06 형태 유지
            amount_raw = row['amount'].replace(',', '')
            
            if not amount_raw:
                continue

            # 2. '취소'인 경우 금액에 마이너스(-) 추가
            if status == '취소':
                stats['cancellations'] += 1
                if not amount_raw.startswith('-'):
                    amount = f"-{amount_raw}"
                    logger.info(f"   [CANCEL] '취소' 상태 감지: 금액 {amount_raw} -> {amount} 변환")
                else:
                    amount = amount_raw
            else:
                stats['normal_transactions'] += 1
                amount = amount_raw

            customer = row['customer']
            account_raw = row['account']

            # 3. 카드사 명칭 통일 및 기본값 설정
            if not account_raw or '카드' in account_raw:
                account = '카드사'
                if not account_raw:
                    logger.info(f"   [WARN] '입금계좌코드'(매입사) 누락 감지: 기본값 '카드사' 할당")
                else:
                    logger.info(f"   [CARD] 카드사 명칭 통일: {account_raw} -> {account}")
            else:
                account = account_raw

            # 입금보고서 행 구성
            paste_row = [
                date_part,      # A: 일자
                "",             # B: 순번
                "",             # C: 회계전표No.
                account,        # D: 입금계좌코드
                "1089",         # E: 계정코드
                "",             # F: 거래처코드
                customer,       # G: 거래처명
                amount,         # H: 금액
                "",             # I: 수수료
                f"카드결제 {customer}", # J: 적요명
                "",             # K: 프로젝트
                ""              # L: 부서
            ]

            paste_rows.append(paste_row)
            new_record_keys.append(record_key)

        # 상세 처리 결과 로깅
        logger.info("=" * 60)
        logger.info("[SUMMARY] 사이클 처리 요약")
        logger.info(f"   [IN] 총 조회 데이터: {stats['total_raw']}건")
        logger.info(f"   [OUT] 업로드 대상: {len(paste_rows)}건")

        total_excluded = stats['excluded_invalid'] + stats['excluded_duplicate_local'] + stats['excluded_duplicate_erp']
        logger.info(f"   [SKIP] 제외된 데이터: {total_excluded}건")
        if total_excluded > 0:
            logger.info(f"      - 중복(로컬): {stats['excluded_duplicate_local']}건")
            logger.info(f"      - 중복(ERP 회계반영): {stats['excluded_duplicate_erp']}건")
            logger.info(f"      - 무효 데이터: {stats['excluded_invalid']}건")

        if len(paste_rows) > 0:
            logger.info(f"   [DETAIL] 업로드 내역:")
            logger.info(f"      - 일반 거래: {stats['normal_transactions']}건")
            logger.info(f"      - 취소 거래: {stats['cancellations']}건")
        logger.info("=" * 60)

        return paste_rows, new_record_keys, stats
