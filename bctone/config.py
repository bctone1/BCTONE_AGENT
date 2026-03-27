import os
from dotenv import load_dotenv


class Settings:
    def __init__(self):
        load_dotenv()

        self.slack_app_token = os.getenv("SLACK_APP_TOKEN", "")
        self.slack_bot_token = os.getenv("SLACK_BOT_TOKEN", "")
        self.slack_signing_secret = os.getenv("SLACK_SIGNING_SECRET", "")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.github_repo_backend = os.getenv("GITHUB_REPO_BACKEND", "")
        self.github_repo_frontend = os.getenv("GITHUB_REPO_FRONTEND", "")
        self.github_repo_planning = os.getenv("GITHUB_REPO_PLANNING", "")
        self.github_default_branch = os.getenv("GITHUB_DEFAULT_BRANCH", "main")
        self.bctone_db_url = os.getenv("BCTONE_DB_URL", "")
        self.bot_log_channel_id = os.getenv("BOT_LOG_CHANNEL_ID", "")
        self.daily_report_hour = int(os.getenv("DAILY_REPORT_HOUR", "18"))
        self.weekly_report_hour = int(os.getenv("WEEKLY_REPORT_HOUR", "18"))
        self.memory_expiry_days = int(os.getenv("MEMORY_EXPIRY_DAYS", "14"))

        self._validate()

    def _validate(self):
        required = {
            "SLACK_APP_TOKEN": self.slack_app_token,
            "SLACK_BOT_TOKEN": self.slack_bot_token,
            "ANTHROPIC_API_KEY": self.anthropic_api_key,
            "GITHUB_TOKEN": self.github_token,
            "BCTONE_DB_URL": self.bctone_db_url,
            "BOT_LOG_CHANNEL_ID": self.bot_log_channel_id,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(f"Missing required env vars: {', '.join(missing)}")


settings: Settings | None = None


def get_settings() -> Settings:
    global settings
    if settings is None:
        settings = Settings()
    return settings
