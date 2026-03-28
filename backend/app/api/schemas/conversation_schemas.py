from typing import Any

from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    title: str | None = None


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str | None = None
    session_summary: str | None = None
    created_at: str
    updated_at: str


class ListConversationsResponse(BaseModel):
    conversations: list[ConversationResponse]


class CreateMessageRequest(BaseModel):
    role: str = Field(..., description="user | assistant | system | tool")
    content: str
    tool_calls: dict[str, Any] | None = None
    execution_trace_id: str | None = None
    metadata: dict[str, Any] | None = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    tool_calls: dict[str, Any] | None = None
    execution_trace_id: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: str


class ListMessagesResponse(BaseModel):
    messages: list[MessageResponse]
