"""FastAPI backend skeleton for chat message handling."""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

from pydantic import BaseModel, Field
from uuid import uuid4

from prof_test import CareerAdvisor

logger = logging.getLogger(__name__)

app = FastAPI(title="Генератор рабочего вайба API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8500")


class ChatMessage(BaseModel):
    """Payload, который прилетает от фронтенда."""

    message: str = Field(..., min_length=1, description="Сообщение пользователя")
    conversation_id: Optional[str] = Field(
        default=None, description="Идентификатор сессии (если есть)"
    )


class ChatResponse(BaseModel):
    """Ответ, который возвращаем на фронт."""

    reply: str
    conversation_id: str
    history: List[Dict[str, str]]


class ErrorResponse(BaseModel):
    detail: str


class ProfTestAnswers(BaseModel):
    q1: Optional[str] = None
    q2: Optional[List[str]] = None
    q3: Optional[List[str]] = None
    q4: Optional[List[str]] = None
    q5: Optional[str] = None
    q6: Optional[List[str]] = None
    q7: Optional[str] = None


class ProfRecommendation(BaseModel):
    recommendation: str


class PictureRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    negative_prompt: Optional[str] = None
    steps: Optional[int] = Field(default=None, ge=1, le=150)
    guidance_scale: Optional[float] = Field(default=None, ge=0.0, le=30.0)
    width: Optional[int] = Field(default=None, ge=64, le=1024)
    height: Optional[int] = Field(default=None, ge=64, le=1024)
    seed: Optional[int] = Field(default=None, ge=0)


class PictureResponse(BaseModel):
    url: str


# In-memory "хранилище" под текущую сессию: conversation_id -> list of messages
_CHAT_HISTORY: Dict[str, List[Dict[str, str]]] = {}
_ADVISOR = CareerAdvisor()


@app.get("/health", response_model=dict[str, str])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse, responses={400: {"model": ErrorResponse}})
async def chat_endpoint(payload: ChatMessage) -> ChatResponse:
    """Получает сообщение от пользователя и возвращает "ответ" от ИИ."""

    conversation_id = payload.conversation_id or str(uuid4())
    history = _CHAT_HISTORY.setdefault(conversation_id, [])

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Пустое сообщение")

    history.append({"role": "user", "content": message})

    try:
        ai_reply = await _call_text_ai(history)
    except Exception as exc:
        # Фолбэк на заглушку, если сервис недоступен, но историю не рушим
        ai_reply = _fake_ai_reply(message)
        logger.error("Text AI call failed: %s", exc)

    history.append({"role": "assistant", "content": ai_reply})

    return ChatResponse(
        reply=ai_reply,
        conversation_id=conversation_id,
        history=history,
    )


@app.post("/api/profession", response_model=ProfRecommendation)
def profession_endpoint(payload: ProfTestAnswers) -> ProfRecommendation:
    """Возвращает рекомендацию профессии на основе результатов теста."""

    answers = {
        key: value
        for key, value in payload.dict().items()
        if value not in (None, "", [], {})
    }

    try:
        recommendation_text = _ADVISOR.get_recommendation(answers)
    except Exception as exc:  # pragma: no cover - сетевые ошибки
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ProfRecommendation(recommendation=recommendation_text)


@app.post("/api/picture", response_model=PictureResponse)
async def generate_picture(payload: PictureRequest) -> PictureResponse:
    if not AI_SERVICE_URL:
        raise HTTPException(status_code=500, detail="AI service URL is not configured")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{AI_SERVICE_URL.rstrip('/')}/generate",
                json=payload.model_dump(exclude_none=True),
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.json().get("detail") if exc.response.content else str(exc)
            raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"AI service unreachable: {exc}") from exc

    data = response.json()
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=502, detail="AI service returned invalid payload")
    return PictureResponse(url=url)


def _fake_ai_reply(user_text: str) -> str:
    """Простейшая заглушка вместо реального LLM.

    Сейчас просто оборачиваем сообщение. Когда появится интеграция,
    эту функцию можно заменить на вызов модели.
    """

    return f"Я услышал: '{user_text}'. Настраиваю рабочий вайб!"


async def _call_text_ai(history: List[Dict[str, str]]) -> str:
    if not AI_SERVICE_URL:
        raise RuntimeError("AI service URL is not configured")

    payload = {
        "messages": history,
        "max_new_tokens": 600,
        "temperature": 0.7,
        "top_p": 0.9,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{AI_SERVICE_URL.rstrip('/')}/text/chat",
            json=payload,
        )

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail")
        except Exception:  # pragma: no cover
            detail = response.text
        raise RuntimeError(f"Text AI service error: {detail}")

    data = response.json()
    if isinstance(data, dict):
        if "text" in data and isinstance(data["text"], str):
            return data["text"].strip()
        if "reply" in data and isinstance(data["reply"], str):
            return data["reply"].strip()

    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict) and "generated_text" in first:
            return str(first["generated_text"]).strip()

    raise RuntimeError("Unexpected response from text AI service")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

