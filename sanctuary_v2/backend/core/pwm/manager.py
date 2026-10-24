from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from sanctuary_v2.backend.core.pwm.entity_registry import EntityRegistry
from sanctuary_v2.backend.models.pwm.entity import Entity


class PWMManager:
    def __init__(self, entity_registry: Optional[EntityRegistry] = None):
        self.entity_registry = entity_registry or EntityRegistry()

    async def register_entity(
        self,
        user_id: str,
        placeholder_id: str,
        entity_type: str,
        surface_form: str,
        session_id: Optional[str],
        db_session: AsyncSession,
        role_tag: str = "unknown",
    ) -> Entity:
        # Try placeholder first (consistent across sessions).
        entity = await self.entity_registry.get_by_placeholder_id(
            user_id=user_id,
            placeholder_id=placeholder_id,
            db_session=db_session,
        )

        # Fall back to exact surface match (Phase 1).
        if not entity:
            entity = await self.entity_registry.get_by_surface_form(
                user_id=user_id,
                entity_type=entity_type,
                surface_form=surface_form,
                db_session=db_session,
            )

        if entity:
            await self.entity_registry.add_surface_form(entity, surface_form, db_session)
            await self.entity_registry.increment_mentions(entity, session_id, db_session)
            return entity

        return await self.entity_registry.create_entity(
            user_id=user_id,
            placeholder_id=placeholder_id,
            entity_type=entity_type,
            surface_form=surface_form,
            role_tag=role_tag,
            session_id=session_id,
            db_session=db_session,
        )
