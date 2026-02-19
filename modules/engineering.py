import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go

def app():
    st.title("📏 Basic Engineering & Sizing Calculator")
    st.info("설비 규격 및 여재 충진량 산출 (AFM IFU V23.4 규격 적용)")

    tab_afm, tab_ro_sizing, tab_piping= st.tabs(["🧪 AFM/Media Filter Sizing", "💧 RO System Sizing","📏 Piping & Hydraulics"])

    with tab_afm:
        st.subheader("Media Filter & AFM Filling Calculation")
        c1, c2 = st.columns(2)
        with c1:
            tank_d = st.number_input("Tank Diameter (mm)", value=2000, step=100, key="afm_d")
            bed_h = st.number_input("Media Bed Height (mm)", value=1200, step=100, help="지지층을 포함한 총 여재 높이", key="afm_h")
            media_type = st.selectbox("Media Type", ["AFM (Activated Filter Media)", "Sand (Quartz Sand)", "Anthracite"], key="afm_type")
            is_afm = False; use_grade0 = False; bottom_type = "Nozzle Plate"
            if "AFM" in media_type:
                is_afm = True; st.markdown("---"); st.markdown("**⚙️ AFM Configuration (IFU V23.4)**")
                bottom_type = st.radio("Filter Bottom Type", ["Nozzle Plate (노즐판)", "Lateral System (스트레이너)"], help="노즐판은 Grade 3가 필요 없으나, 스트레이너 방식은 하부 보호를 위해 Grade 3가 필수입니다.")
                use_grade0 = st.checkbox("Grade 0 (0.25~0.5mm) 포함 (Ultra-filtration)", value=False, help="1 micron 이하 제거 및 SDI 저감이 필요한 경우 선택 (RO 전처리 권장)")
        radius = tank_d / 2000; height = bed_h / 1000; volume = math.pi * (radius ** 2) * height
        with c2:
            st.markdown("#### 🎯 Calculation Summary")
            st.metric("Total Bed Volume", f"{volume:.2f} m³")
            if not is_afm:
                density = 1.6 if "Sand" in media_type else 0.9; total_weight = volume * density * 1000
                st.metric("Total Media Weight", f"{total_weight:.0f} kg", f"Bulk Density: {density} kg/l")
            else:
                d_g0 = 1.24; d_g1 = 1.33; d_g2 = 1.40; d_g3 = 1.43; ratio = {} 
                if "Lateral" in bottom_type:
                    if use_grade0: ratio = {'G0': 0.20, 'G1': 0.30, 'G2': 0.30, 'G3': 0.20}; st.info("💡 **Laterals + Grade 0:** G0(20%) / G1(30%) / G2(30%) / G3(20%) 비율 적용")
                    else: ratio = {'G1': 0.60, 'G2': 0.20, 'G3': 0.20}; st.info("💡 **Laterals Standard:** G1(60%) / G2(20%) / G3(20%) 비율 적용")
                else:
                    if use_grade0: ratio = {'G0': 0.20, 'G1': 0.30, 'G2': 0.50}; st.info("💡 **Nozzle + Grade 0:** G0(20%) / G1(30%) / G2(50%) 비율 적용")
                    else: ratio = {'G1': 0.70, 'G2': 0.30}; st.info("💡 **Nozzle Standard:** G1(70%) / G2(30%) 비율 적용")
                w_g0 = volume * ratio.get('G0', 0) * d_g0 * 1000; w_g1 = volume * ratio.get('G1', 0) * d_g1 * 1000
                w_g2 = volume * ratio.get('G2', 0) * d_g2 * 1000; w_g3 = volume * ratio.get('G3', 0) * d_g3 * 1000
                total_afm_weight = w_g0 + w_g1 + w_g2 + w_g3
                st.metric("Total AFM Weight", f"{total_afm_weight:.0f} kg")

        if is_afm:
            st.divider(); st.markdown("### 🧪 AFM Grade-specific Layering (25kg Bags)")
            cols = st.columns(4 if use_grade0 else 3)
            if use_grade0:
                with cols[0]: bags = math.ceil(w_g0 / 25); st.success(f"🟣 **Grade 0** (Top)\n\n**{w_g0:.0f} kg**\n\n📦 **{bags} Bags**\n\nSize: 0.25-0.5mm\nDensity: {d_g0}")
            idx_g1 = 1 if use_grade0 else 0
            with cols[idx_g1]: bags = math.ceil(w_g1 / 25); st.error(f"🔴 **Grade 1**\n\n**{w_g1:.0f} kg**\n\n📦 **{bags} Bags**\n\nSize: 0.4-0.8mm\nDensity: {d_g1}")
            idx_g2 = 2 if use_grade0 else 1
            with cols[idx_g2]: bags = math.ceil(w_g2 / 25); st.info(f"🔵 **Grade 2**\n\n**{w_g2:.0f} kg**\n\n📦 **{bags} Bags**\n\nSize: 0.7-2.0mm\nDensity: {d_g2}")
            if "Lateral" in bottom_type:
                idx_g3 = 3 if use_grade0 else 2
                with cols[idx_g3]: bags = math.ceil(w_g3 / 25); st.warning(f"⚫ **Grade 3** (Base)\n\n**{w_g3:.0f} kg**\n\n📦 **{bags} Bags**\n\nSize: 2.0-4.0mm\nDensity: {d_g3}")

    with tab_ro_sizing:
        st.subheader("💧 RO System Configuration & Design")
        st.info("💡 **설계 플럭스**와 **원수 TDS**를 기반으로 멤브레인 배열과 고압 펌프 사양을 자동 산출합니다.")
        r1, r2 = st.columns(2)
        with r1:
            st.markdown("### ⚙️ 설계 입력 (Input Data)")
            st.markdown("**1. 생산 목표 (Production)**")
            target_p = st.number_input("목표 생산수 유량 (m3/hr)", value=50.0, step=1.0, key="ro_target_p")
            target_rec = st.slider("목표 회수율 (Recovery, %)", 40, 95, 75, key="ro_target_rec")
            st.markdown("**2. 멤브레인 설계 (Membrane)**")
            design_flux = st.number_input("설계 플럭스 (Flux, LMH)", value=18.7, step=0.1, help="값을 높이면 베셀 수가 줄어들고, 낮추면 늘어납니다.", key="ro_flux")
            elements_per_vessel = st.selectbox("베셀당 엘리먼트 수", [4, 5, 6, 7], index=2, key="ro_ele_per_ves")
            active_area = st.number_input("엘리먼트 유효 면적 (ft²)", value=400, step=10, key="ro_area")
            st.markdown("**3. 펌프 설계 (Pump)**")
            feed_tds = st.number_input("원수 TDS (mg/L)", value=500, step=50, help="삼투압 계산용")
            pump_eff = st.number_input("펌프 효율 (%)", value=65.0, step=1.0); motor_eff = st.number_input("모터 효율 (%)", value=92.0, step=1.0)
            with st.expander("ℹ️ [가이드] 적정 플럭스 범위", expanded=False): st.markdown("* **18 ~ 22 LMH:** 깨끗한 지하수/상수 (부장님 추천 범위)\n* **14 ~ 18 LMH:** 하천수/지표수\n* **10 ~ 14 LMH:** 폐수 재이용/오염된 물")

        feed_flow = target_p / (target_rec / 100); concentrate_flow = feed_flow - target_p
        total_area_m2 = (target_p * 1000) / design_flux; element_area_m2 = active_area * 0.0929
        total_elements = math.ceil(total_area_m2 / element_area_m2); total_vessels = math.ceil(total_elements / elements_per_vessel)
        actual_flux = (target_p * 1000) / (total_elements * element_area_m2)
        v2_st1 = int(round(total_vessels * 0.666)); v2_st2 = total_vessels - v2_st1
        if v2_st2 < 1: v2_st1 -= 1; v2_st2 += 1
        str_2st = f"{v2_st1} : {v2_st2}"
        
        avg_tds = feed_flow * feed_tds / (feed_flow + concentrate_flow) * 1.5; osmotic_pressure = (avg_tds / 1000.0) * 0.75
        base_pressure = 12.0; piping_loss = 2.0; required_pressure = base_pressure + osmotic_pressure + piping_loss
        shaft_power = (feed_flow * required_pressure) / (36 * (pump_eff / 100.0)); required_motor = shaft_power / (motor_eff / 100.0) * 1.15 

        with r2:
            st.markdown("### 🎯 설계 결과 (Engineering Result)")
            res_tab1, res_tab2 = st.tabs(["🏗️ 멤브레인 배열", "🔌 고압 펌프 선정"])
            with res_tab1:
                with st.container(border=True):
                    st.metric("총 엘리먼트 / 베셀", f"{total_elements} EA / {total_vessels} PV"); st.metric("실제 운전 플럭스", f"{actual_flux:.1f} LMH")
                    st.metric("표준 배열 (2:1)", str_2st); st.caption(f"**Stage 1:** {v2_st1} PV  ➔  **Stage 2:** {v2_st2} PV")
                if target_rec <= 80: st.success("✅ **[적합]** 2단 배열(2:1)이 가장 효율적입니다.")
                else: st.warning("⚠️ **[주의]** 고회수율 운전 시 유속 저하 주의.")
                c_f1, c_f2 = st.columns(2)
                c_f1.metric("유입수 유량", f"{feed_flow:.1f} m³/hr"); c_f2.metric("농축수 유량", f"{concentrate_flow:.1f} m³/hr")
            with res_tab2:
                with st.container(border=True):
                    design_q = feed_flow * 1.1
                    st.metric("펌프 설계 유량 (Q)", f"{design_q:.1f} m³/hr", f"Operating: {feed_flow:.1f}"); st.metric("필요 양정/압력 (H)", f"{required_pressure:.1f} bar", f"Osmotic: {osmotic_pressure:.1f} bar")
                    st.metric("모터 동력 (P)", f"{required_motor:.1f} kW", f"Shaft: {shaft_power:.1f} kW")
                st.info(f"**💡 펌프 선정 가이드**\n- **Flow:** {math.ceil(design_q)} m³/hr 이상\n- **Head:** {math.ceil(required_pressure)} bar 이상\n- **Motor:** {math.ceil(required_motor)} kW (여유율 15% 포함)")

    with tab_piping:
        st.subheader("📏 배관 유속 및 마찰 손실 (Piping Hydraulics)")
        st.info("💡 **Hazen-Williams 공식**을 사용하여 유속(Velocity)과 마찰 손실(Head Loss)을 정밀 계산합니다.")
        PIPE_DB = {
            "15A (1/2\")":  {"SCH 10": 17.1, "SCH 40": 15.8, "SCH 80": 13.9}, "20A (3/4\")":  {"SCH 10": 22.5, "SCH 40": 20.9, "SCH 80": 18.9},
            "25A (1\")":    {"SCH 10": 27.9, "SCH 40": 26.6, "SCH 80": 24.3}, "32A (1-1/4\")":{"SCH 10": 36.6, "SCH 40": 35.1, "SCH 80": 32.5},
            "40A (1-1/2\")":{"SCH 10": 42.7, "SCH 40": 40.9, "SCH 80": 38.1}, "50A (2\")":    {"SCH 10": 54.8, "SCH 40": 52.5, "SCH 80": 49.3},
            "65A (2-1/2\")":{"SCH 10": 66.9, "SCH 40": 62.7, "SCH 80": 59.0}, "80A (3\")":    {"SCH 10": 82.8, "SCH 40": 77.9, "SCH 80": 73.7},
            "100A (4\")":   {"SCH 10": 108.2, "SCH 40": 102.3, "SCH 80": 97.2}, "125A (5\")":   {"SCH 10": 134.5, "SCH 40": 128.2, "SCH 80": 122.3},
            "150A (6\")":   {"SCH 10": 161.5, "SCH 40": 154.1, "SCH 80": 146.3}, "200A (8\")":   {"SCH 10": 211.6, "SCH 40": 202.7, "SCH 80": 193.7},
            "250A (10\")":  {"SCH 10": 264.7, "SCH 40": 254.5, "SCH 80": 242.9}, "300A (12\")":  {"SCH 10": 314.7, "SCH 40": 303.2, "SCH 80": 288.9},
            "350A (14\")":  {"SCH 10": 346.0, "SCH 40": 333.3, "SCH 80": 317.5}, "400A (16\")":  {"SCH 10": 396.8, "SCH 40": 381.0, "SCH 80": 363.5},
        }
        C_FACTOR = { "PVC / PE / Plastic": 150, "Stainless Steel (SUS)": 140, "Carbon Steel (New)": 120, "Carbon Steel (Old)": 100, "Concrete": 120 }
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("##### ⚙️ 운전 조건 (Condition)")
            flow_m3 = st.number_input("유량 (Flow Rate, m³/hr)", value=50.0, step=1.0)
            pipe_len = st.number_input("배관 길이 (Length, m)", value=100.0, step=10.0)
            st.markdown("##### 🧪 배관 재질 (Material)")
            mat_sel = st.selectbox("재질 선택 (Roughness)", list(C_FACTOR.keys())); c_val = C_FACTOR[mat_sel]; st.caption(f"적용 C-Factor: {c_val}")
        with col_p2:
            st.markdown("##### 📏 배관 규격 (Size & Schedule)")
            sch_sel = st.radio("배관 두께 (Schedule)", ["SCH 10", "SCH 40", "SCH 80"], horizontal=True)
            size_sel = st.selectbox("호칭경 (Nominal Dia)", list(PIPE_DB.keys()), index=8) 
            real_id_mm = PIPE_DB[size_sel].get(sch_sel, 0); st.metric("실제 내경 (Inner Dia)", f"{real_id_mm} mm", f"{sch_sel} 기준")

        st.divider()
        if real_id_mm > 0 and flow_m3 > 0:
            area_m2 = math.pi * ((real_id_mm / 1000) / 2) ** 2; velocity = (flow_m3 / 3600) / area_m2 
            dp_100m_bar = 6.05 * (10**5) * (flow_m3 ** 1.85) / ((c_val ** 1.85) * (real_id_mm ** 4.87))
            total_dp_bar = dp_100m_bar * (pipe_len / 100.0); total_head_m = total_dp_bar * 10.197 
            st.subheader("📊 유체 역학 분석 결과")
            c_res1, c_res2, c_res3 = st.columns(3)
            with c_res1:
                st.metric("유속 (Velocity)", f"{velocity:.2f} m/s")
                if velocity > 3.0: st.error("⛔ **유속 과다 (Too High)**\n- 침식(Erosion) 및 수격현상(Water Hammer) 위험.\n- 배관을 키우십시오.")
                elif velocity > 2.5: st.warning("⚠️ **유속 높음 (High)**\n- 토출측 허용 한계이나 소음 발생 가능.")
                elif velocity < 0.5: st.warning("⚠️ **유속 저하 (Too Low)**\n- 슬러지 침적(Sedimentation) 우려.")
                else: st.success("✅ **적정 유속 (Good)**\n- (0.5 ~ 2.5 m/s) 범위 만족.")
            with c_res2: st.metric("마찰 손실 (Pressure Drop)", f"{total_dp_bar:.3f} bar", f"길이 {pipe_len}m 기준"); st.caption(f"단위 손실: {dp_100m_bar:.3f} bar/100m")
            with c_res3: st.metric("손실 수두 (Head Loss)", f"{total_head_m:.2f} m"); st.info("💡 펌프 선정 시 이 값 이상의 양정(Head) 여유가 필요합니다.")

            st.markdown("---")
            with st.expander("💡 **[AI 추천] 적정 배관 사이즈 찾기**", expanded=True):
                target_v = 1.8; req_area = (flow_m3 / 3600) / target_v; req_d_mm = math.sqrt(req_area / math.pi) * 2000
                best_size = "N/A"
                for size, specs in PIPE_DB.items():
                    if specs["SCH 40"] >= req_d_mm: best_size = size; break
                c_rec1, c_rec2 = st.columns([1, 3])
                with c_rec1: st.markdown(f"### 👉 추천: **{best_size}**")
                with c_rec2: st.caption(f"경제적 유속(1.8 m/s) 기준 계산된 최소 내경은 **{req_d_mm:.1f} mm** 입니다."); st.caption(f"현재 선택된 **{size_sel}** (내경 {real_id_mm}mm)와 비교해 보십시오.")