"""FastAPI backend skeleton for chat message handling."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx

from pydantic import BaseModel, Field
from uuid import uuid4

from prof_test import CareerAdvisor
from storage import (
    CARDS_DIR,
    fetch_latest_cards,
    get_cards_file_path,
    init_db,
    save_cards,
)

logger = logging.getLogger(__name__)

CARDS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Генератор рабочего вайба API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/cards", StaticFiles(directory=str(CARDS_DIR)), name="cards")

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8500")
JSON_MARKER = "<<JSON>>"


@app.on_event("startup")
def _startup() -> None:
    init_db()


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
    structured_data: Optional[Dict[str, Any]] = None
    cards_file: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str


class CardsResponse(BaseModel):
    data: Optional[Dict[str, Any]] = None
    file: Optional[str] = None


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

    reply_text, structured_payload = _extract_structured(ai_reply)

    history.append({"role": "assistant", "content": reply_text})

    cards_file_url: Optional[str] = None

    if structured_payload:
        try:
            file_path = save_cards(conversation_id, structured_payload)
            cards_file_url = f"/cards/{file_path.name}"
        except Exception as exc:  # pragma: no cover - логирование ошибок БД
            logger.error("Failed to store structured data: %s", exc)
    else:
        file_path = get_cards_file_path(conversation_id)
        if file_path.exists():
            cards_file_url = f"/cards/{file_path.name}"

    return ChatResponse(
        reply=reply_text,
        conversation_id=conversation_id,
        history=history,
        structured_data=structured_payload,
        cards_file=cards_file_url,
    )


@app.get("/api/conversation/{conversation_id}/cards", response_model=CardsResponse)
def conversation_cards(conversation_id: str) -> CardsResponse:
    payload = fetch_latest_cards(conversation_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Карточки не найдены")
    file_path = get_cards_file_path(conversation_id)
    file_url = f"/cards/{file_path.name}" if file_path.exists() else None
    return CardsResponse(data=payload, file=file_url)


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


def _extract_structured(reply: str) -> tuple[str, Optional[Dict[str, Any]]]:
    sanitized = (
        reply.replace("<JSON>", JSON_MARKER)
        .replace("JSON:", JSON_MARKER)
        .replace("<<JSON", JSON_MARKER)
        .replace("JSON>>", JSON_MARKER)
        .replace("<<<", JSON_MARKER)
        .replace(">>>", "")
    )

    if JSON_MARKER in sanitized:
        text_part, possible_json = sanitized.split(JSON_MARKER, 1)
        text_part = _clean_text(text_part)
        candidate = possible_json.strip()
        if candidate:
            parsed, consumed = _parse_json_substring(candidate)
            if parsed is not None:
                tail = _clean_text(candidate[consumed:])
                combined_text = (text_part + (" " + tail if tail else "")).strip()
                return combined_text, parsed
            logger.error("Failed to parse structured JSON after marker")
        return text_part, None

    first_brace = sanitized.find("{")
    if first_brace == -1:
        return _clean_text(sanitized), None

    base_text = _clean_text(sanitized[:first_brace])
    json_candidate = sanitized[first_brace:]
    parsed, consumed = _parse_json_substring(json_candidate)
    if parsed is not None:
        tail = _clean_text(json_candidate[consumed:])
        combined_text = (base_text + (" " + tail if tail else "")).strip()
        return combined_text, parsed
    logger.error("Failed to parse structured JSON fallback")
    return base_text, None


def _parse_json_substring(payload: str) -> tuple[Optional[Dict[str, Any]], int]:
    end_indices = [idx for idx, char in enumerate(payload) if char == "}"]
    for end in reversed(end_indices):
        candidate = payload[: end + 1].strip()
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data, end + 1
        except json.JSONDecodeError:
            continue
    return None, 0


def _clean_text(text: str) -> str:
    return (
        text.replace("<", " ")
        .replace(">", " ")
        .replace(JSON_MARKER, " ")
        .strip()
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

