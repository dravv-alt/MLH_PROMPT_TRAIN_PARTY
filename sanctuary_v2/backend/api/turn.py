"""
Turn endpoint — main pipeline entry point.

Server execution order (Phase 1 — PRD Section 8.3):
 1. Whisper STT if audio provided -> raw_text
 2. distiller.distill(raw_text) -> placeholder_map
 3. Coreference resolution + PWM entity registration
 4. dag_builder.extract(distilled_text, placeholder_map) -> narrative_structure
 5. LLM generate with behavioral spec
 6. Policy gate check (up to 2 attempts, then safe fallback)
 7. Placeholder restoration
 8. TTS synthesis
 9. Persist Turn + update Session
10. Return response
"""

import base64
import binascii
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from sanctuary_v2.backend.core.database import get_db
from sanctuary_v2.backend.core.narrative.dag_builder import DAGBuilder
from sanctuary_v2.backend.core.privacy.coreference import CoreferenceResolver
from sanctuary_v2.backend.core.privacy.distiller import PrivacyDistiller
from sanctuary_v2.backend.core.privacy.restorer import PlaceholderRestorer
from sanctuary_v2.backend.core.pwm.manager import PWMManager
from sanctuary_v2.backend.models.session import Session as SessionModel
from sanctuary_v2.backend.models.turn import Turn
from sanctuary_v2.backend.schemas.turn import TurnRequest, TurnResponse
from sanctuary_v2.backend.services.auth import get_current_user
from sanctuary_v2.backend.services.llm import LLMService
from sanctuary_v2.backend.services.policy_gate import PolicyGate
from sanctuary_v2.backend.services.stt import STTService
from sanctuary_v2.backend.services.tts import TTSService

logger = logging.getLogger(__name__)

router = APIRouter()

# PRD Section 7.14: safe fallback after 2 policy gate failures
SAFE_FALLBACK = "That sounds like it carries a lot. Tell me more."


@router.post("", response_model=TurnResponse)
async def create_turn(
    payload: TurnRequest,
    current_user=Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db),
):
    # ── Step 1: Resolve raw text (STT or direct text) ──────────────────
    session = await db_session.get(SessionModel, payload.session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found",
        )

    raw_text = None
    if payload.audio_base64:
        try:
            audio_bytes = base64.b64decode(payload.audio_base64)
        except binascii.Error as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid audio_base64",
            ) from exc
        raw_text = await STTService().transcribe(
            audio_bytes, payload.audio_filename or "audio.wav",
        )
    elif payload.text:
        raw_text = payload.text
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either text or audio_base64 is required",
        )

    # ── Step 2: Privacy distillation ───────────────────────────────────
    distiller = PrivacyDistiller()
    placeholder_map = await distiller.distill(raw_text, current_user.id, db_session)

    # ── Step 3: Coreference resolution + PWM entity registration ──────
    coref = CoreferenceResolver()
    pwm = PWMManager()

    for placeholder, surface in list(placeholder_map.entity_map.items()):
        entity_type = placeholder_map.entity_types.get(placeholder, "PERSON")
        entity = await coref.resolve(
            surface_form=surface,
            entity_type=entity_type,
            context_distilled=placeholder_map.distilled_text,
            user_id=current_user.id,
            db_session=db_session,
        )

        final_placeholder = placeholder
        if entity and entity.placeholder_id != placeholder:
            final_placeholder = entity.placeholder_id
            placeholder_map.entity_map[final_placeholder] = surface
            placeholder_map.entity_types[final_placeholder] = entity_type
            placeholder_map.reverse_map[surface] = final_placeholder
            placeholder_map.entity_map.pop(placeholder, None)
            placeholder_map.entity_types.pop(placeholder, None)
            placeholder_map.distilled_text = re.sub(
                rf"\b{re.escape(placeholder)}\b",
                final_placeholder,
                placeholder_map.distilled_text,
            )

        await pwm.register_entity(
            user_id=current_user.id,
            placeholder_id=final_placeholder,
            entity_type=entity_type,
            surface_form=surface,
            session_id=session.id,
            db_session=db_session,
        )

    # ── Step 4: NarrativeStructure extraction (Groq-powered) ──────────
    dag_builder = DAGBuilder()
    narrative = await dag_builder.extract(
        placeholder_map.distilled_text, placeholder_map,
    )

    # ── Step 5 + 6: LLM generation with policy gate (2-attempt cycle) ─
    behavioral_spec = (
        "STANDARD_REFLECTION: Reflect what the user shared with care. "
        "Be present. No diagnostic language. No advice. No identity claims."
    )

    llm = LLMService()
    policy_gate = PolicyGate()
    response_text = await llm.generate(
        placeholder_map.distilled_text, behavioral_spec,
    )

    is_safe, violations = policy_gate.check(response_text)
    if not is_safe:
        # Attempt 2: regenerate with stricter spec including the violation reasons
        violation_summary = "; ".join(violations[:5])  # cap to avoid huge prompts
        stricter_spec = (
            f"{behavioral_spec} "
            f"IMPORTANT: Your previous response violated these rules: "
            f"{violation_summary}. Do NOT repeat these violations."
        )
        logger.warning(
            "PolicyGate: attempt 1 failed (%d violations), regenerating",
            len(violations),
        )
        response_text = await llm.generate(
            placeholder_map.distilled_text, stricter_spec,
        )

        is_safe_2, violations_2 = policy_gate.check(response_text)
        if not is_safe_2:
            logger.warning(
                "PolicyGate: attempt 2 also failed (%d violations), using fallback",
                len(violations_2),
            )
            response_text = SAFE_FALLBACK

    # ── Step 7: Placeholder restoration ────────────────────────────────
    restored_text = PlaceholderRestorer().restore(response_text, placeholder_map)

    # ── Step 8: TTS synthesis (graceful failure) ───────────────────────
    try:
        audio_url = await TTSService().synthesize(restored_text)
    except Exception:
        audio_url = None

    # ── Step 9: Persist Turn + update Session ──────────────────────────
    turn = Turn(
        session_id=session.id,
        user_id=current_user.id,
        turn_index=(session.turn_count or 0) + 1,
        distilled_input=placeholder_map.distilled_text,
        narrative_structure_json=narrative.model_dump(),
        strategy_used="standard_reflection",
        winning_hypothesis="none",
        hypothesis_confidence=0.0,
        response_text=restored_text,
        response_audio_url=audio_url,
        vad_valence=None,
        vad_arousal=None,
        vad_dominance=None,
        depth_layer=None,
    )
    db_session.add(turn)

    session.turn_count = (session.turn_count or 0) + 1
    db_session.add(session)

    await db_session.commit()
    await db_session.refresh(turn)

    # ── Step 10: Return ────────────────────────────────────────────────
    return TurnResponse(
        turn_id=turn.id,
        response_text=restored_text,
        response_audio_url=audio_url,
        can_save_to_journal=True,
    )
