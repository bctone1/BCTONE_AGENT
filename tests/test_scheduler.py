import pytest
from unittest.mock import patch, MagicMock


def test_post_daily_report():
    mock_client = MagicMock()

    with patch("bctone.scheduler.daily_report.generate_daily_report", return_value="일일 리포트 내용"):
        with patch("bctone.scheduler.daily_report.save_report") as mock_save:
            from bctone.scheduler.daily_report import post_daily_report
            post_daily_report(mock_client, "C_BOT_LOG")

    mock_client.chat_postMessage.assert_called_once_with(
        channel="C_BOT_LOG",
        text="일일 리포트 내용",
    )
    mock_save.assert_called_once_with("daily", "일일 리포트 내용")


def test_post_weekly_report():
    mock_client = MagicMock()

    with patch("bctone.scheduler.daily_report.generate_weekly_report", return_value="주간 리포트 내용"):
        with patch("bctone.scheduler.daily_report.save_report") as mock_save:
            from bctone.scheduler.daily_report import post_weekly_report
            post_weekly_report(mock_client, "C_BOT_LOG")

    mock_client.chat_postMessage.assert_called_once_with(
        channel="C_BOT_LOG",
        text="주간 리포트 내용",
    )
    mock_save.assert_called_once_with("weekly", "주간 리포트 내용")


def test_run_memory_cleanup():
    with patch("bctone.scheduler.daily_report.cleanup_expired", return_value=5) as mock_cleanup:
        from bctone.scheduler.daily_report import run_memory_cleanup
        run_memory_cleanup()

    mock_cleanup.assert_called_once()


def test_save_report():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    with patch("bctone.scheduler.daily_report.get_connection", return_value=mock_conn):
        from bctone.scheduler.daily_report import save_report
        save_report("daily", "리포트 내용")

    sql = mock_cursor.execute.call_args[0][0]
    assert "INSERT INTO bctone.reports" in sql
