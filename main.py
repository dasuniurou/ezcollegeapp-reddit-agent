"""
main.py — CLI entry-point.

Usage:
    # Run one monitor cycle (scan + reply)
    python main.py monitor

    # Create an on-demand post
    python main.py post --subreddit ApplyingToCollege --format story

    # Create a post with a custom angle
    python main.py post --subreddit college --format tips --context "essay feedback tips"
"""
from __future__ import annotations

import argparse
import logging
import sys

from dotenv import load_dotenv  # type: ignore

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_monitor(_args: argparse.Namespace) -> None:
    from agents.orchestrator import Orchestrator

    orch = Orchestrator()
    count = orch.run_monitor_cycle()
    print(f"\nDone. Replied to {count} post(s).")


def cmd_post(args: argparse.Namespace) -> None:
    from agents.orchestrator import Orchestrator

    orch = Orchestrator()
    title, body = orch.make_post(
        subreddit=args.subreddit,
        post_format=args.format,
        extra_context=args.context,
    )
    if title and body:
        print(f"\nPost generated:\nTITLE: {title}\n\n{body}")
    else:
        print("\nPost skipped (limit reached or dry-run with no title parsed).")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="EZCollegeApp Reddit Community Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("monitor", help="Run one monitor + reply cycle")

    post_parser = sub.add_parser("post", help="Create an on-demand personal experience post")
    post_parser.add_argument("--subreddit", default=None, help="Target subreddit (no r/)")
    post_parser.add_argument(
        "--format",
        choices=["story", "tips", "question"],
        default="story",
        help="Post format style",
    )
    post_parser.add_argument("--context", default="", help="Optional angle or talking point")

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "monitor":
        cmd_monitor(args)
    elif args.command == "post":
        cmd_post(args)
    else:
        parser.print_help()
        sys.exit(1)
