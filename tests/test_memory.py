import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


def _mock_db():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_conn, mock_cursor


def test_save_memory_progress():
    mock_conn, mock_cursor = _mock_db()

    with patch("bctone.services.memory.get_connection", return_value=mock_conn):
        from bctone.services.memory import save_memory
        save_memory(
            category="progress",
            source_user="U123",
            source_channel="C456",
            content="로그인 API 구현 완료",
            summary="백엔드: 로그인 API 완료",
            expiry_days=14,
        )

    mock_cursor.execute.assert_called_once()
    sql = mock_cursor.execute.call_args[0][0]
    assert "INSERT INTO bctone.memories" in sql
    mock_conn.commit.assert_called_once()


def test_save_memory_decision_no_expiry():
    mock_conn, mock_cursor = _mock_db()

    with patch("bctone.services.memory.get_connection", return_value=mock_conn):
        from bctone.services.memory import save_memory
        save_memory(
            category="decision",
            source_user="U123",
            source_channel="C456",
            content="API 인증방식 JWT로 확정",
            summary="JWT 인증 방식 확정",
        )

    params = mock_cursor.execute.call_args[0][1]
    assert params[5] is None  # expires_at is None for decisions


def test_get_recent_memories():
    mock_conn, mock_cursor = _mock_db()
    mock_cursor.fetchall.return_value = [
        (1, "progress", "U123", "C456", "작업내용", "요약", datetime.now(timezone.utc), None),
    ]

    with patch("bctone.services.memory.get_connection", return_value=mock_conn):
        from bctone.services.memory import get_recent_memories
        results = get_recent_memories(limit=10)

    assert len(results) == 1
    assert results[0]["category"] == "progress"


def test_save_conversation():
    mock_conn, mock_cursor = _mock_db()

    with patch("bctone.services.memory.get_connection", return_value=mock_conn):
        from bctone.services.memory import save_conversation
        save_conversation(
            channel_id="C456",
            thread_ts="1234567890.123",
            role="user",
            content="프론트 진행상황 알려줘",
        )

    sql = mock_cursor.execute.call_args[0][0]
    assert "INSERT INTO bctone.conversations" in sql


def test_get_conversation_history():
    mock_conn, mock_cursor = _mock_db()
    mock_cursor.fetchall.return_value = [
        (1, "C456", "1234.123", "user", "질문", datetime.now(timezone.utc)),
        (2, "C456", "1234.123", "assistant", "답변", datetime.now(timezone.utc)),
    ]

    with patch("bctone.services.memory.get_connection", return_value=mock_conn):
        from bctone.services.memory import get_conversation_history
        results = get_conversation_history(channel_id="C456", thread_ts="1234.123", limit=20)

    assert len(results) == 2
    assert results[0]["role"] == "user"


def test_cleanup_expired():
    mock_conn, mock_cursor = _mock_db()
    mock_cursor.rowcount = 3

    with patch("bctone.services.memory.get_connection", return_value=mock_conn):
        from bctone.services.memory import cleanup_expired
        count = cleanup_expired()

    assert count == 3
    sql = mock_cursor.execute.call_args[0][0]
    assert "DELETE FROM bctone.memories" in sql
    assert "expires_at" in sql
