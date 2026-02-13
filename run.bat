@echo off
chcp 65001 >nul
call venv\Scripts\activate
streamlit run app.py
