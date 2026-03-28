from datetime import datetime, timezone
from typing import Any, Optional


class ChatMemory:
    """
    Session-scoped memory.

    Stores:
    - conversation turns
    - executed queries (query memory)
    - references to trace IDs
    """

    def __init__(
        self, session_id: str, *, max_turns: int = 12, keep_recent: int = 6
    ) -> None:
        self.session_id = session_id
        self.created_at = datetime.now(timezone.utc)

        self.max_turns = max_turns
        self.keep_recent = keep_recent

        self.summary: Optional[str] = None

        self.turns: list[dict[str, Any]] = []
        self.query_memory: dict[str, dict[str, Any]] = {}
        # key = normalized_sql + db_id

    # -------------------------
    # Conversation memory
    # -------------------------
    def add_turn(self, role: str, content: str) -> None:
        self.turns.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def get_recent_turns(self, limit: int | None = None) -> list[dict[str, Any]]:
        limit = limit or self.keep_recent
        return self.turns[-limit:]

    def needs_summarization(self) -> bool:
        return len(self.turns) > self.max_turns

    def apply_summary(self, summary_text: str) -> None:
        self.summary = summary_text
        # prune old turns, keep only recent
        self.turns = self.get_recent_turns(self.keep_recent)

    # -------------------------
    # Query memory
    # -------------------------

    def store_query_result(
        self, db_id: str, normalized_sql: str, result: dict[str, Any]
    ) -> None:
        key = self._query_key(db_id, normalized_sql)
        self.query_memory[key] = result

    def get_query_result(
        self, db_id: str, validated_sql: str
    ) -> Optional[dict[str, Any]]:
        key = self._query_key(db_id, validated_sql)
        return self.query_memory.get(key)

    @staticmethod
    def _query_key(db_id: str, sql: str) -> str:
        return f"{db_id}::{sql}"
