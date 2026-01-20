import pandas as pd

# [Fix] Main.py 코드와 엑셀의 Type(분류명)을 100% 일치시킨 최종 버전
# 이 코드를 실행하면 선정바에 약품이 정상적으로 나타납니다.

data = [
    # ==========================================================================
    # 1. [Cooling] 냉각수 약품 (MCO/DREW 시리즈)
    #    Type: Main_Inhibitor / Dispersant / Biocide
    # ==========================================================================
    {'System': 'Cooling', 'Type': 'Main_Inhibitor', 'Name': 'DREW 11-635', 'Desc': '고농축/고알칼리 수질용 All-Organic', 'Dosage': 90.0, 'Target': 'All-Organic', 'Criteria': '2.5 <= LSI <= 3.2'},
    {'System': 'Cooling', 'Type': 'Main_Inhibitor', 'Name': 'DREW 11-635A', 'Desc': '고농축용 All-Organic (Azole Free)', 'Dosage': 60.0, 'Target': 'All-Organic', 'Criteria': '2.5 <= LSI <= 3.2'},
    {'System': 'Cooling', 'Type': 'Main_Inhibitor', 'Name': 'MCO- 308AA', 'Desc': 'Max pH 9.2 대응, 우수한 스케일/방식 능력', 'Dosage': 125.0, 'Target': 'All-Organic', 'Criteria': '2.0 <= LSI <= 3.0'},
    {'System': 'Cooling', 'Type': 'Main_Inhibitor', 'Name': 'DREW 2305 (High)', 'Desc': 'Millennium High Series, 고부하 현장', 'Dosage': 150.0, 'Target': 'Millennium', 'Criteria': '1.5 <= LSI <= 2.5'},
    {'System': 'Cooling', 'Type': 'Main_Inhibitor', 'Name': 'MCO- 2215 (Mid)', 'Desc': 'Millennium Mid-Range, 표준 수질', 'Dosage': 100.0, 'Target': 'Millennium', 'Criteria': '0.5 <= LSI <= 1.8'},
    {'System': 'Cooling', 'Type': 'Main_Inhibitor', 'Name': 'DREW 2105 (Lean)', 'Desc': 'Millennium Lean Series, 경제형', 'Dosage': 60.0, 'Target': 'Millennium', 'Criteria': '-0.5 <= LSI <= 1.0'},
    {'System': 'Cooling', 'Type': 'Main_Inhibitor', 'Name': 'MCO-2021BAA', 'Desc': '안정화 인산염계 표준 제품', 'Dosage': 100.0, 'Target': 'Stab-Phos', 'Criteria': '-0.5 <= LSI <= 1.5'},
    {'System': 'Cooling', 'Type': 'Main_Inhibitor', 'Name': 'PERFORMAX 2525', 'Desc': '저경도/연수 보충수용 강력 방식제', 'Dosage': 135.0, 'Target': 'Soft-Water', 'Criteria': '-0.5 <= LSI <= 1.2'},

    {'System': 'Cooling', 'Type': 'Dispersant', 'Name': 'DREWSPERSE 744', 'Desc': '철(Iron)/망간 분산 특화', 'Dosage': 50.0, 'Target': 'Iron', 'Criteria': 'High Iron'},
    {'System': 'Cooling', 'Type': 'Dispersant', 'Name': 'DREWSPERSE 739', 'Desc': '유분(Oil) 분산 제거', 'Dosage': 50.0, 'Target': 'Oil', 'Criteria': 'Oil Contamination'},
    {'System': 'Cooling', 'Type': 'Dispersant', 'Name': 'PERFORMAX 405', 'Desc': '바이오필름(Bio-slime) 점착 방지', 'Dosage': 50.0, 'Target': 'Biofilm', 'Criteria': 'Bio-Slime'},
    {'System': 'Cooling', 'Type': 'Dispersant', 'Name': 'DREWSPERSE 747', 'Desc': '탄산칼슘 스케일 강력 분산', 'Dosage': 50.0, 'Target': 'CaCO3', 'Criteria': 'High Scale'},

    {'System': 'Cooling', 'Type': 'Biocide', 'Name': 'BioOX-1000', 'Desc': '산화성 살균제 (염소계)', 'Dosage': 50.0, 'Target': 'Bacteria', 'Criteria': 'Standard'},
    {'System': 'Cooling', 'Type': 'Biocide', 'Name': 'BioNox-250', 'Desc': '비산화성 살균제 (슬라임)', 'Dosage': 100.0, 'Target': 'Slime', 'Criteria': 'Shock'},

    # ==========================================================================
    # 2. [Boiler] 보일러 약품 (MBB/MBO 시리즈)
    #    [중요] Type 이름을 Main.py가 인식하는 이름으로 통일했습니다.
    #    - Inhibitor, Scale_Disp -> 'Scale_Disp'
    #    - 응축수 pH -> 'Condensate'
    # ==========================================================================
    # 탈산제 (Oxygen_Scavenger)
    {'System': 'Boiler', 'Type': 'Oxygen_Scavenger', 'Name': 'HBS-100 (Sulfite)', 'Desc': '아황산염 (저압용)', 'Dosage': 20.0, 'Target': 'Oxygen', 'Criteria': 'Low P'},
    {'System': 'Boiler', 'Type': 'Oxygen_Scavenger', 'Name': 'MBO-0815', 'Desc': '응축수/용존산소 제거', 'Dosage': 20.0, 'Target': 'Oxygen', 'Criteria': 'General'},
    {'System': 'Boiler', 'Type': 'Oxygen_Scavenger', 'Name': 'MBO-CHZ7', 'Desc': '복합 탈산제', 'Dosage': 15.0, 'Target': 'Oxygen', 'Criteria': 'General'},
    {'System': 'Boiler', 'Type': 'Oxygen_Scavenger', 'Name': 'MBO-1040', 'Desc': '카보하이드라지드', 'Dosage': 15.0, 'Target': 'Oxygen', 'Criteria': 'Mid P'},
    {'System': 'Boiler', 'Type': 'Oxygen_Scavenger', 'Name': 'MBB-8760 (Hydrazine)', 'Desc': '하이드라진 (고압용)', 'Dosage': 10.0, 'Target': 'Oxygen', 'Criteria': 'High P'},

    # 청관제 (Scale_Disp) - 엑셀의 'Inhibitor'를 'Scale_Disp'로 통합
    {'System': 'Boiler', 'Type': 'Scale_Disp', 'Name': 'HBP-Standard', 'Desc': '표준 인산염계', 'Dosage': 30.0, 'Target': 'Scale', 'Criteria': 'Standard'},
    {'System': 'Boiler', 'Type': 'Scale_Disp', 'Name': 'MBB-1123CH', 'Desc': '보일러 청관제', 'Dosage': 30.0, 'Target': 'Scale', 'Criteria': 'Standard'},
    {'System': 'Boiler', 'Type': 'Scale_Disp', 'Name': 'MBB-1100ODT', 'Desc': 'All-in-One 청관제', 'Dosage': 40.0, 'Target': 'Scale', 'Criteria': 'Multi'},
    {'System': 'Boiler', 'Type': 'Scale_Disp', 'Name': 'MBB-1123NP', 'Desc': '청관제 (NP)', 'Dosage': 30.0, 'Target': 'Scale', 'Criteria': 'Standard'},
    {'System': 'Boiler', 'Type': 'Scale_Disp', 'Name': 'MBB-1123K2', 'Desc': '청관제 (K2)', 'Dosage': 30.0, 'Target': 'Scale', 'Criteria': 'Standard'},
    {'System': 'Boiler', 'Type': 'Scale_Disp', 'Name': 'MBB-1124CHM', 'Desc': '고효율 청관제', 'Dosage': 30.0, 'Target': 'Scale', 'Criteria': 'High Eff'},
    {'System': 'Boiler', 'Type': 'Scale_Disp', 'Name': 'MBB-2217CHM', 'Desc': '복합 청관제', 'Dosage': 35.0, 'Target': 'Scale', 'Criteria': 'Complex'},
    {'System': 'Boiler', 'Type': 'Scale_Disp', 'Name': 'MBB-2800', 'Desc': '고압용 청관제', 'Dosage': 20.0, 'Target': 'Scale', 'Criteria': 'High P'},
    {'System': 'Boiler', 'Type': 'Scale_Disp', 'Name': 'MBB-3000', 'Desc': '특수 청관제', 'Dosage': 20.0, 'Target': 'Scale', 'Criteria': 'Special'},

    # 복수처리제 (Condensate) - 엑셀의 '응축수 pH'를 'Condensate'로 변경
    {'System': 'Boiler', 'Type': 'Condensate', 'Name': 'MBB-2', 'Desc': '응축수 처리제', 'Dosage': 5.0, 'Target': 'Corrosion', 'Criteria': 'Condensate'},
    {'System': 'Boiler', 'Type': 'Condensate', 'Name': 'MBC_8760', 'Desc': '복수 배관 방식제', 'Dosage': 5.0, 'Target': 'Corrosion', 'Criteria': 'Condensate'},

    # ==========================================================================
    # 3. [RO] RO 약품 (HRD 시리즈)
    #    Type: Antiscalant
    # ==========================================================================
    {'System': 'RO', 'Type': 'Antiscalant', 'Name': 'HRD-2000 (General)', 'Desc': '범용 탄산칼슘 제어', 'Dosage': 3.0, 'Target': 'LSI, CaSO4', 'Criteria': 'Standard'},
    {'System': 'RO', 'Type': 'Antiscalant', 'Name': 'HRD-2200 (General)', 'Desc': '범용 탄산칼슘/황산염 제어', 'Dosage': 3.0, 'Target': 'LSI, CaSO4', 'Criteria': 'Standard'},
    {'System': 'RO', 'Type': 'Antiscalant', 'Name': 'HRD-3000 (High Silica)', 'Desc': '실리카 200ppm 대응', 'Dosage': 5.0, 'Target': 'SiO2', 'Criteria': 'High Silica'},
    {'System': 'RO', 'Type': 'Antiscalant', 'Name': 'HRD-2050 (Struvite)', 'Desc': '폐수 재이용/인산염', 'Dosage': 6.0, 'Target': 'Struvite', 'Criteria': 'Wastewater'},
    {'System': 'RO', 'Type': 'Antiscalant', 'Name': 'HRD-2240 (High Sulfate)', 'Desc': '황산염 특화', 'Dosage': 4.0, 'Target': 'BaSO4', 'Criteria': 'High Sulfate'}

    # ==========================================================================
    # 4. [RO] CIP 세정제 (Acid / Alkaline)
    # ==========================================================================
    {'System': 'RO', 'Type': 'CIP_Acid', 'Name': 'MCL-102 (Low pH)', 'Desc': '무기물 스케일/금속 산화물 제거용 산성 세정제', 'Dosage': 2.0, 'Target': 'CaCO3, Metal', 'Criteria': 'pH 2~3'},
    {'System': 'RO', 'Type': 'CIP_Acid', 'Name': 'MCL-305 (General)', 'Desc': '범용 산성 세정제', 'Dosage': 2.0, 'Target': 'Scale', 'Criteria': 'pH 2~3'},    
    {'System': 'RO', 'Type': 'CIP_Alk', 'Name': 'MCL-605 (High pH)', 'Desc': '유기물/미생물 슬라임 제거용 알칼리 세정제', 'Dosage': 2.0, 'Target': 'Biofouling, Organic', 'Criteria': 'pH 11~12'},
    {'System': 'RO', 'Type': 'CIP_Alk', 'Name': 'MCL-510 (Enzyme)', 'Desc': '효소 첨가형 고효율 알칼리 세정제', 'Dosage': 1.0, 'Target': 'Heavy Bio', 'Criteria': 'pH 10~11'},

]  
# 데이터프레임 생성 및 저장
df = pd.DataFrame(data)
file_name = 'chemical_db.xlsx'
df.to_excel(file_name, index=False)

print(f"✅ '{file_name}' 정상 복구 완료!")
print(f"   - Main.py가 인식할 수 있는 올바른 Type 이름으로 정리되었습니다.")