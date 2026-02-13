@echo off
chcp 65001 >nul
call venv\Scripts\activate

echo [1/3] 폴더 준비
python scripts\download_pdfs.py

echo [2/3] PDF 처리 및 청킹
python scripts\process_pdfs.py
if errorlevel 1 (
    echo PDF 처리 실패
    pause
    exit /b 1
)

echo [3/3] 벡터 DB 구축
python scripts\build_vectordb.py
if errorlevel 1 (
    echo 벡터 DB 구축 실패
    pause
    exit /b 1
)

echo 데이터 준비 완료
pause
