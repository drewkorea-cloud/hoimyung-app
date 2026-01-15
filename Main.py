
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

            {'Name': 'HRD-2200 (General)', 'Desc': '범용 탄산칼슘/황산염 제어', 'Dosage': 3.0, 'Target': ['LSI', 'CaSO4']},

            {'Name': 'HRD-3000 (High Silica)', 'Desc': '실리카 200ppm 대응/강력 분산', 'Dosage': 5.0, 'Target': ['SiO2']},

            {'Name': 'HRD-2050 (Struvite)', 'Desc': '폐수 재이용/인산염/스트루바이트 제어', 'Dosage': 6.0, 'Target': ['Struvite', 'CaPO4']},

            {'Name': 'HRD-2240 (High Sulfate)', 'Desc': 'BaSO4, SrSO4 특화 (황산바륨 제어)', 'Dosage': 4.0, 'Target': ['BaSO4', 'SrSO4']}

        ]

    }

}




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
    # Tab 3: Chemical Program (살균제/분산제 시각화 강화 버전)
    # ======================================================================
    with tab3:
        st.subheader("3. Integrated Chemical Program Selection")
        
  # [핵심 수정] Tab 1에서 계산된 배수량 가져오기
        calc_blowdown = st.session_state.get('final_blowdown', 0.0)
        calc_hti = st.session_state.get('final_hti', 0.0)

        col_bal1, col_bal2 = st.columns(2)
        with col_bal1:
            # 연동된 값을 보여주되, 사용자가 직접 수정도 가능하게 구성
            estim_blow = st.number_input("설계 배수량 (Blowdown, m3/hr)", 
                                         value=float(calc_blowdown), 
                                         help="Tab 1 물질수지에서 계산된 값이 자동으로 반영됩니다.")
        with col_bal2:
            st.info(f"💡 **현재 물질수지 상태:** 계산 배수량 {calc_blowdown:.1f} m³/hr | 반감기 {calc_hti:.1f} hr")

        st.markdown("---")
        
        col_c1, col_c2, col_c3 = st.columns(3)
        
        # 1. 부식/스케일 억제제 (Inhibitor)
        with col_c1:
            st.markdown("#### 🛡️ Inhibitor")
            chem_list = PRODUCT_CATALOG['Cooling']['Main_Inhibitor']
            sel_inh = st.selectbox("억제제 선택", [c['Name'] for c in chem_list], key="sel_inh")
            inh_data = next((item for item in chem_list if item['Name'] == sel_inh), None)
            inh_dose = st.number_input("주입농도 (ppm)", value=float(inh_data['Dosage']), key="inh_dose_val")
            usage_inh = (estim_blow * 24 * inh_dose) / 1000.0

        # 2. 분산제 (Dispersant)
        with col_c2:
            st.markdown("#### 🧪 Dispersant")
            disp_list = PRODUCT_CATALOG['Cooling']['Dispersant']
            sel_disp = st.selectbox("분산제 선택", [d['Name'] for d in disp_list], key="sel_disp")
            disp_data = next((item for item in disp_list if item['Name'] == sel_disp), None)
            disp_dose = st.number_input("주입농도 (ppm)", value=float(disp_data['Dosage']), key="disp_dose_val")
            usage_disp = (estim_blow * 24 * disp_dose) / 1000.0

        # 3. 살균제 (Biocide)
        with col_c3:
            st.markdown("#### 🦠 Biocide")
            bio_list = PRODUCT_CATALOG['Cooling']['Biocide']
            sel_bio = st.selectbox("살균제 선택", [b['Name'] for b in bio_list], key="sel_bio")
            bio_data = next((item for item in bio_list if item['Name'] == sel_bio), None)
            bio_dose = st.number_input("주입농도 (ppm)", value=float(bio_data['Dosage']), key="bio_dose_val")
            # 살균제는 보통 충격 주입(Slug)을 하지만, 비교를 위해 일일 평균 소요량으로 계산
            usage_bio = (estim_blow * 24 * bio_dose) / 1000.0

        st.divider()

        # 시각화 차트 영역
        st.markdown("### 📊 일일 약품 소요량 비교 (Daily Consumption)")
        
        chart_data = pd.DataFrame({
            'Category': ['Inhibitor', 'Dispersant', 'Biocide'],
            'Product': [sel_inh, sel_disp, sel_bio],
            'Usage (kg/day)': [usage_inh, usage_disp, usage_bio]
        })

        # Plotly 막대 그래프 생성
        fig_chem = px.bar(
            chart_data, 
            x='Category', 
            y='Usage (kg/day)',
            color='Category',
            text=chart_data['Usage (kg/day)'].apply(lambda x: f'{x:.1f} kg'),
            color_discrete_map={'Inhibitor': '#3498DB', 'Dispersant': '#F1C40F', 'Biocide': '#E74C3C'},
            title="Estimated Daily Chemical Usage"
        )
        
        fig_chem.update_layout(
            showlegend=False,
            height=400,
            yaxis_title="Quantity (kg/day)",
            xaxis_title=""
        )
        
        st.plotly_chart(fig_chem, use_container_width=True)

        # 상세 요약 메트릭
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Total {sel_inh}", f"{usage_inh:.1f} kg/day")
        m2.metric(f"Total {sel_disp}", f"{usage_disp:.1f} kg/day")
        m3.metric(f"Total {sel_bio}", f"{usage_bio:.1f} kg/day")

        with st.expander("ℹ️ 계산 근거 및 참고사항"):
            st.caption("""
            * **계산 공식:** (배수량(m³/hr) × 24시간 × 목표농도(ppm)) / 1000 = 일일 사용량(kg)
            * 살균제의 경우 현장 상황에 따라 일 1회 또는 주 2~3회 충격 주입(Slug Dose)으로 운전될 수 있으므로, 위 수치는 연속 주입 시의 평균 소요량입니다.
            """)
 

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

    tab_sim, tab_chem_prog, tab_safety, tab_energy = st.tabs([
        "1. Water Simulation & Balance", 
        "2. Chemical Program (약품설계)", 
        "3. Na-PO4 Safety Map", 
        "4. Energy Cost"
    ])
    
    # --- Tab 1: Water Simulation & Balance ---
    with tab_sim:
        st.subheader("1. Boiler Water Balance & Quality Prediction")
        col_b1, col_b2 = st.columns([1, 1.2])
        
        with col_b1:
            st.markdown("###### ① 급수 수질 입력 (Feedwater)")
            # DuplicateWidgetID 방지를 위해 유니크한 key 사용
            e_bf = st.data_editor(st.session_state.b_data_feed, hide_index=True, key="b_editor_final_2601",
                                  column_config={"Feedwater": st.column_config.NumberColumn(format="%.1f")})
            f_v = dict(zip(e_bf['Item'], e_bf['Feedwater']))

        with col_b2:
            st.markdown("###### ② 운전 조건 및 물질수지 (Water Balance)")
            b_steam = st.number_input("증기 생산량 (Steam, ton/hr)", value=10.0, key="b_steam_in_26")
            b_coc = st.slider("목표 농축배수 (CoC)", 2.0, 50.0, 15.0, 0.5, key="b_coc_in_26")
            
            # [물질수지 로직] 증기량 대비 배수량 및 급수량 산출
            b_blowdown = b_steam / (b_coc - 1) if b_coc > 1 else 0
            b_feedwater = b_steam + b_blowdown
            
            # 계산 결과 표시
            with st.container(border=True):
                m1, m2 = st.columns(2)
                m1.metric("계산된 급수량 (Feed)", f"{b_feedwater:.1f} t/h")
                m2.metric("계산된 배수량 (Blow)", f"{b_blowdown:.1f} t/h")
            
            st.write("---")
            b_dose_ppm = st.number_input("청관제 목표농도 (ppm, 급수대비)", value=100.0, step=10.0, key="b_dose_in_26")
            b_naoh_pct = st.number_input("청관제 내 가성소다(NaOH) 함량 (%)", value=20.0, step=1.0, key="b_naoh_in_26")
            
            # 가성소다 알칼리도 상승분 (NaOH 1ppm = 1.25ppm CaCO3)
            naoh_boost = b_dose_ppm * (b_naoh_pct / 100) * 1.25
            
            # 시뮬레이션 결과 저장 (Tab 2 연동용)
            st.session_state.b_res_store = {
                'steam': b_steam, 'feed': b_feedwater, 'blow': b_blowdown, 
                'coc': b_coc, 'dose_ppm': b_dose_ppm, 'naoh_pct': b_naoh_pct
            }

        # [수질 예측 계산]
        p_alk = (f_v['M-Alk (ppm)'] * b_coc) + naoh_boost
        p_ph = 9.3 + math.log10(max(p_alk, 1)) if p_alk > 0 else f_v['pH']
        p_ph = min(p_ph, 12.5)
        p_cond = (f_v['Cond (uS/cm)'] * b_coc) + (naoh_boost * 5.5)
        p_cl = f_v['Cl (ppm)'] * b_coc
        p_sio2 = f_v['SiO2 (ppm)'] * b_coc
        p_fe = f_v['Fe (ppm)'] * b_coc

        # ASME 체크
        try:
            _, l_cond = Boiler_Expert_Engine.check_asme_standard(10.0, p_cond, p_sio2, p_alk)
        except:
            l_cond = 3000.0

        st.divider()
        st.subheader(f"📊 보일러 관수 수질 예측 (농축 {b_coc}배)")
        
        # [출력 테이블] 모든 수치 f-string으로 소수점 1자리 고정
        p_df = pd.DataFrame({
            '측정 항목': ['pH (예측값)', 'Cond (uS/cm)', 'M-Alk (ppm)', 'SiO2 (ppm)', 'Cl (ppm)', 'Fe (ppm)'],
            '급수 (Feed)': [f"{f_v['pH']:.1f}", f"{f_v['Cond (uS/cm)']:.1f}", f"{f_v['M-Alk (ppm)']:.1f}", f"{f_v['SiO2 (ppm)']:.1f}", f"{f_v['Cl (ppm)']:.1f}", f"{f_v['Fe (ppm)']:.2f}"],
            '관수 (Predicted)': [f"{p_ph:.1f}", f"{p_cond:.1f}", f"{p_alk:.1f}", f"{p_sio2:.1f}", f"{p_cl:.1f}", f"{p_fe:.2f}"],
            'ASME 관리기준': ["10.5~11.5", f"{l_cond:.1f}", "P 비례", "P 비례", "-", "-"]
        })
        st.table(p_df)

    # --- Tab 2: Chemical Program (냉각수와 동일한 3단 구조) ---
    with tab_chem_prog:
        st.subheader("2. Integrated Boiler Chemical Program")
        res = st.session_state.b_res_store
        
        st.info(f"💡 **물질수지 기반 설계:** 급수량 {res['feed']:.1f} ton/hr | 청관제 목표 {res['dose_ppm']:.1f} ppm")
        st.markdown("---")
        
        c_col1, c_col2, c_col3 = st.columns(3)
        
        with c_col1:
            st.markdown("#### 🌬️ Oxygen Scavenger")
            oxy_list = PRODUCT_CATALOG['Boiler']['Oxygen_Scavenger']
            sel_oxy = st.selectbox("탈산제 선택", [o['Name'] for o in oxy_list], key="b_sel_oxy_final")
            oxy_dose = st.number_input("탈산제 농도 (ppm)", value=20.0, key="b_oxy_val_final")
            usage_oxy = (res['feed'] * 24 * oxy_dose) / 1000.0

        with c_col2:
            st.markdown("#### 🛡️ Scale Inhibitor")
            # 시뮬레이션 탭에서 입력한 주입량 자동 반영
            sel_scale = st.selectbox("청관제 선택", ["HBP-Standard"], key="b_sel_scale_final")
            scale_dose = st.number_input("청관제 농도 (ppm)", value=float(res['dose_ppm']), key="b_scale_val_final")
            usage_scale = (res['feed'] * 24 * scale_dose) / 1000.0

        with c_col3:
            st.markdown("#### 🧪 Condensate")
            sel_cond = st.selectbox("복수처리제 선택", ["HBC-100", "None"], key="b_sel_cond_final")
            cond_dose = st.number_input("기타 농도 (ppm)", value=5.0, key="b_cond_val_final")
            usage_cond = (res['feed'] * 24 * cond_dose) / 1000.0

        st.divider()
        st.markdown("### 📊 일일 약품 소요량 비교 (Daily Consumption)")
        
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
        c_h = (st.session_state.b_res_store['steam'] * 1000 * 620 / 8500 / 0.85) * f_cost
        st.metric("Estimated Hourly Fuel Cost", f"{int(c_h):,} KRW/hr")
# ==============================================================================
# [Module 3] RO Master Pro (에러 원천 차단 + 시각화 고도화 + 소수점 정렬)
# ==============================================================================
elif "RO" in program_mode:
    # 0. 세션 상태 초기화 (Tab 1, 2 보존용)
    if 'ro_v26_data' not in st.session_state:
        st.session_state.ro_v26_data = pd.DataFrame({
            '항목': ['Na', 'Ca', 'Mg', 'NH4', 'Cl', 'SO4', 'HCO3', 'F', 'SiO2', 'PO4'],
            '농도 (mg/L)': [150.0, 60.0, 20.0, 1.0, 200.0, 100.0, 150.0, 0.1, 20.0, 0.1]
        })
    if 'ro_adj_log' not in st.session_state:
        st.session_state.ro_adj_msg = "이온 보정 내역이 없습니다."

    st.title("🌊 RO Master Pro: Expert Solution")
    
    # --- [1. 전역 계산 엔진: 모든 에러의 원인을 여기서 차단] ---
    # 탭 내부가 아닌 여기서 모든 수치를 미리 계산하여 메모리에 올립니다.
    ro_df_main = st.session_state.ro_v26_data
    # 수치 변환 (소수점 처리를 위해 float 강제 적용)
    v_main = dict(zip(ro_df_main['항목'], pd.to_numeric(ro_df_main['농도 (mg/L)'], errors='coerce').fillna(0)))
    
    # 이온 밸런스 (meq/L)
    meq_cat = (v_main['Na']/23.0) + (v_main['Ca']/20.0) + (v_main['Mg']/12.2) + (v_main['NH4']/18.0)
    meq_ani = (v_main['Cl']/35.5) + (v_main['SO4']/48.0) + (v_main['HCO3']/61.0)
    b_err_final = ((meq_cat - meq_ani) / (meq_cat + meq_ani)) * 100 if (meq_cat + meq_ani) > 0 else 0

    # 사이드바 설정
    with st.sidebar:
        st.markdown("---")
        st.subheader("⚙️ Global Design Parameter")
        c_flow_side = st.number_input("현재 실제 유량 (m3/h)", value=80.0, step=1.0, key="side_f")
        c_cond_side = st.number_input("현재 실제 전도도 (μS/cm)", value=15.0, step=1.0, key="side_c")
        g_rec_side = st.slider("설계 회수율 (%)", 40.0, 90.0, 75.0, key="side_r")
        g_ph_side = st.slider("운전 pH", 4.0, 11.0, 7.5, key="side_p")

    # 농축 및 지수 계산
    cf_final = 1 / (1 - (g_rec_side / 100))
    brine_tds_final = sum(v_main.values()) * cf_final
    idx_label_final = "S&DSI" if brine_tds_final > 10000 else "LSI"

    # 스케일 잠재력 (Step 3, 4 공용 변수)
    sc_items_list = ['CaCO3', 'CaSO4', 'BaSO4', 'SiO2', 'PO4']
    u_pot_final = [
        (g_ph_side - 8.2) * 50 + 115, 
        (v_main['Ca'] * v_main['SO4'] * (cf_final**2)) / 24, 
        112.5, 
        (v_main['SiO2'] * cf_final) / 1.2, 
        (v_main['Ca'] * v_main['PO4'] * (cf_final**2)) / 0.5
    ]
    max_y_limit = max(u_pot_final) * 1.3 # 그래프 Y축 고정용

    # --- [2. UI 구성 (Tabs)] ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 수질 분석", "🔮 성능 열화", "🚨 정밀 진단", "💊 Chemical Program (약품)"])

    with tab1:
        st.subheader("Step 1. Water Analysis & Brine Prediction")
        col_t1_1, col_t1_2 = st.columns([1, 1.2])
        with col_t1_1:
            ed_ro = st.data_editor(st.session_state.ro_v26_data, hide_index=True, key="ro_editor_v26_final")
            if not ed_ro.equals(st.session_state.ro_v26_data):
                st.session_state.ro_v26_data = ed_ro
                st.rerun()
            if st.button("🚀 자동 이온 발란스 보정", key="btn_adj_v26"):
                diff = meq_ani - meq_cat
                if diff > 0:
                    val = diff * 23.0
                    st.session_state.ro_v26_data.loc[st.session_state.ro_v26_data['항목'] == 'Na', '농도 (mg/L)'] += val
                    st.session_state.ro_adj_msg = f"✅ **보정 내역:** 부족한 양이온을 채우기 위해 **Na+ 이온 {val:.1f} mg/L를 추가**했습니다."
                else:
                    val = abs(diff) * 35.5
                    st.session_state.ro_v26_data.loc[st.session_state.ro_v26_data['항목'] == 'Cl', '농도 (mg/L)'] += val
                    st.session_state.ro_adj_msg = f"✅ **보정 내역:** 부족한 음이온을 채우기 위해 **Cl- 이온 {val:.1f} mg/L를 추가**했습니다."
                st.rerun()
            st.info(st.session_state.ro_adj_msg)

        with col_t1_2:
            st.metric("이온 밸런스 오차", f"{b_err_final:.2f}%", delta="정상" if abs(b_err_final) <= 5.0 else "확인 요망")
            st.markdown(f"#### ✨ 예측 농축수 수질 (소수점 1자리 적용)")
            p_targets = ['Ca', 'SO4', 'SiO2', 'PO4']
            # [요청 1] 소수점 1자리 정렬 테이블
            st.table(pd.DataFrame({
                '항목': p_targets, 
                '원수 (Feed)': [f"{v_main[i]:.1f}" for i in p_targets], 
                '농축수 (Brine)': [f"{(v_main[i]*cf_final):.1f}" for i in p_targets]
            }))

    with tab2:
        st.subheader("Step 2. 성능 열화(Degradation) 시뮬레이션")
        # [요청 2] 수원별 가이드라인 복구
        with st.expander("💡 수원별 권장 연간 변화율 가이드 (Winflows)", expanded=False):
            st.markdown("| 수원 종류 | 연간 유량 감소 (A) | 연간 염투과 증가 (B) |\n| :--- | :---: | :---: |\n| **지하수** | 2~3% | 3~5% |\n| **표면수** | 5~7% | 10~12% |\n| **폐수** | 10~15% | 15~20% |")

        c_t2_1, c_t2_2 = st.columns(2)
        with c_t2_1: a_rate_s = st.slider("연간 유량 감소율 (%)", 0.0, 15.0, 5.0, key="a_s")
        with c_t2_2: b_rate_s = st.slider("연간 염투과 증가율 (%)", 0.0, 25.0, 10.0, key="b_s")
        op_y = st.slider("📅 멤브레인 사용 년수 (Years)", 0.0, 10.0, 3.0, 0.5, key="y_s")
        
        a_f = (1 - (a_rate_s / 100)) ** op_y
        b_f = (1 + (b_rate_s / 100)) ** op_y
        p_f, p_c = c_flow_side * a_f, c_cond_side * b_f

        m_t2_1, m_t2_2, m_t2_3 = st.columns(3)
        m_t2_1.metric("예상 생산 유량", f"{p_f:.1f} m³/h", f"{int((a_f-1)*100)}% 감소")
        m_t2_2.metric("예상 전도도", f"{p_c:.1f} μS/cm", f"+{int((b_f-1)*100)}% 상승", delta_color="inverse")
        m_t2_3.metric("A / B Factor", f"{a_f:.2f} / {b_f:.2f}")

        # 그래프 (보존)
        y_ax = np.linspace(0, 10, 21)
        f_cv = [c_flow_side * ((1 - (a_rate_s / 100)) ** y) for y in y_ax]
        c_cv = [c_cond_side * ((1 + (b_rate_s / 100)) ** y) for y in y_ax]
        g_t2_1, g_t2_2 = st.columns(2)
        with g_t2_1:
            fig_f = go.Figure(); fig_f.add_trace(go.Scatter(x=y_ax, y=f_cv, line=dict(color='#3498DB', width=3)))
            fig_f.add_trace(go.Scatter(x=[op_y], y=[p_f], mode='markers+text', text=[f"{p_f:.1f}"], textposition="top right", marker=dict(color='red', size=12)))
            st.plotly_chart(fig_f, use_container_width=True)
        with g_t2_2:
            fig_c = go.Figure(); fig_c.add_trace(go.Scatter(x=y_ax, y=c_cv, line=dict(color='#E74C3C', width=3)))
            fig_c.add_trace(go.Scatter(x=[op_y], y=[p_c], mode='markers+text', text=[f"{p_c:.1f}"], textposition="top right", marker=dict(color='black', size=12)))
            st.plotly_chart(fig_c, use_container_width=True)

    with tab3:
        # [요청 3] 정밀 진단 연동 확인
        st.subheader("🚨 Brine 정밀 진단 (Engineering Basis)")
        st.warning(f"💡 분석 근거: 농축수 TDS {brine_tds_final:.0f} ppm 기준 {idx_label_final} 지수 적용")
        st.plotly_chart(px.bar(x=sc_items_list, y=u_pot_final, color=sc_items_list, title="성분별 포화도 (%)", text_auto='.1f'), use_container_width=True)
        
        for name, pot in zip(sc_items_list, u_pot_final):
            if pot > 100: st.error(f"🔴 {name}: {pot:.1f}% (석출 위험)")
            else: st.success(f"🟢 {name}: {pot:.1f}% (안정)")

    with tab4:
        # [요청 4] 약품 변경 실시간 연동 및 Y축 동기화
        st.subheader("💊 Chemical Program (약품)")
        
        # 1. 자동 추천 로직
        rec_p = "HRD-3000" if u_pot_final[3] > 100 else "HRD-2200"
        st.success(f"🎯 **Technical Prescription:** {rec_p}")

        # [수정] 약품 선택 및 주입농도 입력 필드 추가
        c1, c2 = st.columns(2)
        with c1:
            sel_as = st.selectbox("🎯 처방 제품 선택:", [a['Name'] for a in PRODUCT_CATALOG['RO']['Antiscalant']], key="chem_v26")
            as_info = next(item for item in PRODUCT_CATALOG['RO']['Antiscalant'] if item['Name'] == sel_as)
        with c2:
            # 냉각수/보일러처럼 주입농도를 직접 입력할 수 있도록 number_input 추가
            ro_dosage = st.number_input("주입농도 (ppm)", value=float(as_info['Dosage']), step=0.5, key="ro_dosage_val")
        
        # 3. 효과 계산 (타겟 성분 85% 억제 로직 유지)
        t_pot = [p * 0.15 if any(t in as_info.get('Target', []) for t in [name, name[:2], 'LSI' if name == 'CaCO3' else '']) else p * 0.4 for name, p in zip(sc_items_list, u_pot_final)]

        # [요청] Y축 고정 그래프 (시각적 차이 극대화)
        cg1, cg2 = st.columns(2)
        with cg1:
            st.error("🚨 Untreated (미처리)")
            f_pre = px.bar(x=sc_items_list, y=u_pot_final, color_discrete_sequence=['#E74C3C'], text_auto='.1f')
            f_pre.update_layout(yaxis=dict(range=[0, max_y_limit]))
            st.plotly_chart(f_pre, use_container_width=True)
        with cg2:
            st.success(f"✅ Treated ({sel_as})")
            f_post = px.bar(x=sc_items_list, y=t_pot, color_discrete_sequence=['#2ECC71'], text_auto='.1f')
            f_post.update_layout(yaxis=dict(range=[0, max_y_limit]))
            st.plotly_chart(f_post, use_container_width=True)

        # [요청] 일일 약품 소요량 출력 (입력받은 ro_dosage 반영)
        st.divider()
        st.markdown("#### 📊 일일 약품 소요량 및 설계")
        m_e1, m_e2 = st.columns(2)
        # 계산 시 as_info['Dosage'] 대신 사용자가 입력한 ro_dosage를 사용합니다.
        usage_kg = (c_flow_side * 24 * ro_dosage) / 1000.0
        m_e1.metric(f"일일 {sel_as} 소요량", f"{usage_kg:.1f} kg/day")
        m_e2.metric("권장 CIP 탱크 용량", f"{(c_flow_side * 15 * 1.2):.0f} L")

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
    st.info("설비 규격 및 여재 충진량 산출을 위한 엔지니어링 도구입니다.")

    tab_afm, tab_ro_sizing = st.tabs(["🧪 AFM/Media Filter Sizing", "💧 RO System Sizing"])

    # --- [1. AFM/Media Filter Sizing] ---
    with tab_afm:
        st.subheader("Media Filter & AFM Filling Calculation")
        c1, c2 = st.columns(2)
        with c1:
            tank_d = st.number_input("Tank Diameter (mm)", value=2000, step=100)
            bed_h = st.number_input("Media Bed Height (mm)", value=1000, step=100)
            media_type = st.selectbox("Media Type", ["AFM (밀도 1.25)", "Sand (밀도 1.6)", "Anthracite (밀도 0.9)"])
        
        # 계산 로직
        radius = tank_d / 2000 # mm -> m
        height = bed_h / 1000 # mm -> m
        volume = math.pi * (radius ** 2) * height
        
        density = 1.25 if "AFM" in media_type else (1.6 if "Sand" in media_type else 0.9)
        weight = volume * density * 1000 # ton -> kg

        with c2:
            st.markdown("#### 🎯 Calculation Result")
            st.metric("소요 체적 (Volume)", f"{volume:.2f} m³")
            st.metric(f"{media_type.split(' ')[0]} 소요량", f"{weight:.1f} kg")
            st.caption(f"※ 탱크 하부 Support Gravel 및 Freeboard(약 40~50%)는 별도 고려하십시오.")

    # --- [2. RO System Sizing] ---
    with tab_ro_sizing:
        st.subheader("RO Membrane & Vessel Configuration")
        r1, r2 = st.columns(2)
        with r1:
            target_p = st.number_input("Target Permeate (m3/hr)", value=50.0)
            target_rec = st.slider("Target Recovery (%)", 50, 90, 75)
            design_flux = st.number_input("Design Flux (LMH)", value=18.0, help="폐수재이용: 12~18, 공업용수: 18~25")
            elements_per_vessel = st.selectbox("Elements per Vessel", [4, 5, 6, 7], index=2)

        # RO 계산 엔진
        feed_flow = target_p / (target_rec / 100)
        total_area_needed = (target_p * 1000) / design_flux
        # 8인치 막 표준 면적 400 ft2 = 약 37.2 m2 가정
        total_elements = math.ceil(total_area_needed / 37.2)
        total_vessels = math.ceil(total_elements / elements_per_vessel)

        with r2:
            st.markdown("#### 🎯 Engineering Summary")
            st.metric("Total Elements (8\")", f"{total_elements} EA", delta=f"Area: {total_area_needed:.1f} m²")
            st.metric("Total Pressure Vessels", f"{total_vessels} PV", delta=f"{elements_per_vessel} Elements/PV")
            st.write(f"- **Feed Flow:** {feed_flow:.1f} m³/hr")
            st.write(f"- **Brine Flow:** {feed_flow - target_p:.1f} m³/hr")