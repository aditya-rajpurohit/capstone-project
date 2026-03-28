import uuid
from typing import Any

from app.engine.context.chat_context import ChatContext
from app.engine.orchestration.execution_controller import ExecutionController
from app.runtime.chat.chat_memory import ChatMemory
from app.api.services.session_service import SessionService


class QueryService:
    def __init__(
        self,
        controller: ExecutionController,
        session_service: SessionService,
    ) -> None:
        self._controller = controller
        self._session_service = session_service

    async def execute_query(
        self,
        *,
        conversation_id: str,
        user_id: str,
        user_message: str,
        active_database_ids: list[str],
    ) -> dict[str, Any]:

        # 1️⃣ Store user message
        user_msg = await self._session_service.create_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=user_message,
        )

        # 2️⃣ Load recent messages for context
        history = await self._session_service.load_recent_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=5,
        )

        # 3️⃣ Build ChatMemory
        chat_memory = ChatMemory(session_id=conversation_id)

        for msg in history:
            chat_memory.add_turn(
                role=msg.role,
                content=msg.content,
            )

        # 4️⃣ Build ChatContext
        chat_context = ChatContext(active_database_ids)

        # 5️⃣ Run engine
        trace = await self._controller.run(
            user_query=user_message,
            chat_context=chat_context,
            chat_memory=chat_memory,
        )

        # 6️⃣ Build assistant response (simple for now)
        assistant_text = self._build_response(trace)

        # 7️⃣ Store assistant message
        assistant_msg = await self._session_service.create_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content=assistant_text,
            execution_trace_id=trace.request_id,
            metadata={
                "final_state": str(trace.final_state),
                "confidence": trace.final_confidence,
            },
        )

        return {
            "user_message": str(user_msg.id),
            "assistant_message": str(assistant_msg.id),
            "trace_id": trace.request_id,
            "response": assistant_text,
        }

    def _build_response(self, trace) -> str:
        """
        Temporary response builder.

        Later:
        - LLM-based synthesis
        - streaming tokens
        - better formatting
        """

        if trace.final_state.name == "FAILED":
            return "I couldn't complete your request. Please try again."

        if trace.synthesis_result and "rows" in trace.synthesis_result:
            rows = trace.synthesis_result["rows"]
            return f"Query executed successfully. Returned {len(rows)} rows."

        return "Query executed successfully."
