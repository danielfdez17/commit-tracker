"""Organizations a GitHub user belongs to."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from tracker.gh import get, graphql
from tracker.store import DB_PATH, save_organization_snapshot

_VIEWER_LOGIN_QUERY = """
query {
  viewer {
    login
  }
}
"""


@dataclass(frozen=True)
class OrganizationMembership:
    login: str
    role: str
    state: str


@dataclass(frozen=True)
class OrganizationReport:
    login: str
    organizations: tuple[OrganizationMembership, ...]
    collected_at: str
    snapshot_path: str


def collect_organizations(login: str | None = None) -> OrganizationReport:
    """List the organizations the user belongs to and store the snapshot."""
    viewer = graphql(_VIEWER_LOGIN_QUERY)["viewer"]["login"]
    if login is None or login.lower() == viewer.lower():
        canonical, organizations = _viewer_memberships(viewer)
    else:
        canonical, organizations = _public_memberships(login)
    collected_at = datetime.now(timezone.utc)
    report = OrganizationReport(
        login=canonical,
        organizations=organizations,
        collected_at=collected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        snapshot_path=str(DB_PATH),
    )
    save_organization_snapshot(
        login=report.login,
        organizations=report.organizations,
        collected_at=report.collected_at,
    )
    return report


def memberships_from_payload(payload: list[dict]) -> tuple[OrganizationMembership, ...]:
    """Read role and state from the authenticated membership list."""
    memberships: list[OrganizationMembership] = []
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        organization = item.get("organization") or {}
        organization_login = organization.get("login")
        if not organization_login or organization_login in seen:
            continue
        seen.add(organization_login)
        memberships.append(
            OrganizationMembership(
                login=organization_login,
                role=item.get("role") or "",
                state=item.get("state") or "",
            )
        )
    return tuple(sorted(memberships, key=lambda membership: membership.login.lower()))


def format_report(report: OrganizationReport) -> str:
    lines = [
        f"login: {report.login}",
        f"organizations: {len(report.organizations)}",
    ]
    if report.organizations:
        lines.extend(_membership_line(membership) for membership in report.organizations)
    else:
        lines.append("none")
    lines.append(f"snapshot: {report.snapshot_path}")
    return "\n".join(lines)


def _membership_line(membership: OrganizationMembership) -> str:
    details = ", ".join(part for part in (membership.role, membership.state) if part)
    if details:
        return f"{membership.login}: {details}"
    return membership.login


def _viewer_memberships(viewer: str) -> tuple[str, tuple[OrganizationMembership, ...]]:
    payload = get("user/memberships/orgs?per_page=100")
    if not isinstance(payload, list):
        raise RuntimeError("GitHub returned no organization memberships.")
    canonical = viewer
    for item in payload:
        if isinstance(item, dict):
            user = item.get("user") or {}
            if user.get("login"):
                canonical = user["login"]
                break
    return canonical, memberships_from_payload(payload)


def _public_memberships(login: str) -> tuple[str, tuple[OrganizationMembership, ...]]:
    profile = get(f"users/{login}")
    if not isinstance(profile, dict) or not profile.get("login"):
        raise RuntimeError(f"GitHub user {login} was not found.")
    payload = get(f"users/{profile['login']}/orgs?per_page=100")
    if not isinstance(payload, list):
        raise RuntimeError(f"GitHub returned no organizations for {login}.")
    memberships: list[OrganizationMembership] = []
    seen: set[str] = set()
    for organization in payload:
        if not isinstance(organization, dict) or not organization.get("login"):
            continue
        if organization["login"] in seen:
            continue
        seen.add(organization["login"])
        memberships.append(
            OrganizationMembership(login=organization["login"], role="", state="")
        )
    ordered = tuple(sorted(memberships, key=lambda membership: membership.login.lower()))
    return profile["login"], ordered
