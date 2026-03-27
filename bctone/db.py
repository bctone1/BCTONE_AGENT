import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS bctone;

CREATE TABLE IF NOT EXISTS bctone.memories (
    id             SERIAL PRIMARY KEY,
    category       VARCHAR(20) NOT NULL,
    source_user    VARCHAR(50) NOT NULL,
    source_channel VARCHAR(50) NOT NULL,
    content        TEXT NOT NULL,
    summary        TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    expires_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS bctone.conversations (
    id          SERIAL PRIMARY KEY,
    channel_id  VARCHAR(50) NOT NULL,
    thread_ts   VARCHAR(50),
    role        VARCHAR(10) NOT NULL,
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bctone.reports (
    id          SERIAL PRIMARY KEY,
    report_type VARCHAR(20) NOT NULL,
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memories_category ON bctone.memories (category);
CREATE INDEX IF NOT EXISTS idx_memories_created ON bctone.memories (created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_channel ON bctone.conversations (channel_id, thread_ts);
"""


def get_connection():
    db_url = os.getenv("BCTONE_DB_URL", "")
    return psycopg2.connect(db_url)


def init_schema():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()
