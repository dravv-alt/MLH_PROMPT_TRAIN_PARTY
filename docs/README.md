 # Sanctuary Backend

Privacy-first mental health companion API built with FastAPI and Google Gemini.

## Quick Start

### 1. Clone and Setup

```bash
cd sanctuary-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys:
# - GEMINI_API_KEY (get from https://aistudio.google.com/apikey)
# - OPENAI_API_KEY (get from https://platform.openai.com/api-keys)
# - ELEVENLABS_API_KEY (get from https://elevenlabs.io/app/settings/api-keys)
```

### 3. Run Server

```bash
python main.py
```

Server runs at: http://localhost:8000

API docs: http://localhost:8000/docs

## Features

- ✅ Privacy-preserving narrative distillation
- ✅ Google Gemini integration for reasoning
- ✅ Voice input (Whisper STT)
- ✅ Voice output (ElevenLabs TTS)
- ✅ User-curated journaling
- ✅ Gen-Z tone mode
- ✅ Session management

## API Endpoints

### Chat
`POST /chat` - Send message, get Sanctuary response

### Voice
`POST /voice/transcribe` - Upload audio, get text
`POST /voice/synthesize` - Send text, get audio

### Conversation
`GET /conversation/{session_id}` - Get conversation history

### Journal
`POST /journal/suggest` - Get AI-suggested key moments
`POST /journal/create` - Create journal entry from selected turns
`GET /journal/{entry_id}` - Get journal entry
`DELETE /journal/{entry_id}` - Delete journal entry

## Architecture

```
User Input → Narrative Distillation → Gemini API → Response Composition → Output
              (removes identifiers)     (reasoning)    (local assembly)
```

**Privacy-First:**
- Raw text never stored long-term
- Only abstract narrative structure sent to Gemini
- User controls what gets saved (journal)

## Development

### Run Tests
```bash
pytest tests/
```

### Run with Docker
```bash
docker-compose up
```

## License

MIT
