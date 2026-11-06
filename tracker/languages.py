"""Top languages across repositories the user owns."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from tracker.gh import graphql
from tracker.store import DB_PATH, save_language_snapshots

_TOP = 10
_MAX_PAGES = 20

_REPOSITORIES_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    login
    repositories(
      first: 100
      after: $after
      ownerAffiliations: OWNER
      isFork: false
    ) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
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
class LanguageShare:
    rank: int
    name: str
    color: str | None
    size: int
    share: float


@dataclass(frozen=True)
class LanguageReport:
    login: str
    repository_count: int
    languages: tuple[LanguageShare, ...]
    collected_at: str
    snapshot_path: str


def collect_top_languages(login: str | None = None) -> LanguageReport:
    """Rank languages by bytes of code in owned, non-fork repositories."""
    resolved = login or graphql(_VIEWER_LOGIN_QUERY)["viewer"]["login"]
    collected_at = datetime.now(timezone.utc)
    totals, repository_count, canonical = _language_totals(resolved)
    languages = rank_languages(totals)
    report = LanguageReport(
        login=canonical,
        repository_count=repository_count,
        languages=languages,
        collected_at=collected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        snapshot_path=str(DB_PATH),
    )
    save_language_snapshots(
        login=report.login,
        repository_count=report.repository_count,
        collected_at=report.collected_at,
        languages=report.languages,
    )
    return report


def rank_languages(totals: dict[str, tuple[int, str | None]]) -> tuple[LanguageShare, ...]:
    """Rank languages by size. Equal sizes are ordered by name."""
    total_bytes = sum(size for size, _color in totals.values())
    ordered = sorted(totals.items(), key=lambda item: (-item[1][0], item[0].lower()))
    shares: list[LanguageShare] = []
    for rank, (name, (size, color)) in enumerate(ordered, start=1):
        share = (size / total_bytes * 100) if total_bytes else 0.0
        shares.append(LanguageShare(rank=rank, name=name, color=color, size=size, share=share))
    return tuple(shares)


def format_report(report: LanguageReport) -> str:
    shown = report.languages[:_TOP]
    lines = [
        f"login: {report.login}",
        f"repositories: {report.repository_count}",
    ]
    if not shown:
        lines.append("top languages: none")
    else:
        width = max(len(language.name) for language in shown)
        for language in shown:
            lines.append(
                f"{language.rank}. {language.name:<{width}}  "
                f"{language.share:5.1f}%  {language.size} bytes"
            )
    lines.append(f"snapshot: {report.snapshot_path}")
    return "\n".join(lines)


def _language_totals(login: str) -> tuple[dict[str, tuple[int, str | None]], int, str]:
    totals: dict[str, tuple[int, str | None]] = {}
    repository_count = 0
    canonical = login
    cursor: str | None = None

    for _ in range(_MAX_PAGES):
        variables = {"login": login}
        if cursor is not None:
            variables["after"] = cursor
        data = graphql(_REPOSITORIES_QUERY, **variables)
        user = data["user"]
        if user is None:
            raise RuntimeError(f"GitHub user {login} was not found.")
        canonical = user["login"]
        repositories = user["repositories"]
        for node in repositories["nodes"]:
            if node is None:
                continue
            repository_count += 1
            for edge in node["languages"]["edges"]:
                name = edge["node"]["name"]
                color = edge["node"]["color"]
                size, previous_color = totals.get(name, (0, color))
                totals[name] = (size + edge["size"], previous_color or color)
        page = repositories["pageInfo"]
        if not page["hasNextPage"]:
            break
        cursor = page["endCursor"]
    else:
        raise RuntimeError("language scan stopped after 2000 repositories.")

    return totals, repository_count, canonical
