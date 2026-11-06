"""Command line entry: python -m tracker."""

from __future__ import annotations

import argparse
import sys

from tracker.contributions import collect_contributions, format_report as format_contributions
from tracker.gh import GhError
from tracker.streak import collect_current_streak, format_report as format_streak


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tracker")
    subcommands = parser.add_subparsers(dest="command", required=True)
    login = argparse.ArgumentParser(add_help=False)
    login.add_argument(
        "--login",
        help="GitHub login. Defaults to the account signed in to gh.",
    )

    subcommands.add_parser(
        "contributions",
        parents=[login],
        help="Total contributions on the GitHub calendar",
    )
    subcommands.add_parser(
        "streak",
        parents=[login],
        help="Current contribution streak",
    )

    args = parser.parse_args(argv)
    try:
        if args.command == "contributions":
            print(format_contributions(collect_contributions(args.login)))
        elif args.command == "streak":
            print(format_streak(collect_current_streak(args.login)))
    except (GhError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
