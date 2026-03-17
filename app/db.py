import sqlite3
import logging
from datetime import datetime, timezone

from config import DB_PATH

logger = logging.getLogger(__name__)


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sent_notifications (
                match_id          TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                sent_at           TEXT NOT NULL,
                PRIMARY KEY (match_id, notification_type)
            )
        """)
        conn.commit()
    logger.info("Banco de dados inicializado em %s", DB_PATH)


def is_sent(match_id: str, notification_type: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "SELECT 1 FROM sent_notifications WHERE match_id = ? AND notification_type = ?",
            (match_id, notification_type),
        )
        return cur.fetchone() is not None


def mark_sent(match_id: str, notification_type: str):
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sent_notifications (match_id, notification_type, sent_at) VALUES (?, ?, ?)",
            (match_id, notification_type, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
