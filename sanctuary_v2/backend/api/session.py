from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from sanctuary_v2.backend.core.database import get_db
from sanctuary_v2.backend.models.session import Session as SessionModel
from sanctuary_v2.backend.schemas.session import SessionStartResponse, SessionEndRequest, SessionEndResponse
from sanctuary_v2.backend.services.auth import get_current_user


router = APIRouter()


@router.post("/start", response_model=SessionStartResponse)
async def start_session(
    current_user=Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db),
):
    session = SessionModel(user_id=current_user.id)
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    return SessionStartResponse(session_id=session.id, started_at=session.started_at)


@router.post("/end", response_model=SessionEndResponse)
async def end_session(
    payload: SessionEndRequest,
    current_user=Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db),
):
    session = await db_session.get(SessionModel, payload.session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session.status = "ended"
    session.ended_at = datetime.utcnow()
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    return SessionEndResponse(
        session_id=session.id,
        ended_at=session.ended_at,
        status=session.status,
    )
