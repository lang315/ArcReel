"""
In-memory SSE stream request management.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


TERMINAL_EVENTS = {"done", "error"}


@dataclass
class StreamEvent:
    id: int
    event: str
    data: dict[str, Any]

    def to_sse(self) -> str:
        payload = json.dumps(self.data, ensure_ascii=False, separators=(",", ":"))
        return f"id: {self.id}\nevent: {self.event}\ndata: {payload}\n\n"


@dataclass
class StreamRequest:
    request_id: str
    session_id: str
    user_message_id: int
    queue: asyncio.Queue[StreamEvent] = field(default_factory=asyncio.Queue)
    next_event_id: int = 1
    closed: bool = False
    producer_task: Optional[asyncio.Task[Any]] = None

    async def emit(self, event: str, data: dict[str, Any]) -> Optional[StreamEvent]:
        if self.closed:
            return None
        stream_event = StreamEvent(id=self.next_event_id, event=event, data=data)
        self.next_event_id += 1
        await self.queue.put(stream_event)
        if event in TERMINAL_EVENTS:
            self.closed = True
        return stream_event

    async def next_event(self, timeout_seconds: Optional[float] = None) -> StreamEvent:
        if timeout_seconds is None:
            return await self.queue.get()
        return await asyncio.wait_for(self.queue.get(), timeout=timeout_seconds)


class StreamRequestRegistry:
    def __init__(self):
        self._requests: dict[tuple[str, str], StreamRequest] = {}
        self._lock = asyncio.Lock()

    async def create_request(self, session_id: str, user_message_id: int) -> StreamRequest:
        request_id = f"req_{uuid.uuid4().hex}"
        request = StreamRequest(
            request_id=request_id,
            session_id=session_id,
            user_message_id=user_message_id,
        )
        key = (session_id, request_id)
        async with self._lock:
            self._requests[key] = request
        return request

    async def get_request(self, session_id: str, request_id: str) -> Optional[StreamRequest]:
        key = (session_id, request_id)
        async with self._lock:
            return self._requests.get(key)

    async def remove_request(self, session_id: str, request_id: str) -> None:
        key = (session_id, request_id)
        async with self._lock:
            self._requests.pop(key, None)

    async def list_request_ids(self, session_id: str) -> list[str]:
        async with self._lock:
            return [request_id for sid, request_id in self._requests.keys() if sid == session_id]

    @staticmethod
    def ping_event() -> str:
        payload = json.dumps(
            {"ts": datetime.now(timezone.utc).isoformat()},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return f"event: ping\ndata: {payload}\n\n"
