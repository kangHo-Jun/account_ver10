import json
from pathlib import Path
from core.logger import logger


class PGTransformerModule:
    def __init__(self):
        self.records_file = Path("uploaded_records_pg.json")

    def load_uploaded_records(self) -> set:
        if self.records_file.exists():
            try:
                with open(self.records_file, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()

    def save_uploaded_records(self, records: set):
        with open(self.records_file, "w", encoding="utf-8") as f:
            json.dump(list(records), f, ensure_ascii=False, indent=2)

    def transform(self, raw_data: list) -> tuple:
        """PG 매출조회 결과를 입금보고서 업로드 형식으로 변환"""
        logger.info("[PG][TRANSFORM] 데이터 변환 중...")

        uploaded_records = self.load_uploaded_records()
        logger.info(f"[PG][INFO] 기존 업로드 기록: {len(uploaded_records)}건")

        paste_rows = []
        new_record_keys = []
        stats = {
            "total_raw": len(raw_data),
            "excluded_invalid": 0,
            "excluded_duplicate_local": 0,
            "cancellations": 0,
            "normal_transactions": 0,
        }

        for row in raw_data:
            date_raw = row.get("date_raw", "").strip()
            customer = row.get("customer", "").strip()
            amount_val = row.get("amount", "").strip()
            account_raw = row.get("account", "").strip()
            status = row.get("status", "").strip()

            record_key = "|".join([date_raw, customer, amount_val, account_raw, status])

            if not date_raw or not customer or not amount_val:
                logger.info(f"[PG][SKIP] 필수값 누락: {record_key}")
                stats["excluded_invalid"] += 1
                continue

            if record_key in uploaded_records:
                stats["excluded_duplicate_local"] += 1
                continue

            amount_raw = "".join(amount_val.split()).replace(",", "")
            if not amount_raw:
                stats["excluded_invalid"] += 1
                continue

            if status == "취소" and not amount_raw.startswith("-"):
                amount = f"-{amount_raw}"
                stats["cancellations"] += 1
                logger.info(f"[PG][CANCEL] 취소 거래 변환: {amount_raw} -> {amount}")
            else:
                amount = amount_raw
                stats["normal_transactions"] += 1

            account = account_raw or "카드사"
            date_part = date_raw.split(" ")[0]

            paste_rows.append(
                [
                    date_part,
                    "",
                    "",
                    account,
                    "1089",
                    "",
                    customer,
                    amount,
                    "",
                    f"PG결제 {customer}",
                    "",
                    "",
                ]
            )
            new_record_keys.append(record_key)

        logger.info("=" * 60)
        logger.info("[PG][SUMMARY] 사이클 처리 요약")
        logger.info(f"[PG][IN] 총 조회 데이터: {stats['total_raw']}건")
        logger.info(f"[PG][OUT] 업로드 대상: {len(paste_rows)}건")
        logger.info(
            f"[PG][SKIP] 제외된 데이터: {stats['excluded_invalid'] + stats['excluded_duplicate_local']}건"
        )
        logger.info(f"[PG][SKIP] 중복(로컬): {stats['excluded_duplicate_local']}건")
        logger.info(f"[PG][SKIP] 무효 데이터: {stats['excluded_invalid']}건")
        logger.info(f"[PG][DETAIL] 일반 거래: {stats['normal_transactions']}건")
        logger.info(f"[PG][DETAIL] 취소 거래: {stats['cancellations']}건")
        logger.info("=" * 60)

        return paste_rows, new_record_keys, stats
