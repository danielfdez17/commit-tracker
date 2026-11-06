"""Followers of a GitHub user."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from tracker.gh import graphql
from tracker.store import DB_PATH, save_follower_snapshot

_FOLLOWERS_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    login
    followers(first: 100, after: $after) {
      totalCount
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        login
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
class FollowerReport:
    login: str
    followers: int
    follower_logins: tuple[str, ...]
    collected_at: str
    snapshot_path: str


def collect_followers(login: str | None = None) -> FollowerReport:
    """Count followers and store each follower login."""
    resolved = login or graphql(_VIEWER_LOGIN_QUERY)["viewer"]["login"]
    canonical, total, follower_logins = _follower_logins(resolved)
    collected_at = datetime.now(timezone.utc)
    report = FollowerReport(
        login=canonical,
        followers=total,
        follower_logins=follower_logins,
        collected_at=collected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        snapshot_path=str(DB_PATH),
    )
    save_follower_snapshot(
        login=report.login,
        followers=report.followers,
        follower_logins=report.follower_logins,
        collected_at=report.collected_at,
    )
    return report


def format_report(report: FollowerReport) -> str:
    lines = [
        f"login: {report.login}",
        f"followers: {report.followers}",
    ]
    lines.extend(report.follower_logins)
    lines.append(f"snapshot: {report.snapshot_path}")
    return "\n".join(lines)


def _follower_logins(login: str) -> tuple[str, int, tuple[str, ...]]:
    seen: list[str] = []
    total = 0
    canonical = login
    cursor: str | None = None

    for _ in range(50):
        variables = {"login": login}
        if cursor is not None:
            variables["after"] = cursor
        user = graphql(_FOLLOWERS_QUERY, **variables)["user"]
        if user is None:
            raise RuntimeError(f"GitHub user {login} was not found.")
        canonical = user["login"]
        followers = user["followers"]
        total = followers["totalCount"]
        for node in followers["nodes"]:
            if node is not None and node["login"] not in seen:
                seen.append(node["login"])
        if not followers["pageInfo"]["hasNextPage"]:
            break
        cursor = followers["pageInfo"]["endCursor"]
    else:
        raise RuntimeError("follower scan stopped after 5000 followers.")

    return canonical, total, tuple(sorted(seen, key=str.lower))
