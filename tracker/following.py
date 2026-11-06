"""Accounts a GitHub user follows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from tracker.gh import get, graphql
from tracker.store import DB_PATH, save_following_snapshot

_VIEWER_LOGIN_QUERY = """
query {
  viewer {
    login
  }
}
"""


@dataclass(frozen=True)
class FollowingReport:
    login: str
    following: int
    users: tuple[str, ...]
    organizations: tuple[str, ...]
    collected_at: str
    snapshot_path: str


def collect_following(login: str | None = None) -> FollowingReport:
    """List every account the user follows and store the snapshot."""
    resolved = login or graphql(_VIEWER_LOGIN_QUERY)["viewer"]["login"]
    canonical, users, organizations = _followed_accounts(resolved)
    collected_at = datetime.now(timezone.utc)
    report = FollowingReport(
        login=canonical,
        following=len(users) + len(organizations),
        users=users,
        organizations=organizations,
        collected_at=collected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        snapshot_path=str(DB_PATH),
    )
    save_following_snapshot(
        login=report.login,
        following=report.following,
        user_count=len(report.users),
        organization_count=len(report.organizations),
        users=report.users,
        organizations=report.organizations,
        collected_at=report.collected_at,
    )
    return report


def split_followed(accounts: list[dict]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Split a following payload into user logins and organization logins."""
    users: list[str] = []
    organizations: list[str] = []
    for account in accounts:
        if not isinstance(account, dict) or not account.get("login"):
            continue
        target = organizations if account.get("type") == "Organization" else users
        if account["login"] not in target:
            target.append(account["login"])
    return (
        tuple(sorted(users, key=str.lower)),
        tuple(sorted(organizations, key=str.lower)),
    )


def format_report(report: FollowingReport) -> str:
    lines = [
        f"login: {report.login}",
        f"following: {report.following}",
        f"users: {len(report.users)}",
        f"organizations: {len(report.organizations)}",
        "users:",
    ]
    lines.extend(report.users or ("none",))
    lines.append("organizations:")
    lines.extend(report.organizations or ("none",))
    lines.append(f"snapshot: {report.snapshot_path}")
    return "\n".join(lines)


def _followed_accounts(login: str) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    profile = get(f"users/{login}")
    if not isinstance(profile, dict) or not profile.get("login"):
        raise RuntimeError(f"GitHub user {login} was not found.")
    accounts = get(f"users/{profile['login']}/following?per_page=100")
    if not isinstance(accounts, list):
        raise RuntimeError(f"GitHub returned no following list for {login}.")
    users, organizations = split_followed(accounts)
    return profile["login"], users, organizations
