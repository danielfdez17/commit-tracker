"""Total contributions from the GitHub contribution calendar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from tracker.gh import graphql
from tracker.store import DB_PATH, save_contribution_snapshot

# GraphQL rejects a from/to span longer than one year. Windows stay under that
# limit and overlap so a day on the seam is collected twice and counted once.
_WINDOW_SPAN = timedelta(days=364)
_WINDOW_STEP = timedelta(days=360)

_LAST_YEAR_QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    createdAt
    contributionsCollection {
      startedAt
      endedAt
      contributionCalendar {
        totalContributions
      }
    }
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
class ContributionReport:
    login: str
    last_year_total: int
    last_year_from: str
    last_year_to: str
    all_time_total: int
    all_time_from: str
    all_time_to: str
    collected_at: str
    snapshot_path: str


def collect_contributions(login: str | None = None) -> ContributionReport:
    """Fetch last-year and all-time contribution totals and store both."""
    resolved = login or _viewer_login()
    user = graphql(_LAST_YEAR_QUERY, login=resolved)["user"]
    if user is None:
        raise RuntimeError(f"GitHub user {resolved} was not found.")

    calendar = user["contributionsCollection"]
    created_at = _parse_datetime(user["createdAt"])
    collected_at = datetime.now(timezone.utc)
    days = _contribution_days(resolved, created_at, collected_at)

    report = ContributionReport(
        login=user["login"],
        last_year_total=calendar["contributionCalendar"]["totalContributions"],
        last_year_from=_date_only(calendar["startedAt"]),
        last_year_to=_date_only(calendar["endedAt"]),
        all_time_total=sum(days.values()),
        all_time_from=min(days) if days else created_at.date().isoformat(),
        all_time_to=max(days) if days else collected_at.date().isoformat(),
        collected_at=collected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        snapshot_path=str(DB_PATH),
    )
    _save(report)
    return report


def format_report(report: ContributionReport) -> str:
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


def _viewer_login() -> str:
    return graphql(_VIEWER_LOGIN_QUERY)["viewer"]["login"]


def _contribution_days(login: str, start: datetime, end: datetime) -> dict[str, int]:
    days: dict[str, int] = {}
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
                if date < start.date().isoformat() or date > end.date().isoformat():
                    continue
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


def _save(report: ContributionReport) -> None:
    for scope, total, period_from, period_to in (
        ("last_year", report.last_year_total, report.last_year_from, report.last_year_to),
        ("all_time", report.all_time_total, report.all_time_from, report.all_time_to),
    ):
        save_contribution_snapshot(
            login=report.login,
            scope=scope,
            total=total,
            period_from=period_from,
            period_to=period_to,
            collected_at=report.collected_at,
        )


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _format_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _date_only(value: str) -> str:
    return _parse_datetime(value).date().isoformat()
