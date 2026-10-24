from datetime import datetime
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sanctuary_v2.backend.models.pwm.entity import Entity


class EntityRegistry:
    async def get_by_placeholder_id(
        self,
        user_id: str,
        placeholder_id: str,
        db_session: AsyncSession,
    ) -> Optional[Entity]:
        result = await db_session.execute(
            select(Entity).where(
                Entity.user_id == user_id,
                Entity.placeholder_id == placeholder_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_surface_form(
        self,
        user_id: str,
        entity_type: str,
        surface_form: str,
        db_session: AsyncSession,
    ) -> Optional[Entity]:
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

    async def list_entities(self, user_id: str, db_session: AsyncSession) -> List[Entity]:
        result = await db_session.execute(
            select(Entity).where(Entity.user_id == user_id)
        )
        return result.scalars().all()

    async def create_entity(
        self,
        user_id: str,
        placeholder_id: str,
        entity_type: str,
        surface_form: str,
        role_tag: str,
        session_id: Optional[str],
        db_session: AsyncSession,
    ) -> Entity:
        session_appearances = [session_id] if session_id else []

        entity = Entity(
            user_id=user_id,
            placeholder_id=placeholder_id,
            entity_type=entity_type,
            role_tag=role_tag or "unknown",
            surface_forms=[surface_form] if surface_form else [],
            mention_frequency=1,
            session_appearances=session_appearances,
            last_seen=datetime.utcnow(),
        )
        db_session.add(entity)
        await db_session.commit()
        await db_session.refresh(entity)
        return entity

    async def add_surface_form(
        self,
        entity: Entity,
        surface_form: str,
        db_session: AsyncSession,
    ) -> Entity:
        if not surface_form:
            return entity

        forms = list(entity.surface_forms or [])
        if surface_form not in forms:
            forms.append(surface_form)
            entity.surface_forms = forms
            entity.updated_at = datetime.utcnow()
            db_session.add(entity)
            await db_session.commit()
            await db_session.refresh(entity)

        return entity

    async def increment_mentions(
        self,
        entity: Entity,
        session_id: Optional[str],
        db_session: AsyncSession,
    ) -> Entity:
        entity.mention_frequency = (entity.mention_frequency or 0) + 1
        entity.last_seen = datetime.utcnow()

        appearances = list(entity.session_appearances or [])
        if session_id and session_id not in appearances:
            appearances.append(session_id)
            entity.session_appearances = appearances

        entity.updated_at = datetime.utcnow()
        db_session.add(entity)
        await db_session.commit()
        await db_session.refresh(entity)
        return entity
