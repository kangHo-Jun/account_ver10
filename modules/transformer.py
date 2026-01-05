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

    def transform(self, raw_data: list) -> tuple:
        """입금보고서 형식으로 변환 + 중복 체크"""
        logger.info("🔄 데이터 변환 중...")
        
        uploaded_records = self.load_uploaded_records()
        logger.info(f"   기존 업로드 기록: {len(uploaded_records)}건")

        paste_rows = []
        new_record_keys = []

        for row in raw_data:
            record_key = row['date_raw']
            if record_key in uploaded_records:
                continue

            status = row.get('status', '')
            
            # 1. '승인실패' 또는 '취소실패'인 경우 해당 행 제외
            if status in ['승인실패', '취소실패']:
                logger.info(f"   ⏩ {status} 행 제외 (Key: {record_key})")
                continue

            # 날짜 변환
            date_part = row['date_raw'].split(' ')[0].replace('/', '-')
            amount_raw = row['amount'].replace(',', '')
            
            if not amount_raw:
                continue

            # 2. '취소'인 경우 금액에 마이너스(-) 추가
            if status == '취소':
                # 이미 마이너스가 없는 경우에만 추가 (혹시 모를 중복 방지)
                if not amount_raw.startswith('-'):
                    amount = f"-{amount_raw}"
                    logger.info(f"   ➖ '취소' 상태 감지: 금액 {amount_raw} -> {amount} 변환")
                else:
                    amount = amount_raw
            else:
                amount = amount_raw

            customer = row['customer']
            account_raw = row['account']

            # 3. 카드사 명칭 통일: '카드'가 포함된 경우 '카드사'로 변환
            if '카드' in account_raw:
                account = '카드사'
                logger.info(f"   💳 카드사 명칭 통일: {account_raw} -> {account}")
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

        logger.info(f"✅ 새 데이터: {len(paste_rows)}건")
        return paste_rows, new_record_keys
