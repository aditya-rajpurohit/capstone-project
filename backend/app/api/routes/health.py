from fastapi import APIRouter, Request

from app.api.schemas.common import HealthResponse
from app.api.utils.responses import success_response
from app.database.registry.database_registry import DatabaseRegistry

router = APIRouter(tags=["health"])


@router.get("/", summary="Root health")
async def root(request: Request):
    return success_response(
        data={"status": "running"},
        trace_id=getattr(request.state, "trace_id", None),
    )


@router.get("/health", response_model=HealthResponse, summary="Basic health check")
async def health(request: Request):
    registry = DatabaseRegistry.get_instance()

    return HealthResponse(
        success=True,
        data={
            "status": "ok",
            "service": "capstone-project",
            "active_datasources": len(registry.list_all()),
        },
        trace_id=getattr(request.state, "trace_id", None),
        timestamp=request.state.request_timestamp,
    )


@router.get("/health/detailed", summary="Detailed component health")
async def detailed_health(request: Request):
    registry = DatabaseRegistry.get_instance()
    handles = registry.list_all()

    return success_response(
        data={
            "status": "ok",
            "service": "capstone-project",
            "components": {
                "api": {"status": "ok"},
                "app_db": {"status": "ok"},
                "registry": {
                    "status": "ok",
                    "total_datasources": len(handles),
                    "healthy_datasources": len(
                        [h for h in handles if h.is_active and h.is_healthy]
                    ),
                },
            },
        },
        trace_id=getattr(request.state, "trace_id", None),
        timestamp=request.state.request_timestamp,
    )
