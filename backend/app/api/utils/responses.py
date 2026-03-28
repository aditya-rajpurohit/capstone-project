from typing import Any, Optional

from app.api.schemas.common import ErrorEnvelope, SuccessEnvelope


def success_response(
    data: dict[str, Any],
    trace_id: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> SuccessEnvelope:
    payload = {
        "success": True,
        "data": data,
        "trace_id": trace_id,
    }
    if timestamp is not None:
        payload["timestamp"] = timestamp
    return SuccessEnvelope(**payload)


def error_response(
    *,
    error_code: str,
    message: str,
    trace_id: Optional[str] = None,
    recoverable: bool = False,
    timestamp: Optional[str] = None,
) -> ErrorEnvelope:
    payload = {
        "success": False,
        "error_code": error_code,
        "message": message,
        "trace_id": trace_id,
        "recoverable": recoverable,
    }
    if timestamp is not None:
        payload["timestamp"] = timestamp
    return ErrorEnvelope(**payload)
