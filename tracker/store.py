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
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS commit_snapshots (
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
        CREATE TABLE IF NOT EXISTS pull_request_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            opened INTEGER NOT NULL,
            open_count INTEGER NOT NULL,
            closed_count INTEGER NOT NULL,
            merged_count INTEGER NOT NULL,
            collected_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS issue_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            opened INTEGER NOT NULL,
            open_count INTEGER NOT NULL,
            closed_count INTEGER NOT NULL,
            collected_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS weekly_commit_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            week_start TEXT NOT NULL,
            commits INTEGER NOT NULL,
            collected_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS yearly_contribution_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            year INTEGER NOT NULL,
            contributions INTEGER NOT NULL,
            collected_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS public_repository_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            public_count INTEGER NOT NULL,
            source_count INTEGER NOT NULL,
            fork_count INTEGER NOT NULL,
            collected_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS follower_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            followers INTEGER NOT NULL,
            collected_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS follower_member_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            follower_login TEXT NOT NULL,
            collected_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS follower_change_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            follower_login TEXT NOT NULL,
            change TEXT NOT NULL,
            collected_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS following_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            following INTEGER NOT NULL,
            user_count INTEGER NOT NULL,
            organization_count INTEGER NOT NULL,
            collected_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS following_member_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            followed_login TEXT NOT NULL,
            account_type TEXT NOT NULL,
            collected_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS organization_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            organizations INTEGER NOT NULL,
            collected_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS organization_member_snapshots (
            id INTEGER PRIMARY KEY,
            login TEXT NOT NULL,
            organization_login TEXT NOT NULL,
            role TEXT NOT NULL,
            state TEXT NOT NULL,
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


def save_commit_snapshot(
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
            INSERT INTO commit_snapshots (
                login, scope, total, period_from, period_to, collected_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (login, scope, total, period_from, period_to, collected_at),
        )


def save_pull_request_snapshot(
    *,
    login: str,
    opened: int,
    open_count: int,
    closed_count: int,
    merged_count: int,
    collected_at: str,
) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO pull_request_snapshots (
                login, opened, open_count, closed_count, merged_count, collected_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (login, opened, open_count, closed_count, merged_count, collected_at),
        )


def save_issue_snapshot(
    *,
    login: str,
    opened: int,
    open_count: int,
    closed_count: int,
    collected_at: str,
) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO issue_snapshots (
                login, opened, open_count, closed_count, collected_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (login, opened, open_count, closed_count, collected_at),
        )


def save_weekly_commit_snapshots(
    *,
    login: str,
    collected_at: str,
    weeks: tuple,
) -> None:
    with connect() as connection:
        connection.executemany(
            """
            INSERT INTO weekly_commit_snapshots (
                login, week_start, commits, collected_at
            ) VALUES (?, ?, ?, ?)
            """,
            [
                (login, week.week_start, week.commits, collected_at)
                for week in weeks
            ],
        )


def save_yearly_contribution_snapshots(
    *,
    login: str,
    collected_at: str,
    years: tuple,
) -> None:
    with connect() as connection:
        connection.executemany(
            """
            INSERT INTO yearly_contribution_snapshots (
                login, year, contributions, collected_at
            ) VALUES (?, ?, ?, ?)
            """,
            [
                (login, year.year, year.contributions, collected_at)
                for year in years
            ],
        )


def save_public_repository_snapshot(
    *,
    login: str,
    public_count: int,
    source_count: int,
    fork_count: int,
    collected_at: str,
) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO public_repository_snapshots (
                login, public_count, source_count, fork_count, collected_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (login, public_count, source_count, fork_count, collected_at),
        )


def save_follower_snapshot(
    *,
    login: str,
    followers: int,
    follower_logins: tuple[str, ...],
    collected_at: str,
) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO follower_snapshots (
                login, followers, collected_at
            ) VALUES (?, ?, ?)
            """,
            (login, followers, collected_at),
        )
        connection.executemany(
            """
            INSERT INTO follower_member_snapshots (
                login, follower_login, collected_at
            ) VALUES (?, ?, ?)
            """,
            [(login, follower_login, collected_at) for follower_login in follower_logins],
        )


def latest_follower_logins(login: str, before: str | None = None) -> tuple[str, ...] | None:
    """Return the newest stored follower list, or None when no snapshot exists."""
    sql = """
        SELECT collected_at FROM follower_snapshots
        WHERE login = ?
    """
    parameters: list[str] = [login]
    if before is not None:
        sql += " AND collected_at < ?"
        parameters.append(before)
    sql += " ORDER BY collected_at DESC LIMIT 1"
    with connect() as connection:
        row = connection.execute(sql, parameters).fetchone()
        if row is None:
            return None
        members = connection.execute(
            """
            SELECT follower_login FROM follower_member_snapshots
            WHERE login = ? AND collected_at = ?
            """,
            (login, row["collected_at"]),
        ).fetchall()
    return tuple(member["follower_login"] for member in members)


def save_follower_changes(
    *,
    login: str,
    followed: tuple[str, ...],
    unfollowed: tuple[str, ...],
    collected_at: str,
) -> None:
    rows = [(login, follower_login, "followed", collected_at) for follower_login in followed]
    rows.extend(
        (login, follower_login, "unfollowed", collected_at) for follower_login in unfollowed
    )
    with connect() as connection:
        connection.executemany(
            """
            INSERT INTO follower_change_snapshots (
                login, follower_login, change, collected_at
            ) VALUES (?, ?, ?, ?)
            """,
            rows,
        )


def save_following_snapshot(
    *,
    login: str,
    following: int,
    user_count: int,
    organization_count: int,
    users: tuple[str, ...],
    organizations: tuple[str, ...],
    collected_at: str,
) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO following_snapshots (
                login, following, user_count, organization_count, collected_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (login, following, user_count, organization_count, collected_at),
        )
        connection.executemany(
            """
            INSERT INTO following_member_snapshots (
                login, followed_login, account_type, collected_at
            ) VALUES (?, ?, ?, ?)
            """,
            [(login, followed_login, "User", collected_at) for followed_login in users]
            + [
                (login, followed_login, "Organization", collected_at)
                for followed_login in organizations
            ],
        )


def save_organization_snapshot(
    *,
    login: str,
    organizations: tuple,
    collected_at: str,
) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO organization_snapshots (
                login, organizations, collected_at
            ) VALUES (?, ?, ?)
            """,
            (login, len(organizations), collected_at),
        )
        connection.executemany(
            """
            INSERT INTO organization_member_snapshots (
                login, organization_login, role, state, collected_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (login, organization.login, organization.role, organization.state, collected_at)
                for organization in organizations
            ],
        )
