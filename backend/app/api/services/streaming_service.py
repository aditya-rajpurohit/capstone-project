import asyncio
import json
from typing import AsyncGenerator

from app.api.services.query_service import QueryService


class StreamingService:
    def __init__(self, query_service: QueryService):
        self._query_service = query_service

    async def stream_query(
        self,
        *,
        conversation_id: str,
        user_id: str,
        user_message: str,
        active_database_ids: list[str],
        trace_id: str,
    ) -> AsyncGenerator[str, None]:

        # 1️⃣ Planning event
        yield self._event("status", {
            "stage": "PLAN",
            "message": "Analyzing your query...",
            "trace_id": trace_id,
        })

        await asyncio.sleep(0.05)

        # 2️⃣ Routing event
        yield self._event("status", {
            "stage": "ROUTING",
            "message": "Routing to databases...",
            "trace_id": trace_id,
        })

        await asyncio.sleep(0.05)

        # 3️⃣ Execute actual query
        try:
            result = await self._query_service.execute_query(
                conversation_id=conversation_id,
                user_id=user_id,
                user_message=user_message,
                active_database_ids=active_database_ids,
            )

        except Exception as e:
            yield self._event("error", {
                "message": "Execution failed",
                "trace_id": trace_id,
            })
            return

        # 4️⃣ Tool result
        yield self._event("tool_result", {
            "status": "done",
            "trace_id": result["trace_id"],
        })

        # 5️⃣ Final response (simulate token streaming)
        text = result["response"]

        for chunk in self._chunk_text(text):
            yield self._event("token", {
                "text": chunk,
                "trace_id": result["trace_id"],
            })
            await asyncio.sleep(0.01)

        # 6️⃣ Done
        yield self._event("done", {
            "trace_id": result["trace_id"],
        })

    def _event(self, event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    def _chunk_text(self, text: str, size: int = 20):
        for i in range(0, len(text), size):
            yield text[i:i + size]
