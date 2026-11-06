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
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS streak_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            current_streak INTEGER NOT NULL,
            streak_from TEXT,
            streak_to TEXT,
            collected_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS longest_streak_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            longest_streak INTEGER NOT NULL,
            streak_from TEXT,
            streak_to TEXT,
            collected_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS language_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            language TEXT NOT NULL,
            color TEXT,
            bytes INTEGER NOT NULL,
            share REAL NOT NULL,
            rank INTEGER NOT NULL,
            repository_count INTEGER NOT NULL,
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


def save_streak_snapshot(
    *,
    login: str,
    current_streak: int,
    streak_from: str | None,
    streak_to: str | None,
    collected_at: str,
) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO streak_snapshots (
                login, current_streak, streak_from, streak_to, collected_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (login, current_streak, streak_from, streak_to, collected_at),
        )


def save_longest_streak_snapshot(
    *,
    login: str,
    longest_streak: int,
    streak_from: str | None,
    streak_to: str | None,
    collected_at: str,
) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO longest_streak_snapshots (
                login, longest_streak, streak_from, streak_to, collected_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (login, longest_streak, streak_from, streak_to, collected_at),
        )


def save_language_snapshots(
    *,
    login: str,
    repository_count: int,
    collected_at: str,
    languages: tuple,
) -> None:
    with connect() as connection:
        connection.executemany(
            """
            INSERT INTO language_snapshots (
                login, language, color, bytes, share, rank,
                repository_count, collected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    login,
                    language.name,
                    language.color,
                    language.size,
                    language.share,
                    language.rank,
                    repository_count,
                    collected_at,
                )
                for language in languages
            ],
        )
