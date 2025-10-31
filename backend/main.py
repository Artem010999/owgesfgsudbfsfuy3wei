"""FastAPI backend skeleton for chat message handling."""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field
from uuid import uuid4

from prof_test import CareerAdvisor

app = FastAPI(title="Генератор рабочего вайба API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    history: List[str]


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


# In-memory "хранилище" под текущую сессию: conversation_id -> list of messages
_CHAT_HISTORY: Dict[str, List[str]] = {}
_ADVISOR = CareerAdvisor()


@app.get("/health", response_model=dict[str, str])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse, responses={400: {"model": ErrorResponse}})
def chat_endpoint(payload: ChatMessage) -> ChatResponse:
    """Получает сообщение от пользователя и возвращает "ответ" от ИИ."""

    conversation_id = payload.conversation_id or str(uuid4())
    history = _CHAT_HISTORY.setdefault(conversation_id, [])

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Пустое сообщение")

    history.append(f"user: {message}")

    # TODO: интеграция с реальным LLM/сервисом!!!!
    ai_reply = _fake_ai_reply(message)

    history.append(f"assistant: {ai_reply}")

    return ChatResponse(reply=ai_reply, conversation_id=conversation_id, history=history)


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


def _fake_ai_reply(user_text: str) -> str:
    """Простейшая заглушка вместо реального LLM.

    Сейчас просто оборачиваем сообщение. Когда появится интеграция,
    эту функцию можно заменить на вызов модели.
    """

    return f"Я услышал: '{user_text}'. Настраиваю рабочий вайб!"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

