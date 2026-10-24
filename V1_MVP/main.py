"""
Sanctuary Backend - Main API Server
FastAPI application entry point
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import tempfile
from datetime import datetime
import uuid

# Import services
from backend.services.narrative_distiller import NarrativeDistiller
from backend.services.gemini_client import GeminiClient
from backend.services.voice_handler import VoiceHandler
from backend.services.journal_service import JournalService, JournalEntry

# Import models
from backend.models.narrative import ConversationSession, ConversationTurn
from backend.models.conversation import (
    ChatRequest,
    ChatResponse,
    TranscriptionResponse,
    JournalCreateRequest,
    JournalSuggestResponse,
)

# Import utilities
from backend.utils.config import settings
from backend.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Privacy-first mental health companion API",
    debug=settings.debug_mode,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=settings.allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
narrative_distiller = NarrativeDistiller()
gemini_client = GeminiClient()
voice_handler = VoiceHandler()
journal_service = JournalService()

# In-memory session storage (use Redis/DB in production)
sessions: dict[str, ConversationSession] = {}


# ===== Helper Functions =====

def get_or_create_session(session_id: str) -> ConversationSession:
    """Get existing session or create new one"""
    if session_id not in sessions:
        sessions[session_id] = ConversationSession(session_id=session_id)
        logger.info(f"Created new session: {session_id}")
    return sessions[session_id]


def cleanup_temp_file(filepath: str):
    """Background task to clean up temporary files"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.debug(f"Cleaned up temp file: {filepath}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {filepath}: {e}")


# ===== API Endpoints =====

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    
    # Check Gemini connection
    gemini_ok = gemini_client.validate_connection()
    
    return {
        "status": "healthy" if gemini_ok else "degraded",
        "services": {
            "gemini": "ok" if gemini_ok else "error",
            "whisper": "ok" if voice_handler.whisper_enabled else "disabled",
            "elevenlabs": "ok" if voice_handler.tts_enabled else "disabled",
        },
        "sessions_active": len(sessions),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint
    
    Flow:
    1. Get/create conversation session
    2. Distill user message to narrative structure
    3. Generate Gemini prompt
    4. Get response from Gemini
    5. Save both messages to session
    6. Return Sanctuary response
    """
    
    try:
        logger.info(f"Chat request from session: {request.session_id}")
        
        # Get session
        session = get_or_create_session(request.session_id)
        
        # Check turn limit
        if len(session.turns) >= settings.max_conversation_turns:
            raise HTTPException(
                status_code=400,
                detail="Conversation turn limit reached. Please start a new session.",
            )
        
        # Add user turn
        user_turn = session.add_turn(
            role="user",
            text=request.user_message,
            gen_z_mode=request.gen_z_mode,
        )
        
        # Distill narrative structure
        narrative_structure = narrative_distiller.distill(
            user_text=request.user_message,
            conversation_history=session.get_recent_context(),
        )
        
        # Store structure in turn
        user_turn.narrative_structure = narrative_structure
        
        # Create Gemini prompt
        gemini_prompt = narrative_distiller.to_gemini_context(
            structure=narrative_structure,
            user_text=request.user_message,
            gen_z_mode=request.gen_z_mode,
        )
        
        # Generate response
        sanctuary_response = gemini_client.generate_response(gemini_prompt)
        
        if not sanctuary_response:
            # Fallback response when Gemini is unavailable
            sanctuary_response = (
                "I hear you, and what you're sharing matters. "
                "I'm having a moment of difficulty connecting right now, "
                "but I'm still here with you. Could you tell me a bit more?"
            )
        
        # Add Sanctuary turn
        sanctuary_turn = session.add_turn(
            role="sanctuary",
            text=sanctuary_response,
            gen_z_mode=request.gen_z_mode,
        )
        
        logger.info(f"Chat turn completed: {request.session_id} (turn {sanctuary_turn.turn_id})")
        
        return ChatResponse(
            sanctuary_response=sanctuary_response,
            session_id=request.session_id,
            turn_id=sanctuary_turn.turn_id,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/voice/transcribe", response_model=TranscriptionResponse)
async def transcribe_voice(
    audio: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    """
    Speech-to-Text endpoint
    
    Accepts audio file, returns transcribed text
    Supports: WAV, MP3, M4A, WEBM, OGG
    """
    
    try:
        logger.info(f"Transcription request: {audio.filename}")
        
        # Validate file type
        allowed_types = [".wav", ".mp3", ".m4a", ".webm", ".ogg"]
        file_ext = os.path.splitext(audio.filename)[1].lower()
        
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_types}",
            )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_path = temp_file.name
            content = await audio.read()
            temp_file.write(content)
        
        # Transcribe
        transcript = voice_handler.transcribe(temp_path)
        
        # Schedule cleanup
        if background_tasks:
            background_tasks.add_task(cleanup_temp_file, temp_path)
        
        if not transcript:
            raise HTTPException(
                status_code=500,
                detail="Transcription failed",
            )
        
        logger.info(f"Transcription successful: {len(transcript)} chars")
        
        return TranscriptionResponse(text=transcript)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/voice/synthesize")
async def synthesize_voice(text: str, voice: Optional[str] = None):
    """
    Text-to-Speech endpoint
    
    Accepts text, returns audio (MP3)
    """
    
    try:
        logger.info(f"TTS request: {len(text)} chars")
        
        # Validate text length
        if len(text) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Text too long (max 1000 chars)",
            )
        
        # Synthesize
        audio_bytes = voice_handler.synthesize(text, voice)
        
        if not audio_bytes:
            raise HTTPException(
                status_code=500,
                detail="Speech synthesis failed",
            )
        
        logger.info(f"TTS successful: {len(audio_bytes)} bytes")
        
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=sanctuary_response.mp3"
            },
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """
    Get conversation history for session
    
    Returns all turns for journal selection UI
    """
    
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        
        # Format turns for frontend
        turns = [
            {
                "turn_id": turn.turn_id,
                "role": turn.role,
                "text": turn.text,
                "timestamp": turn.timestamp.isoformat(),
            }
            for turn in session.turns
        ]
        
        return {
            "session_id": session_id,
            "turns": turns,
            "total_turns": len(turns),
            "created_at": session.created_at.isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/journal/suggest", response_model=JournalSuggestResponse)
async def suggest_journal_moments(session_id: str):
    """
    Get AI-suggested key moments for journaling
    
    Returns turn IDs that seem important (user can ignore)
    """
    
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[session_id]
        
        # Get suggestions
        suggested_ids = journal_service.suggest_key_moments(session.turns)
        
        return JournalSuggestResponse(
            session_id=session_id,
            suggested_turn_ids=suggested_ids,
            total_turns=len(session.turns),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Journal suggest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/journal/create", response_model=JournalEntry)
async def create_journal_entry(request: JournalCreateRequest):
    """
    Create journal entry from selected turns
    
    User chooses which moments to save + adds reflection
    """
    
    try:
        if request.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[request.session_id]
        
        # Validate turn IDs
        invalid_ids = [
            tid for tid in request.selected_turn_ids
            if tid >= len(session.turns)
        ]
        
        if invalid_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid turn IDs: {invalid_ids}",
            )
        
        # Create entry
        entry = journal_service.create_entry(
            session_id=request.session_id,
            selected_turn_ids=request.selected_turn_ids,
            all_turns=session.turns,
            user_reflection=request.user_reflection,
        )
        
        logger.info(f"Journal entry created: {entry.entry_id}")
        
        return entry
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Journal create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/journal/{entry_id}", response_model=JournalEntry)
async def get_journal_entry(entry_id: str):
    """Get journal entry by ID"""
    
    entry = journal_service.get_entry(entry_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    return entry


@app.delete("/journal/{entry_id}")
async def delete_journal_entry(entry_id: str):
    """Delete journal entry"""
    
    deleted = journal_service.delete_entry(entry_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    return {"status": "deleted", "entry_id": entry_id}


# ===== Startup/Shutdown Events =====

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info(f"{settings.app_name} v{settings.app_version} starting...")
    logger.info(f"Debug mode: {settings.debug_mode}")
    logger.info(f"CORS origins: {settings.allowed_origins_list}")
    
    # Validate Gemini connection
    if gemini_client.validate_connection():
        logger.info("Gemini API connection validated")
    else:
        logger.warning("Gemini API connection failed - check API key")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info(f"{settings.app_name} shutting down...")
    
    # Save any critical data
    logger.info(f"Active sessions: {len(sessions)}")
    logger.info(f"Journal entries: {len(journal_service.entries)}")


# ===== Run Server =====

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
