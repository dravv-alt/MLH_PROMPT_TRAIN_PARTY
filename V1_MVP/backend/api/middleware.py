"""
API Middleware
Error handling and request processing middleware
"""

# CORS middleware is configured directly in main.py.
# Add custom middleware here as needed:
#
# Example: Request timing middleware
#
# import time
# from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.requests import Request
#
# class TimingMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         start = time.time()
#         response = await call_next(request)
#         elapsed = time.time() - start
#         response.headers["X-Process-Time"] = str(elapsed)
#         return response
#
# Usage in main.py:
# from backend.api.middleware import TimingMiddleware
# app.add_middleware(TimingMiddleware)
