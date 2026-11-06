"""Current contribution streak from the GitHub contribution calendar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from tracker.gh import graphql
from tracker.store import DB_PATH, save_streak_snapshot

# An empty today does not break the streak; the day is still open.
_DAYS_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    login
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
class StreakReport:
    login: str
    current_streak: int
    streak_from: str | None
    streak_to: str | None
    collected_at: str
    snapshot_path: str


def collect_current_streak(login: str | None = None) -> StreakReport:
    """Count consecutive contribution days ending today, or yesterday if today is empty."""
    resolved = login or graphql(_VIEWER_LOGIN_QUERY)["viewer"]["login"]
    today = datetime.now().astimezone().date()
    collected_at = datetime.now(timezone.utc)
    window_end = collected_at
    days: dict[str, int] = {}
    streak: tuple[int, date | None, date | None] | None = None

    for _ in range(20):
        window_start = window_end - timedelta(days=364)
        days.update(_fetch_days(resolved, window_start, window_end))
        streak = current_streak(days, today)
        if streak is not None:
            break
        window_end = window_start
    else:
        raise RuntimeError("current streak extends past the fetched calendar.")

    length, started, ended = streak
    report = StreakReport(
        login=resolved,
        current_streak=length,
        streak_from=started.isoformat() if started else None,
        streak_to=ended.isoformat() if ended else None,
        collected_at=collected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        snapshot_path=str(DB_PATH),
    )
    save_streak_snapshot(
        login=report.login,
        current_streak=report.current_streak,
        streak_from=report.streak_from,
        streak_to=report.streak_to,
        collected_at=report.collected_at,
    )
    return report


def current_streak(
    days: dict[str, int],
    today: date,
) -> tuple[int, date | None, date | None] | None:
    """Return length, start, and end. None means earlier days are still needed."""
    cursor = today
    today_count = _count_on(days, cursor)
    if today_count is None:
        return None
    if today_count == 0:
        cursor -= timedelta(days=1)
        yesterday_count = _count_on(days, cursor)
        if yesterday_count is None:
            return None
        if yesterday_count == 0:
            return 0, None, None

    end = cursor
    length = 0
    while True:
        count = _count_on(days, cursor)
        if count is None:
            return None
        if count == 0:
            break
        length += 1
        cursor -= timedelta(days=1)

    start = end - timedelta(days=length - 1)
    return length, start, end


def format_report(report: StreakReport) -> str:
    label = "day" if report.current_streak == 1 else "days"
    line = f"current streak: {report.current_streak} {label}"
    if report.streak_from and report.streak_to:
        line = f"{line} ({report.streak_from} → {report.streak_to})"
    return "\n".join(
        [
            f"login: {report.login}",
            line,
            f"snapshot: {report.snapshot_path}",
        ]
    )


def _fetch_days(login: str, start: datetime, end: datetime) -> dict[str, int]:
    data = graphql(
        _DAYS_QUERY,
        login=login,
        **{
            "from": _format_datetime(start),
            "to": _format_datetime(end),
        },
    )
    user = data["user"]
    if user is None:
        raise RuntimeError(f"GitHub user {login} was not found.")
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    days: dict[str, int] = {}
    for week in weeks:
        for day in week["contributionDays"]:
            days[day["date"]] = day["contributionCount"]
    return days


def _count_on(days: dict[str, int], day: date) -> int | None:
    key = day.isoformat()
    if key in days:
        return days[key]
    if not days:
        return None
    # A hole inside a fetched range is an empty day. A day outside it is unknown.
    if min(days) <= key <= max(days):
        return 0
    yesterday = (day - timedelta(days=1)).isoformat()
    if key > max(days) and yesterday in days:
        return 0
    return None


def _format_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
