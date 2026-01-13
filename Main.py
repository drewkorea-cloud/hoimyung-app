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
# [DATA] 데이터베이스
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
# [엔진 1] RO 화학 엔진
# ==========================================
class RO_Chemistry_Engine:
    def __init__(self):
        pass 

    def calculate_saturation(self, inputs):
        try:
            pH = float(inputs.get('pH', 7.5))
            Temp = float(inputs.get('Temp', 25.0))
            TDS = float(inputs.get('TDS', 500.0))
            Ca = float(inputs.get('Ca', 100.0))
            Mg = float(inputs.get('Mg', 20.0))
            HCO3 = float(inputs.get('HCO3', 100.0))
            SO4 = float(inputs.get('SO4', 50.0))
            SiO2 = float(inputs.get('SiO2', 10.0))
            Ba = float(inputs.get('Ba', 0.05))
            Sr = float(inputs.get('Sr', 0.5))
            PO4 = float(inputs.get('PO4', 0.1))
            NH4 = float(inputs.get('NH4', 0.1))
            F = float(inputs.get('F', 0.1))

            IS = 2.5e-5 * TDS 
            f_monovalent = 10 ** (-0.5 * (IS**0.5) / (1 + (IS**0.5))) 

            pCa = -math.log10(max(Ca, 0.1) / 40.08)
            pAlk = -math.log10(max(HCO3, 0.1) / 61.01)
            C_factor = math.log10(max(TDS, 10)) - 1
            pHs = (9.3 + 2.5) + C_factor - (13.12 * math.log10(Temp + 273)) - pCa - pAlk
            lsi = pH - pHs

            IAP_CaSO4 = (Ca/40.08) * (SO4/96.06) * (f_monovalent**4) * 1e-6
            Ksp_CaSO4 = 4.93e-5
            sat_caso4 = (IAP_CaSO4 / Ksp_CaSO4) * 100

            solubility_sio2 = 120 + (Temp - 25) * 2
            sat_sio2 = (SiO2 / solubility_sio2) * 100

            IAP_BaSO4 = (Ba/137.3) * (SO4/96.06) * 1e-6
            Ksp_BaSO4 = 1.08e-10
            sat_baso4 = (IAP_BaSO4 / Ksp_BaSO4) * 100

            IAP_SrSO4 = (Sr/87.62) * (SO4/96.06) * 1e-6
            Ksp_SrSO4 = 3.44e-7
            sat_srso4 = (IAP_SrSO4 / Ksp_SrSO4) * 100

            IAP_CaF2 = (Ca/40.08) * ((F/19.0)**2) * 1e-9
            Ksp_CaF2 = 3.45e-11
            sat_caf2 = (IAP_CaF2 / Ksp_CaF2) * 100

            struvite_risk = 0
            if NH4 > 0.5 and PO4 > 1.0:
                struvite_risk = (Mg * NH4 * PO4) / 1000.0 
                if pH > 8.0: struvite_risk *= 5

            status = "안정 (Stable)"
            solution = "수질 상태 양호. 범용 약품(MDC-220) 표준 주입 권장."
            warnings = []

            if lsi > 1.5: warnings.append("LSI 높음(CaCO3)")
            if sat_caso4 > 200: warnings.append("CaSO4 위험")
            if sat_baso4 > 100: warnings.append("BaSO4(바륨) 위험") 
            if sat_sio2 > 120: warnings.append("실리카 위험")
            if struvite_risk > 10: warnings.append("스트루바이트 위험")

            if warnings:
                status = f"⚠️ 경고: {', '.join(warnings)}"
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
                "Sat_BaSO4": round(sat_baso4, 0),
                "Sat_SrSO4": round(sat_srso4, 0),
                "Sat_SiO2": round(sat_sio2, 0),
                "Sat_CaF2": round(sat_caf2, 0),
                "Status": status,
                "Solution": solution,
                "Success": True
            }

        except Exception as e:
            return {"Success": False, "Error": str(e), "Status": "Error", "Solution": "Check Input Data"}

# ==========================================
# [엔진 2] 보일러 전문가 엔진
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

# --- 2. 사이드바 메뉴 ---
with st.sidebar:
    st.title("💧 HOIMYUNG WATERZEN")
    st.subheader("Water Master Pro")
    
    program_mode = st.radio(
        "Select Module:", 
        [
            "1. Cooling Expert", 
            "2. Boiler Master", 
            "3. RO Master Pro", 
            "4. Wastewater Reuse", 
            "5. Data Analytics"
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
    # Tab 1: Water Balance
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
        
        # [시각화 & 요약]
        c_chart, c_metric = st.columns([1.2, 1])
        
        with c_chart:
            labels = ['Evaporation (증발)', 'Blowdown (배수)', 'Windage (비산)']
            values = [evap, blowdown, windage]
            fig_bal = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, 
                                           marker_colors=['#3498DB', '#E74C3C', '#95A5A6'])])
            fig_bal.update_layout(title_text="Water Usage Breakdown", height=320, margin=dict(t=40, b=10, l=10, r=10))
            st.plotly_chart(fig_bal, use_container_width=True)

        with c_metric:
            st.subheader("📊 Operation Summary")
            op_m1, op_m2 = st.columns(2)
            with op_m1:
                st.metric("증발량 (Evaporation)", f"{evap:.1f} m³/hr", help="냉각 부하에 비례하여 증발하는 물의 양")
                st.metric("보급수량 (Make-up)", f"{makeup:.1f} m³/hr", help="증발+배수+비산을 채워주는 물")
            with op_m2:
                st.metric("배수량 (Blowdown)", f"{blowdown:.1f} m³/hr", help="농축 관리를 위해 버리는 물")
                ht_msg = "✅ Good"
                ht_color = "normal"
                if hti > 48: 
                    ht_msg = "⚠️ Long"
                    ht_color = "inverse"
                elif hti < 4: 
                    ht_msg = "⚠️ Short"
                    ht_color = "inverse"
                st.metric("반감기 (Half Life)", f"{hti:.1f} hr", delta=ht_msg, delta_color=ht_color, help="약품 농도가 절반이 되는 시간")

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
    # Tab 3: Chemical Program
    # ======================================================================
    with tab3:
        st.subheader("3. Chemical Program Selection")
        
        col_chem1, col_chem2 = st.columns(2)
        with col_chem1:
            st.markdown("#### 🧪 Inhibitor Selection")
            try:
                chem_list = PRODUCT_CATALOG['Cooling']['Main_Inhibitor']
                chem_names = [c['Name'] for c in chem_list]
                sel_chem = st.selectbox("Select Inhibitor Model", chem_names)
                target_chem = next((item for item in chem_list if item['Name'] == sel_chem), None)
                if target_chem:
                    st.info(f"**Selected:** {sel_chem} | **Type:** {target_chem['Type']} | **Dosage:** {target_chem['Dosage']} ppm")
                    rec_dose_ppm = target_chem['Dosage']
            except: 
                st.error("약품 데이터베이스(PRODUCT_CATALOG) 오류")
                rec_dose_ppm = 50.0
        
        with col_chem2:
            st.markdown("#### 🕒 Consumption Calculation")
            sys_vol = st.number_input("보유수량 (System Vol, m3)", value=500.0, step=10.0)
            circ_rate = st.number_input("순환수량 (Circulation, m3/hr)", value=2000.0, step=100.0)
            
            # 물질수지 계산
            estim_mu = circ_rate * 0.015 
            estim_blow = estim_mu / target_coc # 배수량 (Blowdown)
            
            st.info(f"추정 배수량(Blowdown): 약 {estim_blow:.1f} m3/hr (at {target_coc} Cycles)")
            if estim_blow > 0: hti = 0.693 * sys_vol / estim_blow
            else: hti = 999.9
            
            # [수정된 약품 계산] 사용량 = 배수량(Blowdown) 기준
            usage_kg = (estim_blow * 24 * rec_dose_ppm) / 1000.0
            
            st.metric("예상 반감기", f"{hti:.1f} hr")
            st.metric("일일 약품 사용량", f"{usage_kg:.1f} kg/day", help="배수 손실분 보충 기준 (Blowdown Basis)")
        
        st.markdown("---")
        st.markdown("### 🦠 Biocide Program")
        b1, b2 = st.columns(2)
        b1.checkbox("Oxidizing (염소계)", value=True)
        b2.checkbox("Non-Oxidizing (비산화성)", value=True)

    # ======================================================================
    # Tab 4: Lab Analysis & Trouble Shooting
    # ======================================================================
    with tab4:
        st.header("🔬 Lab Analysis & Trouble Shooting")
        st.subheader("1. Deposit Composition Analysis (ICP/Lab Data)")
        
        with st.container(border=True):
            lc1, lc2, lc3, lc4, lc5 = st.columns(5)
            def_vals = st.session_state.deposit_data['Result (%)'].tolist() if 'deposit_data' in st.session_state else [10.0, 40.0, 5.0, 2.0, 5.0]
            if len(def_vals) < 8: def_vals = [10.0, 40.0, 5.0, 2.0, 5.0]

            fe = lc1.number_input("Fe (철분, %)", 0.0, 100.0, float(def_vals[3]))
            ca = lc2.number_input("Ca (칼슘, %)", 0.0, 100.0, float(def_vals[1]))
            sio2_dep = lc3.number_input("SiO2 (실리카, %)", 0.0, 100.0, float(def_vals[5]))
            p2o5 = lc4.number_input("P2O5 (인산염, %)", 0.0, 100.0, float(def_vals[6]))
            loi = lc5.number_input("LOI (유기물, %)", 0.0, 100.0, float(def_vals[0]))
        
        if st.button("🧪 Identify Deposit Type"):
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
# [Module 2] Boiler Master Pro
# ==============================================================================
elif "Boiler" in program_mode:
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

    tab_sim, tab_chem_prog, tab_safety, tab_energy = st.tabs([
        "1. Water Simulation", "2. Chemical Program", "3. Na-PO4 Safety Map", "4. Energy Cost"
    ])
    
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
            fig_map.add_shape(type="rect", x0=10, y0=9.4, x1=40, y1=10.5, line=dict(color="Green"), fillcolor="rgba(0, 255, 0, 0.1)")
            fig_map.add_annotation(x=25, y=10.0, text="Safe Zone", showarrow=False, font=dict(color="green"))

            x_range = np.linspace(0, 60, 100)
            y_upper = 11.6 - (x_range * 0.025)
            y_lower = 9.0 - (x_range * 0.01)
            
            fig_map.add_trace(go.Scatter(x=x_range, y=y_upper, mode='lines', name='Caustic Limit', line=dict(color='red', dash='dash')))
            fig_map.add_trace(go.Scatter(x=x_range, y=y_lower, mode='lines', name='Acidic Limit', line=dict(color='orange', dash='dash')))

            status_color = "green"
            status_msg = "Safe"
            limit_up = 11.6 - (cur_po4 * 0.025)
            limit_down = 9.0 - (cur_po4 * 0.01)
            
            if cur_ph > limit_up:
                status_color = "red"; status_msg = "Caustic Risk"
            elif cur_ph < limit_down:
                status_color = "orange"; status_msg = "Acidic Risk"
            
            fig_map.add_trace(go.Scatter(x=[cur_po4], y=[cur_ph], mode='markers+text', marker=dict(size=18, color=status_color, symbol='x'), text=[status_msg], textposition="top right", name='Current Point'))
            fig_map.update_layout(title="Na-PO4 Safety Map", xaxis_title="Phosphate (PO4, ppm)", yaxis_title="pH", xaxis=dict(range=[0, 60]), yaxis=dict(range=[8.0, 12.5]), height=450)
            st.plotly_chart(fig_map, use_container_width=True)
            
            if status_color == "red":
                st.error("🚨 **위험:** pH가 너무 높습니다. **알칼리 부식(Caustic Gouging)**이 우려됩니다. 인산염을 투입하여 pH를 낮추십시오.")
            elif status_color == "orange":
                st.warning("⚠️ **주의:** pH가 너무 낮습니다. **산성 부식** 가능성이 있습니다.")
            else:
                st.success("✅ **양호:** 적절한 Phosphate 처리 영역에 있습니다.")

    with tab_energy:
        st.subheader("💸 Steam Cost Analysis")
        col_e1, col_e2 = st.columns([1, 1.5])
        with col_e1:
            edited_energy = st.data_editor(st.session_state.energy_data, hide_index=True, key="bo_energy_edit")
        with col_e2:
            e_vals = dict(zip(edited_energy['Parameter'], edited_energy['Value']))
            stm_val = st.session_state.boiler_results['steam'] if st.session_state.boiler_results else 10.0
            fuel_cost = e_vals.get('Fuel Cost (KRW/m3)', 900.0)
            cost_hourly = (stm_val * 1000 * 600 / 8500) * fuel_cost
            st.metric("Hourly Steam Cost", f"{int(cost_hourly):,} KRW/hr")

# ==============================================================================
# [Module 3] RO Master Pro
# ==============================================================================
elif "RO" in program_mode:
        st.title("💧 RO Master Pro (Global Expert Ver.)")
        st.info("Global Chemical사(Nalco/Solenis 등) 수준의 정밀 진단 및 CIP 솔루션 모듈입니다.")

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🛠 System Design", 
            "⚗️ Chemical Projection", 
            "📈 Smart Operation", 
            "🕵️ Autopsy & Trouble",
            "🧹 CIP Manager" 
        ])

        with tab1:
            st.subheader("1. RO Design Configuration")
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                flow_unit = st.radio("유량 단위 선택 (Flow Unit)", ["m³/hr (시간당)", "m³/day (일일)"], horizontal=True)
            col1, col2 = st.columns(2)
            with col1:
                if "hr" in flow_unit:
                    flow_input = st.number_input("Permeate Flow (생산량)", value=50.0, help="시간당 생산량")
                    flow_m3_hr = flow_input
                else:
                    flow_input = st.number_input("Permeate Flow (생산량)", value=50.0, help="일일 생산량 (24hr 가동 기준)")
                    flow_m3_hr = flow_input / 24.0
                rec = st.slider("Target Recovery (회수율 %)", 50, 90, 75)
            with col2:
                temp = st.number_input("Design Temperature (°C)", value=25.0)
                app_type = st.selectbox("수질 용도 (Application)", ["기수/공업용수 (BWRO)", "폐수 재이용 (WWRO)", "해수 담수 (SWRO)"])
                if "BWRO" in app_type:
                    rec_flux = 22.0
                    flux_guide = "20~25"
                elif "WWRO" in app_type:
                    rec_flux = 13.5
                    flux_guide = "12~15"
                else:
                    rec_flux = 14.0 
                    flux_guide = "12~16"
                flux = st.number_input(f"Avg Flux (lmh) - Guide: {flux_guide}", value=rec_flux)
            
            st.markdown("---")
            total_area_req = (flow_m3_hr * 1000.0) / flux
            element_area = 37.0 
            qty = math.ceil(total_area_req / element_area)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Flow Rate (Converted)", f"{flow_m3_hr:.1f} m³/hr", f"{flow_m3_hr*24:.1f} m³/day")
            c2.metric("Design Flux", f"{flux} lmh")
            qty_color = "normal"
            if qty > 100 and "day" in flow_unit: qty_color = "inverse"
            c3.metric("Required Elements (8\")", f"{qty} ea", delta="Standard 400ft²", delta_color=qty_color)
            st.info(f"💡 **Calculation:** {flow_m3_hr:.1f} m³/hr 생산을 위해 {flux} lmh 유속으로 설계 시, 약 **{qty}개**의 8인치 멤브레인이 필요합니다.")

        with tab2:
            st.subheader("2. Advanced Scale Prediction & Chemical Dosing")
            with st.expander("🧪 상세 수질 데이터 입력 (Feed Water Analysis)", expanded=True):
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
                # [수정] 농축 계수(CF) 계산 및 농축수 수질 적용
                try:
                    # Tab 1의 rec 값 참조 (없으면 기본값 75%)
                    current_rec = rec if 'rec' in locals() else 75.0
                    cf = 1.0 / (1.0 - (current_rec / 100.0))
                except:
                    cf = 4.0 # 기본 4배 농축 (회수율 75%)

                # 입력값을 농축수 기준으로 변환 (pH는 보수적으로 원수 유지 또는 LSI 식에서 자동 보정됨)
                inputs = {
                    'pH': ph, 
                    'Temp': temp_c, 
                    'TDS': tds * cf, 
                    'Ca': ca * cf, 'Mg': mg * cf, 'HCO3': hco3 * cf, 'SO4': so4 * cf, 
                    'SiO2': sio2 * cf, 'Ba': ba * cf, 'Sr': sr * cf, 'F': f_ion * cf,
                    'Na': 100 * cf, 'Cl': 100 * cf # 기타 이온도 농축
                }
                
                engine = RO_Chemistry_Engine() 
                res = engine.calculate_saturation(inputs)
                
                st.markdown(f"### 🔍 Projection Result (at {cf:.1f}x Concentration)")
                if "안정" in res['Status']: st.success(f"Diagnostics: {res['Status']}")
                else: st.error(f"Diagnostics: {res['Status']}")
                st.info(f"💊 **Prescription:** {res['Solution']}")

                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("LSI (Conc.)", res['LSI'], help="농축수 기준 LSI")
                mc2.metric("CaSO4 Sat(%)", f"{res['Sat_CaSO4']}%")
                mc3.metric("BaSO4 Sat(%)", f"{res['Sat_BaSO4']}%")
                mc4.metric("SiO2 Sat(%)", f"{res['Sat_SiO2']}%")

        with tab3:
            st.subheader("3. Operation Data Normalization (보정 운전)")
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
                if flow_change < -10: c2.error("🚨 **CIP 시급:** 보정 유량이 10% 이상 감소했습니다.")
                elif flow_change < -5: c2.warning("⚠️ **성능 저하:** 스케일 방지제 주입량을 점검하세요.")
                else: c2.success("✅ **정상:** 유량 감소는 단순 수온 저하 때문입니다.")

        with tab4:
            st.subheader("4. Membrane Autopsy & Troubleshooting")
            col1, col2 = st.columns(2)
            with col1:
                deposit_type = st.selectbox("오염물 성상", ["갈색/점액질 (Biomass)", "단단한 결정 (Scaling)", "검은색 가루 (Metal Oxide)", "유기물/오일 (Organics)"])
            with col2:
                dp_loc = st.selectbox("차압 상승 위치", ["전단부 (Lead)", "후단부 (Tail)", "전체"])
            st.info("💡 **AI Expert Opinion:**")
            if "Biomass" in deposit_type or "전단부" in dp_loc: st.markdown("- **진단:** 미생물 오염 (Biofouling)\n- **처방:** pH 12 알칼리 세정 + 비산화성 살균제 충격 요법")
            elif "결정" in deposit_type or "후단부" in dp_loc: st.markdown("- **진단:** 무기물 스케일 (Scaling)\n- **처방:** pH 2 산 세정 + 회수율 하향 조정")
            elif "오일" in deposit_type: st.markdown("- **진단:** 유분 오염\n- **처방:** 고온 알칼리 + 계면활성제 세정 (복구 어려움)")
            else: st.markdown("현장 데이터를 더 수집해주십시오.")

        with tab5:
            st.header("🧹 CIP (Clean-In-Place) Manager")
            st.caption("Standard Operation Procedure based on Manual")
            st.subheader("1. CIP 실시 기준 (Timing Criteria)")
            st.warning("""다음 현상 중 **하나라도** 발생하면 즉시 세정을 실시해야 합니다.\n* 📉 **생산수량 15% 감소** (정상 압력 기준)\n* 📈 **운전압력 15% 증가** (정상 생산량 기준)\n* 🧂 **염투과율(Salt Passage) 15% 증가** (생산수질 악화)""")
            st.divider()
            st.subheader("2. CIP 설비 용량 계산기 (Design Calculator)")
            with st.container():
                col_c1, col_c2 = st.columns(2)
                cip_vessels = col_c1.number_input("1st Stage Vessels (Vessel 수)", value=5, min_value=1)
                cip_flow_req = cip_vessels * 8.0 
                cip_tank_req = (cip_flow_req * 0.06) + 1.0
                col_c2.metric("권장 CIP 펌프 유량", f"{cip_flow_req:.1f} m³/hr", help="8 inch Vessel 기준 (8m3/hr/vessel)")
                col_c2.metric("최소 CIP 탱크 용량", f"{cip_tank_req:.1f} m³", help="배관 및 베셀 보유수량 포함")
            st.divider()
            st.subheader("3. 약품 선정 및 세정 조건 (Chemicals)")
            cip_type = st.radio("세정 종류 선택", ["무기물 세정 (Scale)", "유기물 세정 (Organic)"], horizontal=True)
            if "무기물" in cip_type: st.success("🧪 **무기물 세정 (Acid Cleaning)**: 탄산칼슘, 금속 산화물 제거 (pH 2.0~3.0)")
            else: st.info("🦠 **유기물 세정 (Alkaline Cleaning)**: 미생물, 실리카 제거 (pH 11.0~12.0)")
            st.markdown(f"**💧 약품 희석 비율 (5% 기준):** 물 1m³ 당 약품 **50kg** 투입")

# ==============================================================================
# [Module 4] Wastewater Expert
# ==============================================================================
elif "Wastewater" in program_mode:
    if 'waste_data' not in st.session_state:
        st.session_state.waste_data = pd.DataFrame({
            'Parameter': ['pH', 'TDS (ppm)', 'SS (ppm)', 'COD (ppm)', 'Cl (ppm)', 'Hardness (Ca, ppm)', 'Oil & Grease (ppm)'],
            'Value': [7.2, 1200.0, 60.0, 150.0, 350.0, 400.0, 5.0]
        })

    st.title("♻️ Wastewater Reuse Engineering")
    st.info("공정 시뮬레이션 및 RO/AFM 설비 설계(Design Calculation) 통합 시스템")
    
    tab_ww_sim, tab_ww_design, tab_ww_chem, tab_ww_roi = st.tabs([
        "1. Process Simulation", 
        "2. Equipment Design (RO/AFM)", 
        "3. Chemical Selection", 
        "4. ROI & Economics"
    ])

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
                curr_ss, curr_cod = w_val['SS (ppm)'], w_val['COD (ppm)']
                curr_oil, curr_tds = w_val['Oil & Grease (ppm)'], w_val['TDS (ppm)']
                curr_ca = w_val['Hardness (Ca, ppm)']
                applied_steps = ["Raw Water"]
                if curr_oil > 10 or curr_ss > 50:
                    applied_steps.append("DAF")
                    curr_ss *= 0.15; curr_cod *= 0.7; curr_oil *= 0.1
                elif curr_ca > 300:
                    applied_steps.append("Softening")
                    curr_ca *= 0.2; curr_ss *= 0.5
                applied_steps.append("AFM Filter")
                curr_ss = min(curr_ss * 0.1, 2.0)
                if curr_tds > 1000 or w_val['Cl (ppm)'] > 250:
                    applied_steps.append("RO System")
                    curr_tds *= 0.02; curr_ca *= 0.01; curr_cod *= 0.05
                applied_steps.append("Product")
                st.info(" ➡️ ".join([f"**[{s}]**" for s in applied_steps]))
                res_df = pd.DataFrame({
                    'Item': ['TDS', 'SS', 'COD', 'Hardness', 'Oil'],
                    'Raw (ppm)': [w_val['TDS (ppm)'], w_val['SS (ppm)'], w_val['COD (ppm)'], w_val['Hardness (Ca, ppm)'], w_val['Oil & Grease (ppm)']],
                    'Product (ppm)': [curr_tds, curr_ss, curr_cod, curr_ca, curr_oil]
                })
                st.markdown("#### ✨ 예상 처리 수질 비교")
                st.dataframe(res_df.style.format("{:.1f}", subset=['Raw (ppm)', 'Product (ppm)']), hide_index=True, use_container_width=True)
                if curr_tds < 100 and curr_ss < 1: st.success("✅ **판정:** 고품질 재이용 가능")
                else: st.warning("⚠️ **판정:** 추가 처리가 필요할 수 있습니다.")

    with tab_ww_design:
        st.subheader("⚙️ Equipment Design Calculator")
        des_tabs = st.tabs(["💧 RO System Design", "⏳ AFM Filter Design"])
        
        with des_tabs[0]:
            st.markdown("#### 1. RO Design Optimization (Conservative vs Economic)")
            st.caption("문서 기준: 20 LMH(안정적) vs 25 LMH(경제적) 설계 비교")
            c_ro1, c_ro2 = st.columns(2)
            with c_ro1:
                ro_prod = st.number_input("목표 생산량 (m3/hr)", value=50.0)
                ro_rec = st.slider("설계 회수율 (%)", 50, 85, 75)
            with c_ro2:
                st.info(f"💡 **Flux 전략:** 폐수 재이용 시 오염 부하를 고려하여 **20~25 LMH** 범위에서 결정합니다.")
            ro_area = 37.0
            feed_flow = ro_prod / (ro_rec / 100.0)
            qty_20 = math.ceil((ro_prod * 1000) / 20.0 / ro_area)
            vess_20 = math.ceil(qty_20 / 6)
            qty_25 = math.ceil((ro_prod * 1000) / 25.0 / ro_area)
            vess_25 = math.ceil(qty_25 / 6)
            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("### 🛡️ Scenario A: 안정 설계 (20 LMH)")
                st.metric("필요 멤브레인", f"{qty_20} ea", f"+{qty_20 - qty_25} ea (vs B)")
                st.metric("필요 베셀 (6-element)", f"{vess_20} ea")
                st.success("✅ **장점:** 오염(Fouling) 저항성 우수, 세정 주기 연장")
            with col_b:
                st.markdown("### 💰 Scenario B: 경제 설계 (25 LMH)")
                st.metric("필요 멤브레인", f"{qty_25} ea", "Standard")
                st.metric("필요 베셀 (6-element)", f"{vess_25} ea")
                st.warning("⚠️ **주의:** 초기 투자비는 저렴하나, 막 오염 가능성 증가")

        with des_tabs[1]:
            st.markdown("#### 2. AFM® Filter Design (Safety Check)")
            c_afm1, c_afm2 = st.columns(2)
            with c_afm1:
                tank_d = st.number_input("필터 탱크 직경 (mm)", value=760)
                tank_h = st.number_input("필터 탱크 전체 높이 (Total Height, mm)", value=1800, help="Freeboard 계산용")
            with c_afm2:
                bed_h = st.number_input("여과재 충진 높이 (Bed Height, mm)", value=1200, help="권장: 1000~1200mm")
            freeboard = tank_h - bed_h
            freeboard_ratio = (freeboard / bed_h) * 100
            st.markdown("---")
            c_chk1, c_chk2 = st.columns(2)
            c_chk1.metric("확보된 여유고 (Freeboard)", f"{freeboard} mm", f"{freeboard_ratio:.1f}% (vs Bed)")
            with c_chk2:
                if freeboard_ratio < 30:
                    st.error("🚨 **위험:** 여유 공간 부족! (권장: 30% 이상)")
                    st.caption("역세척 시 여과재가 유실될 수 있습니다. 충진 높이를 낮추거나 탱크를 키우세요.")
                else:
                    st.success("✅ **안전:** 역세척 팽창 공간(Freeboard)이 충분합니다.")
            radius_m = (tank_d / 2) / 1000.0
            total_vol_l = math.pi * (radius_m ** 2) * (bed_h / 1000.0) * 1000.0
            afm_specs = [
                {"Grade": "Grade 0 (Top)", "Ratio": 0.20, "Density": 1.28},
                {"Grade": "Grade 1", "Ratio": 0.50, "Density": 1.25},
                {"Grade": "Grade 2", "Ratio": 0.15, "Density": 1.23},
                {"Grade": "Grade 3 (Bottom)", "Ratio": 0.15, "Density": 1.23},
            ]
            res_list = []
            for spec in afm_specs:
                v = total_vol_l * spec["Ratio"]
                w = v * spec["Density"]
                res_list.append({"Grade": spec["Grade"], "Vol (L)": v, "Wgt (kg)": w})
            st.markdown("#### 📦 충진 물량 산출서")
            df_afm_calc = pd.DataFrame(res_list)
            st.dataframe(df_afm_calc.style.format({"Vol (L)": "{:.1f}", "Wgt (kg)": "{:.1f}"}), hide_index=True, use_container_width=True)

    with tab_ww_chem:
        st.subheader("💊 Waste Treatment Chemicals")
        wc1, wc2 = st.columns(2)
        with wc1:
            st.selectbox("Coagulant", ["PAC (Standard)", "FeCl3", "Organic"], key="ww_sel_c")
            st.selectbox("Polymer", ["Anionic", "Cationic"], key="ww_sel_p")
        with wc2:
            st.selectbox("Defoamer", ["Silicone", "Non-Silicone"], key="ww_sel_d")
            st.selectbox("Odor Control", ["None", "Bio", "Chemical"], key="ww_sel_o")

    with tab_ww_roi:
        st.subheader("💰 Reused Water Economics")
        rc1, rc2 = st.columns(2)
        with rc1:
            q_day = st.number_input("일일 재이용량 (m3/day)", 1000.0, key="ww_q")
            cost_tap = st.number_input("공업용수 단가 (원/m3)", 1500, key="ww_tap")
        with rc2:
            cost_op = st.number_input("운영비 (원/m3)", 400, key="ww_op")
            invest = st.number_input("투자비 (백만원)", 300.0, key="ww_inv")
        saving = q_day * (cost_tap - cost_op) * 350
        payback = (invest * 1e6) / saving if saving > 0 else 0
        st.metric("연간 절감액", f"{int(saving/1e6):,} 백만원")
        st.metric("회수 기간", f"{payback:.1f} 년")

# ==============================================================================
# [Module 5] Data Analytics
# ==============================================================================
elif "Data" in program_mode:
    st.title("📈 Ultimate Trend Master")
    st.info("화학적 수질(pH, Cl, Fe)과 물리적 운전(유속, 온도, 차압) 데이터를 통합 분석합니다.")

    with st.container(border=True):
        uploaded_file = st.file_uploader("📂 통합 운전 일지 업로드 (Excel/CSV)", type=['xlsx', 'xls', 'csv'])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            cols = df.columns.tolist()
            c_date, c_dummy = st.columns([1, 2])
            with c_date:
                date_col = st.selectbox("📅 날짜/시간 컬럼 (Time Axis)", ["선택"] + cols)
            
            if date_col != "선택":
                df[date_col] = pd.to_datetime(df[date_col])
                df = df.sort_values(by=date_col)
                st.divider()
                st.subheader("2. 테마별 심층 분석 (Deep Dive Analysis)")

                with st.expander("🔴 [부식] Corrosion & Physical Stress", expanded=True):
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        default_corr = [c for c in cols if any(x in c.upper() for x in ['FE', 'IRON', 'CL', 'SO4', 'PH', 'TEMP', 'FLOW', 'VEL'])]
                        corr_items = st.multiselect("부식 영향 인자 (Multi-Select)", cols, default=default_corr)
                    with c2:
                        if corr_items:
                            fig_corr = px.line(df, x=date_col, y=corr_items, title="Corrosion Factors", markers=True)
                            fig_corr.update_layout(height=400, hovermode="x unified")
                            st.plotly_chart(fig_corr, use_container_width=True)
                            st.warning("💡 **Check:** 온도(Temp)나 유속(Flow)이 급변할 때 철분(Fe)이 튀는지 확인하십시오.")

                with st.expander("⚪ [스케일] Scale & Heat Efficiency", expanded=True):
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        default_scale = [c for c in cols if any(x in c.upper() for x in ['CA', 'HARD', 'ALK', 'SIO2', 'PO4', 'DELTA', 'DT', 'DIFF'])]
                        scale_items = st.multiselect("스케일 및 열효율 인자", cols, default=default_scale)
                    with c2:
                        if scale_items:
                            fig_scale = px.line(df, x=date_col, y=scale_items, title="Scale Potential", markers=True)
                            fig_scale.update_layout(height=400, hovermode="x unified")
                            st.plotly_chart(fig_scale, use_container_width=True)
                            st.info("💡 **Check:** 약품 농도는 정상인데 Delta T(온도차)가 줄어든다면 스케일입니다.")

                with st.expander("🟢 [미생물] Bio-fouling & Disinfection Limit", expanded=True):
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        default_bio = [c for c in cols if any(x in c.upper() for x in ['RES', 'CL', 'ORP', 'BIO', 'TOC', 'COD', 'NIT', 'PH'])]
                        bio_items = st.multiselect("살균 및 영양분 인자", cols, default=default_bio)
                    with c2:
                        if bio_items:
                            fig_bio = px.line(df, x=date_col, y=bio_items, title="Bio-Activity", markers=True)
                            ph_cols = [c for c in df.columns if 'PH' in c.upper()]
                            if ph_cols:
                                target_ph_col = ph_cols[0]
                                if not df[df[target_ph_col] > 8.0].empty:
                                    st.error(f"🚨 **pH 경고:** pH 8.0 이상 구간에서는 염소 살균력이 급감합니다.")
                            fig_bio.update_layout(height=400, hovermode="x unified")
                            st.plotly_chart(fig_bio, use_container_width=True)

                st.divider()
                st.subheader("3. 인과관계 증명 (Root Cause Analysis)")
                c_scat1, c_scat2 = st.columns(2)
                with c_scat1: x_axis = st.selectbox("원인 인자 (X-Axis)", ["선택"] + cols, index=0)
                with c_scat2: y_axis = st.selectbox("결과 인자 (Y-Axis)", ["선택"] + cols, index=0)
                if x_axis != "선택" and y_axis != "선택":
                    fig_scat = px.scatter(df, x=x_axis, y=y_axis, trendline="ols", title=f"Correlation: {x_axis} vs {y_axis}")
                    st.plotly_chart(fig_scat, use_container_width=True)

        except Exception as e:
            st.error(f"파일 분석 중 오류가 발생했습니다: {e}")