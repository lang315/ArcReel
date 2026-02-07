"""
Assistant chat/session APIs.
"""

from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from webui.server.agent_runtime.service import AssistantService

router = APIRouter()

project_root = Path(__file__).parent.parent.parent.parent
assistant_service = AssistantService(project_root=project_root)


class CreateSessionRequest(BaseModel):
    project_name: str = Field(min_length=1)
    title: Optional[str] = ""


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1)
    stream: bool = False
    client_message_id: Optional[str] = None


class UpdateSessionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)


@router.post("/assistant/sessions")
async def create_session(req: CreateSessionRequest):
    try:
        session = assistant_service.create_session(req.project_name, req.title or "")
        return {"success": True, "session": session.model_dump()}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"项目 '{req.project_name}' 不存在")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/assistant/sessions")
async def list_sessions(
    project_name: Optional[str] = None,
    status: Optional[Literal["active", "archived", "error"]] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        sessions = assistant_service.list_sessions(
            project_name=project_name, status=status, limit=limit, offset=offset
        )
        return {"sessions": [session.model_dump() for session in sessions]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/assistant/sessions/{session_id}/messages")
async def list_session_messages(
    session_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
):
    try:
        messages = assistant_service.list_messages(session_id=session_id, limit=limit)
        return {"messages": [message.model_dump() for message in messages]}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"会话 '{session_id}' 不存在")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/assistant/sessions/{session_id}")
async def update_session(session_id: str, req: UpdateSessionRequest):
    try:
        session = assistant_service.update_session_title(session_id=session_id, title=req.title)
        if session is None:
            raise HTTPException(status_code=404, detail=f"会话 '{session_id}' 不存在")
        return {"success": True, "session": session.model_dump()}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/assistant/sessions/{session_id}")
async def delete_session(session_id: str):
    try:
        deleted = await assistant_service.delete_session(session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"会话 '{session_id}' 不存在")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/assistant/skills")
async def list_skills(project_name: Optional[str] = None):
    try:
        skills = assistant_service.list_available_skills(project_name=project_name)
        return {"skills": skills}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"项目 '{project_name}' 不存在")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/assistant/sessions/{session_id}/messages")
async def send_message(session_id: str, req: SendMessageRequest):
    try:
        if req.stream:
            result = await assistant_service.start_stream_request(
                session_id=session_id,
                content=req.content,
            )
            stream_url = (
                f"/api/v1/assistant/sessions/{session_id}/streams/{result['request_id']}"
            )
            return {
                "success": True,
                "session": result["session"].model_dump() if result["session"] else None,
                "session_id": session_id,
                "request_id": result["request_id"],
                "stream_url": stream_url,
                "user_message_id": result["user_message"].id,
            }

        result = await assistant_service.send_user_message(
            session_id=session_id, content=req.content
        )
        return {
            "success": True,
            "session": result["session"].model_dump() if result["session"] else None,
            "assistant_message": result["assistant_message"].model_dump(),
            "action": result["action"],
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"会话 '{session_id}' 不存在")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/assistant/sessions/{session_id}/streams/{request_id}")
async def stream_message_events(session_id: str, request_id: str):
    try:
        if not await assistant_service.has_stream_request(
            session_id=session_id,
            request_id=request_id,
        ):
            raise HTTPException(status_code=404, detail=f"流请求 '{request_id}' 不存在")

        stream = assistant_service.stream_events(
            session_id=session_id,
            request_id=request_id,
        )
        return StreamingResponse(
            stream,
            media_type="text/event-stream; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/assistant/sessions/{session_id}/archive")
async def archive_session(session_id: str):
    try:
        archived = assistant_service.archive_session(session_id)
        if not archived:
            raise HTTPException(status_code=404, detail=f"会话 '{session_id}' 不存在")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
