import math
import numpy as np
from datetime import date, timedelta

# 전도도(Cond, µS/cm) → TDS(mg/L) 변환 계수.
# 모든 모듈(cooling/RO)이 이 상수 하나만 참조하도록 통일해 모듈 간 계산 결과가 어긋나지 않게 한다.
COND_TO_TDS_FACTOR = 0.65

# [New Logic] 알칼리도(M-Alk) 기반 pH 예측 알고리즘 (수온 보정 포함)
def predict_ph_from_alkalinity(m_alk, temp_c=25.0):
    alk_points = [0,  20,  50,  100, 150, 200, 300, 400, 500, 600, 800, 1000]
    ph_points  = [7.0, 7.2, 7.6, 8.0, 8.2, 8.3, 8.5, 8.7, 8.8, 8.9, 9.0, 9.1]
    if m_alk <= 0: return 7.0
    base_ph = np.interp(m_alk, alk_points, ph_points)
    # 25도 기준 대비 수온 1도 상승마다 pH 약 0.011 하락 (ro_concentration과 동일한 보정식)
    temp_correction = 0.011 * (temp_c - 25.0)
    return float(base_ph - temp_correction)

# [AI Deep Logic] 제안서 기반 맞춤형 진단 알고리즘 (Cooling)
def get_cooling_deep_audit(lsi, rsi, cl_ion, so4, alk, ca_h, temp, holding_time, target_cl2, ph, 
                           measured_bacteria=0, srb_detected=False, measured_ph=0.0):
    report = []
    # 1. [Microbial Review]
    report.append("#### 1. 🦠 미생물 측정 및 살균 프로그램 진단")
    bio_risk = False
    if measured_bacteria > 10000:
        report.append(f"🚨 **[미생물 오염 심각]** 일반세균수가 **{measured_bacteria:,} CFU/mL**로 관리 기준(10,000)을 초과했습니다.")
        report.append(f"✅ **[처방]** 슬라임 박리제(Bio-dispersant) 투입과 비산화성 살균제 **'충격 투입(Shock Dosing)'** 주기를 단축하십시오.")
        bio_risk = True
    elif srb_detected:
        report.append(f"🧱 **[SRB(황산염환원균) 검출]** 배관 부식의 주원인인 SRB가 검출되었습니다.")
        report.append(f"✅ **[처방]** SRB에 특화된 **'Isothiazoline'** 또는 **'Glutaraldehyde'** 계열 살균제를 즉시 처방하십시오.")
    else:
        report.append(f"✅ **[양호]** 미생물 상태가 관리 범위 이내입니다. 현재의 교차 투입(Dual Biocide) 프로그램을 유지하십시오.")

    # 2. [Water Quality Review]
    if measured_ph > 0:
        report.append("#### 2. 🔎 수질 데이터 Review (실측 vs 시뮬레이션)")
        diff = measured_ph - ph
        if abs(diff) > 0.5:
             report.append(f"⚠️ **[pH 편차 발생]** 실측 pH({measured_ph})와 시뮬레이션 목표 pH({ph})의 차이가 큽니다.")
             if measured_ph > ph:
                 report.append(f"💡 **[진단]** 농축이 예상보다 높거나, 외부 알칼리 유입이 의심됩니다. **'전도도 제어(Bleed-off)'** 설정을 점검하십시오.")
        else:
             report.append(f"✅ **[일치]** 실측 수질이 설계 범위 내에서 안정적으로 유지되고 있습니다.")
    
    # 3. 체류시간
    report.append("#### 1. ⏱️ 체류시간(HT)과 약품의 수명(Life-cycle)")
    if holding_time > 48:
        report.append(f"🐢 **[장기 체류 경고]** 현재 체류시간은 **{holding_time:.1f}시간**입니다. 물이 시스템 내에 48시간 이상 머무르면 약품의 화학적 구조가 깨지기 시작합니다.")
        report.append(f"⛔ **[HEDP 선정 금지]** 일반적인 **'HEDP'** 성분은 장시간 체류 시 가수분해(Hydrolysis)되어 **'정인산(Ortho-phosphate)'**으로 변질됩니다. 변질된 인산은 칼슘과 결합해 **'인산칼슘 스케일'**을 유발하므로 오히려 독이 됩니다.")
        report.append(f"✅ **[필수 성분]** 시간이 지나도 구조가 유지되는 **'PBTC'** 또는 **'PMA / AA / AMPS'** 계열의 고성능 폴리머가 주성분인 제품을 선정하십시오.")
    elif holding_time < 10:
        report.append(f"💸 **[단기 체류 주의]** 체류시간이 **{holding_time:.1f}시간**으로 매우 짧습니다. 약품이 효과를 보기도 전에 배수(Blowdown)로 버려지고 있습니다.")
        report.append(f"💡 **[운전 전략]** 고가(High-End)의 약품을 연속 주입하는 것은 비경제적입니다. 가성비가 좋은 표준 약품을 타이머로 **'충격 투입(Shock Dosing)'** 하여 순간 농도를 높이거나, 농축 배수를 올려 체류시간을 확보하십시오.")
    else:
        report.append(f"✅ **[안정적]** 체류시간({holding_time:.1f}hr)이 약품 효율 최적 구간(24~48hr)입니다. 표준적인 **'HEDP/PBTC 복합제'**를 선정하셔도 무방합니다.")

    # 4. LSI
    report.append("#### 2. ⚖️ LSI 스케일 강도별 최적 성분 배합")
    if lsi > 2.5:
        report.append(f"🔴 **[초고부하 스케일 (LSI {lsi:.2f})]** 탄산칼슘 포화도가 한계치를 넘어, 물속에서 결정(Crystal)이 폭발적으로 성장하려는 상태입니다.")
        report.append(f"✅ **[고성능 분산제 필수]** 일반 인산염(Phosphonate)의 '임계 효과(Threshold Effect)'만으로는 부족합니다. 결정의 모양을 찌그러뜨려 성장을 멈추게 하는 **'Terpolymer(3원 공중합체)'**나 **'HPA'** 성분이 고농도로 함유된 제품이 아니면 배관이 막힙니다.")
    elif lsi < 0:
        report.append(f"🔵 **[부식성 수질 (LSI {lsi:.2f})]** 물이 미포화 상태라 배관의 금속 성분($Fe, Cu$)을 녹여내려 하고 있습니다. 스케일 방지보다는 부식 억제가 급선무입니다.")
        report.append(f"✅ **[방식제 우선 선정]** 금속 표면에 보호막을 입히는 **'아연(Zinc)'** 또는 **'고농도 정인산(High Phosphate)'** 베이스의 제품을 선정하십시오.")
        if ph > 8.3:
             report.append(f"⚠️ **[Zn 사용 주의]** 단, pH 8.3 이상에서는 아연 자체가 **'수산화아연 슬러지'**가 되어 침전됩니다. 아연 제품을 쓰려면 **'산(Acid)'**을 병행하여 pH를 8.0 이하로 유지하거나, **'유기인계(All-Organic)'** 고농도 처리를 고려하십시오.")
    else:
        report.append(f"✅ **[표준 관리 범위]** LSI({lsi:.2f})가 적정합니다. 경제성을 고려하여 **'Phosphonate(인산염) + Polymer'**의 표준 스케일 방지제를 선정하십시오.")

    # 5. 특수 수질
    report.append("#### 3. 🧪 잔류염소 및 특수 이온 대응")
    if target_cl2 >= 0.5:
        report.append(f"🔥 **[산화제 과다 (Cl2 {target_cl2}ppm)]** 살균력을 높이기 위해 염소 농도를 높게 유지하는 현장입니다.")
        report.append(f"⛔ **[HEDP 사용 불가]** HEDP 분자는 염소(산화제)를 만나면 C-P 결합이 끊어져 분해됩니다. 약품 농도를 유지할 수 없습니다.")
        report.append(f"✅ **[내염소성 성분]** 염소 공격에도 구조가 파괴되지 않는 **'PBTC'** 성분이 베이스인 제품을 선정해야만 스케일 방지 효과를 볼 수 있습니다.")
    
    if so4 > 1000:
        report.append(f"🧱 **[황산염 스케일 위험]** 황산이온({so4}ppm)이 높아 탄산칼슘보다 10배 더 단단한 **'석고(Gypsum)'** 스케일이 생성될 수 있습니다.")
        report.append(f"✅ **[전용 분산제]** 일반 폴리머로는 제어가 어렵습니다. 황산염 스케일에 특화된 **'Copolymer (AA/AMPS)'** 성분이 보강된 제품인지 반드시 확인하십시오.")
        
    if cl_ion > 300:
        report.append(f"⚠️ **[공식(Pitting) 경고]** 염소이온({cl_ion}ppm)은 스테인리스와 동관의 보호피막을 국소적으로 뚫어버립니다.")
        report.append(f"✅ **[아졸 강화]** 구리/동관 부식 방지제인 **'Azole (BZT/TT)'** 성분이 일반 제품보다 고농도(2ppm 유지 가능)로 배합된 제품을 선택하십시오.")

    return report

# [AI Deep Logic] 보일러 심층 진단 알고리즘
def get_boiler_deep_audit(pressure, hardness, cond_ph, tds, iron, silica):
    report = []
    report.append("#### 1. 🔥 운전 압력에 따른 탈산제(Oxygen Scavenger) 선정")
    if pressure < 20:
        report.append(f"✅ **[저압 보일러 ({pressure}bar)]** 반응 속도가 빠른 **'Sulfite(아황산나트륨)'** 계열이 가장 경제적이고 효과적입니다.")
    elif pressure >= 40:
        report.append(f"🚨 **[고압 주의 ({pressure}bar)]** 고압에서 아황산염(Sulfite)을 쓰면 분해되어 $SO_2, H_2S$ 부식 가스를 만듭니다.")
        report.append(f"⛔ **[Sulfite 금지]** 반드시 고형분이 남지 않는 **'Hydrazine'** 대체재(DEHA, Carbohydrazide)나 **'All-Volatile'** 약품을 선정하십시오.")
    else:
        report.append(f"⚠️ **[중압 보일러 ({pressure}bar)]** Sulfite 사용이 가능하나, TDS 관리가 중요합니다. 가급적 **'유기 탈산제(DEHA)'** 사용을 권장합니다.")

    report.append("#### 2. 🧱 경도 누출(Leak) 대응 및 스케일 제어")
    if hardness > 0.5:
        report.append(f"🚨 **[경도 누출 경고]** 급수 경도가 **{hardness}ppm**으로 감지됩니다. 연수장치 파과(Breakthrough)가 의심됩니다.")
        report.append(f"✅ **[필수 처방]** 튜브 파열을 막으려면, 경도 성분을 진흙(Sludge)으로 만들어 배출시키는 **'PO4(인산염) + Polymer'** 복합 청관제를 과량 투입해야 합니다.")
    else:
        report.append(f"✅ **[수질 양호]** 경도 누출이 없습니다. 청관 효율을 높이기 위해 **'All-Polymer(분산제 전용)'** 또는 **'Phosphate'** 프로그램을 표준대로 유지하십시오.")

    report.append("#### 3. 💧 응축수 회수 라인 부식 진단")
    if cond_ph < 7.5:
        report.append(f"🔥 **[산성 부식 위험]** 응축수 pH가 **{cond_ph}**로 낮습니다. 탄산($CO_2$) 가스에 의해 배관이 녹아 **'철분({iron}ppm)'**이 보일러로 유입되고 있습니다.")
        report.append(f"✅ **[필수 처방]** 증기와 함께 날아가서 배관 끝단까지 pH를 높여주는 **'중화 아민(Neutralizing Amine)'** 투입이 시급합니다.")
    else:
        report.append(f"✅ **[양호]** 응축수 pH({cond_ph})가 적절하게 유지되어 배관 부식 위험이 낮습니다.")
    return report

# [AI Deep Logic] RO(역삼투) 심층 진단 알고리즘
def get_ro_deep_audit(lsi_brine, silica_brine, sdi, recovery, ph_brine):
    report = []
    report.append("#### 1. ⚖️ LSI 농축수 스케일 강도 진단")
    if lsi_brine > 2.0:
        report.append(f"🔴 **[강한 스케일 (LSI {lsi_brine:.2f})]** 산(Acid) 주입만으로는 막힘을 막을 수 없습니다.")
        report.append(f"✅ **[필수 처방]** 탄산칼슘 결정 성장을 억제하는 **'High-Performance Antiscalant (Dendritic Polymer)'** 제품을 선정하십시오.")
    elif lsi_brine > 1.0:
        report.append(f"⚠️ **[스케일 주의 (LSI {lsi_brine:.2f})]** 일반적인 **'Phosphonate(인산염)'** 계열 스케일 방지제 사용이 필요합니다.")
    else:
        report.append(f"✅ **[안정]** LSI({lsi_brine:.2f})가 낮아 스케일 위험이 적습니다. 소량의 방지제로도 운전 가능합니다.")

    report.append("#### 2. 💎 실리카(Silica) 스케일 위험성")
    if silica_brine > 150:
        report.append(f"🚨 **[실리카 경고]** 농축수 실리카가 **{silica_brine:.1f}ppm**입니다. (용해도 한계 120ppm 초과)")
        report.append(f"⛔ **[일반 약품 금지]** 일반 스케일 방지제는 실리카를 막지 못합니다. 반드시 **'Silica-Specific Dispersant'**가 함유된 전용 약품을 써야 합니다.")
        report.append(f"💡 **[운전 팁]** 약품으로 한계가 있다면 **'회수율(Recovery)'**을 {recovery}%보다 낮춰 실리카 농도를 떨어뜨려야 합니다.")
    else:
        report.append(f"✅ **[양호]** 실리카 농도({silica_brine:.1f}ppm)가 용해도 범위 이내입니다.")

    report.append("#### 3. 🌫️ 전처리(Pre-treatment) 효율 진단")
    if sdi > 4.0:
        report.append(f"🔥 **[파울링 경고]** SDI가 **{sdi}**로 높습니다. 멤브레인 표면에 진흙/입자가 쌓이고 있습니다.")
        report.append(f"✅ **[처방]** 스케일 방지제 외에, 전단에 **'응집제(Coagulant)'** 투입을 검토하거나 마이크로필터(MF) 교체 주기를 확인하십시오.")
    return report

# L.S.I 계산 함수
def calculate_lsi(ph, tds, ca, alk, temp):
    try:
        ph, tds, temp = float(ph), float(tds), float(temp)
        ca, alk = float(ca), float(alk)
        if ca <= 0: ca = 1.0
        if alk <= 0: alk = 1.0
        if tds <= 0: tds = 1.0
        a = (math.log10(tds) - 1) / 10
        b = -13.12 * math.log10(temp + 273.15) + 34.55
        c = math.log10(ca) - 0.4
        d = math.log10(alk)
        phs = (9.3 + a + b) - (c + d)
        return ph - phs
    except (ValueError, TypeError):
        return 0.0

# [엔진 2] 보일러 전문가 엔진 (안토인 식 적용 Ver)
class Boiler_Expert_Engine:
    @staticmethod
    def get_steam_enthalpy(pressure_bar):
        try:
            P_bar = max(pressure_bar, 0.1)
            P_mmHg = P_bar * 750.062
            if P_bar >= 1.013: 
                A, B, C = 8.14019, 1810.94, 244.485
            else:
                A, B, C = 8.07131, 1730.63, 233.426
            val = A - math.log10(P_mmHg)
            ts = (B / val) - C
            h_steam = 665 + 0.3 * ts    
            return round(ts, 1), round(h_steam, 1)
        except Exception as e:
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
        if tds > limit_tds: msgs.append(f"🔴 전도도 초과 (기준 {limit_tds})")
        if silica > limit_sio2: msgs.append(f"🔴 실리카 초과 (기준 {limit_sio2})")
        if alk > limit_alk: msgs.append(f"⚠️ 알칼리도 높음 (기준 {limit_alk})")
        
        if not msgs: return "✅ ASME 기준 만족 (Safe)", limit_tds
        else: return ", ".join(msgs), limit_tds

# --------------------------------------------------------------------------
# [RO 전용 계산 엔진 추가 섹션]
# --------------------------------------------------------------------------

# 1️⃣ Ion Balance 계산 함수
def ion_balance(val_ca, val_mg, val_na, val_k, val_alk, val_cl, val_so4):
    meq_ca = val_ca / 20.04
    meq_mg = val_mg / 12.15
    meq_na = val_na / 22.99
    meq_k  = val_k  / 39.10
    meq_alk = val_alk / 50.0
    meq_cl = val_cl / 35.45
    meq_so4 = val_so4 / 48.03

    sum_cat = meq_ca + meq_mg + meq_na + meq_k
    sum_an = meq_alk + meq_cl + meq_so4

    balance_gap = sum_an - sum_cat

    return {
        "balance_gap": balance_gap,
        "sum_cation": sum_cat,
        "sum_anion": sum_an
    }

# ------------------------------
# 2️⃣ RO Concentration (수온 & 이온강도 정밀 보정 버전)
# ------------------------------
def ro_concentration(in_rec, in_ph, in_temp, ion_dict):
    """
    수온(Temp)과 이온강도(Ionic Strength)를 동시에 고려하여 농축수 pH를 정밀 예측합니다.
    """
    cf = 1 / (1 - (in_rec / 100))
    
    # 1. TDS 및 이온강도 계산
    feed_tds = sum([v for k,v in ion_dict.items() if k != 'pH'])
    brine_tds = feed_tds * cf
    ionic_strength = 2.5e-5 * brine_tds
    
    # 2. 활동도 보정 (Debye-Hückel)
    activity_corr = (0.509 * math.sqrt(ionic_strength)) / (1 + 1.6 * math.sqrt(ionic_strength))
    
    # 3. [신규] 수온 보정 로직 (Temperature Correction)
    # 표준 25도 대비 온도가 1도 오를 때마다 pH가 약 0.011 하락하는 중탄산염 평형 특성 반영
    temp_deviation = 0.011 * (in_temp - 25.0)
    
    # 4. 최종 정밀 pH 산출
    ph_buffer_index = 0.65 + (activity_corr * 0.5) 
    # 기본 농축 상승분 + 이온강도 보정 - 수온 편차
    brine_ph = in_ph + (math.log10(cf) * ph_buffer_index) - temp_deviation
    
    if brine_ph > 9.2: brine_ph = 9.2

    return {
        "cf": cf,
        "feed_tds": feed_tds,
        "brine_tds": brine_tds,
        "brine_ph": round(brine_ph, 2)
    }
# 3️⃣ Osmotic Pressure & NDP 계산 함수
def osmotic_pressure(v_main, temp, recovery, op_press, perm_press):
    temp_k = temp + 273.15
    r = 0.08206
    mw_db = { 'Ca': 40.08, 'Mg': 24.305, 'Na': 22.99, 'Cl': 35.45, 'SO4': 96.06 }
    feed_molarity = 0.0
    for ion, conc in v_main.items():
        if ion in mw_db:
            feed_molarity += (conc / 1000.0) / mw_db[ion]

    cf = 1 / (1 - (recovery / 100))
    brine_molarity = feed_molarity * cf
    avg_bulk = (feed_molarity + brine_molarity) / 2.0

    osmotic_atm = avg_bulk * r * temp_k
    osmotic_bar = osmotic_atm * 1.01325
    ndp = op_press - osmotic_bar - 2.0 - perm_press

    return {
        "osmotic_bar": osmotic_bar,
        "ndp": ndp
    }

# 4️⃣ RO 전용 LSI 계산 함수 (개별 인자 수신형)
# [의도된 차이] 일반 calculate_lsi()와 달리 b_ca*2.5, b_alk*0.82 보정이 들어간다.
# RO 농축수(brine)는 일반 냉각수보다 이온강도가 훨씬 높아, 실제 활동도(activity)가
# 표준 LSI 공식이 가정하는 저농도 수질보다 낮게 작동하는 것을 근사적으로 보정하기 위함.
# 저농도 계에는 calculate_lsi(), 고농축 RO 농축수에는 이 함수를 쓴다.
def calculate_ro_lsi(b_ca, b_alk, b_tds, temp, brine_ph):
    t_k = temp + 273.15
    f_a = (math.log10(b_tds) - 1) / 10.0 if b_tds > 10 else 0
    f_b = -13.12 * math.log10(t_k) + 34.55
    f_c = math.log10(b_ca * 2.5) - 0.4 if b_ca > 1 else 0
    f_d = math.log10(b_alk * 0.82) if b_alk > 1 else 0
    ph_s = (9.3 + f_a + f_b) - (f_c + f_d)
    lsi = brine_ph - ph_s
    return lsi
# ------------------------------------------------------------
# 🎯 WWT(폐수처리) 엔지니어링 계산 엔진
# ------------------------------------------------------------

def calc_carbon_source(tn_to_remove, toc_available):
    """
    4️⃣ 탈질 탄소원 부족분 계산
    이론적 C/N비 3.0~4.0 기준
    """
    req_toc = tn_to_remove * 3.5  # 필요 TOC량
    shortage = max(0, req_toc - toc_available)
    # 메탄올 환산 (TOC 대 메탄올 비 약 0.375)
    methanol_kg = shortage / 0.375
    return round(shortage, 1), round(methanol_kg, 1)

# ------------------------------------------------------------
# 🎯 WWT(폐수처리) 엔지니어링 고도화 엔진 (집대성본)
# ------------------------------------------------------------

def calc_biological_metrics(flow, toc_in, v_tank, mlss):
    """1️⃣ 생물학적 처리 진단 (F/M비 및 용적부하)"""
    if v_tank <= 0 or mlss <= 0: return 0.0, 0.0
    load_toc = flow * toc_in * 0.001
    fm_ratio = load_toc / (v_tank * mlss * 0.001)
    vol_load = load_toc / v_tank
    return round(fm_ratio, 3), round(vol_load, 3)

def calc_chemical_dosage(flow, dose_ppm, sg=1.2):
    """2️⃣ 화학적 응집제/중화제 소요량 계산"""
    weight_kg = (flow * dose_ppm) / 1000.0
    volume_l = weight_kg / sg if sg > 0 else weight_kg
    return round(weight_kg, 1), round(volume_l, 1)

def calc_sludge_production(flow, ss_in, ss_out, cod_rem, yield_factor=0.4, water_content=0.8):
    """3️⃣ 슬러지 발생량 및 탈수 케이크 예측"""
    ss_removed = (ss_in - ss_out) * flow * 0.001
    bio_produced = (cod_rem * flow * 0.001) * yield_factor
    total_dry_sludge = ss_removed + bio_produced
    cake_amount = (total_dry_sludge / (1 - water_content)) / 1000.0
    return round(total_dry_sludge, 1), round(cake_amount, 2)

def estimate_wwt_sdi(ss_conc, turbidity):
    """4️⃣ RO 재이용을 위한 SDI 추산식"""
    sdi_est = (ss_conc * 0.5) + (turbidity * 0.3) + 1.0
    return round(min(sdi_est, 6.6), 1)

def calc_alkalinity_requirement(nh3_rem):
    """5️⃣ 질질화 소모 알칼리도 계산 (기준: 7.14)"""
    return round(nh3_rem * 7.14, 2)

def calc_sedimentation_stokes(particle_dia, particle_rho, water_temp):
    """6️⃣ Stoke's Law 침전 속도 계산"""
    viscosity = 0.00131 / (1 + 0.0337 * water_temp + 0.00022 * water_temp**2)
    g = 9.81
    rho_w = 1000
    vs = (g * (particle_rho - rho_w) * (particle_dia**2)) / (18 * viscosity)
    return round(vs * 3600, 4)

def calc_ro_osmotic_pressure(tds_mg_l, temp_c):
    """7️⃣ 삼투압 계산 (van't Hoff)"""
    pi = (tds_mg_l / 1000) * 0.7 * ((temp_c + 273) / 298)
    return round(pi, 2)

def calc_oxygen_and_air(flow, bod_rem, tn_rem):
    """8️⃣ 소요 산소 및 풍량 계산 (AOR/SOR)"""
    aor = (flow * (1.1 * bod_rem + 4.6 * tn_rem)) / 1000.0
    air_flow = aor / (0.232 * 1.293 * 60 * 0.15)
    return {"aor": round(aor, 2), "air_flow": round(air_flow, 2)}

def calc_total_opex_detail(flow, kwh_per_m3, chem_per_m3, sludge_per_m3):
    """9️⃣ 운영비 상세 산출"""
    cost_m3 = (kwh_per_m3 * 100) + chem_per_m3 + sludge_per_m3
    daily_total = flow * 24 * cost_m3
    return {"cost_per_m3": round(cost_m3, 1), "daily_total": int(daily_total)}
# --- wwt.py의 66행 에러를 해결하기 위한 핵심 함수 ---
def get_wwt_engineering_indices(bod, cod, ss, tn, tp):
    """
    BOD, COD, SS, TN, TP 데이터를 받아 
    생분해성(bc_ratio)과 영양소 비율(n_ratio, p_ratio)을 계산합니다.
    """
    bc_ratio = bod / cod if cod > 0 else 0
    n_ratio = (tn / bod * 100) if bod > 0 else 0
    p_ratio = (tp / bod * 100) if bod > 0 else 0
    return {
        "bc_ratio": round(bc_ratio, 2),
        "n_ratio": round(n_ratio, 1),
        "p_ratio": round(p_ratio, 1)
    }