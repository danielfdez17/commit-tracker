"""Commit totals from GitHub contribution collections."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from tracker.gh import graphql
from tracker.store import DB_PATH, save_commit_snapshot

_LAST_YEAR_QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    createdAt
    contributionsCollection {
      startedAt
      endedAt
      totalCommitContributions
    }
  }
}
"""

_WINDOW_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
    }
  }
}
"""

_VIEWER_LOGIN_QUERY = """
query {
  viewer {
    login
  }
}
"""


@dataclass(frozen=True)
class CommitReport:
    login: str
    last_year_total: int
    last_year_from: str
    last_year_to: str
    all_time_total: int
    all_time_from: str
    all_time_to: str
    collected_at: str
    snapshot_path: str


def collect_commits(login: str | None = None) -> CommitReport:
    """Fetch last-year and all-time contribution commit totals and store both."""
    resolved = login or graphql(_VIEWER_LOGIN_QUERY)["viewer"]["login"]
    user = graphql(_LAST_YEAR_QUERY, login=resolved)["user"]
    if user is None:
        raise RuntimeError(f"GitHub user {resolved} was not found.")

    collection = user["contributionsCollection"]
    created_at = _parse_datetime(user["createdAt"])
    collected_at = datetime.now(timezone.utc)
    all_time_total = _all_time_commits(user["login"], created_at, collected_at)
    report = CommitReport(
        login=user["login"],
        last_year_total=collection["totalCommitContributions"],
        last_year_from=_date_only(collection["startedAt"]),
        last_year_to=_date_only(collection["endedAt"]),
        all_time_total=all_time_total,
        all_time_from=created_at.date().isoformat(),
        all_time_to=collected_at.date().isoformat(),
        collected_at=collected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        snapshot_path=str(DB_PATH),
    )
    for scope, total, period_from, period_to in (
        ("last_year", report.last_year_total, report.last_year_from, report.last_year_to),
        ("all_time", report.all_time_total, report.all_time_from, report.all_time_to),
    ):
        save_commit_snapshot(
            login=report.login,
            scope=scope,
            total=total,
            period_from=period_from,
            period_to=period_to,
            collected_at=report.collected_at,
        )
    return report


def format_report(report: CommitReport) -> str:
    return "\n".join(
        [
            f"login: {report.login}",
            (
                f"last year: {report.last_year_total} "
                f"({report.last_year_from} → {report.last_year_to})"
            ),
            (
                f"all time: {report.all_time_total} "
                f"({report.all_time_from} → {report.all_time_to})"
            ),
            f"snapshot: {report.snapshot_path}",
        ]
    )


def _all_time_commits(login: str, start: datetime, end: datetime) -> int:
    total = 0
    for window_start, window_end in _windows(start, end):
        data = graphql(
            _WINDOW_QUERY,
            login=login,
            **{
                "from": _format_datetime(window_start),
                "to": _format_datetime(window_end),
            },
        )
        total += data["user"]["contributionsCollection"]["totalCommitContributions"]
    return total


def _windows(start: datetime, end: datetime):
    """Yield adjacent ranges of at most one calendar year."""
    cursor = start.astimezone(timezone.utc)
    end = end.astimezone(timezone.utc)
    while cursor < end:
        window_end = min(datetime(cursor.year + 1, 1, 1, tzinfo=timezone.utc), end)
        if window_end <= cursor:
            break
        yield cursor, window_end
        cursor = window_end


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _format_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _date_only(value: str) -> str:
    return _parse_datetime(value).date().isoformat()
