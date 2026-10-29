import os
from typing import Annotated
from datetime import date
from app.models.schemas import CalendarJournalRequest

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    DiagnosticMapResponse,
    ThreadsResponse,
    ThreadActionResponse,
    RejectedCandidatesResponse,
    CorrectionRequest,
    CorrectionResponse,
    MemoryReviewRequest,
    MemorySearchRequest,
    NeuralPreferencesRequest,
    EmergencyResource,
    JournalCreateRequest,
    JournalDeleteResponse,
    JournalEntryResponse,
    JournalListResponse,
    JournalSuggestRequest,
    JournalSuggestResponse,
    JournalUpdateRequest,
    SessionDeleteResponse,
    SessionTurn,
    SessionTurnsResponse,
)
from app.models.db import check_database_connection, get_database_backend
from app.services.clerk_auth import ClerkAuthError, verify_clerk_token
from app.services.journal_service import JournalService
from app.services.narrative import AIResponseUnavailableError, build_reflection
from app.services.privacy import get_ner_backend_mode
from app.services.session_state import SessionStateStore
from app.services.nlp_service import get_nlp_service

router = APIRouter()


def get_session_store(request: Request) -> SessionStateStore:
    return request.app.state.session_state


def get_journal_service(request: Request) -> JournalService:
    return request.app.state.journal_service


def _to_journal_entry_response(entry) -> JournalEntryResponse:
    return JournalEntryResponse(
        entry_id=entry.id,
        session_id=entry.session_id,
        selected_turn_ids=list(entry.selected_turn_ids),
        reasoning_labels=list(entry.reasoning_labels),
        entry_title=entry.entry_title,
        user_reflection_text=entry.user_reflection_text,
        summary_snapshot=entry.summary_snapshot,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        if os.getenv("ENVIRONMENT") == "local":
            return "dev_local_user"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "auth_unauthorized", "message": "Missing bearer token."},
        )

    token = authorization.replace("Bearer ", "", 1)

    if os.getenv("ENVIRONMENT") == "local" and (token.startswith("dev") or token in {"test_token", "local", "dev_local_user"}):
        return token

    try:
        payload = verify_clerk_token(token)
        clerk_user_id = payload.get("sub")
        if clerk_user_id:
            return clerk_user_id
    except ClerkAuthError as exc:
        if os.getenv("ENVIRONMENT") == "local":
            return "dev_local_user"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "auth_unauthorized", "message": "Invalid or expired token."},
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "auth_unauthorized", "message": "Invalid or expired token."},
    )


@router.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Sanctuary V2 API",
        "tagline": "Reflective conversation, not therapy or diagnosis.",
        "privacy": "Identity-stripped narrative processing enabled.",
    }


@router.get("/health")
def health() -> dict[str, str]:
    db_ok = check_database_connection()
    return {
        "status": "ok",
        "service": "sanctuary-v2-backend",
        "privacy_ner_backend": get_ner_backend_mode(),
        "language_alignment_layer": "enabled",
        "generation_scoring_layer": "enabled",
        "database_backend": get_database_backend(),
        "database_status": "ok" if db_ok else "error",
    }


@router.get("/auth/me")
def me(user_id: Annotated[str, Depends(get_current_user_id)]) -> dict[str, str]:
    return {"user_id": user_id}


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    session_store: Annotated[SessionStateStore, Depends(get_session_store)],
) -> ChatResponse:
    return ChatResponse(**get_nlp_service().chat(user_id, payload))


@router.get('/sessions')
def list_sessions(user_id: Annotated[str, Depends(get_current_user_id)], limit: int = 100, offset: int = 0):
    from sqlalchemy import select, func
    from app.models.orm import ChatSession, ChatTurn
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    service = get_nlp_service()
    with service.factory() as db:
        count = db.scalar(select(func.count()).select_from(ChatSession).where(ChatSession.user_id == user_id))
        rows = db.execute(select(ChatSession, func.count(ChatTurn.id)).outerjoin(ChatTurn, ChatTurn.session_id == ChatSession.session_id).where(ChatSession.user_id == user_id).group_by(ChatSession.id).order_by(ChatSession.updated_at.desc(), ChatSession.id.desc()).offset(offset).limit(limit)).all()
        return {'sessions': [{'session_id': row.session_id, 'created_at': row.created_at.isoformat(), 'updated_at': row.updated_at.isoformat(), 'turn_count': turns} for row, turns in rows], 'total': count, 'offset': offset, 'limit': limit}


@router.get('/nlp/generation/status')
def generation_status(user_id: Annotated[str, Depends(get_current_user_id)]):
    from app.services.local_generation import LOCAL_GENERATOR
    from app.services.hosted_generation import hosted_status
    local = LOCAL_GENERATOR.get_capabilities()
    local.pop('model_path', None)
    return {'local': local, 'hosted': hosted_status(), 'default_provider': 'local'}


@router.post("/nlp/analyze", response_model=AnalyzeResponse)
def preview_analysis(payload: AnalyzeRequest, user_id: Annotated[str, Depends(get_current_user_id)]) -> AnalyzeResponse:
    return AnalyzeResponse(**get_nlp_service().preview(user_id, payload.text, payload.session_id, payload.mathematical_profile))


@router.post('/nlp/experiments')
def algorithm_experiments(payload: AnalyzeRequest, user_id: Annotated[str, Depends(get_current_user_id)]):
    return get_nlp_service().experiments(user_id, payload.text, payload.session_id)


@router.get('/nlp/memory')
def world_memory(user_id: Annotated[str, Depends(get_current_user_id)]):
    return get_nlp_service().world(user_id)


@router.post('/nlp/memory/search')
def memory_search(payload: 'MemorySearchRequest',user_id: Annotated[str, Depends(get_current_user_id)]):
    return get_nlp_service().search_memory(user_id,payload.query,payload.limit)


@router.get('/nlp/turns/{turn_id}/classification')
def turn_classification(turn_id: int,user_id: Annotated[str, Depends(get_current_user_id)]):
    return get_nlp_service().neural.classification(user_id,turn_id)


@router.post('/nlp/classification/preview')
def classification_preview(payload: AnalyzeRequest,user_id: Annotated[str, Depends(get_current_user_id)]):
    return get_nlp_service().classification_preview(user_id,payload.text,payload.session_id)


@router.get('/nlp/preferences')
def neural_preferences(user_id: Annotated[str, Depends(get_current_user_id)]):
    return get_nlp_service().neural.preferences(user_id)


@router.patch('/nlp/preferences')
def patch_neural_preferences(payload: 'NeuralPreferencesRequest',user_id: Annotated[str, Depends(get_current_user_id)]):
    if payload.share_history_with_provider is None and payload.process_local_unredacted is None and payload.store_local_unredacted_memory is None:
        raise HTTPException(status_code=422, detail={'code':'empty_preferences','message':'Provide at least one preference.'})
    return get_nlp_service().neural.preferences(
        user_id,
        payload.share_history_with_provider,
        payload.process_local_unredacted,
        payload.store_local_unredacted_memory,
    )


@router.get('/nlp/neural/status')
def neural_status(user_id: Annotated[str, Depends(get_current_user_id)]):
    from app.services.neural_runtime import EMBEDDING,NLI,manifest
    service=get_nlp_service();world=service.world(user_id)
    from app.models.orm import SceneEmbedding
    from sqlalchemy import func,select
    meta=service.neural.metadata(user_id)
    from app.services.neural_runtime import version
    with service.factory() as db:
        indexed=db.scalar(select(func.count()).select_from(SceneEmbedding).where(SceneEmbedding.user_id==user_id,SceneEmbedding.generation==meta['generation'],SceneEmbedding.version==version('embedding')))
    return {'embedding':EMBEDDING.state,'nli':NLI.state,'effective_threads':{'embedding':EMBEDDING.effective_threads,'nli':NLI.effective_threads},'thread_fallback':{'embedding':EMBEDDING.thread_fallback,'nli':NLI.thread_fallback},'versions':manifest().get('versions',{}),'local_memory_mode':'unredacted' if meta.get('store_local_unredacted_memory') else 'redacted','coverage':{'active_scenes':len(world['scenes']),'indexed_scenes':indexed},'evaluation':'DATA_BLOCKED_NO_HUMAN_JUDGMENTS'}


@router.post('/nlp/neural/backfill')
def coordinated_backfill(user_id: Annotated[str, Depends(get_current_user_id)]):
    return get_nlp_service().neural.queue_backfill(user_id)


@router.get('/nlp/memory/graph')
def world_graph(user_id: Annotated[str, Depends(get_current_user_id)]):
    from app.services.memory_tools import memory_graph
    snapshot,_=get_nlp_service().load(user_id,None)
    return memory_graph(snapshot.get('world'))


@router.patch('/nlp/memory/unresolved/{node_id}')
def review_memory_item(node_id: str, payload: MemoryReviewRequest, user_id: Annotated[str, Depends(get_current_user_id)]):
    return get_nlp_service().review_unresolved(user_id,node_id,payload.status,payload.expected_revision)


@router.delete('/nlp/memory')
def delete_world_memory(user_id: Annotated[str, Depends(get_current_user_id)]):
    from app.models.orm import PWMState, NLPState
    from sqlalchemy import delete, select
    service=get_nlp_service()
    with service.factory() as db:
        from app.services.neural_memory import begin
        begin(db)
        service.neural.reset(db,user_id)
        db.execute(delete(PWMState).where(PWMState.user_id==user_id))
        # Remove cached cross-session aliases so future analysis cannot resurrect them.
        states=db.scalars(select(NLPState).where(NLPState.user_id==user_id)).all()
        for state in states:
            state.snapshot={**state.snapshot,'entities':[],'world':{},'hobbs_history':[],'centering_trace':[],'world_revision':0}
            state.revision+=1
        db.commit()
    return {'deleted':True}


@router.get("/sessions/{session_id}/analysis")
def analysis_history(session_id: str, user_id: Annotated[str, Depends(get_current_user_id)]):
    return get_nlp_service().history(user_id, session_id)


@router.get("/nlp/sessions/{session_id}/diagnostic_map", response_model=DiagnosticMapResponse)
def session_diagnostic_map(session_id: str, user_id: Annotated[str, Depends(get_current_user_id)]) -> DiagnosticMapResponse:
    """T5.2 Diagnostic map view: clause annotations, relations, hedges, gaps, and moves."""
    return DiagnosticMapResponse(**get_nlp_service().diagnostic_map(user_id=user_id, session_id=session_id))


@router.post("/nlp/diagnostic_map", response_model=DiagnosticMapResponse)
def preview_diagnostic_map(payload: AnalyzeRequest, user_id: Annotated[str, Depends(get_current_user_id)]) -> DiagnosticMapResponse:
    """T5.2 Diagnostic map preview: returns map view for text input with LLM off (Invariant 2)."""
    return DiagnosticMapResponse(**get_nlp_service().diagnostic_map(user_id=user_id, text_value=payload.text))


@router.get("/nlp/sessions/{session_id}/threads", response_model=ThreadsResponse)
def session_threads(session_id: str, user_id: Annotated[str, Depends(get_current_user_id)]) -> ThreadsResponse:
    """T5.3 Open-threads panel: returns active, resolved, and historical QUD threads."""
    return ThreadsResponse(**get_nlp_service().threads(user_id=user_id, session_id=session_id))


@router.post("/nlp/sessions/{session_id}/threads/{gap_id}/dismiss", response_model=ThreadActionResponse)
def dismiss_thread(session_id: str, gap_id: str, user_id: Annotated[str, Depends(get_current_user_id)]) -> ThreadActionResponse:
    """T5.3 Dismiss thread: marks QUD thread as deflected and updates session state."""
    return ThreadActionResponse(**get_nlp_service().dismiss_thread(user_id=user_id, session_id=session_id, gap_id=gap_id))


@router.post("/nlp/sessions/{session_id}/threads/{gap_id}/prioritize", response_model=ThreadActionResponse)
def prioritize_thread(session_id: str, gap_id: str, user_id: Annotated[str, Depends(get_current_user_id)]) -> ThreadActionResponse:
    """T5.3 Prioritize thread: sets QUD thread as open, bumps recurrence, and refreshes touch turn."""
    return ThreadActionResponse(**get_nlp_service().prioritize_thread(user_id=user_id, session_id=session_id, gap_id=gap_id))


@router.get("/nlp/sessions/{session_id}/rejected_candidates", response_model=RejectedCandidatesResponse)
def session_rejected_candidates(session_id: str, user_id: Annotated[str, Depends(get_current_user_id)]) -> RejectedCandidatesResponse:
    """T5.4 Rejected-candidates view: returns candidates rejected by presupposition filter across session."""
    return RejectedCandidatesResponse(**get_nlp_service().rejected_candidates(user_id=user_id, session_id=session_id))


@router.get("/nlp/turns/{turn_id}/rejected_candidates", response_model=RejectedCandidatesResponse)
def turn_rejected_candidates(turn_id: int, user_id: Annotated[str, Depends(get_current_user_id)]) -> RejectedCandidatesResponse:
    """T5.4 Rejected-candidates view: returns candidates rejected for a specific turn."""
    return RejectedCandidatesResponse(**get_nlp_service().rejected_candidates(user_id=user_id, turn_id=turn_id))


@router.patch("/nlp/analysis/correction", response_model=CorrectionResponse)
def user_correction(payload: CorrectionRequest, user_id: Annotated[str, Depends(get_current_user_id)]) -> CorrectionResponse:
    """T5.5 User correction: logs feedback/correction on detected gap and updates QUD supersessions."""
    return CorrectionResponse(**get_nlp_service().apply_correction(user_id=user_id, payload=payload))


@router.get("/sessions/{session_id}/turns", response_model=SessionTurnsResponse)
def get_session_turns(
    session_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    session_store: Annotated[SessionStateStore, Depends(get_session_store)],
) -> SessionTurnsResponse:
    if not session_store.session_exists(user_id=user_id, session_id=session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Session not found."},
        )

    turns = session_store.get_turns(user_id=user_id, session_id=session_id)
    session_turns: list[SessionTurn] = []
    for turn in turns:
        session_turns.append(
            SessionTurn(
                turn_id=turn["turn_id"],
                turn_index=turn["turn_index"],
                identity_stripped_input=turn["identity_stripped_input"],
                response_text=turn["response_text"],
                safety_mode=turn["safety_mode"],
                narrative_structure=turn["narrative_structure"],
                created_at=turn["created_at"],
            )
        )

    return SessionTurnsResponse(session_id=session_id, turns=session_turns)


@router.delete("/sessions/{session_id}", response_model=SessionDeleteResponse)
def delete_session(
    session_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    session_store: Annotated[SessionStateStore, Depends(get_session_store)],
) -> SessionDeleteResponse:
    deleted = get_nlp_service().delete_session(user_id=user_id, session_id=session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Session not found."},
        )

    return SessionDeleteResponse(session_id=session_id, deleted=True)


@router.post("/journal/suggest", response_model=JournalSuggestResponse)
def suggest_journal_entries(
    payload: JournalSuggestRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    journal_service: Annotated[JournalService, Depends(get_journal_service)],
) -> JournalSuggestResponse:
    if not journal_service.session_exists(user_id=user_id, session_id=payload.session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Session not found."},
        )

    turn_ids, labels = journal_service.suggest(
        user_id=user_id,
        session_id=payload.session_id,
        max_suggestions=payload.max_suggestions,
    )
    return JournalSuggestResponse(
        session_id=payload.session_id,
        suggested_turn_ids=turn_ids,
        reasoning_labels=labels,
    )


@router.get('/journal/calendar')
def calendar_entries(user_id: Annotated[str, Depends(get_current_user_id)]):
    from sqlalchemy import select
    from app.models.orm import CalendarJournalEntry
    with get_nlp_service().factory() as db:
        rows=db.scalars(select(CalendarJournalEntry).where(CalendarJournalEntry.user_id==user_id).order_by(CalendarJournalEntry.entry_date.desc())).all()
        return {'entries':{row.entry_date:{**row.content,'date':row.entry_date,'updatedAt':row.updated_at.isoformat()} for row in rows}}


@router.put('/journal/calendar/{entry_date}')
def save_calendar_entry(entry_date: date, payload: CalendarJournalRequest, user_id: Annotated[str, Depends(get_current_user_id)]):
    from app.models.orm import CalendarJournalEntry, utc_now
    from app.services.privacy import strip_identifiers
    content=payload.model_dump()
    content['title']=strip_identifiers(content['title'])
    content['text']=strip_identifiers(content['text'])
    key=entry_date.isoformat()
    with get_nlp_service().factory() as db:
        row=db.get(CalendarJournalEntry,(user_id,key))
        if row is None:
            row=CalendarJournalEntry(user_id=user_id,entry_date=key,content=content);db.add(row)
        else:row.content=content;row.updated_at=utc_now()
        db.commit()
        return {'entry':{**row.content,'date':key,'updatedAt':row.updated_at.isoformat()},'storage':'redacted_backend'}


@router.delete('/journal/calendar/{entry_date}')
def delete_calendar_entry(entry_date: date, user_id: Annotated[str, Depends(get_current_user_id)]):
    from app.models.orm import CalendarJournalEntry
    with get_nlp_service().factory() as db:
        row=db.get(CalendarJournalEntry,(user_id,entry_date.isoformat()))
        if row is None:raise HTTPException(404,detail={'code':'not_found','message':'Journal entry not found.'})
        db.delete(row);db.commit();return {'deleted':True}


@router.post("/journal/create", response_model=JournalEntryResponse, status_code=status.HTTP_201_CREATED)
def create_journal_entry(
    payload: JournalCreateRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    journal_service: Annotated[JournalService, Depends(get_journal_service)],
) -> JournalEntryResponse:
    try:
        entry = journal_service.create_entry(
            user_id=user_id,
            session_id=payload.session_id,
            selected_turn_ids=payload.selected_turn_ids,
            entry_title=payload.entry_title,
            user_reflection_text=payload.user_reflection_text,
        )
    except ValueError as exc:
        message = str(exc)
        if message == "Session not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": message},
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "validation_error", "message": message},
        ) from exc

    return _to_journal_entry_response(entry)


@router.get("/journal", response_model=JournalListResponse)
def list_journal_entries(
    user_id: Annotated[str, Depends(get_current_user_id)],
    journal_service: Annotated[JournalService, Depends(get_journal_service)],
) -> JournalListResponse:
    entries = journal_service.list_entries(user_id=user_id)
    return JournalListResponse(entries=[_to_journal_entry_response(entry) for entry in entries])


@router.get("/journal/{entry_id}", response_model=JournalEntryResponse)
def get_journal_entry(
    entry_id: int,
    user_id: Annotated[str, Depends(get_current_user_id)],
    journal_service: Annotated[JournalService, Depends(get_journal_service)],
) -> JournalEntryResponse:
    entry = journal_service.get_entry(user_id=user_id, entry_id=entry_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Journal entry not found."},
        )

    return _to_journal_entry_response(entry)


@router.patch("/journal/{entry_id}", response_model=JournalEntryResponse)
def update_journal_entry(
    entry_id: int,
    payload: JournalUpdateRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    journal_service: Annotated[JournalService, Depends(get_journal_service)],
) -> JournalEntryResponse:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "validation_error", "message": "At least one field must be provided."},
        )

    entry = journal_service.update_entry(
        user_id=user_id,
        entry_id=entry_id,
        entry_title=updates.get("entry_title"),
        user_reflection_text=updates.get("user_reflection_text"),
        update_title="entry_title" in updates,
        update_reflection="user_reflection_text" in updates,
    )
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Journal entry not found."},
        )

    return _to_journal_entry_response(entry)


@router.delete("/journal/{entry_id}", response_model=JournalDeleteResponse)
def delete_journal_entry(
    entry_id: int,
    user_id: Annotated[str, Depends(get_current_user_id)],
    journal_service: Annotated[JournalService, Depends(get_journal_service)],
) -> JournalDeleteResponse:
    deleted = journal_service.delete_entry(user_id=user_id, entry_id=entry_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Journal entry not found."},
        )

    return JournalDeleteResponse(entry_id=entry_id, deleted=True)


@router.get("/resources/emergency", response_model=list[EmergencyResource])
def emergency_resources() -> list[EmergencyResource]:
    return [
        EmergencyResource(
            label="988 Suicide and Crisis Lifeline",
            region="United States",
            contact="Call or text 988",
            type="hotline",
        ),
        EmergencyResource(
            label="Crisis Text Line",
            region="US/UK/CA/IE",
            contact="Text HOME to 741741 (US)",
            type="text",
        ),
        EmergencyResource(
            label="International Hotline Directory",
            region="Global",
            contact="https://findahelpline.com",
            type="directory",
        ),
    ]
