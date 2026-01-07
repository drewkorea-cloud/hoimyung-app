import streamlit as st
import pandas as pd
import os
import sys
import math
import plotly.graph_objects as go
import plotly.express as px
import datetime
import numpy as np
from fpdf import FPDF

# --- 1. 기본 설정 ---
st.set_page_config(layout="wide", page_title="Water Solution Master (by 최강파커)")

# [스타일] 보일러/RO/폐수 파트를 위한 디자인 (냉각수 레이아웃에는 영향 없음)
st.markdown("""
    <style>
    .metric-card {
        background-color: #F8F9F9;
        border: 1px solid #E5E8E8;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# [DATA] 회명워터젠 제품 데이터베이스
# ==============================================================================
PRODUCT_CATALOG = {
    'Cooling': {
        'Inhibitor': [
            {'Name': 'HCO-308 (Standard)', 'Desc': '일반적인 개방형 냉각탑용 복합제', 'Dosage': 100.0},
            {'Name': 'HCD-403 (Premium)', 'Desc': '고농축/고부하 운전용 고성능 분산제', 'Dosage': 20.0},
            {'Name': 'HCO-654 (Corrosion)', 'Desc': '배관 부식이 심한 현장용 (방식 강화형)', 'Dosage': 100.0},
            {'Name': 'HWC-Zero (Eco)', 'Desc': '친환경 저독성 제품', 'Dosage': 25.0}
        ],
        'Biocide': [
            {'Name': 'BioOX-1000 (Chlorine)', 'Desc': '산화성 살균제 (경제형)', 'Dosage': 50.0},
            {'Name': 'BioNox-250 (Isothiazoline)', 'Desc': '비산화성 살균제 (슬라임 제거 탁월)', 'Dosage': 100.0},
            {'Name': 'BioOX-1100 (Bromine)', 'Desc': '브롬계 살균제 (고pH 대응)', 'Dosage': 40.0}
        ]
    },
    'Boiler': {
        'Oxygen_Scavenger': [
            {'Name': 'HBS-100 (Sulfite)', 'Desc': '표준 아황산염계 (저압용)', 'Dosage': 20.0},
            {'Name': 'MBB-8760 (Hydrazine)', 'Desc': '하이드라진 대체/고압용', 'Dosage': 10.0},
            {'Name': 'HBB-100 (Carbohydrazide)', 'Desc': '복수 계통 방식 겸용 (DEHA)', 'Dosage': 15.0}
        ],
        'Scale_Disp': [
            {'Name': 'HBP-Standard', 'Desc': '표준 인산염계 청관제', 'Dosage': 30.0},
            {'Name': 'HBP-Polymer', 'Desc': '전체 휘발성 처리(AVT)용', 'Dosage': 20.0}
        ]
    },
    'RO': {
        'Antiscalant': [
            {'Name': 'MRD-2000 (General)', 'Desc': '범용 스케일 방지제', 'Dosage': 3.0},
            {'Name': 'HRD-3000 (High Silica)', 'Desc': '고농도 실리카 대응', 'Dosage': 5.0},
            {'Name': 'HWR-HighpH', 'Desc': '고경도/LSI 대응', 'Dosage': 4.0}
        ]
    }
}

# 로고 경로 찾기
def get_logo_path():
    candidates = ['logo.png', 'logo.jpg', 'hoimyung WaterZen.png']
    base_paths = [os.path.abspath("."), os.path.dirname(sys.executable)]
    for base in base_paths:
        for file in candidates:
            full_path = os.path.join(base, file)
            if os.path.exists(full_path): return full_path
    return None
logo_file = get_logo_path()

# 상수 데이터
factors = {'Calcium (Ca)': 0.0499, 'Magnesium (Mg)': 0.0823, 'Sodium (Na)': 0.0435, 'Potassium (K)': 0.0256, 'Bicarbonate (HCO3)': 0.0164, 'Chloride (Cl)': 0.0282, 'Sulfate (SO4)': 0.0208, 'Nitrate (NO3)': 0.0161, 'Fluoride (F)': 0.0526, 'Silica (SiO2)': 0}

# === [차트] 전문 게이지 차트 ===
def create_gauge(value, title, min_v, max_v, steps, threshold=None):
    gauge_dict = {
        'axis': {'range': [min_v, max_v], 'tickwidth': 1, 'tickcolor': "darkblue"},
        'bar': {'color': "#2E86C1", 'thickness': 0.3},
        'steps': steps
    }
    # [수정] Threshold 에러 방지 코드 적용
    if threshold is not None:
        if isinstance(threshold, (int, float)):
            gauge_dict['threshold'] = {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': threshold}
        elif isinstance(threshold, dict):
            gauge_dict['threshold'] = threshold

    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = value,
        title = {'text': title, 'font': {'size': 20, 'color': '#2c3e50'}},
        number = {'font': {'size': 40, 'color': '#2c3e50'}},
        gauge = gauge_dict
    ))
    fig.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)", font={'family': "Arial"})
    return fig

# === [엔진] 계산 함수들 ===
def calculate_indices_advanced(ph, temp_c, tds, ca_ppm, alk_ppm, cl_ppm, so4_ppm):
    try:
        if ca_ppm <= 0 or alk_ppm <= 0: return -9.9, -9.9, 0
        val_A = (math.log10(tds) - 1) / 10
        val_B = -13.12 * math.log10(temp_c + 273.15) + 34.55
        val_C = math.log10(ca_ppm) - 0.4
        val_D = math.log10(alk_ppm)
        phs = (9.3 + val_A + val_B) - (val_C + val_D)
        lsi = ph - phs
        ph_eq = 1.465 * math.log10(alk_ppm) + 4.54
        psi = 2 * phs - ph_eq
        ls_index = (cl_ppm + so4_ppm) / alk_ppm if alk_ppm > 0 else 0
        return lsi, psi, ls_index
    except: return -9.9, -9.9, 0

def predict_corrosion_mpy(lsi, cl_ppm, velocity_ms, temp_c):
    base_mpy = 2.0 
    if cl_ppm > 500: base_mpy += 3.0
    elif cl_ppm > 200: base_mpy += 1.5
    if lsi < -1.0: base_mpy += 4.0
    elif lsi < -0.2: base_mpy += 2.0
    velocity_factor = 2.0 if velocity_ms < 0.3 else (3.5 if velocity_ms > 3.0 else 0)
    temp_factor = 1.5 if temp_c > 50 else 0
    total_mpy = base_mpy + velocity_factor + temp_factor
    return total_mpy, total_mpy * 0.1 # Return Total, Inhibited

def analyze_deposit(comp_dict):
    loi = comp_dict.get("LOI (550°C)", 0); ca = comp_dict.get("Calcium (CaO)", 0)
    mg = comp_dict.get("Magnesium (MgO)", 0); fe = comp_dict.get("Iron (Fe2O3)", 0)
    al = comp_dict.get("Aluminium (Al2O3)", 0); si = comp_dict.get("Silica (SiO2)", 0)
    p = comp_dict.get("Phosphate (P2O5)", 0); s = comp_dict.get("Sulfate (SO4)", 0)
    diagnosis = "복합 오염물"; cause = "원인 불명"
    if loi > 40: diagnosis = "유기물/슬라임"; cause = "미생물/유기물 유입"
    elif al > 20: diagnosis = "알루미늄계 스케일"; cause = "응집제 과다/pH 급변"
    elif ca > 30: diagnosis = "탄산칼슘 (CaCO3)"; cause = "LSI 높음 (일반 스케일)"
    elif si > 20: diagnosis = "실리카 (Silica)"; cause = "실리카 농도 150ppm 초과"
    elif fe > 30: diagnosis = "산화철 (Rust)"; cause = "배관 부식"
    return diagnosis, cause

def recommend_reuse_process(input_data, target_data):
    process_train = []; chemicals = []
    if input_data['SS'] > target_data['SS']:
        if input_data['SS'] > 50: process_train.append("DAF (가압부상)"); chemicals.append("Coagulant")
        else: process_train.append("Sand Filter"); chemicals.append("None")
    if input_data['COD'] > target_data['COD']:
        process_train.append("MBR (생물학적처리)"); chemicals.append("NaOCl")
    else: process_train.append("MF/UF (정밀여과)")
    if input_data['TDS'] > target_data['TDS']:
        process_train.append("RO System"); chemicals.extend(["Antiscalant", "SMBS", "NaOH/HCl"])
    if target_data['TDS'] < 1.0: process_train.append("Ion Exchange (MBP)")
    return process_train, list(set(chemicals))

# --- 2. 사이드바 ---
with st.sidebar:
    if logo_file: st.image(logo_file, use_container_width=True)
    else: st.title("💧 HOIMYUNG")
    st.title("🧰 Menu")
    program_mode = st.radio("Select Module:", 
        ["1. Cooling Expert", "2. Boiler Master", "3. RO Master Pro", "4. Wastewater Reuse"])
    st.markdown("---")
    st.info("💡 **Tip:** 각 모듈별 입력값을 넣고 '적용' 버튼을 누르면 전문가 진단 리포트가 생성됩니다.")
    st.markdown("---")
    st.markdown("#### 👨‍💻 Creator")
    st.markdown("### **파커 (Parker)**")
    st.caption("Water Solution Master")

# ==============================================================================
# [Module 1] Cooling Expert (냉각수) - **기존 틀 유지 (st.form 적용 버전)**
# ==============================================================================
if "Cooling" in program_mode:
    if 'deposit_data' not in st.session_state:
        st.session_state.deposit_data = pd.DataFrame({'Component': ['LOI (550°C)', 'Calcium (CaO)', 'Magnesium (MgO)', 'Iron (Fe2O3)', 'Aluminium (Al2O3)', 'Silica (SiO2)', 'Phosphate (P2O5)', 'Sulfate (SO4)'], 'Result (%)': [28.02, 0.10, 0.05, 0.23, 45.49, 1.53, 0.10, 23.48]})
    if 'makeup_data' not in st.session_state:
        st.session_state.makeup_data = pd.DataFrame({'Item': ['pH', 'Cond (µS)', 'Ca-H (ppm)', 'Mg-H (ppm)', 'M-Alk (ppm)', 'Cl (ppm)', 'SO4 (ppm)', 'SiO2 (ppm)'], 'Make-up': [7.5, 200.0, 40.0, 10.0, 50.0, 20.0, 10.0, 10.0]})

    st.title("🧪 Cooling Expert System ")
    st.caption("Authorized by **Parker**")
    
    tab_sim, tab_expert, tab_chem, tab_depo = st.tabs(["1. Simulator (Acid Feed)", "2. Advanced Diagnosis", "3. HM Chemical Selection", "4. Deposit Lab"])

    with tab_sim:
        with st.container(border=True):
            # [기존 유지] Form 적용으로 입력값 일괄 적용
            with st.form("cooling_input_form"):
                st.info("👇 **입력값을 수정하고 하단의 [입력값 적용] 버튼을 눌러주세요.**")
                c1, c2 = st.columns([1, 1.5])
                with c1: 
                    st.subheader("1. Make-up Water")
                    edited_mu = st.data_editor(st.session_state.makeup_data, hide_index=True)
                
                with c2: 
                    st.subheader("2. Simulation Control")
                    sim_coc = st.slider("Target Cycles (N)", 1.0, 10.0, 5.0, 0.1)
                    sim_temp = st.slider("Temperature (°C)", 10.0, 60.0, 32.0, 1.0)
                    
                    use_acid = st.checkbox("🧪 Acid Feed (pH Control)", value=False)
                    acid_dosage_ppm = 0.0
                    
                    target_alk = st.number_input("Target Alkalinity (ppm) [Acid Only]", value=100.0)
                    sim_ph_manual = st.number_input("Controlled pH (Optional)", value=7.8, step=0.1)

                submitted = st.form_submit_button("🔄 입력값 적용 (Apply Simulation)")

            if submitted:
                st.session_state.makeup_data = edited_mu

            # 계산 로직
            mu_v = st.session_state.makeup_data.set_index('Item')['Make-up']
            pred_ph_raw = 7.5 + math.log10(sim_coc)
            if pred_ph_raw > 9.0: pred_ph_raw = 9.0
            
            if use_acid:
                sim_ph = sim_ph_manual
                conc_alk_raw = mu_v['M-Alk (ppm)'] * sim_coc
                acid_req_alk = conc_alk_raw - target_alk
                if acid_req_alk < 0: acid_req_alk = 0
                acid_dosage_ppm = acid_req_alk 
                p_alk = target_alk 
                p_so4 = (mu_v['SO4 (ppm)'] * sim_coc) + acid_dosage_ppm 
            else:
                sim_ph = round(pred_ph_raw, 2)
                p_alk = mu_v['M-Alk (ppm)'] * sim_coc
                p_so4 = mu_v['SO4 (ppm)'] * sim_coc

            p_cond = mu_v['Cond (µS)'] * sim_coc
            p_ca = mu_v['Ca-H (ppm)'] * sim_coc
            p_cl = mu_v['Cl (ppm)'] * sim_coc
            p_sio2 = mu_v['SiO2 (ppm)'] * sim_coc
            
            lsi, psi, ls_index = calculate_indices_advanced(sim_ph, sim_temp, p_cond*0.7, p_ca, p_alk, p_cl, p_so4)

            # 결과 표시
            st.subheader("3. Risk Index")
            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                color = "inverse" if lsi > 2.0 else ("off" if lsi > 0.5 else "normal")
                st.metric("LSI (Scaling)", f"{lsi:.2f}", delta="Scale" if lsi>0.5 else "Stable", delta_color=color)
            with rc2:
                st.metric("PSI (Puckorius)", f"{psi:.2f}", delta="Scale Risk" if psi < 6.0 else "Corr Risk", delta_color="inverse")
            with rc3:
                if p_sio2 > 150: st.error(f"🚨 Silica: {p_sio2:.1f} ppm")
                else: st.success(f"✅ Silica: {p_sio2:.1f} ppm")

            if use_acid and acid_dosage_ppm > 0:
                st.info(f"🧪 **Acid Requirement:** To maintain Alk {target_alk:.0f} ppm, approx **{acid_dosage_ppm:.0f} ppm** of H2SO4 is generated/added in system.")

            gc1, gc2 = st.columns([1, 1.5])
            with gc1:
                st.subheader("📊 Visual Status (PSI & L-S)")
                steps_ls = [{'range': [0, 0.8], 'color': "#ABEBC6"}, {'range': [0.8, 1.2], 'color': "#F9E79F"}, {'range': [1.2, 5.0], 'color': "#F5B7B1"}]
                st.plotly_chart(create_gauge(round(ls_index, 2), "Larson-Skold (Pitting)", 0, 3, steps_ls), use_container_width=True)
                res_df = pd.DataFrame({'Parameter': ['pH', 'Cond', 'Ca-H', 'M-Alk', 'Cl', 'SO4'], 
                                       'Make-up': [mu_v['pH'], mu_v['Cond (µS)'], mu_v['Ca-H (ppm)'], mu_v['M-Alk (ppm)'], mu_v['Cl (ppm)'], mu_v['SO4 (ppm)']], 
                                       'Tower (Sim)': [sim_ph, p_cond, p_ca, p_alk, p_cl, p_so4]})
                st.dataframe(res_df.style.format("{:.1f}", subset=['Make-up', 'Tower (Sim)']), hide_index=True)
                
            with gc2:
                st.subheader("📈 LSI & PSI Trend")
                sim_data = []
                for c in np.arange(1.0, 10.1, 0.5):
                    t_ph = 7.5 + math.log10(c); t_ph = 9.0 if t_ph > 9.0 else t_ph
                    t_cond = mu_v['Cond (µS)']*c; t_ca = mu_v['Ca-H (ppm)']*c
                    t_alk = mu_v['M-Alk (ppm)']*c; t_cl = mu_v['Cl (ppm)']*c; t_so4 = mu_v['SO4 (ppm)']*c
                    t_lsi, t_psi, t_ls = calculate_indices_advanced(t_ph, sim_temp, t_cond*0.7, t_ca, t_alk, t_cl, t_so4)
                    sim_data.append({'COC': c, 'LSI': t_lsi, 'PSI': t_psi})
                df_chart = pd.DataFrame(sim_data)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_chart['COC'], y=df_chart['LSI'], mode='lines', name='LSI (High=Scale)', line=dict(color='#E74C3C', width=3)))
                fig.add_trace(go.Scatter(x=df_chart['COC'], y=df_chart['PSI'], mode='lines', name='PSI (Low=Scale)', line=dict(color='#2E86C1', width=3)))
                fig.add_hline(y=2.0, line_dash="dash", line_color="red", annotation_text="LSI Limit")
                fig.add_hline(y=6.0, line_dash="dash", line_color="blue", annotation_text="PSI Limit")
                fig.update_layout(template="plotly_white", height=400, xaxis_title="Cycles of Concentration (N)", yaxis_title="Index Value", hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)

    with tab_expert:
        st.header("⚙️ System Diagnosis (PSI & L-S Analysis)")
        c1, c2 = st.columns(2)
        with c1: 
            circ = st.number_input("Recirculation (m3/hr)", 500.0); dia = st.number_input("Pipe (mm)", 300.0)
            vel = (circ/3600) / (3.14159*(dia/1000)**2/4)
            st.info(f"Velocity: {vel:.2f} m/s")
        with c2:
            rmpy, impy = predict_corrosion_mpy(lsi, p_cl, vel, sim_temp)
            if ls_index > 1.2: rmpy *= 1.3
            st.metric("Corrosion Rate", f"{rmpy:.1f} MPY", delta="Risk" if rmpy>5 else "Normal", delta_color="inverse")
        st.markdown("---")
        if psi < 6.0: st.error(f"🔴 **PSI {psi:.2f}:** Scaling Tendency High (Puckorius Index < 6.0)")
        else: st.success(f"🟢 **PSI {psi:.2f}:** Non-Scaling / Solubilizing Tendency")
        if ls_index > 1.2: st.error(f"🔴 **Larson-Skold {ls_index:.2f}:** High Pitting Potential (Cl+SO4 > Alk).")
        elif ls_index > 0.8: st.warning(f"🟡 **Larson-Skold {ls_index:.2f}:** Moderate Pitting Potential.")
        else: st.success(f"🟢 **Larson-Skold {ls_index:.2f}:** Low Pitting Potential.")

    with tab_chem:
        st.header("💊 Hoimyung Chemical Selection")
        st.info("현장 상황에 맞는 약품을 선택하세요.")
        with st.expander("System Input", expanded=True):
            col_sys1, col_sys2 = st.columns(2)
            circ_rate = col_sys1.number_input("System Circ. Rate (m3/hr)", value=500.0)
            delta_t = col_sys2.number_input("Delta T (°C)", value=5.0)
            evap = circ_rate * delta_t / 580; blow = evap / (sim_coc - 1); makeup = evap + blow; hold_vol = circ_rate * 0.2
            st.markdown(f"**Calculated:** Make-up: `{makeup:.1f} m3/hr`, Holding: `{hold_vol:.0f} m3`")
        
        list_inh = PRODUCT_CATALOG['Cooling']['Inhibitor']
        list_bio = PRODUCT_CATALOG['Cooling']['Biocide']
        inh_names = [p['Name'] for p in list_inh]
        bio_names = [p['Name'] for p in list_bio]

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.subheader("1. Inhibitor Selection")
            sel_inh_name = st.selectbox("Select Inhibitor Model:", inh_names)
            sel_inh_data = next(item for item in list_inh if item["Name"] == sel_inh_name)
            st.success(f"📌 **Model:** {sel_inh_data['Name']}")
            st.caption(f"**Desc:** {sel_inh_data['Desc']}")
            target_ppm = st.number_input(f"Dosage (ppm)", value=float(sel_inh_data['Dosage']))
            daily_use = makeup * 24 * target_ppm / 1000
            st.metric("Daily Consumption", f"{daily_use:.1f} kg/day")
            
        with col_c2:
            st.subheader("2. Biocide Selection")
            sel_bio_name = st.selectbox("Select Biocide Model:", bio_names)
            sel_bio_data = next(item for item in list_bio if item["Name"] == sel_bio_name)
            st.info(f"📌 **Model:** {sel_bio_data['Name']}")
            st.caption(f"**Desc:** {sel_bio_data['Desc']}")
            bio_ppm = st.number_input(f"Shock Dose (ppm)", value=float(sel_bio_data['Dosage']))
            shot_kg = hold_vol * bio_ppm / 1000
            st.metric("Shock Dosing Amount", f"{shot_kg:.1f} kg/shot")

    with tab_depo:
        st.header("🔬 Deposit Analysis Lab (ICP based)")
        col_d1, col_d2 = st.columns([1, 1.5])
        with col_d1:
            st.subheader("1. ICP Data Input (%)")
            with st.form("deposit_form"):
                edited_depo = st.data_editor(st.session_state.deposit_data, hide_index=True, num_rows="fixed")
                d_submit = st.form_submit_button("🧪 분석 실행 (Run Analysis)")
            if d_submit: st.session_state.deposit_data = edited_depo
            comp_dict = dict(zip(st.session_state.deposit_data['Component'], st.session_state.deposit_data['Result (%)']))
        with col_d2:
            st.subheader("2. AI Diagnosis Result")
            diagnosis, cause = analyze_deposit(comp_dict)
            with st.container(border=True):
                st.markdown(f"### 🔍 판독: **{diagnosis}**")
                st.markdown(f"**📌 원인:** {cause}")
            fig_pie = px.pie(st.session_state.deposit_data, values='Result (%)', names='Component', title='Deposit Composition', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

# ==============================================================================
# [Module 2] Boiler Master (전문가급 대시보드로 보강)
# ==============================================================================
elif "Boiler" in program_mode:
    st.title("🔥 Boiler Master Pro Dashboard")
    
    if 'boiler_data' not in st.session_state:
        st.session_state.boiler_data = pd.DataFrame({'Parameter': ['Steam Rate (ton/hr)', 'Pressure (bar)', 'Make-up TDS (ppm)', 'Condensate TDS (ppm)', 'Target TDS (ppm)'], 'Value': [10.0, 10.0, 150.0, 5.0, 3000.0]})
    if 'energy_data' not in st.session_state:
        st.session_state.energy_data = pd.DataFrame({'Parameter': ['Fuel Cost (KRW/m3)', 'Oper. Hours/Day', 'Make-up Temp (°C)', 'Condensate Temp (°C)'], 'Value': [900.0, 24.0, 20.0, 85.0]})

    tab_b1, tab_b2, tab_b3 = st.tabs(["🏭 Boiler Design", "💰 Energy & Cost", "💊 Chemical Solution"])

    with tab_b1:
        with st.form("boiler_input"):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("Input Parameters")
                cond_return = st.slider("응축수 회수율 (%)", 0, 100, 50)
                edited_boiler = st.data_editor(st.session_state.boiler_data, hide_index=True)
            with c2:
                st.subheader("System Balance Diagram")
                # 계산 로직
                b_vals = dict(zip(edited_boiler['Parameter'], edited_boiler['Value']))
                mu_ratio = (100 - cond_return)/100
                feed_tds = (mu_ratio * b_vals['Make-up TDS (ppm)']) + ((cond_return/100) * b_vals['Condensate TDS (ppm)'])
                coc = b_vals['Target TDS (ppm)'] / feed_tds if feed_tds > 0 else 1.0
                blow_pct = (1/coc)*100
                blow_amt = b_vals['Steam Rate (ton/hr)'] * (blow_pct/100) / (1 - blow_pct/100)
                feed_flow = b_vals['Steam Rate (ton/hr)'] + blow_amt
                
                # Sankey Diagram (Visual Flow)
                fig_sankey = go.Figure(data=[go.Sankey(
                    node = dict(
                      pad = 15, thickness = 20, line = dict(color = "black", width = 0.5),
                      label = ["Make-up", "Condensate", "Feedwater", "Boiler", "Steam", "Blowdown"],
                      color = ["#AED6F1", "#F9E79F", "#5DADE2", "#E74C3C", "#D5F5E3", "#95A5A6"]
                    ),
                    link = dict(
                      source = [0, 1, 2, 3, 3], 
                      target = [2, 2, 3, 4, 5],
                      value = [feed_flow*mu_ratio, feed_flow*(cond_return/100), feed_flow, b_vals['Steam Rate (ton/hr)'], blow_amt]
                  ))])
                fig_sankey.update_layout(title_text="Water Mass Balance Flow (ton/hr)", height=300)
                st.plotly_chart(fig_sankey, use_container_width=True)
                
            submit_b = st.form_submit_button("설계 적용 (Apply Design)")
        
        # Result Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Cycles (N)", f"{coc:.1f}", delta="Efficiency")
        m2.metric("Feedwater Flow", f"{feed_flow:.2f} t/hr")
        m3.metric("Blowdown Rate", f"{blow_pct:.1f} %", delta="Loss", delta_color="inverse")
        m4.metric("Mixed TDS", f"{feed_tds:.0f} ppm")

    with tab_b2:
        st.subheader("💸 Steam Cost & Energy Audit")
        with st.form("energy_form"):
            c1, c2 = st.columns([1, 1.5])
            with c1:
                edited_energy = st.data_editor(st.session_state.energy_data, hide_index=True)
            with c2:
                # 에너지 계산
                e_vals = dict(zip(edited_energy['Parameter'], edited_energy['Value']))
                t_feed = (mu_ratio * e_vals['Make-up Temp (°C)'] + (cond_return/100) * e_vals['Condensate Temp (°C)'])
                enthalpy_steam = 660 # approx kcal/kg
                enthalpy_feed = t_feed
                energy_req = feed_flow * 1000 * (enthalpy_steam - enthalpy_feed)
                fuel_req = energy_req / (10500 * 0.9) 
                cost_hr = fuel_req * e_vals['Fuel Cost (KRW/m3)']
                
                # Pie Chart
                labels = ['Steam Generation', 'Blowdown Loss']
                loss_heat = blow_amt * 1000 * (180 - t_feed) 
                total_heat = energy_req
                values = [total_heat - loss_heat, loss_heat]
                fig_pie = px.pie(values=values, names=labels, title="Energy Consumption Breakdown", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)

            submit_e = st.form_submit_button("비용 분석 (Analyze)")
            
        st.warning(f"💰 **Estimated Steam Cost:** {int(cost_hr):,} KRW/hr ({int(cost_hr*e_vals['Oper. Hours/Day']*300/1000000):,} Million KRW/yr)")

    with tab_b3:
        st.subheader("💊 Chemical Treatment Program")
        c1, c2 = st.columns(2)
        sel_oxy = c1.selectbox("Oxygen Scavenger", [p['Name'] for p in PRODUCT_CATALOG['Boiler']['Oxygen_Scavenger']])
        sel_scale = c2.selectbox("Scale Inhibitor", [p['Name'] for p in PRODUCT_CATALOG['Boiler']['Scale_Disp']])
        st.success(f"Selected: **{sel_oxy}** + **{sel_scale}**")
        
        dos_df = pd.DataFrame({'Chemical': ['Oxy Scavenger', 'Scale Inhibitor'], 'Dosage (kg/day)': [feed_flow*24*20/1000, feed_flow*24*30/1000]})
        fig_bar = px.bar(dos_df, x='Chemical', y='Dosage (kg/day)', title="Daily Chemical Consumption", color='Chemical')
        st.plotly_chart(fig_bar, use_container_width=True)

# ==============================================================================
# [Module 3] RO Master (설계 프로그램급 그래프 추가)
# ==============================================================================
elif "RO" in program_mode:
    st.title("🏭 RO Membrane Master Pro")
    
    tab1, tab2, tab3 = st.tabs(["⚙️ Design & Config", "📈 Projection Analysis", "💊 Antiscalant"])
    
    with tab1:
        with st.form("ro_design"):
            st.subheader("1. System Configuration")
            c1, c2, c3 = st.columns(3)
            flow = c1.number_input("Permeate Flow (m3/hr)", 100.0)
            rec = c2.slider("Recovery (%)", 50, 85, 75)
            array = c3.selectbox("Vessel Array", ["2:1", "3:2:1", "1 Stage"])
            
            st.subheader("2. Membrane Selection")
            mem_area = st.selectbox("Membrane Area", ["400 ft2", "440 ft2"])
            area_val = 400 if "400" in mem_area else 440
            
            feed_flow = flow / (rec/100)
            flux = (flow * 1000) / (math.ceil(flow*1000/(15*37.2)) * 37.2)
            
            submit_ro = st.form_submit_button("설계 시뮬레이션 (Run Design)")
        
        g1, g2, g3 = st.columns(3)
        g1.plotly_chart(create_gauge(round(flux,1), "Avg Flux (LMH)", 10, 30, []), use_container_width=True)
        g2.plotly_chart(create_gauge(rec, "Recovery (%)", 40, 90, []), use_container_width=True)
        g3.metric("Feed Flow", f"{feed_flow:.1f} m3/hr")

    with tab2:
        st.subheader("📈 3-Year Performance Projection (Fouling Simulation)")
        years = np.linspace(0, 3, 37) 
        press_clean = 10 + (years * 0.5)
        salt_pass = 1.0 + (years * 0.2)
        
        fig_proj = go.Figure()
        fig_proj.add_trace(go.Scatter(x=years, y=press_clean, name="Feed Pressure (bar)", line=dict(color='red', width=3)))
        fig_proj.add_trace(go.Scatter(x=years, y=salt_pass, name="Salt Passage (%)", yaxis="y2", line=dict(color='blue', dash='dot')))
        
        fig_proj.update_layout(
            title="Membrane Performance Trend",
            xaxis_title="Operation Time (Years)",
            yaxis=dict(title="Pressure (bar)"),
            yaxis2=dict(title="Salt Passage (%)", overlaying="y", side="right"),
            legend=dict(x=0, y=1.1, orientation="h")
        )
        st.plotly_chart(fig_proj, use_container_width=True)

    with tab3:
        st.subheader("💊 Antiscalant Dosing")
        prod = st.selectbox("Product", [p['Name'] for p in PRODUCT_CATALOG['RO']['Antiscalant']])
        st.info(f"Recommended Product: **{prod}** for Silica/Scale Control")

# ==============================================================================
# [Module 4] Wastewater Reuse (시각화 강화)
# ==============================================================================
elif "Wastewater" in program_mode:
    st.title("♻️ Wastewater Reuse Engineering")
    
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.subheader("💧 Water Quality Profile")
        with st.form("waste_input"):
            df_in = pd.DataFrame({'Param': ['COD', 'SS', 'TDS'], 'Raw': [100.0, 50.0, 1500.0], 'Target': [10.0, 5.0, 100.0]})
            edited_waste = st.data_editor(df_in, hide_index=True)
            submit_w = st.form_submit_button("공정 설계 (Design Process)")
    
    with c2:
        st.subheader("📊 Pollutant Removal Efficiency")
        if submit_w:
            raw = dict(zip(edited_waste['Param'], edited_waste['Raw']))
            treated = {
                'COD': raw['COD'] * 0.1, 
                'SS': raw['SS'] * 0.05, 
                'TDS': raw['TDS'] * 0.02 
            }
            
            fig_bar = go.Figure(data=[
                go.Bar(name='Raw Water', x=list(raw.keys()), y=list(raw.values()), marker_color='#95A5A6'),
                go.Bar(name='Treated Water', x=list(treated.keys()), y=list(treated.values()), marker_color='#2ECC71')
            ])
            fig_bar.update_layout(barmode='group', title="Treatment Performance Prediction")
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.subheader("🛤️ Process Flow Diagram (PFD)")
    col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
    col_p1.success("1. Raw Water Tank"); col_p1.markdown("⬇️")
    col_p2.info("2. DAF / Sand Filter"); col_p2.caption("SS Removal"); col_p2.markdown("⬇️")
    col_p3.warning("3. MBR (Bio)"); col_p3.caption("COD/BOD Removal"); col_p3.markdown("⬇️")
    col_p4.error("4. RO System"); col_p4.caption("TDS Removal"); col_p4.markdown("⬇️")
    col_p5.success("5. Product Water"); col_p5.caption("Industrial Reuse")