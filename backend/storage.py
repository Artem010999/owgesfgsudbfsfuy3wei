from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "conversation_cards.db"
CARDS_DIR = BASE_DIR / "cards_export"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db() -> None:
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_cards_conversation
        ON conversation_cards (conversation_id, created_at)
        """
    )
    conn.commit()
    conn.close()


def _file_name(conversation_id: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", conversation_id)
    return f"{safe}.json"


def save_cards(conversation_id: str, payload: Dict[str, Any]) -> Path:
    serialized = json.dumps(payload, ensure_ascii=False)

    conn = _connect()
    conn.execute(
        "INSERT INTO conversation_cards (conversation_id, payload) VALUES (?, ?)",
        (conversation_id, serialized),
    )
    conn.commit()
    conn.close()

    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = CARDS_DIR / _file_name(conversation_id)
    file_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return file_path


def get_cards_file_path(conversation_id: str) -> Path:
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    return CARDS_DIR / _file_name(conversation_id)


def fetch_latest_cards(conversation_id: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    row = conn.execute(
        """
        SELECT payload FROM conversation_cards
        WHERE conversation_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (conversation_id,),
    ).fetchone()
    conn.close()
    if not row:
        file_path = CARDS_DIR / _file_name(conversation_id)
        if file_path.exists():
            try:
                return json.loads(file_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
        return None
    try:
        return json.loads(row[0])
    except json.JSONDecodeError:
        return None

