from app.inference.structured import StructuredModel
from app.inference.types import ModelRequest

SUMMARY_SYSTEM_PROMPT = """You are a summarizer.
Summarize the conversation so far into a compact memory that preserves:
- user goals and constraints
- entities and db names mentioned
- decisions made
- important results returned
Do NOT include irrelevant chit-chat.
Return plain text summary (not JSON)."""


class ChatSummarizer:
    def __init__(self, model: StructuredModel, model_name: str = "gpt-4o-mini") -> None:
        self.model = model
        self.model_name = model_name

    async def summarize(self, turns: list[dict]) -> str:
        # turns: [{"role": "user"/"assistant", "content": "..."}]
        convo = "\n".join([f'{t["role"]}: {t["content"]}' for t in turns])

        req = ModelRequest(
            system_prompt=SUMMARY_SYSTEM_PROMPT,
            user_prompt=convo,
            model=self.model_name,
            temperature=0.0,
        )

        # simplest: use raw backend text generation if you have it
        # If you only support structured outputs, create a Pydantic schema like {"summary": str}
        # resp = await self.model.generate_text(req, [])  # adjust to your b
        resp = ""
        return resp.strip()
