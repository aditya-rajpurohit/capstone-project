from abc import ABC, abstractmethod

from app.retrieval.types import RetrievalDocument, RetrievalHit, RetrievalQuery


class RetrievalBackend(ABC):
    @abstractmethod
    async def upsert(self, retrieval_documents: list[RetrievalDocument]) -> None: ...

    @abstractmethod
    async def search(self, retrieval_queries: RetrievalQuery) -> list[RetrievalHit]: ...
