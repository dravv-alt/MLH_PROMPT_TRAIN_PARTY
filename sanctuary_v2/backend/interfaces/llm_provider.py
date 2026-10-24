from abc import ABC, abstractmethod
from typing import Dict, Any

class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, behavioral_spec: str, distilled_conversation: str) -> str:
        """
        Generate a response based strictly on the behavioral spec.
        Never pass real PII or Identity names here.
        """
        pass
