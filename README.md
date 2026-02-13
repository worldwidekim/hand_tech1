# MSK-AI Physical Therapy Chatbot

RAG 기반 물리치료 상담 보조 웹앱입니다.

## 핵심 요구 반영
- ChatGPT를 메인 LLM으로 사용
- 기존 PDF 기반 RAG 구조 유지
- 증상 답변 형식에 추천/금기 운동 포함
- Gemini API로 근육/동작 이해 보조 이미지 생성
- Google Drive 폴더 PDF 자동 동기화

## 로컬 실행 (macOS)
```bash
cd "/Users/worldwide/Documents/codex/1st hand_tech"
cp .env.example .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### `.env` 필수 값
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `GOOGLE_DRIVE_FOLDER_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON` 또는 `GOOGLE_SERVICE_ACCOUNT_FILE`

### 데이터 준비
```bash
python scripts/download_pdfs.py
python scripts/process_pdfs.py
python scripts/build_vectordb.py
```

### 앱 실행
```bash
streamlit run app.py
```

## 답변 출력 형식
아래 섹션이 고정으로 생성됩니다.
1. 증상 분석
2. 의심 원인 Top3(확률 합 100)
3. 감별 평가 (Special test + ROM)
4. 촉진법
5. 치료 전략
6. 재활 운동 (Phase1~3)
7. 추천 필라테스 운동
8. 추천 웨이트트레이닝
9. 피해야 할 필라테스 운동
10. 피해야 할 웨이트트레이닝
11. 환자 자가관리
12. 의료 안전 안내

## 배포 추천
### Render (권장)
- Docker 기반 배포
- `render.yaml` 포함
- 영속 디스크(`/var/data`)를 사용해 ChromaDB/PDF 유지

Render 환경변수는 `render.yaml` 기준으로 설정됩니다.
필수 비밀값:
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `GOOGLE_DRIVE_FOLDER_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`

## 참고
- 서비스 계정에 Google Drive 폴더 읽기 권한을 반드시 부여해야 합니다.
- 민감한 키는 절대 커밋하지 마세요.
