"""
RAG engine for physical therapy chatbot.
Main response model: Gemini.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


@dataclass
class RetrievedChunk:
    text: str
    source: str
    page: int | None
    score: float | None


class RAGEngine:
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다.")

        genai.configure(api_key=api_key)
        self.chat_model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")

        self.model = genai.GenerativeModel(self.chat_model_name)

        self.top_k = int(os.getenv("TOP_K_RESULTS", "12"))
        self.max_context_chunks = int(os.getenv("MAX_CONTEXT_CHUNKS", "12"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.2"))

        chroma_dir = Path(os.getenv("CHROMA_PERSIST_DIR", "./data/vectordb"))
        self.chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
        self.collection = self.chroma_client.get_or_create_collection(
            name="msk_knowledge_base", metadata={"hnsw:space": "cosine"}
        )

    def _embed_text(self, text: str) -> list[float]:
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                response = genai.embed_content(
                    model=self.embedding_model,
                    content=text,
                    task_type="retrieval_query",
                )
                embedding = response.get("embedding")
                if not embedding:
                    raise RuntimeError("Gemini embedding 응답이 비어 있습니다.")
                return embedding
            except Exception as exc:  # pragma: no cover
                last_error = exc
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"Gemini 임베딩 실패: {last_error}")

    def retrieve(self, query: str) -> list[RetrievedChunk]:
        query_embedding = self._embed_text(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=self.top_k,
            include=["documents", "metadatas", "distances"],
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for i, text in enumerate(docs):
            meta = metas[i] if i < len(metas) and metas[i] else {}
            dist = distances[i] if i < len(distances) else None
            retrieved.append(
                RetrievedChunk(
                    text=text,
                    source=meta.get("source", "unknown"),
                    page=meta.get("page"),
                    score=dist,
                )
            )
        return retrieved

    @staticmethod
    def _format_context(chunks: list[RetrievedChunk]) -> str:
        lines: list[str] = []
        for i, chunk in enumerate(chunks, start=1):
            page = chunk.page if chunk.page is not None else "?"
            lines.append(f"[문서{i}] source={chunk.source}, page={page}\n{chunk.text}")
        return "\n\n".join(lines)

    def _select_diverse_chunks(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        selected: list[RetrievedChunk] = []
        seen_sources: set[str] = set()

        for chunk in chunks:
            if chunk.source not in seen_sources:
                selected.append(chunk)
                seen_sources.add(chunk.source)
            if len(selected) >= self.max_context_chunks:
                return selected

        for chunk in chunks:
            if len(selected) >= self.max_context_chunks:
                break
            if chunk not in selected:
                selected.append(chunk)
        return selected

    def _build_prompt(self, symptom_input: str, context: str) -> str:
        return f"""
당신은 물리치료 전문 RAG 어시스턴트입니다.
아래 검색 근거를 우선 사용해, 증상에 맞는 안전 중심 재활 가이드를 작성하세요.
근거가 불충분한 부분은 반드시 "추론"이라고 명시하세요.
반드시 여러 책(가능하면 서로 다른 출처 3개 이상)의 정보를 교차 검토해 통합 결론을 제시하세요.

[검색 근거]
{context}

[사용자 증상]
{symptom_input}

[출력 형식]
아래 순서를 반드시 지키고, 각 항목을 한국어로 상세히 작성하세요.
1) 🎯 증상 분석
2) 🔍 의심 원인 (Top 3, 각 항목에 가능성 %, 합계 100)
3) 🔍 감별 평가 (필수): Special Tests + ROM 평가
4) 👋 촉진법 (Palpation) (필수)
5) 💉 치료 전략 (필수): Manual Therapy / Mobilization / 기타 치료
6) 🏃 재활 운동 (필수): Phase 1~3
7) 🧘 추천 필라테스 운동 (3~5개)
8) 🏋️ 추천 웨이트트레이닝 (3~5개)
9) ⛔ 피해야 할 필라테스 운동 (2~4개, 이유 포함)
10) ⛔ 피해야 할 웨이트트레이닝 (2~4개, 이유 포함)
11) 🏠 환자 자가관리
12) ⚠️ 의료 안전 안내 (응급/진료 필요 신호)

[작성 규칙]
- 진단 확정 표현은 피하고 가능성 기반으로 작성
- 위험한 운동은 금기 사유를 반드시 명시
- 운동 항목은 목적/방법/주의사항 포함
- 가능한 경우 각 핵심 문단 끝에 "출처: 물리치료 백과사전 기반 추론" 형식 적용
- 특정 단일 문헌에만 의존하지 말고, 서로 다른 문헌의 공통점/차이점을 통합해서 설명
""".strip()

    def generate_answer(self, symptom_input: str) -> dict[str, Any]:
        chunks = self.retrieve(symptom_input)
        if not chunks:
            return {
                "answer": "검색된 문서 근거가 없습니다. 먼저 PDF 처리와 벡터 DB 구축을 진행해 주세요.",
                "chunks": [],
            }

        selected_chunks = self._select_diverse_chunks(chunks)
        context = self._format_context(selected_chunks)

        response = self.model.generate_content(
            self._build_prompt(symptom_input, context),
            generation_config={"temperature": self.temperature},
        )
        answer = (response.text or "응답 생성 실패").strip()

        return {
            "answer": answer,
            "chunks": [chunk.__dict__ for chunk in selected_chunks],
        }


_engine: RAGEngine | None = None


def get_rag_engine() -> RAGEngine:
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine
