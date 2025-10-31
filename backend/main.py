"""FastAPI backend skeleton for chat message handling."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

from pydantic import BaseModel, Field
from uuid import uuid4

from prof_test import CareerAdvisor

logger = logging.getLogger(__name__)

JSON_MARKER = "<<JSON>>"

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
    history: Optional[List[Dict[str, str]]] = Field(
        default=None, description="Полный контекст диалога, который есть у клиента"
    )


class ChatResponse(BaseModel):
    """Ответ, который возвращаем на фронт."""

    reply: str
    conversation_id: str
    history: List[Dict[str, str]]
    structured_data: Optional[Dict[str, Any]] = None


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
_CHAT_STATE: Dict[str, Dict[str, str]] = {}
_ADVISOR = CareerAdvisor()


@app.get("/health", response_model=dict[str, str])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse, responses={400: {"model": ErrorResponse}})
async def chat_endpoint(payload: ChatMessage) -> ChatResponse:
    """Получает сообщение от пользователя и возвращает "ответ" от ИИ."""

    conversation_id = payload.conversation_id or str(uuid4())
    history = _CHAT_HISTORY.setdefault(conversation_id, [])
    state = _CHAT_STATE.setdefault(conversation_id, {"phase": "need_clarifications"})

    if not history and payload.history:
        safe_history: List[Dict[str, str]] = []
        for item in payload.history:
            role = item.get("role")
            content = str(item.get("content", "")).strip()
            if role in {"user", "assistant"} and content:
                safe_history.append({"role": role, "content": content})
        if safe_history:
            history.extend(safe_history)

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Пустое сообщение")

    history.append({"role": "user", "content": message})

    current_phase = state.get("phase", "need_clarifications")
    if current_phase == "awaiting_answers":
        state["phase"] = "ready_for_summary"
    elif current_phase == "summary_sent":
        state["phase"] = "roleplay"
    current_phase = state.get("phase", "need_clarifications")

    try:
        ai_reply = await _call_text_ai(history, state)
    except Exception as exc:
        # Фолбэк на заглушку, если сервис недоступен, но историю не рушим
        ai_reply = _fake_ai_reply(message)
        logger.error("Text AI call failed: %s", exc)
        state["phase"] = current_phase  # не продвигаем фазу при ошибке
    else:
        if current_phase == "need_clarifications":
            state["phase"] = "awaiting_answers"
        elif current_phase == "ready_for_summary":
            if JSON_MARKER in ai_reply:
                state["phase"] = "summary_sent"
            else:
                # если модель не дала JSON, остаёмся в этой фазе
                state["phase"] = "ready_for_summary"
        elif current_phase == "roleplay" and JSON_MARKER in ai_reply:
            # JSON в ролевой фазе не допускается — отбрасываем его
            ai_reply = ai_reply.split(JSON_MARKER)[0].strip()

    reply_text, structured = _extract_structured(ai_reply)

    history.append({"role": "assistant", "content": reply_text})

    if structured is not None:
        state["data"] = structured

    return ChatResponse(
        reply=reply_text,
        conversation_id=conversation_id,
        history=history,
        structured_data=structured,
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


def _build_control_message(phase: str) -> str:
    if phase == "need_clarifications":
        return (
            "Текущий этап: уточняющие вопросы. Задай ровно три коротких вопроса в одном кратком предложении,"
            " избегай списков и длинных описаний. Не выводи JSON и не рассказывай про профессию."
        )
    if phase == "ready_for_summary":
        return (
            "Текущий этап: финальное резюме. Ответь фразой 'Спасибо за ответы! Твое рабочее пространство готово)"
            " Сейчас ты погрузишься в профессию <профессия>.' и сразу после неё без дополнительных слов"
            f" выведи маркер {JSON_MARKER} и чистый JSON. Не используй слова 'JSON', не добавляй пояснений,"
            " не продолжай диалог в этом сообщении."
        )
    if phase in {"awaiting_answers", "summary_sent", "roleplay"}:
        return (
            "Текущий этап: ролевое общение. Отвечай в 1-2 коротких предложениях от лица коллег, менеджеров"
            " или заказчиков. Всегда начинай с указания роли, предлагай задачи или неформальное общение."
            " JSON не формируй."
        )
    return ""


async def _call_text_ai(history: List[Dict[str, str]], state: Dict[str, str]) -> str:
    if not AI_SERVICE_URL:
        raise RuntimeError("AI service URL is not configured")

    phase = state.get("phase", "need_clarifications")
    control_message = _build_control_message(phase)

    payload_messages: List[Dict[str, str]] = []
    if control_message:
        payload_messages.append({"role": "system", "content": control_message})
    payload_messages.extend(history)

    payload = {
        "messages": payload_messages,
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
    sanitized = reply.replace('<JSON>', JSON_MARKER).replace('JSON:', JSON_MARKER)

    if JSON_MARKER in sanitized:
        text_part, possible_json = sanitized.split(JSON_MARKER, 1)
        text_part = text_part.strip().rstrip(':').strip()
        candidate = possible_json.strip()
        if candidate:
            parsed = _parse_json_substring(candidate)
            if parsed is not None:
                return text_part, parsed
            logger.error("Failed to parse structured JSON after marker")
        return text_part, None

    first_brace = sanitized.find('{')
    if first_brace == -1:
        return sanitized.strip(), None

    base_text = sanitized[:first_brace].strip().rstrip(':').strip()
    json_candidate = sanitized[first_brace:]
    parsed = _parse_json_substring(json_candidate)
    if parsed is not None:
        return base_text, parsed
    logger.error("Failed to parse structured JSON fallback")
    return base_text, None


def _parse_json_substring(payload: str) -> Optional[Dict[str, Any]]:
    end_indices = [idx for idx, char in enumerate(payload) if char == '}']
    for end in reversed(end_indices):
        candidate = payload[: end + 1]
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue
    return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

