"""Local page for the latest stored GitHub snapshots."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from tracker.store import connect

_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
_LOGIN_TABLES = (
    "contribution_snapshots",
    "streak_snapshots",
    "longest_streak_snapshots",
    "language_snapshots",
    "commit_snapshots",
    "pull_request_snapshots",
    "issue_snapshots",
    "weekly_commit_snapshots",
    "yearly_contribution_snapshots",
    "public_repository_snapshots",
    "follower_snapshots",
    "following_snapshots",
    "organization_snapshots",
)


@dataclass(frozen=True)
class CountSpan:
    total: int
    period_from: str
    period_to: str
    collected_at: str


@dataclass(frozen=True)
class Streak:
    days: int
    streak_from: str | None
    streak_to: str | None
    collected_at: str


@dataclass(frozen=True)
class LanguageBar:
    name: str
    color: str | None
    size: int
    share: float


@dataclass(frozen=True)
class Languages:
    repository_count: int
    collected_at: str
    languages: tuple[LanguageBar, ...]


@dataclass(frozen=True)
class PullRequests:
    opened: int
    open_count: int
    closed_count: int
    merged_count: int
    collected_at: str


@dataclass(frozen=True)
class Issues:
    opened: int
    open_count: int
    closed_count: int
    collected_at: str


@dataclass(frozen=True)
class Week:
    week_start: str
    commits: int


@dataclass(frozen=True)
class Weekly:
    collected_at: str
    weeks: tuple[Week, ...]


@dataclass(frozen=True)
class YearPoint:
    year: int
    contributions: int


@dataclass(frozen=True)
class Yearly:
    collected_at: str
    years: tuple[YearPoint, ...]


@dataclass(frozen=True)
class Repositories:
    public_count: int
    source_count: int
    fork_count: int
    collected_at: str


@dataclass(frozen=True)
class NamedList:
    count: int
    collected_at: str
    names: tuple[str, ...]


@dataclass(frozen=True)
class Following:
    following: int
    user_count: int
    organization_count: int
    collected_at: str
    users: tuple[str, ...]
    organizations: tuple[str, ...]


@dataclass(frozen=True)
class FollowerChange:
    login: str
    change: str
    collected_at: str


@dataclass(frozen=True)
class Organization:
    login: str
    role: str
    state: str


@dataclass(frozen=True)
class Organizations:
    collected_at: str
    organizations: tuple[Organization, ...]


@dataclass(frozen=True)
class Dashboard:
    login: str
    contributions_last_year: CountSpan | None
    contributions_all_time: CountSpan | None
    commits_last_year: CountSpan | None
    commits_all_time: CountSpan | None
    current_streak: Streak | None
    longest_streak: Streak | None
    languages: Languages | None
    pull_requests: PullRequests | None
    issues: Issues | None
    weekly: Weekly | None
    yearly: Yearly | None
    repositories: Repositories | None
    followers: NamedList | None
    follower_changes: tuple[FollowerChange, ...]
    following: Following | None
    organizations: Organizations | None


def load_dashboard(login: str | None = None) -> Dashboard:
    """Read the newest stored snapshot of each collected stat."""
    connection = connect()
    try:
        resolved = login or _default_login(connection)
        return Dashboard(
            login=resolved,
            contributions_last_year=_count_span(
                connection, "contribution_snapshots", resolved, "last_year"
            ),
            contributions_all_time=_count_span(
                connection, "contribution_snapshots", resolved, "all_time"
            ),
            commits_last_year=_count_span(
                connection, "commit_snapshots", resolved, "last_year"
            ),
            commits_all_time=_count_span(
                connection, "commit_snapshots", resolved, "all_time"
            ),
            current_streak=_streak(connection, "streak_snapshots", "current_streak", resolved),
            longest_streak=_streak(
                connection, "longest_streak_snapshots", "longest_streak", resolved
            ),
            languages=_languages(connection, resolved),
            pull_requests=_pull_requests(connection, resolved),
            issues=_issues(connection, resolved),
            weekly=_weekly(connection, resolved),
            yearly=_yearly(connection, resolved),
            repositories=_repositories(connection, resolved),
            followers=_named_list(
                connection,
                "follower_snapshots",
                "followers",
                "follower_member_snapshots",
                "follower_login",
                resolved,
            ),
            follower_changes=_follower_changes(connection, resolved),
            following=_following(connection, resolved),
            organizations=_organizations(connection, resolved),
        )
    finally:
        connection.close()


def render_dashboard(dashboard: Dashboard) -> str:
    """Return a self-contained HTML page for one dashboard."""
    login = _esc(dashboard.login)
    sections = [
        _hero(dashboard),
        _stat_grid(dashboard),
        _charts(dashboard),
        _languages_section(dashboard.languages),
        _work_section(dashboard),
        _people_section(dashboard),
    ]
    body = "\n".join(section for section in sections if section)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{login} · GitHub activity</title>
<style>
  :root {{
    color-scheme: light dark;
    --bg: #f4f6f8;
    --surface: #ffffff;
    --text: #1c2128;
    --muted: #5c6773;
    --line: #d8dee6;
    --accent: #1f6feb;
    --open: #9a6700;
    --closed: #59636e;
    --merged: #1f6feb;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #0d1117;
      --surface: #161b22;
      --text: #e6edf3;
      --muted: #8b949e;
      --line: #30363d;
      --accent: #4493f8;
      --open: #d4a72c;
      --closed: #8b949e;
      --merged: #4493f8;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font: 400 15px/1.45 ui-sans-serif, system-ui, sans-serif;
  }}
  main {{ max-width: 1040px; margin: 0 auto; padding: 28px 20px 56px; }}
  h1 {{ margin: 0; font-size: 24px; font-weight: 500; }}
  h2 {{ margin: 0 0 10px; font-size: 16px; font-weight: 500; }}
  p {{ margin: 0; }}
  .lede {{ margin: 6px 0 20px; color: var(--muted); }}
  .hero {{ display: flex; flex-wrap: wrap; gap: 28px; align-items: flex-end; margin-bottom: 18px; }}
  .hero .value {{ font-size: 40px; font-weight: 500; letter-spacing: -0.03em; line-height: 1; }}
  .hero .aside {{ font-size: 22px; font-weight: 500; line-height: 1; }}
  .hero .label, .when, .stat span, figcaption {{ color: var(--muted); font-size: 12px; }}
  .stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 10px;
  }}
  .stat {{
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 10px 12px;
  }}
  .stat b {{ display: block; font-size: 20px; font-weight: 500; }}
  .stat .detail {{ display: block; white-space: nowrap; }}
  section {{ margin-top: 28px; }}
  .charts figure + figure {{ margin-top: 22px; }}
  .split {{ display: grid; grid-template-columns: 1.35fr 0.8fr; gap: 28px; }}
  figure {{ margin: 0; }}
  svg {{ width: 100%; height: auto; display: block; }}
  svg text {{ fill: var(--muted); font-size: 11px; font-family: ui-sans-serif, system-ui, sans-serif; }}
  svg rect {{ fill: var(--accent); }}
  svg line {{ stroke: var(--line); }}
  .lang {{
    display: grid;
    grid-template-columns: minmax(108px, 150px) 1fr auto;
    gap: 8px;
    align-items: center;
    margin: 5px 0;
  }}
  .track {{ height: 8px; border-radius: 4px; background: var(--line); }}
  .fill {{ height: 8px; border-radius: 4px; }}
  .also {{ margin-top: 8px; color: var(--muted); }}
  .stack {{ display: flex; height: 10px; border-radius: 5px; overflow: hidden; background: var(--line); }}
  .stack i {{ display: block; height: 10px; }}
  .legend {{ display: flex; flex-wrap: wrap; gap: 12px 16px; margin: 8px 0 0; padding: 0; list-style: none; }}
  .legend li {{ display: flex; align-items: center; gap: 6px; }}
  .swatch {{ width: 8px; height: 8px; border-radius: 2px; background: var(--swatch); }}
  .names {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }}
  .names span, .org {{
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: 2px 8px;
    font-size: 13px;
  }}
  .orgs {{ display: flex; flex-direction: column; align-items: flex-start; gap: 6px; margin-top: 8px; }}
  .columns {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 22px; }}
  @media (max-width: 800px) {{
    .split {{ grid-template-columns: 1fr; }}
    .hero .value {{ font-size: 32px; }}
    svg text {{ font-size: 20px; }}
  }}
</style>
</head>
<body>
<main>
  <h1>{login}</h1>
  <p class="lede">GitHub activity from the latest local snapshots.</p>
  {body}
</main>
</body>
</html>
"""


def serve_dashboard(login: str | None = None, host: str = "127.0.0.1", port: int = 8765) -> None:
    """Serve the dashboard until interrupted."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = self.path.split("?", 1)[0]
            if path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            if path != "/":
                self.send_error(404)
                return
            try:
                payload = render_dashboard(load_dashboard(login)).encode()
            except RuntimeError as error:
                message = str(error).encode()
                self.send_response(500)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(message)))
                self.end_headers()
                self.wfile.write(message)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: object) -> None:
            return

    try:
        class Server(ThreadingHTTPServer):
            allow_reuse_address = True

        server = Server((host, port), Handler)
    except OSError as error:
        raise RuntimeError(f"Could not listen on {host}:{port}. {error.strerror}") from error
    print(f"http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def _default_login(connection) -> str:
    newest: tuple[str, str] | None = None
    for table in _LOGIN_TABLES:
        row = connection.execute(
            f"SELECT login, collected_at FROM {table} ORDER BY collected_at DESC LIMIT 1"
        ).fetchone()
        if row is None:
            continue
        if newest is None or row["collected_at"] > newest[0]:
            newest = (row["collected_at"], row["login"])
    if newest is None:
        raise RuntimeError("No snapshots are stored yet.")
    return newest[1]


def _count_span(connection, table: str, login: str, scope: str) -> CountSpan | None:
    row = connection.execute(
        f"""
        SELECT total, period_from, period_to, collected_at
        FROM {table}
        WHERE login = ? AND scope = ?
        ORDER BY collected_at DESC
        LIMIT 1
        """,
        (login, scope),
    ).fetchone()
    if row is None:
        return None
    return CountSpan(
        total=row["total"],
        period_from=row["period_from"],
        period_to=row["period_to"],
        collected_at=row["collected_at"],
    )


def _streak(connection, table: str, column: str, login: str) -> Streak | None:
    row = connection.execute(
        f"""
        SELECT {column} AS days, streak_from, streak_to, collected_at
        FROM {table}
        WHERE login = ?
        ORDER BY collected_at DESC
        LIMIT 1
        """,
        (login,),
    ).fetchone()
    if row is None:
        return None
    return Streak(
        days=row["days"],
        streak_from=row["streak_from"],
        streak_to=row["streak_to"],
        collected_at=row["collected_at"],
    )


def _languages(connection, login: str) -> Languages | None:
    collected_at = _latest_at(connection, "language_snapshots", login)
    if collected_at is None:
        return None
    rows = connection.execute(
        """
        SELECT language, color, bytes, share, repository_count
        FROM language_snapshots
        WHERE login = ? AND collected_at = ?
        ORDER BY rank
        """,
        (login, collected_at),
    ).fetchall()
    return Languages(
        repository_count=rows[0]["repository_count"] if rows else 0,
        collected_at=collected_at,
        languages=tuple(
            LanguageBar(
                name=row["language"],
                color=row["color"],
                size=row["bytes"],
                share=row["share"],
            )
            for row in rows
        ),
    )


def _pull_requests(connection, login: str) -> PullRequests | None:
    row = connection.execute(
        """
        SELECT opened, open_count, closed_count, merged_count, collected_at
        FROM pull_request_snapshots
        WHERE login = ?
        ORDER BY collected_at DESC
        LIMIT 1
        """,
        (login,),
    ).fetchone()
    if row is None:
        return None
    return PullRequests(**dict(row))


def _issues(connection, login: str) -> Issues | None:
    row = connection.execute(
        """
        SELECT opened, open_count, closed_count, collected_at
        FROM issue_snapshots
        WHERE login = ?
        ORDER BY collected_at DESC
        LIMIT 1
        """,
        (login,),
    ).fetchone()
    if row is None:
        return None
    return Issues(**dict(row))


def _weekly(connection, login: str) -> Weekly | None:
    collected_at = _latest_at(connection, "weekly_commit_snapshots", login)
    if collected_at is None:
        return None
    rows = connection.execute(
        """
        SELECT week_start, commits
        FROM weekly_commit_snapshots
        WHERE login = ? AND collected_at = ?
        ORDER BY week_start
        """,
        (login, collected_at),
    ).fetchall()
    return Weekly(
        collected_at=collected_at,
        weeks=tuple(Week(week_start=row["week_start"], commits=row["commits"]) for row in rows),
    )


def _yearly(connection, login: str) -> Yearly | None:
    collected_at = _latest_at(connection, "yearly_contribution_snapshots", login)
    if collected_at is None:
        return None
    rows = connection.execute(
        """
        SELECT year, contributions
        FROM yearly_contribution_snapshots
        WHERE login = ? AND collected_at = ?
        ORDER BY year
        """,
        (login, collected_at),
    ).fetchall()
    return Yearly(
        collected_at=collected_at,
        years=tuple(
            YearPoint(year=row["year"], contributions=row["contributions"]) for row in rows
        ),
    )


def _repositories(connection, login: str) -> Repositories | None:
    row = connection.execute(
        """
        SELECT public_count, source_count, fork_count, collected_at
        FROM public_repository_snapshots
        WHERE login = ?
        ORDER BY collected_at DESC
        LIMIT 1
        """,
        (login,),
    ).fetchone()
    if row is None:
        return None
    return Repositories(**dict(row))


def _named_list(
    connection,
    snapshot_table: str,
    count_column: str,
    member_table: str,
    member_column: str,
    login: str,
) -> NamedList | None:
    row = connection.execute(
        f"""
        SELECT {count_column} AS count, collected_at
        FROM {snapshot_table}
        WHERE login = ?
        ORDER BY collected_at DESC
        LIMIT 1
        """,
        (login,),
    ).fetchone()
    if row is None:
        return None
    names = connection.execute(
        f"""
        SELECT {member_column} AS name
        FROM {member_table}
        WHERE login = ? AND collected_at = ?
        ORDER BY {member_column} COLLATE NOCASE
        """,
        (login, row["collected_at"]),
    ).fetchall()
    return NamedList(
        count=row["count"],
        collected_at=row["collected_at"],
        names=tuple(name["name"] for name in names),
    )


def _following(connection, login: str) -> Following | None:
    row = connection.execute(
        """
        SELECT following, user_count, organization_count, collected_at
        FROM following_snapshots
        WHERE login = ?
        ORDER BY collected_at DESC
        LIMIT 1
        """,
        (login,),
    ).fetchone()
    if row is None:
        return None
    members = connection.execute(
        """
        SELECT followed_login, account_type
        FROM following_member_snapshots
        WHERE login = ? AND collected_at = ?
        ORDER BY followed_login COLLATE NOCASE
        """,
        (login, row["collected_at"]),
    ).fetchall()
    return Following(
        following=row["following"],
        user_count=row["user_count"],
        organization_count=row["organization_count"],
        collected_at=row["collected_at"],
        users=tuple(
            member["followed_login"] for member in members if member["account_type"] == "User"
        ),
        organizations=tuple(
            member["followed_login"]
            for member in members
            if member["account_type"] == "Organization"
        ),
    )


def _follower_changes(connection, login: str) -> tuple[FollowerChange, ...]:
    rows = connection.execute(
        """
        SELECT follower_login, change, collected_at
        FROM follower_change_snapshots
        WHERE login = ?
        ORDER BY collected_at DESC, follower_login COLLATE NOCASE
        """,
        (login,),
    ).fetchall()
    return tuple(
        FollowerChange(
            login=row["follower_login"],
            change=row["change"],
            collected_at=row["collected_at"],
        )
        for row in rows
    )


def _organizations(connection, login: str) -> Organizations | None:
    collected_at = _latest_at(connection, "organization_member_snapshots", login)
    if collected_at is None:
        count = _latest_at(connection, "organization_snapshots", login)
        if count is None:
            return None
        return Organizations(collected_at=count, organizations=())
    rows = connection.execute(
        """
        SELECT organization_login, role, state
        FROM organization_member_snapshots
        WHERE login = ? AND collected_at = ?
        ORDER BY organization_login COLLATE NOCASE
        """,
        (login, collected_at),
    ).fetchall()
    return Organizations(
        collected_at=collected_at,
        organizations=tuple(
            Organization(login=row["organization_login"], role=row["role"], state=row["state"])
            for row in rows
        ),
    )


def _latest_at(connection, table: str, login: str) -> str | None:
    row = connection.execute(
        f"SELECT MAX(collected_at) AS collected_at FROM {table} WHERE login = ?",
        (login,),
    ).fetchone()
    if row is None:
        return None
    return row["collected_at"]


def _hero(dashboard: Dashboard) -> str:
    total = dashboard.contributions_all_time
    if total is None:
        return ""
    last_year = dashboard.contributions_last_year
    extra = ""
    if last_year is not None:
        extra = (
            f'<p><span class="aside">{_num(last_year.total)}</span>'
            f'<span class="label"> last year, {_esc(last_year.period_from)}'
            f" to {_esc(last_year.period_to)}</span></p>"
        )
    return f"""
    <div class="hero">
      <p><span class="value">{_num(total.total)}</span>
      <span class="label"> contributions, {_esc(total.period_from)} to {_esc(total.period_to)}</span></p>
      {extra}
    </div>
    <p class="when">Contributions collected {_esc(_when(total.collected_at))}</p>
    """


def _stat_grid(dashboard: Dashboard) -> str:
    cards: list[str] = []
    if dashboard.current_streak is not None:
        cards.append(_card("Current streak", f"{_num(dashboard.current_streak.days)} days", _span(dashboard.current_streak)))
    if dashboard.longest_streak is not None:
        cards.append(_card("Longest streak", f"{_num(dashboard.longest_streak.days)} days", _span(dashboard.longest_streak)))
    if dashboard.commits_all_time is not None:
        cards.append(_card("Commits", _num(dashboard.commits_all_time.total), "all time"))
    if dashboard.commits_last_year is not None:
        cards.append(_card("Commits, last year", _num(dashboard.commits_last_year.total), dashboard.commits_last_year.period_from[:4] + "–" + dashboard.commits_last_year.period_to[:4]))
    if dashboard.repositories is not None:
        repos = dashboard.repositories
        cards.append(_card("Public repositories", _num(repos.public_count), f"{_num(repos.source_count)} sources, {_num(repos.fork_count)} forks"))
    if dashboard.pull_requests is not None:
        cards.append(_card("Pull requests", _num(dashboard.pull_requests.opened), "opened"))
    if dashboard.issues is not None:
        cards.append(_card("Issues", _num(dashboard.issues.opened), "opened"))
    if dashboard.followers is not None:
        cards.append(_card("Followers", _num(dashboard.followers.count), ""))
    if dashboard.following is not None:
        cards.append(_card("Following", _num(dashboard.following.following), f"{_num(dashboard.following.user_count)} users, {_num(dashboard.following.organization_count)} organizations"))
    if dashboard.organizations is not None:
        cards.append(_card("Organizations", _num(len(dashboard.organizations.organizations)), "memberships"))
    if not cards:
        return ""
    return f'<div class="stats">{"".join(cards)}</div>'


def _charts(dashboard: Dashboard) -> str:
    yearly = _yearly_figure(dashboard.yearly)
    weekly = _weekly_figure(dashboard.weekly)
    if not yearly and not weekly:
        return ""
    return f'<section class="charts">{yearly}{weekly}</section>'


def _yearly_figure(yearly: Yearly | None) -> str:
    if yearly is None or not yearly.years:
        return ""
    series = [(str(year.year), year.contributions) for year in yearly.years]
    total = sum(year.contributions for year in yearly.years)
    return f"""
    <figure>
      <h2>Contributions per year</h2>
      {_bars(series, aria=f"Contributions per year, {_num(total)} total", value_labels=True)}
      <figcaption>{_num(total)} contributions across {len(yearly.years)} years. Collected {_esc(_when(yearly.collected_at))}.</figcaption>
    </figure>
    """


def _weekly_figure(weekly: Weekly | None) -> str:
    if weekly is None or not weekly.weeks:
        return ""
    series = [(week.week_start, week.commits) for week in weekly.weeks]
    total = sum(week.commits for week in weekly.weeks)
    peak = max(weekly.weeks, key=lambda week: week.commits)
    latest = weekly.weeks[-1]
    return f"""
    <figure>
      <h2>Commits per week</h2>
      {_bars(series, aria=f"Contribution commits per week, {_num(total)} total", label_ends=True)}
      <figcaption>Sunday-start weeks. Peak {_esc(peak.week_start)}, {_num(peak.commits)} commits. Latest {_esc(latest.week_start)}, {_num(latest.commits)}. Total {_num(total)}. Collected {_esc(_when(weekly.collected_at))}.</figcaption>
    </figure>
    """


def _languages_section(languages: Languages | None) -> str:
    if languages is None or not languages.languages:
        return ""
    top = languages.languages[:10]
    rest = languages.languages[10:]
    peak = max(language.share for language in top) or 1
    rows = []
    for language in top:
        width = max(language.share / peak * 100, 0)
        rows.append(
            "<div class=\"lang\">"
            f"<span>{_esc(language.name)}</span>"
            f'<div class="track"><div class="fill" style="width:{width:.1f}%;background:{_swatch(language.color)}"></div></div>'
            f"<span>{language.share:.1f}%</span>"
            "</div>"
        )
    also = ""
    if rest:
        names = ", ".join(
            f"{_esc(language.name)} {language.share:.1f}%" for language in rest
        )
        also = f'<p class="also">Also stored: {names}</p>'
    return f"""
    <section>
      <h2>Top languages</h2>
      <p class="when">Share of bytes in {_num(languages.repository_count)} owned non-fork repositories. Collected {_esc(_when(languages.collected_at))}.</p>
      {''.join(rows)}
      {also}
    </section>
    """


def _work_section(dashboard: Dashboard) -> str:
    blocks = []
    if dashboard.pull_requests is not None:
        pull_requests = dashboard.pull_requests
        blocks.append(
            "<div>"
            "<h2>Pull requests</h2>"
            + _parts(
                [
                    ("Open", pull_requests.open_count, "var(--open)"),
                    ("Closed", pull_requests.closed_count, "var(--closed)"),
                    ("Merged", pull_requests.merged_count, "var(--merged)"),
                ],
                aria=f"Pull requests: {pull_requests.open_count} open, {pull_requests.closed_count} closed, {pull_requests.merged_count} merged",
            )
            + f'<p class="when">{_num(pull_requests.opened)} opened. Collected {_esc(_when(pull_requests.collected_at))}.</p>'
            + "</div>"
        )
    if dashboard.issues is not None:
        issues = dashboard.issues
        blocks.append(
            "<div>"
            "<h2>Issues opened</h2>"
            + _parts(
                [
                    ("Open", issues.open_count, "var(--open)"),
                    ("Closed", issues.closed_count, "var(--closed)"),
                ],
                aria=f"Issues: {issues.open_count} open, {issues.closed_count} closed",
            )
            + f'<p class="when">{_num(issues.opened)} opened. Collected {_esc(_when(issues.collected_at))}.</p>'
            + "</div>"
        )
    if not blocks:
        return ""
    return f'<section class="split">{"".join(blocks)}</section>'


def _people_section(dashboard: Dashboard) -> str:
    columns = []
    if dashboard.followers is not None:
        columns.append(
            "<div><h2>Followers</h2>"
            f"<p>{_num(dashboard.followers.count)}</p>"
            f"{_names(dashboard.followers.names)}"
            f'<p class="when">Collected {_esc(_when(dashboard.followers.collected_at))}.</p>'
            f"{_change_note(dashboard.follower_changes)}"
            "</div>"
        )
    if dashboard.following is not None:
        following = dashboard.following
        columns.append(
            "<div><h2>Following</h2>"
            f"<p>{_num(following.following)} · {_num(following.user_count)} users, {_num(following.organization_count)} organizations</p>"
            "<p class=\"when\">Users</p>"
            f"{_names(following.users)}"
            "<p class=\"when\">Organizations</p>"
            f"{_names(following.organizations)}"
            f'<p class="when">Collected {_esc(_when(following.collected_at))}.</p>'
            "</div>"
        )
    if dashboard.organizations is not None:
        orgs = []
        for organization in dashboard.organizations.organizations:
            detail = ", ".join(
                part for part in (organization.role, organization.state) if part
            )
            label = _esc(organization.login)
            if detail:
                label = f"{label}: {_esc(detail)}"
            orgs.append(f'<span class="org">{label}</span>')
        body = f'<div class="orgs">{"".join(orgs)}</div>' if orgs else "<p>none</p>"
        columns.append(
            "<div><h2>Organizations</h2>"
            f"<p>{_num(len(dashboard.organizations.organizations))} memberships</p>"
            f"{body}"
            f'<p class="when">Collected {_esc(_when(dashboard.organizations.collected_at))}.</p>'
            "</div>"
        )
    if not columns:
        return ""
    return f'<section class="columns">{"".join(columns)}</section>'


def _change_note(changes: tuple[FollowerChange, ...]) -> str:
    if not changes:
        return '<p class="when">No follow or unfollow has been recorded.</p>'
    items = "".join(
        f"<li>{_esc(change.login)} {_esc(change.change)}, {_esc(_when(change.collected_at))}</li>"
        for change in changes
    )
    return f"<ul>{items}</ul>"


def _card(label: str, value: str, detail: str) -> str:
    detail_html = f'<span class="detail">{_esc(detail)}</span>' if detail else ""
    return (
        '<div class="stat">'
        f"<span>{_esc(label)}</span><b>{_esc(value)}</b>{detail_html}"
        "</div>"
    )


def _parts(parts: list[tuple[str, int, str]], *, aria: str) -> str:
    total = sum(count for _, count, _ in parts) or 1
    segments = []
    legend = []
    for label, count, color in parts:
        width = count / total * 100
        segments.append(f'<i style="width:{width:.2f}%;background:{color}"></i>')
        legend.append(
            f'<li><i class="swatch" style="--swatch:{color}"></i>{_esc(label)} {_num(count)}</li>'
        )
    return (
        f'<div class="stack" role="img" aria-label="{_esc(aria)}">{"".join(segments)}</div>'
        f'<ul class="legend">{"".join(legend)}</ul>'
    )


def _bars(
    series: list[tuple[str, int]],
    *,
    aria: str,
    label_every: int | None = None,
    label_ends: bool = False,
    value_labels: bool = False,
) -> str:
    if not series:
        return ""
    width = 640
    height = 210
    pad_left = 36
    pad_right = 8
    pad_top = 18
    pad_bottom = 32
    inner_width = width - pad_left - pad_right
    inner_height = height - pad_top - pad_bottom
    peak = max(value for _, value in series) or 1
    count = len(series)
    gap = 3 if count <= 12 else 1
    bar_width = max((inner_width - gap * (count - 1)) / count, 1)
    shapes: list[str] = []
    labels: list[str] = []
    for index, (label, value) in enumerate(series):
        bar_height = 0 if value == 0 else max(value / peak * inner_height, 1)
        x = pad_left + index * (bar_width + gap)
        y = pad_top + inner_height - bar_height
        shapes.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}">'
            f"<title>{_esc(label)}: {_num(value)}</title></rect>"
        )
        if label_ends:
            show_label = index in {0, count // 2, count - 1}
        else:
            show_label = label_every is None or index % label_every == 0 or index == count - 1
        if show_label:
            if label_ends and index == 0:
                anchor = "start"
                label_x = x
            elif label_ends and index == count - 1:
                anchor = "end"
                label_x = min(x + bar_width, width - pad_right)
            else:
                anchor = "middle"
                label_x = x + bar_width / 2
            labels.append(
                f'<text x="{label_x:.1f}" y="{height - 10}" text-anchor="{anchor}">{_esc(label)}</text>'
            )
        if value_labels:
            labels.append(
                f'<text x="{x + bar_width / 2:.1f}" y="{max(y - 4, 12):.1f}" text-anchor="middle">{_num(value)}</text>'
            )
    axis = (
        f'<line x1="{pad_left}" y1="{pad_top + inner_height}" x2="{width - pad_right}" y2="{pad_top + inner_height}"/>'
        f'<text x="4" y="{pad_top + 8}">{_num(peak)}</text>'
        f'<text x="4" y="{pad_top + inner_height}">{0}</text>'
    )
    return (
        f'<svg role="img" aria-label="{_esc(aria)}" viewBox="0 0 {width} {height}">'
        f"{axis}{''.join(shapes)}{''.join(labels)}</svg>"
    )


def _names(names: tuple[str, ...]) -> str:
    if not names:
        return "<p>none</p>"
    chips = "".join(f"<span>{_esc(name)}</span>" for name in names)
    return f'<div class="names">{chips}</div>'


def _span(streak: Streak) -> str:
    if streak.streak_from and streak.streak_to:
        return f"{streak.streak_from} to {streak.streak_to}"
    return ""


def _swatch(color: str | None) -> str:
    if color and _COLOR.match(color):
        return color
    return "var(--accent)"


def _when(value: str) -> str:
    if "T" in value and value.endswith("Z"):
        return value.replace("T", " ")[:16] + " UTC"
    return value


def _num(value: int) -> str:
    return f"{value:,}"


def _esc(value: str) -> str:
    return html.escape(value, quote=True)
