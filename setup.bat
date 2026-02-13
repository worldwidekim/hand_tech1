@echo off
chcp 65001 >nul
echo ========================================
echo MSK-AI 챗봇 설치 스크립트
echo ========================================

echo [1/3] 가상환경 생성 중...
python -m venv venv
if errorlevel 1 (
    echo 가상환경 생성 실패
    pause
    exit /b 1
)

echo [2/3] 가상환경 활성화 중...
call venv\Scripts\activate

echo [3/3] 패키지 설치 중...
pip install -r requirements.txt
if errorlevel 1 (
    echo 패키지 설치 실패
    pause
    exit /b 1
)

echo 설치 완료
pause
