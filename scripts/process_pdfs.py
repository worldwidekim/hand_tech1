"""
Extract text from PDFs and chunk them for vector DB ingestion.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from pypdf import PdfReader


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def main() -> None:
    raw_dir = Path(os.getenv("RAW_PDF_DIR", "./data/raw_pdfs"))
    out_path = Path(os.getenv("PROCESSED_CHUNKS_PATH", "./data/processed/chunks.jsonl"))
    out_path.parent.mkdir(parents=True, exist_ok=True)

    chunk_size = int(os.getenv("CHUNK_SIZE", "800"))
    overlap = int(os.getenv("CHUNK_OVERLAP", "200"))

    pdf_files = sorted(raw_dir.glob("*.pdf"))
    if not pdf_files:
        raise SystemExit(f"No PDF found in {raw_dir}")

    count = 0
    with out_path.open("w", encoding="utf-8") as f:
        for pdf in pdf_files:
            reader = PdfReader(str(pdf))
            for page_idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                for c_idx, chunk in enumerate(chunk_text(text, chunk_size, overlap), start=1):
                    row = {
                        "id": f"{pdf.stem}_p{page_idx}_c{c_idx}",
                        "text": chunk,
                        "source": pdf.name,
                        "page": page_idx,
                    }
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    count += 1

    print(f"Saved {count} chunks -> {out_path}")


if __name__ == "__main__":
    main()
