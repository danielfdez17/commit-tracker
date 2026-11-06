"""Pull requests opened by a GitHub user."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from tracker.gh import graphql
from tracker.store import DB_PATH, save_pull_request_snapshot

_PULL_REQUESTS_QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    pullRequests {
      totalCount
    }
    open: pullRequests(states: OPEN) {
      totalCount
    }
    closed: pullRequests(states: CLOSED) {
      totalCount
    }
    merged: pullRequests(states: MERGED) {
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
class PullRequestReport:
    login: str
    opened: int
    open_count: int
    closed_count: int
    merged_count: int
    collected_at: str
    snapshot_path: str


def collect_pull_requests(login: str | None = None) -> PullRequestReport:
    """Count pull requests the user opened, split by open, closed, and merged."""
    resolved = login or graphql(_VIEWER_LOGIN_QUERY)["viewer"]["login"]
    user = graphql(_PULL_REQUESTS_QUERY, login=resolved)["user"]
    if user is None:
        raise RuntimeError(f"GitHub user {resolved} was not found.")

    collected_at = datetime.now(timezone.utc)
    report = PullRequestReport(
        login=user["login"],
        opened=user["pullRequests"]["totalCount"],
        open_count=user["open"]["totalCount"],
        closed_count=user["closed"]["totalCount"],
        merged_count=user["merged"]["totalCount"],
        collected_at=collected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        snapshot_path=str(DB_PATH),
    )
    save_pull_request_snapshot(
        login=report.login,
        opened=report.opened,
        open_count=report.open_count,
        closed_count=report.closed_count,
        merged_count=report.merged_count,
        collected_at=report.collected_at,
    )
    return report


def format_report(report: PullRequestReport) -> str:
    return "\n".join(
        [
            f"login: {report.login}",
            f"opened: {report.opened}",
            f"open: {report.open_count}",
            f"closed: {report.closed_count}",
            f"merged: {report.merged_count}",
            f"snapshot: {report.snapshot_path}",
        ]
    )
