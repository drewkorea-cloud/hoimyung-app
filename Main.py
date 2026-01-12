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



# [스타일] CSS 스타일 정의

st.markdown("""

    <style>

    .metric-card {

        background-color: #F8F9F9;

        border: 1px solid #E5E8E8;

        padding: 15px;

        border-radius: 8px;

        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);

    }

    .report-box {

        background-color: #f0f2f6;

        border-left: 5px solid #ff4b4b;

        padding: 15px;

        margin-top: 10px;

        border-radius: 5px;

    }

    </style>

    """, unsafe_allow_html=True)


# ==============================================================================
# [DATA] 데이터베이스 (수정됨: 괄호 닫힘 오류 해결 및 데이터 보강)
# ==============================================================================
PRODUCT_CATALOG = {
    'Cooling': {
        'Main_Inhibitor': [
            {'Name': 'DREW 11-635', 'Type': 'All-Organic', 'LSI_Range': [2.5, 3.2], 'Dosage': 90.0, 'Feature': '고농축/고알칼리 수질용 All-Organic (Azole 함유)'},
            {'Name': 'DREW 11-635A', 'Type': 'All-Organic', 'LSI_Range': [2.5, 3.2], 'Dosage': 60.0, 'Feature': '고농축용 All-Organic (Azole 미함유)'},
            {'Name': 'DREWGARD 308', 'Type': 'All-Organic', 'LSI_Range': [2.0, 3.0], 'Dosage': 125.0, 'Feature': 'Max pH 9.2 대응, 우수한 스케일/방식 능력'},
            {'Name': 'DREW 2305 (High)', 'Type': 'Millennium', 'LSI_Range': [1.5, 2.5], 'Dosage': 150.0, 'Feature': 'Millennium High Series, 고부하 현장 최적화'},
            {'Name': 'DREW 2210 (Mid)', 'Type': 'Millennium', 'LSI_Range': [0.5, 1.8], 'Dosage': 100.0, 'Feature': 'Millennium Mid-Range, 표준 수질 및 방식 제어'},
            {'Name': 'DREW 2105 (Lean)', 'Type': 'Millennium', 'LSI_Range': [-0.5, 1.0], 'Dosage': 60.0, 'Feature': 'Millennium Lean Series, 저농축/경제형 방식 처리'},
            {'Name': 'PERFORMAX 2021A', 'Type': 'Stab-Phos', 'LSI_Range': [-0.5, 1.5], 'Dosage': 100.0, 'Feature': '안정화 인산염계 표준 제품'},
            {'Name': 'PERFORMAX 2525', 'Type': 'Stab-Phos', 'LSI_Range': [-0.5, 1.2], 'Dosage': 135.0, 'Feature': '강력한 방식 능력이 요구되는 연수/저경도 보충수용'}
        ],
        'Dispersant': [
            {'Name': 'DREWSPERSE 744', 'Target': 'Iron', 'Dosage': 50.0, 'Feature': '철(Iron Oxide) 및 망간 분산 특화'},
            {'Name': 'DREWSPERSE 739', 'Target': 'Oil', 'Dosage': 50.0, 'Feature': '유분(Oil) 및 유기물 분산 제거'},
            {'Name': 'PERFORMAX 405', 'Target': 'Biofilm', 'Dosage': 50.0, 'Feature': '바이오필름(Bio-slime) 점착 방지'},
            {'Name': 'DREWSPERSE 747', 'Target': 'CaCO3', 'Dosage': 50.0, 'Feature': '탄산칼슘 스케일 강력 분산'}
        ],
        'Biocide': [
            {'Name': 'BioOX-1000', 'Type': 'Oxidizing', 'Dosage': 50.0, 'Feature': '산화성 살균제 (염소계)'},
            {'Name': 'BioNox-250', 'Type': 'Non-Oxidizing', 'Dosage': 100.0, 'Feature': '비산화성 살균제 (슬라임 제거)'}
        ]
    },
    'Boiler': {
        'Oxygen_Scavenger': [
            {'Name': 'HBS-100 (Sulfite)', 'Desc': '표준 아황산염계 (저압용)', 'Dosage': 20.0},
            {'Name': 'MBB-8760 (Hydrazine)', 'Desc': '하이드라진 대체/고압용', 'Dosage': 10.0}
        ],
        'Scale_Disp': [
            {'Name': 'HBP-Standard', 'Desc': '표준 인산염계 청관제', 'Dosage': 30.0}
        ]
    },
    'RO': {
        'Antiscalant': [
            {'Name': 'MDC-220 (General)', 'Desc': '범용 탄산칼슘/황산염 제어', 'Dosage': 3.0, 'Target': ['LSI', 'CaSO4']},
            {'Name': 'MDC-700 (High Silica)', 'Desc': '실리카 200ppm 대응/강력 분산', 'Dosage': 5.0, 'Target': ['SiO2']},
            {'Name': 'MDC-150 (Struvite)', 'Desc': '폐수 재이용/인산염/스트루바이트 제어', 'Dosage': 6.0, 'Target': ['Struvite', 'CaPO4']},
            {'Name': 'MDC-754 (High Sulfate)', 'Desc': 'BaSO4, SrSO4 특화 (황산바륨 제어)', 'Dosage': 4.0, 'Target': ['BaSO4', 'SrSO4']}
        ]
    }
}
# ==========================================
# [엔진 1] RO 화학 엔진 (Winflows Argo Analyzer 수준으로 고도화)
# ==========================================
class RO_Chemistry_Engine:
    def __init__(self):
        pass # Ksp 데이터는 계산식 내장

    def get_interpolated_k(self, temp_c, column_name):
         # 호환성을 위해 남겨둔 더미 함수 (사용 안함)
         return 0.0

    def calculate_saturation(self, inputs):
        try:
            # 1. 입력값 파싱 (기본값 방어 로직)
            pH = float(inputs.get('pH', 7.5))
            Temp = float(inputs.get('Temp', 25.0))
            TDS = float(inputs.get('TDS', 500.0))
            
            # 이온 농도 (Winflows 필수 인자)
            Ca = float(inputs.get('Ca', 100.0))
            Mg = float(inputs.get('Mg', 20.0))
            Na = float(inputs.get('Na', 100.0))
            HCO3 = float(inputs.get('HCO3', 100.0)) # M-Alk 대신 HCO3 사용 권장
            SO4 = float(inputs.get('SO4', 50.0))
            Cl = float(inputs.get('Cl', 100.0))
            SiO2 = float(inputs.get('SiO2', 10.0))
            
            # [신규] 특수 이온 (없으면 0 처리)
            Ba = float(inputs.get('Ba', 0.05)) # 바륨
            Sr = float(inputs.get('Sr', 0.5))  # 스트론튬
            PO4 = float(inputs.get('PO4', 0.1)) # 인산염 (Struvite용)
            NH4 = float(inputs.get('NH4', 0.1)) # 암모니아 (Struvite용)
            F = float(inputs.get('F', 0.1))     # 불소 (CaF2용)

            # 2. 이온 강도(Ionic Strength) 보정 계수
            IS = 2.5e-5 * TDS # 약식 계산
            f_monovalent = 10 ** (-0.5 * (IS**0.5) / (1 + (IS**0.5))) # 활동도 계수

            # 3. 주요 스케일 지수 계산 (Winflows Logic)
            
            # (1) LSI (Langelier) - 기존 유지 및 보완
            pCa = -math.log10(max(Ca, 0.1) / 40.08)
            pAlk = -math.log10(max(HCO3, 0.1) / 61.01)
            C_factor = math.log10(max(TDS, 10)) - 1
            pHs = (9.3 + 2.5) + C_factor - (13.12 * math.log10(Temp + 273)) - pCa - pAlk
            lsi = pH - pHs

            # (2) CaSO4 (Gypsum) Saturation
            # Ksp = 4.93e-5 (at 25C)
            IAP_CaSO4 = (Ca/40.08) * (SO4/96.06) * (f_monovalent**4) * 1e-6
            Ksp_CaSO4 = 4.93e-5
            sat_caso4 = (IAP_CaSO4 / Ksp_CaSO4) * 100

            # (3) SiO2 (Silica) Saturation
            solubility_sio2 = 120 + (Temp - 25) * 2
            sat_sio2 = (SiO2 / solubility_sio2) * 100

            # --- [신규 추가된 Winflows 정밀 항목] ---

            # (4) BaSO4 (Barium Sulfate) - 가장 난용성 스케일
            # Ksp = 1.08e-10
            IAP_BaSO4 = (Ba/137.3) * (SO4/96.06) * 1e-6
            Ksp_BaSO4 = 1.08e-10
            sat_baso4 = (IAP_BaSO4 / Ksp_BaSO4) * 100

            # (5) SrSO4 (Strontium Sulfate)
            # Ksp = 3.44e-7
            IAP_SrSO4 = (Sr/87.62) * (SO4/96.06) * 1e-6
            Ksp_SrSO4 = 3.44e-7
            sat_srso4 = (IAP_SrSO4 / Ksp_SrSO4) * 100

            # (6) CaF2 (Fluorite)
            IAP_CaF2 = (Ca/40.08) * ((F/19.0)**2) * 1e-9
            Ksp_CaF2 = 3.45e-11
            sat_caf2 = (IAP_CaF2 / Ksp_CaF2) * 100

            # (7) Struvite (MgNH4PO4) - 폐수 재이용 시 치명적
            # Ksp = 2.5e-13 (pH 의존성 큼, 약식)
            if NH4 > 0.5 and PO4 > 1.0:
                struvite_risk = (Mg * NH4 * PO4) / 1000.0 # 간이 지수
                if pH > 8.0: struvite_risk *= 5
            else:
                struvite_risk = 0

            # 4. 진단 및 처방 (Diagnosis & Prescription)
            status = "안정 (Stable)"
            solution = "수질 상태 양호. 범용 약품(MDC-220) 표준 주입 권장."
            warnings = []

            if lsi > 1.5: warnings.append("LSI 높음(CaCO3)")
            if sat_caso4 > 200: warnings.append("CaSO4 위험")
            if sat_baso4 > 100: warnings.append("BaSO4(바륨) 위험") # 케미칼 업체가 꼭 잡아야 함
            if sat_sio2 > 120: warnings.append("실리카 위험")
            if struvite_risk > 10: warnings.append("스트루바이트 위험")

            if warnings:
                status = f"⚠️ 경고: {', '.join(warnings)}"
                
                # 케미칼 전문가 다운 처방 로직
                if "BaSO4" in status or "SrSO4" in status:
                    solution = "난용성 황산염 스케일 감지! 특수 분산제 [MDC-754] 사용 필수."
                elif "실리카" in status:
                    solution = "실리카 중합 위험. 고분산제 [MDC-700]으로 교체 및 회수율 제한."
                elif "스트루바이트" in status:
                    solution = "인산염/암모니아 스케일. [MDC-150] 적용 및 pH 7.0 이하 운전 권장."
                elif "LSI" in status:
                    solution = "탄산칼슘 석출 우려. 산(Acid) 주입 또는 범용 [MDC-220] 증량."

            return {
                "LSI": round(lsi, 2),
                "Sat_CaSO4": round(sat_caso4, 0),
                "Sat_BaSO4": round(sat_baso4, 0), # New
                "Sat_SrSO4": round(sat_srso4, 0), # New
                "Sat_SiO2": round(sat_sio2, 0),
                "Sat_CaF2": round(sat_caf2, 0),   # New
                "Status": status,
                "Solution": solution,
                "Success": True
            }

        except Exception as e:
            return {"Success": False, "Error": str(e), "Status": "Error", "Solution": "Check Input Data"}

# ==========================================

# [엔진 2] 보일러 전문가 엔진 (원본 유지)

# ==========================================

class Boiler_Expert_Engine:

    @staticmethod

    def get_steam_enthalpy(pressure_bar):

        try:

            p = max(pressure_bar, 1.0)

            ts = 179.32 * (p ** 0.239) 

            h_steam = 665 + 0.3 * ts    

            return round(ts, 1), round(h_steam, 1)

        except:

            return 100.0, 640.0



    @staticmethod

    def check_asme_standard(pressure_bar, tds, silica, alk):

        limit_tds, limit_sio2, limit_alk = 3000, 150, 500

        

        if pressure_bar <= 20: limit_tds, limit_sio2, limit_alk = 3500, 150, 700

        elif pressure_bar <= 30: limit_tds, limit_sio2, limit_alk = 3000, 90, 600

        elif pressure_bar <= 40: limit_tds, limit_sio2, limit_alk = 2500, 40, 500

        elif pressure_bar <= 60: limit_tds, limit_sio2, limit_alk = 2000, 20, 400

        else: limit_tds, limit_sio2, limit_alk = 1500, 8, 200



        msgs = []

        if tds > limit_tds: msgs.append(f"🔴 전도도 초과 (기준 {limit_tds} ppm)")

        if silica > limit_sio2: msgs.append(f"🔴 실리카 초과 (기준 {limit_sio2} ppm)")

        if alk > limit_alk: msgs.append(f"⚠️ 알칼리도 높음 (기준 {limit_alk} ppm)")

        

        if not msgs: return "✅ ASME 기준 만족 (Safe)", limit_tds

        else: return ", ".join(msgs), limit_tds



# ==============================================================================

# [CORE ENGINE] 파커 진단 로직 Helper (원본 유지)

# ==============================================================================

class ParkerAI:

    @staticmethod

    def calculate_roi_cooling(makeup_flow, cycles, water_cost=1500):

        if cycles <= 3.0: return 0, 0

        evap = makeup_flow * (1 - 1/cycles)

        base_makeup = evap * (3.0 / (3.0 - 1))

        saved_water = base_makeup - makeup_flow

        return saved_water, saved_water * 24 * 300 * water_cost 



    @staticmethod

    def diagnose_boiler(ph, cond, cl, fe):

        msgs = []

        if ph < 10.5: msgs.append(("🔴", "pH 낮음", "산부식 발생 위험 높음."))

        elif ph > 11.8: msgs.append(("🟡", "pH 높음", "가성취화 우려."))

        if cond > 4000: msgs.append(("🔴", "전도도 초과", "캐리오버 위험."))

        if not msgs: msgs.append(("✅", "정상", "관리 상태 양호."))

        return msgs



    @staticmethod

    def diagnose_ro(flow_ratio, diff_press):

        msgs = []

        if flow_ratio < 85: msgs.append(("🔴", "생산량 저하", f"효율 {flow_ratio}% -> Fouling 심각."))

        if diff_press > 1.5: msgs.append(("⚠️", "차압 상승", f"Delta P {diff_press} bar -> 필터/스케일 확인."))

        if not msgs: msgs.append(("✅", "정상", "RO 운전 상태 양호."))

        return msgs



    @staticmethod

    def diagnose_waste(cod_raw, cod_out, target_cod):

        msgs = []

        if cod_out > target_cod: msgs.append(("🔴", "방류 기준 초과", f"현재 {cod_out} ppm."))

        else: msgs.append(("✅", "기준 만족", "안정적."))

        return msgs



def calculate_indices_advanced(ph, temp_c, tds, ca_ppm, alk_ppm, cl_ppm, so4_ppm):

    try:

        val_A = (math.log10(max(tds,1)) - 1) / 10

        val_B = -13.12 * math.log10(temp_c + 273.15) + 34.55

        val_C = math.log10(max(ca_ppm, 0.1)) - 0.4

        val_D = math.log10(max(alk_ppm, 0.1))

        phs = (9.3 + val_A + val_B) - (val_C + val_D)

        lsi = ph - phs

        ls_index = (cl_ppm + so4_ppm) / max(alk_ppm, 1)

        return lsi, 2*phs - (1.465*math.log10(max(alk_ppm,1)) + 4.54), ls_index

    except: return -9.9, -9.9, 0



def predict_corrosion_mpy(lsi, cl_ppm, velocity_ms, temp_c):

    base_mpy = 2.0 

    if lsi < -0.5: base_mpy += 3.0

    if cl_ppm > 500: base_mpy += 2.0

    return base_mpy, base_mpy * 0.1 



def analyze_deposit(comp_dict):

    ca = comp_dict.get("Calcium (CaO)", 0)

    si = comp_dict.get("Silica (SiO2)", 0)

    if ca > 30: return "탄산칼슘 (CaCO3)", "LSI 높음"

    if si > 20: return "실리카 (Silica)", "실리카 농도 초과"

    return "복합 오염물", "원인 분석 필요"



def create_gauge(value, title, min_v, max_v, steps):

    fig = go.Figure(go.Indicator(

        mode="gauge+number", value=value, title={'text': title},

        gauge={'axis': {'range': [min_v, max_v]}, 'steps': steps, 'bar': {'color': "#2E86C1"}}

    ))

    fig.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=20))

    return fig



# --- 2. 사이드바 메뉴 ---

with st.sidebar:

    st.title("💧 HOIMYUNG")

    st.subheader("Water Master Pro")

    program_mode = st.radio("Select Module:", ["1. Cooling Expert", "2. Boiler Master", "3. RO Master Pro", "4. Wastewater Reuse"], key="main_menu_mode")

    st.markdown("---")

    st.info("💡 **Tip:** 값을 입력하고 '적용' 버튼을 누르면 AI 진단이 시작됩니다.")

    st.caption("Authorized by **Parker**")

# ==============================================================================
# [Module 1] Cooling Expert (냉각수: 들여쓰기 및 문법 오류 수정 완료)
# ==============================================================================
if "Cooling" in program_mode:  # [수정] 첫 번째 모듈이므로 elif가 아니라 if를 써야 합니다.
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
            'Component': ['LOI (550°C)', 'Calcium (CaO)', 'Magnesium (MgO)', 'Iron (Fe2O3)', 'Aluminium (Al2O3)', 'Silica (SiO2)', 'Phosphate (P2O5)', 'Sulfate (SO4)'], 
            'Result (%)': [28.02, 0.10, 0.05, 0.23, 45.49, 1.53, 0.10, 23.48]
        })

    st.title("❄️ Cooling Tower Master (Global Expert Ver.)")
    st.info("Scale/Corrosion/Deposit 통합 진단 및 성분 분석 시스템")

    # 4개 탭 구조
    tab1, tab2, tab3, tab4 = st.tabs([
        "💧 Water Balance (물질수지)", 
        "⚗️ Water Chemistry (수질진단)", 
        "💊 Chemical Program (약품)", 
        "🔬 Lab & Troubleshooting (성분분석)"
    ])

    # ======================================================================
    # Tab 1: Water Balance (기존 유지)
    # ======================================================================
    with tab1:
        st.subheader("1. Cooling Tower Design Data")
        col1, col2 = st.columns(2)
        with col1:
            circ_rate = st.number_input("Circulation Rate (순환수량, m3/hr)", value=1000.0)
            delta_t = st.number_input("Delta T (온도차, °C)", value=5.0)
        with col2:
            coc = st.slider("Cycles of Concentration (농축배수)", 1.0, 10.0, 5.0)
            holding_vol = st.number_input("System Volume (보유수량, m3)", value=300.0)

        # 계산 로직
        evap = circ_rate * delta_t * 0.00153 
        windage = circ_rate * 0.0005        
        
        if coc > 1:
            blowdown = (evap / (coc - 1)) - windage
            if blowdown < 0: blowdown = 0 
        else: 
            blowdown = 0 
        
        makeup = evap + blowdown + windage 
        
        if blowdown > 0: 
            hti = 0.693 * holding_vol / (blowdown + windage) 
        else: 
            hti = 999.9

        st.markdown("---")
        # [시각화] 도넛 차트
        c_chart, c_metric = st.columns([1, 1])
        with c_chart:
            labels = ['Evaporation (증발)', 'Blowdown (배수)', 'Windage (비산)']
            values = [evap, blowdown, windage]
            fig_bal = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker_colors=['#3498DB', '#E74C3C', '#95A5A6'])])
            fig_bal.update_layout(title_text="Water Usage Breakdown", height=300, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig_bal, use_container_width=True)

        with c_metric:
            st.subheader("📊 Operation Summary")
            st.metric("보급수량 (Total Make-up)", f"{makeup:.1f} m³/hr")
            st.metric("배수량 (Blowdown)", f"{blowdown:.1f} m³/hr")
            
            ht_msg = "✅ Good"
            ht_color = "normal"
            if hti > 48: 
                ht_msg = "⚠️ Long"
                ht_color = "inverse"
            elif hti < 4: 
                ht_msg = "⚠️ Short"
                ht_color = "inverse"
            
            st.metric("반감기 (Half Life)", f"{hti:.1f} hr", delta=ht_msg, delta_color=ht_color)

  # ======================================================================
    # Tab 2: Water Chemistry (수정됨: 중복 제거 및 상세 진단 통합)
    # ======================================================================
    with tab2:
        st.subheader("2. Prediction & Diagnosis Simulator")
        st.markdown("보충수(Make-up) 수질을 기반으로 농축 후 순환수 수질을 **예측**하고 **5대 지수**를 진단합니다.")

        # [입력 1] 보충수 수질 데이터 초기화
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
            
            # 산 주입 옵션
            use_acid = st.checkbox("Acid Feed (황산 주입)", value=False)
            if use_acid:
                target_ph = st.number_input("Target pH (Control)", 6.5, 8.5, 7.8, 0.1)
            else:
                est_ph = min(7.5 + math.log10(max(target_coc, 1)), 9.0)
                target_ph = st.number_input("Predicted pH (Natural)", value=round(est_ph, 2), disabled=True)
            
            btn_run = st.button("🚀 Run Simulation (비교 분석)", type="primary", use_container_width=True)

        # [실행 로직]
        if btn_run:
            st.session_state.makeup_data = edited_mu 
            mu_dict = dict(zip(edited_mu['Item'], edited_mu['Value']))
            
            # 1. 농축 계산
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

            # 2. 지수 계산
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
            
            # 3. [비교 분석표] (보충수 vs 순환수 vs Limit)
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
            
            # 4. Limit 초과 자동 경보
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

            # ------------------------------------------------------------------
            # 5. 5대 핵심 지수 진단 (중복 없이 한 번만 표시)
            # ------------------------------------------------------------------
            st.markdown("#### 🧭 5대 핵심 지수 진단 (Indices Diagnosis)")
            
            # (1) 메트릭 카드 표시
            m1, m2, m3, m4, m5 = st.columns(5)
            
            # LSI
            lsi_col = "inverse" if lsi > 1.5 or lsi < 0 else "normal"
            m1.metric("1. LSI (Scale)", f"{lsi:.2f}", "Risk" if lsi>1.5 else "Safe", delta_color=lsi_col)
            
            # RSI
            rsi_state = "Stable"
            if rsi < 5.0: rsi_state = "Scale Risk"
            elif rsi > 8.5: rsi_state = "Corr Risk"
            m2.metric("2. RSI (General)", f"{rsi:.2f}", rsi_state, delta_color="inverse" if "Risk" in rsi_state else "normal")
            
            # PSI
            m3.metric("3. PSI (Stability)", f"{psi:.2f}")
            
            # Pitting
            ls_msg = "Safe"
            ls_col = "normal"
            if ls_idx > 1.2: ls_msg="Pitting!"; ls_col="inverse"
            m4.metric("4. Pitting (L-S)", f"{ls_idx:.2f}", ls_msg, delta_color=ls_col)
            
            # Deposit
            dep_msg = "Clean"
            dep_col = "normal"
            if sim_turbidity > 20: dep_msg="Deposit!"; dep_col="inverse"
            m5.metric("5. Deposit Risk", f"{sim_turbidity} NTU", dep_msg, delta_color=dep_col)

            # (2) 상세 해석 가이드 (Expander)
            st.divider()
            with st.expander("📘 지수별 상세 해석 및 가이드 (Click to Open)", expanded=True):
                col_guide1, col_guide2 = st.columns(2)
                
                with col_guide1:
                    st.markdown("### 🔍 현재 수질 정밀 분석")
                    
                    # LSI 분석
                    if lsi > 2.0:
                        st.error(f"**1. LSI ({lsi:.2f}) - 심각한 스케일:** 탄산칼슘이 배관에 두껍게 쌓일 위험이 높습니다. 산 주입 필수.")
                    elif lsi > 0.5:
                        st.warning(f"**1. LSI ({lsi:.2f}) - 스케일 경향:** 약한 스케일 생성 조건입니다. 방지제로 제어 가능합니다.")
                    elif lsi < -0.5:
                        st.warning(f"**1. LSI ({lsi:.2f}) - 부식 경향:** 물이 배관을 녹일 수 있습니다 (Corrosive).")
                    else:
                        st.success(f"**1. LSI ({lsi:.2f}) - 안정:** 스케일과 부식 균형이 잘 맞습니다.")

                    # RSI 분석
                    if rsi < 5.0:
                        st.error(f"**2. RSI ({rsi:.2f}) - 강한 스케일:** 5.0 미만은 열교환기 막힘의 주원인입니다.")
                    elif rsi > 7.5:
                        st.warning(f"**2. RSI ({rsi:.2f}) - 부식성:** 탄소강 배관 부식 주의. 방식제 농도를 높이십시오.")
                    else:
                        st.success(f"**2. RSI ({rsi:.2f}) - 안정 범위:** (6.0 ± 1.0) 범위를 만족합니다.")

                    # Pitting 분석
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
    # Tab 3: Chemical Program (기존 유지)
    # ======================================================================
    with tab3:
        st.subheader("3. Chemical Program Selection")
        try:
            chem_list = PRODUCT_CATALOG['Cooling']['Main_Inhibitor']
            chem_names = [c['Name'] for c in chem_list]
            sel_chem = st.selectbox("Select Inhibitor Model", chem_names)
            target_chem = next((item for item in chem_list if item['Name'] == sel_chem), None)
            if target_chem:
                st.info(f"**Selected:** {sel_chem} | **Type:** {target_chem['Type']} | **Dosage:** {target_chem['Dosage']} ppm")
                c1, c2 = st.columns(2)
                usage_kg_day = (makeup * target_chem['Dosage']) / 1000.0 * 24
                c1.metric("일일 사용량", f"{usage_kg_day:.1f} kg/day")
        except: 
            st.error("약품 데이터베이스(PRODUCT_CATALOG) 오류")
        
        st.markdown("### 🦠 Biocide Program")
        b1, b2 = st.columns(2)
        b1.checkbox("Oxidizing (염소계)", value=True)
        b2.checkbox("Non-Oxidizing (비산화성)", value=True)

    # ======================================================================
    # Tab 4: Lab Analysis & Trouble Shooting (기존 유지 + 그래프)
    # ======================================================================
    with tab4:
        st.header("🔬 Lab Analysis & Trouble Shooting")
        st.subheader("1. Deposit Composition Analysis (ICP/Lab Data)")
        
        with st.container(border=True):
            lc1, lc2, lc3, lc4, lc5 = st.columns(5)
            # st.session_state에 있는 값이나 기본값 사용
            def_vals = st.session_state.deposit_data['Result (%)'].tolist() if 'deposit_data' in st.session_state else [10.0, 40.0, 5.0, 2.0, 5.0]
            
            # 리스트 길이 안전장치
            if len(def_vals) < 8: def_vals = [10.0, 40.0, 5.0, 2.0, 5.0]

            fe = lc1.number_input("Fe (철분, %)", 0.0, 100.0, float(def_vals[3]))
            ca = lc2.number_input("Ca (칼슘, %)", 0.0, 100.0, float(def_vals[1]))
            sio2_dep = lc3.number_input("SiO2 (실리카, %)", 0.0, 100.0, float(def_vals[5]))
            p2o5 = lc4.number_input("P2O5 (인산염, %)", 0.0, 100.0, float(def_vals[6]))
            loi = lc5.number_input("LOI (유기물, %)", 0.0, 100.0, float(def_vals[0]))
        
        if st.button("🧪 Identify Deposit Type"):
            # 그래프
            c_lab_chart, c_lab_txt = st.columns([1, 1])
            with c_lab_chart:
                fig_lab = go.Figure(go.Bar(
                    x=[fe, ca, sio2_dep, p2o5, loi],
                    y=['Fe', 'Ca', 'SiO2', 'P2O5', 'LOI'],
                    orientation='h', marker=dict(color=['#E74C3C', '#ECF0F1', '#95A5A6', '#F1C40F', '#2ECC71'])
                ))
                fig_lab.update_layout(height=250, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_lab, use_container_width=True)
            
            with c_lab_txt:
                diagnosis = []
                if fe > 20.0: diagnosis.append("🔴 **[Corrosion]** 부식 생성물(녹)입니다.")
                if ca > 30.0: diagnosis.append("⚪ **[Scale]** 미네랄 스케일입니다.")
                if loi > 25.0: diagnosis.append("🟢 **[Bio-fouling]** 미생물 슬라임입니다.")
                
                if not diagnosis: st.write("복합 오염 또는 토사(Silt)입니다.")
                else: 
                    for d in diagnosis: st.write(d)
        
        st.divider()
        st.subheader("2. Symptom Based Diagnosis")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            issue = st.selectbox("발생 현상", ["열교환기 효율 저하", "순환수량 감소", "수조 거품 발생", "탁도 급상승"])
        with col_t2:
            check = st.selectbox("점검 사항", ["약품 농도 정상", "스트레이너 막힘", "Blowdown 밸브 닫힘"])
        
        if "효율" in issue: st.caption("👉 스케일/디포짓 의심. 위 성분 분석을 수행하십시오.")
        elif "거품" in issue: st.caption("👉 유기물 유입. 소포제 투입.")

# ==============================================================================

# [Module 2] Boiler Master Pro (전문가님 원본 코드 100% 유지)

# ==============================================================================

elif "Boiler" in program_mode:

    # --- 1. 데이터 초기화 (필수) ---

    if 'boiler_feed_data' not in st.session_state:

        st.session_state.boiler_feed_data = pd.DataFrame({

            'Item': ['pH', 'Cond (uS/cm)', 'Hardness (ppm)', 'Cl (ppm)', 'SiO2 (ppm)', 'M-Alk (ppm)', 'Fe (ppm)', 'Phosphate (PO4)'],

            'Feedwater': [8.5, 150.0, 1.0, 15.0, 2.0, 40.0, 0.05, 0.5]

        })

    

    if 'energy_data' not in st.session_state:

        st.session_state.energy_data = pd.DataFrame({

            'Parameter': ['Fuel Cost (KRW/m3)', 'Oper. Hours/Day', 'Make-up Temp (°C)', 'Condensate Temp (°C)'],

            'Value': [900.0, 24.0, 20.0, 85.0]

        })



    if 'boiler_results' not in st.session_state:

        st.session_state.boiler_results = None



    st.title("🔥 Boiler Master Pro")

    st.caption("Advanced Chemistry Simulation & Safety Diagnosis")



    # 탭 구성

    tab_sim, tab_chem_prog, tab_safety, tab_energy = st.tabs([

        "1. Water Simulation", "2. Chemical Program", "3. Na-PO4 Safety Map", "4. Energy Cost"

    ])

    

    # --------------------------------------------------------------------------

    # Tab 1: Water Simulation

    # --------------------------------------------------------------------------

    with tab_sim:

        with st.container(border=True):

            col_b1, col_b2 = st.columns([1, 1.5])

            with col_b1:

                st.subheader("1. Feedwater Quality")

                edited_bf = st.data_editor(st.session_state.boiler_feed_data, hide_index=True, key="bo_feed_editor")

            with col_b2:

                st.subheader("2. Operation Control")

                bo_press = st.slider("Steam Pressure (bar)", 5.0, 60.0, 10.0, key="bo_press")

                bo_cycles = st.slider("Target Cycles (N)", 1.0, 50.0, 15.0, key="bo_cycles")

                st.write("---")

                bo_steam = st.number_input("Steam Rate (ton/hr)", 10.0, key="bo_steam_rate")

                btn_sim = st.button("🔄 시뮬레이션 실행 (Run)", key="bo_btn_sim")



            if btn_sim:

                st.session_state.boiler_feed_data = edited_bf

                f_vals = dict(zip(edited_bf['Item'], edited_bf['Feedwater']))

                cycles = bo_cycles

                

                pred_cond = f_vals['Cond (uS/cm)'] * cycles

                pred_cl = f_vals['Cl (ppm)'] * cycles

                pred_sio2 = f_vals['SiO2 (ppm)'] * cycles

                pred_alk = f_vals['M-Alk (ppm)'] * cycles

                pred_fe = f_vals['Fe (ppm)'] * cycles

                pred_po4 = f_vals.get('Phosphate (PO4)', 0.0) * cycles

                

                _, limit_cond = Boiler_Expert_Engine.check_asme_standard(bo_press, pred_cond, pred_sio2, pred_alk)

                

                bw_data = {

                    'Parameter': ['Conductivity', 'Silica (SiO2)', 'Chloride (Cl)', 'M-Alkalinity', 'Iron (Fe)', 'Phosphate (PO4)'],

                    'Feed (급수)': [f_vals['Cond (uS/cm)'], f_vals['SiO2 (ppm)'], f_vals['Cl (ppm)'], f_vals['M-Alk (ppm)'], f_vals['Fe (ppm)'], f_vals.get('Phosphate (PO4)', 0)],

                    'Boiler (예상)': [pred_cond, pred_sio2, pred_cl, pred_alk, pred_fe, pred_po4],

                    'ASME Limit': [limit_cond, "Depends on P", "-", "-", "-", "-"]

                }

                

                st.session_state.boiler_results = {

                    'cycles': cycles, 'press': bo_press, 'steam': bo_steam,

                    'pred_cond': pred_cond, 'limit_cond': limit_cond,

                    'pred_sio2': pred_sio2, 'table': pd.DataFrame(bw_data)

                }



            if st.session_state.boiler_results:

                res = st.session_state.boiler_results

                st.divider()

                st.subheader("💧 Boiler Water Quality Prediction")

                m1, m2, m3 = st.columns(3)

                m1.metric("Target Cycles", f"{res['cycles']:.1f} N")

                m2.metric("Predicted TDS", f"{res['pred_cond']:.0f} uS/cm", delta="Limit Over" if res['pred_cond'] > res['limit_cond'] else "Safe", delta_color="inverse")

                m3.metric("Predicted Silica", f"{res['pred_sio2']:.1f} ppm")

                st.dataframe(res['table'].style.format("{:.1f}", subset=['Feed (급수)', 'Boiler (예상)']), hide_index=True, use_container_width=True)



    # --------------------------------------------------------------------------

    # Tab 2: Chemical Program

    # --------------------------------------------------------------------------

    with tab_chem_prog:

        st.subheader("💊 Chemical Treatment Program")

        

        stm = st.session_state.boiler_results['steam'] if st.session_state.boiler_results else 10.0

        

        c1, c2 = st.columns(2)

        with c1:

            sel_oxy = st.selectbox("Oxygen Scavenger (탈산제)", [p['Name'] for p in PRODUCT_CATALOG['Boiler']['Oxygen_Scavenger']], key="bo_chem_oxy")

            st.info(f"선택 제품: **{sel_oxy}**")

        with c2:

            sel_scale = st.selectbox("Scale Inhibitor (청관제)", [p['Name'] for p in PRODUCT_CATALOG['Boiler']['Scale_Disp']], key="bo_chem_scale")

            st.success(f"선택 제품: **{sel_scale}**")

        

        feed_flow_est = stm * 1.1 

        dos1 = feed_flow_est * 24 * 20 / 1000 

        dos2 = feed_flow_est * 24 * 30 / 1000 

        

        st.write("---")

        st.markdown(f"#### 📊 일일 예상 사용량 (Feed {feed_flow_est:.1f} ton/hr 기준)")

        

        dos_df = pd.DataFrame({

            'Product': [sel_oxy, sel_scale],

            'Dosing (kg/day)': [dos1, dos2]

        })

        fig_bar = px.bar(dos_df, x='Product', y='Dosing (kg/day)', color='Product', text_auto='.1f')

        st.plotly_chart(fig_bar, use_container_width=True)



    # --------------------------------------------------------------------------

    # Tab 3: Na-PO4 Safety Map

    # --------------------------------------------------------------------------

    with tab_safety:

        st.subheader("🧪 Na-PO4 Coordinate Map")

        st.caption("Caustic Gouging & Acidic Corrosion Risk Diagnosis")

        

        col_s1, col_s2 = st.columns([1, 2])

        

        with col_s1:

            with st.container(border=True):

                st.markdown("**현재 관수(Boiler Water) 상태**")

                cur_ph = st.number_input("Current pH", 8.0, 13.0, 10.5, 0.1, key="bo_safe_ph")

                cur_po4 = st.number_input("Current PO4 (ppm)", 0.0, 100.0, 20.0, 1.0, key="bo_safe_po4")

                st.info("※ 시뮬레이션 값이 아닌, 실제 측정값을 입력하여 진단합니다.")



        with col_s2:

            fig_map = go.Figure()

            

            # Safe Zone

            fig_map.add_shape(type="rect", x0=10, y0=9.4, x1=40, y1=10.5,

                              line=dict(color="Green"), fillcolor="rgba(0, 255, 0, 0.1)")

            fig_map.add_annotation(x=25, y=10.0, text="Safe Zone", showarrow=False, font=dict(color="green"))



            # Limits using numpy

            x_range = np.linspace(0, 60, 100)

            y_upper = 11.6 - (x_range * 0.025)

            y_lower = 9.0 - (x_range * 0.01)

            

            fig_map.add_trace(go.Scatter(x=x_range, y=y_upper, mode='lines', name='Caustic Limit', line=dict(color='red', dash='dash')))

            fig_map.add_trace(go.Scatter(x=x_range, y=y_lower, mode='lines', name='Acidic Limit', line=dict(color='orange', dash='dash')))



            # Point

            status_color = "green"

            status_msg = "Safe"

            

            limit_up = 11.6 - (cur_po4 * 0.025)

            limit_down = 9.0 - (cur_po4 * 0.01)

            

            if cur_ph > limit_up:

                status_color = "red"; status_msg = "Caustic Risk"

            elif cur_ph < limit_down:

                status_color = "orange"; status_msg = "Acidic Risk"

            

            fig_map.add_trace(go.Scatter(

                x=[cur_po4], y=[cur_ph],

                mode='markers+text',

                marker=dict(size=18, color=status_color, symbol='x'),

                text=[status_msg], textposition="top right",

                name='Current Point'

            ))



            fig_map.update_layout(

                title="Na-PO4 Safety Map",

                xaxis_title="Phosphate (PO4, ppm)", yaxis_title="pH",

                xaxis=dict(range=[0, 60]), yaxis=dict(range=[8.0, 12.5]),

                height=450

            )

            st.plotly_chart(fig_map, use_container_width=True)

            

            if status_color == "red":

                st.error("🚨 **위험:** pH가 너무 높습니다. **알칼리 부식(Caustic Gouging)**이 우려됩니다. 인산염을 투입하여 pH를 낮추십시오.")

            elif status_color == "orange":

                st.warning("⚠️ **주의:** pH가 너무 낮습니다. **산성 부식** 가능성이 있습니다.")

            else:

                st.success("✅ **양호:** 적절한 Phosphate 처리 영역에 있습니다.")



    # --------------------------------------------------------------------------

    # Tab 4: Energy Cost

    # --------------------------------------------------------------------------

    with tab_energy:

        st.subheader("💸 Steam Cost Analysis")

        col_e1, col_e2 = st.columns([1, 1.5])

        

        with col_e1:

            edited_energy = st.data_editor(st.session_state.energy_data, hide_index=True, key="bo_energy_edit")

        

        with col_e2:

            e_vals = dict(zip(edited_energy['Parameter'], edited_energy['Value']))

            

            if st.session_state.boiler_results:

                p_bar = st.session_state.boiler_results['press']

                stm_val = st.session_state.boiler_results['steam']

            else:

                p_bar = 10.0 

                stm_val = 10.0

            

            try: sat_t, h_steam = Boiler_Expert_Engine.get_steam_enthalpy(p_bar)

            except: sat_t, h_steam = 180.0, 665.0

            

            t_feed = e_vals['Make-up Temp (°C)']

            fuel_cost = e_vals['Fuel Cost (KRW/m3)']

            

            req_kcal = stm_val * 1000 * (h_steam - t_feed)

            req_fuel = req_kcal / (9500 * 0.9)

            cost_hourly = req_fuel * fuel_cost

            

            with st.container(border=True):

                st.metric("Hourly Steam Cost", f"{int(cost_hourly):,} KRW/hr")

                st.caption(f"Based on: {stm_val} ton/hr, {p_bar} bar, Feed {t_feed}°C")

            

            st.info(f"💡 현재 조건에서 스팀 1톤 생산 단가는 약 **{int(cost_hourly/stm_val):,}원** 입니다.")



# ==============================================================================

# [Module 3] RO Master Pro (전문가님 원본 코드 100% 유지)

# ==============================================================================
elif program_mode == "3. RO Master Pro":
        st.title("💧 RO Master Pro (Global Expert Ver.)")
        st.info("Global Chemical사(Nalco/Solenis 등) 수준의 정밀 진단 및 CIP 솔루션 모듈입니다.")

        # [수정] 5개 탭으로 확장 (전문가 기능 4개 + 기존 CIP 기능 1개)
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🛠 System Design", 
            "⚗️ Chemical Projection", 
            "📈 Smart Operation", 
            "🕵️ Autopsy & Trouble",
            "🧹 CIP Manager"  # 파트너님의 필수 기능 복구
        ])

        # --- Tab 1: 기본 설계 (수정됨: 단위 선택 및 Flux 현실화) ---
        with tab1:
            st.subheader("1. RO Design Configuration")
            
            # [수정 1] 유량 단위 선택 기능 추가 (시간당 vs 일일)
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                flow_unit = st.radio("유량 단위 선택 (Flow Unit)", ["m³/hr (시간당)", "m³/day (일일)"], horizontal=True)
            
            col1, col2 = st.columns(2)
            with col1:
                # 단위에 따라 라벨과 기본값 변경
                if "hr" in flow_unit:
                    flow_input = st.number_input("Permeate Flow (생산량)", value=50.0, help="시간당 생산량")
                    flow_m3_hr = flow_input
                else:
                    flow_input = st.number_input("Permeate Flow (생산량)", value=50.0, help="일일 생산량 (24hr 가동 기준)")
                    flow_m3_hr = flow_input / 24.0
                
                rec = st.slider("Target Recovery (회수율 %)", 50, 90, 75)
                
            with col2:
                temp = st.number_input("Design Temperature (°C)", value=25.0)
                
                # [수정 2] 수질 용도에 따른 Flux 가이드 제공
                app_type = st.selectbox("수질 용도 (Application)", 
                                      ["기수/공업용수 (BWRO)", "폐수 재이용 (WWRO)", "해수 담수 (SWRO)"])
                
                if "BWRO" in app_type:
                    rec_flux = 22.0 # 일반적인 공업용수 Flux
                    flux_guide = "20~25"
                elif "WWRO" in app_type:
                    rec_flux = 13.5 # 오염이 심한 폐수 Flux
                    flux_guide = "12~15"
                else:
                    rec_flux = 14.0 # 해수 Flux
                    flux_guide = "12~16"
                    
                flux = st.number_input(f"Avg Flux (lmh) - Guide: {flux_guide}", value=rec_flux)
            
            st.markdown("---")
            
            # [계산 로직]
            # 1. 필요 전체 면적 (m2) = (시간당 유량 L/hr) / Flux (L/m2/hr)
            total_area_req = (flow_m3_hr * 1000.0) / flux
            
            # 2. 8인치 표준 멤브레인 면적 (37m2 = 400ft2)
            element_area = 37.0 
            
            # 3. 필요 개수 산정
            qty = math.ceil(total_area_req / element_area)
            
            # [결과 표시]
            c1, c2, c3 = st.columns(3)
            c1.metric("Flow Rate (Converted)", f"{flow_m3_hr:.1f} m³/hr", f"{flow_m3_hr*24:.1f} m³/day")
            c2.metric("Design Flux", f"{flux} lmh")
            
            # 개수가 너무 적거나 많을 때 색상 강조
            qty_color = "normal"
            if qty > 100 and "day" in flow_unit: qty_color = "inverse" # 일일 50톤인데 100개면 경고
            
            c3.metric("Required Elements (8\")", f"{qty} ea", delta="Standard 400ft²", delta_color=qty_color)
            
            st.info(f"💡 **Calculation:** {flow_m3_hr:.1f} m³/hr 생산을 위해 {flux} lmh 유속으로 설계 시, 약 **{qty}개**의 8인치 멤브레인이 필요합니다.")

        # --- Tab 2: 정밀 케미칼 솔루션 (Winflows급 고도화) ---
        with tab2:
            st.subheader("2. Advanced Scale Prediction & Chemical Dosing")
            
            with st.expander("🧪 상세 수질 데이터 입력 (Water Analysis)", expanded=True):
                wc1, wc2, wc3, wc4 = st.columns(4)
                ph = wc1.number_input("pH", 7.0, 14.0, 8.0)
                tds = wc2.number_input("TDS (mg/L)", 0, 50000, 2000)
                temp_c = wc3.number_input("Temp (°C)", 0, 100, 25)
                
                wc1, wc2, wc3, wc4 = st.columns(4)
                ca = wc1.number_input("Ca (mg/L)", 0.0, 5000.0, 120.0)
                mg = wc2.number_input("Mg (mg/L)", 0.0, 5000.0, 30.0)
                hco3 = wc3.number_input("HCO3", 0.0, 5000.0, 150.0)
                so4 = wc4.number_input("SO4", 0.0, 5000.0, 200.0)
                
                wc1, wc2, wc3, wc4 = st.columns(4)
                sio2 = wc1.number_input("SiO2", 0.0, 200.0, 25.0)
                ba = wc2.number_input("Ba (Barium)", 0.0, 10.0, 0.05)
                sr = wc3.number_input("Sr (Strontium)", 0.0, 20.0, 0.5)
                f_ion = wc4.number_input("F (Fluoride)", 0.0, 10.0, 0.2)

            if st.button("🚀 Run Chemical Projection"):
                inputs = {
                    'pH': ph, 'Temp': temp_c, 'TDS': tds,
                    'Ca': ca, 'Mg': mg, 'HCO3': hco3, 'SO4': so4,
                    'SiO2': sio2, 'Ba': ba, 'Sr': sr, 'F': f_ion, 'Na': 100, 'Cl': 100
                }
                
                engine = RO_Chemistry_Engine() 
                res = engine.calculate_saturation(inputs)
                
                st.markdown("### 🔍 Projection Result")
                if "안정" in res['Status']:
                    st.success(f"Diagnostics: {res['Status']}")
                else:
                    st.error(f"Diagnostics: {res['Status']}")
                
                st.info(f"💊 **Prescription:** {res['Solution']}")

                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("LSI (CaCO3)", res['LSI'])
                mc2.metric("CaSO4 Sat(%)", f"{res['Sat_CaSO4']}%")
                mc3.metric("BaSO4 Sat(%)", f"{res['Sat_BaSO4']}%")
                mc4.metric("SiO2 Sat(%)", f"{res['Sat_SiO2']}%")

        # --- Tab 3: 스마트 운전 관리 (Normalization) ---
        with tab3:
            st.subheader("3. Operation Data Normalization (보정 운전)")
            st.markdown("ASTM D4516 표준에 따라 수온 변화를 보정하여 **진짜 막힘(Real Fouling)**을 진단합니다.")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### 📅 Reference (초기값)")
                ref_flow = st.number_input("초기 유량 (m3/hr)", value=50.0)
                ref_press = st.number_input("초기 압력 (bar)", value=15.0)
                ref_temp = st.number_input("초기 수온 (°C)", value=25.0)
            with col2:
                st.markdown("##### ⏱ Current (현재값)")
                curr_flow = st.number_input("현재 유량 (m3/hr)", value=42.0)
                curr_press = st.number_input("현재 압력 (bar)", value=16.5)
                curr_temp = st.number_input("현재 수온 (°C)", value=15.0)
            
            if st.button("📊 Analyze Performance"):
                tcf_ref = math.exp(2640 * (1/298 - 1/(273+ref_temp)))
                tcf_curr = math.exp(2640 * (1/298 - 1/(273+curr_temp)))
                norm_flow = curr_flow * (tcf_ref / tcf_curr) * (ref_press / curr_press)
                flow_change = ((norm_flow - ref_flow) / ref_flow) * 100
                
                st.markdown("---")
                c1, c2 = st.columns(2)
                c1.metric("보정된 유량", f"{norm_flow:.1f} m3/hr", f"{flow_change:.1f}%")
                
                if flow_change < -10:
                    c2.error("🚨 **CIP 시급:** 보정 유량이 10% 이상 감소했습니다.")
                elif flow_change < -5:
                    c2.warning("⚠️ **성능 저하:** 스케일 방지제 주입량을 점검하세요.")
                else:
                    c2.success("✅ **정상:** 유량 감소는 단순 수온 저하 때문입니다.")

        # --- Tab 4: 부검 및 트러블슈팅 ---
        with tab4:
            st.subheader("4. Membrane Autopsy & Troubleshooting")
            col1, col2 = st.columns(2)
            with col1:
                deposit_type = st.selectbox("오염물 성상", 
                                          ["갈색/점액질 (Biomass)", "단단한 결정 (Scaling)", "검은색 가루 (Metal Oxide)", "유기물/오일 (Organics)"])
            with col2:
                dp_loc = st.selectbox("차압 상승 위치", ["전단부 (Lead)", "후단부 (Tail)", "전체"])
            
            st.info("💡 **AI Expert Opinion:**")
            if "Biomass" in deposit_type or "전단부" in dp_loc:
                st.markdown("- **진단:** 미생물 오염 (Biofouling)\n- **처방:** pH 12 알칼리 세정 + 비산화성 살균제 충격 요법")
            elif "결정" in deposit_type or "후단부" in dp_loc:
                st.markdown("- **진단:** 무기물 스케일 (Scaling)\n- **처방:** pH 2 산 세정 + 회수율 하향 조정")
            elif "오일" in deposit_type:
                 st.markdown("- **진단:** 유분 오염\n- **처방:** 고온 알칼리 + 계면활성제 세정 (복구 어려움)")
            else:
                 st.markdown("현장 데이터를 더 수집해주십시오.")

        # --- Tab 5: CIP Manager (파트너님의 기존 코드 복구) ---
        with tab5:
            st.header("🧹 CIP (Clean-In-Place) Manager")
            st.caption("Standard Operation Procedure based on Manual")
            
            st.subheader("1. CIP 실시 기준 (Timing Criteria)")
            st.warning("""
            다음 현상 중 **하나라도** 발생하면 즉시 세정을 실시해야 합니다.
            * 📉 **생산수량 15% 감소** (정상 압력 기준)
            * 📈 **운전압력 15% 증가** (정상 생산량 기준)
            * 🧂 **염투과율(Salt Passage) 15% 증가** (생산수질 악화)
            """)
            
            st.divider()
            st.subheader("2. CIP 설비 용량 계산기 (Design Calculator)")
            with st.container():
                col_c1, col_c2 = st.columns(2)
                # 입력값을 직관적으로 수정
                cip_vessels = col_c1.number_input("1st Stage Vessels (Vessel 수)", value=5, min_value=1)
                
                # 계산 로직 유지
                cip_flow_req = cip_vessels * 8.0 
                cip_tank_req = (cip_flow_req * 0.06) + 1.0
                
                col_c2.metric("권장 CIP 펌프 유량", f"{cip_flow_req:.1f} m³/hr", help="8 inch Vessel 기준 (8m3/hr/vessel)")
                col_c2.metric("최소 CIP 탱크 용량", f"{cip_tank_req:.1f} m³", help="배관 및 베셀 보유수량 포함")

            st.divider()
            st.subheader("3. 약품 선정 및 세정 조건 (Chemicals)")
            cip_type = st.radio("세정 종류 선택", ["무기물 세정 (Scale)", "유기물 세정 (Organic)"], horizontal=True)
            
            if "무기물" in cip_type:
                st.success("🧪 **무기물 세정 (Acid Cleaning)**: 탄산칼슘, 금속 산화물 제거 (pH 2.0~3.0)")
            else:
                st.info("🦠 **유기물 세정 (Alkaline Cleaning)**: 미생물, 실리카 제거 (pH 11.0~12.0)")
            
            st.markdown(f"**💧 약품 희석 비율 (5% 기준):** 물 1m³ 당 약품 **50kg** 투입")

# ==============================================================================
# [Module 4] Wastewater Expert (설계 및 엔지니어링 기능 통합)
# ==============================================================================
elif "Wastewater" in program_mode:
    # 1. 초기 데이터 및 세션 설정
    if 'waste_data' not in st.session_state:
        st.session_state.waste_data = pd.DataFrame({
            'Parameter': ['pH', 'TDS (ppm)', 'SS (ppm)', 'COD (ppm)', 'Cl (ppm)', 'Hardness (Ca, ppm)', 'Oil & Grease (ppm)'],
            'Value': [7.2, 1200.0, 60.0, 150.0, 350.0, 400.0, 5.0]
        })

    st.title("♻️ Wastewater Reuse Engineering")
    st.info("공정 시뮬레이션 및 RO/AFM 설비 설계(Design Calculation) 통합 시스템")
    
    # 탭 확장: [시뮬레이션] [설계 계산] [약품 선정] [경제성 평가]
    tab_ww_sim, tab_ww_design, tab_ww_chem, tab_ww_roi = st.tabs([
        "1. Process Simulation", 
        "2. Equipment Design (RO/AFM)", 
        "3. Chemical Selection", 
        "4. ROI & Economics"
    ])

    # --------------------------------------------------------------------------
    # Tab 1: Process Simulation (기존 기능 유지 + 오류 수정)
    # --------------------------------------------------------------------------
    with tab_ww_sim:
        st.subheader("🏗️ Process Water Quality Prediction")
        col_s1, col_s2 = st.columns([1, 2])

        with col_s1:
            st.markdown("###### ① 원수 성상 입력 (Raw Water)")
            edited_waste = st.data_editor(st.session_state.waste_data, hide_index=True, key="ww_sim_editor")
            w_val = dict(zip(edited_waste['Parameter'], edited_waste['Value']))
            btn_run_sim = st.button("🚀 Run Simulation", key="ww_btn_sim_run", type="primary")

        with col_s2:
            if btn_run_sim:
                st.session_state.waste_data = edited_waste
                
                # 예측 로직 (기존 동일)
                curr_ss, curr_cod = w_val['SS (ppm)'], w_val['COD (ppm)']
                curr_oil, curr_tds = w_val['Oil & Grease (ppm)'], w_val['TDS (ppm)']
                curr_ca = w_val['Hardness (Ca, ppm)']
                
                applied_steps = ["Raw Water"]
                
                # DAF / Softening
                if curr_oil > 10 or curr_ss > 50:
                    applied_steps.append("DAF (가압부상)")
                    curr_ss *= 0.15; curr_cod *= 0.7; curr_oil *= 0.1
                elif curr_ca > 300:
                    applied_steps.append("Softening (연수화)")
                    curr_ca *= 0.2; curr_ss *= 0.5
                
                # AFM Filter
                applied_steps.append("AFM Filter (정밀여과)")
                curr_ss = min(curr_ss * 0.1, 2.0)
                
                # RO System
                if curr_tds > 1000 or w_val['Cl (ppm)'] > 250:
                    applied_steps.append("RO System (역삼투)")
                    curr_tds *= 0.02; curr_ca *= 0.01; curr_cod *= 0.05

                applied_steps.append("Product Water")

                # 결과 표시
                st.info(" ➡️ ".join([f"**[{s}]**" for s in applied_steps]))
                
                res_df = pd.DataFrame({
                    'Item': ['TDS', 'SS', 'COD', 'Hardness', 'Oil'],
                    'Raw (ppm)': [w_val['TDS (ppm)'], w_val['SS (ppm)'], w_val['COD (ppm)'], w_val['Hardness (Ca, ppm)'], w_val['Oil & Grease (ppm)']],
                    'Product (ppm)': [curr_tds, curr_ss, curr_cod, curr_ca, curr_oil]
                })
                
                # [수정됨] 전체 포맷팅 대신 숫자 컬럼만 지정하여 ValueError 방지
                st.markdown("#### ✨ 예상 처리 수질 비교")
                st.dataframe(res_df.style.format("{:.1f}", subset=['Raw (ppm)', 'Product (ppm)']), 
                             hide_index=True, use_container_width=True)
                
                if curr_tds < 100 and curr_ss < 1: st.success("✅ **판정:** 고품질 재이용 가능 (공정/보일러급)")
                elif curr_ss < 5: st.warning("⚠️ **판정:** 중급 재이용 가능 (조경/청소급)")
                else: st.error("🚨 **판정:** 추가 처리 필요")
            else:
                st.info("👈 원수 데이터 입력 후 시뮬레이션을 실행하세요.")

    # --------------------------------------------------------------------------
    # Tab 2: Equipment Design (신규 추가: RO & AFM 설계)
    # --------------------------------------------------------------------------
    with tab_ww_design:
        st.subheader("⚙️ Equipment Design Calculator")
        
        des_tabs = st.tabs(["💧 RO System Design", "⏳ AFM Filter Design"])
        
        # [2-1] RO 설계 계산기 (문서 'RO 시스템 시간당 50Ton 설계.docx' 기반)
        with des_tabs[0]:
            st.markdown("#### 1. RO Membrane System Calculation")
            
            c_ro1, c_ro2 = st.columns(2)
            with c_ro1:
                ro_prod = st.number_input("목표 생산량 (Product Flow, m3/hr)", value=50.0)
                ro_rec = st.slider("설계 회수율 (Recovery, %)", 50, 85, 75)
                ro_flux = st.number_input("설계 Flux (LMH)", value=25.0, help="표준 25 LMH (오염도 높으면 20 LMH 권장)")
                ro_area = 37.0 # 8인치 표준 면적 (고정)

            with c_ro2:
                # 계산 로직 [cite: 9-13]
                # 1. 공급 유량 = 생산량 / 회수율
                feed_flow = ro_prod / (ro_rec / 100.0)
                
                # 2. 필요 멤브레인 수 = (생산량 * 1000) / Flux / 면적
                total_area = (ro_prod * 1000) / ro_flux
                mem_qty = math.ceil(total_area / ro_area)
                
                # 3. 베셀 수량 (6 element/vessel 기준) [cite: 15]
                vessel_qty = math.ceil(mem_qty / 6)
                
                # 4. 펌프 및 탱크 용량 (여유율 1.15, 체류시간 1hr 적용) [cite: 20, 29]
                pump_capa = feed_flow * 1.15
                tank_capa = feed_flow * 1.0 # 1시간 체류 기준
                
                # 결과 표시
                st.success(f"**필요 멤브레인 수량: {mem_qty} ea** (8 inch)")
                st.info(f"**권장 베셀 수량:** {vessel_qty} ea (6-element vessel)")
                
            st.markdown("---")
            st.markdown("#### 📋 BOP 설비 사양 (Balance of Plant)")
            
            bop1, bop2 = st.columns(2)
            bop1.metric("필요 원수량 (Feed Flow)", f"{feed_flow:.1f} m³/hr")
            bop1.metric("원수 펌프 용량 (Pump)", f"{pump_capa:.1f} m³/hr", "여유율 15% 포함")
            
            bop2.metric("농축수 발생량 (Reject)", f"{feed_flow - ro_prod:.1f} m³/hr")
            bop2.metric("원수 탱크 용량 (Tank)", f"{math.ceil(tank_capa/10)*10} m³", "체류시간 1hr 기준")

        # [2-2] AFM 필터 설계 (문서 'AFM충전시 높이.docx' 기반)
        with des_tabs[1]:
            st.markdown("#### 2. AFM® Filter Media Calculation")
                        
            c_afm1, c_afm2 = st.columns(2)
            with c_afm1:
                tank_d = st.number_input("필터 탱크 직경 (Diameter, mm)", value=760)
                bed_h = st.number_input("여과층 높이 (Bed Height, mm)", value=1200, help="권장: 1000 ~ 1200mm")
            
            with c_afm2:
                # 계산 로직 [cite: 337-340]
                radius_m = (tank_d / 2) / 1000.0
                height_m = bed_h / 1000.0
                
                area = math.pi * (radius_m ** 2)
                total_vol_l = area * height_m * 1000.0
                
                st.info(f"**총 여과재 필요 부피:** {total_vol_l:.1f} Liters")
                st.caption(f"필터 단면적: {area:.2f} m²")

            st.markdown("---")
            st.markdown("#### 📦 Grade별 충진 상세 (Ratio & Weight)")
            
            # Grade별 비율 및 밀도 설정 (문서 기준) [cite: 332-335, 356-359]
            # Grade 0 (20%, 1.28), Grade 1 (50%, 1.25), Grade 2 (15%, 1.23), Grade 3 (15%, 1.23)
            afm_specs = [
                {"Grade": "Grade 0 (Top)", "Ratio": 0.20, "Density": 1.28},
                {"Grade": "Grade 1", "Ratio": 0.50, "Density": 1.25},
                {"Grade": "Grade 2", "Ratio": 0.15, "Density": 1.23},
                {"Grade": "Grade 3 (Bottom)", "Ratio": 0.15, "Density": 1.23},
            ]
            
            afm_res = []
            total_kg = 0
            
            for spec in afm_specs:
                vol = total_vol_l * spec["Ratio"]
                wgt = vol * spec["Density"]
                total_kg += wgt
                afm_res.append({
                    "Grade": spec["Grade"],
                    "Ratio (%)": f"{spec['Ratio']*100:.0f}%",
                    "Volume (L)": vol,
                    "Weight (kg)": wgt
                })
            
            df_afm = pd.DataFrame(afm_res)
            st.dataframe(
                df_afm.style.format({"Volume (L)": "{:.1f}", "Weight (kg)": "{:.1f}"}), 
                hide_index=True, 
                use_container_width=True
            )
            
            st.success(f"🚚 **총 발주 중량:** 약 {total_kg:.1f} kg")

    # --------------------------------------------------------------------------
    # Tab 3: Chemical Selection (기존 유지)
    # --------------------------------------------------------------------------
    with tab_ww_chem:
        st.subheader("💊 Waste Treatment Chemicals")
        wc1, wc2 = st.columns(2)
        with wc1:
            st.markdown("**1. 응집제 (Coagulant)**")
            st.selectbox("Coagulant", ["PAC (Standard)", "FeCl3", "Organic"], key="ww_sel_c")
            st.selectbox("Polymer", ["Anionic", "Cationic"], key="ww_sel_p")
        with wc2:
            st.markdown("**2. 특수 약품**")
            st.selectbox("Defoamer", ["Silicone", "Non-Silicone"], key="ww_sel_d")
            st.selectbox("Odor Control", ["None", "Bio", "Chemical"], key="ww_sel_o")

    # --------------------------------------------------------------------------
    # Tab 4: ROI & Economics (기존 유지)
    # --------------------------------------------------------------------------
    with tab_ww_roi:
        st.subheader("💰 Reused Water Economics")
        rc1, rc2 = st.columns(2)
        with rc1:
            q_day_ww = st.number_input("일일 재이용량 (m3/day)", 1000.0, key="ww_q_input")
            cost_tap_ww = st.number_input("공업용수 단가 (원/m3)", 1500, key="ww_cost_tap")
        with rc2:
            cost_op_ww = st.number_input("예상 운영비 (원/m3)", 400, key="ww_cost_op")
            invest_ww = st.number_input("시설 투자비 (백만원)", 300.0, key="ww_invest")

        saving_ww = q_day_ww * (cost_tap_ww - cost_op_ww) * 350
        payback_ww = (invest_ww * 1000000) / saving_ww if saving_ww > 0 else 0
        
        st.divider()
        rm1, rm2 = st.columns(2)
        rm1.metric("연간 예상 절감액", f"{int(saving_ww/1000000):,} 백만원")
        rm2.metric("투자비 회수 기간", f"{payback_ww:.1f} 년")

