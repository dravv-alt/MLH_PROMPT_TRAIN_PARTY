from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sanctuary_v2.backend.models.pwm.entity import Entity


class CoreferenceResolver:
    """
    Phase 1: Stage 1 exact surface-form match only.
    Later stages (semantic/structural) are deferred to Phase 2+.
    """

    EXACT_MATCH_CONFIDENCE = 1.0
    ACCEPTANCE_THRESHOLD = 0.75

    async def resolve(
        self,
        surface_form: str,
        entity_type: str,
        context_distilled: str,
        user_id: str,
        db_session: AsyncSession,
    ) -> Optional[Entity]:
        """
        Stage 1: exact string match in entity.surface_forms.
        Returns the first match above acceptance threshold.
        """
        normalized = surface_form.strip().lower()
        if not normalized:
            return None

        result = await db_session.execute(
            select(Entity).where(
                Entity.user_id == user_id,
                Entity.entity_type == entity_type,
            )
        )
        entities = result.scalars().all()

        for entity in entities:
            for form in entity.surface_forms or []:
                if form.strip().lower() == normalized:
                    return entity

        return None
