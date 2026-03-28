from app.retrieval.retrieval_types import (RetrievalDocument, RetrievalHit,
                                           RetrievalQuery)


def test_retrieval_document():
    doc = RetrievalDocument(
        id="1",
        index="schema",
        text="hello",
        metadata={"table": "users"},
    )

    assert doc.id == "1"
    assert doc.index == "schema"
    assert doc.text == "hello"
    assert doc.metadata["table"] == "users"


def test_retrieval_hit():
    hit = RetrievalHit(
        id="1",
        index="schema",
        score=0.9,
        text="table users",
        metadata={"table": "users"},
    )

    assert hit.score == 0.9
    assert hit.text == "table users"


def test_retrieval_query_defaults():
    query = RetrievalQuery(
        index="schema",
        query_text="users table",
    )

    assert query.top_k == 5
    assert query.metadata_filter is None
