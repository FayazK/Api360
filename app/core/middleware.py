from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from typing import Callable, Awaitable


class UploadSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Enforce maximum upload size based on Content-Length header.
    If Content-Length is missing, the request is allowed to proceed and
    downstream handlers should stream/validate as needed.
    """

    def __init__(self, app, max_bytes: int):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Only enforce for methods likely to upload
        if request.method in {"POST", "PUT", "PATCH"}:
            content_length = request.headers.get("content-length")
            content_type = request.headers.get("content-type", "")
            if content_length and any(ct in content_type for ct in ("multipart/form-data", "application/octet-stream")):
                try:
                    length = int(content_length)
                    if length > self.max_bytes:
                        return JSONResponse(
                            status_code=413,
                            content={
                                "error": "PAYLOAD_TOO_LARGE",
                                "message": f"Upload too large. Max {self.max_bytes} bytes",
                            },
                        )
                except ValueError:
                    # Malformed header; allow and let downstream handle
                    pass

        return await call_next(request)

