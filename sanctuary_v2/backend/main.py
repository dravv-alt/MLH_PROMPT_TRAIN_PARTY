from contextlib import asynccontextmanager
from fastapi import FastAPI

from sanctuary_v2.backend.core.database import engine
from sanctuary_v2.backend.api.auth import router as auth_router
from sanctuary_v2.backend.api.session import router as session_router
from sanctuary_v2.backend.api.turn import router as turn_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic can be added here later (e.g., warm caches, load models)
    yield
    await engine.dispose()


app = FastAPI(
    title="Sanctuary V2 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(session_router, prefix="/session", tags=["session"])
app.include_router(turn_router, prefix="/turn", tags=["turn"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
