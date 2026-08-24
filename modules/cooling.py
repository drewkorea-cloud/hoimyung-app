import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import math
from utils.calculations import predict_ph_from_alkalinity, calculate_lsi, get_cooling_deep_audit, COND_TO_TDS_FACTOR, calculate_larson_skold, evaluate_corrosion_coupon, calculate_stress_index
from utils.report import generate_cooling_report_docx
from datetime import datetime
def interpolate(value, x_min, x_max, y_min, y_max):
    """구간 내 선형 보간 함수 (Linear Interpolation)"""
    if value <= x_min: return y_min
    if value >= x_max: return y_max
    return y_min + (value - x_min) * (y_max - y_min) / (x_max - x_min)

def calculate_solenis_complex(calcium, ph, temp_c, iron, tss):
    """Solenis 2017 가이드라인 정밀 구현 (Interpolation + Correction)"""
    
    req_ortho = 0.0; req_htd = 0.0; req_zpi = 0.0; mode = ""

    # 1. Base Active Requirements
    if ph >= 7.8:
        mode = "Alkaline (pH > 7.8)"
        if calcium <= 300:
            req_ortho = interpolate(calcium, 100, 300, 10.0, 7.0)
            req_htd = interpolate(calcium, 100, 300, 5.0, 9.0)
            req_zpi = interpolate(calcium, 100, 300, 7.5, 8.5)
        elif calcium <= 900:
            req_ortho = interpolate(calcium, 300, 900, 7.0, 4.0)
            req_htd = interpolate(calcium, 300, 900, 6.0, 10.0)
            req_zpi = interpolate(calcium, 300, 900, 8.5, 10.0)
        elif calcium <= 1400:
            req_ortho = interpolate(calcium, 900, 1400, 4.0, 3.0)
            req_htd = interpolate(calcium, 900, 1400, 8.0, 11.0)
            req_zpi = interpolate(calcium, 900, 1400, 10.0, 13.0)
        else:
            req_ortho = interpolate(calcium, 1400, 2000, 3.0, 2.0)
            req_htd = interpolate(calcium, 1400, 2000, 9.0, 12.0)
            req_zpi = interpolate(calcium, 1400, 2000, 13.0, 15.0)
    else:
        mode = "Neutral (pH < 7.8)"
        if calcium <= 200:
            req_ortho = interpolate(calcium, 100, 200, 20.0, 12.0)
            req_htd = interpolate(calcium, 100, 200, 2.0, 3.0)
            req_zpi = 3.0
        elif calcium <= 400:
            req_ortho = interpolate(calcium, 200, 400, 12.0, 10.0)
            req_htd = interpolate(calcium, 200, 400, 3.0, 5.0)
            req_zpi = 4.0
        elif calcium <= 1000:
            req_ortho = interpolate(calcium, 400, 1000, 10.0, 7.0)
            req_htd = interpolate(calcium, 400, 1000, 5.0, 10.0)
            req_zpi = interpolate(calcium, 400, 1000, 5.0, 8.0)
        else:
            req_ortho = 7.0; req_htd = 12.0; req_zpi = 10.0

    # 2. Correction Factors
    temp_f = (temp_c * 9/5) + 32
    add_htd_temp = (temp_f - 140) / 10.0 if temp_f > 140 else 0.0
    add_htd_iron = min(iron / 2.0, 10.0) if iron > 1.0 else 0.0
    add_htd_tss = (tss - 25) / 25.0 if tss > 25 else 0.0

    return {
        "Mode": mode,
        "MSP (부식방지)": round(req_ortho, 2),
        "BENEPOLY-304 (분산제)": round(req_htd + add_htd_temp + add_htd_iron + add_htd_tss, 2),
        "HPMA (스케일억제)": round(req_zpi, 2),
        "Corrections": f"Temp +{add_htd_temp:.1f} / Fe +{add_htd_iron:.1f}"
    }
# -------------------------------------------------------------------------
def app(PRODUCT_CATALOG):
    if 'makeup_data' not in st.session_state:
        st.session_state.makeup_data = pd.DataFrame({
            'Item': ['pH', 'Cond (µS)', 'Ca-H (ppm)', 'Mg-H (ppm)', 'M-Alk (ppm)', 'Cl (ppm)', 'SO4 (ppm)', 'SiO2 (ppm)'],
            'Value': [7.5, 200.0, 40.0, 10.0, 50.0, 20.0, 10.0, 10.0]
        })
    if 'cooling_results' not in st.session_state:
        st.session_state.cooling_results = None
    if 'deposit_data' not in st.session_state:
        st.session_state.deposit_data = pd.DataFrame({
            'item': ['Sulfate(SO4)', 'Aluminium(Al2O3)', 'Calcium(CaO)', 'Copper(CuO)', 'Iron Oxide (Fe2O3)', 'Potasium(K2O)', 'Magnesium(MgO)', 'Manganese(MnO)', 'Sodium(Na2O)', 'Phosphate (P2O5)', 'Silica(SiO2)', 'Acid InSolubles', 'Zinc(ZnO)', 'Nickel(NiO)', 'Vanadium(V2O3)', 'Chromium(Cr2O3)'],
            'Result (%)': [23.48, 45.49, 0.10, 0.01, 0.23, 0.01, 0.05, 0.01, 0.02, 0.10, 1.53, 0.86, 0.01, 0.01, 0.00, 0.07]
        })

    st.title("❄️ Cooling Tower Master (Global Expert Ver.)")
    st.info("Scale/Corrosion/Deposit 통합 진단 및 성분 분석 시스템")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💧 Water Balance (물질수지)", 
        "⚗️ Water Chemistry (수질진단)",
        "📐 3. 정밀설계 (Design)",
        "💊 Chemical Program (약품)", 
        "🔬 Lab & Deposit (성분분석)",
        "📘 기술 매뉴얼 (Formula)",
    ])

    with tab1:
        st.subheader("1. Cooling Tower Design Data")
        col_season, col_dummy = st.columns([1, 1])
        with col_season:
            season_mode = st.selectbox("📅 운전 계절 (Season Factor)", ["Summer (여름/혹서기)", "Spring/Fall (봄/가을)", "Winter (겨울/혹한기)"])
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
        st.session_state['vol_system'] = holding_vol 
       
        if blowdown > 0: 
            hti = 0.693 * holding_vol / (blowdown + windage) 
        else: 
            hti = 999.9
        st.session_state['final_hti'] = hti
        st.markdown("---")
        
        c_chart, c_metric = st.columns([1.2, 1])
        with c_chart:
            labels = ['Evaporation (증발)', 'Blowdown (배수)', 'Windage (비산)']
            values = [evap, blowdown, windage]
            fig_bal = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker_colors=['#3498DB', '#E74C3C', '#95A5A6'], textinfo='percent+label')])
            fig_bal.update_layout(title_text="Water Usage Breakdown", height=320, margin=dict(t=40, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_bal, use_container_width=True)

        with c_metric:
            st.subheader("📊 Operation Summary")
            op_m1, op_m2, op_m3 = st.columns(3)
            with op_m1:
                st.metric("증발량 (Evap)", f"{evap:.1f} m³/hr", f"Factor {evap_factor:.4f}")
                st.metric("보급수 (Make-up)", f"{makeup:.1f} m³/hr")
            with op_m2:
                st.metric("배수량 (Blowdown)", f"{blowdown:.1f} m³/hr")
                ht_msg = "✅ Good"
                ht_color = "normal"
                if hti > 48: ht_msg = "⚠️ Long"; ht_color = "inverse"
                elif hti < 4: ht_msg = "⚠️ Short"; ht_color = "inverse"
                st.metric("반감기 (Half Life)", f"{hti:.1f} hr", delta=ht_msg, delta_color=ht_color)
            with op_m3:
                st.metric("비산수량 (Windage)", f"{windage:.2f} m³/hr", "0.05% Loss")
                st.caption(f"💧 **보유수량:** {holding_vol:.0f} m³")

    with tab2:
        st.subheader("2. Prediction & Diagnosis Simulator")
        st.markdown("보충수 수질을 기반으로 순환수를 예측하고, **Skin Temperature(열교환기 표면)** 기준의 정밀 진단을 수행합니다.")
        if 'makeup_data_v5' not in st.session_state:
            st.session_state.makeup_data_v5 = pd.DataFrame({
                'Item': ['pH', 'Cond (µS)', 'Ca-H (ppm)', 'M-Alk (ppm)', 'Cl (ppm)', 'SO4 (ppm)', 'SiO2 (ppm)', 'Fe (ppm)', 'Turbidity (NTU)'],
                'Value': [7.5, 200.0, 40.0, 50.0, 20.0, 10.0, 10.0, 0.1, 2.0]
            })
        if 'cooling_limits_v5' not in st.session_state:
            st.session_state.cooling_limits_v5 = {
                "pH": "8.3~9.0", "Calcium (Ca-H)": "800", "M-Alkalinity": "500", "Chloride (Cl)": "500", "Sulfate (SO4)": "1200",
                "Silica (SiO2)": "150", "Conductivity": "5000", "Iron (Fe)": "1.0", "Turbidity (NTU)": "20"
            }
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
            st.markdown("---")
            st.markdown("###### ③ 열교환기 부하 조건 (Heat Load Stress)")
            st.info("💡 공장 내 **가장 뜨거운 설비(Bottleneck)**를 기준으로 선택하세요.")
            heat_load_type = st.radio("가장 가혹한 열교환기 타입은?", ["🟢 저부하 (오일쿨러/공조기)", "🟡 표준 (화학/사출/반도체)", "🔴 고부하 (제철/발전/응축기)"], index=1, horizontal=True)
            if "고부하" in heat_load_type: skin_offset = 25.0; st.caption(f"🔥 **Skin Temp 보정: +25℃** (예상 표면온도: {sim_temp + 25}℃)")
            elif "표준" in heat_load_type: skin_offset = 15.0; st.caption(f"⚙️ **Skin Temp 보정: +15℃** (예상 표면온도: {sim_temp + 15}℃)")
            else: skin_offset = 5.0; st.caption(f"❄️ **Skin Temp 보정: +5℃** (예상 표면온도: {sim_temp + 5}℃)")
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
                est_ph = predict_ph_from_alkalinity(cycle_alk, sim_temp)
                phase_msg = "AI Prediction (Chart Logic)"
                target_ph = st.number_input(f"Predicted pH ({phase_msg})", value=float(f"{est_ph:.2f}"), disabled=True)
            
            if st.button("🚀 Run Simulation (비교 분석)", type="primary", use_container_width=True):
                st.session_state.makeup_data_v5 = edited_mu 
                mu_dict = dict(zip(edited_mu['Item'], edited_mu['Value']))
                pred_ca = mu_dict['Ca-H (ppm)'] * target_coc
                pred_cl = mu_dict['Cl (ppm)'] * target_coc
                pred_sio2 = mu_dict['SiO2 (ppm)'] * target_coc
                pred_cond = mu_dict['Cond (µS)'] * target_coc
                pred_fe = mu_dict.get('Fe (ppm)', 0.1) * target_coc
                pred_turb = mu_dict.get('Turbidity (NTU)', 1.0) * target_coc
                if use_acid:
                    pred_alk = mu_dict['M-Alk (ppm)'] * target_coc * 0.6
                    acid_so4 = (mu_dict['M-Alk (ppm)'] * target_coc) * 0.9
                    pred_so4 = (mu_dict['SO4 (ppm)'] * target_coc) + acid_so4
                else:
                    pred_alk = mu_dict['M-Alk (ppm)'] * target_coc
                    pred_so4 = mu_dict['SO4 (ppm)'] * target_coc

                lsi_bulk = calculate_lsi(target_ph, pred_cond * COND_TO_TDS_FACTOR, pred_ca, pred_alk, sim_temp)
                lsi_skin = calculate_lsi(target_ph, pred_cond * COND_TO_TDS_FACTOR, pred_ca, pred_alk, sim_temp + skin_offset)
                pHs = target_ph - lsi_bulk  # calculate_lsi()가 이미 계산한 pHs를 역산해 재사용 (중복 계산 제거)
                rsi = (2 * pHs) - target_ph
                p_eq = 1.465 * math.log10(max(pred_alk, 1)) + 4.54
                psi = (2 * pHs) - p_eq
                ls_idx = calculate_larson_skold(pred_cl, pred_so4, pred_alk)
                st.session_state.sim_results = {
                    'mu_dict': mu_dict, 'pred_ca': pred_ca, 'pred_alk': pred_alk, 'pred_cl': pred_cl, 'pred_so4': pred_so4, 'pred_sio2': pred_sio2,
                    'pred_fe': pred_fe, 'pred_turb': pred_turb, 'pred_cond': pred_cond, 'target_ph': target_ph,
                    'lsi': lsi_bulk, 'lsi_skin': lsi_skin, 'rsi': rsi, 'psi': psi, 'ls_idx': ls_idx, 'target_coc': target_coc, 'skin_offset': skin_offset
                }
                st.session_state['sim_lsi'] = lsi_bulk
                st.session_state['sim_target_ph'] = target_ph
                st.session_state.run_simulation = True

        if st.session_state.run_simulation:
            res = st.session_state.sim_results
            limits = st.session_state.cooling_limits_v5
            st.divider()
            st.subheader(f"📊 수질 예측 비교 분석 (농축배수: {res['target_coc']}배)")
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
                df_comp, column_config={"Item": st.column_config.TextColumn("항목", disabled=True), "Make-up": st.column_config.NumberColumn("보충수", format="%.1f", disabled=True), "Cooling (Pred)": st.column_config.NumberColumn("순환수 (예측)", format="%.1f", disabled=True), "Limit (Max)": st.column_config.TextColumn("관리 기준 (자유입력)", width="medium", help="범위(~) 또는 상한값 입력")},
                hide_index=True, use_container_width=True, key="limit_editor_simple_v5"
            )
            for index, row in edited_comp.iterrows(): st.session_state.cooling_limits_v5[row['Item']] = str(row['Limit (Max)'])
            warnings = []
            for index, row in edited_comp.iterrows():
                try:
                    limit_val = float(row['Limit (Max)']) 
                    if row['Cooling (Pred)'] > limit_val: warnings.append(f"⚠️ **{row['Item']}** 기준 초과 ({row['Cooling (Pred)']:.1f} > {limit_val:.0f})")
                except ValueError: pass
            if warnings:
                with st.container(border=True):
                    st.error("🚨 **관리 기준 초과 경보**")
                    for w in warnings: st.write(w)
            else: st.success("✅ **Stable Operation** (특이사항 없음)")

            stress = calculate_stress_index(res['lsi'], res['rsi'], res['psi'], res['ls_idx'])
            stress_color = {"안정": "normal", "주의": "normal", "경고": "inverse", "위험": "inverse"}[stress['band']]
            with st.container(border=True):
                sc1, sc2 = st.columns([1, 2.2])
                with sc1:
                    st.metric("🧭 통합 스트레스 지수", f"{stress['score']:.0f} / 100", stress['band'], delta_color=stress_color,
                              help="LSI/RSI/PSI/L-S 4개 지수를 가중합산한 자체 참고 지표입니다 (날코 NSI를 그대로 재현한 것은 아닙니다).")
                with sc2:
                    st.progress(min(stress['score'] / 100.0, 1.0))
                    st.caption(f"기여도 — LSI {stress['breakdown']['LSI']:.0f} · RSI {stress['breakdown']['RSI']:.0f} · PSI {stress['breakdown']['PSI']:.0f} · L-S {stress['breakdown']['L-S']:.0f} (100점 만점 환산)")

            st.markdown("#### 🧭 5대 핵심 지수 진단 (Skin Temp 반영)")
            m1, m2, m3, m4, m5 = st.columns(5)
            lsi = res['lsi']
            lsi_col = "inverse" if lsi > 1.5 or lsi < 0 else "normal"
            m1.metric("1. LSI (Bulk)", f"{lsi:.2f}", "물 온도 기준", delta_color=lsi_col)
            lsi_skin = res['lsi_skin']
            skin_msg = "Safe"; skin_col = "normal"
            if lsi_skin > 2.5: skin_msg = "Critical!"; skin_col = "inverse"
            elif lsi_skin > 2.0: skin_msg = "Warning"; skin_col = "inverse"
            m2.metric("2. LSI (Skin)", f"{lsi_skin:.2f}", skin_msg, delta_color=skin_col, help=f"가장 뜨거운 열교환기 표면 온도 기준 (수온+{res['skin_offset']:.0f}℃)")
            rsi = res['rsi']
            rsi_state = "Stable"
            if rsi < 5.0: rsi_state = "Scale Risk"
            elif rsi > 8.5: rsi_state = "Corr Risk"
            m3.metric("3. RSI (General)", f"{rsi:.2f}", rsi_state, delta_color="inverse" if "Risk" in rsi_state else "normal")
            ls_idx = res['ls_idx']
            ls_msg = "Safe"; ls_col = "normal"
            if ls_idx > 1.2: ls_msg="Pitting!"; ls_col="inverse"
            m4.metric("4. Pitting (L-S)", f"{ls_idx:.2f}", ls_msg, delta_color=ls_col)
            pred_turb = res['pred_turb']
            dep_msg = "Clean"; dep_col = "normal"
            if pred_turb > 20: dep_msg="Deposit!"; dep_col="inverse"
            m5.metric("5. Turbidity", f"{pred_turb:.1f} NTU", dep_msg, delta_color=dep_col)
            
            st.markdown("---")
            st.subheader("📈 농축배수 최적화 시뮬레이션 (Cycle Study)")
            st.info("💡 농축배수를 **2배 ~ 10배**까지 변화시켰을 때, 스케일(LSI)과 부식 지수(PSI)가 어떻게 변하는지 추세를 분석합니다.")
            mu_ph = res['mu_dict']['pH']; mu_cond = res['mu_dict']['Cond (µS)']; mu_ca = res['mu_dict']['Ca-H (ppm)']; mu_alk = res['mu_dict']['M-Alk (ppm)']; temp_c = st.session_state.sim_temp
            cycles_range = np.arange(2.0, 10.5, 0.5)
            sim_data = []
            for coc in cycles_range:
                pred_alk_c = mu_alk * coc
                if pred_alk_c < 1: pred_alk_c = 1
                pred_ph_c = predict_ph_from_alkalinity(pred_alk_c, temp_c)
                pred_ca_c = mu_ca * coc
                lsi_c = calculate_lsi(pred_ph_c, mu_cond * coc * COND_TO_TDS_FACTOR, pred_ca_c, pred_alk_c, temp_c)
                pHs_c = pred_ph_c - lsi_c  # calculate_lsi()가 이미 계산한 pHs를 역산해 재사용 (중복 계산 제거)
                p_eq_c = 1.465 * math.log10(max(pred_alk_c, 1)) + 4.54
                psi_c = (2 * pHs_c) - p_eq_c
                sim_data.append({"Cycles": coc, "LSI": lsi_c, "PSI": psi_c, "pH": pred_ph_c})
            df_sim = pd.DataFrame(sim_data)
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                fig_lsi = px.line(df_sim, x="Cycles", y="LSI", markers=True, title="Cycles vs LSI (스케일 경향)")
                fig_lsi.add_hline(y=2.5, line_dash="dash", line_color="red", annotation_text="Danger Limit (+2.5)")
                fig_lsi.add_hline(y=1.5, line_dash="dot", line_color="orange", annotation_text="Warning")
                fig_lsi.add_vline(x=res['target_coc'], line_dash="dot", line_color="green", annotation_text="현재 운전점")
                st.plotly_chart(fig_lsi, use_container_width=True)
            with c_g2:
                fig_psi = px.line(df_sim, x="Cycles", y="PSI", markers=True, title="Cycles vs PSI (안정성 지수)")
                fig_psi.add_hrect(y0=5.0, y1=6.0, fillcolor="green", opacity=0.1, annotation_text="Best Zone")
                fig_psi.add_hline(y=4.0, line_dash="dash", line_color="red", annotation_text="Scale Risk")
                fig_psi.add_vline(x=res['target_coc'], line_dash="dot", line_color="green", annotation_text="현재 운전점")
                st.plotly_chart(fig_psi, use_container_width=True)
            safe_df = df_sim[(df_sim['LSI'] < 2.5) & (df_sim['PSI'] > 4.0)]
            if not safe_df.empty: best_cycle = safe_df['Cycles'].max(); st.success(f"✅ 시뮬레이션 결과, 약품 처리 하에 **최대 {best_cycle}배**까지 운전 가능합니다.")
            else: st.warning("⚠️ 전 구간에서 스케일 위험이 높습니다. 고성능 스케일 방지제가 필수적입니다.")

        st.divider()
        with st.expander("📘 지수별 상세 관리 기준 (Reference - 항상 표시)", expanded=True):
            st.markdown("### 1. LSI (Langelier Saturation Index)")
            st.markdown("""| 범위 (Range) | 상태 (Condition) | 현상 및 위험 | 관리 대책 (Action) |\n| :--- | :---: | :--- | :--- |\n| **+2.0 이상** | **심각한 스케일** | 배관 막힘, 열효율 급감 | 산(Acid) 주입, 블로우다운 증대 |\n| **+0.5 ~ +2.0** | **약한 스케일** | **[관리 범위]** 얇은 막 형성 | 스케일 방지제(Inhibitor) 제어 |\n| **-0.5 ~ +0.5** | **안정 (Stable)** | 이상적 상태 | 현재 상태 유지 |\n| **-0.5 ~ -2.0** | **약한 부식** | 배관이 서서히 얇아짐 | 방식제(Zn, PO4) 농도 상향 |\n| **-2.0 이하** | **심각한 부식** | 녹물 발생 (Red Water) | pH 상승, 부식 억제제 대량 투입 |""")
            c_g1, c_g2 = st.columns(2)
            with c_g1: st.markdown("### 2. Skin LSI (표면온도 기준)\n* **< 2.0 (안전):** 열교환기 표면도 깨끗함.\n* **2.0 ~ 2.5 (경고):** 고온부(Hot Spot) 스케일 시작.\n* **> 2.5 (위험):** **즉각 조치 필요.** 물은 맑아도 설비는 막히고 있음.\n\n### 3. RSI (Ryznar Stability Index)\n* **4.0 ~ 5.0:** 강한 스케일 (막힘 주의)\n* **5.0 ~ 6.0:** **[최적]** 약한 코팅막 형성\n* **> 8.0:** 강한 부식 (녹물 발생)")
            with c_g2: st.markdown("### 4. L-S Index (부식 지수)\n* **< 0.8 (안전):** 부식 억제력 충분.\n* **0.8 ~ 1.2 (주의):** 국부 부식(Pitting) 가능성.\n* **> 1.2 (위험):** **점부식 경고.** 염소($Cl$) 농도를 낮춰야 함.\n\n### 5. 탁도 & 철분 (오염 지표)\n* **탁도 (Turbidity):** `> 20 NTU` 시 침적(Deposit) 부식 위험. 여과기 가동 필요.\n* **철분 (Fe):** `> 1.0 ppm` 시 배관 부식 진행 중이거나 원수 오염 의심.")
    with tab3:
        st.subheader("3. Advanced Engineering Design (Solenis Logic)")
        st.markdown("수질 진단 결과를 바탕으로 **글로벌 가이드라인**에 따른 **필요 유효 성분(Target Actives)**을 설계합니다.")
        
        if st.session_state.get('run_simulation') and 'sim_results' in st.session_state:
            sim = st.session_state.sim_results
            des_ca = sim.get('pred_ca', 200.0)
            des_ph = sim.get('target_ph', 8.2)
            des_temp = st.session_state.get('sim_temp', 35.0)
            des_fe = sim.get('pred_fe', 0.1)
            des_turb = sim.get('pred_turb', 1.0)
            
            st.info(f"📊 **설계 기준 (Design Basis):** Ca {des_ca:.0f} ppm / pH {des_ph} / Temp {des_temp}℃ / Fe {des_fe:.1f} ppm")
            
            try:
                design_res = calculate_solenis_complex(des_ca, des_ph, des_temp, des_fe, des_turb)
            except NameError:
                st.error("🚨 'calculate_solenis_complex' 함수가 정의되지 않았습니다.")
                st.stop()
            
            st.divider()

            # [Dashboard] 
            col_d1, col_d2 = st.columns([1.5, 1])
            with col_d1:
                st.markdown("#### 🧬 성분 요구량 설계 (Target Actives)")
                st.caption(f"운전 모드: **{design_res.get('Mode', '알 수 없음')}**")
                
                c_a, c_b, c_c = st.columns(3)
                t_po4_val = design_res.get('MSP (부식방지)', 0.0)
                zpi_val = design_res.get('HPMA (스케일억제)', 0.0)
                poly_val = design_res.get('BENEPOLY-304 (분산제)', 0.0)

                # 파란색 강조 적용
                c_a.metric("1. 방식제 (T-PO4)", f"{t_po4_val} ppm")
                c_b.metric("2. 스케일억제 (ZPI)", f"{zpi_val} ppm")
                c_c.metric("3. 분산제 (Polymer)", f"{poly_val} ppm")
                
                st.warning(f"💡 **환경 보정:** {design_res.get('Corrections', '내역 없음')}")

            with col_d2:
                st.markdown("#### ⚖️ 설계 배합비 (Ratio)")
                labels = ['T-PO4', 'ZPI', 'Polymer']
                values = [t_po4_val, zpi_val, poly_val]
                fig_design = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5)])
                fig_design.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=200, showlegend=False)
                st.plotly_chart(fig_design, use_container_width=True)

            st.divider()
            
            # [Engineering Report]
            with st.expander("📘 [엔지니어링 리포트] 정밀 설계 산출 근거 상세", expanded=True):
                st.markdown("### 1️⃣ 성분별 정밀 설계 기준")
                
                # 3개 컬럼으로 수정 (오류 해결 지점)
                c_rep1, c_rep2, c_rep3 = st.columns(3)
                
                with c_rep1:
                    st.markdown("#### 🛡️ 방식 설계 (T-PO4)")
                    st.markdown(f"**설계치: :blue[{t_po4_val} ppm]**") # 파란색 적용
                    st.caption("금속 표면에 부동태 피복을 형성합니다. 중합인산 및 PBTC와 같은 유기인산의 인산 전환값을 모두 포함한 분석 기준 농도입니다.")
                
                with c_rep2:
                    st.markdown("#### 💎 억제 설계 (ZPI)")
                    st.markdown(f"**설계치: :blue[{zpi_val} ppm]**") # 파란색 적용
                    st.caption(f"스케일 억제의 핵심 엔진인 **HPMA 폴리머** 기준 설계치입니다. HPMA는 결정 성장을 강력히 방해하며, PBTC는 이를 보강함과 동시에 방식막 형성을 돕는 보조 역할을 수행합니다.")
                
                with c_rep3:
                    st.markdown("#### 🧪 분산 성분 (Polymer)")
                    st.markdown(f"**설계치: :blue[{poly_val} ppm]**") # 파란색 적용
                    st.caption("고분자 Terpolymer 농도입니다. 미세 스케일과 철분을 분산시켜 Blowdown으로 강제 배출함으로써 열교환기 효율을 유지합니다.")

                st.markdown("---")

                # [가이드라인 표 2종]
                st.markdown("### 2️⃣ Solenis 원본 가이드라인 참조 (Table 3 & 4)")
                tab_ref1, tab_ref2 = st.tabs(["📊 Alkaline Program (Table 3)", "📊 Neutral Program (Table 4)"])
                
                with tab_ref1:
                    st.caption("pH 7.8 이상 운전 시 적용")
                    df3 = pd.DataFrame({
                        "Calcium (ppm)": ["100-300", "300-900", "900-1400", "1400-2000"],
                        "T-PO4 (ppm)": ["10.0-7.0", "7.0-4.0", "4.0-3.0", "3.0-2.0"],
                        "ZPI (ppm)": ["7.5-8.5", "8.5-10.0", "10.0-13.0", "13.0-15.0"],
                        "Polymer (ppm)": ["5.0-9.0", "6.0-10.0", "8.0-11.0", "9.0-12.0"]
                    })
                    st.table(df3)
                    if des_ph >= 7.8: st.success("👈 현재 시스템이 적용 중인 가이드라인입니다.")

                with tab_ref2:
                    st.caption("pH 7.8 미만 운전 시 적용")
                    df4 = pd.DataFrame({
                        "Calcium (ppm)": ["100-200", "200-400", "400-1000", "1000+"],
                        "T-PO4 (ppm)": ["20.0-12.0", "12.0-10.0", "10.0-7.0", "7.0"],
                        "ZPI (ppm)": ["3.0", "4.0", "5.0-8.0", "10.0"],
                        "Polymer (ppm)": ["2.0-3.0", "3.0-5.0", "5.0-10.0", "12.0"]
                    })
                    st.table(df4)
                    if des_ph < 7.8: st.success("👈 현재 시스템이 적용 중인 가이드라인입니다.")

                st.markdown("---")
                st.markdown("### 3️⃣ 스트레스 팩터 보정 (Environmental Adjustment)")
                c_f1, c_f2, c_f3 = st.columns(3)
                
                with c_f1:
                    val_t = (des_temp-60)/5 if des_temp > 60 else 0
                    st.metric("온도 보정", f"+{val_t:.1f} ppm" if val_t > 0 else "양호")
                with c_f2:
                    val_f = min(des_fe/2.0, 10.0) if des_fe > 1.0 else 0
                    st.metric("철분 보정", f"+{val_f:.1f} ppm" if val_f > 0 else "양호")
                with c_f3:
                    val_tb = (des_turb-25)/25 if des_turb > 25 else 0
                    st.metric("탁도 보정", f"+{val_tb:.1f} ppm" if val_tb > 0 else "양호")

            st.success("✅ **정밀 설계 완료:** 위 수치는 Tab 4 제품 매칭의 기준이 됩니다.")
            st.session_state['design_actives'] = design_res
        else:
            st.warning("⚠️ **Tab 2 (수질진단)**에서 시뮬레이션을 먼저 실행해주세요.")

    with tab4:
        st.subheader("4. Intelligent Chemical Selection System")
        st.markdown("수질/미생물 분석 및 스케일 경향에 따른 **최적 약품(Inhibitor/Biocide)**을 선정합니다.")
        if st.session_state.get('run_simulation') and 'sim_results' in st.session_state:
            sim = st.session_state.sim_results
            real_lsi = sim.get('lsi', 1.5); real_rsi = sim.get('rsi', 6.0); real_cl = sim.get('pred_cl', 100.0)
            real_so4 = sim.get('pred_so4', 50.0); real_alk = sim.get('pred_alk', 100.0); real_ca = sim.get('pred_ca', 200.0)
            real_ph = sim.get('target_ph', 8.2); real_temp = st.session_state.get('sim_temp', 30.0)
            real_psi = sim.get('psi', 5.5); real_ls_idx = sim.get('ls_idx', 0.5)
            try:
                bd_rate = st.session_state.get('final_blowdown', 0.0); sys_vol_val = st.session_state.get('vol_m3', 100.0)
                real_ht = sys_vol_val / bd_rate if bd_rate > 0 else 48.0
            except: real_ht = 48.0
            data_status = "✅ 시뮬레이션 데이터 연동됨"
        else:
            real_lsi, real_rsi = 2.0, 5.0; real_cl, real_so4 = 150.0, 80.0
            real_alk, real_ca = 100.0, 200.0; real_ph, real_temp = 8.2, 30.0; real_ht = 24.0
            real_psi, real_ls_idx = 5.5, 0.5
            data_status = "⚠️ 기본값 (시뮬레이션 미실행)"
        
        with st.expander("🔎 **[현장 진단] 수질 및 미생물 측정값 입력 (Optional)**", expanded=True):
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1: target_cl2 = st.number_input("잔류염소 (ppm)", value=0.2, step=0.1, help="운전 관리 기준")
            with f_col2: meas_bacteria = st.number_input("일반세균 (CFU/mL)", value=0, step=1000, help="최근 측정된 세균수")
            with f_col3: meas_srb = st.checkbox("SRB(황산염환원균) 검출", help="검출 시 체크")
            with f_col4: meas_ph = st.number_input("실측 pH", value=0.0, step=0.1, help="현장 측정 pH (비교용)")

            st.markdown("###### 🧪 부식쿠폰 실측치 (Corrosion Coupon, mpy)")
            cp_col1, cp_col2, cp_col3 = st.columns([1, 1, 2])
            with cp_col1: meas_ms_mpy = st.number_input("Mild Steel (mpy)", value=0.0, step=0.1, min_value=0.0, help="부식쿠폰 랙에서 회수한 연강 쿠폰의 실측 부식률")
            with cp_col2: meas_cu_mpy = st.number_input("Copper (mpy)", value=0.0, step=0.05, min_value=0.0, help="부식쿠폰 랙에서 회수한 동 쿠폰의 실측 부식률")
            coupon_result = None
            if meas_ms_mpy > 0 or meas_cu_mpy > 0:
                coupon_result = evaluate_corrosion_coupon(meas_ms_mpy, meas_cu_mpy)
                with cp_col3:
                    sev_icon = {"good": "✅", "caution": "⚠️", "bad": "🚨"}
                    st.markdown(
                        f"{sev_icon[coupon_result['ms']['severity']]} **MS {meas_ms_mpy:.1f} mpy → {coupon_result['ms']['grade']}**"
                        f"&nbsp;&nbsp;|&nbsp;&nbsp;"
                        f"{sev_icon[coupon_result['cu']['severity']]} **Cu {meas_cu_mpy:.2f} mpy → {coupon_result['cu']['grade']}**"
                    )
                    st.caption("기준: MS 우수<1.0·양호<3.0·보통<5.0 / Cu 우수<0.2·양호<0.5·높음<1.0 mpy (담수 냉각수 업계 표준)")
        col_set1, col_set2 = st.columns([1, 2])
        with col_set1: target_cl2 = st.number_input("운전 관리 잔류염소 (ppm)", value=0.2, step=0.1, help="살균을 위해 유지할 잔류염소 농도입니다. 0.5ppm 이상이면 HEDP 분해 경고가 뜹니다.")
        with col_set2: st.info(f"💡 현재 설정된 잔류염소 농도는 **{target_cl2} ppm** 입니다. (0으로 설정 시 경고 해제)")
        
        audit_logs = get_cooling_deep_audit(real_lsi, real_rsi, real_cl, real_so4, real_alk, real_ca, real_temp, real_ht, target_cl2, real_ph, meas_bacteria, meas_srb, meas_ph)
        st.markdown("---")
        with st.expander("📋 **[클릭] 약품 선정 전 심층 분석 보고서**", expanded=True):
            for log in audit_logs:
                if log.startswith("####"): st.markdown(log)
                elif "🔴" in log or "🔥" in log or "🚨" in log: st.error(log)
                elif "⚠️" in log or "🐢" in log or "💸" in log or "🔵" in log: st.warning(log)
                elif "✅" in log: st.success(log)
                else: st.write(log)

        if coupon_result:
            predicted_corrosive = real_lsi < 0 or real_rsi > 8.5
            ms_bad = coupon_result['ms']['severity'] == 'bad'
            cu_bad = coupon_result['cu']['severity'] == 'bad'
            with st.container(border=True):
                st.markdown("###### 🔬 예측 지수 vs 실측 부식쿠폰 비교")
                if predicted_corrosive and not (ms_bad or cu_bad):
                    st.info("💡 LSI/RSI는 부식성 수질로 예측했지만, 실측 부식쿠폰은 양호합니다. 현재 방식제 프로그램이 잘 작동 중일 가능성이 높습니다.")
                elif not predicted_corrosive and (ms_bad or cu_bad):
                    st.warning("⚠️ 지수상으로는 안정 범위인데 실측 부식쿠폰이 불량합니다. 지수가 놓친 국부부식(Pitting)·미생물 부식 등 다른 원인을 점검하세요.")
                elif predicted_corrosive and (ms_bad or cu_bad):
                    st.error("🚨 예측 지수와 실측 쿠폰이 모두 부식 위험을 가리킵니다. 방식제 프로그램 재점검이 시급합니다.")
                else:
                    st.success("✅ 예측 지수와 실측 부식쿠폰이 모두 안정 범위로 일치합니다.")

        cooling_db = PRODUCT_CATALOG.get('Cooling', {})
        inh_list = cooling_db.get('Main_Inhibitor', []); disp_list = cooling_db.get('Dispersant', []); bio_list = cooling_db.get('Biocide', [])
        if not inh_list: st.error("🚨 약품 DB 로드 실패"); st.stop()
        
        rec_prod_name = inh_list[0]['Name']; rec_reason = "기본 추천"
        if target_cl2 >= 0.5:
            match = next((p for p in inh_list if "180" in p['Name'] or "PBTC" in str(p.get('Main_Ingredient',''))), None)
            if match: rec_prod_name = match['Name']; rec_reason = f"🔥 **염소 내성 강화:** 설정하신 잔류염소({target_cl2}ppm)가 높아 산화에 강한 **PBTC** 제품을 선정했습니다."
        elif real_lsi > 2.5:
            match = next((p for p in inh_list if "308" in p['Name'] or "524" in p['Name']), None)
            if match: rec_prod_name = match['Name']; rec_reason = f"🔴 **고부하 대응:** LSI({real_lsi:.2f})가 매우 높아 강력한 **Terpolymer** 복합제를 선정했습니다."
        elif real_lsi < 0.5:
            match = next((p for p in inh_list if "110" in p['Name'] or "Zinc" in str(p.get('Main_Ingredient',''))), None)
            if match:
                rec_prod_name = match['Name']
                if real_ph > 8.2: rec_reason = f"⚠️ **pH 주의 ({real_ph:.1f}):** pH가 높아 아연 슬러지 발생 위험이 있습니다. 하지만 **'분산제(Polymer)' 함량이 높은 제품**을 선정하면 아연을 안정화하여 사용 가능합니다."
                else: rec_reason = f"🔵 **방식 처리:** 저경도/부식성 수질(LSI {real_lsi:.2f})이므로 **아연(Zinc)** 함유 방식제를 선정했습니다."
        else:
            match = next((p for p in inh_list if "180" in p['Name'] or "308" in p['Name']), None)
            if match: rec_prod_name = match['Name']; rec_reason = f"🟢 **표준 관리:** LSI({real_lsi:.2f})가 적정 관리 범위(0.5~2.5)입니다. 경제성과 효율 밸런스가 좋은 **표준 인산염계** 제품을 선정했습니다."
        st.success(f"🧬 **냉각수 약품 추천 사유:** {rec_reason}")
        st.divider()

# --------------------------------------------------------------------------------
        # [핵심] 변수 초기화 (여기가 없어서 에러가 난 겁니다!)
        # --------------------------------------------------------------------------------
        
        # 1. 배수량 (calc_blow) 설정
        if 'final_blowdown' in st.session_state and st.session_state['final_blowdown'] > 0:
            calc_blow = st.session_state['final_blowdown']
            blow_src_msg = "✅ Tab 1 물질수지 연동됨"
        else:
            calc_blow = 10.0
            blow_src_msg = "⚠️ 기본값 (Tab 1 미실행)"

        if 'last_calc_blow' not in st.session_state: st.session_state.last_calc_blow = 0.0
        if calc_blow != st.session_state.last_calc_blow: 
            st.session_state['estim_blow_fix'] = calc_blow
            st.session_state.last_calc_blow = calc_blow

        # 2. 보유수량 (V_sys_val) 설정 - [이 부분이 핵심입니다]
        V_sys_val = st.session_state.get('vol_system', 0.0)
        
        # 값이 0이면 기본값 100을 줍니다.
        if V_sys_val > 0:
            vol_msg = "✅ Tab 1 물질수지 연동됨"
        else:
            V_sys_val = 100.0 
            vol_msg = "⚠️ 기본값 (Tab 1 미실행)"

        # --------------------------------------------------------------------------------
        # 입력 필드 배치 (들여쓰기 및 경고 해결 완료)
        # --------------------------------------------------------------------------------
        col_b1, col_b2 = st.columns([1, 2])
        
        with col_b1: 
            # 1. 배수량 입력
            if 'estim_blow_fix' not in st.session_state:
                st.session_state['estim_blow_fix'] = float(f"{calc_blow:.1f}")
            
            estim_blow = st.number_input("운전 배수량 (m3/hr)", key="estim_blow_fix")
            st.caption(blow_src_msg)

            # 2. 보유수량 입력
            if 'vol_sys_input_final' not in st.session_state:
                # 위에서 정의한 V_sys_val을 여기서 사용합니다.
                st.session_state['vol_sys_input_final'] = float(f"{V_sys_val:.1f}")
            
            V_sys = st.number_input("보유 수량 (m3)", key="vol_sys_input_final")
            st.caption(vol_msg)
            
        with col_b2: 
            st.info(f"📊 **수질 요약:** LSI `{real_lsi:.2f}` / pH `{real_ph:.1f}` / 염소 `{real_cl:.0f} ppm`")

        # 4개 컬럼으로 확장 (주처리제, 분산제, 살균제, +밀폐계)
        c_sel1, c_sel2, c_sel3, c_sel4 = st.columns(4)
        
        # 1. 주처리제 (Open System) -> 배수량(Blowdown) 기준
        with c_sel1:
            st.markdown("#### 🛡️ 주처리제 (Open)")
            inh_names = [p['Name'] for p in inh_list]
            def_idx = inh_names.index(rec_prod_name) if rec_prod_name in inh_names else 0
            
            sel_inh = st.selectbox("제품 선택", inh_names, index=def_idx, key="sel_inh_fix")
            sel_inh_data = next((p for p in inh_list if p['Name'] == sel_inh), {})
            
            with st.container(border=True):
                inh_dose = st.number_input("주입량 (ppm)", value=float(sel_inh_data.get('Dosage', 50)), key="inh_dose_fix")
                st.markdown(f"**🧪 성분:** :red[{sel_inh_data.get('Main_Ingredient', '-')}]")
                st.markdown(f"**💡 특징:** :blue[{sel_inh_data.get('Sales_Point', '-')}]")
                if sel_inh_data.get('Field_Tip') != '-':
                    st.markdown(f"**🔧 Tip:** :green[{sel_inh_data.get('Field_Tip')}]")
            
            usage_inh = (estim_blow * 24 * inh_dose) / 1000.0

        # 2. 분산제 (Open System) -> 배수량(Blowdown) 기준
        with c_sel2:
            st.markdown("#### 🧪 분산제 (Dispersant)")
            if disp_list:
                sel_disp = st.selectbox("제품 선택", [p['Name'] for p in disp_list], key="sel_disp_fix")
                sel_disp_data = next((p for p in disp_list if p['Name'] == sel_disp), {})
                
                with st.container(border=True):
                    disp_dose = st.number_input("주입량 (ppm)", value=float(sel_disp_data.get('Dosage', 20)), key="disp_dose_fix")
                    st.markdown(f"**🧪 성분:** :red[{sel_disp_data.get('Main_Ingredient', '-')}]")
                    st.markdown(f"**💡 특징:** :blue[{sel_disp_data.get('Sales_Point', '-')}]")
                    if sel_disp_data.get('Field_Tip') != '-':
                         st.markdown(f"**🔧 Tip:** :green[{sel_disp_data.get('Field_Tip')}]")
                usage_disp = (estim_blow * 24 * disp_dose) / 1000.0
            else: 
                st.warning("DB 없음")
                usage_disp = 0

        # 3. 살균제 (Open System) -> 배수량(Blowdown) 기준 
        with c_sel3:
            st.markdown("#### 🦠 살균제 (Biocide)")
            if bio_list:
                sel_bio = st.selectbox("제품 선택", [p['Name'] for p in bio_list], key="sel_bio_fix")
                sel_bio_data = next((p for p in bio_list if p['Name'] == sel_bio), {})
                
                with st.container(border=True):
                    bio_dose = st.number_input("주입량 (ppm)", value=float(sel_bio_data.get('Dosage', 50)), key="bio_dose_fix")
                    st.markdown(f"**🧪 성분:** :red[{sel_bio_data.get('Main_Ingredient', '-')}]")
                    st.markdown(f"**💡 특징:** :blue[{sel_bio_data.get('Sales_Point', '-')}]")
                    if sel_bio_data.get('Field_Tip') != '-':
                         st.markdown(f"**🔧 Tip:** :green[{sel_bio_data.get('Field_Tip')}]")
                usage_bio = (estim_blow * 24 * bio_dose) / 1000.0
            else: 
                st.warning("DB 없음")
                usage_bio = 0

        # 4. 밀폐계 (Closed System) -> 보유수량(V_sys) 기준
        with c_sel4:
            st.markdown("#### 🔒 밀폐계 (Closed)")
            closed_list = PRODUCT_CATALOG.get('Cooling', {}).get('Closed_System', [])
            
            if closed_list:
                sel_closed = st.selectbox("제품 선택", [p['Name'] for p in closed_list], key="sel_closed_fix")
                sel_closed_data = next((p for p in closed_list if p['Name'] == sel_closed), {})
                
                with st.container(border=True):
                    closed_dose = st.number_input("초기 투입 (ppm)", value=float(sel_closed_data.get('Dosage', 500)), step=100.0, key="closed_dose_fix")
                    
                    st.markdown(f"**🧪 성분:** :red[{sel_closed_data.get('Main_Ingredient', '-')}]")
                    st.markdown(f"**💡 특징:** :blue[{sel_closed_data.get('Sales_Point', '-')}]") # 특징 색깔 추가
                    
                    if sel_closed_data.get('Field_Tip', '-') != '-': # != 확인 필수!
                        st.markdown(f"**🔧 Tip:** :green[{sel_closed_data.get('Field_Tip')}]") # 팁 색깔 추가
                
                # [핵심] 밀폐계는 배수가 없으므로 '보유수량(V_sys)' 기준 초기 투입량 계산
                usage_closed_init = (V_sys * closed_dose) / 1000.0 
            else: 
                st.info("밀폐계 제품 없음")
                usage_closed_init = 0

        st.divider()
        
        # 차트 시각화
        st.markdown("### 📊 약품 사용량 예측")
        
        col_chart1, col_chart2 = st.columns([2, 1])
        
        with col_chart1:
            st.markdown("##### 📅 일일 보충량 (Open System)")
            st.caption(f"기준: 배수량 {estim_blow:.1f} m3/hr (Blowdown)")
            
            chart_df = pd.DataFrame({
                'Type': ['Inhibitor', 'Dispersant', 'Biocide'], 
                'Usage': [usage_inh, usage_disp, usage_bio], 
                'Product': [sel_inh, sel_disp if disp_list else '-', sel_bio if bio_list else '-']
            })
            
            fig = px.bar(chart_df, x='Type', y='Usage', color='Type', text='Usage', hover_data=['Product'])
            fig.update_traces(texttemplate='%{text:.1f} kg/day', textposition='outside')
            fig.update_layout(height=300, showlegend=False, yaxis_title="Daily Usage (kg)")
            st.plotly_chart(fig, use_container_width=True)
            
        with col_chart2:
            st.markdown("##### 🚀 초기 투입량 (Closed System)")
            st.caption(f"기준: 보유수량 {V_sys:.1f} m3 (V_sys)")
            
            if closed_list:
                st.metric(label=f"제품: {sel_closed}", value=f"{usage_closed_init:.1f} kg", delta="Initial Charge")
                st.info("밀폐계는 배수가 없으므로, 전체 보유수량에 대한 **1회 초기 투입량**입니다.")
            else:
                st.write("밀폐계 제품을 선택해주세요.")

        st.divider()
        st.markdown("### 📋 현장 서비스 리포트")
        st.caption("지금까지 입력·계산된 값을 한 장짜리 Word 리포트로 내려받습니다.")

        report_stress = calculate_stress_index(real_lsi, real_rsi, real_psi, real_ls_idx)

        report_coupon_comment = None
        if coupon_result:
            predicted_corrosive = real_lsi < 0 or real_rsi > 8.5
            ms_bad = coupon_result['ms']['severity'] == 'bad'
            cu_bad = coupon_result['cu']['severity'] == 'bad'
            if predicted_corrosive and not (ms_bad or cu_bad):
                report_coupon_comment = "예측 지수는 부식성으로 나왔으나 실측 쿠폰은 양호 — 현재 방식제 프로그램이 유효한 것으로 판단됨."
            elif not predicted_corrosive and (ms_bad or cu_bad):
                report_coupon_comment = "지수상 안정 범위이나 실측 쿠폰 불량 — 국부부식/미생물 부식 등 지수가 반영 못하는 원인 점검 필요."
            elif predicted_corrosive and (ms_bad or cu_bad):
                report_coupon_comment = "예측 지수와 실측 쿠폰이 모두 부식 위험 — 방식제 프로그램 재점검 시급."
            else:
                report_coupon_comment = "예측 지수와 실측 쿠폰이 모두 안정 범위로 일치."

        chem_rows = [{
            "category": "주처리제 (Inhibitor)", "product": sel_inh,
            "ingredient": sel_inh_data.get('Main_Ingredient', '-'), "dosage": inh_dose, "daily_kg": usage_inh
        }]
        if disp_list:
            chem_rows.append({
                "category": "분산제 (Dispersant)", "product": sel_disp,
                "ingredient": sel_disp_data.get('Main_Ingredient', '-'), "dosage": disp_dose, "daily_kg": usage_disp
            })
        if bio_list:
            chem_rows.append({
                "category": "살균제 (Biocide)", "product": sel_bio,
                "ingredient": sel_bio_data.get('Main_Ingredient', '-'), "dosage": bio_dose, "daily_kg": usage_bio
            })
        if closed_list:
            chem_rows.append({
                "category": "밀폐계 (Closed, 초기투입)", "product": sel_closed,
                "ingredient": sel_closed_data.get('Main_Ingredient', '-'), "dosage": closed_dose, "daily_kg": usage_closed_init
            })

        report_bytes = generate_cooling_report_docx({
            "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "temp": real_temp, "ph": real_ph, "coc": st.session_state.sim_results.get('target_coc', 0) if st.session_state.get('run_simulation') else 0,
            "lsi": real_lsi, "lsi_skin": st.session_state.sim_results.get('lsi_skin', real_lsi) if st.session_state.get('run_simulation') else real_lsi,
            "rsi": real_rsi, "psi": real_psi, "ls_idx": real_ls_idx,
            "stress": report_stress,
            "coupon": coupon_result, "coupon_comment": report_coupon_comment,
            "chem_rows": chem_rows, "rec_reason": rec_reason,
        })
        st.download_button(
            "📥 현장 리포트 다운로드 (.docx)", data=report_bytes,
            file_name=f"냉각수_서비스리포트_{datetime.now().strftime('%Y%m%d')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    with tab5:
        st.header("🔬 Deposit Analysis (ICP-OES Data Analysis)")
        st.caption("※ 성분 수치를 입력하면 자동으로 무기염 총합(Sum)과 각 항목의 비중(%)을 계산합니다.")
        edited_deposit = st.data_editor(st.session_state.deposit_data, hide_index=True, use_container_width=True, key="dep_edit_t1")
        sum_inorganic = edited_deposit['Result (%)'].sum()
        edited_deposit['비중 (%)'] = (edited_deposit['Result (%)'] / sum_inorganic * 100).round(2) if sum_inorganic > 0 else 0
        st.markdown(f"#### 📊 분석 결과 요약: **무기염 총합 (InOrganic Salt SUM) = {sum_inorganic:.2f}%**")
        st.dataframe(edited_deposit, hide_index=True, use_container_width=True)
        st.divider()
        st.subheader("📊 성분별 비중 분석 (Deposit Composition)")
        fig_dep = px.bar(edited_deposit, x='Result (%)', y='item', orientation='h', text_auto='.1f', color='item', title="Deposit Component Analysis (Horizontal Bar)")
        fig_dep.update_layout(showlegend=False, height=550, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_dep, use_container_width=True)
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

    with tab6:
        st.subheader("📘 Engineering Formulas & Theory")
        st.markdown("본 프로그램은 **Drew Principle Manual** 등 수처리 기업의 표준 공식을 준수합니다.")
        with st.expander("💧 1. 냉각탑 물질수지 (Water Balance)", expanded=False):
            st.markdown("#### (1) 증발량 (Evaporation Loss)")
            st.latex(r"E = Q \times \Delta T \times F")
            st.caption("여기서 $Q$: 순환수량, $\Delta T$: 온도차, $F$: 계절계수 (0.0015)")
            st.markdown("#### (2) 배수량 (Blowdown)")
            st.latex(r"B = \frac{E}{COC - 1} - W")
            st.markdown("#### (3) 보유수 반감기 (Half Life Index)")
            st.latex(r"HTI = 0.693 \times \frac{V}{B + W}")
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
        with st.expander("📈 3. 농축수 pH 및 수질 예측 공식", expanded=False):
            st.markdown("#### (1) 농축수 pH 예측 (pH Prediction)")
            st.latex(r"pH_{cycle} = 1.465 \times \log_{10}(Alk_{cycle}) + 4.54")
            st.caption("대기 중 CO2 평형으로 인해 pH는 보통 9.3을 넘지 않습니다.")
            st.markdown("#### (2) 이온 농축 (Cycle Chemistry)")
            st.latex(r"C_{cycle} = C_{makeup} \times COC")
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
        st.divider()
        st.caption("📚 Reference: Drew FIELD SERVICE MANUAL")
