"""SQLite history for collected GitHub stats."""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "tracker.sqlite"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS contribution_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            scope TEXT NOT NULL,
            total INTEGER NOT NULL,
            period_from TEXT NOT NULL,
            period_to TEXT NOT NULL,
            collected_at TEXT NOT NULL
        )
        """
    )
    return connection


def save_contribution_snapshot(
    *,
    login: str,
    scope: str,
    total: int,
    period_from: str,
    period_to: str,
    collected_at: str,
) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO contribution_snapshots (
                login, scope, total, period_from, period_to, collected_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (login, scope, total, period_from, period_to, collected_at),
        )
