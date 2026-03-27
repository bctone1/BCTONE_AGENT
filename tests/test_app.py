import sys
import pytest
from unittest.mock import patch, MagicMock

# Mock external packages that are not installed in the test environment
_mock_slack_bolt = MagicMock()
_mock_socket_mode = MagicMock()
_mock_apscheduler = MagicMock()

sys.modules.setdefault("slack_bolt", _mock_slack_bolt)
sys.modules.setdefault("slack_bolt.adapter", MagicMock())
sys.modules.setdefault("slack_bolt.adapter.socket_mode", _mock_socket_mode)
sys.modules.setdefault("apscheduler", _mock_apscheduler)
sys.modules.setdefault("apscheduler.schedulers", MagicMock())
sys.modules.setdefault("apscheduler.schedulers.background", MagicMock())


def _mock_settings():
    settings = MagicMock()
    settings.slack_bot_token = "xoxb-test"
    settings.slack_app_token = "xapp-test"
    settings.bot_log_channel_id = "C_BOT_LOG"
    settings.daily_report_hour = 9
    return settings


def test_create_app():
    with patch("bctone.app.get_settings", return_value=_mock_settings()):
        from bctone.app import create_app
        app = create_app()

    assert app is not None


def test_start_scheduler():
    mock_app = MagicMock()

    with patch("bctone.app.get_settings", return_value=_mock_settings()):
        with patch("bctone.app.BackgroundScheduler") as MockScheduler:
            mock_scheduler_instance = MagicMock()
            MockScheduler.return_value = mock_scheduler_instance

            from bctone.app import start_scheduler
            scheduler = start_scheduler(mock_app)

    assert mock_scheduler_instance.add_job.call_count == 3  # daily, weekly, cleanup
    mock_scheduler_instance.start.assert_called_once()


def test_full_mention_flow():
    """Test the full flow: mention -> LLM -> response -> saved to memory."""
    event = {
        "text": "<@BOT_ID> 백엔드 PR 요약해줘",
        "user": "U123",
        "channel": "C456",
        "ts": "1234567890.123",
    }
    say = MagicMock()

    with patch("bctone.handlers.mention.get_conversation_history", return_value=[]):
        with patch("bctone.handlers.mention.chat", return_value="백엔드 PR #42가 머지되었습니다."):
            with patch("bctone.handlers.mention.save_conversation") as mock_save:
                from bctone.handlers.mention import handle_mention
                handle_mention(event, say)

    # Should save both user message and assistant response
    assert mock_save.call_count == 2

    # Should respond in thread
    say.assert_called_once()
    call_kwargs = say.call_args[1]
    assert "백엔드" in call_kwargs["text"]
    assert call_kwargs["thread_ts"] == "1234567890.123"


def test_full_collection_flow():
    """Test the full flow: message -> classify -> save to memory."""
    event = {
        "text": "결제 시스템 API 설계 리뷰 완료했습니다",
        "user": "U_BACKEND",
        "channel": "C_DEV",
        "ts": "1234567890.456",
    }

    with patch("bctone.handlers.message.classify_message", return_value="PROGRESS"):
        with patch("bctone.handlers.message.llm_summarize", return_value="결제 API 설계 리뷰 완료"):
            with patch("bctone.handlers.message.save_memory") as mock_save:
                from bctone.handlers.message import handle_message
                handle_message(event)

    mock_save.assert_called_once()
    kwargs = mock_save.call_args[1]
    assert kwargs["category"] == "progress"
    assert kwargs["source_user"] == "U_BACKEND"
    assert kwargs["expiry_days"] == 14
