from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env", override=False)

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.error_contract import (
    error_payload,
    get_request_id_from_state,
    is_retryable_status,
    parse_http_error_detail,
)
from app.api.middleware import PolicyContextMiddleware
from app.api.body_limit import BodyLimitMiddleware
from app.api.routes import router
from app.models.db import init_db
from app.services.journal_service import JournalService
from app.services.session_state import SessionStateStore
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(application):
    from app.services.nlp_service import get_nlp_service
    neural=get_nlp_service().neural
    neural.start()
    try:yield
    finally:neural.stop()

app = FastAPI(
    title="Sanctuary V2 API",
    version="0.1.0",
    description="Research-first reflective narrative backend.",
    lifespan=lifespan,
)

init_db()
app.state.session_state = SessionStateStore()
app.state.journal_service = JournalService()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BodyLimitMiddleware)
app.add_middleware(PolicyContextMiddleware)


@app.exception_handler(StarletteHTTPException)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code, message = parse_http_error_detail(
        exc.detail,
        default_code="request_failed",
        default_message="Request failed.",
    )
    request_id = get_request_id_from_state(request)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(code, message, is_retryable_status(exc.status_code), request_id),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0] if exc.errors() else None
    message = "Invalid request payload."
    if first_error and isinstance(first_error, dict):
        message = str(first_error.get("msg") or message)

    request_id = get_request_id_from_state(request)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_payload("validation_error", message, False, request_id),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    _ = exc
    request_id = get_request_id_from_state(request)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload("internal_error", "Something went wrong.", True, request_id),
    )

app.include_router(router)
