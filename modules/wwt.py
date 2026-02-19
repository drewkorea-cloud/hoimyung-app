import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum
from datetime import datetime

# ============================================================================
# [BACKEND ENGINE] 전문가 수질 분석 및 공정 설계 AI 엔진
# ============================================================================
class WasteWaterType(Enum):
    MUNICIPAL = "일반 하수"
    FOOD = "식품산업 폐수"
    TEXTILE = "섬유산업 폐수"
    CHEMICAL = "화학산업 폐수"
    SEMICONDUCTOR = "반도체 폐수"
    STEEL = "철강산업 폐수"
    PHARMACEUTICAL = "제약산업 폐수"
    DAIRY = "낙농폐수"
    METAL_PLATING = "금속도금 폐수"
    OIL_REFINERY = "정유 폐수"

class TreatmentProcess(Enum):
    SCREENING = "스크린(침사)"
    SEDIMENTATION = "침강(응집/응결)"
    FILTRATION = "여과"
    FLOTATION = "부상분리"
    ACTIVATED_CARBON = "활성탄흡착"
    MEMBRANE_MF = "정밀여과(MF)"
    MEMBRANE_UF = "한외여과(UF)"
    MEMBRANE_NF = "나노여과(NF)"
    MEMBRANE_RO = "역삼투(RO)"
    ACTIVATED_SLUDGE = "활성슬러지"
    TRICKLING_FILTER = "살수여상"
    SBR = "순차식 회분식 반응(SBR)"
    MEMBRANE_BIOREACTOR = "막여과 생물반응(MBR)"
    ANAEROBIC = "혐기소화"
    LAGOON = "산화지(Lagoon)"
    NITRIFICATION = "질산화"
    DENITRIFICATION = "탈질"
    COAGULATION = "응집"
    OXIDATION = "산화(염소/오존/과산화수소)"
    NEUTRALIZATION = "중화"
    PRECIPITATION = "침전(화학)"
    ION_EXCHANGE = "이온교환"
    ADSORPTION = "흡착"
    PHOTOCATALYTIC = "광촉매"
    FENTON = "펜톤 반응"

class ReusePurpose(Enum):
    RECIRCULATION = "공정용수(냉각수 순환)"
    TOILET_FLUSH = "화장실용수"
    COOLING_WATER = "냉각수(비순환)"
    IRRIGATION = "농업용수"
    GREEN_SPACE = "녹지용수"
    CLEANING = "청소용수"
    STREET_WATERING = "도로살수"
    INDUSTRIAL_USE = "산업용수"

@dataclass
class WaterQualityData:
    BOD: float
    COD: float
    SS: float
    TN: float
    TP: float
    oil: float = 0.0
    phenol: float = 0.0
    chrome: float = 0.0
    heavy_metals: float = 0.0
    turbidity: float = 0.0
    color: float = 0.0
    pH: float = 7.0
    temperature: float = 20.0
    ammonia_N: float = 0.0
    sample_date: str = ""
    location: str = ""
    wastewater_type: WasteWaterType = WasteWaterType.MUNICIPAL

# [엔진 수정] 경제성 산출 근거를 담기 위해 cost_details 및 pollution_factor 추가
@dataclass
class TreatmentSolution:
    process_sequence: List[TreatmentProcess]
    effluent_quality: WaterQualityData
    capital_cost_estimate: float
    operating_cost_estimate: float
    treatment_efficiency: Dict[str, float]
    reuse_eligible: List[ReusePurpose]
    reasoning: str
    cost_details: pd.DataFrame = None 
    pollution_factor: float = 1.0 

class WaterQualityStandards:
    DISCHARGE_LIMITS = {"BOD": 30, "COD": 40, "SS": 30, "TN": 40, "TP": 4, "pH": (6.0, 8.5)}
    REUSE_STANDARDS = {
        ReusePurpose.RECIRCULATION: {"BOD": 3, "COD": 10, "SS": 2, "TN": 10, "TP": 1, "turbidity": 1.0},
        ReusePurpose.INDUSTRIAL_USE: {"BOD": 10, "COD": 20, "SS": 5, "TN": 10, "TP": 0.5},
    }

class WaterQualityAnalyzer:
    def calculate_pollution_index(self, wq: WaterQualityData) -> float:
        bod_ratio = wq.BOD / 300 if wq.BOD > 0 else 0
        cod_ratio = wq.COD / 500 if wq.COD > 0 else 0
        ss_ratio = wq.SS / 300 if wq.SS > 0 else 0
        return min(100, (bod_ratio * 0.35 + cod_ratio * 0.35 + ss_ratio * 0.30) * 100)
    
    def classify_wastewater_strength(self, wq: WaterQualityData) -> str:
        if wq.BOD < 100: return "약한 폐수 (Weak)"
        elif wq.BOD < 300: return "중간 폐수 (Medium)"
        elif wq.BOD < 600: return "강한 폐수 (Strong)"
        else: return "매우 강한 폐수 (Very Strong)"
    
    def analyze_characteristics(self, wq: WaterQualityData) -> Dict:
        bd_ratio = wq.BOD / wq.COD if wq.COD > 0 else 0
        cn_ratio = wq.TN / wq.TP if wq.TP > 0 else 0
        if bd_ratio > 0.5: biodeg = "높음 (Highly Biodegradable)"
        elif bd_ratio > 0.3: biodeg = "중간 (Moderately Biodegradable)"
        else: biodeg = "낮음 (Poorly Biodegradable)"
        return {
            "pollution_index": self.calculate_pollution_index(wq),
            "strength_class": self.classify_wastewater_strength(wq),
            "biodegradability": biodeg,
            "bod_cod_ratio": round(bd_ratio, 3),
            "tn_tp_ratio": round(cn_ratio, 2),
            "priority_parameters": self._identify_priority_parameters(wq),
        }
    
    def _identify_priority_parameters(self, wq: WaterQualityData) -> List[str]:
        priorities = []
        if wq.BOD > 200: priorities.append(f"BOD ({wq.BOD} mg/L)")
        if wq.SS > 200: priorities.append(f"SS ({wq.SS} mg/L)")
        if wq.TN > 80: priorities.append(f"TN ({wq.TN} mg/L)")
        if wq.TP > 8: priorities.append(f"TP ({wq.TP} mg/L)")
        if wq.oil > 5: priorities.append(f"Oil ({wq.oil} mg/L)")
        return priorities if priorities else ["일반적인 오염도 수준"]

class TreatmentProcessSelector:
    def __init__(self):
        self.analyzer = WaterQualityAnalyzer()
        self.standards = WaterQualityStandards()
    
    def select_treatment_sequence(self, wq: WaterQualityData, target_effluent: Dict = None, reuse_purpose: ReusePurpose = None) -> TreatmentSolution:
        if target_effluent is None: target_effluent = self.standards.DISCHARGE_LIMITS
        process_sequence = []
        
        process_sequence.append(TreatmentProcess.SCREENING)
        if wq.SS > 100:
            if wq.BOD / wq.COD > 0.4:
                process_sequence.extend([TreatmentProcess.COAGULATION, TreatmentProcess.SEDIMENTATION])
            else: process_sequence.append(TreatmentProcess.FLOTATION)
        elif wq.SS > 50:
            process_sequence.extend([TreatmentProcess.COAGULATION, TreatmentProcess.SEDIMENTATION])
        if wq.oil > 5: process_sequence.append(TreatmentProcess.FLOTATION)
        
        bd_ratio = wq.BOD / wq.COD if wq.COD > 0 else 0
        if bd_ratio > 0.3 and wq.TN < 200:
            if wq.SS > 1000 or wq.BOD > 500: process_sequence.append(TreatmentProcess.MEMBRANE_BIOREACTOR)
            else: process_sequence.append(TreatmentProcess.ACTIVATED_SLUDGE)
        else:
            if bd_ratio < 0.2: process_sequence.append(TreatmentProcess.FENTON)
            else: process_sequence.extend([TreatmentProcess.COAGULATION, TreatmentProcess.FILTRATION])
            
        if reuse_purpose or wq.COD > 200:
            if TreatmentProcess.MEMBRANE_BIOREACTOR not in process_sequence:
                process_sequence.append(TreatmentProcess.FILTRATION)
            process_sequence.append(TreatmentProcess.ACTIVATED_CARBON)
            process_sequence.append(TreatmentProcess.MEMBRANE_RO)
            
        process_sequence = list(dict.fromkeys(process_sequence)) 
        
        # [엔진 수정] 경제성 산출 상세 데이터 받아오기
        capex, opex, cost_df, p_factor = self._estimate_costs(process_sequence, wq)
        
        return TreatmentSolution(
            process_sequence=process_sequence, effluent_quality=wq, 
            capital_cost_estimate=capex, operating_cost_estimate=opex, 
            treatment_efficiency={"BOD": 95, "COD": 90}, reuse_eligible=[], 
            reasoning="AI 엔진 최적화 완료",
            cost_details=cost_df, pollution_factor=p_factor
        )
        
    def _estimate_costs(self, processes: List[TreatmentProcess], wq: WaterQualityData) -> Tuple[float, float, pd.DataFrame, float]:
        cost_factors = {
            TreatmentProcess.SCREENING: (0.5, 0.02), TreatmentProcess.SEDIMENTATION: (2, 0.1),
            TreatmentProcess.FLOTATION: (3, 0.2), TreatmentProcess.COAGULATION: (1.5, 0.1),
            TreatmentProcess.ACTIVATED_SLUDGE: (15, 2), TreatmentProcess.MEMBRANE_BIOREACTOR: (20, 3),
            TreatmentProcess.FENTON: (10, 2), TreatmentProcess.FILTRATION: (2, 0.15),
            TreatmentProcess.ACTIVATED_CARBON: (6, 1.5), TreatmentProcess.MEMBRANE_RO: (25, 3),
        }
        capex = 0; opex = 0
        details = []
        for p in processes:
            cap, op = cost_factors.get(p, (1.0, 0.1))
            capex += cap; opex += op
            details.append({"공정명": p.value, "기준 건설비(억원)": cap, "기준 연간운영비(억원)": op})
            
        factor = max(1.0, wq.BOD / 100.0)
        df_details = pd.DataFrame(details)
        return round(capex * factor, 1), round(opex * factor, 1), df_details, round(factor, 2)

ENGINE_TO_UI_MAP = {
    TreatmentProcess.SCREENING: "Screen/EQ",
    TreatmentProcess.SEDIMENTATION: "Coagulation (화학적 응집)",
    TreatmentProcess.COAGULATION: "Coagulation (화학적 응집)",
    TreatmentProcess.FLOTATION: "DAF (가압부상)",
    TreatmentProcess.ACTIVATED_SLUDGE: "A2O (생물학적 고도처리)",
    TreatmentProcess.MEMBRANE_BIOREACTOR: "MBR (분리막 생물반응조)",
    TreatmentProcess.FENTON: "Fenton (펜톤 산화)",
    TreatmentProcess.FILTRATION: "Sand Filter (여과)",
    TreatmentProcess.ACTIVATED_CARBON: "ACF (활성탄)",
    TreatmentProcess.MEMBRANE_RO: "RO System (역삼투)"
}

# ================================================================================
# [FRONTEND UI] 기존 UI + 산출 근거 표출
# ================================================================================
def app(PRODUCT_CATALOG): 
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { height: 45px; border-radius: 5px 5px 0px 0px; font-weight: bold; }
        div[data-testid="metric-container"] { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 10px; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
        .report-box-danger { border-left: 5px solid #ff4b4b; background-color: #fff1f0; padding: 15px; border-radius: 4px; margin-bottom: 10px; }
        .report-box-success { border-left: 5px solid #28a745; background-color: #f6ffed; padding: 15px; border-radius: 4px; margin-bottom: 10px; }
        .report-title { font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
        </style>
    """, unsafe_allow_html=True)

    PROCESS_LIB = {
        "Screen/EQ": { "Removal": {"SS": 0.1, "TOC": 0.05, "COD": 0.05, "BOD": 0.05, "Oil": 0.1, "TN": 0.0, "TP": 0.0, "TDS": 0.0, "Cl": 0.0, "Silica": 0.0}, "Energy": 0.05, "Sludge_Factor": 0.0, "Desc": "협잡물 제거 및 유량 조정" },
        "pH Control (중화)": { "Removal": {"SS": 0.0, "TOC": 0.0, "COD": 0.0, "BOD": 0.0, "Oil": 0.0, "TN": 0.0, "TP": 0.0, "TDS": -0.1, "Cl": 0.0, "Silica": 0.0}, "Energy": 0.02, "Sludge_Factor": 0.05, "Desc": "산/알칼리 중화" },
        "Coagulation (화학적 응집)": { "Removal": {"SS": 0.90, "TOC": 0.35, "COD": 0.45, "BOD": 0.40, "Oil": 0.6, "TN": 0.1, "TP": 0.9, "TDS": 0.0, "Cl": 0.0, "Silica": 0.2}, "Energy": 0.1, "Sludge_Factor": 1.5, "Desc": "응집/침전" },
        "DAF (가압부상)": { "Removal": {"SS": 0.95, "TOC": 0.40, "COD": 0.5, "BOD": 0.5, "Oil": 0.95, "TN": 0.1, "TP": 0.3, "TDS": 0.0, "Cl": 0.0, "Silica": 0.1}, "Energy": 0.3, "Sludge_Factor": 1.2, "Desc": "가압부상" },
        "A2O (생물학적 고도처리)": { "Removal": {"SS": 0.8, "TOC": 0.85, "COD": 0.85, "BOD": 0.9, "Oil": 0.9, "TN": 0.8, "TP": 0.6, "TDS": 0.0, "Cl": 0.0, "Silica": 0.0}, "Energy": 0.8, "Sludge_Factor": 0.4, "Desc": "생물학적 질소/인 제거" },
        "MBR (분리막 생물반응조)": { "Removal": {"SS": 0.999, "TOC": 0.93, "COD": 0.95, "BOD": 0.98, "Oil": 0.99, "TN": 0.85, "TP": 0.7, "TDS": 0.0, "Cl": 0.0, "Silica": 0.1}, "Energy": 1.5, "Sludge_Factor": 0.3, "Desc": "MBR 시스템" },
        "Fenton (펜톤 산화)": { "Removal": {"SS": 0.2, "TOC": 0.6, "COD": 0.7, "BOD": 0.4, "Oil": 0.1, "TN": 0.1, "TP": 0.8, "TDS": 0.1, "Cl": 0.0, "Silica": 0.1}, "Energy": 0.5, "Sludge_Factor": 1.0, "Desc": "펜톤 산화" },
        "Sand Filter (여과)": { "Removal": {"SS": 0.8, "TOC": 0.1, "COD": 0.1, "BOD": 0.1, "Oil": 0.3, "TN": 0.0, "TP": 0.1, "TDS": 0.0, "Cl": 0.0, "Silica": 0.05}, "Energy": 0.1, "Sludge_Factor": 0.05, "Desc": "모래 여과" },
        "ACF (활성탄)": { "Removal": {"SS": 0.85, "TOC": 0.7, "COD": 0.7, "BOD": 0.6, "Oil": 0.9, "TN": 0.1, "TP": 0.1, "TDS": 0.0, "Cl": 0.1, "Silica": 0.0}, "Energy": 0.1, "Sludge_Factor": 0.0, "Desc": "활성탄 흡착" },
        "RO System (역삼투)": { "Removal": {"SS": 1.0, "TOC": 0.98, "COD": 0.99, "BOD": 0.99, "Oil": 1.0, "TN": 0.95, "TP": 0.99, "TDS": 0.99, "Cl": 0.99, "Silica": 0.95}, "Energy": 3.0, "Sludge_Factor": 0.0, "Desc": "역삼투 시스템" }
    }

    STD_DB = {
        "방류 (법적기준)": {"TOC": 25, "COD": 40, "SS": 10, "TN": 20, "TP": 2, "Oil": 5, "TDS": 5000, "Cl": 1000, "Silica": 100},
        "재이용 (공업용수)": {"TOC": 10, "COD": 20, "SS": 5, "TN": 10, "TP": 0.5, "Oil": 1, "TDS": 1500, "Cl": 300, "Silica": 50},
        "재이용 (RO Feed)": {"TOC": 3, "COD": 10, "SS": 1, "TN": 5, "TP": 0.1, "Oil": 0.1, "TDS": 2000, "Cl": 500, "Silica": 20}
    }

    st.title("🏭 WWT Expert System (Ver 3.0 - AI Engine Integrated)")
    st.markdown("##### **고급 오염도 분석 및 자동 공정/CAPEX 산출 엔진 탑재**")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 1. 유입부하 분석", "⚙️ 2. AI 자동설계", "🧪 3. 처리효율 시뮬레이션", "📑 4. 진단 및 투자비(CAPEX)", "💧 5. RO 연계/재이용", "📘 기술 매뉴얼"
    ])

    # ==============================================================================
    # TAB 1: 유입 폐수 성상 (산출 근거 추가)
    # ==============================================================================
    with tab1:
        st.subheader("1️⃣ 유입 폐수 성상 및 오염부하량 (Pollutant Load)")
        
        col_i1, col_i2 = st.columns([1, 2])
        with col_i1:
            st.markdown("##### **기본 운전 조건**")
            industry_type = st.selectbox("🏭 업종 (Industry)", ["정유/석유화학", "도금/표면처리", "식품/음료", "반도체/전자", "일반 하수", "화학/정밀"])
            target_use = st.selectbox("🎯 처리 목적 (Target)", list(STD_DB.keys()))
            in_flow = st.number_input("일일 유량 (m³/day)", value=1000.0, step=100.0, format="%.0f")
            in_temp = st.number_input("수온 (°C)", value=25.0); in_ph = st.number_input("pH", value=7.0)
            
        with col_i2:
            st.markdown("##### **수질 농도 입력 (Concentration, mg/L)**")
            c1, c2, c3 = st.columns(3)
            with c1: 
                conc_toc = st.number_input("TOC (총유기탄소)", value=80.0)
                conc_tn = st.number_input("T-N (총질소)", value=50.0)
                conc_oil = st.number_input("Oil & Grease", value=15.0)
                conc_cl = st.number_input("Chloride (염소)", value=400.0)
            with c2: 
                conc_cod = st.number_input("COD (유기물)", value=200.0)
                conc_tp = st.number_input("T-P (총인)", value=5.0)
                conc_tds = st.number_input("TDS (염분)", value=1500.0)
                conc_silica = st.number_input("Silica (실리카)", value=20.0)
            with c3: 
                conc_ss = st.number_input("SS (부유물질)", value=300.0)
                conc_bod = st.number_input("BOD (생분해성)", value=100.0)
                conc_alk = st.number_input("Alkalinity", value=150.0)

        load_cod = in_flow * conc_cod * 0.001; load_toc = in_flow * conc_toc * 0.001
        load_ss = in_flow * conc_ss * 0.001; load_tn = in_flow * conc_tn * 0.001
        
        st.divider()
        st.markdown("#### ⚖️ 오염 부하량 산출 결과 (Engineering Load)")
        
        # [NEW] 계산 근거를 보여주는 Expander 추가
        with st.expander("ℹ️ **부하량(Load) 산출 근거 및 공식 보기**"):
            st.markdown(r"""
            ##### **🧮 엔지니어링 계산 공식 (Standard Formula)**
            $$ \text{Load (kg/day)} = \text{Flow (m}^3\text{/day)} \times \text{Concentration (mg/L)} \times 10^{-3} $$
            
            - **단위 환산:** $1 \text{ mg/L} = 1 \text{ g/m}^3 = 0.001 \text{ kg/m}^3$ 이므로 $10^{-3}$을 곱하여 **kg** 단위로 변환합니다.
            """)
            
            cal_c1, cal_c2 = st.columns(2)
            with cal_c1:
                st.code(f"COD Load = {in_flow} (m³/d) × {conc_cod} (mg/L) ÷ 1000\n         = {load_cod:,.1f} kg/day", language='python')
                st.code(f"SS Load  = {in_flow} (m³/d) × {conc_ss} (mg/L) ÷ 1000\n         = {load_ss:,.1f} kg/day", language='python')
            with cal_c2:
                st.code(f"T-N Load = {in_flow} (m³/d) × {conc_tn} (mg/L) ÷ 1000\n         = {load_tn:,.1f} kg/day", language='python')
                st.code(f"TOC Load = {in_flow} (m³/d) × {conc_toc} (mg/L) ÷ 1000\n         = {load_toc:,.1f} kg/day", language='python')

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("COD Load", f"{load_cod:,.1f} kg/d", "유기물 총량")
        m2.metric("TOC Load", f"{load_toc:,.1f} kg/d", "총탄소량")
        m3.metric("SS Load", f"{load_ss:,.1f} kg/d", "고형물 총량")
        m4.metric("T-N Load", f"{load_tn:,.1f} kg/d", "질소 총량")

    # ==============================================================================
    # TAB 2: AI 백엔드 엔진 연동
    # ==============================================================================
    with tab2:
        st.subheader("2️⃣ AI 기반 공정 자동 설계 (Backend Engine)")
        
        industry_map = {"정유/석유화학": WasteWaterType.OIL_REFINERY, "도금/표면처리": WasteWaterType.METAL_PLATING, "식품/음료": WasteWaterType.FOOD, "반도체/전자": WasteWaterType.SEMICONDUCTOR, "일반 하수": WasteWaterType.MUNICIPAL, "화학/정밀": WasteWaterType.CHEMICAL}
        mapped_industry = industry_map.get(industry_type, WasteWaterType.MUNICIPAL)
        
        reuse_map = {"재이용 (공업용수)": ReusePurpose.INDUSTRIAL_USE, "재이용 (RO Feed)": ReusePurpose.RECIRCULATION}
        mapped_reuse = reuse_map.get(target_use, None)

        wq_input = WaterQualityData(
            BOD=conc_bod, COD=conc_cod, SS=conc_ss, TN=conc_tn, TP=conc_tp,
            oil=conc_oil, pH=in_ph, temperature=in_temp, wastewater_type=mapped_industry
        )

        selector = TreatmentProcessSelector()
        analyzer = WaterQualityAnalyzer()
        solution = selector.select_treatment_sequence(wq_input, reuse_purpose=mapped_reuse)
        characteristics = analyzer.analyze_characteristics(wq_input)
        
        st.session_state['ai_solution'] = solution

        c_ai1, c_ai2 = st.columns([1, 1])
        with c_ai1:
            st.markdown("##### 🧬 AI 수질 심층 분석")
            with st.container(border=True):
                st.metric("오염도 지수 (0~100)", f"{characteristics['pollution_index']:.1f} 점", characteristics['strength_class'])
                st.write(f"**생물분해도:** {characteristics['biodegradability']} (BOD/COD: {characteristics['bod_cod_ratio']})")
                st.write(f"**우선 처리 대상:**")
                for p in characteristics['priority_parameters']: st.caption(f"- {p}")

        recommendation_keys = []
        for proc in solution.process_sequence:
            mapped_key = ENGINE_TO_UI_MAP.get(proc)
            if mapped_key and mapped_key not in recommendation_keys:
                recommendation_keys.append(mapped_key)
        
        with c_ai2:
            st.markdown("##### ⚙️ AI 추천 최적 공정 라인업")
            with st.container(border=True):
                st.success(" ➔ ".join(recommendation_keys))
                st.caption(f"초기 건설비(CAPEX) 예상액: 약 {solution.capital_cost_estimate:,.1f} 억원 (Tab 4 참조)")

        st.markdown("---")
        selected_processes = st.multiselect("🛠️ 공정 라인 확정 (AI 추천 기반, 수정 가능)", list(PROCESS_LIB.keys()), default=recommendation_keys)

    # ==============================================================================
    # TAB 3: 처리효율 시뮬레이션
    # ==============================================================================
    with tab3:
        st.subheader("3️⃣ 처리효율 시뮬레이션 (Waterfall)")
        curr_conc = { "SS": conc_ss, "TOC": conc_toc, "COD": conc_cod, "BOD": conc_bod, "Oil": conc_oil, "TN": conc_tn, "TP": conc_tp, "TDS": conc_tds, "Cl": conc_cl, "Silica": conc_silica }
        sim_log = [{"Step": "Raw Water", **curr_conc}] 
        cum_energy = 0.0; cum_sludge = 0.0
        
        for proc_name in selected_processes:
            lib_data = PROCESS_LIB.get(proc_name, {"Removal": {}, "Energy": 0, "Sludge_Factor": 0})
            rem_rates = lib_data["Removal"]
            next_conc = {}
            for param, val in curr_conc.items():
                rate = rem_rates.get(param, 0.0)
                removed_val = val * rate
                next_conc[param] = max(val - removed_val, 0)
                if param == "SS": cum_sludge += (in_flow * removed_val * 0.001) * 1.0 
                elif param == "COD" and lib_data["Sludge_Factor"] > 0: cum_sludge += (in_flow * removed_val * 0.001) * lib_data["Sludge_Factor"]
            cum_energy += in_flow * lib_data["Energy"]
            curr_conc = next_conc
            sim_log.append({"Step": proc_name, **curr_conc})
            
        if st.button("🚀 시뮬레이션 시작", type="primary"):
            with st.spinner('엔지니어링 엔진 가동 중...'): time.sleep(0.5) 
            df_sim = pd.DataFrame(sim_log)
            st.session_state['df_sim'] = df_sim
            st.session_state['cum_energy'] = cum_energy
            st.session_state['cum_sludge'] = cum_sludge
            
            st.dataframe(df_sim.style.format({col: "{:.1f}" for col in df_sim.columns if col != "Step"}), use_container_width=True)
            
            fig = go.Figure()
            colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA']
            for i, param in enumerate(["COD", "TOC", "SS", "TDS"]): 
                fig.add_trace(go.Scatter(x=df_sim["Step"], y=df_sim[param], mode='lines+markers', name=param, line=dict(width=3, color=colors[i]), marker=dict(size=8)))
            fig.update_layout(title="공정별 수질 변화 추이", template="plotly_white", hovermode="x unified", height=450)
            st.plotly_chart(fig, use_container_width=True)

    # ==============================================================================
    # TAB 4: 종합 진단 및 투자/운영비 (CAPEX 산출 근거 추가)
    # ==============================================================================
    with tab4:
        st.subheader("4️⃣ 종합 진단 및 투자/운영비 (CAPEX & OPEX)")
        
        if 'df_sim' not in st.session_state:
            st.warning("⚠️ 먼저 Tab 3에서 '시뮬레이션'을 실행해주세요.")
        else:
            final_eff = st.session_state['df_sim'].iloc[-1]
            target_std = STD_DB[target_use]
            
            score = 100; fail_items = {}
            st.markdown("##### **1. 규제 기준 준수 현황**")
            cols = st.columns(4)
            idx = 0
            for param, limit in target_std.items():
                val = final_eff.get(param, 0)
                is_pass = val <= limit
                if not is_pass: score -= 15; fail_items[param] = val
                with cols[idx % 4]: st.metric(label=param, value=f"{val:.1f}", delta=f"기준 {limit}", delta_color="normal" if is_pass else "inverse")
                idx += 1
            st.divider()

            st.markdown("##### **2. 엔진 솔루션 (Prescription)**")
            if not fail_items:
                st.markdown("""<div class="report-box-success"><div class="report-title">✅ 시스템 설계 적합 (System Validated)</div>모든 수질 항목이 목표 기준을 만족합니다. 현재 설계를 유지하십시오.</div>""", unsafe_allow_html=True)
            else:
                for param, val in fail_items.items():
                    solution_text = ""
                    if param in ["SS", "TP"]: solution_text = "👉 **[처방]** 물리적 침전 효율 부족. **여과(Sand Filter)** 추가 필요."
                    elif param in ["COD", "BOD", "TOC"]: solution_text = "👉 **[처방]** 생물학적 처리 용량 초과. **펜톤/활성탄** 공정 보강 필요."
                    elif param == "TN": solution_text = "👉 **[처방]** 탈질 효율 저하. **외부탄소원(메탄올)** 투입 조정."
                    elif param in ["TDS", "Cl", "Silica"]: solution_text = "👉 **[처방]** 이온성 물질 잔류. **RO System** 도입 필수."
                    st.markdown(f"""<div class="report-box-danger"><div class="report-title">🚨 {param} 기준 초과 (Current: {val:.1f} / Limit: {target_std[param]})</div>{solution_text}</div>""", unsafe_allow_html=True)

            st.markdown("##### **3. AI 예측 경제성 평가 (CAPEX & OPEX)**")
            cost_elec = 120; cost_sludge = 150; cost_chem = st.session_state['cum_energy'] * 20
            daily_opex = (st.session_state['cum_energy'] * cost_elec) + (st.session_state['cum_sludge'] * cost_sludge) + cost_chem
            
            capex_val = st.session_state.get('ai_solution', None)
            capex_str = f"{capex_val.capital_cost_estimate:,.1f} 억원" if capex_val else "계산 불가"

            c1, c2, c3 = st.columns(3)
            c1.metric("🏗️ 초기 건설비 (CAPEX)", capex_str, "AI 엔진 추산")
            c2.metric("💰 일일 운영비 (OPEX)", f"{int(daily_opex):,} 원/일", "전력+슬러지+약품")
            c3.metric("♻️ 연간 운영비 (300일)", f"{int(daily_opex * 300 / 100000000):.2f} 억원/년")
            
            # [NEW] AI 경제성 평가 산출 근거 표출
            if capex_val and capex_val.cost_details is not None:
                with st.expander("ℹ️ **AI 건설비/운영비(CAPEX) 산출 근거 상세내역**", expanded=True):
                    st.markdown("**1) 선택된 공정별 기본 단가표 (처리량 1,000 ㎥/일, 표준 하수 기준)**")
                    st.dataframe(capex_val.cost_details, hide_index=True, use_container_width=True)
                    
                    base_cap = capex_val.cost_details['기준 건설비(억원)'].sum()
                    base_op = capex_val.cost_details['기준 연간운영비(억원)'].sum()
                    p_factor = capex_val.pollution_factor
                    
                    st.markdown("**2) 오염도 가중치 (Pollution Factor) 적용**")
                    st.info(f"💡 현재 유입수의 **BOD({wq_input.BOD} mg/L)**가 표준 설계 기준인 하수(100 mg/L) 대비 **{p_factor}배** 높게 설정되어 있습니다. 따라서 설비 용량 증대 및 부대 설비 확장을 고려하여 **모든 비용에 가중치 {p_factor}가 곱해집니다.**")
                    
                    st.latex(rf"\text{{최종 CAPEX (건설비)}} = {base_cap:.1f} \times {p_factor} = \mathbf{{{capex_val.capital_cost_estimate:,.1f} \text{{ 억원}}}}")
                    st.latex(rf"\text{{최종 OPEX (운영비)}} = {base_op:.1f} \times {p_factor} = \mathbf{{{capex_val.operating_cost_estimate:,.1f} \text{{ 억원/년}}}}")

    # ==============================================================================
    # TAB 5 & 6
    # ==============================================================================
    with tab5:
        st.subheader("💧 5. RO 시스템 연계 적합성 판정")
        if 'df_sim' not in st.session_state: st.info("Tab 3에서 시뮬레이션 버튼을 먼저 눌러주세요.")
        else:
            ro_feed = st.session_state['df_sim'].iloc[-1]; limit_ro = STD_DB["재이용 (RO Feed)"]; ro_ready = True
            c_ro1, c_ro2 = st.columns(2)
            with c_ro1:
                st.markdown("##### 🔍 막 오염(Fouling) 리스크 진단")
                if ro_feed.get("SS", 0) > limit_ro["SS"]: st.error(f"❌ **SS:** 막 막힘 위험. UF 필수."); ro_ready = False
                else: st.success(f"✅ **SS:** 양호")
                if ro_feed.get("Oil", 0) > limit_ro["Oil"]: st.error(f"❌ **Oil:** 유분 오염 위험. DAF 필수."); ro_ready = False
                else: st.success(f"✅ **Oil:** 양호")
                if ro_feed.get("Silica", 0) > limit_ro["Silica"]: st.warning(f"⚠️ **Silica:** 스케일 위험. 방지제 필수.")
                else: st.success(f"✅ **Silica:** 양호")
            with c_ro2:
                st.markdown("##### 📊 RO 성능 예측")
                if ro_ready:
                    est_rec = 75.0; est_perm_tds = ro_feed.get("TDS", 0) * 0.02
                    st.info(f"**✅ RO 운전 가능**\n- 예상 회수율: **{est_rec}%**\n- 예상 처리수 TDS: **{est_perm_tds:.1f} mg/L**")
                else: st.warning("⚠️ **RO 유입 불가!** 전처리 공정을 강화하십시오.")

    with tab6:
        st.subheader("📘 Wastewater Treatment Engineering Manual")
        with st.expander("🦠 1. 생물학적 처리 핵심 지표", expanded=True):
            st.markdown("#### F/M 비 (Food to Microorganism Ratio)")
            st.latex(r"F/M = \frac{Q \times BOD}{V \times MLSS}")
            st.write("- **표준:** 0.2 ~ 0.4 / **MBR:** 0.05 ~ 0.15")