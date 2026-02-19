import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import math
from utils.calculations import Boiler_Expert_Engine

def app(PRODUCT_CATALOG):
    if 'b_data_feed' not in st.session_state:
        st.session_state.b_data_feed = pd.DataFrame({
            'Item': ['pH', 'Cond (uS/cm)', 'Hardness (ppm)', 'Cl (ppm)', 'SiO2 (ppm)', 'M-Alk (ppm)', 'Fe (ppm)'],
            'Feedwater': [8.5, 150.0, 1.0, 15.0, 2.0, 40.0, 0.05]
        })
    if 'b_res_store' not in st.session_state:
        st.session_state.b_res_store = {
            'steam': 10.0, 'feed': 10.7, 'blow': 0.7, 'coc': 15.0, 'dose_ppm': 100.0, 'naoh_pct': 20.0
        }

    st.title("🔥 Boiler Master Pro")
    st.info("증기 발생량 대비 정밀 물질수지(Water Balance)와 가성소다 함량 기반 수질 예측 시스템입니다.")

    tab_sim, tab_chem_prog, tab_safety, tab_risk, tab_manual = st.tabs([
        "💧Water Simulation & Balance", 
        "💊 Chemical Program (약품)", 
        "🎯 Na-PO4 Safety Map", 
        "🛡️ 설비 진단 (Risk & Cost)",
        "📘 기술 매뉴얼 (Formula)",
       
    ])
    
    with tab_sim:
        st.subheader("1. Boiler Water Balance & Quality Prediction")
        col_b1, col_b2 = st.columns([1, 1.2])
        with col_b1:
            st.markdown("###### ① 급수 수질 데이터 (Feedwater Quality)")
            e_bf = st.data_editor(st.session_state.b_data_feed, hide_index=True, key="b_editor_expert_v2", column_config={"Feedwater": st.column_config.NumberColumn(format="%.1f")})
            mu_v = dict(zip(e_bf['Item'], e_bf['Feedwater']))
            st.caption("※ 위 데이터는 '보급수(Make-up)' 기준입니다.")

        with col_b2:
            st.markdown("###### ② 운전 조건 및 물질수지 (Mass Balance)")
            b_steam = st.number_input("증기 생산량 (Steam, ton/hr)", value=10.0, key="b_steam_ex")
            b_pressure = st.number_input("운전 압력 (Pressure, bar)", value=10.0, key="b_press_ex")
            sat_temp, sat_h = Boiler_Expert_Engine.get_steam_enthalpy(b_pressure)
            st.write(f"🔥 포화 온도: **{sat_temp} °C** (Antoine Eq. 적용)")
            st.divider()
            b_coc = st.slider("목표 농축배수 (Cycles)", 2.0, 50.0, 15.0, 0.5, key="b_coc_ex")
            b_return_pct = st.slider("응축수 회수율 (Condensate Return %)", 0, 100, 50, key="b_ret_ex")
            if b_coc > 1: b_blowdown = b_steam / (b_coc - 1)
            else: b_blowdown = 0.0
            b_feedwater = b_steam + b_blowdown
            b_condensate = b_feedwater * (b_return_pct / 100.0)
            b_makeup = b_feedwater - b_condensate
            with st.container(border=True):
                c_m1, c_m2, c_m3 = st.columns(3)
                c_m1.metric("총 급수량 (Total Feed)", f"{b_feedwater:.1f} t/h")
                c_m2.metric("보급수 (Make-up)", f"{b_makeup:.1f} t/h", f"회수율 {b_return_pct}%")
                c_m3.metric("배수량 (Blowdown)", f"{b_blowdown:.1f} t/h")
            st.write("---")
            b_dose_ppm = st.number_input("청관제 목표농도 (ppm, 급수대비)", value=100.0, step=10.0, key="b_dose_ex")
            b_naoh_pct = st.number_input("청관제 내 가성소다(NaOH) 함량 (%)", value=20.0, step=1.0, key="b_naoh_ex")
            st.session_state.b_res_store = { 'steam': b_steam, 'feed': b_feedwater, 'blow': b_blowdown, 'coc': b_coc, 'dose_ppm': b_dose_ppm, 'naoh_pct': b_naoh_pct }

        cond_tds_assumed = 5.0 
        mu_ratio = (100 - b_return_pct) / 100.0
        feed_cond = (mu_v['Cond (uS/cm)'] * mu_ratio) + (cond_tds_assumed * (b_return_pct/100.0))
        feed_m_alk = mu_v['M-Alk (ppm)'] * mu_ratio
        feed_cl = mu_v['Cl (ppm)'] * mu_ratio
        feed_sio2 = mu_v['SiO2 (ppm)'] * mu_ratio
        feed_fe = mu_v['Fe (ppm)'] * mu_ratio + (0.05 * (b_return_pct/100.0))
        feed_ph_est = mu_v['pH'] 
        feed_p_alk = feed_m_alk * 0.5 if feed_ph_est >= 8.3 else 0.0

        naoh_boost = b_dose_ppm * (b_naoh_pct / 100) * 1.25 
        p_m_alk = (feed_m_alk * b_coc) + naoh_boost
        p_p_alk = (feed_p_alk * b_coc) + naoh_boost 
        if p_p_alk > 0 and p_m_alk > 0:
            if 2 * p_p_alk > p_m_alk: oh_alk = 2 * p_p_alk - p_m_alk; p_ph = 11.0 + math.log10(max(oh_alk, 1)) * 0.6 
            else: p_ph = 9.3 + math.log10(max(p_m_alk, 1)) * 0.5
        else: p_ph = mu_v['pH']
        p_ph = min(p_ph, 12.5) 
        p_cond = (feed_cond * b_coc) + (naoh_boost * 5.5)
        p_cl = feed_cl * b_coc
        p_sio2 = feed_sio2 * b_coc
        p_fe = feed_fe * b_coc

        try: _, l_cond = Boiler_Expert_Engine.check_asme_standard(b_pressure, p_cond, p_sio2, p_m_alk)
        except: l_cond = 3000.0

        st.divider()
        st.subheader(f"📊 보일러 관수 수질 예측 (농축 {b_coc}배, P-Alk 추정 적용)")
        p_df = pd.DataFrame({
            '측정 항목': ['pH (예측값)', 'P-Alk (ppm)', 'M-Alk (ppm)', 'Cond (uS/cm)', 'SiO2 (ppm)', 'Cl (ppm)'],
            '보급수 (Make-up)': [f"{mu_v['pH']:.1f}", f"{feed_p_alk:.1f} (Est)", f"{mu_v['M-Alk (ppm)']:.1f}", f"{mu_v['Cond (uS/cm)']:.1f}", f"{mu_v['SiO2 (ppm)']:.1f}", f"{mu_v['Cl (ppm)']:.1f}"],
            '혼합 급수 (Feed)': ["-", f"{feed_p_alk*mu_ratio:.1f}", f"{feed_m_alk:.1f}", f"{feed_cond:.1f}", f"{feed_sio2:.1f}", f"{feed_cl:.1f}"],
            '관수 (Boiler W)': [f"{p_ph:.1f}", f"{p_p_alk:.0f}", f"{p_m_alk:.0f}", f"{p_cond:.0f}", f"{p_sio2:.1f}", f"{p_cl:.1f}"],
            'ASME/관리 기준': ["11.0~11.8", "M-Alk의 1/2↑", "800 이하", f"{l_cond:.0f} 이하", "P 비례", "-"]
        })
        st.table(p_df)
        if p_m_alk > 0:
            pm_ratio = p_p_alk / p_m_alk
            if pm_ratio < 0.4: st.warning(f"⚠️ **P-Alk 부족 ({pm_ratio:.2f}):** P-Alk가 M-Alk의 50% 미만입니다. 실리카 스케일 위험이 있으니 가성소다 비중을 높이세요.")
            elif pm_ratio > 0.6: st.info(f"✅ **Free OH 확보 ({pm_ratio:.2f}):** P-Alk가 충분하여 실리카가 용해 상태로 유지됩니다.")

        st.markdown("---")
        st.subheader("📈 농축배수 한계점 진단 (Limit Study)")
        if b_pressure <= 20: abma_limit_tds = 3500; range_msg = "저압 구간 (0~20 bar)"
        elif b_pressure <= 30: abma_limit_tds = 3000; range_msg = "중압 구간 (21~30 bar)"
        elif b_pressure <= 40: abma_limit_tds = 2500; range_msg = "고압 구간 (31~40 bar)"
        elif b_pressure <= 50: abma_limit_tds = 2000; range_msg = "초고압 구간 (41~50 bar)"
        else: abma_limit_tds = 1500; range_msg = "극초고압 (>50 bar)"
        st.info(f"💡 현재 압력 **{b_pressure} bar**는 **[{range_msg}]**에 해당하며, 허용 TDS는 **{abma_limit_tds} ppm**입니다.")
        ignore_silica = False
        if b_pressure < 30:
            ignore_silica = True; dist_ratio = 0.0; st.success("✅ **저압 운전 (<30 bar):** 실리카 캐리오버(Carryover) 위험이 없어 **무시합니다.**")
        else:
            dist_ratio = 0.00005 * math.pow(b_pressure, 1.8); st.warning("⚠️ **고압 운전 (≥30 bar):** 실리카가 스팀으로 녹아들어갈 위험이 있어 **정밀 관리**합니다.")

        cycles_range = np.arange(5, 65, 1)
        sim_data = []
        feed_tds = mu_v.get('Cond (uS/cm)', 150) * (1 - b_return_pct/100)
        feed_sio2 = mu_v.get('SiO2 (ppm)', 2.0) * (1 - b_return_pct/100)
        limit_factor = "None"; max_safe_cycle = 5.0 

        for cyc in cycles_range:
            bw_tds = feed_tds * cyc
            bw_sio2 = feed_sio2 * cyc
            steam_sio2_ppb = (bw_sio2 * dist_ratio) * 1000 
            status = "Safe"
            if bw_tds > abma_limit_tds: status = "Fail (TDS)"; limit_factor = "TDS (거품 발생 위험)" if limit_factor == "None" else limit_factor
            if not ignore_silica and steam_sio2_ppb > 20: status = "Fail (SiO2)"; limit_factor = "Silica (터빈 보호)" if limit_factor == "None" else limit_factor
            if status == "Safe": max_safe_cycle = cyc
            sim_data.append({"Cycles": cyc, "Boiler TDS": bw_tds, "Steam SiO2 (ppb)": steam_sio2_ppb, "Status": status})
        df_sim = pd.DataFrame(sim_data)

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
                st.info("비활성화: 저압 조건에서는 실리카가 스팀으로 넘어가지 않습니다.")
                fig_sio2 = px.line(title="Low Pressure - No Silica Risk")
                fig_sio2.add_annotation(text="Safe Zone (Low Pressure)", x=30, y=0, showarrow=False, font=dict(size=20))
            else:
                fig_sio2 = px.line(df_sim, x="Cycles", y="Steam SiO2 (ppb)", title="농축배수 vs 스팀 실리카")
                fig_sio2.add_hline(y=20, line_dash="dash", line_color="red", annotation_text="Turbine Limit (20ppb)")
                fig_sio2.add_vline(x=max_safe_cycle, line_dash="dot", line_color="green", annotation_text="Max Safe")
            st.plotly_chart(fig_sio2, use_container_width=True)

        st.subheader("📢 진단 결과")
        if limit_factor == "None": st.success(f"✅ 현재 조건에서는 **60배수 이상** 고농축 운전도 가능합니다. (수질 매우 양호)")
        else:
            if ignore_silica: st.success(f"✅ 저압 조건이므로 실리카 제한은 없습니다.")
            st.warning(f"⚠️ 운전 가능 최대 농축배수는 **{max_safe_cycle}배** 입니다.")
            st.error(f"🛑 제한 요인: **{limit_factor}** 기준을 초과합니다.")

        if max_safe_cycle > b_coc:
            st.markdown("---")
            st.subheader("💰 에너지 비용 절감 분석 (Cost Benefit)")
            st.info("💡 농축배수를 올리면 **'버려지는 뜨거운 물(Blowdown)'**이 줄어들어 연료비가 절감됩니다.")
            col_cost1, col_cost2 = st.columns(2)
            with col_cost1: unit_cost = st.number_input("블로우다운 톤당 단가 (원/ton)", value=40000, step=1000, format="%d", help="고온수(150~200도) 1톤을 만드는 데 들어가는 비용 (연료비+용수비+약품비). 통상 3~5만원 적용")
            with col_cost2: op_days = st.number_input("연간 가동 일수 (일/년)", value=300, step=10)
            curr_blow_rate = b_steam / (b_coc - 1); opt_blow_rate = b_steam / (max_safe_cycle - 1)
            save_rate_hr = curr_blow_rate - opt_blow_rate
            save_ton_year = save_rate_hr * 24 * op_days
            save_money_year = save_ton_year * unit_cost
            st.markdown(f"""#### 📊 분석 결과\n* **시간당 절감량:** `{save_rate_hr:.2f} ton/hr` (고온 배출수 감소)\n* **연간 절감 물량:** `{save_ton_year:,.0f} ton/year` ({op_days}일 기준)\n* **💰 연간 예상 절감액:** :green[**{save_money_year/100000000:.2f} 억원**]""")
            st.caption(f"※ 계산 근거: {save_ton_year:,.0f}톤 × {unit_cost:,}원 = {save_money_year:,.0f}원")
    
    with tab_chem_prog:
        st.subheader("2. Integrated Boiler Chemical Program & Diagnosis")
        
        # 1. 데이터 로드 및 시뮬레이션 변수 매칭 (오류 방지)
        # Tab 1에서 계산된 p_m_alk, p_sio2, p_p_alk, p_cond, l_cond를 직접 사용합니다.
        res = st.session_state.get('b_res_store', {'feed': 10.0, 'dose_ppm': 100.0})
        
        # -------------------------------------------------------------------------
        # [핵심] 보일러 정밀 진단 리포트 (전문가 기준 반영)
        # -------------------------------------------------------------------------
        with st.expander("📘 [엔지니어링 리포트] 보일러 운전 건전성 및 수질 평형 진단", expanded=True):
            st.markdown("### 1️⃣ 화학적 처리 및 스케일 억제력 진단")
            br_col1, br_col2, br_col3 = st.columns(3)
            
            with br_col1:
                st.markdown("#### 🛡️ 실리카 용해력 (M-Alk/SiO2)")
                # 전문가 가이드: M-알칼리도가 실리카의 1.7배 이상인지 진단
                alk_sio2_ratio = p_m_alk / max(p_sio2, 0.1)
                if alk_sio2_ratio >= 1.7:
                    st.markdown(f"**상태: :blue[안전 ({alk_sio2_ratio:.2f})]**")
                    st.caption(f"기준치(1.7배) 이상 확보되었습니다. 실리카가 안정적으로 용해되어 스케일 위험이 낮습니다.")
                else:
                    st.markdown(f"**상태: :red[위험 ({alk_sio2_ratio:.2f})]**")
                    st.caption(f"기준치(1.7배) 미달입니다. 실리카 스케일 방지를 위해 가성소다 비중 상향이 시급합니다.")

            with br_col2:
                st.markdown("#### 💎 인산염 처리 지표 (P-Alk)")
                # 시뮬레이션된 P-알칼리도(p_p_alk)를 기준으로 진단
                if p_p_alk >= 300: 
                    st.markdown(f"**상태: :blue[양호 ({p_p_alk:.0f}ppm)]**")
                    st.caption("충분한 P-알칼리도가 형성되어 관수 내 부식 및 하드 스케일 억제력이 우수합니다.")
                else:
                    st.markdown(f"**상태: :orange[주의]**")
                    st.caption("P-알칼리도가 낮습니다. 청관제 농도 상향 또는 가성소다 함량 조정을 권고합니다.")

            with br_col3:
                st.markdown("#### 🧪 농축 한계 진단 (Cond)")
                # 시뮬레이션된 전도도(p_cond)와 한계치(l_cond) 비교
                if p_cond <= l_cond:
                    st.markdown(f"**상태: :blue[정상 ({p_cond:.0f})]**")
                    st.caption(f"예측 전도도가 관리 기준({l_cond:.0f} µS/cm) 이내에서 안정적으로 유지됩니다.")
                else:
                    st.markdown(f"**상태: :red[기준 초과]**")
                    st.caption(f"전도도가 기준을 초과하여 거품 발생(Foaming) 및 캐리오버 위험이 높습니다.")
# -------------------------------------------------------------------------
            # [섹션 2] 산소 부식 및 탈기기 성능 진단 (새로 추가되는 위치)
            # -------------------------------------------------------------------------
            st.markdown("---")
            st.markdown("### 2️⃣ 산소 부식 진단 및 약품 요구량 (CHZ 10% 기준)")
            
            # 탈기기 설정 및 효율 조정
            sys_col1, sys_col2 = st.columns(2)
            with sys_col1:
                has_deaerator = st.toggle("탈기기(Deaerator) 설치 여부", value=True, key="b_has_da_v7")
                if has_deaerator:
                    da_performance = st.select_slider(
                        "탈기기 성능 (잔류 산소 ppb)",
                        options=[7, 15, 30, 50, 100], value=15,
                        help="기계적 탈기 효율을 선택하세요. (7ppb: 최상, 100ppb: 불량)",
                        key="b_da_ppb_v7"
                    )
                    est_do = da_performance / 1000.0
                else:
                    feed_temp_input = st.number_input("급수 온도 (℃)", 20, 100, 85, key="b_feed_temp_v7")
                    est_do = 14.6 * math.exp(-0.022 * feed_temp_input)
            
            # --- 함량 반영 계산 로직 ---
            chz_active_pct = 10.0  # 전문가님이 말씀하신 제품 함량 10%
            
            # 1. 순수 성분(Active) 기준 요구량 (이론 당량 1.4배 적용)
            sf = 1.5 if has_deaerator else 2.5
            active_required_ppm = est_do * 1.4 * sf
            
            # 2. 10% 제품 기준 실제 투입 농도 계산 (Active / 0.1)
            product_dosage_ppm = active_required_ppm * (100 / chz_active_pct)
            
            with sys_col2:
                st.info(f"**추정 잔류 산소:** {est_do:.3f} ppm")
                st.warning(f"**제품 투입 권장량 (10%):** :red[{product_dosage_ppm:.1f} ppm]")
                st.caption(f"※ 순수 성분 요구량 {active_required_ppm:.2f} ppm을 10% 제품으로 환산")
# -------------------------------------------------------------------------
        # [최종] Target pH 설정을 포함한 응축수 아민 설계
        # -------------------------------------------------------------------------
        st.markdown("---")
        st.markdown("### 3️⃣ 응축수 부식 진단 및 복합 아민 설계 (Target pH 설정)")
        
        am_col1, am_col2 = st.columns(2)
        
        with am_col1:
            st.caption("💡 제품 성분 함량 및 목표 pH를 설정하십시오.")
            
            # 1. 성분별 개별 함량 입력
            pct_m = st.number_input("Morpholine 함량 (%)", 0.0, 100.0, 10.0, step=1.0, key="am_pct_m_v11")
            pct_c = st.number_input("Cyclohexylamine 함량 (%)", 0.0, 100.0 - pct_m, 10.0, step=1.0, key="am_pct_c_v11")
            pct_e = st.number_input("MEA 함량 (%)", 0.0, 100.0 - pct_m - pct_c, 0.0, step=1.0, key="am_pct_e_v11")
            
            total_active = pct_m + pct_c + pct_e
            
            # 2. Target pH 설정 슬라이더 (실무적 가중치 반영)
            target_ph = st.select_slider(
                "🎯 목표 응축수 pH (Target pH)",
                options=[8.0, 8.5, 9.0, 9.2],
                value=8.5,
                help="8.0: 최소 보호 | 8.5: 표준 관리 | 9.0: 강력 보호 | 9.2: 고압/터빈 시스템",
                key="am_target_ph_val"
            )
            
            # pH별 요구량 가중치 (pH 9.0을 1.0으로 보았을 때의 상대적 필요량)
            ph_weight_map = {8.0: 0.5, 8.5: 0.75, 9.0: 1.0, 9.2: 1.3}
            ph_weight = ph_weight_map[target_ph]

        # 3. 계산 로직
        est_co2_steam = feed_m_alk * 0.79 
        
        if total_active > 0:
            # 통합 중화 파워 (M: 2.0, C: 2.25, E: 1.4)
            active_power = (pct_m/100 * 2.0) + (pct_c/100 * 2.25) + (pct_e/100 * 1.4)
            
            # 최종 제품 ppm 계산
            # (CO2량 * 통합당량 * pH가중치 * 안전계수 1.1) / (함량비)
            required_product_ppm = (est_co2_steam * active_power * ph_weight * 1.1) / (total_active/100)
        else:
            required_product_ppm = 0

        with am_col2:
            st.metric("증기 내 CO2 추정", f"{est_co2_steam:.1f} ppm")
            if total_active > 0:
                st.success(f"**최종 제품 권장 농도 (Target pH {target_ph})**")
                st.subheader(f"{required_product_ppm:.1f} ppm")
                st.caption(f"설정하신 pH {target_ph} 유지를 위한 엔지니어링 계산 결과입니다.")
            else:
                st.error("성분 함량을 입력하세요.")

        st.info(f"""
        💡 **엔지니어링 팁:** 목표 pH를 **{target_ph}**로 설정함에 따라 
        중화 효율 가중치 **{ph_weight}**가 적용되었습니다. 
        실제 현장에서는 급수 M-알칼리도의 변동에 따라 pH 수치가 달라질 수 있으므로 정기적인 분석이 필요합니다.
        """)
        # -------------------------------------------------------------------------
        # [약품 설계] 실제 투입 제품 선정 및 소요량 계산
        # -------------------------------------------------------------------------
        st.info(f"💡 **설계 기준:** 총 급수량 {res['feed']:.1f} t/h | 청관제 목표 {res['dose_ppm']:.1f} ppm")
        
        c_col1, c_col2, c_col3 = st.columns(3)
        boiler_db = PRODUCT_CATALOG.get('Boiler', {})
        
        with c_col1:
            st.markdown("#### 🌬️ Oxygen Scavenger")
            oxy_list = boiler_db.get('Oxygen_Scavenger') or boiler_db.get('OxygenScavenger') or []
            if oxy_list:
                sel_oxy = st.selectbox("탈산제 선택", [o['Name'] for o in oxy_list], key="b_sel_oxy_final")
                oxy_item = next((i for i in oxy_list if i['Name'] == sel_oxy), None)
                def_oxy = float(oxy_item['Dosage']) if oxy_item else 20.0
                if oxy_item:
                    with st.container(border=True):
                        st.markdown(f"**🧪 성분:** :red[{oxy_item.get('Main_Ingredient', '-')}]")
                        st.markdown(f"**💡 특징:** :blue[{oxy_item.get('Sales_Point', '-')}]")
            else: 
                st.warning("데이터 없음")
                def_oxy = 0.0
            
            oxy_dose = st.number_input("탈산제 농도 (ppm)", value=def_oxy, key="b_oxy_val_final")
            usage_oxy = (res['feed'] * 24 * oxy_dose) / 1000.0

        with c_col2:
            st.markdown("#### 🛡️ Scale Inhibitor")
            scale_list = boiler_db.get('Scale_Disp') or boiler_db.get('Inhibitor') or []
            if scale_list:
                sel_scale = st.selectbox("청관제 선택", [s['Name'] for s in scale_list], key="b_sel_scale_final")
                scale_item = next((i for i in scale_list if i['Name'] == sel_scale), None)
                if scale_item:
                    with st.container(border=True):
                        st.markdown(f"**🧪 성분:** :red[{scale_item.get('Main_Ingredient', '-')}]")
                        st.markdown(f"**💡 특징:** :blue[{scale_item.get('Sales_Point', '-')}]")
            else: st.warning("데이터 없음")
            
            scale_dose = st.number_input("청관제 농도 (ppm)", value=float(res['dose_ppm']), key="b_scale_val_final")
            usage_scale = (res['feed'] * 24 * scale_dose) / 1000.0

        with c_col3:
            st.markdown("#### 🧪 Condensate")
            cond_list = boiler_db.get('Condensate') or boiler_db.get('응축수 pH') or []
            if cond_list:
                sel_cond = st.selectbox("복수처리제 선택", [c['Name'] for c in cond_list], key="b_sel_cond_final")
                cond_item = next((i for i in cond_list if i['Name'] == sel_cond), None)
                def_cond = float(cond_item['Dosage']) if cond_item else 5.0
                if cond_item:
                    with st.container(border=True):
                        st.markdown(f"**🧪 성분:** :red[{cond_item.get('Main_Ingredient', '-')}]")
                        st.markdown(f"**💡 특징:** :blue[{cond_item.get('Sales_Point', '-')}]")
            else: 
                sel_cond = st.selectbox("복수처리제 선택", ["None"], key="b_sel_cond_final_none")
                def_cond = 0.0
            
            cond_dose = st.number_input("기타 농도 (ppm)", value=def_cond, key="b_cond_val_final")
            usage_cond = (res['feed'] * 24 * cond_dose) / 1000.0

        st.divider()
        st.markdown("### 📊 일일 약품 소요량 (Daily Consumption)")
        b_plot_df = pd.DataFrame({
            'Category': ['Scavenger', 'Inhibitor', 'Condensate'], 
            'Usage (kg/day)': [usage_oxy, usage_scale, usage_cond]
        })
        fig_b_chem = px.bar(
            b_plot_df, x='Category', y='Usage (kg/day)', color='Category',
            text=b_plot_df['Usage (kg/day)'].apply(lambda x: f'{x:.1f} kg')
        )
        st.plotly_chart(fig_b_chem, use_container_width=True)

    with tab_safety:
        st.subheader("3. Na-PO4 Coordinate Map & Action Plan")
        c_s1, c_s2 = st.columns([1, 2])
        with c_s1:
            with st.container(border=True):
                st.markdown("### ⚙️ 설정 및 입력")
                boiler_type = st.radio("운전 모드 (Pressure Mode)", ["저압 보일러 (≤ 20bar)", "고압 보일러 (> 60bar)"], index=0, help="저압은 pH를 높게(11.0~11.8) 유지하며, 고압은 pH를 낮게(9.4~10.5) 관리합니다.")
                st.markdown("---")
                st.info("보일러 관수(Boiler Water) 분석치를 입력하세요.")
                cur_ph = st.number_input("현재 pH (at 25℃)", 8.0, 13.0, 11.5, 0.1, key="b_safe_ph_final")
                cur_po4 = st.number_input("현재 PO4 (ppm)", 0.0, 80.0, 25.0, 1.0, key="b_safe_po4_final")
        
        if "저압" in boiler_type:
            safe_ph_min, safe_ph_max = 11.0, 11.8; safe_po4_min, safe_po4_max = 20, 40; limit_caustic_slope = 0.01; mode_msg = "저압 표준 (High pH / Free OH 허용)"
        else:
            safe_ph_min, safe_ph_max = 9.4, 10.5; safe_po4_min, safe_po4_max = 10, 30; limit_caustic_slope = 0.025; mode_msg = "고압 표준 (Low pH / Free OH 금지)"

        with c_s2:
            fig_map = go.Figure()
            fig_map.add_shape(type="rect", x0=safe_po4_min, y0=safe_ph_min, x1=safe_po4_max, y1=safe_ph_max, line=dict(color="Green", width=2), fillcolor="rgba(0, 255, 0, 0.1)")
            x_r = np.linspace(0, 80, 100)
            base_ph = 12.2 if "저압" in boiler_type else 11.6
            fig_map.add_trace(go.Scatter(x=x_r, y=base_ph-(x_r*limit_caustic_slope), mode='lines', name='Upper Limit', line=dict(color='red', dash='dash')))
            fig_map.add_trace(go.Scatter(x=[cur_po4], y=[cur_ph], mode='markers+text', marker=dict(size=18, color="blue", symbol="x"), text=["Current"], textposition="top center", name="내 운전점"))
            fig_map.update_layout(title=f"Na-PO4 상관관계도 - [{mode_msg}]", xaxis_title="Phosphate (PO4, ppm)", yaxis_title="pH (at 25℃)", height=450, xaxis=dict(range=[0, 80]), yaxis=dict(range=[8.5, 12.5]))
            st.plotly_chart(fig_map, use_container_width=True)

        st.divider()
        st.subheader("📢 상태 진단 및 조치 가이드")
        is_ph_high = cur_ph > safe_ph_max; is_ph_low = cur_ph < safe_ph_min; is_po4_high = cur_po4 > safe_po4_max; is_po4_low = cur_po4 < safe_po4_min
        if not (is_ph_high or is_ph_low or is_po4_high or is_po4_low): st.success(f"✅ **[정상]** 현재 pH({cur_ph})와 인산염({cur_po4})은 **{boiler_type}** 기준에 완벽하게 부합합니다.")
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
# ==============================================================================
    # [추가] TAB 4: 설비 진단 및 경제성 분석 (Risk & Cost)
    # ==============================================================================
    with tab_risk:
        st.subheader("5. Risk Assessment & Engineering Guide")
        
        # [1] 사용자 혼동 방지를 위한 명확한 안내 문구 (요청사항 반영)
        st.info("""
        ℹ️ **에너지 절감의 두 가지 핵심 접근법**
        * **Tab 1 (화학적):** 고성능 약품을 사용하여 **'버리는 물의 양(Ton)'** 자체를 줄이는 방법입니다.
        * **Tab 5 (기계적):** 물리적으로 버려지는 물에서 **'폐열(Kcal)'**만 다시 회수하는 설비적 방법입니다.
        👉 **두 방법을 병행할 때 에너지 절감 효과는 극대화됩니다.**
        """)

        st.markdown("### 📊 설비 리스크 및 경제성 진단")
        
        # 데이터 로드
        res = st.session_state.get('b_res_store', {})
        val_feed = res.get('feed', 10.0)
        val_press = st.session_state.get('b_press_ex', 10.0)
        try:
            val_fe = st.session_state.b_data_feed[st.session_state.b_data_feed['Item']=='Fe (ppm)']['Feedwater'].values[0]
        except:
            val_fe = 0.05

        col_r1, col_r2 = st.columns(2)
        
        # ----------------------------------------------------------------------
        # 1. 블로우다운 열회수 진단 (Flash Steam) - Source: Ch 13
        # ----------------------------------------------------------------------
        with col_r1:
            st.markdown("#### 💰 블로우다운 열회수 진단")
            
            # 플래시 증기 발생율 간이 계산
            h_b = 100 + (val_press * 10) 
            flash_pct = min(25.0, (h_b - 100) / 539 * 100) if val_press > 0 else 0
            
            val_blow = res.get('blow', 0.0)
            flash_steam_kg = val_blow * 1000 * (flash_pct / 100)
            
            fuel_cost = st.number_input("스팀 생산 단가 (원/ton)", value=45000, step=1000)
            op_days = st.number_input("연간 가동일수 (일)", value=300)
            
            saving = (flash_steam_kg * 24 * op_days * fuel_cost) / 1000
            
            c_e1, c_e2 = st.columns(2)
            c_e1.metric("회수 가능 증기율", f"{flash_pct:.1f} %")
            c_e2.metric("시간당 회수량", f"{flash_steam_kg:.1f} kg/hr")
            
            if saving > 0:
                st.success(f"💸 **연간 예상 절감액: {saving/100000000:.2f} 억원**")
                
                # [2] 구체적인 설비 도입 제안 (요청사항 반영)
                with st.expander("🛠️ **어떤 설비를 설치해야 하나요? (제안서)**", expanded=True):
                    st.markdown(f"""
                    귀사의 운전 압력(**{val_press} bar**)에서는 다음 **2단계 시스템**을 추천합니다.
                    
                    **1. 플래시 탱크 (Flash Tank)**
                    * 고압의 블로우다운 수를 저압 탱크로 보내 **{flash_pct:.1f}%**를 스팀으로 재생산합니다.
                    * **용도:** 탈기기(Deaerator) 가열원 또는 급수탱크 예열용.
                    
                    **2. 열교환기 (Heat Exchanger)**
                    * 스팀이 되지 못하고 남은 고온수(약 100℃)를 배출 전 급수와 교차시킵니다.
                    * **용도:** 차가운 보급수(Make-up) 온도를 높여 연료비를 2차로 절감.
                    """)
            else:
                st.info("블로우다운 양이 없거나 압력이 너무 낮아 경제성이 낮습니다.")

        # ----------------------------------------------------------------------
        # 2. 기계적 리스크 (Iron Load) - Source: Ch 12
        # ----------------------------------------------------------------------
        with col_r2:
            st.markdown("#### 🏗️ 철분 침적 부하 (Iron Deposit)")
            st.caption("보일러 내부로 유입되어 튜브에 쌓이는 산화철의 총량")
            
            iron_load_kg = (val_feed * 24 * 30 * val_fe) / 1000
            limit_fe = 0.1 if val_press < 20 else 0.02
            
            c_f1, c_f2 = st.columns(2)
            c_f1.metric("현재 급수 철분", f"{val_fe:.2f} ppm")
            c_f2.metric("월간 유입량", f"{iron_load_kg:.2f} kg/month")
            
            if limit_fe > 0: risk_score = (val_fe / limit_fe) * 100
            else: risk_score = 0
            
            st.write(f"**관리 위험도 (기준 {limit_fe}ppm):** {risk_score:.0f}%")
            st.progress(min(risk_score/100, 1.0))
            
            if risk_score > 100:
                st.error("🚨 **위험:** 허용치 초과! 다공성 스케일 생성.")
                st.markdown("**👉 솔루션:** 고성능 분산제(Polymer) 적용 필수")
            else:
                st.success("✅ **안전:** 철분 유입량이 관리 기준 이내입니다.")

        st.divider()

    # ==============================================================================
    # TAB 4: 기술 매뉴얼 (기존 내용 복구 + 신규 보완 + 디자인 개선)
    # ==============================================================================
    with tab_manual:
        st.subheader("📘 Boiler Engineering Formulas & Theory")
        st.markdown("본 프로그램은 **ASME / ABMA / JIS** 보일러 관리 표준 공식을 준수합니다.")

        # ----------------------------------------------------------------------
        # [기존 내용 100% 복구] 삭제되었던 원래 매뉴얼 내용
        # ----------------------------------------------------------------------
        with st.expander("🔥 1. 보일러 물질수지 (Mass Balance) [기존]", expanded=False):
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

        with st.expander("💊 2. 약품 투입 원리 및 반응식 (Chemical Reaction) [기존]", expanded=False):
            st.markdown("#### (1) 탈산제 반응 (Oxygen Scavenger)")
            st.markdown("물속 용존 산소($O_2$)를 제거하여 부식을 방지합니다.")
            st.info("**① 아황산나트륨 ($Na_2SO_3$) - 저압용**")
            st.latex(r"2Na_2SO_3 + O_2 \rightarrow 2Na_2SO_4")
            st.caption("반응이 빠르지만 고압에서 황산염($SO_4$) 스케일 원인이 될 수 있음.")
            st.success("**② 카보하이드라자이드 ($N_4H_6CO$) - 고압/청정용**")
            st.latex(r"(N_2H_3)_2CO + 2O_2 \rightarrow 2N_2 \uparrow + 3H_2O + CO_2 \uparrow")
            st.caption("독성인 하이드라진을 대체하는 안전한 물질. 분해 시 **질소($N_2$)와 물($H_2O$)**만 남아 매우 청정합니다.")
            st.markdown("---")
            st.markdown("#### (2) 청관제 반응 (Phosphate Treatment)")
            st.info("**인산칼슘 ($Ca_3(PO_4)_2$) 생성 반응:**")
            st.latex(r"3Ca^{2+} + 2PO_4^{3-} \rightarrow Ca_3(PO_4)_2 \downarrow (\text{Sludge})")
            st.caption("딱딱한 $CaCO_3$ 스케일 대신, 배출하기 쉬운 $Ca_3(PO_4)_2$ 슬러지로 변환시킵니다.")
            st.markdown("#### (3) 응축수 처리 (Condensate Treatment)")
            st.latex(r"R-NH_2 + H_2CO_3 \rightarrow R-NH_3^+ + HCO_3^-")
            st.caption("휘발성 아민이 증기와 함께 날아가서 응축수의 pH를 8.5~9.0으로 유지시킵니다.")

        with st.expander("🔥 3. 고압 보일러 특수 이론 (Advanced Theory) [기존]", expanded=False):
            st.markdown("#### (1) 실리카의 증기 이행 (Silica Carryover)")
            st.info("고압에서 실리카($SiO_2$)는 기체처럼 변해 스팀에 녹아듭니다. (Selective Carryover)")
            st.latex(r"D = \frac{C_{steam}}{C_{boiler}} \approx 0.00005 \times P^{1.8}")
            st.caption("여기서 $D$: 분배 계수, $P$: 압력(bar). 압력이 높을수록 기하급수적으로 스팀 오염도가 증가합니다.")
            st.markdown("#### (2) 가성취화 (Caustic Embrittlement)")
            st.info("농축된 알칼리($NaOH$)가 인장 응력을 받는 철판의 입계(Grain Boundary)를 파고드는 현상입니다.")
            st.latex(r"Fe + 2NaOH \rightarrow Na_2FeO_2 + H_2 \uparrow")
            st.caption("철이 가성소다와 반응하여 녹아버리고, 수소 가스가 금속 조직을 파괴합니다.")

        # ----------------------------------------------------------------------
        # [신규 추가] 요청하신 추가 계산식 보완 (철분 부하량 & 열회수)
        # ----------------------------------------------------------------------
        with st.expander("🛠️ 4. [신규] 설비 진단 및 경제성 계산식 (Advanced Diagnosis)", expanded=True):
            st.markdown("#### (1) 블로우다운 열회수 (Flash Steam Recovery)")
            st.info("고압의 블로우다운 수가 저압으로 방출될 때 생성되는 재증발 증기량 계산")
            st.latex(r"\% \text{Flash} = \frac{H_b - H_f}{V_f} \times 100")
            st.markdown("""
            * $H_b$: 보일러 압력에서의 포화수 엔탈피 (kcal/kg)
            * $H_f$: 플래시 탱크 압력에서의 포화수 엔탈피 (kcal/kg)
            * $V_f$: 플래시 탱크 압력에서의 증발 잠열 (kcal/kg)
            """)

            st.markdown("#### (2) 철분 침적 부하량 (Iron Deposit Load)")
            st.info("급수 중 철분이 보일러 내부에 쌓이는 절대량(Mass) 계산")
            st.latex(r"\text{Load (kg/mon)} = \frac{\text{Feed} \times 24 \times 30 \times Fe_{ppm}}{1,000}")
            st.caption("철분 농도(ppm)가 낮아도 유량이 많으면 막대한 양의 스케일이 누적됨을 경고하는 공식입니다.")

        # ----------------------------------------------------------------------
        # [디자인 개선] ASME / JIS / KS 표를 예쁘게 변경 (Pandas DataFrame 적용)
        # ----------------------------------------------------------------------
        st.divider()
        st.subheader("⚖️ Global Boiler Water Quality Standards")
        st.info("💡 각 탭을 클릭하여 압력별 상세 관리 기준을 확인하십시오.")
        
        std_t1, std_t2, std_t3 = st.tabs(["🇺🇸 ASME (미국)", "🇯🇵 JIS (일본)", "🇰🇷 KS (한국)"])
        
        with std_t1:
            st.markdown("### 🇺🇸 ASME Suggested Water Chemistry (Industrial)")
            st.caption("미국기계학회 권장치 (압력 단위: MPa / psig). 보일러수(Boiler Water) 기준")
            
            asme_df = pd.DataFrame([
                {"Pressure (MPa)": "0 - 2.07", "Range (psig)": "0 - 300", "SiO2 (ppm)": "≤ 150", "Alk (ppm)": "< 700", "Cond (µS)": "1100-5400"},
                {"Pressure (MPa)": "2.08 - 3.10", "Range (psig)": "301 - 450", "SiO2 (ppm)": "≤ 90", "Alk (ppm)": "< 600", "Cond (µS)": "900-4600"},
                {"Pressure (MPa)": "3.11 - 4.14", "Range (psig)": "451 - 600", "SiO2 (ppm)": "≤ 40", "Alk (ppm)": "< 500", "Cond (µS)": "800-3800"},
                {"Pressure (MPa)": "4.15 - 5.17", "Range (psig)": "601 - 750", "SiO2 (ppm)": "≤ 30", "Alk (ppm)": "< 400", "Cond (µS)": "300-1500"},
                {"Pressure (MPa)": "5.18 - 6.21", "Range (psig)": "751 - 900", "SiO2 (ppm)": "≤ 20", "Alk (ppm)": "< 300", "Cond (µS)": "200-1200"},
                {"Pressure (MPa)": "6.22 - 6.89", "Range (psig)": "901 - 1000", "SiO2 (ppm)": "≤ 8", "Alk (ppm)": "< 200", "Cond (µS)": "200-1000"},
                {"Pressure (MPa)": "6.90 - 10.34", "Range (psig)": "1001 - 1500", "SiO2 (ppm)": "≤ 2", "Alk (ppm)": "0", "Cond (µS)": "≤ 150"},
            ])
            st.dataframe(
                asme_df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Pressure (MPa)": st.column_config.TextColumn("압력 범위 (MPa)", width="medium"),
                    "Range (psig)": st.column_config.TextColumn("압력 범위 (psig)", width="medium"),
                    "SiO2 (ppm)": st.column_config.TextColumn("실리카 (Max)", help="스케일 및 터빈 침적 방지"),
                    "Alk (ppm)": st.column_config.TextColumn("총 알칼리도 (Max)", help="기수공발 및 가성취화 방지"),
                    "Cond (µS)": st.column_config.TextColumn("전도도 (Range)", help="총 용존 고형물 관리")
                }
            )

        with std_t2:
            st.markdown("### 🇯🇵 JIS B 8223 (Water Conditioning)")
            st.caption("일본 공업 규격 (수관식 보일러). 급수/관수 구분 관리")
            
            jis_df = pd.DataFrame([
                {"Pressure": "≤ 1 MPa", "pH": "11.0-11.8", "Cond": "< 6000", "M-Alk": "< 800", "SiO2": "-"},
                {"Pressure": "1 - 2 MPa", "pH": "11.0-11.6", "Cond": "< 5000", "M-Alk": "< 600", "SiO2": "-"},
                {"Pressure": "2 - 3 MPa", "pH": "10.8-11.6", "Cond": "< 4000", "M-Alk": "< 400", "SiO2": "-"},
                {"Pressure": "3 - 5 MPa", "pH": "10.5-11.5", "Cond": "< 2500", "M-Alk": "< 250", "SiO2": "-"},
                {"Pressure": "5 - 7.5 MPa", "pH": "10.0-11.0", "Cond": "< 1500", "M-Alk": "< 130", "SiO2": "< 50"},
                {"Pressure": "7.5 - 10 MPa", "pH": "9.6-10.6", "Cond": "< 1000", "M-Alk": "< 80", "SiO2": "< 30"},
            ])
            st.dataframe(
                jis_df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Pressure": "운전 압력 (MPa)",
                    "pH": "pH (at 25℃)",
                    "Cond": "전도도 (µS/cm)",
                    "M-Alk": "M-알칼리도 (ppm)",
                    "SiO2": "실리카 (ppm)"
                }
            )

        with std_t3:
            st.markdown("### 🇰🇷 KS B 6209 (Boiler Water Quality)")
            st.caption("한국 산업 표준 (수관식 보일러). 최근 개정 사항 반영")
            
            ks_df = pd.DataFrame([
                {"Pressure": "≤ 1 MPa", "Group": "저압", "pH": "11.0-11.8", "Cond": "Max 6000", "PO4": "20-40"},
                {"Pressure": "1 - 2 MPa", "Group": "중압", "pH": "11.0-11.6", "Cond": "Max 5000", "PO4": "20-40"},
                {"Pressure": "2 - 3 MPa", "Group": "중압", "pH": "10.8-11.6", "Cond": "Max 4000", "PO4": "10-30"},
                {"Pressure": "3 - 5 MPa", "Group": "고압", "pH": "10.5-11.5", "Cond": "Max 2500", "PO4": "10-30"},
                {"Pressure": "5 - 7.5 MPa", "Group": "고압", "pH": "10.0-11.0", "Cond": "Max 1500", "PO4": "5-20"},
                {"Pressure": "7.5 - 10 MPa", "Group": "초고압", "pH": "9.6-10.6", "Cond": "Max 1000", "PO4": "2-10"},
                {"Pressure": "10 - 15 MPa", "Group": "초고압", "pH": "9.4-10.2", "Cond": "Max 500", "PO4": "2-6"},
            ])
            st.dataframe(
                ks_df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Pressure": "운전 압력 (MPa)",
                    "Group": st.column_config.TextColumn("구분", width="small"),
                    "pH": "pH (25℃)",
                    "Cond": "전도도 (µS/cm)",
                    "PO4": "인산이온 (PO4, ppm)"
                }
            )
