# 물리치료 챗봇 프로젝트 재현 가이드

## 프로젝트 개요
- UI: Streamlit
- 메인 LLM: ChatGPT (`OPENAI_CHAT_MODEL`)
- 이미지 보조: Gemini (`GEMINI_IMAGE_MODEL`)
- 벡터 DB: ChromaDB
- 데이터 소스: Google Drive PDF (자동 동기화)

## 폴더 구조
- `app.py`: Streamlit UI
- `rag_engine.py`: 검색 + ChatGPT 응답 생성(JSON 스키마 고정)
- `image_engine.py`: Gemini 이미지 생성
- `scripts/download_pdfs.py`: Google Drive PDF 증분 동기화
- `scripts/process_pdfs.py`: PDF 청킹
- `scripts/build_vectordb.py`: 임베딩 + Chroma 적재

## 로컬 재현 절차
1. `.env.example` -> `.env` 복사
2. API 키/Drive 설정 입력
3. `pip install -r requirements.txt`
4. `python scripts/download_pdfs.py`
5. `python scripts/process_pdfs.py`
6. `python scripts/build_vectordb.py`
7. `streamlit run app.py`

## 배포 권장
- 1순위: Render + Docker
- 영속 스토리지: `render.yaml`에 `/var/data` 디스크 마운트
- 주요 저장 경로:
  - `RAW_PDF_DIR=/var/data/raw_pdfs`
  - `PROCESSED_CHUNKS_PATH=/var/data/processed/chunks.jsonl`
  - `CHROMA_PERSIST_DIR=/var/data/vectordb`
