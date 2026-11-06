"""Command line entry: python -m tracker."""

from __future__ import annotations

import argparse
import sys

from tracker.commits import collect_commits, format_report as format_commits
from tracker.contributions import collect_contributions, format_report as format_contributions
from tracker.followers import collect_followers, format_report as format_followers
from tracker.follower_changes import collect_follower_changes, format_report as format_follower_changes
from tracker.following import collect_following, format_report as format_following
from tracker.organizations import collect_organizations, format_report as format_organizations
from tracker.gh import GhError
from tracker.issues import collect_issues, format_report as format_issues
from tracker.languages import collect_top_languages, format_report as format_languages
from tracker.pull_requests import collect_pull_requests, format_report as format_pull_requests
from tracker.repositories import collect_public_repositories, format_report as format_repositories
from tracker.streak import collect_current_streak, collect_longest_streak
from tracker.streak import format_longest_report, format_report as format_streak
from tracker.weekly_commits import collect_weekly_commits, format_report as format_weekly_commits
from tracker.yearly_contributions import (
    collect_yearly_contributions,
    format_report as format_yearly_contributions,
)


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
    subcommands.add_parser(
        "longest-streak",
        parents=[login],
        help="Longest contribution streak",
    )
    subcommands.add_parser(
        "languages",
        parents=[login],
        help="Top languages by code size",
    )
    subcommands.add_parser(
        "commits",
        parents=[login],
        help="Total contribution commits",
    )
    subcommands.add_parser(
        "pull-requests",
        parents=[login],
        help="Pull requests opened by the user",
    )
    subcommands.add_parser(
        "issues",
        parents=[login],
        help="Issues opened by the user",
    )
    subcommands.add_parser(
        "weekly-commits",
        parents=[login],
        help="Contribution commits per week",
    )
    subcommands.add_parser(
        "yearly-contributions",
        parents=[login],
        help="Contributions per calendar year",
    )
    subcommands.add_parser(
        "public-repositories",
        parents=[login],
        help="Public repositories owned by the user",
    )
    subcommands.add_parser(
        "followers",
        parents=[login],
        help="Followers of the user",
    )
    subcommands.add_parser(
        "follower-changes",
        parents=[login],
        help="Who followed and unfollowed the user",
    )
    subcommands.add_parser(
        "following",
        parents=[login],
        help="Accounts the user follows",
    )
    subcommands.add_parser(
        "organizations",
        parents=[login],
        help="Organizations the user belongs to",
    )

    args = parser.parse_args(argv)
    try:
        if args.command == "contributions":
            print(format_contributions(collect_contributions(args.login)))
        elif args.command == "streak":
            print(format_streak(collect_current_streak(args.login)))
        elif args.command == "longest-streak":
            print(format_longest_report(collect_longest_streak(args.login)))
        elif args.command == "languages":
            print(format_languages(collect_top_languages(args.login)))
        elif args.command == "commits":
            print(format_commits(collect_commits(args.login)))
        elif args.command == "pull-requests":
            print(format_pull_requests(collect_pull_requests(args.login)))
        elif args.command == "issues":
            print(format_issues(collect_issues(args.login)))
        elif args.command == "weekly-commits":
            print(format_weekly_commits(collect_weekly_commits(args.login)))
        elif args.command == "yearly-contributions":
            print(format_yearly_contributions(collect_yearly_contributions(args.login)))
        elif args.command == "public-repositories":
            print(format_repositories(collect_public_repositories(args.login)))
        elif args.command == "followers":
            print(format_followers(collect_followers(args.login)))
        elif args.command == "follower-changes":
            print(format_follower_changes(collect_follower_changes(args.login)))
        elif args.command == "following":
            print(format_following(collect_following(args.login)))
        elif args.command == "organizations":
            print(format_organizations(collect_organizations(args.login)))
    except (GhError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
