from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware


class PolicyContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        incoming_request_id = request.headers.get("X-Request-ID")
        request_id = incoming_request_id or f"req_{uuid4().hex[:12]}"
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault("Pragma", "no-cache")
        return response
