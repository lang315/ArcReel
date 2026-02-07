"""
Agent runtime data models.
"""

from typing import Literal, Optional

from pydantic import BaseModel

SessionStatus = Literal["active", "archived", "error"]
MessageRole = Literal["user", "assistant", "system", "tool"]
MessageEventType = Literal["message", "chunk", "tool_call", "tool_result"]


class AgentSession(BaseModel):
    id: str
    project_name: str
    title: str = ""
    status: SessionStatus = "active"
    created_at: str
    updated_at: str


class AgentMessage(BaseModel):
    id: int
    session_id: str
    role: MessageRole
    content: str
    event_type: Optional[MessageEventType] = "message"
    created_at: str

