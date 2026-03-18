"""
Gemini API Client
Handles all interactions with Google Gemini API
"""

import google.generativeai as genai
from typing import Optional
from backend.utils.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class GeminiClient:
    """
    Google Gemini API client for narrative reasoning
    
    Responsibilities:
    - Generate reflective responses
    - Handle rate limiting
    - Manage errors gracefully
    - Log API usage
    
    Note: Gemini receives DISTILLED structure, not raw user text
    """
    
    def __init__(self):
        """Initialize Gemini client with API key and configuration"""
        
        if not settings.gemini_api_key:
            logger.warning("GEMINI_API_KEY not configured - Gemini disabled")
            self.enabled = False
            return
        
        self.enabled = True
        
        # Configure API
        genai.configure(api_key=settings.gemini_api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                'temperature': settings.gemini_temperature,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': settings.gemini_max_tokens,
                'candidate_count': 1,
            },
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        )
        
        logger.info(f"Gemini client initialized with model: {settings.gemini_model}")
    
    def generate_response(self, prompt: str) -> Optional[str]:
        """
        Generate response from Gemini
        
        Args:
            prompt: Complete prompt (from narrative_distiller.to_gemini_context)
        
        Returns:
            Generated response text or None if error
        """
        
        if not self.enabled:
            logger.error("Gemini client not enabled - missing API key")
            return None
        
        try:
            logger.debug(f"Sending prompt to Gemini (length: {len(prompt)} chars)")
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Extract text
            if response and response.text:
                response_text = response.text.strip()
                logger.info(f"Gemini response received (length: {len(response_text)} chars)")
                return response_text
            
            # Handle empty response
            logger.warning("Gemini returned empty response")
            return None
        
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            
            # Check for specific error types
            if "quota" in str(e).lower():
                logger.error("API quota exceeded")
                raise Exception("API quota exceeded. Please try again later.")
            elif "api key" in str(e).lower():
                logger.error("Invalid API key")
                raise Exception("API configuration error")
            else:
                logger.error(f"Unexpected Gemini error: {e}")
                raise Exception(f"Failed to generate response: {str(e)}")
    
    async def generate_response_async(self, prompt: str) -> Optional[str]:
        """
        Async version of generate_response
        
        For future async API support
        Currently just wraps sync version
        """
        return self.generate_response(prompt)
    
    def validate_connection(self) -> bool:
        """
        Test Gemini API connection
        
        Returns:
            True if connection works, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            test_prompt = "Respond with just the word 'OK'"
            response = self.model.generate_content(test_prompt)
            
            if response and response.text:
                logger.info("Gemini connection validated successfully")
                return True
            
            logger.warning("Gemini connection test failed: empty response")
            return False
        
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False
