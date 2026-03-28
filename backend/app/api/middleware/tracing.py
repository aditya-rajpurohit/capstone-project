import uuid
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Attaches:
    - request.state.trace_id
    - request.state.request_timestamp

    Also mirrors trace_id into response headers.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        request.state.request_timestamp = datetime.now(timezone.utc).isoformat()

        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response
