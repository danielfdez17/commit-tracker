"""Contribution streaks from the GitHub contribution calendar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from tracker.gh import graphql
from tracker.store import DB_PATH, save_longest_streak_snapshot, save_streak_snapshot

# GraphQL rejects a from/to span longer than one year.
_WINDOW_SPAN = timedelta(days=364)
_WINDOW_STEP = timedelta(days=360)

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

_USER_QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    createdAt
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


@dataclass(frozen=True)
class LongestStreakReport:
    login: str
    longest_streak: int
    streak_from: str | None
    streak_to: str | None
    collected_at: str
    snapshot_path: str


def collect_longest_streak(login: str | None = None) -> LongestStreakReport:
    """Find the longest run of consecutive contribution days since the account was created."""
    resolved = login or graphql(_VIEWER_LOGIN_QUERY)["viewer"]["login"]
    user = graphql(_USER_QUERY, login=resolved)["user"]
    if user is None:
        raise RuntimeError(f"GitHub user {resolved} was not found.")

    created_at = _parse_datetime(user["createdAt"])
    collected_at = datetime.now(timezone.utc)
    days = _contribution_days(user["login"], created_at, collected_at)
    length, started, ended = longest_streak(days)
    report = LongestStreakReport(
        login=user["login"],
        longest_streak=length,
        streak_from=started.isoformat() if started else None,
        streak_to=ended.isoformat() if ended else None,
        collected_at=collected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        snapshot_path=str(DB_PATH),
    )
    save_longest_streak_snapshot(
        login=report.login,
        longest_streak=report.longest_streak,
        streak_from=report.streak_from,
        streak_to=report.streak_to,
        collected_at=report.collected_at,
    )
    return report


def longest_streak(days: dict[str, int]) -> tuple[int, date | None, date | None]:
    """Return the longest run. An equal later run replaces an earlier one."""
    if not days:
        return 0, None, None

    cursor = date.fromisoformat(min(days))
    last = date.fromisoformat(max(days))
    best = 0
    best_start: date | None = None
    best_end: date | None = None
    run = 0
    run_start: date | None = None

    while cursor <= last:
        if days.get(cursor.isoformat(), 0) > 0:
            if run == 0:
                run_start = cursor
            run += 1
            if run >= best and run_start is not None:
                best = run
                best_start = run_start
                best_end = cursor
        else:
            run = 0
        cursor += timedelta(days=1)

    return best, best_start, best_end


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


def format_longest_report(report: LongestStreakReport) -> str:
    label = "day" if report.longest_streak == 1 else "days"
    line = f"longest streak: {report.longest_streak} {label}"
    if report.streak_from and report.streak_to:
        line = f"{line} ({report.streak_from} → {report.streak_to})"
    return "\n".join(
        [
            f"login: {report.login}",
            line,
            f"snapshot: {report.snapshot_path}",
        ]
    )


def _contribution_days(login: str, start: datetime, end: datetime) -> dict[str, int]:
    days: dict[str, int] = {}
    first = start.date().isoformat()
    last = end.date().isoformat()
    for window_start, window_end in _windows(start, end):
        for key, count in _fetch_days(login, window_start, window_end).items():
            if first <= key <= last:
                days[key] = count
    return days


def _windows(start: datetime, end: datetime):
    cursor = start
    while cursor < end:
        window_end = min(cursor + _WINDOW_SPAN, end)
        yield cursor, window_end
        if window_end >= end:
            break
        cursor = cursor + _WINDOW_STEP


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


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
