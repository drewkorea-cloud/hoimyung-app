import streamlit as st
import os
import sys

# 모듈 Import (경로 설정 필요시 sys.path.append 사용 가능)
from utils.data_loader import load_data_master
from utils.styles import get_css
from modules import cooling, boiler, ro, wwt, engineering, chemical

# 1. 페이지 설정 (최상단 필수)
st.set_page_config(page_title="Water Master Pro", page_icon="logo.png", layout="wide")

# 2. 전역 변수 로드
PRODUCT_CATALOG, df_master = load_data_master()

# 3. 스타일 적용
st.markdown(get_css(), unsafe_allow_html=True)

# 4. 로그인 로직
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("### 🔒 관계자 외 출입금지")
    password_input = st.text_input("접속 비밀번호를 입력하세요:", type="password")
    if st.button("로그인"):
        if password_input == "1234":  
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ 비밀번호가 틀렸습니다. 다시 시도하세요.")
    st.stop()

# 5. 사이드바 메뉴
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
        st.markdown("### **Water Master Pro**") 
    else:
        st.title("💧 HOIMYUNG WATERZEN")
        st.subheader("Water Master Pro")
    
    # 세션스테이트에 메뉴 저장 (RO 탭에서 자동이동 기능 지원을 위해)
    if 'main_menu_mode' not in st.session_state:
        st.session_state.main_menu_mode = "1. Cooling Calc."

    program_mode = st.radio(
        "Select Module:", 
        [
            "1. Cooling Calc.", 
            "2. Boiler Calc.", 
            "3. RO Calc.", 
            "4. WWT Calc.", 
            "5. Engineering Calc.",
            "6. Chemical Database"
        ],
        key="main_menu_mode" 
    )
    
    st.markdown("---")
    st.info("💡 **Tip:** 값을 입력하고 '적용' 버튼을 누르면 AI 진단이 시작됩니다.")
    st.caption("Authorized by **PARKER**")

# 6. 모듈 라우팅
if "Cooling" in program_mode:
    cooling.app(PRODUCT_CATALOG)
elif "Boiler" in program_mode:
    boiler.app(PRODUCT_CATALOG)
elif "RO" in program_mode:
    ro.app(PRODUCT_CATALOG)
elif "WWT" in program_mode:
    wwt.app(PRODUCT_CATALOG)
elif "Engineering" in program_mode:
    engineering.app()
elif "Chemical Database" in program_mode:
    chemical.app(df_master)