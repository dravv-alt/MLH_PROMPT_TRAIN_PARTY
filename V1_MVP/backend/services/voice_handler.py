"""
Voice Processing Service
Speech-to-Text (Whisper) and Text-to-Speech (ElevenLabs)
"""

import openai
from typing import Optional
from pathlib import Path
from backend.utils.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class VoiceHandler:
    """
    Handles voice input and output
    
    STT: OpenAI Whisper (best-in-class accuracy)
    TTS: ElevenLabs (natural, emotional voices) - loaded dynamically
    """
    
    def __init__(self):
        """Initialize voice processing clients"""
        
        # OpenAI (for Whisper STT)
        if not settings.openai_api_key:
            logger.warning("OPENAI_API_KEY not configured - STT disabled")
            self.whisper_enabled = False
        else:
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
            self.whisper_enabled = True
            logger.info("Whisper STT initialized")
        
        # ElevenLabs (for TTS) - lazy import to avoid crash if not installed
        if not settings.elevenlabs_api_key:
            logger.warning("ELEVENLABS_API_KEY not configured - TTS disabled")
            self.tts_enabled = False
        else:
            try:
                from elevenlabs.client import ElevenLabs
                self.elevenlabs_client = ElevenLabs(api_key=settings.elevenlabs_api_key)
                self.voice = settings.elevenlabs_voice
                self.el_model = settings.elevenlabs_model
                self.tts_enabled = True
                logger.info(f"ElevenLabs TTS initialized (voice: {self.voice})")
            except ImportError:
                logger.warning("elevenlabs package not installed - TTS disabled")
                self.tts_enabled = False
    
    def transcribe(self, audio_file_path: str) -> Optional[str]:
        """
        Convert speech to text using Whisper
        
        Args:
            audio_file_path: Path to audio file (.wav, .mp3, .m4a, .webm)
        
        Returns:
            Transcribed text or None if error
        
        Supported formats:
        - WAV, MP3, M4A, WEBM, OGG
        - Max size: 25MB
        - Any language (auto-detected)
        """
        
        if not self.whisper_enabled:
            logger.error("Whisper STT not enabled - missing API key")
            return None
        
        try:
            # Validate file exists
            if not Path(audio_file_path).exists():
                logger.error(f"Audio file not found: {audio_file_path}")
                return None
            
            logger.info(f"Transcribing audio file: {audio_file_path}")
            
            # Open and transcribe
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model=settings.whisper_model,
                    file=audio_file,
                    language="en",
                    response_format="text"
                )
            
            # Whisper returns string directly with response_format="text"
            transcribed_text = transcript.strip()
            
            logger.info(f"Transcription successful (length: {len(transcribed_text)} chars)")
            logger.debug(f"Transcribed text: {transcribed_text[:100]}...")
            
            return transcribed_text
        
        except openai.APIError as e:
            logger.error(f"Whisper API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    def synthesize(self, text: str, voice: Optional[str] = None) -> Optional[bytes]:
        """
        Convert text to speech using ElevenLabs
        
        Args:
            text: Text to convert to speech
            voice: Voice ID or name (default: from config)
        
        Returns:
            Audio bytes (MP3) or None if error
        
        Voice options (calm, therapeutic):
        - Rachel: Calm, warm, mature female
        - Bella: Young, empathetic female
        - Nicole: Clear, professional female
        - Elli: Gentle, soothing female
        """
        
        if not self.tts_enabled:
            logger.error("ElevenLabs TTS not enabled - missing API key")
            return None
        
        try:
            from elevenlabs import VoiceSettings
            
            voice_to_use = voice or self.voice
            
            logger.info(f"Synthesizing text (length: {len(text)} chars, voice: {voice_to_use})")
            
            # Generate audio
            audio = self.elevenlabs_client.generate(
                text=text,
                voice=voice_to_use,
                model=self.el_model,
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
            )
            
            # Convert generator to bytes
            audio_bytes = b''.join(audio)
            
            logger.info(f"TTS successful (audio size: {len(audio_bytes)} bytes)")
            return audio_bytes
        
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None
    
    def get_available_voices(self) -> list:
        """
        Get list of available ElevenLabs voices
        
        Returns:
            List of voice dicts with id and name
        """
        
        if not self.tts_enabled:
            return []
        
        try:
            voices = self.elevenlabs_client.voices.get_all()
            return [
                {"id": voice.voice_id, "name": voice.name}
                for voice in voices.voices
            ]
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
            return []
