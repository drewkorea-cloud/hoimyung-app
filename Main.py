import streamlit as st

import pandas as pd

import os

import sys

import math

import plotly.graph_objects as go

import plotly.express as px

import numpy as np

import re
# ==============================================================================
# [통합 데이터 로더] 엑셀을 한 번만 읽어서 모든 곳에 공급 (최적화 Ver)
# ==============================================================================
@st.cache_data
def load_data_master():
    excel_file = 'chemical_db.xlsx'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, excel_file)
    
    catalog = {
        'Cooling': { 'Main_Inhibitor': [], 'Biocide': [], 'Dispersant': [] },
        'Boiler':  { 'Oxygen_Scavenger': [], 'Scale_Disp': [], 'Condensate': [] },
        'RO':      { 'Antiscalant': [], 'CIP_Acid': [], 'CIP_Alk': [] }
    }
    df_raw = pd.DataFrame()

    if os.path.exists(file_path):
        try:
            df_raw = pd.read_excel(file_path)
            df_raw = df_raw.fillna("-")
            df_raw.columns = [str(c).strip() for c in df_raw.columns]

            for _, row in df_raw.iterrows():
                sys_val = str(row.get('System', '')).strip()
                raw_type = str(row.get('Type', '')).strip()
                p_type = raw_type 

                # 자동 분류 로직
                if sys_val == 'Cooling':
                    if raw_type in ['Inhibitor', 'Corrosion Inhibitor', 'Main_Inhibitor']: p_type = 'Main_Inhibitor'
                    elif raw_type in ['Biocides', 'Biocide']: p_type = 'Biocide'
                    elif raw_type in ['Dispersant']: p_type = 'Dispersant'
                elif sys_val == 'Boiler':
                    if 'Oxygen' in raw_type: p_type = 'Oxygen_Scavenger'
                    elif any(x in raw_type for x in ['Scale', 'Sludge', 'Inhibitor']): p_type = 'Scale_Disp'
                    elif 'Amine' in raw_type or 'Condensate' in raw_type: p_type = 'Condensate'
                elif sys_val == 'RO':
                    if 'Scale' in raw_type or 'Antiscalant' in raw_type: p_type = 'Antiscalant'
                    elif 'Acid' in raw_type: p_type = 'CIP_Acid'
                    elif 'Alk' in raw_type: p_type = 'CIP_Alk'

                if sys_val in catalog and p_type in catalog[sys_val]:
                    target_raw = row.get('Target', '')
                    target_list = [t.strip() for t in str(target_raw).split(',')] if target_raw != '-' else []
                    
                    # [스마트 숫자 추출 함수] "200~400" -> 200.0 으로 변환
                    def smart_parse(val):
                        if isinstance(val, (int, float)): return float(val)
                        val_str = str(val)
                        # 숫자와 소수점만 찾아서 첫 번째 값 반환
                        match = re.search(r"(\d+(\.\d+)?)", val_str)
                        if match: return float(match.group(1))
                        return 0.0

                    item = {
                        'Name': str(row.get('Name', 'Unknown')),
                        'Type': p_type,
                        'Desc': str(row.get('Desc', '-')),
                        'Dosage': smart_parse(row.get('Dosage', 0)),
                        'Target': target_list,
                        'Main_Ingredient': str(row.get('Main_Ingredient', '-')),
                        'Sales_Point': str(row.get('Sales_Point', '-')),
                        'Field_Tip': str(row.get('Field_Tip', '-')),
                        # ★ 엑셀 연동 핵심 (스마트 파싱 적용)
                        'Max_LSI': smart_parse(row.get('Max_LSI', 0)),
                        'Max_CaSO4': smart_parse(row.get('Max_CaSO4', 0)),
                        'Max_SiO2': smart_parse(row.get('Max_SiO2', 0)),
                        'Max_BaSO4': smart_parse(row.get('Max_BaSO4', 0)),
                        'Max_SrSO4': smart_parse(row.get('Max_SrSO4', 0)),
                        'Max_CaF2': smart_parse(row.get('Max_CaF2', 0))
                    }
                    catalog[sys_val][p_type].append(item)
                    
        except Exception as e:
            st.error(f"🚨 데이터 로드 중 오류 발생: {e}")
            
    return catalog, df_raw

# [중요] 프로그램 시작 시 1번만 실행해서 전역 변수에 담습니다.
PRODUCT_CATALOG, df_master = load_data_master()
# --- 1. 기본 설정 ---

st.set_page_config(
    page_title="Water Master Pro",
    page_icon="logo.png",  # 
    layout="wide"
)

# --- [여기서부터 복사하세요] 비밀번호 보안 장치 ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 로그인이 안 된 상태면 로그인 화면만 보여줌
if not st.session_state.authenticated:
    st.markdown("### 🔒 관계자 외 출입금지")
    password_input = st.text_input("접속 비밀번호를 입력하세요:", type="password")
    
    if st.button("로그인"):
        # 👇 [수정 가능] 원하는 비밀번호로 바꾸세요 (예: parker2024)
        if password_input == "1234":  
            st.session_state.authenticated = True
            st.rerun()  # 화면을 새로고침해서 앱을 보여줌
        else:
            st.error("❌ 비밀번호가 틀렸습니다. 다시 시도하세요.")
            
    st.stop()  # ⛔ 비밀번호를 맞추기 전까지는 아래 코드를 절대 실행하지 않음!


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

# ------------------------------------------------------------------------------
# [신규 추가] L.S.I 계산 함수 (에러 방지 기능 포함)
# ------------------------------------------------------------------------------
def calculate_lsi(ph, tds, ca, alk, temp):
    try:
        # 안전장치: 숫자가 아닌 값이 들어오면 강제로 변환
        ph, tds, temp = float(ph), float(tds), float(temp)
        ca, alk = float(ca), float(alk)

        # 로그 계산 오류 방지 (0이 들어오면 1로 변경)
        if ca <= 0: ca = 1.0
        if alk <= 0: alk = 1.0
        if tds <= 0: tds = 1.0

        # 공식 적용
        a = (math.log10(tds) - 1) / 10
        b = -13.12 * math.log10(temp + 273) + 34.55
        c = math.log10(ca) - 0.4
        d = math.log10(alk)

        phs = (9.3 + a + b) - (c + d)
        return ph - phs

    except:
        return 0.0  # 에러 나면 0 반환

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
            "1. Cooling Calc.", 
            "2. Boiler Calc.", 
            "3. RO Calc.", 
            "4. WWT Calc.", 
            "5. Engineering Calc."
        ], 
        key="main_menu_mode"
    )
    
    st.markdown("---")
    st.info("💡 **Tip:** 값을 입력하고 '적용' 버튼을 누르면 AI 진단이 시작됩니다.")
    st.caption("Authorized by **PARKER**")

# ==============================================================================

# [Module 1] Cooling Master PRO

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



    # 5개 탭 구조

    tab1, tab2, tab3, tab4, tab5 = st.tabs([

        "💧 Water Balance (물질수지)", 

        "⚗️ Water Chemistry (수질진단)", 

        "💊 Chemical Program (약품)", 

        "🔬 Lab & Deposit (성분분석)",

        "📘 기술 매뉴얼 (Formula)",
    
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
    # Tab 2: Water Chemistry (Mg 제거 / Fe, 탁도 추가 / 가이드 항시 표시 v5)
    # ======================================================================
    with tab2:
        st.subheader("2. Prediction & Diagnosis Simulator")
        st.markdown("보충수 수질을 기반으로 순환수를 예측하고, **Skin Temperature(열교환기 표면)** 기준의 정밀 진단을 수행합니다.")

        # 1. 초기 데이터 설정 (v5로 변경하여 화면 강제 갱신)
        if 'makeup_data_v5' not in st.session_state:
            st.session_state.makeup_data_v5 = pd.DataFrame({
                'Item': ['pH', 'Cond (µS)', 'Ca-H (ppm)', 'M-Alk (ppm)', 'Cl (ppm)', 'SO4 (ppm)', 'SiO2 (ppm)', 'Fe (ppm)', 'Turbidity (NTU)'],
                'Value': [7.5, 200.0, 40.0, 50.0, 20.0, 10.0, 10.0, 0.1, 2.0]
            })
        
        # [관리 기준] 초기값
        if 'cooling_limits_v5' not in st.session_state:
            st.session_state.cooling_limits_v5 = {
                "pH": "8.3~9.0", "Calcium (Ca-H)": "800", 
                "M-Alkalinity": "500", "Chloride (Cl)": "500", "Sulfate (SO4)": "1200",
                "Silica (SiO2)": "150", "Conductivity": "5000",
                "Iron (Fe)": "1.0", "Turbidity (NTU)": "20"
            }
            
        # 결과 저장소
        if 'sim_results' not in st.session_state: st.session_state.sim_results = {}
        if 'run_simulation' not in st.session_state: st.session_state.run_simulation = False

        col_sim1, col_sim2 = st.columns([1, 1])
        
        with col_sim1:
            st.markdown("###### ① 보충수(Make-up) 수질 입력")
            edited_mu = st.data_editor(st.session_state.makeup_data_v5, hide_index=True, key="mu_editor_v5", height=320)
        
        with col_sim2:
            st.markdown("###### ② 운전 목표 및 설비 부하 설정")
            target_coc = st.slider("Target Cycles (목표 농축배수)", 1.0, 10.0, 5.0, 0.1, key="sim_coc")
            sim_temp = st.slider("Water Temperature (수온, °C)", 10.0, 60.0, 35.0, 1.0, key="sim_temp")
            
            # [Skin Temp 추정을 위한 설비 부하 선택]
            st.markdown("---")
            st.markdown("###### ③ 열교환기 부하 조건 (Heat Load Stress)")
            st.info("💡 공장 내 **가장 뜨거운 설비(Bottleneck)**를 기준으로 선택하세요.")
            
            heat_load_type = st.radio(
                "가장 가혹한 열교환기 타입은?",
                ["🟢 저부하 (오일쿨러/공조기)", "🟡 표준 (화학/사출/반도체)", "🔴 고부하 (제철/발전/응축기)"],
                index=1,
                horizontal=True
            )

            # [Skin Temp 자동 계산 로직]
            if "고부하" in heat_load_type:
                skin_offset = 25.0
                st.caption(f"🔥 **Skin Temp 보정: +25℃** (예상 표면온도: {sim_temp + 25}℃)")
            elif "표준" in heat_load_type:
                skin_offset = 15.0
                st.caption(f"⚙️ **Skin Temp 보정: +15℃** (예상 표면온도: {sim_temp + 15}℃)")
            else:
                skin_offset = 5.0
                st.caption(f"❄️ **Skin Temp 보정: +5℃** (예상 표면온도: {sim_temp + 5}℃)")

            st.markdown("---")
            use_acid = st.checkbox("Acid Feed (황산 주입 모드)", value=False)

            if use_acid:
                target_ph = st.number_input("Target pH (Control)", 6.5, 8.5, 7.8, 0.1)
                st.info("🧪 pH 컨트롤러 설정값으로 계산합니다.")
            else:
                try:
                    temp_mu = dict(zip(edited_mu['Item'], edited_mu['Value'])) 
                    base_alk = temp_mu.get('M-Alk (ppm)', 50.0)
                except: base_alk = 50.0

                cycle_alk = base_alk * target_coc
                if cycle_alk < 1: cycle_alk = 1.0
                
                alk_threshold = 370.0 
                if cycle_alk < alk_threshold:
                    est_ph_raw = (2.0 * math.log10(cycle_alk)) + 3.15
                    phase_msg = "Bicarbonate Phase (pH < 8.3)"
                else:
                    est_ph_raw = (1.465 * math.log10(cycle_alk)) + 4.54
                    phase_msg = "Carbonate Buffer Phase (pH ≥ 8.3)"

                est_ph = min(est_ph_raw, 9.3)
                target_ph = st.number_input(f"Predicted pH ({phase_msg})", value=float(f"{est_ph:.2f}"), disabled=True)
            
            # [버튼] 실행
            if st.button("🚀 Run Simulation (비교 분석)", type="primary", use_container_width=True):
                st.session_state.makeup_data_v5 = edited_mu 
                mu_dict = dict(zip(edited_mu['Item'], edited_mu['Value']))
                
                # 예측 계산 (Mg 삭제 / Fe, Turbidity 추가)
                pred_ca = mu_dict['Ca-H (ppm)'] * target_coc
                pred_cl = mu_dict['Cl (ppm)'] * target_coc
                pred_sio2 = mu_dict['SiO2 (ppm)'] * target_coc
                pred_cond = mu_dict['Cond (µS)'] * target_coc
                
                # 신규 항목 계산
                pred_fe = mu_dict.get('Fe (ppm)', 0.1) * target_coc
                pred_turb = mu_dict.get('Turbidity (NTU)', 1.0) * target_coc
                
                if use_acid:
                    pred_alk = mu_dict['M-Alk (ppm)'] * target_coc * 0.6
                    acid_so4 = (mu_dict['M-Alk (ppm)'] * target_coc) * 0.9
                    pred_so4 = (mu_dict['SO4 (ppm)'] * target_coc) + acid_so4
                else:
                    pred_alk = mu_dict['M-Alk (ppm)'] * target_coc
                    pred_so4 = mu_dict['SO4 (ppm)'] * target_coc

                # 지수 계산
                temp_k = sim_temp + 273.15
                tds_val = pred_cond * 0.7
                
                val_a = (math.log10(max(tds_val, 1)) - 1) / 10
                val_b = -13.12 * math.log10(temp_k) + 34.55
                val_c = math.log10(max(pred_ca, 1)) - 0.4
                val_d = math.log10(max(pred_alk, 1))
                
                pHs = (9.3 + val_a + val_b) - (val_c + val_d)
                
                # LSI를 Bulk(물 온도)와 Skin(표면 온도) 2가지로 계산
                lsi_bulk = calculate_lsi(target_ph, pred_cond * 0.7, pred_ca, pred_alk, sim_temp)
                lsi_skin = calculate_lsi(target_ph, pred_cond * 0.7, pred_ca, pred_alk, sim_temp + skin_offset)
                
                rsi = (2 * pHs) - target_ph
                p_eq = 1.465 * math.log10(max(pred_alk, 1)) + 4.54
                psi = (2 * pHs) - p_eq
                ls_idx = (pred_cl + pred_so4) / pred_alk if pred_alk > 0 else 0
                
                # 결과 저장
                st.session_state.sim_results = {
                    'mu_dict': mu_dict,
                    'pred_ca': pred_ca, 'pred_alk': pred_alk,
                    'pred_cl': pred_cl, 'pred_so4': pred_so4, 'pred_sio2': pred_sio2,
                    'pred_fe': pred_fe, 'pred_turb': pred_turb,
                    'pred_cond': pred_cond, 'target_ph': target_ph,
                    'lsi': lsi_bulk, 'lsi_skin': lsi_skin, 'rsi': rsi, 'psi': psi, 'ls_idx': ls_idx,
                    'target_coc': target_coc, 'skin_offset': skin_offset
                }
                st.session_state['sim_lsi'] = lsi_bulk
                st.session_state['sim_target_ph'] = target_ph
                st.session_state.run_simulation = True

        # ----------------------------------------------------------------------
        # [결과 화면] - 시뮬레이션 버튼을 누르면 나타남
        # ----------------------------------------------------------------------
        if st.session_state.run_simulation:
            res = st.session_state.sim_results
            limits = st.session_state.cooling_limits_v5

            st.divider()
            st.subheader(f"📊 수질 예측 비교 분석 (농축배수: {res['target_coc']}배)")
            
            # 테이블 데이터 구성
            comp_data = [
                {"Item": "pH", "Make-up": res['mu_dict']['pH'], "Cooling (Pred)": res['target_ph'], "Limit (Max)": limits["pH"]},
                {"Item": "Conductivity", "Make-up": res['mu_dict']['Cond (µS)'], "Cooling (Pred)": res['pred_cond'], "Limit (Max)": limits["Conductivity"]},
                {"Item": "Calcium (Ca-H)", "Make-up": res['mu_dict']['Ca-H (ppm)'], "Cooling (Pred)": res['pred_ca'], "Limit (Max)": limits["Calcium (Ca-H)"]},
                {"Item": "M-Alkalinity", "Make-up": res['mu_dict']['M-Alk (ppm)'], "Cooling (Pred)": res['pred_alk'], "Limit (Max)": limits["M-Alkalinity"]},
                {"Item": "Chloride (Cl)", "Make-up": res['mu_dict']['Cl (ppm)'], "Cooling (Pred)": res['pred_cl'], "Limit (Max)": limits["Chloride (Cl)"]},
                {"Item": "Sulfate (SO4)", "Make-up": res['mu_dict']['SO4 (ppm)'], "Cooling (Pred)": res['pred_so4'], "Limit (Max)": limits["Sulfate (SO4)"]},
                {"Item": "Silica (SiO2)", "Make-up": res['mu_dict']['SiO2 (ppm)'], "Cooling (Pred)": res['pred_sio2'], "Limit (Max)": limits["Silica (SiO2)"]},
                {"Item": "Iron (Fe)", "Make-up": res['mu_dict'].get('Fe (ppm)', 0), "Cooling (Pred)": res['pred_fe'], "Limit (Max)": limits.get("Iron (Fe)", "1.0")},
                {"Item": "Turbidity (NTU)", "Make-up": res['mu_dict'].get('Turbidity (NTU)', 0), "Cooling (Pred)": res['pred_turb'], "Limit (Max)": limits.get("Turbidity (NTU)", "20")},
            ]
            
            df_comp = pd.DataFrame(comp_data)
            
            edited_comp = st.data_editor(
                df_comp, 
                column_config={
                    "Item": st.column_config.TextColumn("항목", disabled=True),
                    "Make-up": st.column_config.NumberColumn("보충수", format="%.1f", disabled=True),
                    "Cooling (Pred)": st.column_config.NumberColumn("순환수 (예측)", format="%.1f", disabled=True),
                    "Limit (Max)": st.column_config.TextColumn("관리 기준 (자유입력)", width="medium", help="범위(~) 또는 상한값 입력")
                },
                hide_index=True, use_container_width=True, key="limit_editor_simple_v5"
            )
            
            for index, row in edited_comp.iterrows():
                st.session_state.cooling_limits_v5[row['Item']] = str(row['Limit (Max)'])

            warnings = []
            for index, row in edited_comp.iterrows():
                try:
                    limit_val = float(row['Limit (Max)']) 
                    if row['Cooling (Pred)'] > limit_val: 
                        warnings.append(f"⚠️ **{row['Item']}** 기준 초과 ({row['Cooling (Pred)']:.1f} > {limit_val:.0f})")
                except ValueError: pass
            
            if warnings:
                with st.container(border=True):
                    st.error("🚨 **관리 기준 초과 경보**")
                    for w in warnings: st.write(w)
            else:
                st.success("✅ **Stable Operation** (특이사항 없음)")

            # [5대 지수 진단]
            st.markdown("#### 🧭 5대 핵심 지수 진단 (Skin Temp 반영)")
            m1, m2, m3, m4, m5 = st.columns(5)
            
            # 1. Bulk LSI
            lsi = res['lsi']
            lsi_col = "inverse" if lsi > 1.5 or lsi < 0 else "normal"
            m1.metric("1. LSI (Bulk)", f"{lsi:.2f}", "물 온도 기준", delta_color=lsi_col)
            
            # 2. Skin LSI
            lsi_skin = res['lsi_skin']
            skin_msg = "Safe"
            skin_col = "normal"
            if lsi_skin > 2.5:
                skin_msg = "Critical!"
                skin_col = "inverse"
            elif lsi_skin > 2.0:
                skin_msg = "Warning"
                skin_col = "inverse"
            m2.metric("2. LSI (Skin)", f"{lsi_skin:.2f}", skin_msg, delta_color=skin_col,
                      help=f"가장 뜨거운 열교환기 표면 온도 기준 (수온+{res['skin_offset']:.0f}℃)")
            
            # 3. RSI
            rsi = res['rsi']
            rsi_state = "Stable"
            if rsi < 5.0: rsi_state = "Scale Risk"
            elif rsi > 8.5: rsi_state = "Corr Risk"
            m3.metric("3. RSI (General)", f"{rsi:.2f}", rsi_state, delta_color="inverse" if "Risk" in rsi_state else "normal")
            
            # 4. Pitting (L-S Index)
            ls_idx = res['ls_idx']
            ls_msg = "Safe"
            ls_col = "normal"
            if ls_idx > 1.2: ls_msg="Pitting!"; ls_col="inverse"
            m4.metric("4. Pitting (L-S)", f"{ls_idx:.2f}", ls_msg, delta_color=ls_col)
            
            # 5. Turbidity
            pred_turb = res['pred_turb']
            dep_msg = "Clean"
            dep_col = "normal"
            if pred_turb > 20: dep_msg="Deposit!"; dep_col="inverse"
            m5.metric("5. Turbidity", f"{pred_turb:.1f} NTU", dep_msg, delta_color=dep_col)

# ------------------------------------------------------------------
            # [Advanced] 농축배수 최적화 시뮬레이션 (Cycle Optimization Study)
            # ------------------------------------------------------------------
            st.markdown("---")
            st.subheader("📈 농축배수 최적화 시뮬레이션 (Cycle Study)")
            st.info("💡 농축배수를 **2배 ~ 10배**까지 변화시켰을 때, 스케일(LSI)과 부식 지수(PSI)가 어떻게 변하는지 추세를 분석합니다.")

            # 1. 데이터 준비 (현재 입력된 보충수 수질 기준)
            mu_ph = res['mu_dict']['pH']
            mu_cond = res['mu_dict']['Cond (µS)']
            mu_ca = res['mu_dict']['Ca-H (ppm)']
            mu_alk = res['mu_dict']['M-Alk (ppm)']
            temp_c = st.session_state.sim_temp
            
            # 2. 시뮬레이션 루프 (2.0 ~ 10.0배)
            cycles_range = np.arange(2.0, 10.5, 0.5)
            sim_data = []

            for coc in cycles_range:
                # (A) 농축 수질 예측
                # 알칼리도 예측
                pred_alk_c = mu_alk * coc
                if pred_alk_c < 1: pred_alk_c = 1
                
                # pH 예측 (Buffer 구간 반영 모델)
                if pred_alk_c < 370:
                    pred_ph_c = (2.0 * math.log10(pred_alk_c)) + 3.15
                else:
                    pred_ph_c = (1.465 * math.log10(pred_alk_c)) + 4.54
                if pred_ph_c > 9.3: pred_ph_c = 9.3 # 최대 상한

                pred_tds_c = mu_cond * coc * 0.7
                pred_ca_c = mu_ca * coc

                # (B) LSI 계산
                val_a = (math.log10(max(pred_tds_c, 1)) - 1) / 10
                val_b = -13.12 * math.log10(temp_c + 273.15) + 34.55
                val_c = math.log10(max(pred_ca_c, 1)) - 0.4
                val_d = math.log10(max(pred_alk_c, 1))
                
                pHs_c = (9.3 + val_a + val_b) - (val_c + val_d)
                lsi_c = pred_ph_c - pHs_c
                
                # (C) PSI 계산 (Puckorius Scaling Index)
                p_eq_c = 1.465 * math.log10(max(pred_alk_c, 1)) + 4.54
                psi_c = (2 * pHs_c) - p_eq_c

                sim_data.append({
                    "Cycles": coc, "LSI": lsi_c, "PSI": psi_c, "pH": pred_ph_c
                })

            df_sim = pd.DataFrame(sim_data)

            # 3. 그래프 그리기 (LSI & PSI)
            c_g1, c_g2 = st.columns(2)
            
            with c_g1:
                # LSI 그래프
                fig_lsi = px.line(df_sim, x="Cycles", y="LSI", markers=True, title="Cycles vs LSI (스케일 경향)")
                fig_lsi.add_hline(y=2.5, line_dash="dash", line_color="red", annotation_text="Danger Limit (+2.5)")
                fig_lsi.add_hline(y=1.5, line_dash="dot", line_color="orange", annotation_text="Warning")
                fig_lsi.add_vline(x=res['target_coc'], line_dash="dot", line_color="green", annotation_text="현재 운전점")
                st.plotly_chart(fig_lsi, use_container_width=True)

            with c_g2:
                # PSI 그래프
                fig_psi = px.line(df_sim, x="Cycles", y="PSI", markers=True, title="Cycles vs PSI (안정성 지수)")
                fig_psi.add_hrect(y0=5.0, y1=6.0, fillcolor="green", opacity=0.1, annotation_text="Best Zone")
                fig_psi.add_hline(y=4.0, line_dash="dash", line_color="red", annotation_text="Scale Risk")
                fig_psi.add_vline(x=res['target_coc'], line_dash="dot", line_color="green", annotation_text="현재 운전점")
                st.plotly_chart(fig_psi, use_container_width=True)
            
            # 4. 최적 운전점 제안
            # LSI < 2.5 이면서 PSI > 4.0 인 최대 농축배수 찾기
            safe_df = df_sim[(df_sim['LSI'] < 2.5) & (df_sim['PSI'] > 4.0)]
            
            if not safe_df.empty:
                best_cycle = safe_df['Cycles'].max()
                st.success(f"✅ 시뮬레이션 결과, 약품 처리 하에 **최대 {best_cycle}배**까지 운전 가능합니다.")
            else:
                st.warning("⚠️ 전 구간에서 스케일 위험이 높습니다. 고성능 스케일 방지제가 필수적입니다.")

        # ----------------------------------------------------------------------
        # [가이드 섹션] - 시뮬레이션 여부와 상관없이 '항상' 맨 아래에 표시됨
        # ----------------------------------------------------------------------
        st.divider()
        with st.expander("📘 지수별 상세 관리 기준 (Reference - 항상 표시)", expanded=True):
            st.markdown("### 1. LSI (Langelier Saturation Index)")
            st.markdown("""
            | 범위 (Range) | 상태 (Condition) | 현상 및 위험 | 관리 대책 (Action) |
            | :--- | :---: | :--- | :--- |
            | **+2.0 이상** | **심각한 스케일** | 배관 막힘, 열효율 급감 | 산(Acid) 주입, 블로우다운 증대 |
            | **+0.5 ~ +2.0** | **약한 스케일** | **[관리 범위]** 얇은 막 형성 | 스케일 방지제(Inhibitor) 제어 |
            | **-0.5 ~ +0.5** | **안정 (Stable)** | 이상적 상태 | 현재 상태 유지 |
            | **-0.5 ~ -2.0** | **약한 부식** | 배관이 서서히 얇아짐 | 방식제(Zn, PO4) 농도 상향 |
            | **-2.0 이하** | **심각한 부식** | 녹물 발생 (Red Water) | pH 상승, 부식 억제제 대량 투입 |
            """)
            
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                st.markdown("### 2. Skin LSI (표면온도 기준)")
                st.markdown("""
                * **< 2.0 (안전):** 열교환기 표면도 깨끗함.
                * **2.0 ~ 2.5 (경고):** 고온부(Hot Spot) 스케일 시작.
                * **> 2.5 (위험):** **즉각 조치 필요.** 물은 맑아도 설비는 막히고 있음.
                """)
                
                st.markdown("### 3. RSI (Ryznar Stability Index)")
                st.markdown("""
                * **4.0 ~ 5.0:** 강한 스케일 (막힘 주의)
                * **5.0 ~ 6.0:** **[최적]** 약한 코팅막 형성
                * **> 8.0:** 강한 부식 (녹물 발생)
                """)

            with c_g2:
                st.markdown("### 4. L-S Index (부식 지수)")
                st.markdown("""
                * **< 0.8 (안전):** 부식 억제력 충분.
                * **0.8 ~ 1.2 (주의):** 국부 부식(Pitting) 가능성.
                * **> 1.2 (위험):** **점부식 경고.** 염소($Cl$) 농도를 낮춰야 함.
                """)

                st.markdown("### 5. 탁도 & 철분 (오염 지표)")
                st.markdown("""
                * **탁도 (Turbidity):** `> 20 NTU` 시 침적(Deposit) 부식 위험. 여과기 가동 필요.
                * **철분 (Fe):** `> 1.0 ppm` 시 배관 부식 진행 중이거나 원수 오염 의심.
                """)
# ======================================================================
    # Tab 3: Chemical Program (약품)
    # ======================================================================
    with tab3:
        st.subheader("3. Intelligent Chemical Selection System")
        st.markdown("수질 분석 및 스케일 경향에 따른 **최적 약품(Inhibitor/Biocide)**을 선정합니다.")

        # ------------------------------------------------------------------
        # 1. 데이터 소스 및 배수량 설정 (배수량 연동 강화 Ver)
        # ------------------------------------------------------------------
        
 # [A] Tab 1에서 계산된 배수량 가져오기
        if 'final_blowdown' in st.session_state and st.session_state['final_blowdown'] > 0:
            calc_blow = st.session_state['final_blowdown']
            blow_src_msg = "✅ Tab 1 물질수지 연동됨 (Auto Sync)"
        else:
            calc_blow = 10.0 # 기본값
            blow_src_msg = "⚠️ 기본값 (Tab 1 미실행)"

        # [B] 🔥 연동 문제 해결을 위한 핵심 로직 (Change Detection)
        # 설명: Tab 1 값이 바뀌었을 때만 Tab 3 입력창을 강제로 업데이트합니다.
        
        # 1. 이전에 기억해둔 계산값이 없으면 초기화
        if 'last_calc_blow' not in st.session_state:
            st.session_state.last_calc_blow = 0.0
            
        # 2. 만약 Tab 1의 계산값이 이전과 달라졌다면? (새로 계산했다는 뜻)
        if calc_blow != st.session_state.last_calc_blow:
            st.session_state['estim_blow_fix'] = calc_blow  # 입력창 값을 강제로 덮어씌움
            st.session_state.last_calc_blow = calc_blow     # 현재 값을 '이전 값'으로 기억
            # 이렇게 하면, Tab 1이 변할 때만 자동 업데이트되고, 평소에는 수동 입력도 가능합니다.

        # [C] 수질 데이터 (LSI/pH) 가져오기
        if st.session_state.get('run_simulation'):
            sim_res = st.session_state.sim_results
            curr_lsi = sim_res['lsi']
            curr_ph = sim_res['target_ph']
            
            # 보충수 LSI 계산
            mu_dict = sim_res.get('mu_dict', {})
            sys_temp = st.session_state.get('sim_temp', 35.0)
            mu_lsi = calculate_lsi(
                mu_dict.get('pH', 7.5),
                mu_dict.get('Cond (µS)', 200) * 0.7,
                mu_dict.get('Ca-H (ppm)', 40),
                mu_dict.get('M-Alk (ppm)', 50),
                sys_temp
            )
            data_src_quality = "✅ 시뮬레이션 데이터 (Simulated)"
        else:
            curr_lsi = 1.5 
            curr_ph = 8.5
            mu_lsi = 0.0
            data_src_quality = "⚠️ 기본값 (시뮬레이션 미실행)"

        # [D] 화면 표시 (입력창 + 수질정보)
        col_b1, col_b2 = st.columns([1, 2])
        
        with col_b1:
            # value 설정을 유지하되, 위쪽 [B] 로직이 우선순위를 가집니다.
            estim_blow = st.number_input(
                "운전 배수량 (Blowdown, m3/hr)", 
                value=float(f"{calc_blow:.1f}"), 
                key="estim_blow_fix",
                help="Tab 1 값이 변경되면 자동으로 반영됩니다."
            )
            st.caption(blow_src_msg)

        with col_b2:
            lsi_delta = curr_lsi - mu_lsi
            st.info(f"""
            **📊 수질 진단 리포트 ({data_src_quality})**
            * **💧 보충수 (Make-up) LSI:** `{mu_lsi:.2f}`
            * **🔥 순환수 (Cycle) LSI:** `{curr_lsi:.2f}`
            * **📈 변동폭 (Delta):** `{lsi_delta:+.2f}`
            """)

        st.divider()

        # 2. 엑셀 데이터 로드
        cooling_db = PRODUCT_CATALOG.get('Cooling', {})
        inh_list = cooling_db.get('Main_Inhibitor', [])
        disp_list = cooling_db.get('Dispersant', [])
        bio_list = cooling_db.get('Biocide', [])

        if not inh_list:
            st.error("🚨 엑셀 데이터 로드 실패: 'Cooling' 시트의 약품 정보를 확인해주세요.")
            st.stop()

        # 3. AI 추천 로직
        rec_prod_name = inh_list[0]['Name']
        rec_reason = "기본 추천"

        if curr_lsi > 2.5:
            match = next((p for p in inh_list if "308AA" in p['Name'] or "524" in p['Name']), None)
            if match: 
                rec_prod_name = match['Name']
                rec_reason = f"🔴 **고부하 조건 (LSI {curr_lsi:.2f}):** 스케일 강도가 매우 높습니다. 고성능 폴리머 복합제를 추천합니다."
        elif 1.5 <= curr_lsi <= 2.5:
            match = next((p for p in inh_list if "180" in p['Name'] or "308" in p['Name']), None)
            if match:
                rec_prod_name = match['Name']
                rec_reason = f"🟢 **표준 관리 범위 (LSI {curr_lsi:.2f}):** 경제적인 표준 인산염계 제품이 적합합니다."
        else: # LSI < 1.5
            match = next((p for p in inh_list if "Zinc" in str(p.get('Main_Ingredient','')) or "110" in p['Name']), None)
            if match:
                rec_prod_name = match['Name']
                rec_reason = f"🔵 **부식성 수질 (LSI {curr_lsi:.2f}):** 방식 효과가 뛰어난 아연(Zinc) 함유 제품을 추천합니다."

# 4. 약품 선택 및 상세 정보 연동
        c_sel1, c_sel2, c_sel3 = st.columns(3)

        # [A] 억제제 (Inhibitor) - 수정됨
        with c_sel1:
            st.markdown("#### 🛡️ Inhibitor (주처리제)")
            inh_names = [p['Name'] for p in inh_list]
            def_idx = inh_names.index(rec_prod_name) if rec_prod_name in inh_names else 0
            sel_inh = st.selectbox("제품 선택", inh_names, index=def_idx, key="sel_inh_fix")
            sel_inh_data = next((p for p in inh_list if p['Name'] == sel_inh), None)
            
            if sel_inh_data:
                with st.container(border=True):
                    inh_dose = st.number_input("주입량 (ppm)", value=float(sel_inh_data.get('Dosage', 50)), key="inh_dose_fix")
                    
                    # [변경 포인트] st.caption -> st.markdown (:color 적용)
                    st.markdown(f"**🧪 성분:** :red[{sel_inh_data.get('Main_Ingredient', '-')}]")
                    st.markdown(f"**💡 특징:** :blue[{sel_inh_data.get('Sales_Point', '-')}]")
                    
                    # [변경 포인트] st.info -> st.markdown (:green 적용)
                    if sel_inh_data.get('Field_Tip') and sel_inh_data.get('Field_Tip') != '-':
                        st.markdown(f"**🔧 Tip:** :green[{sel_inh_data.get('Field_Tip')}]")

                    if sel_inh == rec_prod_name:
                        st.success(f"✅ AI 추천 사유:\n{rec_reason}")
            
            usage_inh = (estim_blow * 24 * inh_dose) / 1000.0

        # [B] 분산제 (Dispersant) - 수정됨
        with c_sel2:
            st.markdown("#### 🧪 Dispersant (분산제)")
            if disp_list:
                disp_names = [p['Name'] for p in disp_list]
                sel_disp = st.selectbox("제품 선택", disp_names, key="sel_disp_fix")
                sel_disp_data = next((p for p in disp_list if p['Name'] == sel_disp), None)
                
                with st.container(border=True):
                    disp_dose = st.number_input("주입량 (ppm)", value=float(sel_disp_data.get('Dosage', 20)), key="disp_dose_fix")
                    
                    # [변경 포인트] 색상 적용
                    st.markdown(f"**🧪 성분:** :red[{sel_disp_data.get('Main_Ingredient', '-')}]")
                    st.markdown(f"**💡 특징:** :blue[{sel_disp_data.get('Sales_Point', '-')}]")
                    
                    if sel_disp_data.get('Field_Tip') and sel_disp_data.get('Field_Tip') != '-':
                         st.markdown(f"**🔧 Tip:** :green[{sel_disp_data.get('Field_Tip')}]")
                
                usage_disp = (estim_blow * 24 * disp_dose) / 1000.0
            else:
                st.warning("DB 없음")
                usage_disp = 0

        # [C] 살균제 (Biocide) - 수정됨
        with c_sel3:
            st.markdown("#### 🦠 Biocide (살균제)")
            if bio_list:
                bio_names = [p['Name'] for p in bio_list]
                sel_bio = st.selectbox("제품 선택", bio_names, key="sel_bio_fix")
                sel_bio_data = next((p for p in bio_list if p['Name'] == sel_bio), None)
                
                with st.container(border=True):
                    bio_dose = st.number_input("주입량 (ppm)", value=float(sel_bio_data.get('Dosage', 50)), key="bio_dose_fix")
                    
                    # [변경 포인트] 색상 적용
                    st.markdown(f"**🧪 성분:** :red[{sel_bio_data.get('Main_Ingredient', '-')}]")
                    st.markdown(f"**💡 특징:** :blue[{sel_bio_data.get('Sales_Point', '-')}]")
                    
                    if sel_bio_data.get('Field_Tip') and sel_bio_data.get('Field_Tip') != '-':
                         st.markdown(f"**🔧 Tip:** :green[{sel_bio_data.get('Field_Tip')}]")
                
                usage_bio = (estim_blow * 24 * bio_dose) / 1000.0
            else:
                st.warning("DB 없음")
                usage_bio = 0       
    
        # 5. 최종 집계 차트
        st.divider()
        st.markdown("### 📊 일일 약품 사용량 예측 (Daily Consumption)")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric(f"주처리제 ({sel_inh})", f"{usage_inh:.1f} kg/day")
        if disp_list: col_m2.metric(f"분산제 ({sel_disp})", f"{usage_disp:.1f} kg/day")
        if bio_list: col_m3.metric(f"살균제 ({sel_bio})", f"{usage_bio:.1f} kg/day")

        # 그래프 그리기
        chart_df = pd.DataFrame({
            'Type': ['Inhibitor', 'Dispersant', 'Biocide'],
            'Usage': [usage_inh, usage_disp, usage_bio],
            'Product': [sel_inh, sel_disp if disp_list else '-', sel_bio if bio_list else '-']
        })
        
        fig = px.bar(chart_df, x='Type', y='Usage', color='Type', text='Usage',
                     hover_data=['Product'], title="약품별 일일 사용량 (kg)")
        fig.update_traces(texttemplate='%{text:.1f} kg', textposition='outside')
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # ======================================================================

    # Tab 4: Lab Analysis & Deposit

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
# --------------------------------------------------------------------------
    # Tab 5: Technical Manual 
    # --------------------------------------------------------------------------
    with tab5:
        st.subheader("📘 Engineering Formulas & Theory")
        st.markdown("본 프로그램은 **Drew Principle Manual** 등 수처리 기업의 표준 공식을 준수합니다.")

        # 1. 물질수지
        with st.expander("💧 1. 냉각탑 물질수지 (Water Balance)", expanded=False):
            st.markdown("#### (1) 증발량 (Evaporation Loss)")
            st.latex(r"E = Q \times \Delta T \times F")
            st.caption("여기서 $Q$: 순환수량, $\Delta T$: 온도차, $F$: 계절계수 (0.0015)")
            
            st.markdown("#### (2) 배수량 (Blowdown)")
            st.latex(r"B = \frac{E}{COC - 1} - W")
            
            st.markdown("#### (3) 보유수 반감기 (Half Life Index)")
            st.latex(r"HTI = 0.693 \times \frac{V}{B + W}")

        # 2. 5대 스케일/부식 지수
        with st.expander("⚗️ 2. 수질 진단 5대 지수 (5 Major Indices)", expanded=False):
            st.markdown("#### ① Langelier Saturation Index (LSI)")
            st.latex(r"LSI = pH_{act} - pH_s")

            st.markdown("#### ② Ryznar Stability Index (RSI)")
            st.latex(r"RSI = 2pH_s - pH_{act}")

            st.markdown("#### ③ Puckorius Scaling Index (PSI)")
            st.latex(r"PSI = 2pH_s - pH_{eq}")

            st.markdown("#### ④ Larson-Skold Index (L-S)")
            st.latex(r"L-S = \frac{[Cl^-] + [SO_4^{2-}]}{[HCO_3^-] + [CO_3^{2-}]}")
            st.caption("0.8 이상 시 스테인리스(SUS) 국부 부식(Pitting) 위험")

            st.markdown("#### ⑤ Stiff-Davis Index (SDI)")
            st.latex(r"SDI = pH_{act} - pCa - pAlk - K")
            st.caption("고농도(전도도 4000µS/cm 이상) 수질 전용 지표")

        # 3. 농축 pH 및 수질 예측
        with st.expander("📈 3. 농축수 pH 및 수질 예측 공식", expanded=False):
            st.markdown("#### (1) 농축수 pH 예측 (pH Prediction)")
            st.latex(r"pH_{cycle} = 1.465 \times \log_{10}(Alk_{cycle}) + 4.54")
            st.caption("대기 중 CO2 평형으로 인해 pH는 보통 9.3을 넘지 않습니다.")

            st.markdown("#### (2) 이온 농축 (Cycle Chemistry)")
            st.latex(r"C_{cycle} = C_{makeup} \times COC")

        # 4. 약품 투입량 및 펌프 계산 (NEW! 요청하신 부분)
        with st.expander("💊 4. 약품 투입량 및 펌프 계산 (Chemical Dosage)", expanded=True):
            st.info("💡 현장에서 가장 많이 사용하는 **약품 투입량 산출** 및 **정량펌프 세팅** 공식입니다.")

            st.markdown("#### (1) 초기 투입량 (Initial Dosage)")
            st.markdown("시스템 가동 시작(Start-up) 시, 보유 수량 전체의 농도를 맞추기 위한 투입량입니다.")
            st.latex(r"W_{init} (kg) = \frac{V_{sys} \times C_{target}}{1000}")
            st.caption("여기서 $V_{sys}$: 보유수량($m^3$), $C_{target}$: 목표 농도($ppm$)")

            st.markdown("#### (2) 유지 투입량 (Maintenance Dosage)")
            st.markdown("운전 중 손실되는 약품(배수+비산)을 보충하여 농도를 유지하는 일일 사용량입니다.")
            st.latex(r"W_{day} (kg/day) = \frac{(B + W) \times C_{target} \times 24}{1000}")
            st.caption("여기서 $B$: 배수량($m^3/hr$), $W$: 비산량($m^3/hr$), 약품은 나가는 물만큼 빠져나갑니다.")

            st.markdown("#### (3) 살균제 충격 투입 (Biocide Slug Dosing)")
            st.markdown("살균제는 미생물 내성 방지를 위해 1주 1~2회, 고농도로 충격 투입합니다.")
            st.latex(r"W_{slug} (kg/shot) = \frac{V_{sys} \times C_{shock}}{1000}")
            st.caption("보통 비산화성 살균제는 100~150ppm, 산화성(염소)은 0.5~1.0ppm(잔류) 기준입니다.")

            st.markdown("#### (4) 정량 펌프 세팅 (Pump Setting)")
            st.markdown("일일 사용량을 기준으로 펌프의 토출 유속(ml/min)을 계산하여 다이얼을 맞춥니다.")
            st.latex(r"Q_{pump} (ml/min) = \frac{W_{day} \times 1000}{24 \times 60 \times SG}")
            st.caption("여기서 $SG$: 약품 비중(Specific Gravity). 물=1.0이며, 보통 약품은 1.1~1.2 입니다.")
            
        # 5. 참고 문헌
        st.divider()
        st.caption("📚 Reference: Drew FIELD SERVICE MANUAL")

        
# ==============================================================================
# [Module 2] Boiler Master PRO (오류 완전 해결 및 물질수지/약품설계 강화)
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

    tab_sim, tab_chem_prog, tab_safety, tab_manual= st.tabs([
        "💧Water Simulation & Balance", 
        "💊 Chemical Program (약품)", 
        "🎯 Na-PO4 Safety Map", 
        "📘 기술 매뉴얼 (Formula)",
      
    ])
    
# --- Tab 1: Water Simulation & Balance (P-Alk 추정 및 정밀 수질 예측) ---
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
            if b_coc > 1:
                b_blowdown = b_steam / (b_coc - 1)
            else:
                b_blowdown = 0.0
            
            # 2. 총 급수량 (Total Feed)
            b_feedwater = b_steam + b_blowdown
            
            # 3. 응축수량 및 보급수량 분리
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

            # 세션 저장
            st.session_state.b_res_store = {
                'steam': b_steam, 'feed': b_feedwater, 'blow': b_blowdown, 
                'coc': b_coc, 'dose_ppm': b_dose_ppm, 'naoh_pct': b_naoh_pct
            }

        # [수질 예측 계산 - 혼합 수질 및 P-Alk 반영]
        cond_tds_assumed = 5.0 
        mu_ratio = (100 - b_return_pct) / 100.0
        
        # 1. 혼합 급수(Mixed Feed) 수질 계산
        feed_cond = (mu_v['Cond (uS/cm)'] * mu_ratio) + (cond_tds_assumed * (b_return_pct/100.0))
        feed_m_alk = mu_v['M-Alk (ppm)'] * mu_ratio
        feed_cl = mu_v['Cl (ppm)'] * mu_ratio
        feed_sio2 = mu_v['SiO2 (ppm)'] * mu_ratio
        feed_fe = mu_v['Fe (ppm)'] * mu_ratio + (0.05 * (b_return_pct/100.0))
        
        # [New] 급수 P-Alk 추정 (pH 8.3 이상일 때 M-Alk의 50% 가정)
        feed_ph_est = mu_v['pH'] # 보급수 pH 기준 (간이)
        feed_p_alk = feed_m_alk * 0.5 if feed_ph_est >= 8.3 else 0.0

        # 2. 관수(Boiler Water) 농축 계산
        # 가성소다(NaOH)는 P-Alk와 M-Alk를 동시에 올림 (OH- 이므로)
        naoh_boost = b_dose_ppm * (b_naoh_pct / 100) * 1.25 # ppm as CaCO3 환산
        
        p_m_alk = (feed_m_alk * b_coc) + naoh_boost
        p_p_alk = (feed_p_alk * b_coc) + naoh_boost # 가성소다는 전량 P-Alk 기여
        
        # pH 예측 (M-Alk와 P-Alk 관계 이용)
        # 2P > M 인 경우 OH가 존재 -> pH 11 이상 상승
        if p_p_alk > 0 and p_m_alk > 0:
            if 2 * p_p_alk > p_m_alk: # OH alkalinity exists
                oh_alk = 2 * p_p_alk - p_m_alk
                p_ph = 11.0 + math.log10(max(oh_alk, 1)) * 0.6 # 경험식 보정
            else:
                p_ph = 9.3 + math.log10(max(p_m_alk, 1)) * 0.5
        else:
            p_ph = mu_v['pH']
            
        p_ph = min(p_ph, 12.5) # Max Limit
        
        p_cond = (feed_cond * b_coc) + (naoh_boost * 5.5)
        p_cl = feed_cl * b_coc
        p_sio2 = feed_sio2 * b_coc
        p_fe = feed_fe * b_coc

        # ASME 체크
        try:
            _, l_cond = Boiler_Expert_Engine.check_asme_standard(b_pressure, p_cond, p_sio2, p_m_alk)
        except:
            l_cond = 3000.0

        st.divider()
        st.subheader(f"📊 보일러 관수 수질 예측 (농축 {b_coc}배, P-Alk 추정 적용)")
        
        # [결과 테이블 - P-Alk 추가됨]
        p_df = pd.DataFrame({
            '측정 항목': ['pH (예측값)', 'P-Alk (ppm)', 'M-Alk (ppm)', 'Cond (uS/cm)', 'SiO2 (ppm)', 'Cl (ppm)'],
            '보급수 (Make-up)': [f"{mu_v['pH']:.1f}", f"{feed_p_alk:.1f} (Est)", f"{mu_v['M-Alk (ppm)']:.1f}", f"{mu_v['Cond (uS/cm)']:.1f}", f"{mu_v['SiO2 (ppm)']:.1f}", f"{mu_v['Cl (ppm)']:.1f}"],
            '혼합 급수 (Feed)': ["-", f"{feed_p_alk*mu_ratio:.1f}", f"{feed_m_alk:.1f}", f"{feed_cond:.1f}", f"{feed_sio2:.1f}", f"{feed_cl:.1f}"],
            '관수 (Boiler W)': [f"{p_ph:.1f}", f"{p_p_alk:.0f}", f"{p_m_alk:.0f}", f"{p_cond:.0f}", f"{p_sio2:.1f}", f"{p_cl:.1f}"],
            'ASME/관리 기준': ["11.0~11.8", "M-Alk의 1/2↑", "800 이하", f"{l_cond:.0f} 이하", "P 비례", "-"]
        })
        st.table(p_df)
        
        # P-Alk/M-Alk 비율 진단
        if p_m_alk > 0:
            pm_ratio = p_p_alk / p_m_alk
            if pm_ratio < 0.4:
                st.warning(f"⚠️ **P-Alk 부족 ({pm_ratio:.2f}):** P-Alk가 M-Alk의 50% 미만입니다. 실리카 스케일 위험이 있으니 가성소다 비중을 높이세요.")
            elif pm_ratio > 0.6:
                st.info(f"✅ **Free OH 확보 ({pm_ratio:.2f}):** P-Alk가 충분하여 실리카가 용해 상태로 유지됩니다.")
# ----------------------------------------------------------------------
        # [Advanced] 보일러 농축 한계 시뮬레이션 (Cycle Limit Study) - 현장 정밀 보정
        # ----------------------------------------------------------------------
        st.markdown("---")
        st.subheader("📈 농축배수 한계점 진단 (Limit Study)")
        
        # 1. 기준 데이터 준비 (ABMA 표준 & 실리카 특성 반영)
        
        # [1] TDS 제한선 (계단식 기준)
        if b_pressure <= 20: 
            abma_limit_tds = 3500
            range_msg = "저압 구간 (0~20 bar)"
        elif b_pressure <= 30: 
            abma_limit_tds = 3000
            range_msg = "중압 구간 (21~30 bar)"
        elif b_pressure <= 40: 
            abma_limit_tds = 2500
            range_msg = "고압 구간 (31~40 bar)"
        elif b_pressure <= 50: 
            abma_limit_tds = 2000
            range_msg = "초고압 구간 (41~50 bar)"
        else: 
            abma_limit_tds = 1500
            range_msg = "극초고압 (>50 bar)"

        st.info(f"💡 현재 압력 **{b_pressure} bar**는 **[{range_msg}]**에 해당하며, 허용 TDS는 **{abma_limit_tds} ppm**입니다.")

        # [2] 실리카 휘발성 (Volatility) 판정
        # 실리카는 40bar 이상에서만 스팀으로 넘어가는 성질이 있음 (Ray's Diagram)
        ignore_silica = False
        if b_pressure < 30:
            ignore_silica = True
            dist_ratio = 0.0 # 저압에서는 휘발 안 함
            st.success("✅ **저압 운전 (<30 bar):** 실리카 캐리오버(Carryover) 위험이 없어 **무시합니다.**")
        else:
            # 고압에서는 압력에 비례해 기하급수적으로 증가
            dist_ratio = 0.00005 * math.pow(b_pressure, 1.8) 
            st.warning("⚠️ **고압 운전 (≥30 bar):** 실리카가 스팀으로 녹아들어갈 위험이 있어 **정밀 관리**합니다.")

        # 2. 시뮬레이션 실행 (5배 ~ 60배)
        cycles_range = np.arange(5, 65, 1)
        sim_data = []

        # 급수(Feedwater) 수질
        feed_tds = mu_v.get('Cond (uS/cm)', 150) * (1 - b_return_pct/100)
        feed_sio2 = mu_v.get('SiO2 (ppm)', 2.0) * (1 - b_return_pct/100)

        limit_factor = "None" 
        max_safe_cycle = 5.0 

        for cyc in cycles_range:
            # (A) 보일러수 수질 예측
            bw_tds = feed_tds * cyc
            bw_sio2 = feed_sio2 * cyc
            
            # (B) 스팀 실리카 예측 (ppb)
            steam_sio2_ppb = (bw_sio2 * dist_ratio) * 1000 
            
            # (C) 판정 (Pass/Fail)
            status = "Safe"
            
            # 기준 1: TDS (ABMA)
            if bw_tds > abma_limit_tds:
                status = "Fail (TDS)"
                if limit_factor == "None": limit_factor = "TDS (거품 발생 위험)"
            
            # 기준 2: Steam Silica (고압일 때만 체크)
            if not ignore_silica and steam_sio2_ppb > 20:
                status = "Fail (SiO2)"
                if limit_factor == "None": limit_factor = "Silica (터빈 보호)"
            
            if status == "Safe":
                max_safe_cycle = cyc

            sim_data.append({
                "Cycles": cyc,
                "Boiler TDS": bw_tds,
                "Steam SiO2 (ppb)": steam_sio2_ppb,
                "Status": status
            })

        df_sim = pd.DataFrame(sim_data)

        # 3. 결과 시각화
        c_res1, c_res2 = st.columns(2)
        
        with c_res1:
            st.markdown(f"**① TDS 제한선 (기준: {abma_limit_tds} ppm)**")
            fig_tds = px.line(df_sim, x="Cycles", y="Boiler TDS", title="농축배수 vs TDS Trend")
            fig_tds.add_hline(y=abma_limit_tds, line_dash="dash", line_color="red", annotation_text="ABMA Limit")
            fig_tds.add_vline(x=max_safe_cycle, line_dash="dot", line_color="green", annotation_text="Max Safe")
            st.plotly_chart(fig_tds, use_container_width=True)
            
        with c_res2:
            st.markdown("**② 스팀 실리카 (Steam Purity)**")
            if ignore_silica:
                # 저압일 때는 그래프 대신 메시지 표시 or 빈 그래프
                st.info("비활성화: 저압 조건에서는 실리카가 스팀으로 넘어가지 않습니다.")
                fig_sio2 = px.line(title="Low Pressure - No Silica Risk")
                fig_sio2.add_annotation(text="Safe Zone (Low Pressure)", x=30, y=0, showarrow=False, font=dict(size=20))
            else:
                fig_sio2 = px.line(df_sim, x="Cycles", y="Steam SiO2 (ppb)", title="농축배수 vs 스팀 실리카")
                fig_sio2.add_hline(y=20, line_dash="dash", line_color="red", annotation_text="Turbine Limit (20ppb)")
                fig_sio2.add_vline(x=max_safe_cycle, line_dash="dot", line_color="green", annotation_text="Max Safe")
            
            st.plotly_chart(fig_sio2, use_container_width=True)

        # 4. 최종 진단 리포트
        st.subheader("📢 진단 결과")
        
        # (1) 한계점 판정 메시지 출력
        if limit_factor == "None":
            st.success(f"✅ 현재 조건에서는 **60배수 이상** 고농축 운전도 가능합니다. (수질 매우 양호)")
        else:
            if ignore_silica:
                st.success(f"✅ 저압 조건이므로 실리카 제한은 없습니다.")
                
            st.warning(f"⚠️ 운전 가능 최대 농축배수는 **{max_safe_cycle}배** 입니다.")
            st.error(f"🛑 제한 요인: **{limit_factor}** 기준을 초과합니다.")

        # (2) 에너지 절감액 계산 (들여쓰기 수정됨)
        # 위에서 '안전'하든 '경고'가 떴든, 목표 배수가 현재 배수보다 높으면 계산합니다.
        if max_safe_cycle > b_coc:
            st.markdown("---")
            st.subheader("💰 에너지 비용 절감 분석 (Cost Benefit)")
            st.info("💡 농축배수를 올리면 **'버려지는 뜨거운 물(Blowdown)'**이 줄어들어 연료비가 절감됩니다.")

            col_cost1, col_cost2 = st.columns(2)
            
            with col_cost1:
                # [입력 1] 톤당 단가 (가스비가 대부분)
                unit_cost = st.number_input(
                    "블로우다운 톤당 단가 (원/ton)", 
                    value=40000, step=1000, format="%d",
                    help="고온수(150~200도) 1톤을 만드는 데 들어가는 비용 (연료비+용수비+약품비). 통상 3~5만원 적용"
                )
            
            with col_cost2:
                # [입력 2] 가동 일수
                op_days = st.number_input("연간 가동 일수 (일/년)", value=300, step=10)

            # [계산 로직]
            # 1. 현재 배수일 때 버리는 물 양
            curr_blow_rate = b_steam / (b_coc - 1)
            # 2. 최적 배수일 때 버리는 물 양
            opt_blow_rate = b_steam / (max_safe_cycle - 1)
            # 3. 아끼는 물 양 (시간당)
            save_rate_hr = curr_blow_rate - opt_blow_rate
            # 4. 연간 절감량 (톤)
            save_ton_year = save_rate_hr * 24 * op_days
            # 5. 연간 절감액 (원)
            save_money_year = save_ton_year * unit_cost

            # [결과 리포트]
            st.markdown(f"""
            #### 📊 분석 결과
            * **시간당 절감량:** `{save_rate_hr:.2f} ton/hr` (고온 배출수 감소)
            * **연간 절감 물량:** `{save_ton_year:,.0f} ton/year` ({op_days}일 기준)
            * **💰 연간 예상 절감액:** :green[**{save_money_year/100000000:.2f} 억원**]
            """)
            
            st.caption(f"※ 계산 근거: {save_ton_year:,.0f}톤 × {unit_cost:,}원 = {save_money_year:,.0f}원")
# ======================================================================
    # Tab 2: Chemical Program (색상 강조 적용 Ver)
    # ======================================================================
    with tab_chem_prog:
        st.subheader("2. Integrated Boiler Chemical Program")
        
        res = st.session_state.get('b_res_store', {'feed': 10.0, 'dose_ppm': 100.0})
        st.info(f"💡 **물질수지 기반 설계:** 급수량 {res['feed']:.1f} ton/hr | 청관제 목표 {res['dose_ppm']:.1f} ppm")
        st.markdown("---")
        
        c_col1, c_col2, c_col3 = st.columns(3)
        boiler_db = PRODUCT_CATALOG.get('Boiler', {})
        
        # 1. 탈산제 (Oxygen Scavenger)
        with c_col1:
            st.markdown("#### 🌬️ Oxygen Scavenger")
            oxy_list = boiler_db.get('Oxygen_Scavenger') or boiler_db.get('OxygenScavenger') or []
            
            if oxy_list:
                sel_oxy = st.selectbox("탈산제 선택", [o['Name'] for o in oxy_list], key="b_sel_oxy_safe")
                oxy_item = next((i for i in oxy_list if i['Name'] == sel_oxy), None)
                def_oxy = float(oxy_item['Dosage']) if oxy_item else 20.0
                
                # [수정] 상세 설명 카드 (색상 적용)
                if oxy_item:
                    with st.container(border=True):
                        st.markdown(f"**🧪 성분:** :red[{oxy_item.get('Main_Ingredient', '-')}]")
                        st.markdown(f"**💡 특징:** :blue[{oxy_item.get('Sales_Point', '-')}]")
                        
                        if oxy_item.get('Field_Tip') and oxy_item.get('Field_Tip') != '-':
                            st.markdown(f"**🔧 Tip:** :green[{oxy_item.get('Field_Tip')}]")
            else:
                st.warning("데이터 없음")
                sel_oxy = None
                def_oxy = 0.0
            
            oxy_dose = st.number_input("탈산제 농도 (ppm)", value=def_oxy, key="b_oxy_val_safe")
            usage_oxy = (res['feed'] * 24 * oxy_dose) / 1000.0

        # 2. 청관제 (Scale Inhibitor)
        with c_col2:
            st.markdown("#### 🛡️ Scale Inhibitor")
            scale_list = boiler_db.get('Scale_Disp') or boiler_db.get('Inhibitor') or []
            
            if scale_list:
                sel_scale = st.selectbox("청관제 선택", [s['Name'] for s in scale_list], key="b_sel_scale_safe")
                scale_item = next((i for i in scale_list if i['Name'] == sel_scale), None)
                
                # [수정] 상세 설명 카드 (색상 적용)
                if scale_item:
                    with st.container(border=True):
                        st.markdown(f"**🧪 성분:** :red[{scale_item.get('Main_Ingredient', '-')}]")
                        st.markdown(f"**💡 특징:** :blue[{scale_item.get('Sales_Point', '-')}]")
                        
                        if scale_item.get('Field_Tip') and scale_item.get('Field_Tip') != '-':
                            st.markdown(f"**🔧 Tip:** :green[{scale_item.get('Field_Tip')}]")
            else:
                st.warning("데이터 없음")
            
            scale_dose = st.number_input("청관제 농도 (ppm)", value=float(res['dose_ppm']), key="b_scale_val_safe")
            usage_scale = (res['feed'] * 24 * scale_dose) / 1000.0

        # 3. 복수처리제 (Condensate)
        with c_col3:
            st.markdown("#### 🧪 Condensate")
            cond_list = boiler_db.get('Condensate') or boiler_db.get('응축수 pH') or []
            
            if cond_list:
                sel_cond = st.selectbox("복수처리제 선택", [c['Name'] for c in cond_list], key="b_sel_cond_safe")
                cond_item = next((i for i in cond_list if i['Name'] == sel_cond), None)
                def_cond = float(cond_item['Dosage']) if cond_item else 5.0
                
                # [수정] 상세 설명 카드 (색상 적용)
                if cond_item:
                    with st.container(border=True):
                        st.markdown(f"**🧪 성분:** :red[{cond_item.get('Main_Ingredient', '-')}]")
                        st.markdown(f"**💡 특징:** :blue[{cond_item.get('Sales_Point', '-')}]")
                        
                        if cond_item.get('Field_Tip') and cond_item.get('Field_Tip') != '-':
                            st.markdown(f"**🔧 Tip:** :green[{cond_item.get('Field_Tip')}]")
            else:
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

# --- Tab 3: Na-PO4 Safety Map (저압/고압 모드 선택 기능 추가) ---
    with tab_safety:
        st.subheader("3. Na-PO4 Coordinate Map & Action Plan")
        
        c_s1, c_s2 = st.columns([1, 2])
        
        with c_s1:
            with st.container(border=True):
                st.markdown("### ⚙️ 설정 및 입력")
                
                # [New] 운전 모드 선택 (저압 vs 고압)
                boiler_type = st.radio(
                    "운전 모드 (Pressure Mode)", 
                    ["저압 보일러 (≤ 20bar)", "고압 보일러 (> 60bar)"],
                    index=0, # 기본값을 저압으로 설정
                    help="저압은 pH를 높게(11.0~11.8) 유지하며, 고압은 pH를 낮게(9.4~10.5) 관리합니다."
                )

                st.markdown("---")
                st.info("보일러 관수(Boiler Water) 분석치를 입력하세요.")
                cur_ph = st.number_input("현재 pH (at 25℃)", 8.0, 13.0, 11.5, 0.1, key="b_safe_ph_final")
                cur_po4 = st.number_input("현재 PO4 (ppm)", 0.0, 80.0, 25.0, 1.0, key="b_safe_po4_final")
        
        # [모드에 따른 기준값 변경]
        if "저압" in boiler_type:
            # 저압 표준 (KS/JIS 20bar 미만)
            safe_ph_min, safe_ph_max = 11.0, 11.8
            safe_po4_min, safe_po4_max = 20, 40
            limit_caustic_slope = 0.01 # 저압은 가성소다 허용하므로 완만하게
            mode_msg = "저압 표준 (High pH / Free OH 허용)"
        else:
            # 고압 표준 (Coordinated Phosphate)
            safe_ph_min, safe_ph_max = 9.4, 10.5
            safe_po4_min, safe_po4_max = 10, 30
            limit_caustic_slope = 0.025 # 고압은 엄격
            mode_msg = "고압 표준 (Low pH / Free OH 금지)"

        # [그래프 그리기]
        with c_s2:
            fig_map = go.Figure()
            
            # 1. 안전 영역 (Safe Zone) - 모드에 따라 박스 위치가 변함
            fig_map.add_shape(type="rect", 
                              x0=safe_po4_min, y0=safe_ph_min, 
                              x1=safe_po4_max, y1=safe_ph_max, 
                              line=dict(color="Green", width=2), fillcolor="rgba(0, 255, 0, 0.1)")
            
            # 2. 위험 한계선 (참고용)
            x_r = np.linspace(0, 80, 100)
            # 상한선 (Caustic Limit) - 저압일 땐 12.0 근처에서 시작
            base_ph = 12.2 if "저압" in boiler_type else 11.6
            fig_map.add_trace(go.Scatter(x=x_r, y=base_ph-(x_r*limit_caustic_slope), mode='lines', name='Upper Limit', line=dict(color='red', dash='dash')))
            
            # 3. 내 위치 찍기
            fig_map.add_trace(go.Scatter(x=[cur_po4], y=[cur_ph], mode='markers+text', 
                                         marker=dict(size=18, color="blue", symbol="x"), 
                                         text=["Current"], textposition="top center", name="내 운전점"))
            
            fig_map.update_layout(
                title=f"Na-PO4 상관관계도 - [{mode_msg}]",
                xaxis_title="Phosphate (PO4, ppm)", 
                yaxis_title="pH (at 25℃)", 
                height=450,
                xaxis=dict(range=[0, 80]),
                yaxis=dict(range=[8.5, 12.5])
            )
            st.plotly_chart(fig_map, use_container_width=True)

        # ----------------------------------------------------------------------
        # [자동 조치 가이드] - 모드별 기준 적용
        # ----------------------------------------------------------------------
        st.divider()
        st.subheader("📢 상태 진단 및 조치 가이드")
        
        # 진단 로직
        is_ph_high = cur_ph > safe_ph_max
        is_ph_low = cur_ph < safe_ph_min
        is_po4_high = cur_po4 > safe_po4_max
        is_po4_low = cur_po4 < safe_po4_min
        
        # 1. 정상 상태
        if not (is_ph_high or is_ph_low or is_po4_high or is_po4_low):
            st.success(f"✅ **[정상]** 현재 pH({cur_ph})와 인산염({cur_po4})은 **{boiler_type}** 기준에 완벽하게 부합합니다.")
        
        # 2. 비정상 상태
        else:
            c_diag1, c_diag2 = st.columns(2)
            with c_diag1:
                st.error("🚨 **현재 상태 진단**")
                if is_ph_high: st.write(f"- **pH 과다:** 기준치({safe_ph_max}) 초과. {'가성취화 위험' if '고압' in boiler_type else '알칼리 과다'}")
                if is_ph_low: st.write(f"- **pH 부족:** 기준치({safe_ph_min}) 미달. 산성 부식 위험.")
                if is_po4_high: st.write(f"- **PO4 과다:** 기준치({safe_po4_max}) 초과. 캐리오버 위험.")
                if is_po4_low: st.write(f"- **PO4 부족:** 기준치({safe_po4_min}) 미달. 스케일 발생 위험.")

            with c_diag2:
                st.warning("🛠️ **조치 가이드**")
                if is_ph_high: st.markdown("👉 **가성소다(NaOH) 주입량을 줄이십시오.**")
                if is_ph_low: st.markdown("👉 **가성소다 주입량을 늘리십시오.**")
                if is_po4_high: st.markdown("👉 **블로우다운을 실시하여 농도를 낮추십시오.**")
                if is_po4_low: st.markdown("👉 **청관제 투입량을 늘리십시오.**")
# ======================================================================
    # Tab 4: Technical Manual (보일러 기술 매뉴얼) - 수정 완료
    # ======================================================================
    with tab_manual:
        st.subheader("📘 Boiler Engineering Formulas & Theory")
        st.markdown("본 프로그램은 **ASME / ABMA / JIS** 보일러 관리 표준 공식을 준수합니다.")

        # 1. 보일러 물질수지
        with st.expander("🔥 1. 보일러 물질수지 (Mass Balance)", expanded=True):
            st.info("증기 생산을 위해 필요한 급수량과 배출해야 할 블로우다운량을 계산합니다.")
            
            st.markdown("#### (1) 농축배수 (Cycles of Concentration)")
            st.latex(r"COC = \frac{\text{Boiler TDS}}{\text{Feedwater TDS}} = \frac{\text{Boiler Cl}}{\text{Feedwater Cl}}")
            st.caption("관수(보일러 내부 물)가 급수 대비 얼마나 농축되었는지를 나타내는 지표입니다.")

            st.markdown("#### (2) 배수량 (Blowdown Rate)")
            st.markdown("증기 생산량($S$) 기준으로 계산할 때:")
            st.latex(r"B (ton/hr) = \frac{S}{COC - 1}")
            st.caption("농축배수를 유지하기 위해 버려야 하는 물의 양입니다.")

            st.markdown("#### (3) 급수량 (Feedwater Rate)")
            st.latex(r"F (ton/hr) = S + B")
            st.caption("증기($S$)로 나가는 양과 배수($B$)로 버리는 양을 합친 만큼 급수해야 수위가 유지됩니다.")

            st.markdown("#### (4) 블로우다운율 (Blowdown %)")
            st.latex(r"BD(\%) = \frac{1}{COC} \times 100")
            st.caption("급수량 대비 배수량의 비율입니다. (예: 10배 농축 시 10% 배수)")

        # 2. 약품 투입 반응식
        with st.expander("💊 2. 약품 투입 원리 및 반응식 (Chemical Reaction)", expanded=True):
            
            st.markdown("#### (1) 탈산제 반응 (Oxygen Scavenger)")
            st.markdown("물속 용존 산소($O_2$)를 제거하여 부식을 방지합니다.")
            
            # [A] 아황산나트륨 (저압용)
            st.info("**① 아황산나트륨 ($Na_2SO_3$) - 저압용**")
            st.latex(r"2Na_2SO_3 + O_2 \rightarrow 2Na_2SO_4")
            st.caption("반응이 빠르지만 고압에서 황산염($SO_4$) 스케일 원인이 될 수 있음.")

            # [B] 카보하이드라자이드 (고압용/청정용)
            st.success("**② 카보하이드라자이드 ($N_4H_6CO$) - 고압/청정용**")
            st.latex(r"(N_2H_3)_2CO + 2O_2 \rightarrow 2N_2 \uparrow + 3H_2O + CO_2 \uparrow")
            st.caption("독성인 하이드라진을 대체하는 안전한 물질. 분해 시 **질소($N_2$)와 물($H_2O$)**만 남아 매우 청정합니다.")
            st.markdown("- **특징:** 저온에서도 반응성이 좋으며, 금속 산화물(녹)을 환원시키는 **금속 부동태화(Passivation)** 효과가 탁월함.")

            st.markdown("---")

            st.markdown("#### (2) 청관제 반응 (Phosphate Treatment)")
            st.markdown("경도 성분($Ca, Mg$)을 연질 슬러지($PO_4$)로 만들어 눌어붙지 않게 합니다.")
            st.info("**인산칼슘 ($Ca_3(PO_4)_2$) 생성 반응:**")
            st.latex(r"3Ca^{2+} + 2PO_4^{3-} \rightarrow Ca_3(PO_4)_2 \downarrow (\text{Sludge})")
            st.caption("딱딱한 $CaCO_3$ 스케일 대신, 배출하기 쉬운 $Ca_3(PO_4)_2$ 슬러지로 변환시킵니다.")

            st.markdown("#### (3) 응축수 처리 (Condensate Treatment)")
            st.latex(r"R-NH_2 + H_2CO_3 \rightarrow R-NH_3^+ + HCO_3^-")
            st.caption("휘발성 아민이 증기와 함께 날아가서 응축수의 pH를 8.5~9.0으로 유지시킵니다.")

        # 3. 고압 보일러 특수 이론 (들여쓰기 수정됨!)
        with st.expander("🔥 3. 고압 보일러 특수 이론 (Advanced Theory)", expanded=True):
            st.markdown("#### (1) 실리카의 증기 이행 (Silica Carryover)")
            st.info("고압에서 실리카($SiO_2$)는 기체처럼 변해 스팀에 녹아듭니다. (Selective Carryover)")
            
            st.latex(r"D = \frac{C_{steam}}{C_{boiler}} \approx 0.00005 \times P^{1.8}")
            st.caption("여기서 $D$: 분배 계수, $P$: 압력(bar). 압력이 높을수록 기하급수적으로 스팀 오염도가 증가합니다.")
            st.markdown("- **영향:** 터빈 날개(Blade)에 **유리(Glass) 형태의 스케일**을 형성하여 효율을 급감시킵니다.")

            st.markdown("#### (2) 가성취화 (Caustic Embrittlement)")
            st.info("농축된 알칼리($NaOH$)가 인장 응력을 받는 철판의 입계(Grain Boundary)를 파고드는 현상입니다.")
            
            st.latex(r"Fe + 2NaOH \rightarrow Na_2FeO_2 + H_2 \uparrow")
            st.caption("철이 가성소다와 반응하여 녹아버리고, 수소 가스가 금속 조직을 파괴합니다.")
            st.markdown("- **방지법:** **Coordinated Phosphate** 처리를 통해 Free NaOH를 제거해야 합니다.")
            st.latex(r"3Na^+ + PO_4^{3-} \rightarrow Na_3PO_4 (\text{Safe Buffer})")
        # ----------------------------------------------------------------------
        # 4. 글로벌 수질 관리 표준 (ASME / JIS / KS 정밀 데이터 반영)
        # ----------------------------------------------------------------------
        st.divider()
        st.subheader("⚖️ Global Boiler Water Quality Standards (Detailed)")
        st.info("💡 엑셀 데이터 기반의 **압력별 상세 관리 기준**입니다.")

        # [수정] 탭을 3개로 명확하게 선언합니다 (이전 에러 원인 해결)
        std_t1, std_t2, std_t3 = st.tabs(["🇺🇸 ASME (미국)", "🇯🇵 JIS (일본)", "🇰🇷 KS (한국)"])

        # [1] ASME (미국 기계학회)
        with std_t1:
            st.markdown("### 🇺🇸 ASME Suggested Water Chemistry")
            st.caption("※ 압력 단위: MPa (괄호 안은 psig), 값은 보일러 수(Boiler Water) 기준")
            asme_data = {
                "Pressure (MPa)": ["0 - 2.07", "2.08 - 3.10", "3.11 - 4.14", "4.15 - 5.17", "5.18 - 6.21", "6.22 - 6.89", "6.90 - 10.34", "10.35 - 13.79"],
                "Silica (ppm SiO2)": ["≤ 150", "≤ 90", "≤ 40", "≤ 30", "≤ 20", "≤ 8", "≤ 2", "≤ 1"],
                "Total Alkalinity (ppm)": ["< 350", "< 300", "< 250", "< 200", "< 150", "< 100", "NS", "NS"],
                "Conductance (µS/cm)": ["1100 - 5400", "900 - 4600", "800 - 3800", "300 - 1500", "200 - 1200", "200 - 1000", "≤ 150", "≤ 80"]
            }
            st.dataframe(pd.DataFrame(asme_data).set_index("Pressure (MPa)"), use_container_width=True)

        # [2] JIS (일본 표준)
        with std_t2:
            st.markdown("### 🇯🇵 JIS B 8223 (Water Conditioning)")
            st.caption("※ 보일러 수(관수) 관리 기준치")
            jis_data = {
                "Pressure (MPa)": ["≤ 1", "1 - 2", "2 - 3", "3 - 5", "5 - 7.5", "7.5 - 10"],
                "pH (25℃)": ["11.0 ~ 11.8", "11.0 ~ 11.6", "10.8 ~ 11.6", "10.5 ~ 11.5", "10.0 ~ 11.0", "9.6 ~ 10.6"],
                "Conductivity (µS)": ["Max 6000", "Max 5000", "Max 4000", "Max 2500", "Max 1500", "Max 1000"],
                "M-Alk (ppm)": ["Max 800", "Max 600", "Max 400", "Max 250", "Max 130", "Max 80"],
                "Chloride (ppm)": ["Max 500", "Max 500", "Max 300", "Max 150", "Max 100", "Max 50"],
                "Phosphate (ppm)": ["20 ~ 40", "20 ~ 40", "20 ~ 30", "10 ~ 30", "10 ~ 30", "5 ~ 15"],
                "Sulfite (ppm)": ["10 ~ 20", "10 ~ 20", "10 ~ 20", "10 ~ 20", "5 ~ 10", "5 ~ 10"]
            }
            st.dataframe(pd.DataFrame(jis_data).set_index("Pressure (MPa)").T, use_container_width=True)

        # [3] KS (한국 표준)
        with std_t3:
            st.markdown("### 🇰🇷 KS B 6209 (보일러 수질)")
            st.caption("대한민국 산업 표준 (수관식 보일러). 압력 단위는 **MPa** 입니다.")
            
            st.markdown("**[1] 저압 ~ 중압 구간 (20 bar 미만 ~ 50 bar)**")
            st.markdown("""
            | 구분 (Item) | **≤ 1 MPa** | **1 ~ 2 MPa** | **2 ~ 3 MPa** | **3 ~ 5 MPa** |
            | :--- | :---: | :---: | :---: | :---: |
            | **pH (25℃)** | 11.0 ~ 11.8 | 11.0 ~ 11.6 | 10.8 ~ 11.6 | 10.5 ~ 11.5 |
            | **전도도 (µS)** | Max 6,000 | Max 5,000 | Max 4,000 | Max 2,500 |
            | **P-알칼리도** | Max 800 | Max 600 | Max 400 | Max 300 |
            | **실리카 (SiO2)** | - | - | - | Max 80 |
            | **인산이온 (PO4)** | 20 ~ 40 | 20 ~ 40 | 10 ~ 30 | 10 ~ 30 |
            """)
            
            st.markdown("**[2] 고압 ~ 초고압 구간 (50 bar 이상)**")
            st.markdown("""
            | 구분 (Item) | **5 ~ 7.5 MPa** | **7.5 ~ 10 MPa** | **10 ~ 15 MPa** | **15 ~ 20 MPa** |
            | :--- | :---: | :---: | :---: | :---: |
            | **pH (25℃)** | 10.0 ~ 11.0 | 9.6 ~ 10.6 | 9.4 ~ 10.2 | 9.2 ~ 10.0 |
            | **전도도 (µS)** | Max 1,500 | Max 1,000 | Max 500 | Max 150 |
            | **실리카 (SiO2)** | Max 50 | Max 30 | Max 10 | Max 3 |
            | **인산이온 (PO4)** | 5 ~ 20 | 2 ~ 10 | 2 ~ 6 | - |
            """)
            
            st.success("✅ **참고:** 1 MPa = 10 bar 입니다. (예: 2 MPa = 20 bar)")

# ==============================================================================
# [Module 3] RO Master Pro (변수 순서 오류 수정: 입력창 최상단 배치)
# ==============================================================================
elif "RO" in program_mode:
    # 1. 초기 데이터 및 세션 설정
    if 'ro_v26_data' not in st.session_state:
        st.session_state.ro_v26_data = pd.DataFrame({
            '항목': ['pH', 'Cond (µS)', 'Ca', 'Cl', 'M-Alk', 'Fe', 'SiO2', 'SO4'],
            '농도 (mg/L)': [7.5, 1000.0, 80.0, 150.0, 200.0, 0.1, 15.0, 0.0]
        })

    st.title("🌊 RO Master Pro (Smart Operations)")
    st.info("AI 기반 수질 예측, 성능 진단, 약품 시뮬레이션 및 CIP/유지관리 통합 시스템")
# --------------------------------------------------------------------------
    # [★핵심 수정] 변수 안전 초기화 (Safety Initialization)
    # --------------------------------------------------------------------------
    # 이 부분이 없으면 expander를 안 열었을 때 뒤에서 에러가 납니다.
    # 무조건 0.0으로 먼저 만들어 놓고 시작합니다.
    val_mg = 0.0
    val_na = 0.0
    val_k = 0.0
    val_ba = 0.0
    val_sr = 0.0
    val_f = 0.0
    val_fe = 0.0
    val_mn = 0.0
    val_al = 0.0
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # [0] 운전 조건 입력 (여기가 제일 먼저 실행되어야 함! ★수정됨★)
    # --------------------------------------------------------------------------
    # 탭보다 위에 있어야 모든 탭에서 변수(in_flow 등)를 인식합니다.
    with st.expander("⚙️ 운전 조건 설정 (Design Factors)", expanded=True):
        col_in1, col_in2, col_in3, col_in4 = st.columns(4)
        with col_in1: 
            in_flow = st.number_input("생산 유량 (m3/hr)", value=50.0, step=1.0, key="ro_in_flow_fix")
        with col_in2: 
            in_rec = st.number_input("설계 회수율 (%)", value=75.0, step=1.0, key="ro_in_rec_fix")
        with col_in3: 
            in_temp = st.number_input("원수 수온 (°C)", value=25.0, step=1.0, key="ro_in_temp_fix")
        with col_in4: 
            in_ph = st.number_input("원수 pH", value=7.5, step=0.1, key="ro_in_ph_fix")

    # 6개 탭 구성
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🧪 스마트 수질 분석", 
        "🔮 성능 열화 진단", 
        "🚨 스케일 정밀 진단", 
        "💊 약품 투입 시뮬레이션", 
        "🛠️ O&M 및 CIP 가이드",
        "📘 기술 매뉴얼 (Formula)"

    ])

# ==========================================================================
    # [Tab 1] 스마트 수질 분석 (Step 3: 특수 항목 Ba, Sr, F 추가 완료)
    # ==========================================================================
    with tab1:
        st.subheader("Step 1. Smart Water Analysis & Auto-Balancing")
        st.info("💡 **[3단계 완료]** 바륨(Ba), 스트론튬(Sr), 불소(F) 등 특수 이온 입력창이 추가되었습니다.")

        # [1] 변수 사전 초기화 (안전장치)
        val_mg = 0.0; val_na_meas = 0.0; val_k = 0.0; val_fe = 0.0
        val_nh4 = 0.0; val_no3 = 0.0; val_no2 = 0.0; val_al = 0.0
        # [NEW] 3단계 추가 변수
        val_ba = 0.0; val_sr = 0.0; val_f = 0.0

        # [2] 운전 조건 표시
        col_ref1, col_ref2, col_ref3, col_ref4 = st.columns(4)
        with col_ref1: st.caption(f"💧 유량: {in_flow} m3/hr")
        with col_ref2: st.caption(f"🔄 회수율: {in_rec} %")
        with col_ref3: st.caption(f"🌡️ 수온: {in_temp} °C")
        with col_ref4: st.caption(f"🧪 pH: {in_ph}")

        st.divider()

        col_input, col_result = st.columns([1, 1.2])

        # [3] 데이터 입력창
        with col_input:
            st.markdown("###### 📝 필수 측정 항목 (Measured)")
            c1, c2 = st.columns(2)
            with c1:
                val_ec = st.number_input("전도도 (µS/cm)", value=1000.0, step=10.0)
                val_ca = st.number_input("Ca (mg/L)", value=80.0, step=1.0)
                val_alk = st.number_input("M-Alk (mg/L)", value=150.0, step=10.0)
                val_sio2 = st.number_input("SiO2 (mg/L)", value=15.0, step=1.0)
            with c2:
                st.empty() 
                val_cl = st.number_input("Cl (mg/L)", value=150.0, step=10.0)
                val_so4 = st.number_input("SO4 (mg/L)", value=50.0, step=10.0)
                st.markdown(f"**pH:** {in_ph} (상단 설정값)")

            st.markdown("---")
            with st.expander("➕ 상세 이온 입력 (Ba, Sr, F, Fe 등)", expanded=False):
                ac1, ac2 = st.columns(2)
                with ac1:
                    val_mg = st.number_input("Mg (mg/L)", value=0.0, step=1.0, help="0이면 자동 계산")
                    val_na_meas = st.number_input("Na (mg/L)", value=0.0, step=1.0, help="0이면 자동 계산")
                    val_fe = st.number_input("Fe (mg/L)", value=0.1, step=0.1)
                    # [NEW]
                    val_ba = st.number_input("Ba (mg/L)", value=0.0, step=0.01)
                    val_f = st.number_input("F (불소, mg/L)", value=0.0, step=0.1)
                with ac2:
                    val_k  = st.number_input("K (mg/L)", value=5.0, step=1.0)
                    val_nh4 = st.number_input("NH4 (mg/L)", value=0.0, step=0.1)
                    val_no3 = st.number_input("NO3 (mg/L)", value=0.0, step=1.0)
                    # [NEW]
                    val_sr = st.number_input("Sr (mg/L)", value=0.0, step=0.1)

            # [4] 자동 밸런싱 로직
            meq_ca = val_ca / 20.04
            meq_mg_in = val_mg / 12.15
            meq_na_in = val_na_meas / 22.99
            meq_alk = val_alk / 50.0
            meq_cl = val_cl / 35.45
            meq_so4 = val_so4 / 48.03
            meq_fe = val_fe / 27.92
            meq_al = val_al / 8.99
            meq_k = val_k / 39.10
            meq_nh4 = val_nh4 / 18.04
            meq_no3 = val_no3 / 62.00
            # 미량 원소는 밸런스에 큰 영향 없으므로 생략 가능하나 정밀도를 위해 포함 가능
            
            sum_cat_meas = meq_ca + meq_mg_in + meq_na_in + meq_fe + meq_al + meq_k + meq_nh4
            sum_an_meas = meq_alk + meq_cl + meq_so4 + meq_no3
            balance_gap = sum_an_meas - sum_cat_meas
            
            final_mg = val_mg
            final_na = val_na_meas
            final_nh4 = val_nh4
            final_no3 = val_no3
            final_no2 = 0.0
            
            if balance_gap > 0.001: 
                add_meq = balance_gap
                if val_mg == 0:
                    est_mg_meq = meq_ca * 0.4 
                    if est_mg_meq > add_meq: est_mg_meq = add_meq * 0.5
                    final_mg = est_mg_meq * 12.15
                    rem_meq = add_meq - est_mg_meq
                else:
                    rem_meq = add_meq

                if val_na_meas == 0:
                    final_na = rem_meq * 22.99
                else:
                    final_na = val_na_meas + (rem_meq * 22.99)
                bal_msg = f"✅ **Auto-Fill:** 부족한 양이온을 **Mg/Na**로 자동 보정함"

            elif balance_gap < -0.001:
                gap_abs = abs(balance_gap)
                if val_no3 == 0:
                    final_no3 = gap_abs * 62.00
                    bal_msg = f"✅ **Auto-Fill:** 부족한 음이온을 **NO3**로 자동 보정함"
                else:
                    bal_msg = "✅ **Check:** 음이온 부족 (NO3 입력값 유지)"
            else:
                bal_msg = "✅ **Perfect Balance:** 보정 없음"
            
            st.info(bal_msg)

        # [5] 최종 결과 및 변수 패키징
        with col_result:
            st.markdown("###### 📊 최종 수질 분석 결과")
            v_main = {
                'Ca': val_ca, 'Mg': final_mg, 'Na': final_na, 'K': val_k, 'NH4': final_nh4,
                'HCO3': val_alk * 1.22, 
                'Cl': val_cl, 'SO4': val_so4, 'NO3': final_no3, 'NO2': final_no2,
                'SiO2': val_sio2, 'Fe': val_fe, 'Al': val_al, 'pH': in_ph,
                # [NEW] 3단계 추가 항목
                'Ba': val_ba, 'Sr': val_sr, 'F': val_f
            }
            
            cf_final = 1 / (1 - (in_rec / 100))
            feed_tds = sum([v for k,v in v_main.items() if k != 'pH'])
            brine_tds_final = feed_tds * cf_final
            brine_ph_final = in_ph + (math.log10(cf_final) * 0.7)

            m1, m2 = st.columns(2)
            m1.metric("원수 TDS (합계)", f"{feed_tds:.0f} mg/L")
            m2.metric("농축수 TDS", f"{brine_tds_final:.0f} mg/L", f"x{cf_final:.1f}배")

            res_data = []
            # 표시할 항목에 특수 이온 추가
            disp_ions = ['Ca', 'Mg', 'Na', 'K', 'NH4', 'HCO3', 'Cl', 'SO4', 'NO3', 'SiO2', 'Fe', 'Al', 'Ba', 'Sr', 'F']
            
            c_mg = locals().get('val_mg', 0)
            c_na = locals().get('val_na_meas', 0)
            c_no3 = locals().get('val_no3', 0)

            for ion in disp_ions:
                f_val = v_main.get(ion, 0.0)
                b_val = f_val * cf_final
                note = ""
                
                if ion == 'Mg' and c_mg == 0 and f_val > 0: note = "⚡ (Auto)"
                if ion == 'Na' and c_na == 0 and f_val > 0: note = "⚡ (Auto)"
                if ion == 'NO3' and c_no3 == 0 and f_val > 0: note = "⚡ (Auto)"
                
                res_data.append({"이온": ion, "원수 (Feed)": f"{f_val:.1f} {note}", "농축수 (Brine)": f"{b_val:.1f}"})
            
            st.dataframe(pd.DataFrame(res_data), hide_index=True, use_container_width=True, height=500)
            
            st.markdown("---")
            p_targets = ['Ca', 'SO4', 'SiO2']
            limits = {'Ca': 600, 'SO4': 1500, 'SiO2': 150}
            comp_data = []
            for t in p_targets:
                val = v_main.get(t, 0.0) * cf_final
                state = "🚨 위험" if val > limits[t] else "✅ 양호"
                comp_data.append({'항목': t, '농축농도': f"{val:.1f}", '진단': state})
            st.table(pd.DataFrame(comp_data))
# ==========================================================================
    # [Tab 2] 🔮 성능 열화 및 부하 진단 (Hybrid Ver)
    # ==========================================================================
    with tab2:
        st.subheader("Step 2. 멤브레인 부하 진단 및 수명 예측")
        st.info("💡 **Flux(부하)**와 **수온**을 분석하여 막이 현재 '무리하게 운전되고 있는지' 진단하고, 미래 수명을 예측합니다.")

        # ----------------------------------------------------------------------
        # [Section 1] 현재 운전 부하 진단 (기존 코드 유지)
        # ----------------------------------------------------------------------
        with st.container(border=True):
            st.markdown("#### 1️⃣ 현재 막 부하(Flux) 및 운전 상태 진단")
            
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                curr_perm_flow = in_flow 
                curr_rec = in_rec
                curr_feed_flow = curr_perm_flow / (curr_rec / 100.0) if curr_rec > 0 else 0
                st.metric("현재 공급 유량", f"{curr_feed_flow:.1f} m³/hr", f"회수율 {curr_rec}%")
            
            with col_d2:
                st.markdown("**⚙️ 막(Membrane) 구성**")
                n_vessel = st.number_input("베셀 수량 (Vessels)", value=5, step=1, key="t2_ves")
                n_ele = st.number_input("베셀당 엘리먼트 (Elements)", value=6, step=1, key="t2_ele")
                area_per_ele = 400.0 
            
            with col_d3:
                op_press = st.number_input("현재 운전 압력 (bar)", value=12.0, step=0.1, key="t2_press")
                op_temp = in_temp 

            # 진단 계산
            total_area = n_vessel * n_ele * area_per_ele
            gpd = curr_perm_flow * 264.172 * 24 
            flux_gfd = gpd / total_area if total_area > 0 else 0.0
            
            # 온도 보정 압력 (ASTM D4516)
            tcf = math.exp(2700 * (1/(273 + op_temp) - 1/(273 + 25)))
            norm_press = op_press * tcf

            st.divider()

            c_res1, c_res2 = st.columns(2)            
            # ① Flux 진단
            with c_res1:
                st.metric("평균 플럭스 (Average Flux)", f"{flux_gfd:.1f} GFD")
                if flux_gfd > 18.0:
                    st.error("⛔ **과부하 (High Flux):** 설계 기준 초과! 막 오염이 매우 빠르게 진행됩니다.")
                elif flux_gfd > 15.0:
                    st.warning("⚠️ **주의 (Medium):** 다소 높은 부하입니다. 전처리가 완벽해야 합니다.")
                else:
                    st.success("✅ **안정 (Conservative):** 오염에 강한 안정적인 설계입니다.")

            # ② 온도 보정 압력 진단
            with c_res2:
                st.metric("온도 보정 압력 (at 25℃)", f"{norm_press:.1f} bar", f"실측 {op_press} bar")
                if norm_press > 15.0:
                    st.error("⛔ **막힘 의심 (Fouling):** 수온 영향을 제외해도 압력이 높습니다. 스케일/오염이 진행 중입니다.")
                else:
                    st.success("✅ **정상 (Normal):** 현재 압력은 수온 영향이거나 정상 범위입니다.")

        # ----------------------------------------------------------------------
        # [Section 1.5] 엔지니어링 정밀 진단 (★ 엑셀 엔진 이식 - 1단계 업그레이드 ★)
        # ----------------------------------------------------------------------
        st.divider()
        st.markdown("#### 🔬 엔지니어링 정밀 진단 (Physics Engine Applied)")
        st.info("💡 엑셀의 **Van't Hoff 법칙**을 적용하여, 수온과 이온 농도에 따른 **'진짜 삼투압'**과 **'NDP'**를 계산합니다.")

        # [1] 데이터 준비 (Tab 1에서 넘어온 데이터 활용)
        if 'v_main' not in locals():
            # Tab 1이 아직 안 돌았을 경우를 대비한 가상 데이터
            v_main_safe = {}
            st.warning("⚠️ 수질 데이터가 로드되지 않아 약식으로 계산합니다.")
        else:
            v_main_safe = v_main

        perm_press_input = st.number_input("처리수 배압 (Back Pressure, bar)", value=0.0, step=0.1, key="eng_pp_upgrade")

        # [2] 정밀 삼투압 계산 (엑셀 로직: Sum(Molarity) * R * T)
        temp_k = op_temp + 273.15 # 절대온도
        r_constant = 0.08206      # 기체상수
        
        # 분자량 DB
        mw_db = {
            'Ca': 40.08, 'Mg': 24.305, 'Na': 22.99, 'K': 39.10, 'NH4': 18.04,
            'HCO3': 61.02, 'Cl': 35.45, 'SO4': 96.06, 'NO3': 62.00, 'NO2': 46.01,
            'SiO2': 60.08, 'Fe': 55.85, 'Al': 26.98
        }

        # (A) 원수 몰농도 합계
        feed_molarity_sum = 0.0
        if v_main_safe:
            for ion, conc_mg_l in v_main_safe.items():
                if ion in mw_db:
                    molarity = (conc_mg_l / 1000.0) / mw_db[ion]
                    feed_molarity_sum += molarity
        else:
            # 데이터 없으면 TDS/50000 정도로 대충 추정
            feed_molarity_sum = (in_flow * 0) + 0.01 

        # (B) 농축수 및 평균 몰농도
        # cf_final은 Tab 1에서 계산됨. 없으면 여기서 계산
        if 'cf_final' not in locals(): cf_final = 1.0 / (1.0 - (curr_rec / 100.0)) if curr_rec < 100 else 1.0
        
        brine_molarity_sum = feed_molarity_sum * cf_final
        avg_bulk_molarity = (feed_molarity_sum + brine_molarity_sum) / 2.0
        
        # (C) 농도 분극 계수 (Beta)
        eng_beta = math.exp(0.7 * (curr_rec / 100.0))
        
        # (D) 표면 삼투압 (Surface Osmotic Pressure)
        surface_molarity = avg_bulk_molarity * eng_beta
        osmotic_atm = surface_molarity * r_constant * temp_k
        osmotic_bar = osmotic_atm * 1.01325 # bar 변환
        
        # (E) NDP 계산
        eng_p_loss = 2.0 
        eng_ndp = op_press - osmotic_bar - eng_p_loss - perm_press_input

        # [3] 진단 결과 시각화
        k1, k2, k3 = st.columns(3)
        
        # 삼투압 표시
        k1.metric("막 표면 삼투압", f"{osmotic_bar:.1f} bar", help=f"Van't Hoff 식으로 계산된 정밀 삼투압 (수온 {op_temp}도 반영)")
        
        # CP 계수 표시
        k2.metric("농도 분극 계수 (Beta)", f"{eng_beta:.2f}", help="1.2 이상이면 스케일 위험 급증")
        
        # NDP 표시
        ndp_state = "normal"
        if eng_ndp < 3.0: ndp_state = "inverse"
        k3.metric("유효 구동 압력 (NDP)", f"{eng_ndp:.1f} bar", delta_color=ndp_state, help="실제 물을 생산하는 힘 (운전압 - 삼투압 - 손실)")

        # 종합 코멘트
        if eng_beta > 1.2:
            st.warning(f"⚠️ **농도 분극 심화 ({eng_beta:.2f}):** 회수율이 높아 막 표면 농도가 위험 수준입니다.")
        
        if eng_ndp < 5.0:
            st.error(f"🚨 **NDP 부족 ({eng_ndp:.1f} bar):** 삼투압({osmotic_bar:.1f} bar)이 너무 높아 생산 효율이 떨어집니다.")
        elif eng_ndp > 15.0:
            st.warning(f"⚠️ **과도한 NDP ({eng_ndp:.1f} bar):** 막 압밀(Compaction) 우려가 있습니다.")
        else:
            st.success(f"✅ **NDP 양호:** 에너지 효율이 최적 상태입니다.")

        # ----------------------------------------------------------------------
        # [Section 2] 미래 성능 예측 (기존 코드 100% 유지)
        # ----------------------------------------------------------------------
        st.divider()
        st.markdown("#### 2️⃣ 장기 성능 열화 시뮬레이션 (Prediction)")
        with st.expander("💡 수원별 권장 연간 변화율 가이드 (Reference)", expanded=False):
            st.markdown("""
            | 수원 종류 (Source) | 연간 유량 감소율 (Flux Decline) | 연간 염투과 증가율 (Salt Passage) |
            | :--- | :---: | :---: |
            | **지하수 (Well Water)** | 2 ~ 3 % | 3 ~ 5 % |
            | **지표수 (Surface Water)** | 5 ~ 7 % | 10 ~ 12 % |
            | **폐수 재이용 (Wastewater)** | 10 ~ 15 % | 15 ~ 20 % |
            """)
        
        c_t2_1, c_t2_2 = st.columns(2)
        with c_t2_1: a_rate_s = st.slider("📉 연간 유량 감소율 (%)", 0.0, 20.0, 5.0, key="a_s")
        with c_t2_2: b_rate_s = st.slider("📈 연간 염투과 증가율 (%)", 0.0, 30.0, 10.0, key="b_s")
        
        op_y = st.slider("📅 운전 기간 시뮬레이션 (년)", 0.0, 10.0, 3.0, 0.5, key="y_s")
        
        # 시뮬레이션 계산
        if 'brine_tds_final' not in locals(): brine_tds_final = 1000 # 안전장치
        if 'cf_final' not in locals(): cf_final = 1.0 # 안전장치

        base_cond = brine_tds_final / cf_final / 0.65 # TDS 역산 추정
        
        a_f = (1 - (a_rate_s / 100)) ** op_y
        b_f = (1 + (b_rate_s / 100)) ** op_y
        
        p_f_res = curr_perm_flow * a_f
        p_c_res = base_cond * b_f

        # 결과 그래프
        y_ax = np.linspace(0, 10, 21)
        f_cv = [curr_perm_flow * ((1 - (a_rate_s / 100)) ** y) for y in y_ax]
        c_cv = [base_cond * ((1 + (b_rate_s / 100)) ** y) for y in y_ax]
        
        g1, g2 = st.columns(2)
        with g1:
            fig_f = go.Figure()
            fig_f.add_trace(go.Scatter(x=y_ax, y=f_cv, line=dict(color='#3498DB', width=3), name='Flow'))
            fig_f.add_trace(go.Scatter(x=[op_y], y=[p_f_res], mode='markers+text', text=[f"{p_f_res:.1f}"], textposition="top right", marker=dict(color='red', size=12)))
            fig_f.update_layout(title="생산 유량 감소 예측 (Flow Decline)", xaxis_title="년 (Year)", yaxis_title="유량 (m3/h)", height=300, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_f, use_container_width=True)
            st.caption(f"🔻 {op_y}년 후 예상 유량: **{p_f_res:.1f} m³/h** ({-(1-a_f)*100:.1f}% 감소)")
            
        with g2:
            fig_c = go.Figure()
            fig_c.add_trace(go.Scatter(x=y_ax, y=c_cv, line=dict(color='#E74C3C', width=3), name='Salt Passage'))
            fig_c.add_trace(go.Scatter(x=[op_y], y=[p_c_res], mode='markers+text', text=[f"{p_c_res:.1f}"], textposition="top right", marker=dict(color='black', size=12)))
            fig_c.update_layout(title="전도도 상승 예측 (Salt Passage)", xaxis_title="년 (Year)", yaxis_title="전도도 (μS/cm)", height=300, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_c, use_container_width=True)
            st.caption(f"🔺 {op_y}년 후 예상 전도도: **{p_c_res:.1f} μS/cm** ({+(b_f-1)*100:.1f}% 증가)")

# ==========================================================================
    # [Tab 3] 🚨 스케일 정밀 진단 (Step 3 Complete: 특수 스케일 확장)
    # ==========================================================================
    with tab3:
        st.subheader("Step 3. 스케일 및 오염 정밀 진단 (Full Chemistry)")
        st.info("💡 **[3단계 완료]** 엑셀 파일의 모든 진단 항목(BaSO4, SrSO4, CaF2)을 포함한 **종합 진단 시스템**이 완성되었습니다.")

        # [1] 데이터 로드
        if 'v_main' not in locals(): v_main = {}
        if 'brine_ph_final' not in locals(): 
            cf_temp = 1.0 / (1 - (in_rec/100)) if in_rec < 100 else 1.0
            brine_ph_final = in_ph + (math.log10(cf_temp) * 0.7)
            cf_final = cf_temp
        if 'brine_tds_final' not in locals(): brine_tds_final = 1000.0

        st.info(f"💡 진단 기준: 농축수 pH **{brine_ph_final:.2f}**, TDS **{brine_tds_final:.0f} ppm** (CF: {cf_final:.1f}배)")

        # ----------------------------------------------------------------------
        # [2] 종합 스케일 계산 엔진 (Full Engine)
        # ----------------------------------------------------------------------
        
        # (A) 기초 데이터 준비
        ca_val = v_main.get('Ca', 0.0)
        so4_val = v_main.get('SO4', 0.0)
        sio2_val = v_main.get('SiO2', 0.0)
        fe_val = v_main.get('Fe', 0.0)
        al_val = v_main.get('Al', 0.0)
        alk_val = v_main.get('HCO3', 0.0)
        # [NEW] 3단계 추가 변수
        ba_val = v_main.get('Ba', 0.0)
        sr_val = v_main.get('Sr', 0.0)
        f_val = v_main.get('F', 0.0)

        # 농축수 농도 변환
        b_ca = ca_val * cf_final
        b_so4 = so4_val * cf_final
        b_sio2 = sio2_val * cf_final
        b_alk = alk_val * cf_final
        b_ba = ba_val * cf_final
        b_sr = sr_val * cf_final
        b_f = f_val * cf_final
        b_tds = brine_tds_final
        t_k = in_temp + 273.15 

        # (B) 1단계: LSI (CaCO3)
        f_a = (math.log10(b_tds) - 1) / 10.0 if b_tds > 10 else 0
        f_b = -13.12 * math.log10(t_k) + 34.55
        f_c = math.log10(b_ca * 2.5) - 0.4 if b_ca > 1 else 0
        f_d = math.log10(b_alk * 0.82) if b_alk > 1 else 0
        ph_s = (9.3 + f_a + f_b) - (f_c + f_d)
        lsi_val = brine_ph_final - ph_s

        # (C) 2단계: CaSO4 (석고)
        mol_ca = (b_ca / 40.08) / 1000.0
        mol_so4 = (b_so4 / 96.06) / 1000.0
        ip_caso4 = mol_ca * mol_so4
        ksp_caso4 = 3.14e-5 * (1 + 0.005 * (in_temp - 25)) 
        caso4_sat = math.sqrt(ip_caso4 / ksp_caso4) * 100.0 if ksp_caso4 > 0 else 0

        # (D) 3단계: SiO2 (실리카)
        base_sol = 120.0 
        temp_corr_sol = base_sol * (1 + 0.02 * (in_temp - 25))
        final_sio2_limit = temp_corr_sol * (1 + 10**(brine_ph_final - 9.8)) if brine_ph_final > 8.0 else temp_corr_sol
        sio2_sat = (b_sio2 / final_sio2_limit) * 100.0

        # (E) [NEW] 4단계: BaSO4 (Barite) - 매우 난용성
        # Ksp ~ 1.1e-10 (25도)
        mol_ba = (b_ba / 137.33) / 1000.0
        ip_baso4 = mol_ba * mol_so4
        ksp_baso4 = 1.1e-10 # 바륨은 온도 영향이 적음
        baso4_sat = math.sqrt(ip_baso4 / ksp_baso4) * 100.0 if ksp_baso4 > 0 else 0

        # (F) [NEW] 5단계: SrSO4 (Celestite)
        # Ksp ~ 3.2e-7 (25도)
        mol_sr = (b_sr / 87.62) / 1000.0
        ip_srso4 = mol_sr * mol_so4
        ksp_srso4 = 3.2e-7 
        srso4_sat = math.sqrt(ip_srso4 / ksp_srso4) * 100.0 if ksp_srso4 > 0 else 0

        # (G) [NEW] 6단계: CaF2 (Fluorite)
        # Ksp ~ 3.45e-11 (25도)
        mol_f = (b_f / 19.00) / 1000.0
        ip_caf2 = mol_ca * (mol_f ** 2)
        ksp_caf2 = 3.45e-11
        # CaF2는 이온이 3개(Ca, F, F)이므로 3제곱근 사용이 정확하나, 엑셀은 2제곱근 스케일 사용
        caf2_sat = (ip_caf2 / ksp_caf2)**0.33 * 100.0 if ksp_caf2 > 0 else 0

        # ----------------------------------------------------------------------
        # [3] 결과 시각화
        # ----------------------------------------------------------------------
        
        # 그래프 데이터 구성 (LSI는 % 스케일링)
        sc_items = ['CaCO3(LSI)', 'CaSO4', 'SiO2', 'BaSO4', 'SrSO4', 'CaF2']
        pots = [lsi_val * 50.0, caso4_sat, sio2_sat, baso4_sat, srso4_sat, caf2_sat]
        
        fig_risk = px.bar(x=sc_items, y=pots, color=sc_items, title="Mineral Saturation Levels (%) - Full Spectrum", text_auto='.1f')
        fig_risk.add_hline(y=100, line_dash="dot", line_color="red", annotation_text="Limit")
        st.plotly_chart(fig_risk, use_container_width=True)
        
        c_diag1, c_diag2 = st.columns(2)
        
        # 1. 무기물 스케일 종합 진단
        with c_diag1:
            st.markdown("##### ⚠️ 스케일 종합 진단")
            
            # LSI
            if lsi_val > 2.0: st.error(f"🔴 **CaCO3 (LSI): {lsi_val:.2f}** - 산 주입 필수")
            elif lsi_val > 1.0: st.warning(f"🔸 **CaCO3 (LSI): {lsi_val:.2f}** - 스케일 방지제 필요")
            else: st.success(f"🟢 **CaCO3 (LSI): {lsi_val:.2f}** - 안전")

            # 나머지 항목 일괄 진단
            check_list = [
                ('CaSO4', caso4_sat), ('SiO2', sio2_sat), 
                ('BaSO4', baso4_sat), ('SrSO4', srso4_sat), ('CaF2', caf2_sat)
            ]
            
            for name, pot in check_list:
                if pot > 100: 
                    st.error(f"🔴 **{name}: {pot:.0f}% (위험)** - 한계치 초과")
                elif pot > 80:
                    st.warning(f"🔸 {name}: {pot:.0f}% (경고) - 여유 없음")
                # 안전한 항목은 너무 길어지니 생략하거나 필요시 추가

        # 2. 금속 오염 진단
        with c_diag2:
            st.markdown("##### 🔩 금속 오염 진단")
            fe_conc = fe_val * cf_final
            al_conc = al_val * cf_final 
            
            if fe_conc > 0.3: st.warning(f"🔸 **Fe: {fe_conc:.2f} ppm** (기준>0.3) - 산화철 주의")
            else: st.info(f"🔹 Fe: {fe_conc:.2f} ppm (안정)")
                
            if al_conc > 0.05: st.warning(f"🔸 **Al: {al_conc:.2f} ppm** (기준>0.05) - 알루미늄계 스케일")
            else: st.info(f"🔹 Al: {al_conc:.2f} ppm (안정)")
# ==========================================================================
    # [Tab 4] 💊 약품 선정 및 주입량 시뮬레이션 (Excel Linked)
    # ==========================================================================
    with tab4:
        st.subheader("2️⃣ 약품 선정 및 주입량 시뮬레이션")

        # [1] 데이터 준비
        if 'v_main' not in locals(): v_main = {}
        lsi_safe = max(0.0, locals().get('lsi_val', 0.0))
        
        raw_vals = {
            'CaCO3': lsi_safe * 50.0,
            'CaSO4': locals().get('caso4_sat', 0.0),
            'SiO2':  locals().get('sio2_sat', 0.0),
            'BaSO4': locals().get('baso4_sat', 0.0),
            'SrSO4': locals().get('srso4_sat', 0.0),
            'CaF2':  locals().get('caf2_sat', 0.0)
        }

        # [2] 약품 선택 UI
        ro_chem_list = PRODUCT_CATALOG['RO']['Antiscalant']
        
        col_sel1, col_sel2 = st.columns([1.5, 1])
        with col_sel1:
            chem_names = [item['Name'] for item in ro_chem_list]
            sel_chem_name = st.selectbox("🔴 적용할 약품 (Product)", chem_names)
            sel_chem_info = next(item for item in ro_chem_list if item['Name'] == sel_chem_name)
            
            with st.container(border=True):
                st.markdown(f"**🧪 주성분:** :red[{sel_chem_info.get('Main_Ingredient', '-')}]")
                st.markdown(f"**💡 특징:** :blue[{sel_chem_info.get('Sales_Point', '-')}]")
                if sel_chem_info.get('Field_Tip') != '-':
                    st.markdown(f"**🔧 Tip:** :green[{sel_chem_info.get('Field_Tip')}]")

        with col_sel2:
            std_dose = float(sel_chem_info.get('Dosage', 3.0)) 
            if std_dose == 0: std_dose = 3.0
            
            input_dose = st.slider("주입량 (ppm)", 0.0, 20.0, std_dose, 0.5)
            
            dose_eff = min(input_dose / std_dose, 1.2)
            if dose_eff < 1.0: st.warning(f"⚠️ 권장량({std_dose}ppm) 부족")
            else: st.success(f"✅ 충분한 주입량")

        st.divider()

        # [3] 시뮬레이션 엔진 (엑셀 데이터 기반 Risk Index 계산)
        treated_vals = {}
        
        for item, val in raw_vals.items():
            # 1. 엑셀 값 읽기 (스마트 파싱된 값)
            max_limit = sel_chem_info.get(f'Max_{item}', 0.0)
            
            # 2. 값 없으면 백업 로직 (타겟 이름 추정)
            if max_limit == 0:
                target_str = str(sel_chem_info.get('Target', '')).upper()
                if item == 'CaCO3' and ('SCALE' in target_str or 'CACO3' in target_str): max_limit = 250
                elif item == 'CaSO4' and ('SULFATE' in target_str or 'CASO4' in target_str): max_limit = 300
                elif item == 'SiO2' and ('SILICA' in target_str or 'SIO2' in target_str): max_limit = 200
                elif item == 'BaSO4' and ('SULFATE' in target_str or 'BASO4' in target_str): max_limit = 800
                elif item == 'SrSO4' and ('SULFATE' in target_str or 'SRSO4' in target_str): max_limit = 400
                elif item == 'CaF2' and ('SCALE' in target_str or 'CAF2' in target_str): max_limit = 150
                else: max_limit = 110 

            # 3. 실제 방어 한계 계산 (주입량 효율 반영)
            real_limit = 100 + (max_limit - 100) * dose_eff
            
            # 4. 위험도 계산
            risk_index = (val / real_limit * 100) if real_limit > 0 else val
            treated_vals[item] = risk_index

        # [4] 결과 그래프 (스마트 Y축)
        st.subheader(f"📊 위험도 분석 결과: {sel_chem_name} 적용 시")
        
        df_chart = pd.DataFrame({
            "Ion": list(raw_vals.keys()),
            "Raw Risk": list(raw_vals.values()),      
            "Treated Risk": list(treated_vals.values()) 
        })

        max_val = max(max(raw_vals.values()), max(treated_vals.values()))
        y_limit = max(120, max_val * 1.1)

        col_g1, col_arr, col_g2 = st.columns([4, 0.5, 4])
        
        with col_g1:
            st.markdown("**🔴 무처리 위험도 (Raw Risk)**")
            fig1 = px.bar(df_chart, x="Ion", y="Raw Risk", text_auto='.0f', color_discrete_sequence=['#FF4B4B'])
            fig1.add_hline(y=100, line_dash="dot", line_color="black")
            fig1.update_yaxes(range=[0, y_limit])
            st.plotly_chart(fig1, use_container_width=True)
        
        with col_arr:
             st.markdown("<br><br><br><br><div style='text-align:center; font-size:30px;'>👉</div>", unsafe_allow_html=True)
        
        with col_g2:
            st.markdown(f"**🔵 약품 처리 후 위험도 (Risk Index)**")
            fig2 = px.bar(df_chart, x="Ion", y="Treated Risk", text_auto='.0f', color_discrete_sequence=['#2E86C1'])
            fig2.add_hline(y=100, line_dash="dot", line_color="red")
            fig2.update_yaxes(range=[0, y_limit])
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.markdown("##### 📝 상태 판정")
        cols = st.columns(6)
        for i, (k, v) in enumerate(treated_vals.items()):
            with cols[i]:
                state = "🚨 위험" if v > 100 else "✅ 안전"
                st.metric(k, f"{v:.0f}%", state)
# ==========================================================================
    # [Tab 5] 🛠️ RO 현장 진단 & CIP 통합 솔루션 (Diagnosis, Prediction, Action)
    # ==========================================================================
    with tab5:
        st.subheader("🛠️ RO 유지관리 통합 센터 (O&M One-Stop Center)")
        st.info("💡 **[1.진단]** 현재 상태 확인 → **[2.예측]** 세정 시기 결정 → **[3.조치]** 약품/탱크 계산을 한 번에 수행합니다.")

        # ----------------------------------------------------------------------
        # [Step 1] 현장 운전 데이터 정밀 진단 (Normalization) - 기존 유지
        # ----------------------------------------------------------------------
        st.markdown("#### 1️⃣ 현장 운전 데이터 진단 (Normalization)")
        
        # 1. 초기 기준값 (Baseline)
        with st.expander("⚙️ 시스템 설정 및 초기 기준값 (Commissioning Data) - 클릭하여 설정", expanded=False):
            c_conf1, c_conf2 = st.columns(2)
            with c_conf1:
                mem_model = st.selectbox("멤브레인 모델", ["CSM RE8040-BE", "LG BW 400 R", "DOW BW30-400"], key="ro_model_sel")
                
                # 멤브레인 스펙 DB
                mem_specs = {
                    "CSM RE8040-BE": {"area": 400, "flow": 10500}, 
                    "LG BW 400 R": {"area": 400, "flow": 10500},
                    "DOW BW30-400": {"area": 400, "flow": 10500},
                }
                curr_spec = mem_specs[mem_model]
                
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
            dp1_curr = p_feed - p_inter
            dp2_curr = p_inter - p_conc
            st.caption(f"Calculated DP: 1단 {dp1_curr:.1f} / 2단 {dp2_curr:.1f} bar")
        with col_f4:
            cond_p1 = st.number_input("1단 전도도 (µS/cm)", value=15.0, step=1.0, key="c_p1")
            cond_p2 = st.number_input("2단 전도도 (µS/cm)", value=40.0, step=1.0, key="c_p2")

        # 3. 진단 버튼 및 계산 로직
        if st.button("🚀 현장 진단 실행 (Analyze)", type="primary", use_container_width=True):
            
            # --- [Algorithm] 정규화 및 진단 로직 ---
            if f_temp < 1: f_temp = 1
            tcf = math.exp(0.03 * (25 - f_temp))
            flow_corr = (base_flow / f_flow) ** 1.5 if f_flow > 0 else 1.0
            
            norm_dp1 = dp1_curr * tcf * flow_corr
            norm_dp2 = dp2_curr * tcf * flow_corr
            
            rise_dp1 = ((norm_dp1 - base_dp1) / base_dp1) * 100
            rise_dp2 = ((norm_dp2 - base_dp2) / base_dp2) * 100
            
            # --- [Result] 결과 리포트 출력 ---
            st.divider()
            st.subheader("📊 진단 결과 리포트")
            
            col_res1, col_res2 = st.columns(2)
            
            with col_res1:
                st.markdown("##### [1단] 전처리/미생물 오염 진단")
                st.metric("1단 정규화 차압", f"{norm_dp1:.2f} bar", f"{rise_dp1:+.1f}% (변동률)", 
                          delta_color="inverse" if rise_dp1 > 10 else "normal")
                
                if rise_dp1 >= 15.0:
                    st.error("🚨 **[CRITICAL] 차압 15% 이상 상승!**")
                    st.markdown("- **처방:** **알칼리 세정(Alkaline CIP, pH 11)** 즉시 수행 필요")
                elif rise_dp1 >= 10.0:
                    st.warning("⚠️ **[WARNING] 차압 상승 추세**")
                else:
                    st.success("✅ **[NORMAL] 상태 양호**")
            
            with col_res2:
                st.markdown("##### [2단] 스케일 오염 진단")
                st.metric("2단 정규화 차압", f"{norm_dp2:.2f} bar", f"{rise_dp2:+.1f}% (변동률)",
                          delta_color="inverse" if rise_dp2 > 10 else "normal")
                
                if rise_dp2 >= 15.0:
                    st.error("🚨 **[CRITICAL] 차압 15% 이상 상승!**")
                    st.markdown("- **처방:** **산성 세정(Acid CIP, pH 2~3)** 즉시 수행 필요")
                elif rise_dp2 >= 10.0:
                    st.warning("⚠️ **[WARNING] 스케일 생성 초기**")
                else:
                    st.success("✅ **[NORMAL] 상태 양호**")

            st.markdown("---")
            st.markdown("##### 🧪 수질/전도도 추가 분석")
            if cond_p2 > (cond_p1 * 4):
                st.warning(f"⚠️ **2단 전도도({cond_p2})가 매우 높습니다.** 농축 배수가 한계에 도달했습니다.")
            else:
                st.info(f"ℹ️ 생산수 수질 상태: 1단 {cond_p1}, 2단 {cond_p2} µS/cm (양호)")

            if f_temp < 15.0:
                st.caption(f"❄️ **참고:** 현재 수온({f_temp}°C)이 낮아 실제 압력은 높지만, 정규화(Normalization) 완료됨.")
        
        st.divider()

        # ======================================================================
        # [Step 2] 🤖 AI CIP 주기 예측 (New! 부장님 지시사항 삽입)
        # ======================================================================
        st.markdown("#### 2️⃣ 🤖 AI CIP 주기 예측 (Next Cleaning Prediction)")
        
        # [Layout] 좌측: 입력 / 우측: 결과
        col_pred1, col_pred2 = st.columns([1, 2])
        
        with col_pred1:
            st.markdown("**📅 예측 기준 데이터 (Baseline)**")
            last_cip_date = st.date_input("마지막 세정일 (Last CIP)", value=pd.to_datetime("2024-01-01"))
            
            # 기준 유량은 위 Section 1에서 입력한 base_flow를 그대로 사용 (중복입력 방지)
            st.caption(f"🔹 기준(초기) 유량: **{base_flow} m³/hr**")
            st.caption(f"🔹 현재(실측) 유량: **{f_flow} m³/hr**")
            
            limit_decline = st.slider("관리 한계선 (Limit %)", 5, 20, 15, help="성능이 몇 % 떨어지면 세정할까요?")

        with col_pred2:
            # 예측 로직 (Linear Regression Logic)
            from datetime import date, timedelta
            
            days_elapsed = (date.today() - last_cip_date).days
            if days_elapsed < 1: days_elapsed = 1
            
            # 유량 감소율 계산
            current_decline_pct = ((base_flow - f_flow) / base_flow) * 100
            
            # 일일 감소율
            daily_decline_rate = current_decline_pct / days_elapsed
            
            # 잔여 수명 계산
            remaining_pct = limit_decline - current_decline_pct
            
            if daily_decline_rate > 0:
                days_remaining = remaining_pct / daily_decline_rate
                predicted_date = date.today() + timedelta(days=int(days_remaining))
            else:
                days_remaining = 999 
                predicted_date = date.today()
            
            # 결과 리포트
            r1, r2, r3 = st.columns(3)
            r1.metric("현재 성능 저하율", f"{current_decline_pct:.1f} %", f"경과 {days_elapsed}일")
            
            if current_decline_pct >= limit_decline:
                r2.metric("CIP 권장 상태", "즉시 수행", delta_color="inverse")
                r3.error("🚨 **CIP 시점 도달!**\n효율이 관리 기준 이하입니다.")
            elif daily_decline_rate <= 0:
                 r2.metric("예상 D-Day", "계산 불가")
                 r3.info("✅ **매우 양호**\n성능 저하가 없습니다.")
            else:
                r2.metric("다음 세정 D-Day", f"D - {int(days_remaining)}일")
                r3.success(f"🗓️ **예상 세정일:**\n**{predicted_date.strftime('%Y년 %m월 %d일')}**")

        # [Graph] 오염 예측 곡선
        if daily_decline_rate > 0 and days_remaining < 999:
            x_past = [last_cip_date, date.today()]
            y_past = [0, current_decline_pct]
            x_future = [date.today(), predicted_date]
            y_future = [current_decline_pct, limit_decline]
            
            fig_cip = go.Figure()
            fig_cip.add_trace(go.Scatter(x=x_past, y=y_past, mode='lines+markers', name='현재 진행률', line=dict(color='blue')))
            fig_cip.add_trace(go.Scatter(x=x_future, y=y_future, mode='lines', name='예측 추세', line=dict(color='red', dash='dot')))
            fig_cip.add_hline(y=limit_decline, line_width=2, line_color="orange", annotation_text="관리 한계선")
            fig_cip.update_layout(title="📉 멤브레인 오염 예측 곡선 (Fouling Trend)", height=300, margin=dict(t=40, b=20))
            st.plotly_chart(fig_cip, use_container_width=True)
            

        st.divider()

# [Step 3] CIP 설비 엔지니어링 (베셀 수량 자유 입력 Ver)
        # ----------------------------------------------------------------------
        st.markdown("#### 3️⃣ CIP 설비 엔지니어링 (Equipment Sizing)")
        st.info("💡 **베셀 수량**을 현장에 맞게 입력하면, **탱크와 펌프 용량**이 자동 계산됩니다.")
        
        with st.container(border=True):
            c_eq1, c_eq2 = st.columns(2)
            
            with c_eq1:
                st.markdown("**⚙️ RO 시스템 배열 (Array) 설정**")
                
                # [핵심 수정] 1단 베셀 수량을 고정하지 않고 직접 입력받음 (기본값 6개로 변경)
                n_st1_input = st.number_input(
                    "1단 베셀 수량 (Stage 1 Vessels)", 
                    min_value=1, max_value=100, value=6, step=1, 
                    help="현장 1단에 설치된 베셀 개수를 입력하세요. (예: 6개)"
                )

                # [옵션] 설계 기준 선택
                cip_calc_base = st.radio(
                    "설계 기준 (Design Basis)",
                    ["1단 기준 (Stage 1 Only) - 표준", "전체 베셀 합산 (Total System)"],
                    help="보통 1단과 2단을 따로 세정하므로 '1단 기준'이 원칙이나, 동시에 한다면 '전체'를 선택하세요."
                )
                
                # 타겟 베셀 수량 산출
                if "전체" in cip_calc_base:
                    # 2단 수량 입력 (기본값은 1단의 절반인 3개로 세팅)
                    def_st2 = int(n_st1_input / 2)
                    n_st2_input = st.number_input("2단 베셀 수량 (Stage 2)", value=def_st2, min_value=0)
                    target_vessels = n_st1_input + n_st2_input
                    st.caption(f"📌 총 {target_vessels} 베셀 (1단+2단) 기준으로 펌프를 선정합니다.")
                else:
                    target_vessels = n_st1_input
                    st.caption(f"📌 1단 {target_vessels} 베셀 기준으로 펌프를 선정합니다.")

                st.markdown("---")
                cip_vessel_d = st.selectbox("베셀 구경 (Diameter)", ["8 inch", "4 inch", "16 inch"], index=0, key="cip_dia")
                
                # [이론 계산] 최소 필요 탱크 용량
                if "8 inch" in cip_vessel_d: unit_vol = 0.18 # 8인치 Element 6개 기준
                elif "4 inch" in cip_vessel_d: unit_vol = 0.04
                else: unit_vol = 0.70 
                
                # 최소 순환 볼륨 = (타겟 베셀 수 * 단위부피) * 1.5 (배관/여유율)
                calc_min_vol = (target_vessels * unit_vol) * 1.5
                if calc_min_vol < 1.0: calc_min_vol = 1.0 
                
                st.write(f"📏 권장 최소 용량: **{calc_min_vol:.1f} ㎥**")

            with c_eq2:
                st.markdown("**🛢️ CIP 탱크 용량 설정 (현장 값)**")
                
                # 사용자가 직접 입력
                cip_vol_real = st.number_input(
                    "실제 보유 탱크 용량 (㎥)", 
                    value=float(math.ceil(calc_min_vol)), 
                    step=0.5, 
                    format="%.1f",
                    key="cip_vol_user_input",
                    help="약품 희석을 위해 실제 물을 채우는 양"
                )
                
                if cip_vol_real < calc_min_vol * 0.8:
                    st.warning("⚠️ **주의:** 탱크가 너무 작아 공기가 찰 수 있습니다.")
                else:
                    st.success(f"✅ 설정된 세정액: **{cip_vol_real:.1f} 톤**")
                    
                # --------------------------------------------------------------
                # 펌프 및 히터 설계 (자동 계산)
                # --------------------------------------------------------------
                st.divider()
                st.markdown("**🔧 설비 사양 (Spec)**")

                # 유량 계산 (8인치 기준: 베셀당 10톤/hr)
                if "8 inch" in cip_vessel_d: flow_per_vessel = 10.0
                elif "4 inch" in cip_vessel_d: flow_per_vessel = 2.5
                else: flow_per_vessel = 40.0
                
                # 고유속 세정 시 20% 증량
                cip_mode = st.radio("유속 모드", ["표준 유속", "고유속 (High Flow)"], horizontal=True)
                if "High" in cip_mode: flow_per_vessel *= 1.2
                
                # [결과] 총 유량 = 베셀 개수 * 개당 유량
                total_cip_flow = target_vessels * flow_per_vessel
                
                # 히터 용량 (20도 승온)
                req_heat = (cip_vol_real * 1000 * 20) / 860
                
                c_spec1, c_spec2 = st.columns(2)
                c_spec1.metric("펌프 유량", f"{total_cip_flow:.1f} ㎥/hr")
                c_spec2.metric("히터 용량", f"{req_heat:.1f} kW")

        # [Step 4] 약품 배합비 (Recipe) - 실제 탱크 용량 연동
        # ----------------------------------------------------------------------
        st.markdown("#### 4️⃣ 약품 배합비 및 소요량 (Chemical Recipe)")
        
        tab_acid, tab_alk = st.tabs(["🔴 산성 세정 (Acid Cleaning)", "🔵 알칼리 세정 (Alkaline Cleaning)"])
        
        # (1) 산성 세정
        with tab_acid:
            st.info(f"🎯 **Target:** 금속 산화물, 탄산칼슘(Scale) 제거 | **물 {cip_vol_real}톤** 기준")
            
            # 약품 선택 로직 (카탈로그 연동)
            acid_db = PRODUCT_CATALOG.get('RO', {}).get('CIP_Acid', [])
            if acid_db:
                sel_acid = st.selectbox("세정제 선택", [p['Name'] for p in acid_db], key="cip_sel_acid")
                acid_item = next((i for i in acid_db if i['Name'] == sel_acid), None)
                target_ph = 2.0
                # 5% 희석 기준 (통상값)
                req_kg = cip_vol_real * 1000 * 0.05 
                desc = acid_item.get('Desc', '표준 산성 세정제')
            else:
                st.warning("데이터베이스 없음 - 구연산(Citric Acid) 기준으로 계산합니다.")
                sel_acid = "Citric Acid (Powder)"
                req_kg = cip_vol_real * 1000 * 0.05 # 5% w/w
                desc = "분말형 유기산"
            
            c_a1, c_a2 = st.columns([1, 1])
            with c_a1:
                st.metric(label=f"{sel_acid} 투입량", value=f"{req_kg:.1f} kg")
            with c_a2:
                st.markdown(f"**📋 준비물:**")
                st.markdown(f"- 물 (RO 생산수): **{cip_vol_real} ㎥**")
                st.markdown(f"- 약품 ({desc}): **{req_kg:.1f} kg**")
                st.markdown(f"- 목표 pH: **2.0 ~ 3.0**")

        # (2) 알칼리 세정
        with tab_alk:
            st.info(f"🎯 **Target:** 유기물, 슬라임(Biofouling), 실리카 제거 | **물 {cip_vol_real}톤** 기준")
            
            alk_db = PRODUCT_CATALOG.get('RO', {}).get('CIP_Alk', [])
            if alk_db:
                sel_alk = st.selectbox("세정제 선택", [p['Name'] for p in alk_db], key="cip_sel_alk")
                alk_item = next((i for i in alk_db if i['Name'] == sel_alk), None)
                # 5% 희석 기준 (통상값)
                req_alk_kg = cip_vol_real * 1000 * 0.05 
                desc_alk = alk_item.get('Desc', '표준 알칼리 세정제')
            else:
                st.warning("데이터베이스 없음 - NaOH(가성소다) 기준으로 계산합니다.")
                sel_alk = "NaOH (Liquid 100%)"
                req_alk_kg = cip_vol_real * 1000 * 0.005 # 0.5% w/w (pH 11~12)
                desc_alk = "pH 조정제"

            c_b1, c_b2 = st.columns([1, 1])
            with c_b1:
                st.metric(label=f"{sel_alk} 투입량", value=f"{req_alk_kg:.1f} kg")
            with c_b2:
                st.markdown(f"**📋 준비물:**")
                st.markdown(f"- 물 (RO 생산수): **{cip_vol_real} ㎥**")
                st.markdown(f"- 약품 ({desc_alk}): **{req_alk_kg:.1f} kg**")
                st.markdown(f"- 목표 pH: **11.0 ~ 12.0**")

    with tab6:
        st.subheader("📘 RO Engineering Manual & Troubleshooting")
        st.markdown("본 매뉴얼은 **ASTM D4516 (Standard Practice for Standardizing RO Performance Data)** 및 주요 멤브레인 제조사(Dupont/Hydranautics) 기술 자료를 기반으로 합니다.")

        # 1. 핵심 성능 계산 공식
        with st.expander("📐 1. 핵심 성능 계산 공식 (Key Formulas)", expanded=True):
            st.markdown("#### (1) 회수율 (Recovery Rate)")
            st.latex(r"R (\%) = \frac{Q_p}{Q_f} \times 100")
            st.caption("$Q_p$: 생산 유량, $Q_f$: 공급 유량. (일반적 범위: 해수 40~50%, 기수 75~85%)")

            st.markdown("#### (2) 염제거율 (Salt Rejection)")
            st.latex(r"SR (\%) = \left( 1 - \frac{C_p}{C_f} \right) \times 100")
            st.caption("$C_p$: 생산수 농도, $C_f$: 공급수 농도. (최신 RO막은 99.5% 이상)")

            st.markdown("#### (3) 염투과율 (Salt Passage)")
            st.latex(r"SP (\%) = 100 - SR")
            st.caption("막을 통과하여 생산수로 넘어가는 염분의 비율입니다. 수온이 1℃ 오르면 염투과는 약 3~5% 증가합니다.")

            st.markdown("#### (4) 정규화 유량 (Normalized Permeate Flow)")
            st.info("💡 운전 조건(압력, 온도)이 변해도 막의 **'진짜 성능'**이 떨어졌는지 확인하기 위해 표준 조건(25℃)으로 환산하는 공식입니다.")
            st.latex(r"Q_{norm} = Q_{act} \times \left( \frac{NDP_{ref}}{NDP_{act}} \right) \times \frac{TCF_{ref}}{TCF_{act}}")
            st.caption("유량이 줄어도 정규화 유량이 일정하다면, 막힘(Fouling)이 아니라 단순히 수온/압력이 낮아진 것입니다.")

        # 2. 오염 진단 매트릭스 (가장 중요한 부분)
        with st.expander("🚨 2. 트러블슈팅 매트릭스 (Troubleshooting Matrix)", expanded=True):
            st.markdown("#### 증상별 오염 원인 판별 가이드")
            st.markdown("RO 운전 데이터(정규화 기준)의 변화 패턴을 통해 오염 종류를 진단합니다.")

            trouble_data = {
                "구분 (Symptoms)": ["정규화 유량 ↓ (Flow Drop)", "정규화 유량 ↓ (Flow Drop)", "정규화 유량 ↑ (Flow Increase)", "차압(Delta P) 급증 ↑"],
                "염제거율 (Salt Rejection)": ["약간 감소 또는 일정", "급격한 감소", "급격한 감소", "상승 또는 일정"],
                "차압 (Delta P)": ["상승 (1단 위주)", "상승 (2단 위주)", "변화 없음", "급격한 상승"],
                "예상 원인 (Diagnosis)": ["입자성/Colloidal 오염 (SDI 높음)", "스케일(Scale) 발생 (CaCO3, CaSO4)", "막 파손(Oxidation) 또는 O-ring 누수", "미생물 오염 (Biofouling)"],
                "조치 (Action)": ["SDI 체크, 필터 교체, 알칼리 세정", "스케일 방지제 점검, 산성 세정", "Probing Test 수행, 엘리먼트 교체", "살균제(Biocide) 충격 요법, 알칼리 세정"]
            }
            st.table(pd.DataFrame(trouble_data))

        # 3. CIP 가이드
        with st.expander("🧼 3. CIP (Chemical Cleaning) 가이드라인", expanded=False):
            st.markdown("#### 세정 시점 (When to Clean)")
            st.warning("""
            다음 중 하나라도 해당되면 **즉시** 세정을 실시해야 합니다. (지연 시 성능 회복 불가)
            1. **정규화 유량(N.Flow):** 초기 대비 **10 ~ 15% 감소** 시
            2. **정규화 차압(N.DP):** 초기 대비 **15% 상승** 시
            3. **염투과율(Salt Passage):** 초기 대비 **10 ~ 15% 증가** 시
            """)

            st.markdown("#### 세정 순서 (Sequence)")
            st.markdown("""
            1. **알칼리 세정 (High pH):** 유기물, 미생물, 실리카 제거 (pH 11~12, 30~35℃)
            2. **린싱 (Rinsing):** 생산수로 pH 중성까지 헹굼
            3. **산성 세정 (Low pH):** 금속 산화물, 탄산염 스케일 제거 (pH 2~3, 25℃)
            4. **주의:** 스케일이 주원인인 경우 산성 세정을 먼저 할 수도 있으나, 통상적으로는 **[알칼리 → 산]** 순서를 권장합니다. (유기막이 산성에서 굳어버리는 것을 방지)
            """)

        # 4. 관리 지표 설명
        with st.expander("📊 4. 주요 관리 지표 (Indices)", expanded=False):
            st.markdown("**① SDI (Silt Density Index)**")
            st.write("- 전처리 효율을 나타내는 지표. RO 유입수는 **SDI < 3.0** (권장), 최대 5.0 이하로 관리해야 함.")
            
            st.markdown("**② LSI (Langelier Saturation Index)**")
            st.write("- 탄산칼슘(CaCO3) 스케일 경향성. **LSI > 1.8** 이상이면 스케일 방지제 투입 필수.")
            
            st.markdown("**③ Flux (플럭스)**")
            st.latex(r"Flux (LMH) = \frac{Flow (m^3/hr)}{Area (m^2)}")
            st.write("- 단위 면적당 생산량. 너무 높으면 오염 속도가 기하급수적으로 빨라짐.")       
# ==============================================================================
# [Module 4] Wastewater Reuse: Expert System (TOC Edition)
# ==============================================================================
if "WWT" in program_mode:
 
    # 1. 공정 라이브러리 (TOC 제거율 기반 DB 업데이트)
    PROCESS_LIB = {
        "Screen/EQ": {
            "Removal": {"SS": 0.1, "TOC": 0.05, "COD": 0.05, "Oil": 0.0, "TN": 0.0, "TDS": 0.0},
            "Energy": 0.05, "Sludge_Factor": 0.0, "Desc": "유량 조정 및 협잡물 제거"
        },
        "pH Control (중화)": {
            "Removal": {"SS": 0.0, "TOC": 0.0, "COD": 0.0, "Oil": 0.0, "TN": 0.0, "TDS": -0.1}, 
            "Energy": 0.02, "Sludge_Factor": 0.05, "Desc": "산/알칼리 중화"
        },
        "Coagulation (화학적 응집)": {
            "Removal": {"SS": 0.85, "TOC": 0.30, "COD": 0.45, "Oil": 0.6, "TN": 0.1, "TP": 0.9, "TDS": 0.0},
            "Energy": 0.1, "Sludge_Factor": 1.5, "Desc": "PAC/Polymer 투입 (SS, TP, Colloid TOC 제거)"
        },
        "DAF (가압부상)": {
            "Removal": {"SS": 0.90, "TOC": 0.35, "COD": 0.5, "Oil": 0.95, "TN": 0.1, "TDS": 0.0},
            "Energy": 0.3, "Sludge_Factor": 1.2, "Desc": "유분(Oil) 및 부유성 유기물 제거"
        },
        "A2O (생물학적 고도처리)": {
            "Removal": {"SS": 0.8, "TOC": 0.85, "COD": 0.85, "Oil": 0.9, "TN": 0.8, "NH3-N": 0.9, "TDS": 0.0},
            "Energy": 0.8, "Sludge_Factor": 0.4, "Desc": "생분해성 유기탄소(TOC) 및 질소/인 제거"
        },
        "MBR (분리막 생물반응조)": {
            "Removal": {"SS": 0.999, "TOC": 0.93, "COD": 0.95, "Oil": 0.99, "TN": 0.85, "TDS": 0.0},
            "Energy": 1.5, "Sludge_Factor": 0.3, "Desc": "SS 완벽 제거 및 고효율 TOC 처리"
        },
        "Sand Filter (여과)": {
            "Removal": {"SS": 0.7, "TOC": 0.1, "COD": 0.1, "Oil": 0.2, "TN": 0.0, "TDS": 0.0},
            "Energy": 0.2, "Sludge_Factor": 0.05, "Desc": "잔류 부유물질 제거"
        },
        "ACF (활성탄)": {
            "Removal": {"SS": 0.8, "TOC": 0.7, "COD": 0.7, "Oil": 0.8, "TN": 0.1, "TDS": 0.0},
            "Energy": 0.1, "Sludge_Factor": 0.0, "Desc": "난분해성 TOC 및 색도 흡착 (RO 전처리 필수)"
        },
        "RO System (역삼투)": {
            "Removal": {"SS": 1.0, "TOC": 0.98, "COD": 0.99, "Oil": 1.0, "TN": 0.95, "TDS": 0.98},
            "Energy": 3.0, "Sludge_Factor": 0.0, "Desc": "용존 이온 및 잔류 TOC 제거"
        }
    }

    # 규제/목표 기준 DB (TOC 기준 적용)
    STD_DB = {
        "방류 (법적기준)": {"TOC": 25, "COD": 40, "SS": 10, "TN": 20, "TP": 2, "Oil": 5, "TDS": 5000},
        "재이용 (공업용수)": {"TOC": 10, "COD": 20, "SS": 5, "TN": 10, "TP": 0.5, "Oil": 1, "TDS": 1500},
        "재이용 (RO Feed)": {"TOC": 3, "COD": 10, "SS": 1, "TN": 5, "TP": 0.1, "Oil": 0.1, "TDS": 2000}
    }

    # --------------------------------------------------------------------------
    # UI Layout: 6-Step Structure
    # --------------------------------------------------------------------------
    st.title("🏭 WWT Expert System (폐수처리 및 재이용 진단)")
    st.markdown("##### **Load 기반 공정 설계 & 재이용(RO) 타당성 평가 솔루션**")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 1. 유입부하 분석", 
        "⚙️ 2. 공정 자동설계", 
        "🧪 3. 처리효율 시뮬레이션", 
        "📈 4. 진단 및 ROI", 
        "💧 5. RO 연계/재이용",
        "📘 기술 매뉴얼 (Formula)"
    ])

    # ==========================================================================
    # Step 1. Influent Data & Load Calculation
    # ==========================================================================
    with tab1:
        st.subheader("1️⃣ 유입 폐수 성상 및 오염부하량 (Pollutant Load)")
        st.info("💡 **Load(kg/day)**는 공정 설계의 핵심 지표입니다. (BOD 삭제 -> TOC 대체됨)")
        
        col_i1, col_i2 = st.columns([1, 2])
        with col_i1:
            st.markdown("**기본 운전 조건**")
            in_flow = st.number_input("일일 유량 (Q, m³/day)", value=1000.0, step=100.0, format="%.0f")
            in_temp = st.number_input("수온 (°C)", value=25.0)
            in_ph = st.number_input("pH", value=7.0)

        with col_i2:
            st.markdown("**수질 농도 입력 (Concentration, mg/L)**")
            c1, c2, c3 = st.columns(3)
            with c1:
                # [수정] BOD 삭제 -> TOC 추가
                conc_toc = st.number_input("TOC (총유기탄소)", value=80.0, help="Total Organic Carbon")
                conc_tn = st.number_input("T-N", value=50.0)
                conc_oil = st.number_input("Oil & Grease", value=10.0)
            with c2:
                conc_cod = st.number_input("COD", value=200.0)
                conc_tp = st.number_input("T-P", value=5.0)
                conc_tds = st.number_input("TDS (염분)", value=1200.0)
            with c3:
                conc_ss = st.number_input("SS (부유물)", value=300.0)
                conc_nh3 = st.number_input("NH3-N", value=30.0)
                conc_color = st.number_input("Color (도)", value=50.0)

        # [Engine] Load Calculation (kg/day)
        load_cod = in_flow * conc_cod * 0.001
        load_toc = in_flow * conc_toc * 0.001
        load_ss = in_flow * conc_ss * 0.001
        load_tn = in_flow * conc_tn * 0.001
        
        st.divider()
        st.markdown("#### ⚖️ 오염 부하량 산출 결과 (Engineering Load)")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("COD Load", f"{load_cod:,.1f} kg/d")
        m2.metric("TOC Load", f"{load_toc:,.1f} kg/d", "Organic Carbon")
        m3.metric("SS Load", f"{load_ss:,.1f} kg/d")
        m4.metric("T-N Load", f"{load_tn:,.1f} kg/d")

    # ==========================================================================
    # Step 2. Process Design (Auto & Custom)
    # ==========================================================================
    with tab2:
        st.subheader("2️⃣ 공정 선택 및 설계 (Process Selection)")
        
        c_sel1, c_sel2 = st.columns(2)
        with c_sel1:
            target_mode = st.selectbox("🎯 처리 목적 (Target)", list(STD_DB.keys()))
        with c_sel2:
            industry_type = st.selectbox("🏭 업종 (Industry)", ["도금/표면처리", "식품/음료", "화학/정밀", "반도체/전자", "일반 하수"])

        # [Engine] Auto Recommendation Logic
        recommendation = []
        if industry_type == "도금/표면처리":
            recommendation = ["pH Control (중화)", "Coagulation (화학적 응집)", "DAF (가압부상)", "Sand Filter (여과)"]
        elif industry_type == "식품/음료":
            recommendation = ["Screen/EQ", "DAF (가압부상)", "A2O (생물학적 고도처리)", "Sand Filter (여과)"]
        elif industry_type == "화학/정밀":
            recommendation = ["pH Control (중화)", "Coagulation (화학적 응집)", "A2O (생물학적 고도처리)", "ACF (활성탄)"]
        elif industry_type == "반도체/전자":
            recommendation = ["pH Control (중화)", "Coagulation (화학적 응집)", "Sand Filter (여과)", "ACF (활성탄)"]
        else: # 일반
            recommendation = ["Screen/EQ", "A2O (생물학적 고도처리)", "Sand Filter (여과)"]

        # 재이용 목적이면 후단 설비 추가 (TOC 제어를 위해 활성탄 중요)
        if "재이용" in target_mode:
            if "RO" not in recommendation and "MBR" not in recommendation:
                recommendation.append("ACF (활성탄)")
            if "RO Feed" in target_mode:
                 recommendation.append("RO System (역삼투)")

        st.info(f"💡 **AI 추천 공정 ({industry_type} → {target_mode}):** \n {' > '.join(recommendation)}")
        
        # User Customization
        selected_processes = st.multiselect(
            "🛠️ 공정 라인 구성 (순서대로 적용됩니다)", 
            list(PROCESS_LIB.keys()), 
            default=recommendation
        )

    # ==========================================================================
    # Step 3. Simulation & Prediction
    # ==========================================================================
    with tab3:
        st.subheader("3️⃣ 공정별 처리 효율 시뮬레이션 (Waterfall Simulation)")
        
        # [Engine] Sequential Removal Calculation
        # 초기 농도 (TOC 포함)
        curr_conc = {
            "SS": conc_ss, "TOC": conc_toc, "COD": conc_cod, 
            "Oil": conc_oil, "TN": conc_tn, "TP": conc_tp, "TDS": conc_tds
        }
        
        sim_log = []
        sim_log.append({"Step": "Raw Water", **curr_conc}) # 초기값 저장
        
        cum_energy = 0.0
        cum_sludge = 0.0

        for proc_name in selected_processes:
            lib_data = PROCESS_LIB[proc_name]
            rem_rates = lib_data["Removal"]
            
            # 농도 감소 계산
            next_conc = {}
            for param, val in curr_conc.items():
                rate = rem_rates.get(param, 0.0)
                removed_val = val * rate
                next_val = val - removed_val
                if next_val < 0: next_val = 0
                next_conc[param] = next_val
                
                # 슬러지 발생 계산 (SS 및 COD 제거량 기반 간이 계산)
                if param == "SS":
                    cum_sludge += (in_flow * removed_val * 0.001) * 1.0 # SS는 100% 슬러지화 가정
                elif param == "COD" and lib_data["Sludge_Factor"] > 0:
                     cum_sludge += (in_flow * removed_val * 0.001) * lib_data["Sludge_Factor"]

            # 에너지 계산
            cum_energy += in_flow * lib_data["Energy"]
            
            curr_conc = next_conc
            sim_log.append({"Step": proc_name, **curr_conc})

        # Display Result Table
        df_sim = pd.DataFrame(sim_log)
        
        # [Error Fix Applied] 문자열 컬럼 제외 포맷팅
        st.dataframe(
            df_sim.style.format({col: "{:.1f}" for col in df_sim.columns if col != "Step"}), 
            use_container_width=True
        )

        # Graph (TOC 추가)
        st.markdown("#### 📉 오염물질 제거 추이")
        fig = go.Figure()
        for param in ["COD", "TOC", "SS", "TDS"]:
            fig.add_trace(go.Scatter(x=df_sim["Step"], y=df_sim[param], mode='lines+markers', name=param))
        st.plotly_chart(fig, use_container_width=True)

    # ==========================================================================
    # Step 4. Diagnosis & ROI
    # ==========================================================================
    with tab4:
        st.subheader("4️⃣ 종합 진단 및 경제성 평가")
        
        # 1. 수질 진단 (Score)
        final_eff = df_sim.iloc[-1]
        target_std = STD_DB[target_mode]
        
        score = 100
        fail_list = []
        
        c_res1, c_res2 = st.columns([1, 1])
        with c_res1:
            st.markdown("**규제 기준 만족 여부**")
            for param, limit in target_std.items():
                val = final_eff.get(param, 0)
                if val > limit:
                    st.error(f"❌ {param}: {val:.1f} > {limit} (초과)")
                    score -= 20
                    fail_list.append(param)
                else:
                    st.success(f"✅ {param}: {val:.1f} ≤ {limit} (만족)")
            if score < 0: score = 0

        with c_res2:
            st.markdown("**종합 안전 등급**")
            if score >= 80:
                st.metric("System Score", f"{score}점", "안정 (Stable)", delta_color="normal")
            elif score >= 50:
                st.metric("System Score", f"{score}점", "주의 (Warning)", delta_color="off")
            else:
                st.metric("System Score", f"{score}점", "위험 (Critical)", delta_color="inverse")
            
            if fail_list:
                st.warning(f"⚠️ 개선 필요 항목: {', '.join(fail_list)}")
                
        # 2. OPEX & ROI
        st.divider()
        st.markdown("#### 💰 운영비(OPEX) 및 투자회수(ROI)")
        
        # 비용 가정
        cost_elec = 120 # 원/kWh
        cost_sludge = 150 # 원/kg (처리비)
        cost_chem = cum_energy * 20 # 약품비는 에너지비의 20%로 간이 추정
        cost_water = 1500 # 공업용수 단가 (원/톤)
        
        daily_opex = (cum_energy * cost_elec) + (cum_sludge * cost_sludge) + cost_chem
        daily_saving = in_flow * cost_water if score >= 80 and "재이용" in target_mode else 0
        
        roi_col1, roi_col2, roi_col3 = st.columns(3)
        roi_col1.metric("일일 전력비", f"{int(cum_energy * cost_elec):,} 원")
        roi_col2.metric("일일 슬러지 처리비", f"{int(cum_sludge * cost_sludge):,} 원", f"발생량 {cum_sludge:.1f} kg/d")
        roi_col3.metric("총 운영비 (OPEX)", f"{int(daily_opex):,} 원/일")

        if daily_saving > 0:
            net_benefit = daily_saving - daily_opex
            st.success(f"💰 **재이용 경제성 분석:** 하루 {int(daily_saving):,}원의 용수 비용 절감 → 순이익 **{int(net_benefit):,} 원/일**")
        else:
            st.info("ℹ️ 재이용 모드가 아니거나 수질 기준 미달로 경제성 산출 불가")

    # ==========================================================================
    # Step 5. RO Integration (The Killer Feature)
    # ==========================================================================
    with tab5:
        st.subheader("💧 5. RO 시스템 연계 적합성 판정")
        st.markdown("WWT 최종 방류수를 **RO 유입수(Feed)**로 사용할 수 있는지 정밀 진단합니다.")

        ro_feed_ss = final_eff["SS"]
        ro_feed_toc = final_eff["TOC"] # BOD 대체
        ro_feed_tds = final_eff["TDS"]
        ro_feed_oil = final_eff["Oil"]

        # [RO Feed Limits] - Membrane Maker Guideline (TOC 기준)
        limit_ro_ss = 5.0  # SDI < 3~5 equivalent
        limit_ro_toc = 3.0 # Biofouling risk (BOD보다 엄격)
        limit_ro_oil = 0.1
        
        # Diagnosis
        ro_ready = True
        
        c_ro1, c_ro2 = st.columns(2)
        with c_ro1:
            st.markdown("##### 🔍 RO 유입 제한 기준 Check")
            
            # SS Check
            if ro_feed_ss > limit_ro_ss:
                st.error(f"❌ **SS ({ro_feed_ss:.1f}) > {limit_ro_ss}:** 막 막힘(Fouling) 위험 큼. UF 또는 여과 보강 필요.")
                ro_ready = False
            else:
                st.success(f"✅ **SS ({ro_feed_ss:.1f}):** 양호")

            # TOC Check (BOD 대체)
            if ro_feed_toc > limit_ro_toc:
                st.error(f"❌ **TOC ({ro_feed_toc:.1f}) > {limit_ro_toc}:** 바이오파울링(Biofouling) 위험. 활성탄/살균제 필요.")
                ro_ready = False
            else:
                st.success(f"✅ **TOC ({ro_feed_toc:.1f}):** 양호")
                
            # Oil Check
            if ro_feed_oil > limit_ro_oil:
                st.error(f"❌ **Oil ({ro_feed_oil:.1f}) > {limit_ro_oil}:** 치명적 막 오염. 활성탄/DAF 보강 필수.")
                ro_ready = False
            else:
                st.success(f"✅ **Oil ({ro_feed_oil:.1f}):** 양호")

        with c_ro2:
            st.markdown("##### 📊 RO 성능 예측 (간이)")
            if ro_ready:
                est_recovery = 75.0
                est_perm_tds = ro_feed_tds * (1 - 0.98) # 98% Rej
                st.info(f"""
                **✅ RO 운전 가능 (Ready to RO)**
                - 예상 회수율: **{est_recovery}%**
                - 예상 처리수 TDS: **{est_perm_tds:.1f} mg/L** (양호)
                - 필요 전처리: Cartridge Filter (5 micron)
                """)
               # -----------------------------------------------------------
                # [수정된 코드] 콜백(Callback) 방식을 사용하여 에러 해결
                # -----------------------------------------------------------
                
                # 1. 실행할 함수 정의 (이 함수는 버튼을 누르는 순간 실행됨)
                def go_to_ro_callback(val_flow, val_temp):
                    # (1) 단위 및 유량 변환
                    flow_hr = val_flow / 24.0
                    prod_flow = flow_hr * 0.75
                    
                    # (2) RO 입력창 값 세팅
                    st.session_state['ro_in_flow_fix'] = float(prod_flow)
                    st.session_state['ro_in_temp_fix'] = float(val_temp)
                    st.session_state['ro_in_rec_fix'] = 75.0
                    
                    # (3) 메뉴 변경 (콜백 함수 안에서는 에러 없이 변경 가능!)
                    st.session_state['main_menu_mode'] = "3. RO Calc."
                    
                # 2. 버튼 생성 (on_click에 함수와 인자 전달)
                # args=(in_flow, in_temp)를 통해 현재 입력된 유량과 수온을 함수로 넘겨줍니다.
                if st.button("🚀 이 데이터를 RO 모듈로 전송 (Simulation)", type="primary", 
                             on_click=go_to_ro_callback, args=(in_flow, in_temp)):
                    st.toast("데이터 전송 완료! RO 탭으로 이동합니다.")
    with tab6:
        st.subheader("📘 Wastewater Treatment Engineering Manual")
        st.markdown("활성슬러지 공정(Activated Sludge) 진단 및 운전 관리를 위한 핵심 이론서입니다.")

        # 1. 운전 지표 (F/M, SRT)
        with st.expander("🦠 1. 생물학적 처리 핵심 지표 (Key Parameters)", expanded=True):
            st.markdown("#### (1) F/M 비 (Food to Microorganism Ratio)")
            st.info("미생물(MLSS)에게 공급되는 먹이(BOD/COD)의 비율입니다. 운전 상태를 결정하는 가장 중요한 지표입니다.")
            st.latex(r"F/M (kg \cdot BOD/kg \cdot MLSS \cdot day) = \frac{Q \times BOD}{V \times MLSS}")
            st.markdown("""
            - **표준 활성슬러지:** 0.2 ~ 0.4 (정상 침강성)
            - **장기 폭기/MBR:** 0.05 ~ 0.15 (자기 산화, 슬러지 감량)
            - **고부하 (High Rate):** > 0.5 (침강 불량, 분산 증식)
            """)

            st.markdown("#### (2) SVI (Sludge Volume Index)")
            st.info("슬러지의 침강성을 나타내는 지표로, 벌킹(Bulking) 여부를 판단합니다.")
            st.latex(r"SVI = \frac{SV_{30} (\%) \times 10,000}{MLSS (mg/L)}")
            
            c_svi1, c_svi2 = st.columns(2)
            with c_svi1:
                st.write("**판정 기준:**")
                st.write("- **50 ~ 150:** 양호 (Good Settling)")
                st.write("- **> 200:** 벌킹 (Bulking) - 사상균 과다")
                st.write("- **< 50:** 핀 플럭 (Pin Floc) - 과도한 해체")
            with c_svi2:
                st.write("**트러블슈팅:**")
                st.write("- **SVI 높을 때:** DO 증대, 반송율 증대, 염소(Cl2) 살균")
                st.write("- **SVI 낮을 때:** 폐수 부하 증대, 폭기량 감소")

        # 2. 질소/인 제거 원리
        with st.expander("♻️ 2. 고도처리 원리 (Nutrient Removal)", expanded=False):
            st.markdown("#### (1) 질소 제거 (Nitrification & Denitrification)")
            st.markdown("**Step 1: 질산화 (호기성, Aerobic)**")
            st.latex(r"NH_4^+ + 2O_2 \rightarrow NO_3^- + 2H^+ + H_2O")
            st.caption("질산화균(Nitrosomonas, Nitrobacter)이 암모니아를 질산으로 산화시킵니다. (알칼리도 소모, pH 저하)")
            
            st.markdown("**Step 2: 탈질 (무산소, Anoxic)**")
            st.latex(r"2NO_3^- + 10H + \rightarrow N_2 \uparrow + 2OH^- + 4H_2O")
            st.caption("탈질균이 유기물(탄소원)을 이용하여 질산을 질소 가스로 환원시킵니다. (알칼리도 회복, pH 상승)")

            st.markdown("#### (2) 인 제거 (P Removal)")
            st.write("- **혐기조 (Anaerobic):** 인 방출 (미생물이 스트레스 상태에서 체내 인을 뱉어냄)")
            st.write("- **호기조 (Aerobic):** 인 과잉 섭취 (Luxury Uptake, 뱉어낸 양보다 더 많이 섭취)")
            st.write("- **최종:** 인을 많이 머금은 잉여 슬러지를 폐기(Was)하여 제거.")

        # 3. 미생물 관찰 가이드
        with st.expander("🔬 3. 미생물 지표 생물 (Indicator Organisms)", expanded=False):
            st.markdown("현미경 관찰 시 보이는 미생물로 현재 처리 상태를 진단할 수 있습니다.")
            
            micro_data = {
                "상태 (Condition)": ["운전 개시 / 고부하", "양호 (Good Condition)", "해체 / 과폭기", "DO 부족 / 부하 변동"],
                "지표 미생물 (Organism)": ["편모충류 (Flagellates), 아메바", "종벌레 (Vorticella), 로티퍼 (Rotifier)", "유각변형충 (Arcella)", "사상균 (Sphaerotilus)"],
                "특징": ["슬러지가 형성되지 않음, 처리수 탁함", "플럭 형성 양호, 처리수 맑음", "플럭이 깨짐, 핀 플럭 발생", "슬러지 팽화(Bulking), 침강성 불량"]
            }
            st.dataframe(pd.DataFrame(micro_data), use_container_width=True)

        # 4. 현장 문제 해결 가이드
        with st.expander("🛠️ 4. 현장 트러블슈팅 가이드", expanded=True):
            st.markdown("##### 1. 거품(Foam) 발생 원인 및 대책")
            st.write("- **흰 거품:** 시운전 초기 또는 과도한 세제 유입 → 소포제 살포, 반송 슬러지 증대")
            st.write("- **갈색 거품:** 과폭기, SRT가 너무 길 때 (Old Sludge) → 잉여 폐기(Was)량 증대")
            st.write("- **검은 거품:** 혐기화 진행, 공기 공급 부족 → 송풍량 증대, 바닥 침전물 확인")

            st.markdown("##### 2. 처리수 pH 저하")
            st.write("- **원인:** 질산화가 과도하게 진행되어 알칼리도 소모")
            st.write("- **대책:** 가성소다(NaOH) 투입 또는 탈질 효율 증대 (탈질 시 알칼리도 회복됨)")

# ==============================================================================
# [Module 5] Basic Engineering Calculator (RO & AFM Sizing)
# ==============================================================================
elif "Engineering" in program_mode:
    st.title("📏 Basic Engineering & Sizing Calculator")
    st.info("설비 규격 및 여재 충진량 산출 (AFM IFU V23.4 규격 적용)")

    tab_afm, tab_ro_sizing, tab_piping= st.tabs(["🧪 AFM/Media Filter Sizing", "💧 RO System Sizing","📏 Piping & Hydraulics"])

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

# --- [2. RO System Sizing] (플럭스 & 펌프 선정 통합) ---
    with tab_ro_sizing:
        st.subheader("💧 RO System Configuration & Design")
        st.info("💡 **설계 플럭스**와 **원수 TDS**를 기반으로 멤브레인 배열과 고압 펌프 사양을 자동 산출합니다.")

        # 좌우 2단 컬럼 레이아웃 유지 (입력 / 결과)
        r1, r2 = st.columns(2)
        
        # --- [입력 섹션] ---
        with r1:
            st.markdown("### ⚙️ 설계 입력 (Input Data)")
            
            st.markdown("**1. 생산 목표 (Production)**")
            target_p = st.number_input("목표 생산수 유량 (m3/hr)", value=50.0, step=1.0, key="ro_target_p")
            target_rec = st.slider("목표 회수율 (Recovery, %)", 40, 95, 75, key="ro_target_rec")
            
            st.markdown("**2. 멤브레인 설계 (Membrane)**")
            # [핵심] 플럭스 변경 시 베셀 수 즉시 연동 (기존 로직 유지)
            design_flux = st.number_input("설계 플럭스 (Flux, LMH)", value=18.7, step=0.1, 
                                        help="값을 높이면 베셀 수가 줄어들고, 낮추면 늘어납니다.", key="ro_flux")
            elements_per_vessel = st.selectbox("베셀당 엘리먼트 수", [4, 5, 6, 7], index=2, key="ro_ele_per_ves")
            active_area = st.number_input("엘리먼트 유효 면적 (ft²)", value=400, step=10, key="ro_area")

            st.markdown("**3. 펌프 설계 (Pump)**")
            # [추가됨] 펌프 용량 계산을 위한 입력값
            feed_tds = st.number_input("원수 TDS (mg/L)", value=500, step=50, help="삼투압 계산용")
            pump_eff = st.number_input("펌프 효율 (%)", value=65.0, step=1.0)
            motor_eff = st.number_input("모터 효율 (%)", value=92.0, step=1.0)

            with st.expander("ℹ️ [가이드] 적정 플럭스 범위", expanded=False):
                st.markdown("""
                * **18 ~ 22 LMH:** 깨끗한 지하수/상수 (부장님 추천 범위)
                * **14 ~ 18 LMH:** 하천수/지표수
                * **10 ~ 14 LMH:** 폐수 재이용/오염된 물
                """)

        # --- [엔지니어링 계산 엔진] ---
        feed_flow = target_p / (target_rec / 100)
        concentrate_flow = feed_flow - target_p
        
        # 1. 멤브레인 계산 (기존 로직 유지)
        total_area_m2 = (target_p * 1000) / design_flux
        element_area_m2 = active_area * 0.0929
        total_elements = math.ceil(total_area_m2 / element_area_m2)
        total_vessels = math.ceil(total_elements / elements_per_vessel)
        actual_flux = (target_p * 1000) / (total_elements * element_area_m2)

        # 2. 배열 계산 (2단 2:1 정석 - 기존 로직 유지)
        v2_st1 = int(round(total_vessels * 0.666)) 
        v2_st2 = total_vessels - v2_st1
        if v2_st2 < 1: v2_st1 -= 1; v2_st2 += 1
        str_2st = f"{v2_st1} : {v2_st2}"
        
        # 3. 배열 계산 (3단)
        if total_vessels >= 6:
            v3_st1 = math.ceil(total_vessels * 0.5)
            v3_st2 = math.ceil(total_vessels * 0.3)
            v3_st3 = total_vessels - v3_st1 - v3_st2
            if v3_st3 < 1: v3_st2 -= 1; v3_st3 += 1
            str_3st = f"{v3_st1} : {v3_st2} : {v3_st3}"
        else:
            str_3st = "N/A (베셀 부족)"

        # 4. [NEW] 펌프 용량 계산 로직
        # 삼투압 추정 (1000ppm ≈ 0.75 bar)
        avg_tds = feed_flow * feed_tds / (feed_flow + concentrate_flow) * 1.5 
        osmotic_pressure = (avg_tds / 1000.0) * 0.75
        
        # 필요 압력 (NDP + 삼투압 + 배관손실)
        base_pressure = 12.0 # 기본 운전 압력
        piping_loss = 2.0
        required_pressure = base_pressure + osmotic_pressure + piping_loss
        
        # 동력 계산 (Shaft Power & Motor Power)
        # Power(kW) = (Flow(m3/hr) * Pressure(bar)) / (36 * Efficiency)
        shaft_power = (feed_flow * required_pressure) / (36 * (pump_eff / 100.0))
        required_motor = shaft_power / (motor_eff / 100.0) * 1.15 # 여유율 15%

        # --- [결과 표시 섹션] ---
        with r2:
            st.markdown("### 🎯 설계 결과 (Engineering Result)")
            
            # 탭으로 깔끔하게 구분 (멤브레인 vs 펌프)
            res_tab1, res_tab2 = st.tabs(["🏗️ 멤브레인 배열", "🔌 고압 펌프 선정"])
            
            with res_tab1:
                with st.container(border=True):
                    st.metric("총 엘리먼트 / 베셀", f"{total_elements} EA / {total_vessels} PV")
                    st.metric("실제 운전 플럭스", f"{actual_flux:.1f} LMH")
                    st.metric("표준 배열 (2:1)", str_2st)
                    st.caption(f"**Stage 1:** {v2_st1} PV  ➔  **Stage 2:** {v2_st2} PV")
                
                if target_rec <= 80:
                    st.success("✅ **[적합]** 2단 배열(2:1)이 가장 효율적입니다.")
                else:
                    st.warning("⚠️ **[주의]** 고회수율 운전 시 유속 저하 주의.")

                # 유량 밸런스
                c_f1, c_f2 = st.columns(2)
                c_f1.metric("유입수 유량", f"{feed_flow:.1f} m³/hr")
                c_f2.metric("농축수 유량", f"{concentrate_flow:.1f} m³/hr")

            with res_tab2:
                with st.container(border=True):
                    # 펌프 유량 = Feed Flow * 1.1 (여유율)
                    design_q = feed_flow * 1.1
                    st.metric("펌프 설계 유량 (Q)", f"{design_q:.1f} m³/hr", f"Operating: {feed_flow:.1f}")
                    st.metric("필요 양정/압력 (H)", f"{required_pressure:.1f} bar", f"Osmotic: {osmotic_pressure:.1f} bar")
                    st.metric("모터 동력 (P)", f"{required_motor:.1f} kW", f"Shaft: {shaft_power:.1f} kW")
                
                st.info(f"""
                **💡 펌프 선정 가이드**
                - **Flow:** {math.ceil(design_q)} m³/hr 이상
                - **Head:** {math.ceil(required_pressure)} bar 이상
                - **Motor:** {math.ceil(required_motor)} kW (여유율 15% 포함)
                """)
# [Tab 3] 배관 유속 및 마찰 손실 계산 (New!)
    # ==========================================================================
    with tab_piping:
        st.subheader("📏 배관 유속 및 마찰 손실 (Piping Hydraulics)")
        st.info("💡 **Hazen-Williams 공식**을 사용하여 유속(Velocity)과 마찰 손실(Head Loss)을 정밀 계산합니다.")

        # 1. 배관 데이터베이스 (ANSI/ASME B36.10M 표준)
        # Key: 호칭경(A), Value: {SCH10: 내경mm, SCH40: 내경mm, SCH80: 내경mm}
        PIPE_DB = {
            "15A (1/2\")":  {"SCH 10": 17.1, "SCH 40": 15.8, "SCH 80": 13.9},
            "20A (3/4\")":  {"SCH 10": 22.5, "SCH 40": 20.9, "SCH 80": 18.9},
            "25A (1\")":    {"SCH 10": 27.9, "SCH 40": 26.6, "SCH 80": 24.3},
            "32A (1-1/4\")":{"SCH 10": 36.6, "SCH 40": 35.1, "SCH 80": 32.5},
            "40A (1-1/2\")":{"SCH 10": 42.7, "SCH 40": 40.9, "SCH 80": 38.1},
            "50A (2\")":    {"SCH 10": 54.8, "SCH 40": 52.5, "SCH 80": 49.3},
            "65A (2-1/2\")":{"SCH 10": 66.9, "SCH 40": 62.7, "SCH 80": 59.0},
            "80A (3\")":    {"SCH 10": 82.8, "SCH 40": 77.9, "SCH 80": 73.7},
            "100A (4\")":   {"SCH 10": 108.2, "SCH 40": 102.3, "SCH 80": 97.2},
            "125A (5\")":   {"SCH 10": 134.5, "SCH 40": 128.2, "SCH 80": 122.3},
            "150A (6\")":   {"SCH 10": 161.5, "SCH 40": 154.1, "SCH 80": 146.3},
            "200A (8\")":   {"SCH 10": 211.6, "SCH 40": 202.7, "SCH 80": 193.7},
            "250A (10\")":  {"SCH 10": 264.7, "SCH 40": 254.5, "SCH 80": 242.9},
            "300A (12\")":  {"SCH 10": 314.7, "SCH 40": 303.2, "SCH 80": 288.9},
            "350A (14\")":  {"SCH 10": 346.0, "SCH 40": 333.3, "SCH 80": 317.5},
            "400A (16\")":  {"SCH 10": 396.8, "SCH 40": 381.0, "SCH 80": 363.5},
        }

        # 조도 계수 (C-Factor)
        C_FACTOR = {
            "PVC / PE / Plastic": 150,
            "Stainless Steel (SUS)": 140,
            "Carbon Steel (New)": 120,
            "Carbon Steel (Old)": 100,
            "Concrete": 120
        }

        # 2. 입력 섹션
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            st.markdown("##### ⚙️ 운전 조건 (Condition)")
            flow_m3 = st.number_input("유량 (Flow Rate, m³/hr)", value=50.0, step=1.0)
            pipe_len = st.number_input("배관 길이 (Length, m)", value=100.0, step=10.0)
            
            st.markdown("##### 🧪 배관 재질 (Material)")
            mat_sel = st.selectbox("재질 선택 (Roughness)", list(C_FACTOR.keys()))
            c_val = C_FACTOR[mat_sel]
            st.caption(f"적용 C-Factor: {c_val}")

        with col_p2:
            st.markdown("##### 📏 배관 규격 (Size & Schedule)")
            sch_sel = st.radio("배관 두께 (Schedule)", ["SCH 10", "SCH 40", "SCH 80"], horizontal=True)
            size_sel = st.selectbox("호칭경 (Nominal Dia)", list(PIPE_DB.keys()), index=8) # Default 100A
            
            # 실제 내경 조회
            real_id_mm = PIPE_DB[size_sel].get(sch_sel, 0)
            st.metric("실제 내경 (Inner Dia)", f"{real_id_mm} mm", f"{sch_sel} 기준")

        st.divider()

        # 3. 계산 엔진 (Calculation Engine)
        if real_id_mm > 0 and flow_m3 > 0:
            # A. 유속 계산 (Velocity)
            # Area (m2) = pi * (d/2000)^2
            area_m2 = math.pi * ((real_id_mm / 1000) / 2) ** 2
            velocity = (flow_m3 / 3600) / area_m2 # m/s
            
            # B. 마찰 손실 계산 (Hazen-Williams)
            # Head Loss (m) = 10.67 * L * Q^1.85 / (C^1.85 * d^4.87) 
            # (Q in m3/s, d in m) -> 공식 변환 주의
            
            # 편의상 bar 단위 계산식 (Global Standard):
            # dP (bar/100m) = 6.05 * 10^5 * (Q_m3h ^ 1.85) / (C ^ 1.85 * d_mm ^ 4.87)
            dp_100m_bar = 6.05 * (10**5) * (flow_m3 ** 1.85) / ((c_val ** 1.85) * (real_id_mm ** 4.87))
            total_dp_bar = dp_100m_bar * (pipe_len / 100.0)
            total_head_m = total_dp_bar * 10.197 # bar -> mAq

            # 4. 결과 리포트
            st.subheader("📊 유체 역학 분석 결과")
            
            c_res1, c_res2, c_res3 = st.columns(3)
            
            # [Result 1] 유속 진단
            with c_res1:
                st.metric("유속 (Velocity)", f"{velocity:.2f} m/s")
                
                # 유속 가이드라인 (부장님 기준)
                if velocity > 3.0:
                    st.error("⛔ **유속 과다 (Too High)**\n- 침식(Erosion) 및 수격현상(Water Hammer) 위험.\n- 배관을 키우십시오.")
                elif velocity > 2.5:
                    st.warning("⚠️ **유속 높음 (High)**\n- 토출측 허용 한계이나 소음 발생 가능.")
                elif velocity < 0.5:
                    st.warning("⚠️ **유속 저하 (Too Low)**\n- 슬러지 침적(Sedimentation) 우려.")
                else:
                    st.success("✅ **적정 유속 (Good)**\n- (0.5 ~ 2.5 m/s) 범위 만족.")

            # [Result 2] 마찰 손실
            with c_res2:
                st.metric("마찰 손실 (Pressure Drop)", f"{total_dp_bar:.3f} bar", f"길이 {pipe_len}m 기준")
                st.caption(f"단위 손실: {dp_100m_bar:.3f} bar/100m")

            # [Result 3] 펌프 양정 환산
            with c_res3:
                st.metric("손실 수두 (Head Loss)", f"{total_head_m:.2f} m")
                st.info("💡 펌프 선정 시 이 값 이상의 양정(Head) 여유가 필요합니다.")

            # 5. 추천 배관 사이즈 제안 (Auto Sizing)
            st.markdown("---")
            with st.expander("💡 **[AI 추천] 적정 배관 사이즈 찾기**", expanded=True):
                # 1.5 ~ 2.0 m/s가 되도록 역산
                target_v = 1.8 # m/s
                req_area = (flow_m3 / 3600) / target_v
                req_d_mm = math.sqrt(req_area / math.pi) * 2000
                
                # DB에서 가장 가까운 큰 사이즈 찾기
                best_size = "N/A"
                for size, specs in PIPE_DB.items():
                    if specs["SCH 40"] >= req_d_mm:
                        best_size = size
                        break
                
                c_rec1, c_rec2 = st.columns([1, 3])
                with c_rec1:
                    st.markdown(f"### 👉 추천: **{best_size}**")
                with c_rec2:
                    st.caption(f"경제적 유속(1.8 m/s) 기준 계산된 최소 내경은 **{req_d_mm:.1f} mm** 입니다.")
                    st.caption(f"현재 선택된 **{size_sel}** (내경 {real_id_mm}mm)와 비교해 보십시오.")
# ==============================================================================
# [Module 6] Chemical Database (영업사원 맞춤형 화면)
# ==============================================================================
elif "Chemical Database" in program_mode:
    st.title("💊 종합 약품 정보 & 영업 가이드")
    st.caption("💡 영업사원 필독: 제품별 핵심 세일즈 포인트와 현장 기술 팁을 확인하세요.")
    st.markdown("---")
    
    # 이미 2단계에서 로드한 df_master 데이터를 사용합니다.
    if not df_master.empty:
        # 1. 검색 및 필터링
        col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
        
        with col_s1:
            search_keyword = st.text_input("🔍 통합 검색", placeholder="예: 308, 아연, 스케일, 카보, DBNPA")
        with col_s2:
            system_list = sorted(df_master['System'].unique().tolist())
            selected_system = st.multiselect("설비", system_list, default=system_list)
        with col_s3:
            type_list = sorted(df_master['Type'].unique().tolist())
            selected_type = st.multiselect("용도", type_list, default=type_list)

        # 2. 데이터 필터링 로직
        df_view = df_master[
            (df_master['System'].isin(selected_system)) & 
            (df_master['Type'].isin(selected_type))
        ]
        
        if search_keyword:
            mask = df_view.astype(str).apply(lambda x: x.str.contains(search_keyword, case=False, na=False)).any(axis=1)
            df_view = df_view[mask]

        st.info(f"📋 검색 결과: 총 **{len(df_view)}** 건")

        # 3. [핵심] 리스트 뷰 vs 상세 카드 뷰 자동 전환
        
        # (A) 결과가 많을 때 (5개 초과) -> 엑셀처럼 표로 보여줌
        if len(df_view) > 5:
            st.dataframe(
                df_view,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "System": st.column_config.TextColumn("설비", width="small"),
                    "Name": st.column_config.TextColumn("제품명", width="medium"),
                    "Main_Ingredient": st.column_config.TextColumn("🧪 주요 성분", width="large"),
                    "Sales_Point": st.column_config.TextColumn("💰 영업 포인트", width="large"),
                    "Dosage": st.column_config.NumberColumn("주입량", format="%d ppm"),
                }
            )
            st.caption("👇 검색 결과가 5개 이하가 되면 '상세 가이드 모드'가 열립니다.")

        # (B) 결과가 적을 때 (5개 이하) -> 영업사원용 '상세 카드' 보여줌
        else:
            for index, row in df_view.iterrows():
                # 제품마다 카드를 펼쳐서 보여줍니다.
                with st.expander(f"📌 **{row['Name']}** ({row['Desc']})", expanded=True):
                    
                    # [기본 정보]
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**🧪 주성분 (Recipe):**")
                        # 성분을 눈에 띄게 회색 박스 안에 표시
                        st.code(row['Main_Ingredient'], language=None) 
                    with c2:
                        st.markdown(f"**🎯 적용 대상:** {row['Target']}")
                        st.markdown(f"**💧 표준 주입량:** {row['Dosage']} ppm")
                        st.markdown(f"**📏 관리 기준:** {row['Criteria']}")

                    st.markdown("---")

                    # [영업 & 기술 핵심 정보] -> 여기가 영업사원에게 가장 중요한 부분입니다.
                    
                    # 1. 세일즈 포인트 (초록색 박스)
                    st.success(f"**🗣️ Sales Point (고객에게 이렇게 말하세요):**\n\n{row['Sales_Point']}")
                    
                    # 2. 필드 팁 (파란색/노란색 박스)
                    st.info(f"**🔧 Field Tip (엔지니어 주의사항):**\n\n{row['Field_Tip']}")

    else:
        st.warning("데이터를 불러오지 못했습니다. chemical_db.xlsx 파일을 확인하세요.")