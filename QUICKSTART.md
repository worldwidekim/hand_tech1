# MSK-AI 챗봇 빠른 시작

## 1) 환경 변수
```bash
cp .env.example .env
```
`.env`에 아래 값 입력:
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `GOOGLE_DRIVE_FOLDER_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON` 또는 `GOOGLE_SERVICE_ACCOUNT_FILE`

## 2) 설치
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3) Google Drive에서 PDF 자동 동기화
```bash
python scripts/download_pdfs.py
```

## 4) 데이터 구축
```bash
python scripts/process_pdfs.py
python scripts/build_vectordb.py
```

## 5) 실행
```bash
streamlit run app.py
```
브라우저: `http://localhost:8501`

## 6) 답변 형식 확인 포인트
- `의심 원인 Top 3` 확률 합계 100%
- `추천 필라테스/웨이트`와 `피해야 할 필라테스/웨이트` 포함
- 감별평가/촉진/치료전략/재활운동(Phase1~3) 포함
