from app.tools.synthesis_engine import SynthesisEngine


def test_synthesis_engine():

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


def test_synthesis_engine_failure():

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
