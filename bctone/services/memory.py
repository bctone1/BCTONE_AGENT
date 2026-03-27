from datetime import datetime, timedelta, timezone
from bctone.db import get_connection


def save_memory(
    category: str,
    source_user: str,
    source_channel: str,
    content: str,
    summary: str | None = None,
    expiry_days: int | None = None,
):
    expires_at = None
    if expiry_days is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expiry_days)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bctone.memories
                    (category, source_user, source_channel, content, summary, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (category, source_user, source_channel, content, summary, expires_at),
            )
        conn.commit()
    finally:
        conn.close()


def get_recent_memories(limit: int = 20, category: str | None = None) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if category:
                cur.execute(
                    """
                    SELECT id, category, source_user, source_channel, content, summary, created_at, expires_at
                    FROM bctone.memories
                    WHERE category = %s
                      AND (expires_at IS NULL OR expires_at > NOW())
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (category, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT id, category, source_user, source_channel, content, summary, created_at, expires_at
                    FROM bctone.memories
                    WHERE expires_at IS NULL OR expires_at > NOW()
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        {
            "id": r[0],
            "category": r[1],
            "source_user": r[2],
            "source_channel": r[3],
            "content": r[4],
            "summary": r[5],
            "created_at": r[6],
            "expires_at": r[7],
        }
        for r in rows
    ]


def save_conversation(channel_id: str, thread_ts: str | None, role: str, content: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bctone.conversations (channel_id, thread_ts, role, content)
                VALUES (%s, %s, %s, %s)
                """,
                (channel_id, thread_ts, role, content),
            )
        conn.commit()
    finally:
        conn.close()


def get_conversation_history(
    channel_id: str, thread_ts: str | None = None, limit: int = 20
) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if thread_ts:
                cur.execute(
                    """
                    SELECT id, channel_id, thread_ts, role, content, created_at
                    FROM bctone.conversations
                    WHERE channel_id = %s AND thread_ts = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (channel_id, thread_ts, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT id, channel_id, thread_ts, role, content, created_at
                    FROM bctone.conversations
                    WHERE channel_id = %s AND thread_ts IS NULL
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (channel_id, limit),
                )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        {
            "id": r[0],
            "channel_id": r[1],
            "thread_ts": r[2],
            "role": r[3],
            "content": r[4],
            "created_at": r[5],
        }
        for r in rows
    ]


def cleanup_expired() -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM bctone.memories
                WHERE expires_at IS NOT NULL AND expires_at < NOW()
                """
            )
            count = cur.rowcount
        conn.commit()
    finally:
        conn.close()
    return count
