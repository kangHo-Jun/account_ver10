
import sys
import os
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.append(os.getcwd())

from modules.transformer import TransformerModule

def test_cancellation_formatting():
    transformer = TransformerModule()
    
    # 1. 다양한 공백이 섞인 취소 건 데이터 시뮬레이션
    mock_data = [
        {
            'date_raw': '2026/01/20 09:00:00',
            'customer': '테스트고객1',
            'amount': ' 400 ',      # 일반 공백
            'status': '취소 ',      # 뒤에 공백
            'account': '카드사'
        },
        {
            'date_raw': '2026/01/20 09:01:00',
            'customer': '테스트고객2',
            'amount': '1,200\xa0',   # Non-breaking space (&nbsp;)
            'status': ' 취소',      # 앞에 공백
            'account': '카드사'
        },
        {
            'date_raw': '2026/01/20 09:02:00',
            'customer': '테스트고객3',
            'amount': ' 5,000 ',
            'status': '취소',       # 정상
            'account': '카드사'
        }
    ]
    
    print("=" * 60)
    print("취소 건 마이너스(-) 및 공백 제거 테스트")
    print("=" * 60)
    
    paste_rows, _, stats = transformer.transform(mock_data)
    
    all_passed = True
    for i, row in enumerate(paste_rows):
        amount = row[7] # H열 (인덱스 7)
        expected = f"-{mock_data[i]['amount'].strip().replace(',', '')}"
        # 실제 0번째는 "".join(row['amount'].split()) 이므로 공백이 아예 없어야 함
        clean_mock_amount = "".join(mock_data[i]['amount'].split()).replace(',', '')
        expected = f"-{clean_mock_amount}"
        
        print(f"데이터 {i+1}: '{mock_data[i]['amount']}' (상태: '{mock_data[i]['status']}')")
        print(f"   결과 금액: '{amount}'")
        
        if amount == expected and not ' ' in amount:
            print(f"   [PASS] 정확히 일치하며 공백 없음")
        else:
            print(f"   [FAIL] Expected '{expected}', got '{amount}'")
            all_passed = False
            
    print("-" * 60)
    if all_passed:
        print("결과: 모든 테스트 통과! 공백 없이 마이너스가 정상적으로 붙습니다.")
    else:
        print("결과: 테스트 실패가 발생했습니다.")
    print("=" * 60)

if __name__ == "__main__":
    test_cancellation_formatting()
