from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.api.dependencies import (get_current_user, get_query_service,
                                  get_session_service, get_streaming_service)
from app.api.schemas.conversation_schemas import (ConversationResponse,
                                                  CreateConversationRequest,
                                                  CreateMessageRequest,
                                                  ListConversationsResponse,
                                                  ListMessagesResponse,
                                                  MessageResponse)
from app.api.utils.responses import success_response

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


def _conversation_to_dict(conversation) -> dict:
    return {
        "id": str(conversation.id),
        "user_id": str(conversation.user_id),
        "title": conversation.title,
        "session_summary": conversation.session_summary,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


def _message_to_dict(message) -> dict:
    return {
        "id": str(message.id),
        "conversation_id": str(message.conversation_id),
        "role": message.role,
        "content": message.content,
        "tool_calls": message.tool_calls,
        "execution_trace_id": message.execution_trace_id,
        "metadata": message.message_metadata,
        "created_at": message.created_at.isoformat(),
    }


@router.post("")
async def create_conversation(
    payload: CreateConversationRequest,
    request: Request,
    current_user=Depends(get_current_user),
    session_service=Depends(get_session_service),
):
    conversation = await session_service.create_conversation(
        user_id=str(current_user.id),
        title=payload.title,
    )

    return success_response(
        data=_conversation_to_dict(conversation),
        trace_id=getattr(request.state, "trace_id", None),
        timestamp=getattr(request.state, "request_timestamp", None),
    )


@router.get("")
async def list_conversations(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user=Depends(get_current_user),
    session_service=Depends(get_session_service),
):
    conversations = await session_service.list_conversations(
        user_id=str(current_user.id),
        limit=limit,
        offset=offset,
    )

    return success_response(
        data={
            "conversations": [
                _conversation_to_dict(conversation) for conversation in conversations
            ]
        },
        trace_id=getattr(request.state, "trace_id", None),
        timestamp=getattr(request.state, "request_timestamp", None),
    )


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    request: Request,
    current_user=Depends(get_current_user),
    session_service=Depends(get_session_service),
):
    conversation = await session_service.get_conversation(
        conversation_id=conversation_id,
        user_id=str(current_user.id),
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return success_response(
        data=_conversation_to_dict(conversation),
        trace_id=getattr(request.state, "trace_id", None),
        timestamp=getattr(request.state, "request_timestamp", None),
    )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    request: Request,
    current_user=Depends(get_current_user),
    session_service=Depends(get_session_service),
):
    deleted = await session_service.delete_conversation(
        conversation_id=conversation_id,
        user_id=str(current_user.id),
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return success_response(
        data={"deleted": True, "conversation_id": conversation_id},
        trace_id=getattr(request.state, "trace_id", None),
        timestamp=getattr(request.state, "request_timestamp", None),
    )


@router.post("/{conversation_id}/messages")
async def create_message(
    conversation_id: str,
    payload: CreateMessageRequest,
    request: Request,
    current_user=Depends(get_current_user),
    session_service=Depends(get_session_service),
    query_service=Depends(get_query_service),
    streaming_service=Depends(get_streaming_service),
):
    # Non-user → normal behavior
    if payload.role != "user":
        message = await session_service.create_message(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            role=payload.role,
            content=payload.content,
        )
        return success_response(
            data=_message_to_dict(message),
            trace_id=request.state.trace_id,
        )

    active_db_ids = payload.metadata.get("active_db_ids") if payload.metadata else None

    if not active_db_ids:
        raise HTTPException(status_code=400, detail="active_db_ids required")

    if payload.metadata:
        # 🔥 STREAMING PATH
        if payload.metadata.get("stream", False):
            generator = streaming_service.stream_query(
                conversation_id=conversation_id,
                user_id=str(current_user.id),
                user_message=payload.content,
                active_db_ids=active_db_ids,
                trace_id=request.state.trace_id,
            )

            return StreamingResponse(generator, media_type="text/event-stream")

    # 🔥 NON-STREAMING PATH
    result = await query_service.execute_query(
        conversation_id=conversation_id,
        user_id=str(current_user.id),
        user_message=payload.content,
        active_db_ids=active_db_ids,
    )

    return success_response(
        data=result,
        trace_id=request.state.trace_id,
    )


@router.get("/{conversation_id}/messages")
async def list_messages(
    conversation_id: str,
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user=Depends(get_current_user),
    session_service=Depends(get_session_service),
):
    try:
        messages = await session_service.list_messages(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            limit=limit,
            offset=offset,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return success_response(
        data={"messages": [_message_to_dict(message) for message in messages]},
        trace_id=getattr(request.state, "trace_id", None),
        timestamp=getattr(request.state, "request_timestamp", None),
    )
