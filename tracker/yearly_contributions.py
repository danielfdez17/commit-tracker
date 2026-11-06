"""Contribution totals for each calendar year."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from tracker.gh import graphql
from tracker.store import DB_PATH, save_yearly_contribution_snapshots

# GraphQL rejects a from/to span longer than one year. Windows overlap so a
# day on the seam is collected twice and counted once.
_WINDOW_SPAN = timedelta(days=364)
_WINDOW_STEP = timedelta(days=360)

_USER_QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    createdAt
  }
}
"""

_DAYS_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
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
class YearContributions:
    year: int
    contributions: int


@dataclass(frozen=True)
class YearlyContributionReport:
    login: str
    years: tuple[YearContributions, ...]
    total: int
    collected_at: str
    snapshot_path: str


def collect_yearly_contributions(login: str | None = None) -> YearlyContributionReport:
    """Sum contribution-calendar days into the calendar year of each day."""
    resolved = login or graphql(_VIEWER_LOGIN_QUERY)["viewer"]["login"]
    user = graphql(_USER_QUERY, login=resolved)["user"]
    if user is None:
        raise RuntimeError(f"GitHub user {resolved} was not found.")

    created_at = _parse_datetime(user["createdAt"])
    collected_at = datetime.now(timezone.utc)
    days = _contribution_days(user["login"], created_at, collected_at)
    years = contributions_by_year(days, created_at.year, collected_at.year)
    report = YearlyContributionReport(
        login=user["login"],
        years=years,
        total=sum(year.contributions for year in years),
        collected_at=collected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        snapshot_path=str(DB_PATH),
    )
    save_yearly_contribution_snapshots(
        login=report.login,
        collected_at=report.collected_at,
        years=report.years,
    )
    return report


def contributions_by_year(
    days: dict[str, int],
    first_year: int,
    last_year: int,
) -> tuple[YearContributions, ...]:
    """Count each calendar day in its own year. Missing years are zero."""
    totals = {year: 0 for year in range(first_year, last_year + 1)}
    for day, count in days.items():
        year = int(day[:4])
        if year in totals:
            totals[year] += count
    return tuple(
        YearContributions(year=year, contributions=totals[year])
        for year in range(first_year, last_year + 1)
    )


def format_report(report: YearlyContributionReport) -> str:
    lines = [f"login: {report.login}"]
    lines.extend(f"{year.year}  {year.contributions}" for year in report.years)
    lines.append(f"total: {report.total}")
    lines.append(f"snapshot: {report.snapshot_path}")
    return "\n".join(lines)


def _contribution_days(login: str, start: datetime, end: datetime) -> dict[str, int]:
    days: dict[str, int] = {}
    first = start.date().isoformat()
    last = end.date().isoformat()
    for window_start, window_end in _windows(start, end):
        data = graphql(
            _DAYS_QUERY,
            login=login,
            **{
                "from": _format_datetime(window_start),
                "to": _format_datetime(window_end),
            },
        )
        weeks = data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        for week in weeks:
            for day in week["contributionDays"]:
                date = day["date"]
                if first <= date <= last:
                    days[date] = day["contributionCount"]
    return days


def _windows(start: datetime, end: datetime):
    cursor = start
    while cursor < end:
        window_end = min(cursor + _WINDOW_SPAN, end)
        yield cursor, window_end
        if window_end >= end:
            break
        cursor = cursor + _WINDOW_STEP


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _format_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
