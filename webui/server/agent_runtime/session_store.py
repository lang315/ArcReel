"""
SQLite-based session and message storage for assistant runtime.
"""

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from webui.server.agent_runtime.models import (
    AgentMessage,
    AgentSession,
    MessageEventType,
    MessageRole,
    SessionStatus,
)


class AgentSessionStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _to_session(row: sqlite3.Row) -> AgentSession:
        return AgentSession(
            id=row["id"],
            project_name=row["project_name"],
            title=row["title"] or "",
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _to_message(row: sqlite3.Row) -> AgentMessage:
        return AgentMessage(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            event_type=row["event_type"],
            created_at=row["created_at"],
        )

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_sessions (
                    id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    title TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    event_type TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES agent_sessions(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_agent_sessions_project_updated
                ON agent_sessions (project_name, updated_at DESC)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_agent_sessions_status_updated
                ON agent_sessions (status, updated_at DESC)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_agent_messages_session_id
                ON agent_messages (session_id, id)
                """
            )

    def create_session(self, project_name: str, title: str = "") -> AgentSession:
        session_id = uuid.uuid4().hex
        now = self._now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_sessions (id, project_name, title, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, project_name, title, "active", now, now),
            )
        session = self.get_session(session_id)
        if session is None:
            raise RuntimeError("failed to load created session")
        return session

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, project_name, title, status, created_at, updated_at
                FROM agent_sessions
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return self._to_session(row)

    def list_sessions(
        self,
        project_name: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentSession]:
        clauses: list[str] = []
        params: list[object] = []

        if project_name:
            clauses.append("project_name = ?")
            params.append(project_name)
        if status:
            clauses.append("status = ?")
            params.append(status)

        query = """
            SELECT id, project_name, title, status, created_at, updated_at
            FROM agent_sessions
        """
        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([max(1, limit), max(0, offset)])

        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        return [self._to_session(row) for row in rows]

    def update_session_status(self, session_id: str, status: SessionStatus) -> bool:
        now = self._now()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE agent_sessions
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, now, session_id),
            )
        return cursor.rowcount > 0

    def archive_session(self, session_id: str) -> bool:
        if self.update_session_status(session_id, "archived"):
            return True
        return self.get_session(session_id) is not None

    def update_session_title(self, session_id: str, title: str) -> bool:
        now = self._now()
        normalized = title.strip()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE agent_sessions
                SET title = ?, updated_at = ?
                WHERE id = ?
                """,
                (normalized, now, session_id),
            )
        return cursor.rowcount > 0

    def delete_session(self, session_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                DELETE FROM agent_sessions
                WHERE id = ?
                """,
                (session_id,),
            )
        return cursor.rowcount > 0

    def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        event_type: MessageEventType = "message",
    ) -> AgentMessage:
        text = content.strip()
        if not text:
            raise ValueError("message content cannot be empty")

        now = self._now()
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO agent_messages (session_id, role, content, event_type, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (session_id, role, text, event_type, now),
                )
                conn.execute(
                    """
                    UPDATE agent_sessions
                    SET updated_at = ?
                    WHERE id = ?
                    """,
                    (now, session_id),
                )
                row = conn.execute(
                    """
                    SELECT id, session_id, role, content, event_type, created_at
                    FROM agent_messages
                    WHERE id = ?
                    """,
                    (cursor.lastrowid,),
                ).fetchone()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"invalid session id: {session_id}") from exc

        if row is None:
            raise RuntimeError("failed to load inserted message")
        return self._to_message(row)

    def list_messages(self, session_id: str, limit: int = 200) -> list[AgentMessage]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, session_id, role, content, event_type, created_at
                FROM agent_messages
                WHERE session_id = ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (session_id, max(1, limit)),
            ).fetchall()
        return [self._to_message(row) for row in rows]
