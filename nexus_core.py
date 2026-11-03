"""Small, dependency-free primitives for the NEXUS coordination bot."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_TERMS = (
    "گزارش", "وضعیت", "خلاصه پروژه", "بررسی پروژه", "ریسک", "باگ",
    "خطاها", "نقاط قوت", "نقاط ضعف", "پیشنهاد بهبود", "health",
    "project status", "project report", "repository report",
)
GITHUB_TERMS = (
    "گیت هاب", "github", "commit", "کامیت", "branch", "شاخه",
    "pull request", "پول ریکوئست", "pr ", "issue", "ایشیو",
    "ریپو", "repository", "فایل", "کد", "readme", ".py", ".tsx", ".ts",
    ".json", ".yaml", ".yml", "workflow", "pipeline", "وضعیت ci", "آخرین تغییرات",
)
COORDINATION_TERMS = (
    "ایجنت", "agent", "هماهنگی", "فعالیت اعضا", "چه کسی",
    "چه کار", "پیشرفت تیم", "گزارش تیم", "گزارش فعالیت",
)
REQUEST_TERMS = (
    "لطفا", "لطفاً", "بررسی کن", "بررسی کن", "بگو", "توضیح بده",
    "نشان بده", "نمایش بده", "تهیه کن", "جمع بندی", "جمع‌بندی",
    "تحلیل کن", "بخون", "بخوان", "پیدا کن", "مقایسه کن", "کمک",
    "please", "explain", "show", "check", "review", "summarize",
    "analyze", "compare", "help",
)


def parse_channel_ids(value: str | None) -> set[int]:
    """Parse a comma-separated list of Discord snowflakes."""
    result: set[int] = set()
    for item in (value or "").split(","):
        item = item.strip()
        if not item:
            continue
        if not item.isdecimal():
            raise ValueError(f"Invalid Discord channel ID: {item!r}")
        result.add(int(item))
    return result


def parse_user_ids(value: str | None) -> set[int]:
    """Parse a comma-separated list of Discord user/bot IDs."""
    return parse_channel_ids(value)


def classify_message(text: str) -> str:
    """Return report, github, coordination, chat, or ignore."""
    normalized = re.sub(r"\s+", " ", text.casefold()).strip()
    if not normalized:
        return "ignore"

    if any(term in normalized for term in COORDINATION_TERMS):
        return "coordination"
    if any(term in normalized for term in REPORT_TERMS):
        return "report"
    if any(term in normalized for term in GITHUB_TERMS):
        return "github"
    if "?" in normalized or "؟" in normalized:
        return "chat"
    if any(term in normalized for term in REQUEST_TERMS):
        return "chat"
    return "ignore"


class ActivityStore:
    """Persistent, bounded Discord activity history backed by SQLite."""

    def __init__(self, database_path: str, retention_days: int = 30) -> None:
        self.database_path = database_path
        self.retention_days = max(1, retention_days)
        if database_path != ":memory:":
            Path(database_path).expanduser().parent.mkdir(
                parents=True, exist_ok=True
            )
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE NOT NULL,
                    channel_id TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    is_bot INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_activity_created "
                "ON activity(created_at)"
            )

    def record(
        self,
        *,
        message_id: int | str,
        channel_id: int | str,
        author_id: int | str,
        author_name: str,
        is_bot: bool,
        content: str,
        created_at: datetime | None = None,
    ) -> None:
        timestamp = (created_at or datetime.now(timezone.utc)).astimezone(
            timezone.utc
        ).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO activity
                (message_id, channel_id, author_id, author_name, is_bot,
                 content, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(message_id), str(channel_id), str(author_id),
                    author_name[:100], int(is_bot), content[:6000], timestamp,
                ),
            )
            connection.execute(
                "DELETE FROM activity WHERE created_at < datetime('now', ?)",
                (f"-{self.retention_days} days",),
            )

    def recent(self, limit: int = 60) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT author_name, is_bot, content, created_at, channel_id
                FROM activity ORDER BY id DESC LIMIT ?
                """,
                (max(1, min(limit, 200)),),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def get_setting(self, key: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
        return row["value"] if row else None

    def set_setting(self, key: str, value: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO settings(key, value) VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )


def format_activity(events: list[dict[str, Any]], limit: int = 40) -> str:
    """Create a compact, chronological evidence block for the report model."""
    if not events:
        return "در بازه ذخیره‌شده، فعالیتی در کانال‌های پایش‌شده ثبت نشده است."
    lines = []
    for event in events[-limit:]:
        role = "ایجنت" if event.get("is_bot") else "عضو"
        content = re.sub(r"\s+", " ", event.get("content", "")).strip()
        if not content:
            continue
        lines.append(
            f"- [{event.get('created_at', '')}] "
            f"{role} {event.get('author_name', 'unknown')}: {content[:500]}"
        )
    return "\n".join(lines) or "پیام متنی قابل استفاده‌ای ثبت نشده است."


def format_github_snapshot(snapshot: dict[str, Any]) -> str:
    """Serialize GitHub facts without silently inventing missing values."""
    return json.dumps(snapshot, ensure_ascii=False, indent=2, default=str)
