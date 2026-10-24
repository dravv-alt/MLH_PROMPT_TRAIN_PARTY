from abc import ABC, abstractmethod

class TTSProvider(ABC):
    @abstractmethod
    async def generate_speech(self, text: str) -> str:
        """
        Convert the restored response text into speech audio.
        Returns the path or URL to the generated audio.
        """
        pass
