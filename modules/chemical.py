import streamlit as st
import pandas as pd

def app(df_master):
    st.title("💊 종합 약품 정보 & 영업 가이드")
    st.caption("💡 영업사원 필독: 제품별 핵심 세일즈 포인트와 현장 기술 팁을 확인하세요.")
    st.markdown("---")
    
    if not df_master.empty:
        col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
        with col_s1: search_keyword = st.text_input("🔍 통합 검색", placeholder="예: 308, 아연, 스케일, 카보, DBNPA")
        with col_s2: system_list = sorted(df_master['System'].unique().tolist()); selected_system = st.multiselect("설비", system_list, default=system_list)
        with col_s3: type_list = sorted(df_master['Type'].unique().tolist()); selected_type = st.multiselect("용도", type_list, default=type_list)
        df_view = df_master[(df_master['System'].isin(selected_system)) & (df_master['Type'].isin(selected_type))]
        if search_keyword:
            mask = df_view.astype(str).apply(lambda x: x.str.contains(search_keyword, case=False, na=False)).any(axis=1)
            df_view = df_view[mask]
        st.info(f"📋 검색 결과: 총 **{len(df_view)}** 건")

        if len(df_view) > 5:
            st.dataframe(
                df_view, use_container_width=True, hide_index=True,
                column_config={ "System": st.column_config.TextColumn("설비", width="small"), "Name": st.column_config.TextColumn("제품명", width="medium"), "Main_Ingredient": st.column_config.TextColumn("🧪 주요 성분", width="large"), "Sales_Point": st.column_config.TextColumn("💰 영업 포인트", width="large"), "Dosage": st.column_config.NumberColumn("주입량", format="%d ppm") }
            )
            st.caption("👇 검색 결과가 5개 이하가 되면 '상세 가이드 모드'가 열립니다.")
        else:
            for index, row in df_view.iterrows():
                with st.expander(f"📌 **{row['Name']}** ({row['Desc']})", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1: st.markdown(f"**🧪 주성분 (Recipe):**"); st.code(row['Main_Ingredient'], language=None) 
                    with c2: st.markdown(f"**🎯 적용 대상:** {row['Target']}"); st.markdown(f"**💧 표준 주입량:** {row['Dosage']} ppm"); st.markdown(f"**📏 관리 기준:** {row['Criteria']}")
                    st.markdown("---")
                    st.success(f"**🗣️ Sales Point (고객에게 이렇게 말하세요):**\n\n{row['Sales_Point']}")
                    st.info(f"**🔧 Field Tip (엔지니어 주의사항):**\n\n{row['Field_Tip']}")
    else:
        st.warning("데이터를 불러오지 못했습니다. chemical_db.xlsx 파일을 확인하세요.")