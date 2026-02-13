"""
Gemini image helper for movement/muscle visualization.
"""

from __future__ import annotations

import io
import os
from typing import Tuple

from PIL import Image
import google.generativeai as genai


def generate_muscle_image(symptom: str) -> Tuple[Image.Image | None, str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None, "GEMINI_API_KEY가 설정되지 않아 이미지 생성을 건너뜁니다."

    genai.configure(api_key=api_key)
    preferred_model = os.getenv("GEMINI_IMAGE_MODEL", "models/nano-banana-pro-preview")
    fallback_models = [
        preferred_model,
        "models/gemini-2.0-flash-exp-image-generation",
        "models/gemini-2.5-flash-image",
    ]

    prompt = (
        "Create a clean medical-style educational illustration for physical therapy. "
        "Show major muscles, tendon region, and movement direction relevant to this symptom: "
        f"{symptom}. "
        "No gore, no diagnosis label, no patient-identifiable details."
    )

    for model_name in fallback_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config={"response_modalities": ["TEXT", "IMAGE"]},
            )

            candidates = getattr(response, "candidates", None) or []
            for candidate in candidates:
                content = getattr(candidate, "content", None)
                parts = getattr(content, "parts", None) or []
                for part in parts:
                    inline_data = getattr(part, "inline_data", None)
                    if inline_data and getattr(inline_data, "data", None):
                        image_bytes = inline_data.data
                        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                        return img, "Gemini 기반 근육/동작 참고 이미지를 생성했습니다."

            text = getattr(response, "text", "") or ""
            if text:
                return None, f"이미지 대신 텍스트 응답만 수신했습니다: {text[:160]}"
        except Exception:
            continue

    return None, "Gemini 이미지 생성 실패: 사용 가능한 이미지 모델을 찾지 못했습니다."
