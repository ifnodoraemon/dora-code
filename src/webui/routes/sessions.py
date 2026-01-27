"""
Sessions API Routes

Manages chat sessions.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from src.core.session import SessionManager

router = APIRouter()


class SessionResponse(BaseModel):
    id: str
    name: str | None
    message_count: int
    updated_at: float


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(project: str = "default", limit: int = 50):
    """List recent sessions."""
    mgr = SessionManager()
    sessions = mgr.list_sessions(project=project, limit=limit)
    
    return [
        SessionResponse(
            id=s.id,
            name=s.name,
            message_count=s.message_count,
            updated_at=s.updated_at
        )
        for s in sessions
    ]


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Get session details."""
    mgr = SessionManager()
    session = mgr.resume_session(session_id)
    if not session:
        return {"error": "Session not found"}
    
    return {
        "id": session.metadata.id,
        "name": session.metadata.name,
        "messages": [m for m in session.messages]
    }
