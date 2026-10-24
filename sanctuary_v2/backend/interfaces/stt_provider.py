from abc import ABC, abstractmethod

class STTProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        """
        Convert user audio input into raw text.
        This raw text MUST NOT leave Zone A until distilled.
        """
        pass
