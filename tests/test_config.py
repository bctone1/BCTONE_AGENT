import os
import pytest
from bctone.config import Settings


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("SLACK_APP_TOKEN", "xapp-test")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
    monkeypatch.setenv("GITHUB_REPO_BACKEND", "owner/backend")
    monkeypatch.setenv("GITHUB_REPO_FRONTEND", "owner/frontend")
    monkeypatch.setenv("BCTONE_DB_URL", "postgresql://localhost/bctone")
    monkeypatch.setenv("BOT_LOG_CHANNEL_ID", "C123")

    settings = Settings()

    assert settings.slack_app_token == "xapp-test"
    assert settings.slack_bot_token == "xoxb-test"
    assert settings.anthropic_api_key == "sk-ant-test"
    assert settings.daily_report_hour == 9
    assert settings.memory_expiry_days == 14


def test_settings_raises_on_missing_required(monkeypatch):
    monkeypatch.setattr("bctone.config.load_dotenv", lambda: None)
    monkeypatch.delenv("SLACK_APP_TOKEN", raising=False)
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("BCTONE_DB_URL", raising=False)
    monkeypatch.delenv("BOT_LOG_CHANNEL_ID", raising=False)

    with pytest.raises(ValueError, match="Missing required"):
        Settings()
