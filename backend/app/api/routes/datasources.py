from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies import get_current_user, get_datasource_service
from app.api.schemas.datasource_schemas import (
    DatasourceResponse,
    RegisterDatasourceRequest,
)
from app.api.utils.responses import success_response

router = APIRouter(prefix="/v1/datasources", tags=["datasources"])


def _serialize(ds) -> dict:
    return {
        "id": str(ds.id),
        "name": ds.name,
        "dialect": ds.dialect,
        "is_active": ds.is_active,
        "is_healthy": True,  # registry will reflect actual later
        "created_at": ds.created_at.isoformat(),
    }


@router.post("")
async def register_datasource(
    payload: RegisterDatasourceRequest,
    request: Request,
    current_user=Depends(get_current_user),
    service=Depends(get_datasource_service),
):
    if payload.dialect.lower() != "postgres":
        raise HTTPException(status_code=400, detail="Only postgres supported")

    try:
        ds = await service.register_postgres(
            name=payload.name,
            config=payload.config.model_dump(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return success_response(
        data=_serialize(ds),
        trace_id=request.state.trace_id,
        timestamp=request.state.request_timestamp,
    )


@router.get("")
async def list_datasources(
    request: Request,
    current_user=Depends(get_current_user),
    service=Depends(get_datasource_service),
):
    ds_list = await service.list_datasources()

    return success_response(
        data={"datasources": [_serialize(ds) for ds in ds_list]},
        trace_id=request.state.trace_id,
        timestamp=request.state.request_timestamp,
    )


@router.get("/{datasource_id}")
async def get_datasource(
    datasource_id: str,
    request: Request,
    current_user=Depends(get_current_user),
    service=Depends(get_datasource_service),
):
    ds = await service.get_datasource(datasource_id)

    if not ds:
        raise HTTPException(status_code=404, detail="Datasource not found")

    return success_response(
        data=_serialize(ds),
        trace_id=request.state.trace_id,
        timestamp=request.state.request_timestamp,
    )


@router.delete("/{datasource_id}")
async def delete_datasource(
    datasource_id: str,
    request: Request,
    current_user=Depends(get_current_user),
    service=Depends(get_datasource_service),
):
    deleted = await service.delete_datasource(datasource_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Datasource not found")

    return success_response(
        data={"deleted": True},
        trace_id=request.state.trace_id,
        timestamp=request.state.request_timestamp,
    )
