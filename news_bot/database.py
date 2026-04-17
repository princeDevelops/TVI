import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent / "seen_articles.db"


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(str(DB_PATH))


def init_db() -> None:
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_articles (
                id         TEXT PRIMARY KEY,
                title      TEXT,
                source     TEXT,
                category   TEXT,
                url        TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_stories (
                id             TEXT PRIMARY KEY,
                title          TEXT,
                tweaked_title  TEXT,
                summary        TEXT,
                why_it_matters TEXT,
                category       TEXT,
                source         TEXT,
                url            TEXT,
                image_url      TEXT,
                posted_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Tracks API call counts per service per UTC date for budget enforcement.
        # One row per (service, date). Resets naturally as dates change.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                service    TEXT    NOT NULL,
                date_utc   TEXT    NOT NULL,
                calls      INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (service, date_utc)
            )
        """)
        conn.commit()


def purge_old_stories() -> None:
    with _conn() as conn:
        conn.execute(
            "DELETE FROM daily_stories WHERE posted_at < datetime('now', '-48 hours')"
        )
        conn.commit()


def _article_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def is_seen(url: str) -> bool:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id FROM seen_articles WHERE id = ?", (_article_id(url),)
        ).fetchone()
    return row is not None


def mark_seen(article: dict) -> None:
    with _conn() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO seen_articles (id, title, source, category, url)
               VALUES (?, ?, ?, ?, ?)""",
            (
                _article_id(article["url"]),
                article.get("title", ""),
                article.get("source", ""),
                article.get("category", ""),
                article["url"],
            ),
        )
        conn.commit()


def save_daily_story(article: dict, ai_result: dict) -> None:
    summary = "\n".join(ai_result.get("summary_points", []))
    with _conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO daily_stories
               (id, title, tweaked_title, summary, why_it_matters, category, source, url, image_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                _article_id(article["url"]),
                article.get("title", ""),
                ai_result.get("tweaked_title") or article.get("title", ""),
                summary,
                ai_result.get("why_it_matters", ""),
                ai_result.get("category_refined") or article.get("category", ""),
                article.get("source", ""),
                article["url"],
                article.get("image_url"),
            ),
        )
        conn.commit()


def api_calls_today(service: str) -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _conn() as conn:
        row = conn.execute(
            "SELECT calls FROM api_usage WHERE service = ? AND date_utc = ?",
            (service, today),
        ).fetchone()
    return row[0] if row else 0


def record_api_call(service: str) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _conn() as conn:
        conn.execute(
            """INSERT INTO api_usage (service, date_utc, calls) VALUES (?, ?, 1)
               ON CONFLICT(service, date_utc) DO UPDATE SET calls = calls + 1""",
            (service, today),
        )
        conn.commit()


def get_api_usage_summary() -> dict[str, int]:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _conn() as conn:
        rows = conn.execute(
            "SELECT service, calls FROM api_usage WHERE date_utc = ?", (today,)
        ).fetchall()
    return {r[0]: r[1] for r in rows}


def get_recent_stories(hours: int = 24) -> list:
    with _conn() as conn:
        rows = conn.execute(
            """SELECT title, tweaked_title, summary, why_it_matters, category, source, url
               FROM daily_stories
               WHERE posted_at > datetime('now', ?)
               ORDER BY posted_at DESC""",
            (f"-{hours} hours",),
        ).fetchall()
    return [
        {
            "title": r[0],
            "tweaked_title": r[1],
            "summary": r[2],
            "why_it_matters": r[3],
            "category": r[4],
            "source": r[5],
            "url": r[6],
        }
        for r in rows
    ]
