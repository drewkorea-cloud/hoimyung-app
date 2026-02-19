import streamlit as st
import pandas as pd
import os
import re

@st.cache_data
def load_data_master():
    """
    엑셀 파일을 있는 그대로 읽어와서, UI가 인식할 수 있는 카테고리로 연결만 해줍니다.
    (강제 데이터 수정/보정 로직 삭제됨)
    """
    excel_file = 'chemical_db.xlsx'
    # 경로 설정 (main.py 위치 기준)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, excel_file)
    
    # UI에서 사용하는 방(Tab) 이름표 정의
    catalog = {
        'Cooling': { 'Main_Inhibitor': [], 'Biocide': [], 'Dispersant': [], 'Closed_System': [] },
        'Boiler':  { 'Oxygen_Scavenger': [], 'Scale_Disp': [], 'Condensate': [] }, # 청관제 방 이름은 'Scale_Disp'
        'RO':      { 'Antiscalant': [], 'CIP_Acid': [], 'CIP_Alk': [] }
    }
    
    df_raw = pd.DataFrame()

    if os.path.exists(file_path):
        try:
            # 엑셀 파일 읽기
            df_raw = pd.read_excel(file_path)
            df_raw = df_raw.fillna("-")
            df_raw.columns = [str(c).strip() for c in df_raw.columns]

            for _, row in df_raw.iterrows():
                # 1. 엑셀 데이터 가져오기
                prod_name = str(row.get('Name', 'Unknown')).strip()
                sys_val = str(row.get('System', '')).strip()
                raw_type = str(row.get('Type', '')).strip()
                
                # 2. 숫자값 파싱 함수 (ppm 등 단위 제거)
                def smart_parse(val):
                    if isinstance(val, (int, float)): return float(val)
                    match = re.search(r"(\d+(\.\d+)?)", str(val))
                    return float(match.group(1)) if match else 0.0

                # 3. 시스템별 카테고리 연결 (Mapping)
                # 엑셀의 Type 명칭이 프로그램 내부 명칭과 다를 때만 연결해줍니다.
                p_type = None 

                if sys_val == 'Cooling':
                    # 냉각수는 엑셀 Type 그대로 따라가되, 필요한 경우 분류
                    if 'Closed' in raw_type: p_type = 'Closed_System'
                    elif 'Biocide' in raw_type: p_type = 'Biocide'
                    elif 'Dispersant' in raw_type: p_type = 'Dispersant'
                    else: p_type = 'Main_Inhibitor' # 나머지는 다 주처리제로
                
                elif sys_val == 'Boiler':
                    if 'Oxygen' in raw_type: p_type = 'Oxygen_Scavenger'
                    elif 'Condensate' in raw_type or 'Amine' in raw_type: p_type = 'Condensate'
                    # [핵심] 엑셀의 "Scale_Inhibitor"를 프로그램의 "Scale_Disp" 방으로 입장시킴
                    elif 'Scale' in raw_type or 'Sludge' in raw_type or 'Inhibitor' in raw_type or 'All' in raw_type: 
                        p_type = 'Scale_Disp'
                
                elif sys_val == 'RO':
                    if 'Scale' in raw_type or 'Antiscalant' in raw_type: p_type = 'Antiscalant'
                    elif 'Acid' in raw_type: p_type = 'CIP_Acid'
                    elif 'Alk' in raw_type or 'Cleaner' in raw_type: p_type = 'CIP_Alk'

                # 4. 데이터 담기 (유효한 타입인 경우만)
                if p_type:
                    # 만약 카테고리에 없는 새로운 방이면 자동 생성
                    if sys_val not in catalog: catalog[sys_val] = {}
                    if p_type not in catalog[sys_val]: catalog[sys_val][p_type] = []
                    
                    target_raw = row.get('Target', '')
                    target_list = [t.strip() for t in str(target_raw).split(',')] if target_raw != '-' else []

                    item = {
                        'Name': prod_name,
                        'Type': raw_type, # 화면에는 엑셀 원본 Type 이름을 보여줌
                        'Desc': str(row.get('Desc', '-')),
                        'Dosage': smart_parse(row.get('Dosage', 0)),
                        'Target': target_list,
                        'Main_Ingredient': str(row.get('Main_Ingredient', '-')),
                        'Sales_Point': str(row.get('Sales_Point', '-')),
                        'Field_Tip': str(row.get('Field_Tip', '-')),
                        'Max_LSI': smart_parse(row.get('Max_LSI', 0)),
                        'Max_CaSO4': smart_parse(row.get('Max_CaSO4', 0)),
                        'Max_SiO2': smart_parse(row.get('Max_SiO2', 0))
                    }
                    catalog[sys_val][p_type].append(item)
                    
        except Exception as e:
            st.error(f"🚨 데이터 로드 중 오류 발생: {e}")
            
    return catalog, df_raw