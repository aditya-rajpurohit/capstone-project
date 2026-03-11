from abc import ABC, abstractmethod

from app.retrieval.retrieval_types import RetrievalDocument, RetrievalHit, RetrievalQuery


class RetrievalBackend(ABC):    
    @abstractmethod
    async def upsert(self, retrieval_documents: list[RetrievalDocument]) -> None: 
        ...

    @abstractmethod
    async def search(self, retrieval_query: RetrievalQuery) -> list[RetrievalHit]: 
        ...
