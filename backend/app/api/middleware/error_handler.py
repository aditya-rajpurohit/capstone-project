from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.utils.responses import error_response


class GlobalErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Converts uncaught exceptions into safe API envelopes.
    Never leak stack traces or internal implementation details to clients.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)

        except HTTPException as exc:
            payload = error_response(
                error_code="HTTP_ERROR",
                message=exc.detail if isinstance(exc.detail, str) else "Request failed",
                trace_id=getattr(request.state, "trace_id", None),
                recoverable=400 <= exc.status_code < 500,
                timestamp=getattr(request.state, "request_timestamp", None),
            )
            return JSONResponse(
                status_code=exc.status_code, content=payload.model_dump()
            )

        except ValidationError:
            payload = error_response(
                error_code="VALIDATION_ERROR",
                message="Request validation failed.",
                trace_id=getattr(request.state, "trace_id", None),
                recoverable=True,
                timestamp=getattr(request.state, "request_timestamp", None),
            )
            return JSONResponse(status_code=422, content=payload.model_dump())

        except RuntimeError as exc:
            payload = error_response(
                error_code="RUNTIME_ERROR",
                message=str(exc),
                trace_id=getattr(request.state, "trace_id", None),
                recoverable=False,
                timestamp=getattr(request.state, "request_timestamp", None),
            )
            return JSONResponse(status_code=500, content=payload.model_dump())

        except Exception:
            payload = error_response(
                error_code="INTERNAL_SERVER_ERROR",
                message=f"An internal error occurred.",
                trace_id=getattr(request.state, "trace_id", None),
                recoverable=False,
                timestamp=getattr(request.state, "request_timestamp", None),
            )
            return JSONResponse(status_code=500, content=payload.model_dump())
