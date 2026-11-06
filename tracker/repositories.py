"""Public repositories owned by a GitHub user."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from tracker.gh import graphql
from tracker.store import DB_PATH, save_public_repository_snapshot

_REPOSITORIES_QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    public: repositories(privacy: PUBLIC, ownerAffiliations: OWNER) {
      totalCount
    }
    sources: repositories(privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false) {
      totalCount
    }
    forks: repositories(privacy: PUBLIC, ownerAffiliations: OWNER, isFork: true) {
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
class PublicRepositoryReport:
    login: str
    public_count: int
    source_count: int
    fork_count: int
    collected_at: str
    snapshot_path: str


def collect_public_repositories(login: str | None = None) -> PublicRepositoryReport:
    """Count public repositories the user owns, split into sources and forks."""
    resolved = login or graphql(_VIEWER_LOGIN_QUERY)["viewer"]["login"]
    user = graphql(_REPOSITORIES_QUERY, login=resolved)["user"]
    if user is None:
        raise RuntimeError(f"GitHub user {resolved} was not found.")

    collected_at = datetime.now(timezone.utc)
    report = PublicRepositoryReport(
        login=user["login"],
        public_count=user["public"]["totalCount"],
        source_count=user["sources"]["totalCount"],
        fork_count=user["forks"]["totalCount"],
        collected_at=collected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        snapshot_path=str(DB_PATH),
    )
    save_public_repository_snapshot(
        login=report.login,
        public_count=report.public_count,
        source_count=report.source_count,
        fork_count=report.fork_count,
        collected_at=report.collected_at,
    )
    return report


def format_report(report: PublicRepositoryReport) -> str:
    return "\n".join(
        [
            f"login: {report.login}",
            f"public: {report.public_count}",
            f"sources: {report.source_count}",
            f"forks: {report.fork_count}",
            f"snapshot: {report.snapshot_path}",
        ]
    )
