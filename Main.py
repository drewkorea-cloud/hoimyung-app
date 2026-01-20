
import streamlit as st

import pandas as pd

import os

import sys

import math

import plotly.graph_objects as go

import plotly.express as px

import numpy as np



# --- 1. 기본 설정 ---

st.set_page_config(layout="wide", page_title="Water Solution Master (by Parker)")


# [스타일] CSS 스타일 정의 (표 겹침 오류 해결 Ver)
st.markdown("""
    <style>
    /* 1. 전체 기본 폰트 및 본문 텍스트 확대 */
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
        font-size: 20px !important;
    }
    .stMarkdown p, .stMarkdown li {
        font-size: 20px !important;
        line-height: 1.6 !important;
        color: #2D3748 !important;
    }

    /* 2. 탭 (Tab) 버튼 스타일 (크고 잘 보이게) */
    button[data-baseweb="tab"] {
        font-size: 24px !important;
        font-weight: 800 !important;
        color: #718096 !important;
        background-color: #F7FAFC !important;
        border-radius: 8px 8px 0 0;
        padding: 12px 24px !important; 
        margin-right: 8px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FFFFFF !important;
        background-color: #2E86C1 !important;
        border: none !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }

    /* 3. 사이드바 (Sidebar) 메뉴 글씨 확대 */
    [data-testid="stSidebar"] .stRadio label {
        font-size: 22px !important;
        font-weight: 700 !important;
        padding: 12px 5px !important;
    }
    [data-testid="stSidebar"] h1 {
        font-size: 30px !important;
        font-weight: 900 !important;
    }

    /* 4. 입력창 라벨 (Input Label) */
    .stNumberInput label, .stTextInput label, .stSelectbox label, .stSlider label {
        font-size: 22px !important;
        font-weight: 800 !important;
        color: #1A202C !important;
        margin-bottom: 10px !important;
    }
    
    /* 5. 입력창 내부 글씨 (Input Value) */
    .stNumberInput input, .stSelectbox div[data-baseweb="select"] div {
        font-size: 20px !important;
        font-weight: 600 !important;
        min-height: 45px !important;
    }

    /* 6. 결과값 (Metric) */
    [data-testid="stMetricLabel"] {
        font-size: 20px !important;
        font-weight: 600;
    }
    [data-testid="stMetricValue"] {
        font-size: 38px !important;
        font-weight: 900 !important;
        color: #2563EB !important;
    }
    
    /* 7. 제목 및 헤더 */
    h1, h2, h3 {
        font-weight: 800 !important;
        color: #2C3E50 !important;
    }
    h3 { font-size: 26px !important; }

    /* 8. [수정] 데이터 테이블 (Data Editor) */
    /* zoom 속성을 제거하여 겹침 현상 방지 */
    [data-testid="stDataFrame"] {
        font-size: 18px !important; /* 내부 폰트만 살짝 키움 */
    }

    /* 9. 박스 디자인 */
    .metric-card {
        background-color: #FFFFFF;
        border: 2px solid #E2E8F0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 4px 4px 12px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# [Helper] 엑셀 카탈로그 로더 (최종 수정본: 키 불일치 및 모호한 타입 자동 보정)
# ==============================================================================
def load_product_catalog_from_excel():
    excel_file = 'chemical_db.xlsx'
    current_dir = os.getcwd()
    file_path = os.path.join(current_dir, excel_file)

    # 1. 카탈로그 구조 초기화 (Main.py가 사용하는 Key와 100% 일치시킴)
    catalog = {
        'Cooling': { 'Main_Inhibitor': [], 'Biocide': [], 'Dispersant': [] },
        'Boiler':  { 
            'Oxygen_Scavenger': [], 
            'Scale_Disp': [],  # [수정] Scale_Inhibitor -> Scale_Disp (화면 코드와 일치)
            'Condensate': [] 
        },
        'RO':      { 
            'Antiscalant': [], 
            'CIP_Acid': [], 
            'CIP_Alk': [] 
        }
    }

    # 2. 비상용 기본 데이터 (Fallback Data) - 엑셀 없을 때 사용
    fallback_data = {
        'Cooling': {
            'Main_Inhibitor': [{'Name': 'Cool-100', 'Type': 'Main_Inhibitor', 'Desc': 'Standard', 'Feature': 'Standard', 'Dosage': 50, 'Target': ['Corrosion']}],
            'Biocide': [{'Name': 'Bio-Kill', 'Type': 'Biocide', 'Desc': 'Oxidizing', 'Feature': 'Oxidizing', 'Dosage': 10, 'Target': ['Bacteria']}],
            'Dispersant': [{'Name': 'Disp-200', 'Type': 'Dispersant', 'Desc': 'Polymer', 'Feature': 'Polymer', 'Dosage': 20, 'Target': ['Scale']}]
        },
        'Boiler': {
            'Oxygen_Scavenger': [{'Name': 'Oxy-Zero', 'Type': 'Oxygen_Scavenger', 'Desc': 'Sulfite', 'Feature': 'Sulfite', 'Dosage': 30, 'Target': ['Oxygen']}],
            'Scale_Disp': [{'Name': 'Scale-X', 'Type': 'Scale_Disp', 'Desc': 'Polymer', 'Feature': 'Polymer', 'Dosage': 40, 'Target': ['Scale']}], # Key 수정됨
            'Condensate': [{'Name': 'Steam-Save', 'Type': 'Condensate', 'Desc': 'Amine', 'Feature': 'Amine', 'Dosage': 15, 'Target': ['pH']}]
        },
        'RO': {
            'Antiscalant': [{'Name': 'RO-ScaleStop', 'Type': 'Antiscalant', 'Desc': 'General', 'Feature': 'General', 'Dosage': 3.0, 'Target': ['CaCO3']}],
            'CIP_Acid': [{'Name': 'RO-Acid Clean', 'Type': 'CIP_Acid', 'Desc': 'pH 2.0', 'Feature': 'pH 2.0', 'Dosage': 2.0, 'Target': ['Scale']}],
            'CIP_Alk': [{'Name': 'RO-Alk Clean', 'Type': 'CIP_Alk', 'Desc': 'pH 12.0', 'Feature': 'pH 12.0', 'Dosage': 2.0, 'Target': ['Bio']}]
        }
    }

    # 3. 엑셀 파일 읽기 및 스마트 매핑
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            # 컬럼명 공백 제거
            df.columns = [str(c).strip() for c in df.columns]

            for _, row in df.iterrows():
                sys = str(row.get('System', '')).strip()
                raw_type = str(row.get('Type', '')).strip()
                
                # [스마트 매핑] 엑셀의 다양한 표현을 프로그램 표준 Key로 자동 변환
                p_type = raw_type 

                # (1) Cooling 매핑
                if sys == 'Cooling':
                    if raw_type in ['Inhibitor', 'Corrosion Inhibitor', 'Scale/Corrosion']: p_type = 'Main_Inhibitor'
                    elif raw_type in ['Biocides', 'Biocide']: p_type = 'Biocide'
                
                # (2) Boiler 매핑 (Scale_Disp로 통일)
                elif sys == 'Boiler':
                    if 'Oxygen' in raw_type: p_type = 'Oxygen_Scavenger'
                    # 'Scale', 'Sludge', 'Inhibitor' 등이 들어오면 무조건 'Scale_Disp'로 보냄
                    elif any(x in raw_type for x in ['Scale', 'Sludge', 'Inhibitor', 'Disp']): p_type = 'Scale_Disp'
                    elif 'Amine' in raw_type or 'Condensate' in raw_type: p_type = 'Condensate'

                # (3) RO 매핑 (CIP 자동 분류)
                elif sys == 'RO':
                    if 'Scale' in raw_type or 'Antiscalant' in raw_type: p_type = 'Antiscalant'
                    # 엑셀에 'CIP'라고만 적혀있어도 이름/설명을 보고 산성/알칼리 판단
                    elif 'CIP' in raw_type or 'Acid' in raw_type or 'Alk' in raw_type:
                        name_desc = (str(row.get('Name', '')) + str(row.get('Desc', ''))).lower()
                        if 'acid' in raw_type or 'acid' in name_desc or '산성' in name_desc or 'low ph' in name_desc:
                            p_type = 'CIP_Acid'
                        elif 'alk' in raw_type or 'alk' in name_desc or '알칼리' in name_desc or 'high ph' in name_desc or 'organic' in name_desc:
                            p_type = 'CIP_Alk'
                        else:
                            # 정보가 부족하면 기본적으로 알칼리로 분류 (유기물 세정용)
                            p_type = 'CIP_Alk'

                # 카탈로그에 해당 시스템/타입이 존재할 때만 추가
                if sys in catalog and p_type in catalog[sys]:
                    target_raw = row.get('Target', '')
                    target_list = [t.strip() for t in str(target_raw).split(',')] if pd.notnull(target_raw) and str(target_raw).strip() != '' else []
                    
                    try: dose_val = float(row.get('Dosage', 0))
                    except: dose_val = 0.0

                    item = {
                        'Name': str(row.get('Name', 'Unknown')),
                        'Type': p_type,      # [중요] 프로그램 Key로 변환된 타입을 저장
                        'Desc': str(row.get('Desc', '')),
                        'Dosage': dose_val,
                        'Target': target_list,
                        'Feature': str(row.get('Desc', ''))
                    }
                    catalog[sys][p_type].append(item)

        except Exception as e:
            st.warning(f"⚠️ 엑셀 읽기 중 일부 오류: {e} (기본 데이터를 병합합니다)")

    # 4. 데이터가 빈 항목은 기본값(Fallback)으로 채움
    for sys in fallback_data:
        for p_type in fallback_data[sys]:
            if not catalog[sys][p_type]: 
                catalog[sys][p_type] = fallback_data[sys][p_type]

    return catalog
# --------------------------------------------------------
# [여기가 중요!] 함수 밖으로 빠져나와서 변수를 선언해야 함
# --------------------------------------------------------
PRODUCT_CATALOG = load_product_catalog_from_excel()

# ==========================================
# [엔진 2] 보일러 전문가 엔진 (안토인 식 적용 Ver)
# ==========================================
class Boiler_Expert_Engine:
    @staticmethod
    def get_steam_enthalpy(pressure_bar):
        """
        [Global Expert Update] Antoine Equation (안토인 식) 적용
        - 단순 회귀식 대신 화학공학 표준 수식을 사용하여 온도 예측 오차를 최소화합니다.
        """
        try:
            P_bar = max(pressure_bar, 0.1) # 0.1 bar 이상으로 보정
            
            # Antoine Constants (Water): log10(P_mmHg) = A - B / (T_C + C)
            # 압력 변환: bar -> mmHg
            P_mmHg = P_bar * 750.062
            
            # 고압(100도 이상) vs 저압(100도 미만) 상수가 다름
            if P_bar >= 1.013: 
                # 고온 영역 (100°C ~ 374°C)
                A, B, C = 8.14019, 1810.94, 244.485
            else:
                # 저온 영역 (0°C ~ 100°C)
                A, B, C = 8.07131, 1730.63, 233.426

            # 온도 역산 (T = B / (A - logP) - C)
            val = A - math.log10(P_mmHg)
            ts = (B / val) - C
            
            # 엔탈피 계산 (간이식 유지: 현장 관리용으로 충분함)
            # H = 600 + 0.3 * T (대략적 근사)
            h_steam = 665 + 0.3 * ts    
            
            return round(ts, 1), round(h_steam, 1)

        except Exception as e:
            # 계산 에러 시 기본값 반환
            return 100.0, 640.0

    @staticmethod
    def check_asme_standard(pressure_bar, tds, silica, alk):
        # ASME 가이드라인 (동일 유지)
        limit_tds, limit_sio2, limit_alk = 3000, 150, 500
        if pressure_bar <= 20: limit_tds, limit_sio2, limit_alk = 3500, 150, 700
        elif pressure_bar <= 30: limit_tds, limit_sio2, limit_alk = 3000, 90, 600
        elif pressure_bar <= 40: limit_tds, limit_sio2, limit_alk = 2500, 40, 500
        elif pressure_bar <= 60: limit_tds, limit_sio2, limit_alk = 2000, 20, 400
        else: limit_tds, limit_sio2, limit_alk = 1500, 8, 200

        msgs = []
        if tds > limit_tds: msgs.append(f"🔴 전도도 초과 (기준 {limit_tds})")
        if silica > limit_sio2: msgs.append(f"🔴 실리카 초과 (기준 {limit_sio2})")
        if alk > limit_alk: msgs.append(f"⚠️ 알칼리도 높음 (기준 {limit_alk})")
        
        if not msgs: return "✅ ASME 기준 만족 (Safe)", limit_tds
        else: return ", ".join(msgs), limit_tds

# ==============================================================================
# [Troubleshooting] Total System Audit (TSA) - Master's Edition (50년 경력 Ver)
# ==============================================================================
def draw_trouble_shooter(system_name):
    st.markdown(f"#### 🕵️‍♂️ {system_name} Master's Deep-Dive Audit")
    st.info("단순 증상 확인을 넘어, **설비 재질(Metallurgy), 이력(Trend), 수원(Source)**을 고려한 입체적 진단입니다.")

    # --------------------------------------------------------------------------
    # 1. [Cooling] 냉각수 : 재질/트렌드 + 4대 악재 정밀 진단
    # --------------------------------------------------------------------------
    if system_name == "Cooling":
        # [Step 0] 마스터의 질문: 설비 재질 및 추세 확인 (가장 중요)
        with st.expander("⚙️ [Step 0] 설비 재질 및 이력 확인 (Master's Check)", expanded=True):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                mat_type = st.radio("주요 열교환기 재질", 
                                  ["Carbon Steel (탄소강)", "Copper/Brass (동계열)", "Stainless (SUS304/316)", "Titanium (티타늄)"],
                                  key="c_mat_type")
            with col_m2:
                trend_spd = st.radio("문제 발생 속도 (Trend)", 
                                    ["서서히 악화 (수개월)", "급격히 악화 (수일 내)", "운전 조건 변경 직후"],
                                    key="c_trend_spd")

        # 4대 악재 탭 구성
        t1, t2, t3, t4 = st.tabs(["🔴 부식 (Corrosion)", "⚪ 스케일/침적", "🟢 미생물/슬라임", "⚙️ 공정/운전"])

        with t1: # 부식 탭
            st.markdown("##### 1. 부식 정밀 진단")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**[수질 화학]**")
                ck_c_alk = st.checkbox("M-Alk / Cl 비율이 3.0 이하 (공식 위험)", key="c_alk")
                ck_c_ph_low = st.checkbox("pH < 7.0 (저산성 운전)", key="c_ph_low")
            with c2:
                st.markdown("**[설비 환경]**")
                ck_c_vel_low = st.checkbox("유속 < 0.3 m/s (Low Flow)", key="c_vl")
                ck_c_mic = st.checkbox("슬라임 하부 흑색 녹 (MIC 의심)", key="c_mic")

            st.divider()
            
            # [Master's Logic] 재질별 맞춤 진단
            if ck_c_alk and "Stainless" in mat_type:
                st.error("🚨 **[치명적] 응력부식균열(SCC) 경보:** SUS 재질에 염소이온 농축은 시한폭탄입니다. 염소 농도를 즉시 낮추거나 티타늄 변경을 검토하십시오.")
            
            if "Copper" in mat_type:
                if ck_c_ph_low:
                    st.error("🚨 **[동 부식] 산성 용출:** 동 재질은 pH 7.0 이하에서 급격히 녹습니다. 아졸(Azole) 투입량을 2배 증량하십시오.")
                elif ck_c_vel_low:
                    st.warning("⚠️ **[동 부식] 침적 부식:** 유속이 느려 이물질 하부에서 동이 녹고 있습니다. 역세정이 시급합니다.")
            
            if "Carbon Steel" in mat_type and (ck_c_vel_low or ck_c_mic):
                st.error("🚨 **[탄소강] 국부 부식(Pitting):** 유속 부족과 슬라임은 탄소강에 치명적입니다. 물리적 세정 없이는 배관 구멍을 막을 수 없습니다.")

        with t2: # 스케일 탭
            st.markdown("##### 2. 스케일 및 침적 특성")
            s1, s2 = st.columns(2)
            with s1:
                ck_s_lsi = st.checkbox("LSI > +2.8 (강한 스케일 경향)", key="s_lsi")
                ck_s_temp = st.checkbox("열교환기 출구 온도 상승 (효율 저하)", key="s_dt")
            with s2:
                ck_s_phos = st.checkbox("인산염(PO4) > 20ppm (인산칼슘 위험)", key="s_phos")
                ck_s_mud = st.checkbox("냉각탑 하부 진흙(Mud) 퇴적", key="s_mud")
            
            st.divider()
            
            # [Master's Logic] 트렌드 기반 진단
            if ck_s_temp:
                if "서서히" in trend_spd:
                    st.warning("⚠️ **[진단] 결정성 스케일 (Hard Scale):** 서서히 효율이 떨어지는 것은 칼슘/실리카 스케일 특징입니다. 고분자 분산제(Polymer)를 증량하십시오.")
                elif "급격히" in trend_spd:
                    st.error("🚨 **[진단] 미생물 슬라임 또는 토사:** 며칠 만에 효율이 급감하는 건 스케일이 아닙니다. 슬라임입니다! 살균제를 충격 투입하십시오.")
            
            if ck_s_phos and "High" in str(ck_s_temp): # 고온 + 인산염
                 st.error("🚨 **인산칼슘 스케일:** 고온부에서는 일반 Polymer가 깨집니다. **Tr-Polymer(고온용)**를 사용해야 합니다.")

        with t3: # 미생물 탭
            st.markdown("##### 3. 미생물 및 레지오넬라")
            b1, b2 = st.columns(2)
            with b1:
                ck_b_sr = st.checkbox("잔류염소 소모량 급증 (Demand)", key="b_sr")
                ck_b_leg = st.checkbox("레지오넬라 검출 이력 있음", key="b_leg")
            with b2:
                ck_b_slm = st.checkbox("열교환기/충진재 미끈거림 확인", key="b_slm")

            if ck_b_slm or ck_b_sr:
                st.error("🚨 **바이오 해저드 (Bio-Hazard):** 산화제(염소)만으로는 부족합니다. **이소치아졸론** 계열 살균제를 '충격 요법(Shock Dosing)'으로 투입하십시오.")

        with t4: # 공정 탭
            st.markdown("##### 4. 공정 누설 감지")
            ck_o_oil = st.checkbox("수면 위 무지개빛 기름막 (Oil)", key="o_oil")
            ck_o_chem = st.checkbox("암모니아/유기용제 냄새", key="o_chem")
            
            if ck_o_oil or ck_o_chem:
                st.error("🚨 **공정 누설(Process Leak):** 수처리 약품으로는 해결 불가능합니다. 누설된 열교환기를 찾아 격리(Isolation)하십시오.")

    # --------------------------------------------------------------------------
    # 2. [Boiler] 보일러 : 압력/타입별 정밀 진단
    # --------------------------------------------------------------------------
    elif system_name == "Boiler":
        # [Step 0] 마스터의 질문
        with st.expander("⚙️ [Step 0] 보일러 운전 조건 확인 (Master's Check)", expanded=True):
            c_b1, c_b2 = st.columns(2)
            with c_b1:
                blr_type = st.radio("보일러 종류", ["수관식 (Water Tube)", "노통연관식 (Fire Tube)", "관류식 (Once-through)"], key="b_type")
            with c_b2:
                press_range = st.selectbox("운전 압력 범위", ["저압 (< 15 bar)", "중압 (15 ~ 40 bar)", "고압 (> 40 bar)"], key="b_press")

        t_feed, t_blr, t_stm = st.tabs(["💧 급수/탈기기", "🔥 관수/본체", "💨 증기/응축수"])

        with t_feed:
            st.markdown("##### 1. 급수 계통 건전성")
            f1, f2 = st.columns(2)
            with f1:
                bk_do = st.checkbox("용존산소(DO) > 0.007 ppm (7 ppb)", key="bk_do")
                bk_temp = st.checkbox("탈기기 온도 < 103°C (저온)", key="bk_dt")
            with f2:
                bk_hard = st.checkbox("급수 경도(Hardness) Trace 검출", key="bk_hd")
                bk_fe = st.checkbox("급수 철분 > 0.1 ppm", key="bk_fe")

            st.divider()
            
            # [Master's Logic] 압력/타입별 진단
            if bk_do:
                if "고압" in press_range:
                    st.error("🚨 **[치명적] 고압 산소 부식:** 40bar 이상에서 DO 검출은 튜브 파열 직행입니다. 탈기기 성능 미달입니다.")
                else:
                    st.warning("⚠️ **탈산제 부족:** 저압이라도 장기적으로 곰보 부식(Pitting)이 발생합니다. 탈산제를 증량하십시오.")
            
            if bk_hard:
                if "관류식" in blr_type:
                    st.error("🚨 **[비상] 관류 보일러 경도 유입:** 관류식은 보유수량이 적어 경도 유입 시 즉시 튜브가 막힙니다. 즉각 가동 중지 및 연수기 점검 필수.")
                else:
                    st.warning("⚠️ **연수기 파과:** 연수 장치 재생이 시급합니다.")

        with t_blr:
            st.markdown("##### 2. 보일러 내부 및 pH 관리")
            b1, b2 = st.columns(2)
            with b1:
                bk_ph_h = st.checkbox("관수 pH > 12.0 (과잉 알칼리)", key="bk_ph_h")
            with b2:
                bk_scale = st.checkbox("튜브 국부 과열 (Hot Spot)", key="bk_sc")

            if bk_ph_h and "수관식" in blr_type:
                st.warning("⚠️ **가성취화(Caustic Embrittlement) 경고:** 용접 부위 크랙 위험이 있습니다. Phosphate Program으로 전환하여 Free OH를 제거하십시오.")

        with t_stm:
            st.markdown("##### 3. 증기 및 응축수")
            bk_cph = st.checkbox("응축수 pH < 6.5 (산성)", key="bk_cph")
            if bk_cph:
                st.error("🚨 **탄산 가스 부식:** 응축수 배관이 녹고 있습니다. **중화 아민(Neutralizing Amine)** 투입량을 30% 증량하십시오.")

    # --------------------------------------------------------------------------
    # 3. [RO] RO : 수원/막 종류별 정밀 진단
    # --------------------------------------------------------------------------
    elif system_name == "RO":
        # [Step 0] 마스터의 질문
        with st.expander("⚙️ [Step 0] 원수 소스 및 막 종류 확인 (Master's Check)", expanded=True):
            col_r1, col_r2 = st.columns(2)
            with col_r1: 
                water_src = st.radio("원수 소스", ["지하수/상수", "하수 재이용 (Reuse)", "해수 (Seawater)"], key="r_src")
            with col_r2: 
                mem_type = st.radio("막 종류", ["BWRO (기수용)", "SWRO (해수용)", "LPRO (저압용)"], key="r_mem")

        t_pre, t_ro, t_cip = st.tabs(["🛡️ 전처리/막힘", "🧪 화학적 손상/스케일", "🚿 CIP 효율"])

        with t_pre:
            st.markdown("##### 1. 막힘(Fouling) 및 전처리")
            rk_n_dp = st.checkbox("정규화 차압(Normalized DP) 15% 상승", key="rk_ndp")
            rk_sdi = st.checkbox("SDI (15min) > 4.0", key="rk_sdi")

            if rk_n_dp:
                st.divider()
                if "하수 재이용" in water_src:
                    st.error("🚨 **[유기물 파울링]:** 하수 재이용수는 90% 확률로 유기물/미생물 오염입니다. **알칼리 세정(pH 12) + 효소 세정제**를 쓰지 않으면 회복 안 됩니다.")
                elif "지하수" in water_src:
                    st.warning("⚠️ **[무기물 스케일/실리카]:** 지하수는 주로 실리카/탄산칼슘 문제입니다. **산성 세정(pH 2)**을 먼저 수행하십시오.")
                elif "해수" in water_src:
                    st.warning("⚠️ **[미생물/유기물]:** 해수는 Biofouling이 주원인입니다. 알칼리 세정이 우선입니다.")

        with t_ro:
            st.markdown("##### 2. 산화 손상 및 스케일")
            rk_cl = st.checkbox("원수 염소(Cl2) 검출 / 활성탄 파과", key="rk_cl")
            rk_scale = st.checkbox("농축수 측 흰색 결정 (Scaling)", key="rk_sc")

            if rk_cl:
                if "BWRO" in mem_type or "LPRO" in mem_type:
                    st.error("🚨 **[산화 손상]:** Polyamide 막은 염소에 닿는 순간 녹습니다. 복구 불가능합니다. 즉시 활성탄 교체 및 SMBS 투입량을 확인하십시오.")
            if rk_scale:
                st.error("🚨 **스케일 석출:** 회수율이 한계를 넘었습니다. 스케일 방지제 증량 또는 회수율 하향 조정이 필요합니다.")

        with t_cip:
            st.markdown("##### 3. CIP 및 기계적 결함")
            rk_cip_fail = st.checkbox("CIP 후에도 차압 복원 안됨", key="rk_cf")
            rk_tele = st.checkbox("엘리먼트 텔레스코핑 (Telescoping)", key="rk_tele")

            if rk_cip_fail:
                st.error("🚨 **비가역적 오염:** 이미 오염물이 막에 고착되었습니다. **Soaking(담그기) 요법**을 시도하거나 막 교체를 준비하십시오.")
            if rk_tele:
                st.error("🚨 **물리적 파손:** 과도한 차압 운전으로 막이 밀려 나왔습니다. 1단 막 교체 및 Brine Seal 방향을 확인하십시오.")

    # [공통] 마스터의 조언
    st.divider()
    st.info("""
    💡 **Master's Tip:** 수처리 사고의 80%는 **'변화된 운전 조건'**을 약품이 따라가지 못할 때 발생합니다. 
    진단 결과가 '정상'이라도, **지난주 대비 데이터의 '기울기(Trend)'가 나빠졌다면** 이미 오염은 시작된 것입니다.
    """)

# --- 2. 사이드바 메뉴 ---
with st.sidebar:
    # [수정] 로고와 텍스트 타이틀 중 하나만 표시하는 로직
    if os.path.exists("logo.png"):
        # 1. 로고 파일이 있으면 로고를 보여준다. (타이틀 텍스트는 숨김)
        st.image("logo.png", use_container_width=True)
        # 로고 아래에 프로그램 이름만 깔끔하게 표시
        st.markdown("### **Water Master Pro**") 
    else:
        # 2. 로고 파일이 없으면 기존처럼 텍스트 타이틀을 보여준다.
        st.title("💧 HOIMYUNG WATERZEN")
        st.subheader("Water Master Pro")
    
    # (아래부터는 기존 메뉴 코드 유지)
    program_mode = st.radio(
        "Select Module:", 
        [
            "1. Cooling Expert", 
            "2. Boiler Master", 
            "3. RO Master Pro", 
            "4. Wastewater Reuse", 
            "5. Basic Engineering"
        ], 
        key="main_menu_mode"
    )
    
    st.markdown("---")
    st.info("💡 **Tip:** 값을 입력하고 '적용' 버튼을 누르면 AI 진단이 시작됩니다.")
    st.caption("Authorized by **PARKER**")

# ==============================================================================

# [Module 1] Cooling Expert

# ==============================================================================

if "Cooling" in program_mode:

    # 1. 초기 데이터 및 세션 설정

    if 'makeup_data' not in st.session_state:

        st.session_state.makeup_data = pd.DataFrame({

            'Item': ['pH', 'Cond (µS)', 'Ca-H (ppm)', 'Mg-H (ppm)', 'M-Alk (ppm)', 'Cl (ppm)', 'SO4 (ppm)', 'SiO2 (ppm)'],

            'Value': [7.5, 200.0, 40.0, 10.0, 50.0, 20.0, 10.0, 10.0]

        })

    

    if 'cooling_results' not in st.session_state:

        st.session_state.cooling_results = None



    if 'deposit_data' not in st.session_state:
        st.session_state.deposit_data = pd.DataFrame({
            'item': [
                'Sulfate(SO4)', 'Aluminium(Al2O3)', 'Calcium(CaO)', 'Copper(CuO)', 
                'Iron Oxide (Fe2O3)', 'Potasium(K2O)', 'Magnesium(MgO)', 'Manganese(MnO)', 
                'Sodium(Na2O)', 'Phosphate (P2O5)', 'Silica(SiO2)', 'Acid InSolubles', 
                'Zinc(ZnO)', 'Nickel(NiO)', 'Vanadium(V2O3)', 'Chromium(Cr2O3)'
            ],
            'Result (%)': [23.48, 45.49, 0.10, 0.01, 0.23, 0.01, 0.05, 0.01, 0.02, 0.10, 1.53, 0.86, 0.01, 0.01, 0.00, 0.07]
        })


    st.title("❄️ Cooling Tower Master (Global Expert Ver.)")

    st.info("Scale/Corrosion/Deposit 통합 진단 및 성분 분석 시스템")



    # 4개 탭 구조

    tab1, tab2, tab3, tab4, tab5 = st.tabs([

        "💧 Water Balance (물질수지)", 

        "⚗️ Water Chemistry (수질진단)", 

        "💊 Chemical Program (약품)", 

        "🔬 Lab & Troubleshooting (성분분석)",

        "🛠️ TSA 정밀진단"

    ])



# ======================================================================
    # Tab 1: Water Balance (핵심 수정: 계절별 증발량 보정)
    # ======================================================================
    with tab1:
        st.subheader("1. Cooling Tower Design Data")

        # [수정] 계절 선택 기능 추가 (증발량 정밀도 향상)
        col_season, col_dummy = st.columns([1, 1])
        with col_season:
            season_mode = st.selectbox("📅 운전 계절 (Season Factor)", 
                                     ["Summer (여름/혹서기)", "Spring/Fall (봄/가을)", "Winter (겨울/혹한기)"])
            
            # F값 설정 (이론적 최대치 0.0018에 대한 현열/잠열 보정계수)
            # - 여름: 증발(잠열) 냉각 의존도가 높음 -> Factor 높음 (0.85)
            # - 겨울: 대류(현열) 냉각 비율이 높음 -> 증발량 감소 -> Factor 낮음 (0.55)
            if "Summer" in season_mode:
                f_factor = 0.85
                st.caption("🔥 **여름철:** 증발 냉각 비율 높음 (보정계수 0.85 적용)")
            elif "Winter" in season_mode:
                f_factor = 0.55
                st.caption("❄️ **겨울철:** 현열(대류) 냉각 비율 높음 (보정계수 0.55 적용)")
            else:
                f_factor = 0.75
                st.caption("🍂 **봄/가을:** 표준 운전 조건 (보정계수 0.75 적용)")

        col1, col2 = st.columns(2)
        with col1:
            circ_rate = st.number_input("Circulation Rate (순환수량, m3/hr)", value=1000.0)
            delta_t = st.number_input("Delta T (온도차, °C)", value=5.0)
        with col2:
            coc = st.slider("Cycles of Concentration (농축배수)", 1.0, 10.0, 5.0)
            holding_vol = st.number_input("System Volume (보유수량, m3)", value=300.0)

        # [Global Expert Formula] Evap = Q * dT * 0.0018 * F
        # 0.0018은 물의 비열(1) / 증발잠열(약 550~600)의 이론적 비율
        evap_factor = 0.0018 * f_factor
        evap = circ_rate * delta_t * evap_factor 

        windage = circ_rate * 0.0005        
        
        if coc > 1:
            blowdown = (evap / (coc - 1)) - windage
            if blowdown < 0: blowdown = 0 
        else: 
            blowdown = 0 
        
        makeup = evap + blowdown + windage 
        st.session_state['final_blowdown'] = blowdown
        
        if blowdown > 0: 
            hti = 0.693 * holding_vol / (blowdown + windage) 
        else: 
            hti = 999.9
        st.session_state['final_hti'] = hti

        st.markdown("---")
        
        # [시각화 & 요약]
        c_chart, c_metric = st.columns([1.2, 1])
        
        with c_chart:
            labels = ['Evaporation (증발)', 'Blowdown (배수)', 'Windage (비산)']
            values = [evap, blowdown, windage]
            
            # 파이 차트 색상 및 설정
            fig_bal = go.Figure(data=[go.Pie(
                labels=labels, 
                values=values, 
                hole=.4, 
                marker_colors=['#3498DB', '#E74C3C', '#95A5A6'],
                textinfo='percent+label' # 비율과 라벨 같이 표시
            )])
            fig_bal.update_layout(
                title_text="Water Usage Breakdown", 
                height=320, 
                margin=dict(t=40, b=10, l=10, r=10),
                showlegend=False
            )
            st.plotly_chart(fig_bal, use_container_width=True)

        with c_metric:
            st.subheader("📊 Operation Summary")
            
            # [핵심 수정] 컬럼을 2개 -> 3개로 늘립니다!
            op_m1, op_m2, op_m3 = st.columns(3)
            
            with op_m1:
                st.metric("증발량 (Evap)", f"{evap:.1f} m³/hr", f"Factor {evap_factor:.4f}")
                st.metric("보급수 (Make-up)", f"{makeup:.1f} m³/hr")
                
            with op_m2:
                st.metric("배수량 (Blowdown)", f"{blowdown:.1f} m³/hr")
                
                # 반감기 상태 표시 로직
                ht_msg = "✅ Good"
                ht_color = "normal"
                if hti > 48: 
                    ht_msg = "⚠️ Long"
                    ht_color = "inverse"
                elif hti < 4: 
                    ht_msg = "⚠️ Short"
                    ht_color = "inverse"
                st.metric("반감기 (Half Life)", f"{hti:.1f} hr", delta=ht_msg, delta_color=ht_color)
                
            with op_m3:
                # [여기!] 3번째 칸에 비산수량을 표시합니다.
                st.metric("비산수량 (Windage)", f"{windage:.2f} m³/hr", "0.05% Loss")
                st.caption(f"💧 **보유수량:** {holding_vol:.0f} m³")

    # ======================================================================

    # Tab 2: Water Chemistry (pH 수식 변경)

    # ======================================================================

    with tab2:

        st.subheader("2. Prediction & Diagnosis Simulator")

        st.markdown("보충수(Make-up) 수질을 기반으로 농축 후 순환수 수질을 **예측**하고 **5대 지수**를 진단합니다.")



        if 'makeup_data' not in st.session_state:

            st.session_state.makeup_data = pd.DataFrame({

                'Item': ['pH', 'Cond (µS)', 'Ca-H (ppm)', 'Mg-H (ppm)', 'M-Alk (ppm)', 'Cl (ppm)', 'SO4 (ppm)', 'SiO2 (ppm)'],

                'Value': [7.5, 200.0, 40.0, 10.0, 50.0, 20.0, 10.0, 10.0]

            })



        col_sim1, col_sim2 = st.columns([1, 1])

        

        with col_sim1:

            st.markdown("###### ① 보충수(Make-up) 수질 입력")

            edited_mu = st.data_editor(st.session_state.makeup_data, hide_index=True, key="mu_editor", height=280)

        

        with col_sim2:

            st.markdown("###### ② 운전 목표 및 관리 기준 설정")

            target_coc = st.slider("Target Cycles (목표 농축배수)", 1.0, 10.0, 5.0, 0.1, key="sim_coc")

            sim_temp = st.slider("Temperature (°C)", 10.0, 60.0, 35.0, 1.0, key="sim_temp")

            sim_turbidity = st.number_input("예상 탁도 (NTU) - Deposit 예측용", 0.0, 100.0, 10.0)

            

            use_acid = st.checkbox("Acid Feed (황산 주입 모드)", value=False)



            if use_acid:

                target_ph = st.number_input("Target pH (Control)", 6.5, 8.5, 7.8, 0.1)

                st.info("🧪 pH 컨트롤러 설정값으로 계산합니다.")

            else:

                # 1. 기초 데이터 확보

                try:

                    temp_mu = dict(zip(edited_mu['Item'], edited_mu['Value'])) 

                    base_alk = temp_mu.get('M-Alk (ppm)', 50.0)

                except:

                    base_alk = 50.0



                # 2. 농축 알칼리도 계산

                cycle_alk = base_alk * target_coc

                if cycle_alk < 1: cycle_alk = 1.0



                # 3. pH 8.3 Breakpoint Logic (글로벌 표준)

                # 알칼리도가 일정 수준(약 350~400ppm)을 넘으면 pH 8.3을 돌파하며 탄산(CO3) 완충 구간에 진입합니다.

                # Threshold Point: Puckorius 식 기준 pH 8.3이 되는 Alk 값 = 약 370 ppm

                

                alk_threshold = 370.0 



                if cycle_alk < alk_threshold:

                    # [Case A: pH < 8.3 구간] Bicarbonate Dominant

                    # 기울기가 더 가파른 수식 적용 (저농축 구간)

                    # Formula: pH = 2.0 * log10(Alk) + 3.15 (보정식)

                    est_ph_raw = (2.0 * math.log10(cycle_alk)) + 3.15

                    phase_msg = "Bicarbonate Phase (pH < 8.3)"

                else:

                    # [Case B: pH >= 8.3 구간] Carbonate Buffering

                    # 기울기가 완만해지는 Puckorius 평형 수식 적용 (고농축 구간)

                    # Formula: pH = 1.465 * log10(Alk) + 4.54

                    est_ph_raw = (1.465 * math.log10(cycle_alk)) + 4.54

                    phase_msg = "Carbonate Buffer Phase (pH ≥ 8.3)"



                # 4. 물리적 한계 (Ceiling)

                # 대기 개방형 냉각탑은 통상 pH 9.3 이상 상승하기 어려움 (탄산염 평형)

                est_ph = min(est_ph_raw, 9.3)



                # 5. 결과 표시

                target_ph = st.number_input(f"Predicted pH ({phase_msg})", value=float(f"{est_ph:.2f}"), disabled=True)

                

                # 분석 멘트

                if est_ph >= 8.3:

                    st.caption(f"💡 **분석:** 농축 알칼리도 {int(cycle_alk)}ppm → **탄산(CO3) 완충 구간** 진입 (pH 상승 둔화)")

                else:

                    st.caption(f"💡 **분석:** 농축 알칼리도 {int(cycle_alk)}ppm → **중탄산(HCO3) 지배 구간** (pH 상승 가속)")

            

            btn_run = st.button("🚀 Run Simulation (비교 분석)", type="primary", use_container_width=True)



        if btn_run:

            st.session_state.makeup_data = edited_mu 

            mu_dict = dict(zip(edited_mu['Item'], edited_mu['Value']))

            

            pred_ca = mu_dict['Ca-H (ppm)'] * target_coc

            pred_mg = mu_dict['Mg-H (ppm)'] * target_coc

            pred_cl = mu_dict['Cl (ppm)'] * target_coc

            pred_sio2 = mu_dict['SiO2 (ppm)'] * target_coc

            pred_cond = mu_dict['Cond (µS)'] * target_coc

            

            if use_acid:

                pred_alk = mu_dict['M-Alk (ppm)'] * target_coc * 0.6

                acid_so4 = (mu_dict['M-Alk (ppm)'] * target_coc) * 0.9

                pred_so4 = (mu_dict['SO4 (ppm)'] * target_coc) + acid_so4

            else:

                pred_alk = mu_dict['M-Alk (ppm)'] * target_coc

                pred_so4 = mu_dict['SO4 (ppm)'] * target_coc



            temp_k = sim_temp + 273.15

            tds_val = pred_cond * 0.7

            

            val_a = (math.log10(max(tds_val, 1)) - 1) / 10

            val_b = -13.12 * math.log10(temp_k) + 34.55

            val_c = math.log10(max(pred_ca, 1)) - 0.4

            val_d = math.log10(max(pred_alk, 1))

            

            pHs = (9.3 + val_a + val_b) - (val_c + val_d)

            

            lsi = target_ph - pHs

            rsi = (2 * pHs) - target_ph

            p_eq = 1.465 * math.log10(max(pred_alk, 1)) + 4.54

            psi = (2 * pHs) - p_eq

            ls_idx = (pred_cl + pred_so4) / pred_alk if pred_alk > 0 else 0

            

            st.divider()

            st.subheader(f"📊 수질 예측 비교 분석 (농축배수: {target_coc}배)")

            

            comp_data = [

                {"Item": "pH", "Make-up": mu_dict['pH'], "Cooling (Pred)": target_ph, "Limit (Max)": 9.0},

                {"Item": "Calcium (Ca-H)", "Make-up": mu_dict['Ca-H (ppm)'], "Cooling (Pred)": pred_ca, "Limit (Max)": 800.0},

                {"Item": "Magnesium (Mg-H)", "Make-up": mu_dict['Mg-H (ppm)'], "Cooling (Pred)": pred_mg, "Limit (Max)": 300.0},

                {"Item": "M-Alkalinity", "Make-up": mu_dict['M-Alk (ppm)'], "Cooling (Pred)": pred_alk, "Limit (Max)": 500.0},

                {"Item": "Chloride (Cl)", "Make-up": mu_dict['Cl (ppm)'], "Cooling (Pred)": pred_cl, "Limit (Max)": 500.0},

                {"Item": "Sulfate (SO4)", "Make-up": mu_dict['SO4 (ppm)'], "Cooling (Pred)": pred_so4, "Limit (Max)": 1200.0},

                {"Item": "Silica (SiO2)", "Make-up": mu_dict['SiO2 (ppm)'], "Cooling (Pred)": pred_sio2, "Limit (Max)": 150.0},

                {"Item": "Conductivity", "Make-up": mu_dict['Cond (µS)'], "Cooling (Pred)": pred_cond, "Limit (Max)": 5000.0},

            ]

            

            df_comp = pd.DataFrame(comp_data)

            

            st.caption("※ 'Limit (Max)' 컬럼의 숫자를 클릭하여 현장 기준에 맞게 수정하십시오.")

            edited_comp = st.data_editor(

                df_comp, 

                column_config={

                    "Item": st.column_config.TextColumn("항목", disabled=True),

                    "Make-up": st.column_config.NumberColumn("보충수 (원수)", format="%.1f", disabled=True),

                    "Cooling (Pred)": st.column_config.NumberColumn("순환수 (예측)", format="%.1f", disabled=True),

                    "Limit (Max)": st.column_config.NumberColumn("관리 기준 (Edit)", format="%.0f", min_value=0, max_value=10000)

                },

                hide_index=True, use_container_width=True, key="limit_editor"

            )

            

            warnings = []

            for index, row in edited_comp.iterrows():

                if row['Cooling (Pred)'] > row['Limit (Max)']:

                    warnings.append(f"⚠️ **{row['Item']}** 농도({row['Cooling (Pred)']})가 관리 기준({row['Limit (Max)']})을 초과했습니다.")

            

            if warnings:

                with st.container(border=True):

                    st.error("🚨 **관리 기준 초과 경보 (Limit Violation)**")

                    for w in warnings: st.write(w)

                    st.write("👉 **Action:** 농축배수(Cycles)를 낮추거나, 전용 약품 처리를 강화하십시오.")

            else:

                st.success("✅ 모든 항목이 관리 기준 이내입니다. (Stable Operation)")



            st.markdown("#### 🧭 5대 핵심 지수 진단 (Indices Diagnosis)")

            m1, m2, m3, m4, m5 = st.columns(5)

            

            lsi_col = "inverse" if lsi > 1.5 or lsi < 0 else "normal"

            m1.metric("1. LSI (Scale)", f"{lsi:.2f}", "Risk" if lsi>1.5 else "Safe", delta_color=lsi_col)

            

            rsi_state = "Stable"

            if rsi < 5.0: rsi_state = "Scale Risk"

            elif rsi > 8.5: rsi_state = "Corr Risk"

            m2.metric("2. RSI (General)", f"{rsi:.2f}", rsi_state, delta_color="inverse" if "Risk" in rsi_state else "normal")

            

            m3.metric("3. PSI (Stability)", f"{psi:.2f}")

            

            ls_msg = "Safe"

            ls_col = "normal"

            if ls_idx > 1.2: ls_msg="Pitting!"; ls_col="inverse"

            m4.metric("4. Pitting (L-S)", f"{ls_idx:.2f}", ls_msg, delta_color=ls_col)

            

            dep_msg = "Clean"

            dep_col = "normal"

            if sim_turbidity > 20: dep_msg="Deposit!"; dep_col="inverse"

            m5.metric("5. Deposit Risk", f"{sim_turbidity} NTU", dep_msg, delta_color=dep_col)



            st.divider()

            with st.expander("📘 지수별 상세 해석 및 가이드 (Click to Open)", expanded=True):

                col_guide1, col_guide2 = st.columns(2)

                with col_guide1:

                    st.markdown("### 🔍 현재 수질 정밀 분석")

                    if lsi > 2.0:

                        st.error(f"**1. LSI ({lsi:.2f}) - 심각한 스케일:** 탄산칼슘이 배관에 두껍게 쌓일 위험이 높습니다. 산 주입 필수.")

                    elif lsi > 0.5:

                        st.warning(f"**1. LSI ({lsi:.2f}) - 스케일 경향:** 약한 스케일 생성 조건입니다. 방지제로 제어 가능합니다.")

                    elif lsi < -0.5:

                        st.warning(f"**1. LSI ({lsi:.2f}) - 부식 경향:** 물이 배관을 녹일 수 있습니다 (Corrosive).")

                    else:

                        st.success(f"**1. LSI ({lsi:.2f}) - 안정:** 스케일과 부식 균형이 잘 맞습니다.")



                    if rsi < 5.0:

                        st.error(f"**2. RSI ({rsi:.2f}) - 강한 스케일:** 5.0 미만은 열교환기 막힘의 주원인입니다.")

                    elif rsi > 7.5:

                        st.warning(f"**2. RSI ({rsi:.2f}) - 부식성:** 탄소강 배관 부식 주의. 방식제 농도를 높이십시오.")

                    else:

                        st.success(f"**2. RSI ({rsi:.2f}) - 안정 범위:** (6.0 ± 1.0) 범위를 만족합니다.")



                    if ls_idx > 1.2:

                        st.error(f"**4. Pitting ({ls_idx:.2f}) - 국부 부식 위험:** 염소/황산 이온 비율이 높습니다. 배관에 구멍(Pitting)이 뚫릴 수 있습니다.")

                    elif ls_idx > 0.8:

                        st.warning(f"**4. Pitting ({ls_idx:.2f}) - 주의:** 점부식 발생 가능성이 증가하고 있습니다.")

                    else:

                        st.success(f"**4. Pitting ({ls_idx:.2f}) - 안전:** 부식 촉진 이온 농도가 적절합니다.")



                with col_guide2:

                    st.markdown("### 📖 지수별 관리 기준 (Reference)")

                    st.info("""

                    * **LSI (Langelier Saturation Index):** 이론적 탄산칼슘 포화도

                        * `> 2.0`: 심각한 스케일 / `0 ~ 1.0`: 관리 범위 / `< -1.0`: 심각한 부식

                    * **RSI (Ryznar Stability Index):** 실제 현장 경험 지수 (가장 중요)

                        * `< 5.0`: 스케일 위험 / `6.0`: 이상적 / `> 7.5`: 부식 위험

                    * **PSI (Puckorius Scaling Index):** 고 pH 운전 시 완충 능력 고려

                        * RSI와 유사하게 해석 (< 6.0 스케일, > 7.0 부식)

                    * **L-S Index (Larson-Skold):** 국부 부식(Pitting) 예측 지수

                        * `(Cl + SO4) / Alkalinity` 비율

                        * `< 0.8`: 안전 / `> 1.2`: 스테인리스/탄소강 점부식 위험

                    * **Turbidity (Deposit):** 부유물질 침적 위험

                        * `> 20 NTU`: 슬러지 침적 우려 (분산제 필요)

                    """) 

 
# ======================================================================
    # Tab 3: Chemical Program (지능형 선정 및 소요량 계산 - 오류 수정본)
    # ======================================================================
    with tab3:
        st.subheader("💡 Intelligent Chemical Selection System")
        
        # [오류 해결 1] 변수 안전 확보 (Tab 1, 2 데이터 연동)
        calc_blowdown = st.session_state.get('final_blowdown', 0.0)
        mu_df = st.session_state.makeup_data
        mu_dict = dict(zip(mu_df['Item'], mu_df['Value']))
        
        ca_h = mu_dict.get('Ca-H (ppm)', 40.0)
        # Tab 2 시뮬레이션 미실행 시를 대비한 기본값 처리
        curr_ph = st.session_state.get('sim_target_ph', mu_dict.get('pH', 7.5))
        curr_lsi = st.session_state.get('sim_lsi', 1.0)
        
        # [오류 해결 2] 계산용 배수량 변수(estim_blow) 선행 정의
        col_bal1, col_bal2 = st.columns([1, 2])
        with col_bal1:
            estim_blow = st.number_input("운전 배수량 (Blowdown, m3/hr)", 
                                         value=float(calc_blowdown), 
                                         key="estim_blow_tab3_v26")
        with col_bal2:
            st.info(f"💡 **참고:** Tab 1의 계산 배수량({calc_blowdown:.1f} m³/hr)이 연동되었습니다.")

        st.divider()

        # 1. Dual-Filter 선정 알고리즘 (LSI + SK Matrix)
        final_prod = ""
        reason = ""

        if curr_lsi > 2.0:
            if curr_ph > 8.5: # SK 알칼리 로직
                final_prod = "DREW 11-635"
                reason = "고농축/고알칼리 수질에서 성분 석출이 없는 All-Organic 처방이 필수적입니다."
            else:
                final_prod = "DREW 2305 (High)"
                reason = "고부하 현장용으로, Millennium 시리즈 중 가장 강력한 스케일 분산력을 제공합니다."
        elif 0.5 <= curr_lsi <= 2.0:
            if ca_h < 50: # SK 저경도 로직
                final_prod = "PERFORMAX 2525"
                reason = "보충수 Ca-H가 낮아 부식 위험이 높으므로 저경도 전용 방식제를 권장합니다."
            elif curr_ph > 7.8:
                final_prod = "DREWGARD 308"
                reason = "알칼리성 수질(pH 7.5~9.2)에서 안정적인 방스케일 성능을 발휘합니다."
            else:
                final_prod = "PERFORMAX 2021A"
                reason = "중성 영역의 표준 수질로, 가장 경제적이고 안정적인 인산염계 처방입니다."
        else:
            final_prod = "PERFORMAX 2525"
            reason = "LSI가 낮아 부식 성향이 매우 강한 수질입니다. 강력한 금속 보호막 형성이 필요합니다."

        # 2. 결과 대시보드 출력
        with st.container(border=True):
            st.markdown(f"### 🎯 최적 처방 제품: **{final_prod}**")
            item_info = next((item for item in PRODUCT_CATALOG['Cooling']['Main_Inhibitor'] if item['Name'] == final_prod), None)
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.info(f"**LSI:** {curr_lsi:.2f}\n**Ca-H:** {ca_h:.1f} ppm\n**pH:** {curr_ph:.1f}")
            with c2:
                if item_info:
                    st.write(f"**제품 타입:** {item_info['Type']}")
                    st.write(f"**주요 특징:** {item_info['Feature']}")
                st.warning(f"**선정 근거:** {reason}")

        st.divider()
        
        # 3. 약품 소요량 계산 (Inhibitor / Dispersant / Biocide)
        col_c1, col_c2, col_c3 = st.columns(3)
        
        with col_c1:
            st.markdown("#### 🛡️ Inhibitor")
            chem_list = PRODUCT_CATALOG['Cooling']['Main_Inhibitor']
            # 추천 제품을 기본값으로 설정
            default_idx = [i for i, c in enumerate(chem_list) if c['Name'] == final_prod]
            sel_inh = st.selectbox("억제제 선택", [c['Name'] for c in chem_list], 
                                   index=default_idx[0] if default_idx else 0, key="sel_inh_v26")
            inh_data = next((item for item in chem_list if item['Name'] == sel_inh), None)
            inh_dose = st.number_input("주입농도 (ppm)", value=float(inh_data['Dosage']), key="inh_dose_v26")
            usage_inh = (estim_blow * 24 * inh_dose) / 1000.0

        with col_c2:
            st.markdown("#### 🧪 Dispersant")
            disp_list = PRODUCT_CATALOG['Cooling']['Dispersant']
            sel_disp = st.selectbox("분산제 선택", [d['Name'] for d in disp_list], key="sel_disp_v26")
            disp_data = next((item for item in disp_list if item['Name'] == sel_disp), None)
            disp_dose = st.number_input("분산제 농도 (ppm)", value=float(disp_data['Dosage']), key="disp_dose_v26")
            usage_disp = (estim_blow * 24 * disp_dose) / 1000.0

        with col_c3:
            st.markdown("#### 🦠 Biocide")
            bio_list = PRODUCT_CATALOG['Cooling']['Biocide']
            sel_bio = st.selectbox("살균제 선택", [b['Name'] for b in bio_list], key="sel_bio_v26")
            bio_data = next((item for item in bio_list if item['Name'] == sel_bio), None)
            bio_dose = st.number_input("살균제 농도 (ppm)", value=float(bio_data['Dosage']), key="bio_dose_v26")
            usage_bio = (estim_blow * 24 * bio_dose) / 1000.0

        # 4. 시각화 대시보드
        st.divider()
        st.markdown("### 📊 일일 약품 소요량 요약")
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Total {sel_inh}", f"{usage_inh:.1f} kg/day")
        m2.metric(f"Total {sel_disp}", f"{usage_disp:.1f} kg/day")
        m3.metric(f"Total {sel_bio}", f"{usage_bio:.1f} kg/day")

        chart_data = pd.DataFrame({
            'Category': ['Inhibitor', 'Dispersant', 'Biocide'],
            'Usage (kg/day)': [usage_inh, usage_disp, usage_bio]
        })
        fig_chem = px.bar(chart_data, x='Category', y='Usage (kg/day)', color='Category',
                          text=chart_data['Usage (kg/day)'].apply(lambda x: f'{x:.1f} kg'))
        fig_chem.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig_chem, use_container_width=True)
    # ======================================================================

    # Tab 4: Lab Analysis & Trouble Shooting

    # ======================================================================

    with tab4:
        st.header("🔬 Deposit Analysis (ICP-OES Data Analysis)")
        st.caption("※ 성분 수치를 입력하면 자동으로 무기염 총합(Sum)과 각 항목의 비중(%)을 계산합니다.")
        
        # [입력] 16개 항목 Data Editor
        edited_deposit = st.data_editor(st.session_state.deposit_data, hide_index=True, use_container_width=True, key="dep_edit_t1")
        
        # [계산] 무기염 총합 및 비중(%) 계산 열 추가
        sum_inorganic = edited_deposit['Result (%)'].sum()
        edited_deposit['비중 (%)'] = (edited_deposit['Result (%)'] / sum_inorganic * 100).round(2) if sum_inorganic > 0 else 0
        
        st.markdown(f"#### 📊 분석 결과 요약: **무기염 총합 (InOrganic Salt SUM) = {sum_inorganic:.2f}%**")
        st.dataframe(edited_deposit, hide_index=True, use_container_width=True)

        # [출력] 가로 막대 그래프 (Horizontal Bar Chart)
        st.divider()
        st.subheader("📊 성분별 비중 분석 (Deposit Composition)")
        fig_dep = px.bar(edited_deposit, x='Result (%)', y='item', orientation='h', 
                         text_auto='.1f', color='item',
                         title="Deposit Component Analysis (Horizontal Bar)")
        # 보기 편하도록 비중 순서대로 정렬 및 높이 조절
        fig_dep.update_layout(showlegend=False, height=550, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_dep, use_container_width=True)

        # [출력] 화학 반응식 박스 (항상 노출)
        st.divider()
        st.subheader("💡 주요 성분별 화학적 생성 기전 (Chemical Reaction Mechanism)")
        
        col_rx1, col_rx2 = st.columns(2)
        with col_rx1:
            with st.container(border=True):
                st.info("**1. 알루미늄($Al_2O_3$) 및 황산염($SO_4$)**")
                st.latex(r"Al^{3+} + 3OH^- \rightarrow Al(OH)_3 \downarrow")
                st.caption("수산화알루미늄 침전: 주로 응집제(PAC) Carryover에 의해 발생하며 끈적한 슬러지가 타 성분을 응집시킴.")
                st.latex(r"2Al^{3+} + 3SO_4^{2-} \rightarrow Al_2(SO_4)_3")
                st.caption("황산알루미늄 복합염: 산 주입 과다 또는 원수 내 황산염 농도가 높을 때 생성되는 단단한 스케일.")

        with col_rx2:
            with st.container(border=True):
                st.info("**2. 산화철($Fe_2O_3$) 및 실리카($SiO_2$)**")
                st.latex(r"4Fe + 3O_2 \rightarrow 2Fe_2O_3")
                st.caption("산화철(녹): 배관 내부 부식의 직접적인 결과물이며 방식 처리가 부족할 때 주로 검출됨.")
                st.latex(r"Mg^{2+} + SiO_3^{2-} \rightarrow MgSiO_3 \downarrow")
                st.caption("규산마그네슘: 실리카 농축 한계 초과 시 마그네슘과 결합하여 형성되는 매우 단단한 난용성 스케일.")
        with tab5:
           draw_trouble_shooter("Cooling")  #

# ==============================================================================
# [Module 2] Boiler Master Pro (오류 완전 해결 및 물질수지/약품설계 강화)
# ==============================================================================
elif "Boiler" in program_mode:
    # 1. 초기 데이터 및 세션 설정 (AttributeError 방지)
    if 'b_data_feed' not in st.session_state:
        st.session_state.b_data_feed = pd.DataFrame({
            'Item': ['pH', 'Cond (uS/cm)', 'Hardness (ppm)', 'Cl (ppm)', 'SiO2 (ppm)', 'M-Alk (ppm)', 'Fe (ppm)'],
            'Feedwater': [8.5, 150.0, 1.0, 15.0, 2.0, 40.0, 0.05]
        })

    # 세션 결과값 초기화 (AttributeError 방지용 기본값)
    if 'b_res_store' not in st.session_state:
        st.session_state.b_res_store = {
            'steam': 10.0, 'feed': 10.7, 'blow': 0.7, 'coc': 15.0, 'dose_ppm': 100.0, 'naoh_pct': 20.0
        }

    st.title("🔥 Boiler Master Pro")
    st.info("증기 발생량 대비 정밀 물질수지(Water Balance)와 가성소다 함량 기반 수질 예측 시스템입니다.")

    tab_sim, tab_chem_prog, tab_safety, tab_energy, tab_trouble = st.tabs([
        "💧Water Simulation & Balance", 
        "💊 Chemical Program (약품)", 
        "🎯 Na-PO4 Safety Map", 
        "🔥 Energy Cost",
        "🛠️ TSA 정밀진단"
    ])
    
# --- Tab 1: Water Simulation & Balance (응축수 회수율 반영 Ver) ---
    with tab_sim:
        st.subheader("1. Boiler Water Balance & Quality Prediction")
        
        col_b1, col_b2 = st.columns([1, 1.2])
        
        with col_b1:
            st.markdown("###### ① 급수 수질 데이터 (Feedwater Quality)")
            # [기능 개선] 보급수(Make-up) 수질을 기준으로 입력받음
            e_bf = st.data_editor(st.session_state.b_data_feed, hide_index=True, key="b_editor_expert_v2",
                                  column_config={"Feedwater": st.column_config.NumberColumn(format="%.1f")})
            mu_v = dict(zip(e_bf['Item'], e_bf['Feedwater']))
            st.caption("※ 위 데이터는 '보급수(Make-up)' 기준입니다.")

        with col_b2:
            st.markdown("###### ② 운전 조건 및 물질수지 (Mass Balance)")
            
            # 입력 변수
            b_steam = st.number_input("증기 생산량 (Steam, ton/hr)", value=10.0, key="b_steam_ex")
            b_pressure = st.number_input("운전 압력 (Pressure, bar)", value=10.0, key="b_press_ex")
            
            # [엔진 호출] 안토인 식으로 온도 계산
            sat_temp, sat_h = Boiler_Expert_Engine.get_steam_enthalpy(b_pressure)
            st.write(f"🔥 포화 온도: **{sat_temp} °C** (Antoine Eq. 적용)")

            st.divider()

            # [핵심 로직] 응축수 회수율 반영
            b_coc = st.slider("목표 농축배수 (Cycles)", 2.0, 50.0, 15.0, 0.5, key="b_coc_ex")
            b_return_pct = st.slider("응축수 회수율 (Condensate Return %)", 0, 100, 50, key="b_ret_ex")

            # --- [Global Expert 물질수지 계산] ---
            # 1. 블로우다운량 계산 (증기량 기준)
            # Blowdown = Steam / (Cycles - 1)
            if b_coc > 1:
                b_blowdown = b_steam / (b_coc - 1)
            else:
                b_blowdown = 0.0
            
            # 2. 총 급수량 (Total Feed) = 증기 + 블로우다운
            b_feedwater = b_steam + b_blowdown
            
            # 3. 응축수량 및 보급수량 분리
            # Feed = Makeup + Condensate
            b_condensate = b_feedwater * (b_return_pct / 100.0)
            b_makeup = b_feedwater - b_condensate
            
            # 결과 표시 (컨테이너)
            with st.container(border=True):
                c_m1, c_m2, c_m3 = st.columns(3)
                c_m1.metric("총 급수량 (Total Feed)", f"{b_feedwater:.1f} t/h")
                c_m2.metric("보급수 (Make-up)", f"{b_makeup:.1f} t/h", f"회수율 {b_return_pct}%")
                c_m3.metric("배수량 (Blowdown)", f"{b_blowdown:.1f} t/h")

            # 약품 농도 설정
            st.write("---")
            b_dose_ppm = st.number_input("청관제 목표농도 (ppm, 급수대비)", value=100.0, step=10.0, key="b_dose_ex")
            b_naoh_pct = st.number_input("청관제 내 가성소다(NaOH) 함량 (%)", value=20.0, step=1.0, key="b_naoh_ex")

            # 세션 저장 (Tab 2 약품 계산용)
            st.session_state.b_res_store = {
                'steam': b_steam, 'feed': b_feedwater, 'blow': b_blowdown, 
                'coc': b_coc, 'dose_ppm': b_dose_ppm, 'naoh_pct': b_naoh_pct
            }

        # [수질 예측 계산 - 혼합 수질 반영]
        # 급수 TDS = (보급수TDS * 보급수비율) + (응축수TDS * 응축수비율)
        # 통상 응축수 TDS는 매우 낮음 (약 2~5 ppm 가정)
        cond_tds_assumed = 5.0 
        mu_ratio = (100 - b_return_pct) / 100.0
        
        # 1. 혼합 급수(Mixed Feed) 수질 계산
        feed_cond = (mu_v['Cond (uS/cm)'] * mu_ratio) + (cond_tds_assumed * (b_return_pct/100.0))
        feed_alk = mu_v['M-Alk (ppm)'] * mu_ratio
        feed_cl = mu_v['Cl (ppm)'] * mu_ratio
        feed_sio2 = mu_v['SiO2 (ppm)'] * mu_ratio
        feed_fe = mu_v['Fe (ppm)'] * mu_ratio + (0.05 * (b_return_pct/100.0)) # 응축수 철분 0.05 가정

        # 2. 관수(Boiler Water) 농축 계산
        naoh_boost = b_dose_ppm * (b_naoh_pct / 100) * 1.25 # 가성소다에 의한 알칼리 상승
        
        p_alk = (feed_alk * b_coc) + naoh_boost
        p_ph = 9.3 + math.log10(max(p_alk, 1)) if p_alk > 0 else mu_v['pH']
        p_ph = min(p_ph, 12.3) # Max Ceiling
        
        p_cond = (feed_cond * b_coc) + (naoh_boost * 5.5)
        p_cl = feed_cl * b_coc
        p_sio2 = feed_sio2 * b_coc
        p_fe = feed_fe * b_coc

        # ASME 체크
        try:
            _, l_cond = Boiler_Expert_Engine.check_asme_standard(b_pressure, p_cond, p_sio2, p_alk)
        except:
            l_cond = 3000.0

        st.divider()
        st.subheader(f"📊 보일러 관수 수질 예측 (농축 {b_coc}배, 응축수 회수 {b_return_pct}%)")
        
        # [결과 테이블]
        p_df = pd.DataFrame({
            '측정 항목': ['pH (예측값)', 'Cond (uS/cm)', 'M-Alk (ppm)', 'SiO2 (ppm)', 'Cl (ppm)', 'Fe (ppm)'],
            '보급수 (Make-up)': [f"{mu_v['pH']:.1f}", f"{mu_v['Cond (uS/cm)']:.1f}", f"{mu_v['M-Alk (ppm)']:.1f}", f"{mu_v['SiO2 (ppm)']:.1f}", f"{mu_v['Cl (ppm)']:.1f}", f"{mu_v['Fe (ppm)']:.2f}"],
            '혼합 급수 (Feed)': ["-", f"{feed_cond:.1f}", f"{feed_alk:.1f}", f"{feed_sio2:.1f}", f"{feed_cl:.1f}", f"{feed_fe:.2f}"],
            '관수 (Boiler W)': [f"{p_ph:.1f}", f"{p_cond:.0f}", f"{p_alk:.0f}", f"{p_sio2:.1f}", f"{p_cl:.1f}", f"{p_fe:.2f}"],
            'ASME 기준': ["10.5~11.5", f"{l_cond:.0f} 이하", "P 비례", "P 비례", "-", "-"]
        })
        st.table(p_df)


# --- Tab 2: Chemical Program (보일러 약품 연동 안전 강화 버전) ---
    with tab_chem_prog:
        st.subheader("2. Integrated Boiler Chemical Program")
        
        # 세션 데이터 가져오기 (오류 방지)
        res = st.session_state.get('b_res_store', {'feed': 10.0, 'dose_ppm': 100.0})
        st.info(f"💡 **물질수지 기반 설계:** 급수량 {res['feed']:.1f} ton/hr | 청관제 목표 {res['dose_ppm']:.1f} ppm")
        st.markdown("---")
        
        c_col1, c_col2, c_col3 = st.columns(3)
        
        # 엑셀 데이터 가져오기 (안전 로딩)
        boiler_db = PRODUCT_CATALOG.get('Boiler', {})
        
        # 1. 탈산제 (Oxygen Scavenger)
        with c_col1:
            st.markdown("#### 🌬️ Oxygen Scavenger")
            # [안전장치] 여러 가지 이름으로 찾아보기
            oxy_list = boiler_db.get('Oxygen_Scavenger') or boiler_db.get('OxygenScavenger') or []
            
            if oxy_list:
                sel_oxy = st.selectbox("탈산제 선택", [o['Name'] for o in oxy_list], key="b_sel_oxy_safe")
                oxy_item = next((i for i in oxy_list if i['Name'] == sel_oxy), None)
                def_oxy = float(oxy_item['Dosage']) if oxy_item else 20.0
            else:
                st.warning("데이터 없음")
                sel_oxy = None
                def_oxy = 0.0
            
            oxy_dose = st.number_input("탈산제 농도 (ppm)", value=def_oxy, key="b_oxy_val_safe")
            usage_oxy = (res['feed'] * 24 * oxy_dose) / 1000.0

        # 2. 청관제 (Scale Inhibitor) - 여기가 문제였음!
        with c_col2:
            st.markdown("#### 🛡️ Scale Inhibitor")
            # [안전장치] Scale_Disp(신규) 또는 Inhibitor(기존) 둘 다 확인
            scale_list = boiler_db.get('Scale_Disp') or boiler_db.get('Inhibitor') or []
            
            if scale_list:
                sel_scale = st.selectbox("청관제 선택", [s['Name'] for s in scale_list], key="b_sel_scale_safe")
            else:
                st.warning("데이터 없음")
            
            # 청관제 농도는 시뮬레이션 목표값(dose_ppm)을 기본으로 사용
            scale_dose = st.number_input("청관제 농도 (ppm)", value=float(res['dose_ppm']), key="b_scale_val_safe")
            usage_scale = (res['feed'] * 24 * scale_dose) / 1000.0

        # 3. 복수처리제 (Condensate) - 여기도 문제였음!
        with c_col3:
            st.markdown("#### 🧪 Condensate")
            # [안전장치] Condensate(신규) 또는 '응축수 pH'(기존) 둘 다 확인
            cond_list = boiler_db.get('Condensate') or boiler_db.get('응축수 pH') or []
            
            if cond_list:
                sel_cond = st.selectbox("복수처리제 선택", [c['Name'] for c in cond_list], key="b_sel_cond_safe")
                cond_item = next((i for i in cond_list if i['Name'] == sel_cond), None)
                def_cond = float(cond_item['Dosage']) if cond_item else 5.0
            else:
                # 데이터가 아예 없을 경우 'None' 표시
                sel_cond = st.selectbox("복수처리제 선택", ["None"], key="b_sel_cond_none")
                def_cond = 0.0

            cond_dose = st.number_input("기타 농도 (ppm)", value=def_cond, key="b_cond_val_safe")
            usage_cond = (res['feed'] * 24 * cond_dose) / 1000.0

        st.divider()
        st.markdown("### 📊 일일 약품 소요량 (Daily Consumption)")
        
        b_plot_df = pd.DataFrame({
            'Category': ['Scavenger', 'Inhibitor', 'Condensate'],
            'Usage (kg/day)': [usage_oxy, usage_scale, usage_cond]
        })

        fig_b_chem = px.bar(b_plot_df, x='Category', y='Usage (kg/day)', color='Category',
                            text=b_plot_df['Usage (kg/day)'].apply(lambda x: f'{x:.1f} kg'))
        st.plotly_chart(fig_b_chem, use_container_width=True)
        

    # --- Tab 3: Na-PO4 Safety Map ---
    with tab_safety:
        st.subheader("3. Na-PO4 Coordinate Map")
        c_s1, c_s2 = st.columns([1, 2])
        with c_s1:
            with st.container(border=True):
                st.markdown("**현장 측정 데이터**")
                cur_ph = st.number_input("현재 pH", 8.0, 13.0, 10.5, 0.1, key="b_safe_ph_final")
                cur_po4 = st.number_input("현재 PO4 (ppm)", 0.0, 100.0, 20.0, 1.0, key="b_safe_po4_final")
        with c_s2:
            fig_map = go.Figure()
            fig_map.add_shape(type="rect", x0=10, y0=9.4, x1=40, y1=10.5, line=dict(color="Green"), fillcolor="rgba(0, 255, 0, 0.1)")
            x_r = np.linspace(0, 60, 100)
            fig_map.add_trace(go.Scatter(x=x_r, y=11.6-(x_r*0.025), mode='lines', name='Caustic Limit', line=dict(color='red', dash='dash')))
            fig_map.add_trace(go.Scatter(x=x_r, y=9.0-(x_r*0.01), mode='lines', name='Acidic Limit', line=dict(color='orange', dash='dash')))
            fig_map.add_trace(go.Scatter(x=[cur_po4], y=[cur_ph], mode='markers', marker=dict(size=15, color="blue"), name="Current"))
            fig_map.update_layout(xaxis_title="PO4 (ppm)", yaxis_title="pH", height=400)
            st.plotly_chart(fig_map, use_container_width=True)
# --- Tab 4: Energy Cost ---
    with tab_energy:
        st.subheader("4. Steam Production Cost Analysis")
        # 에러 방지용 세션 데이터 재호출
        if 'b_data_energy' not in st.session_state:
            st.session_state.b_data_energy = pd.DataFrame({
                'Parameter': ['Fuel Cost (KRW/m3)', 'Oper. Hours/Day', 'Make-up Temp (°C)', 'Condensate Temp (°C)'],
                'Value': [900.0, 24.0, 20.0, 85.0]
            })
        e_edit = st.data_editor(st.session_state.b_data_energy, hide_index=True, key="b_energy_final")
        e_v = dict(zip(e_edit['Parameter'], e_edit['Value']))
        f_cost = e_v.get('Fuel Cost (KRW/m3)', 900.0)
        
        # 시간당 연료비 = (증기량 * 증발잠열) / (연료발열량 * 효율) * 연료단가
        # 급수 엔탈피는 대략 온도(°C)와 비슷함 (1 kcal/kg/°C)
        # [수정] 아래 줄들의 들여쓰기를 안쪽으로 맞췄습니다.
        h_steam = 660 # 통상 10bar 증기 엔탈피
        h_feed = e_v.get('Make-up Temp (°C)', 20.0) # 급수 온도 반영 (KeyError 방지 추가)
        real_enthalpy = h_steam - h_feed 

        # 안전장치: steam 값이 없을 경우 대비
        steam_val = st.session_state.b_res_store.get('steam', 10.0)
        
        c_h = (steam_val * 1000 * real_enthalpy / 8500 / 0.85) * f_cost        

        st.metric("Estimated Hourly Fuel Cost", f"{int(c_h):,} KRW/hr")

    # [중요] tab_trouble은 tab_energy와 같은 라인에 있어야 합니다.
    with tab_trouble:
        draw_trouble_shooter("Boiler")
# ==============================================================================
# [Module 3] RO Master Pro (수질 항목 추가: Ba, Fe, Al 및 진단 로직 연동)
# ==============================================================================
elif "RO" in program_mode:
    # 0. 세션 상태 초기화 (항목 추가: Ba, Fe, Al)
    if 'ro_v26_data' not in st.session_state:
        st.session_state.ro_v26_data = pd.DataFrame({
            # Ba(바륨), Fe(철), Al(알루미늄) 항목 추가 및 기본값 설정
            '항목': ['Na', 'Ca', 'Mg', 'Ba', 'Fe', 'Al', 'NH4', 'Cl', 'SO4', 'HCO3', 'F', 'SiO2', 'PO4'],
            '농도 (mg/L)': [150.0, 60.0, 20.0, 0.05, 0.05, 0.02, 1.0, 200.0, 100.0, 150.0, 0.1, 20.0, 0.1]
        })
    
    # 이온 보정 메시지 초기화
    if 'ro_adj_msg' not in st.session_state:
        st.session_state.ro_adj_msg = "💡 이온 밸런스 오차가 크면 버튼을 눌러주세요."

    st.title("🌊 RO Master Pro: Expert Solution")
    
    # --- [1. 데이터 핸들링 및 전역 변수 설정] ---
    # 데이터 에디터 연동
    ro_df_main = st.session_state.ro_v26_data
    # 딕셔너리 변환 (새로 추가된 항목도 자동으로 포함됨)
    v_main = dict(zip(ro_df_main['항목'], pd.to_numeric(ro_df_main['농도 (mg/L)'], errors='coerce').fillna(0)))
    
    # 이온 밸런스 계산 (meq/L)
    # Ba, Fe, Al은 미량이라 밸런스 계산에 큰 영향은 없으나 정밀도를 위해 포함 가능 (여기선 주요 이온 위주 유지)
    meq_cat = (v_main['Na']/23.0) + (v_main['Ca']/20.0) + (v_main['Mg']/12.2) + (v_main['NH4']/18.0)
    meq_ani = (v_main['Cl']/35.5) + (v_main['SO4']/48.0) + (v_main['HCO3']/61.0)
    
    # 분모가 0일 경우 방어 로직
    if (meq_cat + meq_ani) > 0:
        b_err_final = ((meq_cat - meq_ani) / (meq_cat + meq_ani)) * 100
    else:
        b_err_final = 0.0

    # --- [2. UI 구성] ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 수질 분석", 
        "🔮 성능 열화", 
        "🚨 정밀 진단", 
        "💊 Chemical Program",
        "🛠️ 현장 진단 & CIP",
        "🚑 TSA 정밀진단"
    ])

  # [Tab 1] 수질 분석 및 데이터 입력 (삼투압 실시간 계산 추가 Ver)
    with tab1:
        st.subheader("Step 1. Feed Water Analysis & Brine Prediction")
        
        # 원수 운전 조건 입력 (기존 유지)
        col_input_top = st.columns(4)
        with col_input_top[0]:
            in_ph = st.number_input("원수 pH", value=7.5, step=0.1, format="%.2f", key="ro_in_ph")
        with col_input_top[1]:
            in_temp = st.number_input("원수 수온 (°C)", value=25.0, step=1.0, format="%.1f", key="ro_in_temp")
        with col_input_top[2]:
            in_rec = st.number_input("설계 회수율 (%)", value=75.0, step=1.0, format="%.1f", key="ro_in_rec")
        with col_input_top[3]:
            in_flow = st.number_input("생산 유량 (m3/hr)", value=50.0, step=1.0, key="ro_in_flow")

        st.divider()

        # 이온 데이터 입력 및 결과 표시
        col_t1_1, col_t1_2 = st.columns([1, 1.2])
        
        with col_t1_1:
            st.markdown("###### 🧪 이온 농도 입력 (mg/L)")
            st.caption("※ **Ba(바륨), Fe(철), Al(알루미늄)** 항목이 추가되어 정밀 진단에 활용됩니다.")
            ed_ro = st.data_editor(st.session_state.ro_v26_data, hide_index=True, key="ro_editor_v26_final", height=450)
            
            # 데이터 변경 감지 및 저장 (기존 유지)
            if not ed_ro.equals(st.session_state.ro_v26_data):
                st.session_state.ro_v26_data = ed_ro
                st.rerun()
            
            # 자동 이온 발란스 보정 (기존 유지)
            if st.button("🚀 자동 이온 발란스 보정 (Auto-Balance)", key="btn_adj_v26", use_container_width=True):
                diff = meq_ani - meq_cat
                if abs(diff) < 0.01:
                    st.session_state.ro_adj_msg = "✅ 이미 밸런스가 맞습니다."
                elif diff > 0:
                    val_add = diff * 23.0
                    st.session_state.ro_v26_data.loc[st.session_state.ro_v26_data['항목'] == 'Na', '농도 (mg/L)'] += val_add
                    st.session_state.ro_adj_msg = f"✅ **보정 완료:** 부족한 양이온을 맞추기 위해 **Na {val_add:.1f} mg/L**를 추가했습니다."
                else:
                    val_add = abs(diff) * 35.5
                    st.session_state.ro_v26_data.loc[st.session_state.ro_v26_data['항목'] == 'Cl', '농도 (mg/L)'] += val_add
                    st.session_state.ro_adj_msg = f"✅ **보정 완료:** 부족한 음이온을 맞추기 위해 **Cl {val_add:.1f} mg/L**를 추가했습니다."
                st.rerun()
            
            if "✅" in st.session_state.ro_adj_msg:
                st.success(st.session_state.ro_adj_msg)
            else:
                st.info(st.session_state.ro_adj_msg)

        with col_t1_2:
            # 1. 기초 파라미터 계산 (기존 로직)
            cf_final = 1 / (1 - (in_rec / 100))
            feed_tds = sum(v_main.values()) # TDS 합계
            brine_tds_final = feed_tds * cf_final
            brine_ph_final = in_ph + math.log10(cf_final)

            # -----------------------------------------------------------
            # [추가된 기능] 삼투압(Osmotic P) 및 운전압력 실시간 계산 로직
            # -----------------------------------------------------------
            # (1) 온도 보정: 삼투압은 절대온도(Kelvin)에 비례
            temp_k = in_temp + 273.15
            # (2) 삼투압 계수: TDS 1000ppm 당 약 0.75 bar (at 25°C 기준)
            osm_factor = 0.75 * (temp_k / 298.15)
            
            # (3) 삼투압 계산
            feed_osm_bar = (feed_tds / 1000) * osm_factor     # 원수 삼투압
            brine_osm_bar = (brine_tds_final / 1000) * osm_factor # 농축수 삼투압
            avg_osm_bar = (feed_osm_bar + brine_osm_bar) / 2  # 평균 삼투압
            
            # (4) 필요 운전 압력 (Pump Pressure) 예측
            # 운전압력 = 평균삼투압 + 막저항(NDP) + 시스템손실
            net_driving_p = 12.0 # 일반적인 BWRO 막 저항(NDP) 가정
            estim_feed_p = avg_osm_bar + net_driving_p + 2.0 # +배관/차압 손실 2bar
            # -----------------------------------------------------------

            st.markdown("###### 📊 Simulation Result (Brine & Pressure)")
            
            # [Row 1] 농축수 수질 및 이온 밸런스 (기존 표시)
            m1, m2, m3 = st.columns(3)
            m1.metric("농축수 pH", f"{brine_ph_final:.2f}", f"+{brine_ph_final - in_ph:.2f}")
            m2.metric("농축수 TDS", f"{brine_tds_final:.0f} ppm", f"x{cf_final:.1f}")
            
            err_color = "normal"
            if abs(b_err_final) > 5.0: err_color = "inverse"
            m3.metric("이온 밸런스 오차", f"{b_err_final:.2f}%", delta_color=err_color)

            # [Row 2] 삼투압 및 운전 압력 (새로 추가됨!)
            st.divider()
            p1, p2 = st.columns(2)
            p1.metric("평균 삼투압 (Osmotic)", f"{avg_osm_bar:.1f} bar", f"원수 {feed_osm_bar:.1f} bar")
            p2.metric("필요 운전 압력 (Feed P)", f"{estim_feed_p:.1f} bar", help="삼투압 + 막저항(12) + 손실(2) 고려")

            st.markdown("---")
            st.markdown(f"#### ✨ 농축수 예상 수질 (Concentrate)")
            # 표시할 주요 항목에 Ba, Fe, Al 추가 (기존 유지)
            p_targets = ['Ca', 'SO4', 'SiO2', 'Ba', 'Fe', 'Al']
            
            # 수질 비교 테이블 생성 (기존 유지)
            comp_df = pd.DataFrame({
                '항목': p_targets,
                '원수 (Feed)': [f"{v_main.get(i, 0):.2f}" for i in p_targets],
                '농축수 (Brine)': [f"{(v_main.get(i, 0)*cf_final):.2f}" for i in p_targets],
                '농축비': [f"x{cf_final:.1f}" for _ in p_targets]
            })
            st.table(comp_df)  

    # [Tab 2] 성능 열화 시뮬레이션
    with tab2:
        st.subheader("Step 2. 성능 열화(Degradation) 시뮬레이션")
        with st.expander("💡 수원별 권장 연간 변화율 가이드 (Reference)", expanded=True):
            st.markdown("""
            | 수원 종류 (Source) | 연간 유량 감소율 (Flux Decline) | 연간 염투과 증가율 (Salt Passage) |
            | :--- | :---: | :---: |
            | **지하수 (Well Water)** | 2 ~ 3 % | 3 ~ 5 % |
            | **지표수 (Surface Water)** | 5 ~ 7 % | 10 ~ 12 % |
            | **폐수 재이용 (Wastewater)** | 10 ~ 15 % | 15 ~ 20 % |
            """)
        
        c_t2_1, c_t2_2 = st.columns(2)
        with c_t2_1: a_rate_s = st.slider("연간 유량 감소율 (%)", 0.0, 20.0, 5.0, key="a_s")
        with c_t2_2: b_rate_s = st.slider("연간 염투과 증가율 (%)", 0.0, 30.0, 10.0, key="b_s")
        
        op_y = st.slider("📅 멤브레인 사용 년수 (Years)", 0.0, 10.0, 3.0, 0.5, key="y_s")
        
        # Tab 1 입력값 연동
        base_flow = in_flow 
        base_cond = brine_tds_final / cf_final / 0.65 # TDS 역산 추정
        
        a_f = (1 - (a_rate_s / 100)) ** op_y
        b_f = (1 + (b_rate_s / 100)) ** op_y
        
        p_f_res = base_flow * a_f
        p_c_res = base_cond * b_f

        m_t2_1, m_t2_2 = st.columns(2)
        m_t2_1.metric("예상 생산 유량", f"{p_f_res:.1f} m³/h", f"{int((a_f-1)*100)}%")
        m_t2_2.metric("예상 생산수 전도도", f"{p_c_res:.1f} μS/cm", f"+{int((b_f-1)*100)}%", delta_color="inverse")

        # 그래프 시각화
        y_ax = np.linspace(0, 10, 21)
        f_cv = [base_flow * ((1 - (a_rate_s / 100)) ** y) for y in y_ax]
        c_cv = [base_cond * ((1 + (b_rate_s / 100)) ** y) for y in y_ax]
        
        g1, g2 = st.columns(2)
        with g1:
            fig_f = go.Figure()
            fig_f.add_trace(go.Scatter(x=y_ax, y=f_cv, line=dict(color='#3498DB', width=3), name='Flow'))
            fig_f.add_trace(go.Scatter(x=[op_y], y=[p_f_res], mode='markers+text', text=[f"{p_f_res:.1f}"], textposition="top right", marker=dict(color='red', size=12)))
            fig_f.update_layout(title="Flow Decline Curve", xaxis_title="Years", yaxis_title="Flow (m3/h)", height=350)
            st.plotly_chart(fig_f, use_container_width=True)
        with g2:
            fig_c = go.Figure()
            fig_c.add_trace(go.Scatter(x=y_ax, y=c_cv, line=dict(color='#E74C3C', width=3), name='Salt Passage'))
            fig_c.add_trace(go.Scatter(x=[op_y], y=[p_c_res], mode='markers+text', text=[f"{p_c_res:.1f}"], textposition="top right", marker=dict(color='black', size=12)))
            fig_c.update_layout(title="Salt Passage Increase", xaxis_title="Years", yaxis_title="Conductivity", height=350)
            st.plotly_chart(fig_c, use_container_width=True)

    # [Tab 3] 정밀 진단 (수정: Ba, Fe, Al 연동 로직 적용)
    with tab3:
        st.subheader("🚨 Brine 정밀 진단 (Engineering Basis)")
        st.info(f"💡 진단 기준: 농축수 pH **{brine_ph_final:.2f}**, TDS **{brine_tds_final:.0f} ppm** (CF: {cf_final:.1f}배)")
        
        # 스케일 잠재력 계산 (Ba 연동 수정)
        sc_items = ['CaCO3', 'CaSO4', 'BaSO4', 'SiO2', 'PO4']
        
        # [수정] BaSO4 Potential 계산 (입력 데이터 연동)
        # BaSO4는 용해도가 매우 낮으므로 (Ksp ~ 1.1e-10), 미량이라도 농축되면 위험
        ba_val = v_main.get('Ba', 0.0)
        so4_val = v_main.get('SO4', 0.0)
        
        # Ba 농도가 0이면 위험도 0, 아니면 계산 (임의 계수 적용하여 %화)
        ba_pot = (ba_val * so4_val * (cf_final**2)) * 50.0 if ba_val > 0 else 0.0
        
        pots = [
            (brine_ph_final - 8.2) * 50 + 115,  # CaCO3
            (v_main['Ca'] * v_main['SO4'] * (cf_final**2)) / 24, # CaSO4
            ba_pot, # BaSO4 (실제 연동값)
            (v_main['SiO2'] * cf_final) / 1.2, # SiO2
            (v_main['Ca'] * v_main['PO4'] * (cf_final**2)) / 0.5 # PO4
        ]
        
        # 차트 출력
        fig_risk = px.bar(x=sc_items, y=pots, color=sc_items, 
                          title="Saturation Level (%) - Ba/Fe/Al 반영", 
                          text_auto='.1f')
        fig_risk.add_hline(y=100, line_dash="dot", line_color="red", annotation_text="Risk Limit")
        st.plotly_chart(fig_risk, use_container_width=True)
        
        # 진단 메시지
        c_diag1, c_diag2 = st.columns(2)
        with c_diag1:
            for name, pot in zip(sc_items, pots):
                if pot > 100: 
                    st.error(f"🔴 **{name}: {pot:.1f}% (석출 위험)** - 스케일 방지제 필수")
                else: 
                    st.success(f"🟢 {name}: {pot:.1f}% (안정)")
        
        with c_diag2:
            st.markdown("##### ⚠️ 금속 이온 오염 진단 (Metal Fouling)")
            # [추가] Fe, Al 진단 로직
            fe_conc_brine = v_main.get('Fe', 0.0) * cf_final
            al_conc_brine = v_main.get('Al', 0.0) * cf_final
            
            if fe_conc_brine > 0.3:
                st.warning(f"🔸 **철(Fe) 농축 농도 {fe_conc_brine:.2f} ppm** (관리기준 > 0.3)\n- 산화철 오염 가능성이 높습니다. 전처리 점검 필요.")
            else:
                st.info(f"🔹 철(Fe) 농축 농도 {fe_conc_brine:.2f} ppm (안정)")
                
            if al_conc_brine > 0.05:
                st.warning(f"🔸 **알루미늄(Al) 농축 농도 {al_conc_brine:.2f} ppm** (관리기준 > 0.05)\n- 알루미늄계 스케일 주의. pH 조절 고려.")
            else:
                st.info(f"🔹 알루미늄(Al) 농축 농도 {al_conc_brine:.2f} ppm (안정)")

    # [Tab 4] Chemical Program (약품 시뮬레이션)
    with tab4:
        st.subheader("💊 Chemical Dosing & Simulation (HRD Series)")
        st.info("💡 코드에 등록된 **'HRD 시리즈'** 약품 데이터를 기반으로 스케일 제어 효율을 시뮬레이션합니다.")

        ro_chem_list = PRODUCT_CATALOG['RO']['Antiscalant']
        CHEM_SIM_MAP = {
            'HRD-2200 (General)':    {'CaCO3': 0.15, 'CaSO4': 0.20, 'BaSO4': 0.15, 'SrSO4': 0.20, 'SiO2': 0.60, 'Mn': 1.0, 'Struvite': 0.8},
            'HRD-3000 (High Silica)':{'CaCO3': 0.25, 'CaSO4': 0.30, 'BaSO4': 0.20, 'SrSO4': 0.25, 'SiO2': 0.20, 'Mn': 1.0, 'Struvite': 0.8},
            'HRD-2050 (Struvite)':   {'CaCO3': 0.20, 'CaSO4': 0.25, 'BaSO4': 0.20, 'SrSO4': 0.25, 'SiO2': 0.70, 'Mn': 1.0, 'Struvite': 0.15},
            'HRD-2240 (High Sulfate)':{'CaCO3': 0.20, 'CaSO4': 0.15, 'BaSO4': 0.05, 'SrSO4': 0.10, 'SiO2': 0.70, 'Mn': 1.0, 'Struvite': 0.8}
        }

        with st.expander("🧪 시뮬레이션용 수질 농도 설정 (Ion Concentration)", expanded=True):
            col_i1, col_i2, col_i3, col_i4 = st.columns(4)
            # 탭 1의 입력값을 기본값으로 가져오기
            with col_i1:
                s_ca = st.number_input("Ca (ppm)", value=float(v_main['Ca']), step=10.0, key="s_ca_v2")
                s_mg = st.number_input("Mg (ppm)", value=float(v_main['Mg']), step=10.0, key="s_mg_v2")
            with col_i2:
                s_hco3 = st.number_input("HCO3 (ppm)", value=float(v_main['HCO3']), step=10.0, key="s_hco3_v2")
                s_so4 = st.number_input("SO4 (ppm)", value=float(v_main['SO4']), step=10.0, key="s_so4_v2")
            with col_i3:
                # Ba 값 연동
                s_ba = st.number_input("Ba (ppm)", value=float(v_main.get('Ba', 0.1)), format="%.2f", key="s_ba_v2")
                s_sio2 = st.number_input("SiO2 (ppm)", value=float(v_main['SiO2']), step=1.0, key="s_sio2_v2")
            with col_i4:
                # Fe/Al은 약품으로 제거 안됨 -> Mn 등 기타 항목
                s_mn = st.number_input("Mn (ppm)", value=0.5, format="%.2f", help="망간은 약품으로 제거되지 않음", key="s_mn_v2")
                s_po4 = st.number_input("PO4 (ppm)", value=float(v_main['PO4']), format="%.2f", key="s_po4_v2")

        st.divider()

        c_sel1, c_sel2 = st.columns([1.5, 1])
        with c_sel1:
            chem_names = [item['Name'] for item in ro_chem_list]
            sel_chem_name = st.selectbox("🎯 적용할 약품 선택 (PRODUCT_CATALOG)", chem_names)
            sel_chem_info = next(item for item in ro_chem_list if item['Name'] == sel_chem_name)
            st.caption(f"ℹ️ **특징:** {sel_chem_info['Desc']} | **Target:** {', '.join(sel_chem_info['Target'])}")

        with c_sel2:
            rec_dose = float(sel_chem_info['Dosage'])
            input_dose = st.slider("주입량 (Dosage, ppm)", 0.0, 10.0, rec_dose, 0.5, key="sim_dose_v2")

        # 시뮬레이션 로직
        sat_raw = {
            "CaCO3": (s_ca * s_hco3) / 1000.0,    
            "CaSO4": (s_ca * s_so4) / 1500.0,
            "BaSO4": (s_ba * s_so4) * 150.0,       
            "SiO2":  (s_sio2 / 120.0) * 100.0,     
            "Mn":    (s_mn / 0.05) * 100.0,
            "Struvite": (s_mg * s_po4) * 10.0
        }

        eff_factors = CHEM_SIM_MAP.get(sel_chem_name, 
                                     {'CaCO3': 0.5, 'CaSO4': 0.5, 'BaSO4': 0.5, 'SiO2': 0.8, 'Mn': 1.0, 'Struvite': 0.8})
        
        dose_ratio = input_dose / rec_dose if rec_dose > 0 else 0
        dose_factor = min(dose_ratio, 1.2)

        sat_treated = {}
        for ion, val in sat_raw.items():
            base_eff = eff_factors.get(ion, 1.0)
            final_factor = base_eff / (dose_factor**0.5) if dose_factor > 0 else 1.0
            final_factor = max(0.05, min(final_factor, 1.0))
            sat_treated[ion] = val * final_factor

        st.markdown(f"#### 📊 시뮬레이션 결과: **{sel_chem_name}**")
        
        df_chart = pd.DataFrame({
            "Ion": list(sat_raw.keys()),
            "No Treatment (%)": list(sat_raw.values()),
            "With HRD Chemical (%)": list(sat_treated.values())
        })
        
        col_g1, col_arr, col_g2 = st.columns([4, 0.5, 4])
        with col_g1:
            st.markdown("**🔴 무처리 (Raw)**")
            st.bar_chart(df_chart.set_index("Ion")["No Treatment (%)"], color="#FF4B4B")
        with col_arr:
             st.markdown("<br><br><div style='text-align:center; font-size:30px;'>👉</div>", unsafe_allow_html=True)
        with col_g2:
            st.markdown(f"**🔵 {sel_chem_name} ({input_dose}ppm)**")
            st.bar_chart(df_chart.set_index("Ion")["With HRD Chemical (%)"], color="#2E86C1")

        st.markdown("##### 📝 전문 분석 (AI Diagnosis)")
        if sat_treated["Mn"] > 100:
            st.error(f"🚨 **[경고] 망간(Mn) 포화도 {sat_treated['Mn']:.0f}%** - 약품으로 제거되지 않습니다. 전처리 설비를 점검하십시오.")
        
        targets = sel_chem_info['Target']
        is_safe = True
        
        if 'SiO2' in targets:
            if sat_treated['SiO2'] > 100:
                st.warning(f"⚠️ 실리카 전용 약품({sel_chem_name})을 사용 중이나, 여전히 실리카 수치가 높습니다. 회수율 조정을 권장합니다.")
                is_safe = False
        elif sat_treated['SiO2'] > 100:
             st.warning("⚠️ 실리카 수치가 높습니다. **HRD-3000 (High Silica)** 제품으로 변경을 고려하십시오.")
             is_safe = False
             
        if 'BaSO4' in targets and sat_treated['BaSO4'] < 100:
            st.info("✅ 황산바륨(BaSO4) 제어가 효과적으로 이루어지고 있습니다.")

        if is_safe and sat_treated['Mn'] <= 100:
            st.success(f"✅ **{sel_chem_name}** 처방이 현재 수질에 적합합니다.")

    # [Tab 5] 현장 진단 & CIP 스케줄러 (NEW)
    with tab5:
        st.subheader("🛠️ RO 현장 진단 및 CIP 스케줄러 (Field Diagnosis)")
        st.info("💡 현장 데이터를 입력하면 **정규화(Normalization)**를 거쳐 정확한 **CIP 시점과 세정 방법**을 알려줍니다.")

        # 1. 시스템 및 기준값 설정 (Commissioning Data)
        with st.expander("⚙️ 시스템 설정 및 초기 기준값 (Commissioning Data) - 클릭하여 설정", expanded=False):
            c_conf1, c_conf2 = st.columns(2)
            with c_conf1:
                mem_model = st.selectbox("멤브레인 모델", ["CSM RE8040-BE", "LG BW 400 R", "DOW BW30-400"], key="ro_model_sel")
                
                # 멤브레인 스펙 DB (표준 유량/면적)
                mem_specs = {
                    "CSM RE8040-BE": {"area": 400, "flow": 10500}, # GPD
                    "LG BW 400 R": {"area": 400, "flow": 10500},
                    "DOW BW30-400": {"area": 400, "flow": 10500},
                }
                curr_spec = mem_specs[mem_model]
                
                # 배열 설정
                col_arr1, col_arr2 = st.columns(2)
                with col_arr1: n_st1 = st.number_input("1단 베셀 수량", value=4, step=1, key="n_st1")
                with col_arr2: n_st2 = st.number_input("2단 베셀 수량", value=2, step=1, key="n_st2")
                elem_per_vess = st.number_input("베셀당 엘리먼트 수", value=6, step=1, key="n_ele")

            with c_conf2:
                st.markdown("**🏁 초기 운전 데이터 (기준값)**")
                base_dp1 = st.number_input("초기 1단 차압 (bar)", value=2.0, step=0.1, key="base_dp1")
                base_dp2 = st.number_input("초기 2단 차압 (bar)", value=1.5, step=0.1, key="base_dp2")
                base_flow = st.number_input("초기 생산 유량 (m3/hr)", value=45.0, step=1.0, key="base_flow")
                
        st.divider()

        # 2. 현장 데이터 입력 (Daily Log)
        st.markdown("#### 📝 금일 현장 점검 데이터 입력")
        
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            f_temp = st.number_input("수온 (°C)", value=20.0, step=0.5, key="f_temp")
            f_flow = st.number_input("현재 유량 (m3/hr)", value=40.0, step=0.5, key="f_flow")
        with col_f2:
            p_feed = st.number_input("1단 입구 압력 (bar)", value=14.0, step=0.1, key="p_feed")
            p_inter = st.number_input("2단 입구 압력 (bar)", value=11.5, step=0.1, key="p_inter")
        with col_f3:
            p_conc = st.number_input("농축수 압력 (bar)", value=9.5, step=0.1, key="p_conc")
            # 차압 자동 계산 표시
            dp1_curr = p_feed - p_inter
            dp2_curr = p_inter - p_conc
            st.caption(f"Calculated DP: 1단 {dp1_curr:.1f} / 2단 {dp2_curr:.1f} bar")
        with col_f4:
            cond_p1 = st.number_input("1단 전도도 (µS/cm)", value=15.0, step=1.0, key="c_p1")
            cond_p2 = st.number_input("2단 전도도 (µS/cm)", value=40.0, step=1.0, key="c_p2")

        # 3. 진단 버튼 및 계산 로직
        if st.button("🚀 현장 진단 실행 (Analyze)", type="primary", use_container_width=True):
            
            # --- [Algorithm] 정규화 및 진단 로직 ---
            
            # A. 온도 보정 계수 (TCF) 계산
            # 수온이 25도보다 낮으면 점도가 높아져 압력이 오르고 유량이 줄어듦 -> 이를 보정
            if f_temp < 1: f_temp = 1
            tcf = math.exp(0.03 * (25 - f_temp))
            
            # B. 차압 정규화 (Normalized DP)
            # 유량이 줄어들면 마찰저항이 줄어 차압이 낮아보임 -> 유량 보정 필요
            # 공식: Norm_DP = Meas_DP * TCF * (Base_Flow / Meas_Flow)^1.5 (난류 보정)
            
            flow_corr = (base_flow / f_flow) ** 1.5 if f_flow > 0 else 1.0
            
            norm_dp1 = dp1_curr * tcf * flow_corr
            norm_dp2 = dp2_curr * tcf * flow_corr
            
            # C. 상승률 계산 (%)
            rise_dp1 = ((norm_dp1 - base_dp1) / base_dp1) * 100
            rise_dp2 = ((norm_dp2 - base_dp2) / base_dp2) * 100
            
            # --- [Result] 결과 리포트 출력 ---
            st.divider()
            st.subheader("📊 진단 결과 리포트")
            
            # 1) 물리적 진단 (차압)
            col_res1, col_res2 = st.columns(2)
            
            with col_res1:
                st.markdown("##### [1단] 전처리/미생물 오염 진단")
                st.metric("1단 정규화 차압", f"{norm_dp1:.2f} bar", f"{rise_dp1:+.1f}% (변동률)", 
                          delta_color="inverse" if rise_dp1 > 10 else "normal")
                
                if rise_dp1 >= 15.0:
                    st.error("🚨 **[CRITICAL] 차압 15% 이상 상승!**")
                    st.markdown("""
                    - **원인:** 미생물 슬라임(Bio-fouling) 또는 전처리 필터 누설(SS)
                    - **처방:** **알칼리 세정(Alkaline CIP, pH 11)** 즉시 수행 필요
                    """)
                elif rise_dp1 >= 10.0:
                    st.warning("⚠️ **[WARNING] 차압 상승 추세**")
                    st.markdown("- 세정 계획을 수립하십시오.")
                else:
                    st.success("✅ **[NORMAL] 상태 양호**")
            
            with col_res2:
                st.markdown("##### [2단] 스케일 오염 진단")
                st.metric("2단 정규화 차압", f"{norm_dp2:.2f} bar", f"{rise_dp2:+.1f}% (변동률)",
                          delta_color="inverse" if rise_dp2 > 10 else "normal")
                
                if rise_dp2 >= 15.0:
                    st.error("🚨 **[CRITICAL] 차압 15% 이상 상승!**")
                    st.markdown("""
                    - **원인:** 무기물 스케일(CaCO3, Silica) 석출 심각
                    - **처방:** **산성 세정(Acid CIP, pH 2~3)** 즉시 수행 필요
                    """)
                elif rise_dp2 >= 10.0:
                    st.warning("⚠️ **[WARNING] 스케일 생성 초기**")
                    st.markdown("- 회수율을 낮추거나 스케일 방지제 주입량을 점검하십시오.")
                else:
                    st.success("✅ **[NORMAL] 상태 양호**")

            # 2) 화학적 진단 (전도도)
            st.markdown("---")
            st.markdown("##### 🧪 수질/전도도 추가 분석")
            c_msg = []
            
            # 전도도 단순 상승률 비교 (임의 기준)
            # 보통 2단 전도도가 급격히 오르면 스케일 농도분극 영향
            if cond_p2 > (cond_p1 * 4): # 경험적 수치: 2단이 1단보다 4배 이상 높으면 위험
                st.warning(f"⚠️ **2단 전도도({cond_p2})가 매우 높습니다.** 농축 배수가 한계에 도달했습니다. 스케일 위험이 큽니다.")
            else:
                st.info(f"ℹ️ 생산수 수질 상태: 1단 {cond_p1}, 2단 {cond_p2} µS/cm (양호)")

            # 온도 보정 코멘트
            if f_temp < 15.0:
                st.caption(f"❄️ **참고:** 현재 수온({f_temp}°C)이 낮아 실제 압력은 높게 측정되지만, AI가 이를 보정하여 '정규화 차압'을 산출했습니다.")
        
        # --- [Section 2] CIP 설비 엔지니어링 (NEW - TRILITE 가이드북 반영) ---
        st.divider()
        st.markdown("#### 2️⃣ CIP 설비 엔지니어링 (Equipment Sizing)")
        st.info("💡 현장 RO 배열에 적합한 **CIP 탱크 용량, 펌프 유량, 히터 용량**을 계산합니다.")

        with st.container(border=True):
            col_cip1, col_cip2 = st.columns(2)
            
            with col_cip1:
                st.markdown("**⚙️ RO 시스템 및 세정 조건**")
                cip_vessel_d = st.selectbox("베셀 구경 (Vessel Diameter)", ["8 inch", "4 inch", "16 inch"], index=0, key="cip_dia")
                # CIP는 유량이 가장 많은 1단(Stage 1) 베셀 수량을 기준으로 설계함
                num_vessels_st1 = st.number_input("1단 베셀 수량 (Stage 1 Vessels)", value=5, step=1, key="cip_ves_cnt")
                
                cip_mode = st.radio("세정 모드 (Cleaning Mode)", 
                                  ["표준 세정 (Standard)", "고유량 세정 (High Flow)"], 
                                  help="심한 오염 시 고유량 세정이 필요할 수 있습니다.")

                # TRILITE 가이드북 기반 유량 설정 (m3/hr per vessel)
                if "8 inch" in cip_vessel_d:
                    flow_per_vessel = 9.0 if "표준" in cip_mode else 12.0
                elif "4 inch" in cip_vessel_d:
                    flow_per_vessel = 2.5 if "표준" in cip_mode else 3.5
                else: # 16 inch
                    flow_per_vessel = 36.0 if "표준" in cip_mode else 45.0

            # 계산 로직
            total_cip_flow = num_vessels_st1 * flow_per_vessel
            min_tank_vol = (total_cip_flow / 60) * 5  # 최소 5분 체류
            rec_tank_vol = (total_cip_flow / 60) * 10 # 권장 10분 체류
            heater_kw = (rec_tank_vol * 1000 * 20) / 860 / 2 # 20도 승온, 2시간 기준

            with col_cip2:
                st.markdown("**📊 설계 결과 (Calculated Specs)**")
                st.metric("CIP 펌프 유량 (Flow Rate)", f"{total_cip_flow:.1f} m³/hr", f"Vessel당 {flow_per_vessel} m³/hr")
                st.metric("CIP 탱크 용량 (Tank Volume)", f"{rec_tank_vol:.1f} m³", f"최소: {min_tank_vol:.1f} m³")
                st.metric("히터 용량 (Heater Capacity)", f"{heater_kw:.1f} kW", "Winter (dT 20°C)")
                
                st.warning("""
                **⚠️ 엔지니어링 가이드 (TRILITE):**
                - **펌프 압력:** 2~4 bar (저압 세정 권장)
                - **탱크 재질:** PE, FRP, STS316 (내산/내알칼리성)
                - **필터:** 순환 라인에 **5 micron 카트리지 필터** 설치 필수
                """)

        st.divider()
# --- [Section 3] CIP 약품 선정 및 소요량 계산 (NEW! 추가된 부분) ---
        st.divider()
        st.markdown("#### 3️⃣ CIP Chemical Selection (세정제 선정 및 소요량)")
        st.info(f"💡 위에서 계산된 **CIP 탱크 용량({rec_tank_vol:.1f} m³)**을 기준으로 필요한 약품량을 자동 산출합니다.")
        
        # 엑셀 데이터 로드
        ro_db = PRODUCT_CATALOG.get('RO', {})
        acid_list = ro_db.get('CIP_Acid', [])
        alk_list = ro_db.get('CIP_Alk', [])
        
        col_cip_c1, col_cip_c2 = st.columns(2)
        
        # 1. 산성 세정제 (Acid) 선정
        with col_cip_c1:
            with st.container(border=True):
                st.markdown("🔴 **산성 세정제 (Acid Cleaner)**")
                if acid_list:
                    sel_acid = st.selectbox("제품 선택 (Acid)", [item['Name'] for item in acid_list], key="sel_cip_acid")
                    acid_info = next((i for i in acid_list if i['Name'] == sel_acid), None)
                    
                    st.caption(f"📌 **특징:** {acid_info['Desc']}")
                    st.caption(f"🎯 **Target:** {', '.join(acid_info['Target'])}")
                    
                    # 소요량 계산 (탱크용량 * 농도%)
                    acid_conc = st.number_input("희석 농도 (%)", value=float(acid_info['Dosage']), step=0.5, key="conc_acid")
                    req_acid_kg = rec_tank_vol * 1000 * (acid_conc / 100.0)
                    
                    st.markdown("---")
                    st.metric("소요량 (1회 세정 기준)", f"{req_acid_kg:.1f} kg", f"Tank: {rec_tank_vol:.1f} m³")
                else:
                    st.warning("⚠️ 엑셀 DB에 산성 세정제가 없습니다. (make_excel.py 확인)")

        # 2. 알칼리 세정제 (Alkaline) 선정
        with col_cip_c2:
            with st.container(border=True):
                st.markdown("🔵 **알칼리 세정제 (Alkaline Cleaner)**")
                if alk_list:
                    sel_alk = st.selectbox("제품 선택 (Alkaline)", [item['Name'] for item in alk_list], key="sel_cip_alk")
                    alk_info = next((i for i in alk_list if i['Name'] == sel_alk), None)
                    
                    st.caption(f"📌 **특징:** {alk_info['Desc']}")
                    st.caption(f"🎯 **Target:** {', '.join(alk_info['Target'])}")
                    
                    # 소요량 계산
                    alk_conc = st.number_input("희석 농도 (%)", value=float(alk_info['Dosage']), step=0.5, key="conc_alk")
                    req_alk_kg = rec_tank_vol * 1000 * (alk_conc / 100.0)
                    
                    st.markdown("---")
                    st.metric("소요량 (1회 세정 기준)", f"{req_alk_kg:.1f} kg", f"Tank: {rec_tank_vol:.1f} m³")
                else:
                    st.warning("⚠️ 엑셀 DB에 알칼리 세정제가 없습니다. (make_excel.py 확인)")

        st.divider()

        # --- [Section 4] 막 보관 및 보존 가이드 (기존 유지, 섹션 번호만 변경) ---
        with st.expander("📦 RO 막 보관 및 장기 가동 정지 가이드 (Preservation)", expanded=False):
            st.markdown("### 🛑 장기 가동 정지 시 관리 요령")
            
            stop_period = st.selectbox("가동 정지 예상 기간", 
                                     ["단기 (48시간 이내)", "중기 (2일 ~ 4주)", "장기 (4주 이상)"], key="stop_period")
            
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                if "단기" in stop_period:
                    st.info("✅ **단순 정지 (Flush):**\n- 약품 처리 불필요.\n- 매 24시간마다 30분 이상 원수/생산수로 플러싱(Flushing).")
                elif "중기" in stop_period:
                    st.warning("⚠️ **살균 권장:**\n- 미생물 증식 방지를 위해 살균제(DTPMP 등) 처리 또는 산성 세정 후 정지.\n- 주 1회 이상 플러싱 수행.")
                else:
                    st.error("🚨 **화학적 보존 (Preservation):**\n- **SMBS (Sodium Metabisulfite) 1.0%** 용액 주입 및 밀봉.\n- 동결 위험 시 글리세린(20%) 혼합.\n- pH는 3~4 유지 권장.")
            
            with c_p2:
                st.caption("""
                **※ 신품 막 보관 팁 (TRILITE 가이드):**
                - **건식 (Dry):** 12개월 이상 장기 보관 가능. 동파 위험 없음.
                - **습식 (Wet):** 12개월 경과 시 미생물 오염 확인 필요. 5~45°C 보관 (동결 주의).
                """)
    with tab6:
       draw_trouble_shooter("RO")
# ==============================================================================
# [Module 4] Wastewater Reuse: Smart Engineering (안전 경고 강화 버전)
# ==============================================================================
elif "Wastewater" in program_mode:
    # 1. 공정 라이브러리 (정제된 데이터베이스 및 설계 한계치)
    PROCESS_LIB = {
        "Neutralization (중화)": {"SS": 0, "COD": 0, "TDS": 1.05, "Hard": 0, "Oil": 0, "Limit": {}, "Name": "중화"},
        "DAF (가압부상)": {"SS": 0.85, "COD": 0.3, "TDS": 1.0, "Hard": 0, "Oil": 0.90, "Limit": {"Oil": 300}, "Name": "DAF"},
        "Coagulation (응집침전)": {"SS": 0.9, "COD": 0.4, "TDS": 1.1, "Hard": 0.2, "Oil": 0.6, "Limit": {"SS": 5000}, "Name": "응집침전"},
        "AFM Filter (여과)": {"SS": 0.8, "COD": 0.2, "TDS": 1.0, "Hard": 0, "Oil": 0.3, "Limit": {"SS": 50}, "Name": "AFM"},
        "UF (한외여과)": {"SS": 0.99, "COD": 0.4, "TDS": 1.0, "Hard": 0, "Oil": 0.5, "Limit": {"SS": 20, "Oil": 5}, "Name": "UF"},
        "AOP (고도산화)": {"SS": 0.2, "COD": 0.85, "TDS": 1.05, "Hard": 0, "Oil": 0.5, "Limit": {"COD": 500}, "Name": "AOP"},
        "RO System (역삼투)": {"SS": 0.99, "COD": 0.98, "TDS": 0.99, "Hard": 0.99, "Oil": 0.99, "Limit": {"SS": 1.0, "COD": 20, "Oil": 0.1}, "Name": "RO"}
    }

    # 2. 데이터 초기화
    if 'ww_data' not in st.session_state:
        st.session_state.ww_data = pd.DataFrame({
            'Parameter': ['pH', 'TDS', 'SS', 'COD', 'Hard', 'Oil'],
            'Value': [7.0, 1500.0, 200.0, 400.0, 300.0, 20.0]
        })

    st.title("♻️ Wastewater Reuse: Smart Engineering System")

    # --- [Step 1] 수질 입력 및 지능형 추천 로직 ---
    col_in, col_rec = st.columns([1, 1.5])
    with col_in:
        st.subheader("📊 Raw Water Data")
        edited_df = st.data_editor(st.session_state.ww_data, hide_index=True, use_container_width=True)
        st.session_state.ww_data = edited_df 
        w_v = dict(zip(edited_df['Parameter'], edited_df['Value']))

    # 수질 기반 자동 추천 엔진
    recom_list = []
    if w_v['pH'] < 6.5 or w_v['pH'] > 8.5: recom_list.append("Neutralization (중화)")
    if w_v['Oil'] > 50: recom_list.append("DAF (가압부상)")
    if w_v['SS'] > 100: recom_list.append("Coagulation (응집침전)")
    if w_v['COD'] > 300: recom_list.append("AOP (고도산화)")
    if w_v['SS'] > 10: recom_list.append("AFM Filter (여과)")
    if w_v['TDS'] > 300: recom_list.append("RO System (역삼투)")
    
    auto_suggested = [p for p in list(PROCESS_LIB.keys()) if p in recom_list]

    with col_rec:
        st.subheader("🏗️ Process Recommendation")
        st.success(f"**현재 수질 맞춤형 설계:** \n\n {' → '.join(auto_suggested)}")
        sel_procs = st.multiselect(
            "공정 설계를 확정하세요:",
            list(PROCESS_LIB.keys()),
            default=auto_suggested
        )

    # --- [Step 2] 시뮬레이션 및 안전 진단 ---
    tab_sim, tab_sludge, tab_report = st.tabs(["🔬 수질 변화", "💩 슬러지 분석", "📑 판정 리포트"])

    with tab_sim:
        sim_log = []
        curr = {"SS": w_v['SS'], "COD": w_v['COD'], "TDS": w_v['TDS'], "Hard": w_v['Hard'], "Oil": w_v['Oil']}
        sim_log.append({"Step": "Raw Water", **curr, "Status": "✅ OK"})
        
        # [추가] 안전 경고 저장 리스트
        safety_alerts = []
        
        for p_name in sel_procs:
            proc = PROCESS_LIB[p_name]
            status = "✅ OK"
            
            # [추가] 공정 진입 전 유입수 수질 안전 진단
            for param, limit in proc['Limit'].items():
                if curr.get(param, 0) > limit:
                    status = "❌ CRITICAL"
                    safety_alerts.append(f"🚨 **{p_name}** 유입부 {param} 농도({curr[param]:.1f})가 설계 한계({limit})를 초과했습니다.")

            # 제거 효율 적용
            curr["SS"] *= (1 - proc.get('SS', 0))
            curr["COD"] *= (1 - proc.get('COD', 0))
            curr["Oil"] *= (1 - proc.get('Oil', 0))
            curr["Hard"] *= (1 - proc.get('Hard', 0))
            if "RO" in p_name or "NF" in p_name: curr["TDS"] *= (1 - proc.get('TDS', 0))
            else: curr["TDS"] *= proc.get('TDS', 1.0)
            
            sim_log.append({"Step": p_name, **curr, "Status": status})

        df_log = pd.DataFrame(sim_log)
        fig = go.Figure()
        for p in ['SS', 'COD', 'Oil']:
            fig.add_trace(go.Scatter(x=df_log['Step'], y=df_log[p], name=p, mode='lines+markers'))
        fig.add_trace(go.Scatter(x=df_log['Step'], y=df_log['TDS'], name='TDS (보조축)', yaxis="y2", line=dict(dash='dot')))
        fig.update_layout(yaxis2=dict(overlaying="y", side="right"), height=350, legend=dict(orientation="h", y=1.2))
        st.plotly_chart(fig, use_container_width=True)
        
        # [추가] 설계 위험 감지 시 경고창 출력
        if safety_alerts:
            with st.container(border=True):
                st.error("⚠️ **Engineering Safety Warning (설계 위험 감지)**")
                for alert in safety_alerts: st.write(alert)
                st.info("💡 **전문가 제언:** RO/NF 막 보호를 위해 전처리 공정을 보강하십시오.")

        st.dataframe(df_log.style.format({c: "{:.1f}" for c in ['SS','COD','TDS','Hard','Oil']}), use_container_width=True)

    with tab_sludge:
        flow = st.number_input("설계 유량 (m3/hr)", value=100.0)
        daily_sludge = (flow * 24 * (w_v['SS'] - curr['SS'])) / 1000.0 * 1.5
        st.metric("일일 슬러지 발생량 예측", f"{daily_sludge:.1f} kg/day")

    with tab_report:
        last = df_log.iloc[-1]
        standards = {"공업용수 (냉각탑)": {"SS": 10, "COD": 20, "TDS": 1000}, "조경/화장실용": {"SS": 20, "COD": 30, "TDS": 1500}}
        cols = st.columns(2)
        for i, (usage, limits) in enumerate(standards.items()):
            is_pass = all(last[p] <= lim for p, lim in limits.items() if p in last)
            with cols[i]:
                if is_pass: st.success(f"✅ **{usage}** 사용 가능")
                else: st.warning(f"⚠️ **{usage}** 부적합")
# ==============================================================================
# [Module 5] Basic Engineering Calculator (RO & AFM Sizing)
# ==============================================================================
elif "Engineering" in program_mode:
    st.title("📏 Basic Engineering & Sizing Calculator")
    st.info("설비 규격 및 여재 충진량 산출 (AFM IFU V23.4 규격 적용)")

    tab_afm, tab_ro_sizing = st.tabs(["🧪 AFM/Media Filter Sizing", "💧 RO System Sizing"])

    # --- [1. AFM/Media Filter Sizing] ---
    with tab_afm:
        st.subheader("Media Filter & AFM Filling Calculation")
        
        # 입력 섹션
        c1, c2 = st.columns(2)
        with c1:
            tank_d = st.number_input("Tank Diameter (mm)", value=2000, step=100, key="afm_d")
            bed_h = st.number_input("Media Bed Height (mm)", value=1200, step=100, help="지지층을 포함한 총 여재 높이", key="afm_h")
            media_type = st.selectbox("Media Type", ["AFM (Activated Filter Media)", "Sand (Quartz Sand)", "Anthracite"], key="afm_type")

            # [AFM 전용 옵션]
            is_afm = False
            use_grade0 = False
            bottom_type = "Nozzle Plate"
            
            if "AFM" in media_type:
                is_afm = True
                st.markdown("---")
                st.markdown("**⚙️ AFM Configuration (IFU V23.4)**")
                # 필터 하부 타입 선택 (Layering 로직이 달라짐)
                bottom_type = st.radio("Filter Bottom Type", ["Nozzle Plate (노즐판)", "Lateral System (스트레이너)"], 
                                       help="노즐판은 Grade 3가 필요 없으나, 스트레이너 방식은 하부 보호를 위해 Grade 3가 필수입니다.")
                # Grade 0 사용 여부
                use_grade0 = st.checkbox("Grade 0 (0.25~0.5mm) 포함 (Ultra-filtration)", value=False, 
                                        help="1 micron 이하 제거 및 SDI 저감이 필요한 경우 선택 (RO 전처리 권장)")

        # [물리적 계산]
        radius = tank_d / 2000 # mm -> m
        height = bed_h / 1000 # mm -> m
        volume = math.pi * (radius ** 2) * height
        
        # [결과 표시 섹션]
        with c2:
            st.markdown("#### 🎯 Calculation Summary")
            st.metric("Total Bed Volume", f"{volume:.2f} m³")
            
            if not is_afm:
                # 일반 여재 계산 (Sand/Anthracite)
                density = 1.6 if "Sand" in media_type else 0.9
                total_weight = volume * density * 1000
                st.metric("Total Media Weight", f"{total_weight:.0f} kg", f"Bulk Density: {density} kg/l")
            
            else:
                # [AFM 상세 계산 로직 - IFU V23.4 Page 8 & 14]
                # 등급별 밀도 (Page 8 Table)
                d_g0 = 1.24
                d_g1 = 1.33
                d_g2 = 1.40
                d_g3 = 1.43
                
                # 적층 비율(Ratio) 결정 로직
                ratio = {} # {grade: percentage}
                
                if "Lateral" in bottom_type:
                    # 스트레이너 타입 (Grade 3 필수 - Page 14)
                    if use_grade0:
                        # High Precision: G0(20) / G1(30) / G2(30) / G3(20)
                        ratio = {'G0': 0.20, 'G1': 0.30, 'G2': 0.30, 'G3': 0.20}
                        st.info("💡 **Laterals + Grade 0:** G0(20%) / G1(30%) / G2(30%) / G3(20%) 비율 적용")
                    else:
                        # Standard: G1(60%) / G2(20%) / G3(20%) (Page 14 Diagram >800mm)
                        ratio = {'G1': 0.60, 'G2': 0.20, 'G3': 0.20}
                        st.info("💡 **Laterals Standard:** G1(60%) / G2(20%) / G3(20%) 비율 적용")
                else:
                    # 노즐판 타입 (Grade 3 불필요 - Page 12)
                    if use_grade0:
                        # High Precision: G0(20) / G1(30) / G2(50) (Page 12 범위 중간값)
                        ratio = {'G0': 0.20, 'G1': 0.30, 'G2': 0.50}
                        st.info("💡 **Nozzle + Grade 0:** G0(20%) / G1(30%) / G2(50%) 비율 적용")
                    else:
                        # Standard: G1(70%) / G2(30%)
                        ratio = {'G1': 0.70, 'G2': 0.30}
                        st.info("💡 **Nozzle Standard:** G1(70%) / G2(30%) 비율 적용")

                # 중량 계산
                w_g0 = volume * ratio.get('G0', 0) * d_g0 * 1000
                w_g1 = volume * ratio.get('G1', 0) * d_g1 * 1000
                w_g2 = volume * ratio.get('G2', 0) * d_g2 * 1000
                w_g3 = volume * ratio.get('G3', 0) * d_g3 * 1000
                
                total_afm_weight = w_g0 + w_g1 + w_g2 + w_g3
                st.metric("Total AFM Weight", f"{total_afm_weight:.0f} kg")

        # [AFM Layering Display]
        if is_afm:
            st.divider()
            st.markdown("### 🧪 AFM Grade-specific Layering (25kg Bags)")
            
            # 컬럼 수 동적 할당
            cols = st.columns(4 if use_grade0 else 3)
            
            # G0 (Optional)
            if use_grade0:
                with cols[0]:
                    bags = math.ceil(w_g0 / 25)
                    st.success(f"🟣 **Grade 0** (Top)\n\n"
                               f"**{w_g0:.0f} kg**\n\n"
                               f"📦 **{bags} Bags**\n\n"
                               f"Size: 0.25-0.5mm\n"
                               f"Density: {d_g0}")
            
            # G1
            idx_g1 = 1 if use_grade0 else 0
            with cols[idx_g1]:
                bags = math.ceil(w_g1 / 25)
                st.error(f"🔴 **Grade 1**\n\n"
                           f"**{w_g1:.0f} kg**\n\n"
                           f"📦 **{bags} Bags**\n\n"
                           f"Size: 0.4-0.8mm\n"
                           f"Density: {d_g1}")

            # G2
            idx_g2 = 2 if use_grade0 else 1
            with cols[idx_g2]:
                bags = math.ceil(w_g2 / 25)
                st.info(f"🔵 **Grade 2**\n\n"
                          f"**{w_g2:.0f} kg**\n\n"
                          f"📦 **{bags} Bags**\n\n"
                          f"Size: 0.7-2.0mm\n"
                          f"Density: {d_g2}")

            # G3 (Lateral Only)
            if "Lateral" in bottom_type:
                idx_g3 = 3 if use_grade0 else 2
                with cols[idx_g3]:
                    bags = math.ceil(w_g3 / 25)
                    st.warning(f"⚫ **Grade 3** (Base)\n\n"
                               f"**{w_g3:.0f} kg**\n\n"
                               f"📦 **{bags} Bags**\n\n"
                               f"Size: 2.0-4.0mm\n"
                               f"Density: {d_g3}")
            elif not use_grade0:
                 # 노즐 타입이고 Standard일 때 3번째 컬럼 비우기 방지용 (빈 공간)
                 pass
# --- [2. RO System Sizing] (Updated with 2-Stage vs 3-Stage Logic) ---
    with tab_ro_sizing:
        st.subheader("💧 RO System Configuration & Design")
        st.info("💡 회수율에 따른 **최적 배열(Array)**과 **3단 배열(3:2:1) 적용 가능성**을 분석합니다.")

        r1, r2 = st.columns(2)
        with r1:
            st.markdown("**⚙️ 설계 목표 (Design Basis)**")
            target_p = st.number_input("목표 생산수 유량 (Permeate Flow, m3/hr)", value=50.0, step=1.0, key="ro_target_p")
            target_rec = st.slider("목표 회수율 (Recovery, %)", 40, 95, 75, key="ro_target_rec")
            
            st.markdown("**🧪 설계 인자 (Design Parameter)**")
            design_flux = st.number_input("설계 플럭스 (Flux, LMH)", value=15.0, 
                                        help="표준: 15~18 LMH. 높을수록 오염 위험 증가.", key="ro_flux")
            
            # [플럭스 가이드]
            with st.expander("ℹ️ [참조] 적정 플럭스 가이드라인", expanded=False):
                st.markdown("""
                * **폐수 재이용:** `10 ~ 14 LMH`
                * **하천수/지표수:** `14 ~ 18 LMH`
                * **지하수:** `18 ~ 22 LMH`
                """)

            elements_per_vessel = st.selectbox("베셀당 엘리먼트 수", [4, 5, 6, 7], index=2, key="ro_ele_per_ves")
            active_area = st.number_input("엘리먼트 유효 면적 (ft²)", value=400, step=10, key="ro_area")

        # --- [엔지니어링 계산 엔진] ---
        feed_flow = target_p / (target_rec / 100)
        concentrate_flow = feed_flow - target_p
        
        # 1. 필요 막 수량 및 베셀 수량 계산
        total_area_m2 = (target_p * 1000) / design_flux
        element_area_m2 = active_area * 0.0929
        total_elements = math.ceil(total_area_m2 / element_area_m2)
        total_vessels = math.ceil(total_elements / elements_per_vessel)
        
        # 실제 플럭스
        actual_flux = (target_p * 1000) / (total_elements * element_area_m2)

        # 2. [NEW] 배열 시뮬레이션 (2단 vs 3단)
        
        # (Option A) 2단 배열 (Standard 2:1)
        # 비율: 약 2:1 (67% : 33%)
        v2_st1 = math.ceil(total_vessels * 0.67)
        v2_st2 = total_vessels - v2_st1
        str_2st = f"{v2_st1} : {v2_st2}"
        
        # (Option B) 3단 배열 (High Recovery 3:2:1 or 4:2:1)
        # 비율: 약 4:2:1 또는 3:2:1 (50% : 33% : 17% 근사치)
        if total_vessels >= 6:
            v3_st1 = math.ceil(total_vessels * 0.5)
            v3_st2 = math.ceil(total_vessels * 0.3)
            v3_st3 = total_vessels - v3_st1 - v3_st2
            # 3단 잔여량 보정
            if v3_st3 < 1: 
                v3_st2 -= 1
                v3_st3 += 1
            str_3st = f"{v3_st1} : {v3_st2} : {v3_st3}"
        else:
            str_3st = "N/A (베셀 부족)"

        with r2:
            st.markdown("#### 🎯 Engineering Result")
            with st.container(border=True):
                st.metric("총 엘리먼트 / 베셀", f"{total_elements} EA / {total_vessels} PV")
                st.metric("실제 운전 플럭스", f"{actual_flux:.1f} LMH")

            st.divider()
            
            # [핵심] 배열 추천 및 비교 분석
            st.markdown("##### 🏗️ 배열 구성 비교 (Array Configuration)")
            
            # 추천 로직
            rec_tab1, rec_tab2 = st.tabs(["⭐ 추천: 2단 배열", "⚠️ 대안: 3단 배열"])
            
            with rec_tab1:
                st.metric("Standard Array (2:1)", str_2st)
                if target_rec <= 80:
                    st.success("✅ **[적합]** 회수율 80% 이하에서는 **2단 배열**이 수력학적 밸런스와 비용 면에서 가장 유리합니다.")
                else:
                    st.warning("⚠️ **[주의]** 회수율이 너무 높습니다. 2단으로는 농축수 유량이 부족할 수 있습니다.")
            
            with rec_tab2:
                st.metric("3-Stage Array (3:2:1)", str_3st)
                if target_rec >= 85:
                    st.success("✅ **[적합]** 회수율 85% 이상 고회수율 운전 시 필요한 구성입니다.")
                else:
                    st.error("⛔ **[비추천]** 일반 회수율(75%)에서 3단을 쓰면 **후단부 유속 저하 및 차압 상승** 문제가 발생합니다.")

            # [Explain] 3:2:1이 안되는 이유 (전문가 설명)
            with st.expander("❓ 왜 75% 회수율에서 '3:2:1(3단)'을 안 쓸까요?", expanded=True):
                st.markdown("""
                **1. 차압(Delta P)의 과도한 상승**
                * RO 막을 한 번 통과할 때마다 약 1~2 bar의 압력 손실이 발생합니다.
                * 3단 구성을 하면 전체 차압이 커져 **앞단(1단)에 과도한 압력**을 걸어야 하고, 이는 **에너지 낭비**로 이어집니다.

                **2. 플럭스 불균형 (Flux Imbalance)**
                * 3단까지 가면 1단과 3단의 생산량 격차가 너무 커집니다.
                * 1단은 너무 일을 많이 해서 **파울링(오염)**되고, 3단은 배압(Backpressure) 때문에 **일을 안 하는 현상**이 발생합니다.

                **3. 배관 및 설비 복잡성 (CAPEX)**
                * 헤더 배관, 계측기(Flow/Pressure Tx)가 1세트 더 필요하여 **설치비가 15~20% 증가**합니다.
                
                👉 **결론:** 회수율 85% 이상을 억지로 짜내야 하는 경우가 아니라면, **'2단 배열'**이 정답입니다.
                """)
            
            col_flow1, col_flow2 = st.columns(2)
            with col_flow1: st.metric("유입수 유량", f"{feed_flow:.1f} m³/hr")
            with col_flow2: st.metric("농축수 유량", f"{concentrate_flow:.1f} m³/hr")   