from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, List, Literal

from fastapi import FastAPI, HTTPException
from gradio_client import Client
from pydantic import BaseModel, Field

from text_ai.call_hf_endpoint import chat as hf_chat

DEFAULT_NEGATIVE_PROMPT = (
    "bad quality, worst quality, low quality, blurry, low details, bad anatomy, "
    "bad proportions, extra limbs, text, watermark, signature"
)
MAX_DIMENSION = 1024
MIN_DIMENSION = 64


class ImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Основной промпт для генерации")
    negative_prompt: str = Field(
        default=DEFAULT_NEGATIVE_PROMPT,
        description="Негативный промпт для исключения нежелательных артефактов",
    )
    steps: int = Field(default=50, ge=1, le=150)
    guidance_scale: float = Field(default=7.0, ge=0.0, le=30.0)
    width: int = Field(default=512, ge=MIN_DIMENSION, le=MAX_DIMENSION)
    height: int = Field(default=512, ge=MIN_DIMENSION, le=MAX_DIMENSION)
    seed: int = Field(default=0, ge=0, description="Seed для детерминированности")


class ImageResponse(BaseModel):
    url: str = Field(..., description="URL сгенерированного изображения")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_new_tokens: int = Field(default=512, ge=64, le=1024)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    top_p: float = Field(default=0.9, ge=0.1, le=1.0)


class ChatResponse(BaseModel):
    text: str = Field(..., description="Ответ ассистента")


@lru_cache(maxsize=1)
def _get_client() -> Client:
    endpoint = os.getenv("PICTURE_AI_ENDPOINT")
    if not endpoint:
        raise RuntimeError("Environment variable PICTURE_AI_ENDPOINT is required")
    return Client(endpoint.rstrip("/"))


app = FastAPI(title="Picture AI Proxy", version="1.0.0")


def _extract_url(result: Any) -> str:
    """Пытаемся достать URL из различных форматов ответа gradio_client."""
    if result is None:
        raise HTTPException(status_code=502, detail="Empty response from image service")

    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        if "url" in result and isinstance(result["url"], str):
            return result["url"]
        for value in result.values():
            try:
                return _extract_url(value)
            except HTTPException:
                continue

    if isinstance(result, (list, tuple, set)):
        for item in result:
            try:
                return _extract_url(item)
            except HTTPException:
                continue

    url = getattr(result, "url", None)
    if isinstance(url, str):
        return url

    raise HTTPException(status_code=502, detail="Unexpected response format from image service")


def _extract_text(result: Any) -> str:
    if result is None:
        raise HTTPException(status_code=502, detail="Empty response from text service")

    if isinstance(result, str):
        return result

    if isinstance(result, dict):
        if "generated_text" in result and isinstance(result["generated_text"], str):
            return result["generated_text"]
        if "text" in result and isinstance(result["text"], str):
            return result["text"]
        for value in result.values():
            try:
                return _extract_text(value)
            except HTTPException:
                continue

    if isinstance(result, (list, tuple, set)):
        for item in result:
            try:
                return _extract_text(item)
            except HTTPException:
                continue

    text = getattr(result, "generated_text", None) or getattr(result, "text", None)
    if isinstance(text, str):
        return text

    raise HTTPException(status_code=502, detail="Unexpected response format from text service")


@app.post("/generate", response_model=ImageResponse)
async def generate_image(payload: ImageRequest) -> ImageResponse:
    client = _get_client()

    try:
        prediction = client.predict(
            prompt=payload.prompt,
            negative_prompt=payload.negative_prompt,
            steps=payload.steps,
            guidance_scale=payload.guidance_scale,
            width=payload.width,
            height=payload.height,
            seed=payload.seed,
            api_name="/generate_image",
        )
    except Exception as exc:  # pragma: no cover - proxied external errors
        raise HTTPException(status_code=502, detail=f"Image generation failed: {exc}") from exc

    image_url = _extract_url(prediction)
    return ImageResponse(url=image_url)


@app.post("/text/chat", response_model=ChatResponse)
async def generate_text(payload: ChatRequest) -> ChatResponse:
    try:
        result = hf_chat(
            messages=[message.model_dump() for message in payload.messages],
            max_new_tokens=payload.max_new_tokens,
            temperature=payload.temperature,
            top_p=payload.top_p,
        )
    except Exception as exc:  # pragma: no cover - внешние ошибки
        raise HTTPException(status_code=502, detail=f"Text generation failed: {exc}") from exc

    text = _extract_text(result)
    return ChatResponse(text=text)
