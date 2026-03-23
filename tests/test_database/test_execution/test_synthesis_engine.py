from app.database.execution.synthesis_engine import SynthesisEngine


def test_synthesis_engine_multiple_success():
    per_db = {
        "db1": {
            "execution_result": {
                "status": "success",
                "rows": [{"id": 1}],
                "row_count": 1,
            }
        },
        "db2": {
            "execution_result": {
                "status": "success",
                "rows": [{"id": 2}],
                "row_count": 1,
            }
        },
    }

    result = SynthesisEngine.synthesize(per_db)

    assert result["status"] == "success"
    assert result["row_count"] == 2


def test_synthesis_engine_schema_mismatch():
    per_db = {
        "db1": {
            "execution_result": {
                "status": "success",
                "rows": [{"id": 1}],
                "row_count": 1,
            }
        },
        "db2": {
            "execution_result": {
                "status": "success",
                "rows": [{"email": "a@x"}],
                "row_count": 1,
            }
        },
    }

    result = SynthesisEngine.synthesize(per_db)

    assert result["status"] == "failed"


def test_synthesis_engine_all_failed():
    per_db = {
        "db1": {"execution_result": {"status": "failed"}},
        "db2": {"execution_result": {"status": "failed"}},
    }

    result = SynthesisEngine.synthesize(per_db)

    assert result["status"] == "failed"
    assert result["row_count"] == 0
    assert result["successful_db_ids"] == []


def test_synthesis_engine_single_success():
    per_db = {
        "db1": {
            "execution_result": {
                "status": "success",
                "rows": [{"id": 1}],
                "row_count": 1,
            }
        },
        "db2": {"execution_result": {"status": "failed"}},
    }

    result = SynthesisEngine.synthesize(per_db)

    assert result["status"] == "success"
    assert result["row_count"] == 1
    assert result["successful_db_ids"] == ["db1"]


def test_synthesis_engine_empty_rows_union():
    per_db = {
        "db1": {
            "execution_result": {
                "status": "success",
                "rows": [],
                "row_count": 0,
            }
        },
        "db2": {
            "execution_result": {
                "status": "success",
                "rows": [{"id": 2}],
                "row_count": 1,
            }
        },
    }

    result = SynthesisEngine.synthesize(per_db)

    assert result["status"] == "success"
    assert result["row_count"] == 1
