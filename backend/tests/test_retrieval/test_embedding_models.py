from app.retrieval.embedding_models import EmbeddingRecord


def test_embedding_record():
    record = EmbeddingRecord(
        index="schema",
        doc_id="doc1",
        text="users table",
        meta_data={"table": "users"},
        embedding=[0.1] * 1536,
    )

    assert record.index == "schema"
    assert record.doc_id == "doc1"
    assert record.meta_data["table"] == "users"
