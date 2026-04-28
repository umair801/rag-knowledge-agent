"""
Conversation memory manager.
Maintains per-session chat history for multi-turn RAG conversations.
"""
import uuid
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()

# In-memory session store: {session_id: {messages, created_at, last_active}}
_sessions: Dict[str, dict] = {}

# Session settings
MAX_HISTORY_TURNS = 10       # Max question/answer pairs to keep
SESSION_TTL_MINUTES = 60     # Auto-expire sessions after 60 min of inactivity


def create_session() -> str:
    """Create a new conversation session and return its ID."""
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "messages": [],
        "created_at": datetime.now(),
        "last_active": datetime.now(),
    }
    logger.info("session_created", session_id=session_id)
    return session_id


def get_history(session_id: str) -> List[dict]:
    """
    Retrieve chat history for a session.
    Returns empty list if session does not exist or has expired.
    """
    session = _sessions.get(session_id)
    if not session:
        return []

    # Check expiry
    idle_minutes = (datetime.now() - session["last_active"]).seconds / 60
    if idle_minutes > SESSION_TTL_MINUTES:
        delete_session(session_id)
        logger.info("session_expired", session_id=session_id)
        return []

    return session["messages"]


def add_turn(session_id: str, query: str, answer: str) -> None:
    """
    Add a question/answer pair to session history.
    Automatically trims history to MAX_HISTORY_TURNS.
    """
    if session_id not in _sessions:
        _sessions[session_id] = {
            "messages": [],
            "created_at": datetime.now(),
            "last_active": datetime.now(),
        }

    session = _sessions[session_id]

    # Append user question and assistant answer
    session["messages"].append({"role": "user", "content": query})
    session["messages"].append({"role": "assistant", "content": answer})
    session["last_active"] = datetime.now()

    # Trim to last N turns (each turn = 2 messages)
    max_messages = MAX_HISTORY_TURNS * 2
    if len(session["messages"]) > max_messages:
        session["messages"] = session["messages"][-max_messages:]

    logger.info(
        "turn_added",
        session_id=session_id,
        total_messages=len(session["messages"]),
    )


def delete_session(session_id: str) -> bool:
    """Delete a session and its history."""
    if session_id in _sessions:
        del _sessions[session_id]
        logger.info("session_deleted", session_id=session_id)
        return True
    return False


def get_session_stats(session_id: str) -> Optional[dict]:
    """Return metadata about a session."""
    session = _sessions.get(session_id)
    if not session:
        return None
    return {
        "session_id": session_id,
        "turn_count": len(session["messages"]) // 2,
        "created_at": session["created_at"].isoformat(),
        "last_active": session["last_active"].isoformat(),
    }