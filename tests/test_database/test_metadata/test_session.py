import pytest
from unittest.mock import patch, MagicMock
import app.database.metadata.session as session_module


def test_get_async_session_requires_database_url(monkeypatch):
    monkeypatch.setattr(session_module, "DATABASE_URL", None)
    session_module._sessionmaker = None

    with pytest.raises(RuntimeError):
        session_module.get_async_session()


def test_get_async_session_creates_sessionmaker(monkeypatch):
    monkeypatch.setattr(session_module, "DATABASE_URL", "postgresql+asyncpg://test")

    fake_engine = MagicMock()
    fake_sessionmaker = MagicMock()

    with patch.object(session_module, "create_async_engine", return_value=fake_engine), \
         patch.object(session_module, "async_sessionmaker", return_value=fake_sessionmaker):

        session_module._sessionmaker = None

        result = session_module.get_async_session()

        assert result == fake_sessionmaker


def test_get_async_session_cached(monkeypatch):
    fake_sessionmaker = MagicMock()

    session_module._sessionmaker = fake_sessionmaker

    result = session_module.get_async_session()

    assert result == fake_sessionmaker
