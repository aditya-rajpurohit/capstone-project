from app.engine.strategy.meta_planner import MetaPlannerMVP


def test_meta_planner_detects_multi_db():
    assert MetaPlannerMVP.requires_multi_db("compare results across databases")


def test_meta_planner_single_db():
    assert not MetaPlannerMVP.requires_multi_db("show all users")
