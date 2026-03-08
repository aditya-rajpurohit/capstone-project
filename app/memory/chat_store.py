from sqlalchemy import select

from app.data_source.session import get_sessionmaker
from app.memory.chat_memory import ChatMemory
from app.memory.models import ChatSessionModel


class ChatStore:
    async def load(self, session_id: str) -> ChatMemory:
        Session = get_sessionmaker()
        async with Session() as session:
            row = await session.scalar(
                select(ChatSessionModel).where(
                    ChatSessionModel.session_id == session_id
                )
            )
            mem = ChatMemory(session_id=session_id)
            if not row:
                return mem
            mem.summary = row.summary
            mem.turns = list(row.turns.get("turns", []))
            return mem

    async def save(self, mem: ChatMemory) -> None:
        Session = get_sessionmaker()
        async with Session() as session:
            row = await session.scalar(
                select(ChatSessionModel).where(
                    ChatSessionModel.session_id == mem.session_id
                )
            )
            payload = {"turns": mem.turns}
            if not row:
                session.add(
                    ChatSessionModel(
                        session_id=mem.session_id, summary=mem.summary, turns=payload
                    )
                )
            else:
                row.summary = mem.summary
                row.turns = payload
            await session.commit()
