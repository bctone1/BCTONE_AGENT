import pytest
from unittest.mock import patch, MagicMock, call


def test_init_schema_creates_tables():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("bctone.db.get_connection", return_value=mock_conn):
        from bctone.db import init_schema
        init_schema()

    executed_sql = " ".join(
        c.args[0] for c in mock_cursor.execute.call_args_list
    )
    assert "CREATE SCHEMA" in executed_sql
    assert "bctone.memories" in executed_sql
    assert "bctone.conversations" in executed_sql
    assert "bctone.reports" in executed_sql
    mock_conn.commit.assert_called_once()


def test_get_connection_uses_db_url(monkeypatch):
    monkeypatch.setenv("BCTONE_DB_URL", "postgresql://test:test@localhost/bctone")

    with patch("psycopg2.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        from bctone.db import get_connection
        conn = get_connection()
        mock_connect.assert_called_once_with("postgresql://test:test@localhost/bctone")
