"""SQLite-backed persistence: sessions, message history, escalations, audit log."""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone

from config import get_settings

_settings = get_settings()
_lock = threading.RLock()
_conn: sqlite3.Connection | None = None


def _db() -> sqlite3.Connection:
    global _conn
    with _lock:
        if _conn is None:
            import os

            os.makedirs(os.path.dirname(_settings.db_path) or ".", exist_ok=True)
            _conn = sqlite3.connect(_settings.db_path, check_same_thread=False)
            _init(_conn)
        return _conn


def _init(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT,
            created_at TEXT,
            context TEXT
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            meta TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS escalations (
            escalation_id TEXT PRIMARY KEY,
            user_id TEXT,
            question TEXT,
            summary TEXT,
            reason TEXT,
            docs_ids TEXT,
            passages TEXT,
            created_at TEXT,
            status TEXT,
            resolution TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_id TEXT,
            question TEXT,
            status TEXT,
            decision TEXT,
            citations TEXT,
            created_at TEXT
        );
        """
    )
    conn.commit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- sessions --------------------------------------------------------------

def create_session(user_id: str) -> dict:
    sid = uuid.uuid4().hex[:12]
    row = {"session_id": sid, "user_id": user_id, "created_at": _now(), "context": {}}
    with _lock:
        _db().execute(
            "INSERT INTO sessions (session_id, user_id, created_at, context) VALUES (?,?,?,?)",
            (sid, user_id, row["created_at"], json.dumps(row["context"])),
        )
        _db().commit()
    return row


def get_session(session_id: str) -> dict | None:
    cur = _db().execute(
        "SELECT session_id, user_id, created_at, context FROM sessions WHERE session_id=?", (session_id,)
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "session_id": row[0],
        "user_id": row[1],
        "created_at": row[2],
        "context": json.loads(row[3] or "{}"),
    }


def update_session_context(session_id: str, context: dict) -> None:
    with _lock:
        _db().execute("UPDATE sessions SET context=? WHERE session_id=?", (json.dumps(context), session_id))
        _db().commit()


def list_sessions(user_id: str) -> list[dict]:
    cur = _db().execute(
        "SELECT session_id, created_at FROM sessions WHERE user_id=? ORDER BY created_at DESC", (user_id,)
    )
    return [{"session_id": r[0], "created_at": r[1]} for r in cur.fetchall()]


# --- messages --------------------------------------------------------------

def add_message(session_id: str, role: str, content: str, meta: dict | None = None) -> None:
    with _lock:
        _db().execute(
            "INSERT INTO messages (session_id, role, content, meta, created_at) VALUES (?,?,?,?,?)",
            (session_id, role, content, json.dumps(meta or {}), _now()),
        )
        _db().commit()


def get_history(session_id: str, limit: int = 12) -> list[dict]:
    cur = _db().execute(
        "SELECT role, content, meta FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
        (session_id, limit),
    )
    return [{"role": r[0], "content": r[1], "meta": json.loads(r[2] or "{}")} for r in reversed(cur.fetchall())]


# --- escalations ------------------------------------------------------------

def save_escalation(esc: dict) -> None:
    with _lock:
        _db().execute(
            "INSERT OR REPLACE INTO escalations "
            "(escalation_id, user_id, question, summary, reason, docs_ids, passages, created_at, status, resolution) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                esc["escalation_id"],
                esc["user_id"],
                esc["question"],
                esc["summary"],
                esc["reason"],
                json.dumps(esc["docs_ids"]),
                json.dumps(esc["passages"]),
                esc["created_at"],
                esc["status"],
                esc.get("resolution", ""),
            ),
        )
        _db().commit()


def list_escalations(status_filter: str | None = None) -> list[dict]:
    if status_filter:
        cur = _db().execute(
            "SELECT escalation_id, user_id, question, summary, reason, created_at, status FROM escalations WHERE status=? ORDER BY created_at DESC",
            (status_filter,),
        )
    else:
        cur = _db().execute(
            "SELECT escalation_id, user_id, question, summary, reason, created_at, status FROM escalations ORDER BY created_at DESC"
        )
    return [
        {
            "escalation_id": r[0],
            "user_id": r[1],
            "question": r[2],
            "summary": r[3],
            "reason": r[4],
            "created_at": r[5],
            "status": r[6],
        }
        for r in cur.fetchall()
    ]


def resolve_escalation(escalation_id: str, resolution: str) -> bool:
    with _lock:
        cur = _db().execute(
            "UPDATE escalations SET status='RESOLVED', resolution=? WHERE escalation_id=? AND status='OPEN'",
            (resolution, escalation_id),
        )
        _db().commit()
        return cur.rowcount > 0


# --- audit ------------------------------------------------------------------

def log_turn(session_id: str, user_id: str, question: str, status: str, decision: str, citations: list) -> None:
    with _lock:
        _db().execute(
            "INSERT INTO audit_log (session_id, user_id, question, status, decision, citations, created_at) VALUES (?,?,?,?,?,?,?)",
            (session_id, user_id, question, status, decision, json.dumps(citations), _now()),
        )
        _db().commit()


def recent_audit(limit: int = 50) -> list[dict]:
    cur = _db().execute(
        "SELECT session_id, user_id, question, status, decision, created_at FROM audit_log ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    return [
        {"session_id": r[0], "user_id": r[1], "question": r[2], "status": r[3], "decision": r[4], "created_at": r[5]}
        for r in cur.fetchall()
    ]