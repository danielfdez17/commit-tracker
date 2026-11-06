"""Call the GitHub API through the GitHub CLI."""

from __future__ import annotations

import json
import shutil
import subprocess


class GhError(RuntimeError):
    """gh was missing, unauthenticated, or the API rejected the query."""


def graphql(query: str, **variables: str) -> dict:
    """Run a GraphQL query with `gh api graphql` and return the data object."""
    if shutil.which("gh") is None:
        raise GhError("GitHub CLI (gh) is not installed.")

    command = ["gh", "api", "graphql", "-f", f"query={query}"]
    for name, value in variables.items():
        command.extend(["-f", f"{name}={value}"])

    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    payload = None
    if stdout:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            payload = None

    if result.returncode != 0 or (isinstance(payload, dict) and payload.get("errors")):
        message = _error_message(payload, stderr, stdout)
        raise GhError(message)

    if not isinstance(payload, dict) or "data" not in payload:
        raise GhError(stderr or stdout or "gh returned an empty response.")

    return payload["data"]


def _error_message(payload: dict | None, stderr: str, stdout: str) -> str:
    if isinstance(payload, dict) and payload.get("errors"):
        messages = [error.get("message", "") for error in payload["errors"]]
        joined = "; ".join(message for message in messages if message)
        if joined:
            return joined
    if "auth" in stderr.lower() or "login" in stderr.lower():
        return stderr or "gh is not logged in. Run `gh auth login`."
    return stderr or stdout or "gh api graphql failed."
