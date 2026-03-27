import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from apscheduler.schedulers.background import BackgroundScheduler

from bctone.config import get_settings
from bctone.db import init_schema
from bctone.handlers.mention import handle_mention
from bctone.handlers.message import handle_message
from bctone.handlers.command import handle_command
from bctone.scheduler.daily_report import (
    post_daily_report,
    post_weekly_report,
    run_memory_cleanup,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("bctone")


def create_app() -> App:
    settings = get_settings()
    app = App(token=settings.slack_bot_token)

    # Register mention handler
    @app.event("app_mention")
    def on_mention(event, say):
        handle_mention(event, say)

    # Register message handler (silent collection)
    @app.event("message")
    def on_message(event, say):
        # Only process actual user messages, not subtypes
        if event.get("subtype") is None:
            handle_message(event)

    # Register slash command
    @app.command("/bctone")
    def on_command(ack, respond, command):
        handle_command(ack, respond, command)

    return app


def start_scheduler(app: App):
    settings = get_settings()
    scheduler = BackgroundScheduler(timezone="Asia/Seoul")

    # Daily report: weekdays at configured hour (default 9 AM KST)
    scheduler.add_job(
        post_daily_report,
        "cron",
        day_of_week="mon-fri",
        hour=settings.daily_report_hour,
        args=[app.client, settings.bot_log_channel_id],
        id="daily_report",
    )

    # Weekly report: Monday at configured hour
    scheduler.add_job(
        post_weekly_report,
        "cron",
        day_of_week="mon",
        hour=settings.daily_report_hour,
        minute=30,
        args=[app.client, settings.bot_log_channel_id],
        id="weekly_report",
    )

    # Memory cleanup: daily at midnight KST
    scheduler.add_job(
        run_memory_cleanup,
        "cron",
        hour=0,
        id="memory_cleanup",
    )

    scheduler.start()
    logger.info("Scheduler started")
    return scheduler


def main():
    settings = get_settings()

    # Initialize database schema
    logger.info("Initializing database schema...")
    init_schema()

    # Create Slack app
    app = create_app()

    # Start scheduler
    scheduler = start_scheduler(app)

    # Start Socket Mode
    logger.info("Starting BCTone bot in Socket Mode...")
    handler = SocketModeHandler(app, settings.slack_app_token)

    try:
        handler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
