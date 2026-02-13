"""
MSK-AI chatbot UI (Streamlit).
- Main LLM: Gemini
- RAG source: local PDF vector DB
- Optional image: Gemini
"""

from __future__ import annotations

import os
import streamlit as st
from dotenv import load_dotenv

from rag_engine import get_rag_engine

load_dotenv()

st.set_page_config(
    page_title="물리치료 백과사전",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.main-header { font-size: 2.2rem; font-weight: 800; color: #0F172A; margin-bottom: 0.25rem; }
.sub-header { color: #334155; margin-bottom: 1rem; }
.block-label { font-size: 0.95rem; color: #475569; margin-bottom: 0.2rem; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="main-header">통증 검색기</div>', unsafe_allow_html=True)

symptom = st.text_area(
    "증상/통증 설명",
    placeholder="예: 아킬레스건 통증이 3개월째 반복되고 아침에 뻣뻣함이 심해요.",
    height=120,
)

if st.button("분석 시작", type="primary", use_container_width=True):
    if not symptom.strip():
        st.warning("증상을 먼저 입력해 주세요.")
        st.stop()

    try:
        engine = get_rag_engine()

        with st.spinner("RAG 검색 및 Gemini 답변 생성 중..."):
            result = engine.generate_answer(symptom)

        st.subheader("분석 결과")
        st.markdown(result["answer"])

        st.info(
            "안내: 이 결과는 참고용입니다. 급성 악화, 열감/심한 부기, 야간통, 파열 의심(갑작스런 '뚝' 소리 + 보행 불가) 시 즉시 진료를 받으세요."
        )

    except Exception as exc:
        st.error(f"실행 중 오류: {exc}")

st.divider()
st.caption("데이터가 없는 경우 먼저 PDF 처리/벡터DB 구축 스크립트를 실행하세요.")
