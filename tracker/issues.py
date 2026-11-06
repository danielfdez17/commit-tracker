"""Issues opened by a GitHub user."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from tracker.gh import graphql
from tracker.store import DB_PATH, save_issue_snapshot

_ISSUES_QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    issues {
      totalCount
    }
    open: issues(states: OPEN) {
      totalCount
    }
    closed: issues(states: CLOSED) {
      totalCount
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
class IssueReport:
    login: str
    opened: int
    open_count: int
    closed_count: int
    collected_at: str
    snapshot_path: str


def collect_issues(login: str | None = None) -> IssueReport:
    """Count issues the user opened, split by open and closed."""
    resolved = login or graphql(_VIEWER_LOGIN_QUERY)["viewer"]["login"]
    user = graphql(_ISSUES_QUERY, login=resolved)["user"]
    if user is None:
        raise RuntimeError(f"GitHub user {resolved} was not found.")

    collected_at = datetime.now(timezone.utc)
    report = IssueReport(
        login=user["login"],
        opened=user["issues"]["totalCount"],
        open_count=user["open"]["totalCount"],
        closed_count=user["closed"]["totalCount"],
        collected_at=collected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        snapshot_path=str(DB_PATH),
    )
    save_issue_snapshot(
        login=report.login,
        opened=report.opened,
        open_count=report.open_count,
        closed_count=report.closed_count,
        collected_at=report.collected_at,
    )
    return report


def format_report(report: IssueReport) -> str:
    return "\n".join(
        [
            f"login: {report.login}",
            f"opened: {report.opened}",
            f"open: {report.open_count}",
            f"closed: {report.closed_count}",
            f"snapshot: {report.snapshot_path}",
        ]
    )
