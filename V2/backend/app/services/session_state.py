import secrets

from sqlalchemy import func, select

from app.models.db import SessionLocal
from app.models.orm import ChatSession, ChatTurn, utc_now
from app.models.schemas import NarrativeStructure


class SessionStateStore:
    def __init__(self, session_factory=SessionLocal) -> None:
        self._session_factory = session_factory

    def session_exists(self, user_id: str, session_id: str) -> bool:
        with self._session_factory() as db:
            return (
                db.scalar(
                    select(ChatSession.id).where(
                        ChatSession.user_id == user_id,
                        ChatSession.session_id == session_id,
                    )
                )
                is not None
            )

    def resolve_session_id(self, user_id: str, requested_session_id: str | None) -> str:
        with self._session_factory() as db:
            if requested_session_id:
                existing = db.scalar(
                    select(ChatSession).where(
                        ChatSession.user_id == user_id,
                        ChatSession.session_id == requested_session_id,
                    )
                )
                if existing:
                    return requested_session_id

            while True:
                session_id = secrets.token_hex(8)
                collision = db.scalar(select(ChatSession.id).where(ChatSession.session_id == session_id))
                if collision is None:
                    break

            db.add(ChatSession(session_id=session_id, user_id=user_id, updated_at=utc_now()))
            db.commit()
            return session_id

    def get_history(self, user_id: str, session_id: str) -> list[NarrativeStructure]:
        with self._session_factory() as db:
            rows = db.scalars(
                select(ChatTurn)
                .where(
                    ChatTurn.user_id == user_id,
                    ChatTurn.session_id == session_id,
                )
                .order_by(ChatTurn.turn_index.desc())
                .limit(50)
            ).all()

        history: list[NarrativeStructure] = []
        for row in reversed(rows):
            try:
                history.append(NarrativeStructure.model_validate(row.narrative_structure))
            except Exception:
                # Keep serving chat even if a historical row is malformed.
                continue
        return history

    def get_turns(self, user_id: str, session_id: str) -> list[dict]:
        with self._session_factory() as db:
            rows = db.scalars(
                select(ChatTurn)
                .where(
                    ChatTurn.user_id == user_id,
                    ChatTurn.session_id == session_id,
                )
                .order_by(ChatTurn.turn_index.asc())
            ).all()

        return [
            {
                "turn_id": row.id,
                "turn_index": row.turn_index,
                "identity_stripped_input": row.stripped_input,
                "response_text": row.response_text,
                "safety_mode": row.safety_mode,
                "narrative_structure": row.narrative_structure,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    def delete_session(self, user_id: str, session_id: str) -> bool:
        with self._session_factory() as db:
            session = db.scalar(
                select(ChatSession).where(
                    ChatSession.user_id == user_id,
                    ChatSession.session_id == session_id,
                )
            )
            if session is None:
                return False

            db.delete(session)
            db.commit()
            return True

    def append_structure(
        self,
        user_id: str,
        session_id: str,
        structure: NarrativeStructure,
        stripped_input: str | None = None,
        response_text: str | None = None,
        safety_mode: str | None = None,
    ) -> None:
        with self._session_factory() as db:
            session = db.scalar(
                select(ChatSession).where(
                    ChatSession.user_id == user_id,
                    ChatSession.session_id == session_id,
                )
            )
            if session is None:
                session = ChatSession(session_id=session_id, user_id=user_id, updated_at=utc_now())
                db.add(session)
                db.flush()

            last_turn_index = db.scalar(
                select(func.max(ChatTurn.turn_index)).where(
                    ChatTurn.user_id == user_id,
                    ChatTurn.session_id == session_id,
                )
            )
            next_turn_index = (last_turn_index or 0) + 1

            db.add(
                ChatTurn(
                    user_id=user_id,
                    session_id=session_id,
                    turn_index=next_turn_index,
                    stripped_input=stripped_input,
                    response_text=response_text,
                    safety_mode=safety_mode,
                    narrative_structure=structure.model_dump(),
                )
            )
            session.updated_at = utc_now()
            db.commit()
