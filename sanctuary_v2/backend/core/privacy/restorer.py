import re
from sanctuary_v2.backend.core.privacy.distiller import PlaceholderMap


class PlaceholderRestorer:
    """
    Replaces placeholders (PERSON_A) with original surface forms.
    This runs after the Policy Gate and right before TTS.
    """

    def restore(self, text: str, placeholder_map: PlaceholderMap) -> str:
        restored = text

        # Replace longer placeholders first to avoid partial replacements
        for placeholder, surface in sorted(
            placeholder_map.entity_map.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            pattern = re.compile(rf"\b{re.escape(placeholder)}\b")
            restored = pattern.sub(surface, restored)

        return restored
