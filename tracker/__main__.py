"""Command line entry: python -m tracker contributions."""

from __future__ import annotations

import argparse
import sys

from tracker.contributions import collect_contributions, format_report
from tracker.gh import GhError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tracker")
    subcommands = parser.add_subparsers(dest="command", required=True)

    contributions = subcommands.add_parser(
        "contributions",
        help="Total contributions on the GitHub calendar",
    )
    contributions.add_argument(
        "--login",
        help="GitHub login. Defaults to the account signed in to gh.",
    )

    args = parser.parse_args(argv)
    try:
        if args.command == "contributions":
            report = collect_contributions(args.login)
            print(format_report(report))
    except (GhError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
