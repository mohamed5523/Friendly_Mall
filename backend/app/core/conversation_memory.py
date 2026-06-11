"""Simplified in-memory conversation memory (no Redis)."""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from app.core.state_manager import MallConversationState


@dataclass
class Message:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)


class SessionMemory:
    def __init__(self, max_messages: int = 20, ttl_seconds: int = 3600):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self.max_messages = max_messages
        self.ttl = ttl_seconds

    def _get_session(self, session_id: str) -> Dict[str, Any]:
        now = time.time()
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "messages": [], "state": None, "last_active": now
            }
        s = self._sessions[session_id]
        # expire old sessions
        if now - s["last_active"] > self.ttl:
            self._sessions[session_id] = {
                "messages": [], "state": None, "last_active": now
            }
        s["last_active"] = now
        return self._sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        s = self._get_session(session_id)
        s["messages"].append(Message(role=role, content=content))
        if len(s["messages"]) > self.max_messages:
            s["messages"] = s["messages"][-self.max_messages:]

    def get_messages(self, session_id: str, limit: int = 10) -> List[Message]:
        return self._get_session(session_id)["messages"][-limit:]

    def get_history_dicts(self, session_id: str, limit: int = 6) -> List[dict]:
        return [
            {"role": m.role, "content": m.content}
            for m in self.get_messages(session_id, limit)
        ]

    def save_state(self, session_id: str, state: MallConversationState):
        self._get_session(session_id)["state"] = state

    def get_state(self, session_id: str) -> Optional[MallConversationState]:
        return self._get_session(session_id).get("state")


# Global instance
short_term_memory = SessionMemory(max_messages=20, ttl_seconds=3600)