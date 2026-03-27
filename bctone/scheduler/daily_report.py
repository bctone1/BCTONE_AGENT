import logging
from bctone.db import get_connection
from bctone.services.summarizer import generate_daily_report, generate_weekly_report
from bctone.services.memory import cleanup_expired

logger = logging.getLogger("bctone.scheduler")


def save_report(report_type: str, content: str):
    """Archive a report to the database."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO bctone.reports (report_type, content) VALUES (%s, %s)",
                (report_type, content),
            )
        conn.commit()
    finally:
        conn.close()


def post_daily_report(slack_client, channel_id: str):
    """Generate and post daily report to #bot-log."""
    try:
        report = generate_daily_report()
        slack_client.chat_postMessage(channel=channel_id, text=report)
        save_report("daily", report)
        logger.info("Daily report posted successfully")
    except Exception as e:
        logger.error(f"Failed to post daily report: {e}")


def post_weekly_report(slack_client, channel_id: str):
    """Generate and post weekly report to #bot-log."""
    try:
        report = generate_weekly_report()
        slack_client.chat_postMessage(channel=channel_id, text=report)
        save_report("weekly", report)
        logger.info("Weekly report posted successfully")
    except Exception as e:
        logger.error(f"Failed to post weekly report: {e}")


def run_memory_cleanup():
    """Delete expired memory records."""
    try:
        count = cleanup_expired()
        logger.info(f"Cleaned up {count} expired memory records")
    except Exception as e:
        logger.error(f"Failed to cleanup expired memories: {e}")
