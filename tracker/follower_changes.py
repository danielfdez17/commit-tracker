"""Changes in who follows a GitHub user between two snapshots."""

from __future__ import annotations

from dataclasses import dataclass

from tracker.followers import collect_followers
from tracker.store import DB_PATH, latest_follower_logins, save_follower_changes


@dataclass(frozen=True)
class FollowerChangeReport:
    login: str
    followers: int
    followed: tuple[str, ...]
    unfollowed: tuple[str, ...]
    baseline: bool
    collected_at: str
    snapshot_path: str


def collect_follower_changes(login: str | None = None) -> FollowerChangeReport:
    """Refresh the follower list and compare it with the previous snapshot."""
    current = collect_followers(login)
    previous = latest_follower_logins(current.login, before=current.collected_at)
    followed, unfollowed = follower_changes(
        None if previous is None else set(previous),
        set(current.follower_logins),
    )
    if previous is not None:
        save_follower_changes(
            login=current.login,
            followed=followed,
            unfollowed=unfollowed,
            collected_at=current.collected_at,
        )
    return FollowerChangeReport(
        login=current.login,
        followers=current.followers,
        followed=followed,
        unfollowed=unfollowed,
        baseline=previous is None,
        collected_at=current.collected_at,
        snapshot_path=str(DB_PATH),
    )


def follower_changes(
    previous: set[str] | None,
    current: set[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return logins that joined and logins that left. None means there is no baseline."""
    if previous is None:
        return (), ()
    followed = tuple(sorted(current - previous, key=str.lower))
    unfollowed = tuple(sorted(previous - current, key=str.lower))
    return followed, unfollowed


def format_report(report: FollowerChangeReport) -> str:
    lines = [
        f"login: {report.login}",
        f"followers: {report.followers}",
    ]
    if report.baseline:
        lines.append("baseline: no earlier follower list")
    else:
        lines.append(_change_line("followed", report.followed))
        lines.append(_change_line("unfollowed", report.unfollowed))
    lines.append(f"snapshot: {report.snapshot_path}")
    return "\n".join(lines)


def _change_line(label: str, logins: tuple[str, ...]) -> str:
    if not logins:
        return f"{label}: none"
    return f"{label}: {', '.join(logins)}"
