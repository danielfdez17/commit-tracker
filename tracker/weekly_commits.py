"""Contribution commits grouped by week."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from tracker.gh import graphql
from tracker.store import DB_PATH, save_weekly_commit_snapshots

_REPOSITORY_CAP = 100

_WEEKS_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    login
    contributionsCollection {
      startedAt
      endedAt
      commitContributionsByRepository(maxRepositories: 100) {
        contributions(first: 100, after: $after) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            commitCount
            occurredAt
          }
        }
      }
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
class WeekCommits:
    week_start: str
    commits: int


@dataclass(frozen=True)
class WeeklyCommitReport:
    login: str
    period_from: str
    period_to: str
    weeks: tuple[WeekCommits, ...]
    total: int
    repository_count: int
    collected_at: str
    snapshot_path: str


def collect_weekly_commits(login: str | None = None) -> WeeklyCommitReport:
    """Count contribution commits for each Sunday-start week in the last year."""
    resolved = login or graphql(_VIEWER_LOGIN_QUERY)["viewer"]["login"]
    days, canonical, started_at, ended_at, repository_count = _commit_days(resolved)
    weeks = tuple(
        WeekCommits(week_start=week.isoformat(), commits=count)
        for week, count in _weekly_totals(days, started_at, ended_at)
    )
    collected_at = datetime.now(timezone.utc)
    report = WeeklyCommitReport(
        login=canonical,
        period_from=_date_only(started_at),
        period_to=_date_only(ended_at),
        weeks=weeks,
        total=sum(week.commits for week in weeks),
        repository_count=repository_count,
        collected_at=collected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        snapshot_path=str(DB_PATH),
    )
    save_weekly_commit_snapshots(
        login=report.login,
        collected_at=report.collected_at,
        weeks=report.weeks,
    )
    return report


def format_report(report: WeeklyCommitReport) -> str:
    lines = [
        f"login: {report.login}",
        f"window: {report.period_from} → {report.period_to}",
    ]
    lines.extend(f"{week.week_start}  {week.commits}" for week in report.weeks)
    lines.append(f"total: {report.total}")
    if report.repository_count >= _REPOSITORY_CAP:
        lines.append(f"repositories: {report.repository_count} (API returns at most 100)")
    lines.append(f"snapshot: {report.snapshot_path}")
    return "\n".join(lines)


def _commit_days(login: str) -> tuple[dict[date, int], str, str, str, int]:
    days: dict[date, int] = {}
    cursor: str | None = None
    canonical = login
    started_at = ""
    ended_at = ""
    repository_count = 0

    for _ in range(6):
        variables = {"login": login}
        if cursor is not None:
            variables["after"] = cursor
        user = graphql(_WEEKS_QUERY, **variables)["user"]
        if user is None:
            raise RuntimeError(f"GitHub user {login} was not found.")
        canonical = user["login"]
        collection = user["contributionsCollection"]
        started_at = collection["startedAt"]
        ended_at = collection["endedAt"]
        groups = collection["commitContributionsByRepository"]
        repository_count = len(groups)
        next_cursor = None
        for group in groups:
            page = group["contributions"]
            for node in page["nodes"]:
                day = _parse_datetime(node["occurredAt"]).date()
                days[day] = days.get(day, 0) + node["commitCount"]
            if page["pageInfo"]["hasNextPage"]:
                next_cursor = page["pageInfo"]["endCursor"]
        if next_cursor is None:
            break
        cursor = next_cursor
    else:
        raise RuntimeError("weekly commit scan stopped after 600 days in one repository.")

    return days, canonical, started_at, ended_at, repository_count


def _weekly_totals(days: dict[date, int], started_at: str, ended_at: str):
    totals: dict[date, int] = {}
    for day, count in days.items():
        week = _sunday(day)
        totals[week] = totals.get(week, 0) + count

    start = _sunday(_parse_datetime(started_at).date())
    end = _sunday(_parse_datetime(ended_at).date())
    if totals:
        start = min(start, min(totals))
        end = max(end, max(totals))

    cursor = start
    while cursor <= end:
        yield cursor, totals.get(cursor, 0)
        cursor += timedelta(days=7)


def _sunday(day: date) -> date:
    return day - timedelta(days=(day.weekday() + 1) % 7)


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _date_only(value: str) -> str:
    return _parse_datetime(value).date().isoformat()
