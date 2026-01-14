import openpyxl

def analyze():
    # 로그 데이터 (상위 26건의 일부)
    log_customers = [
        "감사합니다", "인테리어 웍스", "(주)안양철물만돌이", "감사합니다", "감사합니다", 
        "(주) 맑은창", "감사합니다", "리스토어디자인", "감사합니다", "감사합니다",
        "감사합니다", "감사합니다", "감사합니다", "(주)모드니퍼스트", "동아인테리어",
        "그린인테리어(내손동)", "감사합니다", "사팔우드", "동아인테리어", "감사합니다",
        "(주)모드니퍼스트", "나래설비", "감사합니다", "나래설비", "다함인테리어", "주식회사 스페이스류"
    ]
    
    wb = openpyxl.load_workbook('1CIY6HQXG9KNMPF.xlsx', data_only=True)
    ws = wb.active
    
    excel_v_count = 0
    excel_matches = []
    
    for row in ws.iter_rows(min_row=3):
        customer = str(row[3].value).strip() if row[3].value else ""
        reflected = str(row[10].value).strip() if row[10].value else ""
        
        if reflected == 'V':
            excel_v_count += 1
            if customer in log_customers:
                excel_matches.append(customer)
                
    print(f"Excel Total 'V' (Reflected) count: {excel_v_count}")
    print(f"Matches with Logged 26 records: {len(excel_matches)}")
    print(f"Unique Matches: {set(excel_matches)}")

if __name__ == "__main__":
    analyze()
