import uuid
from typing import Sequence

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.metadata.models.conversation import ConversationModel
from app.database.metadata.models.message import MessageModel
from app.database.metadata.session import get_async_session


class SessionService:
    def __init__(
        self,
        sessionmaker: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._Session = sessionmaker or get_async_session()

    async def create_conversation(
        self,
        *,
        user_id: str,
        title: str | None = None,
    ) -> ConversationModel:
        async with self._Session() as session:
            conversation = ConversationModel(
                user_id=uuid.UUID(user_id),
                title=title,
            )
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            return conversation

    async def get_conversation(
        self,
        *,
        conversation_id: str,
        user_id: str,
    ) -> ConversationModel | None:
        async with self._Session() as session:
            stmt = select(ConversationModel).where(
                ConversationModel.id == uuid.UUID(conversation_id),
                ConversationModel.user_id == uuid.UUID(user_id),
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def list_conversations(
        self,
        *,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[ConversationModel]:
        async with self._Session() as session:
            stmt = (
                select(ConversationModel)
                .where(ConversationModel.user_id == uuid.UUID(user_id))
                .order_by(desc(ConversationModel.updated_at))
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def delete_conversation(
        self,
        *,
        conversation_id: str,
        user_id: str,
    ) -> bool:
        async with self._Session() as session:
            stmt = select(ConversationModel).where(
                ConversationModel.id == uuid.UUID(conversation_id),
                ConversationModel.user_id == uuid.UUID(user_id),
            )
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if not conversation:
                return False

            await session.delete(conversation)
            await session.commit()
            return True

    async def create_message(
        self,
        *,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        tool_calls: dict | None = None,
        execution_trace_id: str | None = None,
        metadata: dict | None = None,
    ) -> MessageModel:
        async with self._Session() as session:
            stmt = select(ConversationModel).where(
                ConversationModel.id == uuid.UUID(conversation_id),
                ConversationModel.user_id == uuid.UUID(user_id),
            )
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise ValueError("Conversation not found")

            message = MessageModel(
                conversation_id=conversation.id,
                role=role,
                content=content,
                tool_calls=tool_calls,
                execution_trace_id=execution_trace_id,
                message_metadata=metadata,
            )
            session.add(message)
            await session.flush()

            if role == "user" and not conversation.title:
                conversation.title = self._derive_title(content)

            await session.commit()
            await session.refresh(message)
            return message

    async def list_messages(
        self,
        *,
        conversation_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[MessageModel]:
        async with self._Session() as session:
            stmt = select(ConversationModel).where(
                ConversationModel.id == uuid.UUID(conversation_id),
                ConversationModel.user_id == uuid.UUID(user_id),
            )
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise ValueError("Conversation not found")

            msg_stmt = (
                select(MessageModel)
                .where(MessageModel.conversation_id == conversation.id)
                .order_by(MessageModel.created_at.asc())
                .limit(limit)
                .offset(offset)
            )
            msg_result = await session.execute(msg_stmt)
            return msg_result.scalars().all()

    async def load_recent_messages(
        self,
        *,
        conversation_id: str,
        user_id: str,
        limit: int = 5,
    ) -> Sequence[MessageModel]:
        async with self._Session() as session:
            stmt = select(ConversationModel).where(
                ConversationModel.id == uuid.UUID(conversation_id),
                ConversationModel.user_id == uuid.UUID(user_id),
            )
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise ValueError("Conversation not found")

            msg_stmt = (
                select(MessageModel)
                .where(MessageModel.conversation_id == conversation.id)
                .order_by(MessageModel.created_at.desc())
                .limit(limit)
            )
            msg_result = await session.execute(msg_stmt)
            rows = list(msg_result.scalars().all())
            rows.reverse()
            return rows

    async def update_summary(
        self,
        *,
        conversation_id: str,
        user_id: str,
        summary: str,
    ) -> bool:
        async with self._Session() as session:
            stmt = select(ConversationModel).where(
                ConversationModel.id == uuid.UUID(conversation_id),
                ConversationModel.user_id == uuid.UUID(user_id),
            )
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if not conversation:
                return False

            conversation.session_summary = summary
            await session.commit()
            return True

    def _derive_title(self, content: str) -> str:
        normalized = " ".join(content.strip().split())
        if len(normalized) <= 60:
            return normalized
        return normalized[:57] + "..."
