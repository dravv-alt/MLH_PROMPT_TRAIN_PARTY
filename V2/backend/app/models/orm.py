from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func, Boolean, LargeBinary, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.db import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    turns: Mapped[list["ChatTurn"]] = relationship(
        "ChatTurn",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class ChatTurn(Base):
    __tablename__ = "chat_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)

    stripped_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    narrative_structure: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped[ChatSession] = relationship("ChatSession", back_populates="turns")

    __table_args__ = (
        UniqueConstraint("session_id", "turn_index", name="uq_chat_turns_session_turn_index"),
    )


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    session_id: Mapped[str] = mapped_column(String(32), index=True)

    selected_turn_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    reasoning_labels: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    entry_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    user_reflection_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_snapshot: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NLPState(Base):
    __tablename__ = "nlp_session_states"
    session_id: Mapped[str] = mapped_column(String(32), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    schema_version: Mapped[str] = mapped_column(String(64), default="sanctuary.nlp.v1")
    snapshot: Mapped[dict] = mapped_column(JSON, default=dict)


class NLPRecord(Base):
    __tablename__ = "nlp_analysis_records"
    turn_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_turns.id", ondelete="CASCADE"), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(32), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    request_id: Mapped[str] = mapped_column(String(36))
    input_digest: Mapped[str] = mapped_column(String(64))
    schema_version: Mapped[str] = mapped_column(String(64), default="sanctuary.nlp.v1")
    analysis: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("user_id", "request_id", name="uq_nlp_request"),)


class NLPTopic(Base):
    __tablename__ = "nlp_topics"
    session_id: Mapped[str] = mapped_column(String(32), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), primary_key=True)
    topic_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(64), default="sanctuary.nlp.v1")
    centroid_sum: Mapped[dict] = mapped_column(JSON)
    count: Mapped[int] = mapped_column(Integer)


class PWMState(Base):
    __tablename__ = 'pwm_world_states'
    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    schema_version: Mapped[str] = mapped_column(String(64), default='pwm.v1')
    world: Mapped[dict] = mapped_column(JSON, default=dict)


class NeuralMemoryState(Base):
    __tablename__ = 'neural_memory_states'
    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    generation: Mapped[str] = mapped_column(String(36))
    index_revision: Mapped[int] = mapped_column(Integer, default=0)
    share_history: Mapped[bool] = mapped_column(Boolean, default=False)
    preference_revision: Mapped[int] = mapped_column(Integer, default=0)


class LocalProcessingPreference(Base):
    __tablename__ = 'local_processing_preferences'
    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    process_unredacted: Mapped[bool] = mapped_column(Boolean, default=False)


class LocalMemoryPreference(Base):
    __tablename__ = 'local_memory_preferences'
    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    store_unredacted: Mapped[bool] = mapped_column(Boolean, default=False)


class LocalRawTurn(Base):
    __tablename__ = 'local_raw_turns'
    turn_id: Mapped[int] = mapped_column(Integer, ForeignKey('chat_turns.id', ondelete='CASCADE'), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    session_id: Mapped[str] = mapped_column(String(32), index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    offset_map: Mapped[list] = mapped_column(JSON, default=list)
    lexical_vector: Mapped[dict] = mapped_column(JSON, default=dict)


class SceneEmbedding(Base):
    __tablename__ = 'neural_scene_embeddings'
    turn_id: Mapped[int] = mapped_column(Integer, ForeignKey('chat_turns.id', ondelete='CASCADE'), primary_key=True)
    version: Mapped[str] = mapped_column(String(160), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    generation: Mapped[str] = mapped_column(String(36))
    scene_id: Mapped[str] = mapped_column(String(32))
    input_hash: Mapped[str] = mapped_column(String(64))
    dimension: Mapped[int] = mapped_column(Integer, default=384)
    pooled: Mapped[bytes] = mapped_column(LargeBinary)
    windows: Mapped[bytes] = mapped_column(LargeBinary)
    spans: Mapped[list] = mapped_column(JSON)


class NeuralJob(Base):
    __tablename__ = 'neural_jobs'
    turn_id: Mapped[int] = mapped_column(Integer, ForeignKey('chat_turns.id', ondelete='CASCADE'), primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), primary_key=True)
    version: Mapped[str] = mapped_column(String(160), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    generation: Mapped[str] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(20), default='pending', index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    due: Mapped[float] = mapped_column(Float, default=0)
    lease: Mapped[float] = mapped_column(Float, default=0)
    lease_token: Mapped[str | None] = mapped_column(String(36), nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class CalendarJournalEntry(Base):
    __tablename__ = 'calendar_journal_entries'
    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    entry_date: Mapped[str] = mapped_column(String(10), primary_key=True)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
