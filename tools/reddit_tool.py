"""
Reddit tool: public JSON API for reads, PRAW for writes.

Read path:    Uses Reddit's public .json endpoints — no credentials required.
Dry-run mode  (DRY_RUN=true):  All write operations are no-ops — output printed only.
Review mode   (REVIEW_MODE=true):  Replies/posts go to review_queue.json, not Reddit.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import requests

try:
    import praw  # type: ignore
    _PRAW_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PRAW_AVAILABLE = False

logger = logging.getLogger(__name__)

REVIEW_QUEUE_PATH = Path(__file__).parent.parent / "review_queue" / "review_queue.json"


class RedditPost:
    """Lightweight data class representing a Reddit post."""

    def __init__(self, post_id: str, title: str, body: str, subreddit: str, url: str):
        self.id = post_id
        self.title = title
        self.body = body
        self.subreddit = subreddit
        self.url = url

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "subreddit": self.subreddit,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RedditPost":
        return cls(
            post_id=data["id"],
            title=data["title"],
            body=data["body"],
            subreddit=data["subreddit"],
            url=data.get("url", ""),
        )


class RedditTool:
    """PRAW-based Reddit interface with dry-run and review-mode guards."""

    def __init__(
        self,
        dry_run: bool | None = None,
        review_mode: bool | None = None,
    ):
        """
        Args:
            dry_run:     If True, no writes to Reddit. Defaults to DRY_RUN env var.
            review_mode: If True, writes go to review_queue.json. Defaults to REVIEW_MODE env var.
        """
        self.dry_run = dry_run if dry_run is not None else _env_bool("DRY_RUN", default=True)
        self.review_mode = (
            review_mode if review_mode is not None else _env_bool("REVIEW_MODE", default=False)
        )

        # PRAW client is only needed for write operations (reply / post).
        # scan_subreddit uses the public JSON API and needs no credentials.
        self._reddit = None
        self._user_agent = os.getenv("REDDIT_USER_AGENT", "ezcommon_market_agent/1.0")

        mode = "DRY_RUN" if self.dry_run else ("REVIEW_MODE" if self.review_mode else "LIVE")
        logger.info("RedditTool initialized in %s mode", mode)

    # ------------------------------------------------------------------
    # Public: Read operations (always real)
    # ------------------------------------------------------------------

    def scan_subreddit(
        self, subreddit_name: str, post_limit: int = 25
    ) -> Generator[RedditPost, None, None]:
        """Yield the latest `post_limit` posts from a subreddit.

        Uses Reddit's public JSON API — no OAuth credentials required.
        """
        url = f"https://www.reddit.com/r/{subreddit_name}/new.json"
        params = {"limit": min(post_limit, 100)}
        headers = {"User-Agent": self._user_agent}

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Failed to fetch r/%s: %s", subreddit_name, exc)
            return

        children = resp.json().get("data", {}).get("children", [])
        for child in children:
            data = child.get("data", {})
            yield RedditPost(
                post_id=data["id"],
                title=data.get("title", ""),
                body=data.get("selftext", ""),
                subreddit=subreddit_name,
                url=f"https://www.reddit.com{data.get('permalink', '')}",
            )

    # ------------------------------------------------------------------
    # Public: Write operations (guarded by dry_run / review_mode)
    # ------------------------------------------------------------------

    def reply_to_post(self, post_id: str, reply_text: str, post: RedditPost | None = None) -> bool:
        """
        Reply to a post.

        Returns:
            True if submitted (or queued/printed), False on error.
        """
        if self.dry_run:
            print("\n" + "=" * 60)
            print(f"[DRY-RUN] Would reply to post {post_id}:")
            print("-" * 60)
            print(reply_text)
            print("=" * 60 + "\n")
            return True

        if self.review_mode:
            self._queue_item("reply", post_id=post_id, text=reply_text, post=post)
            logger.info("Queued reply for post %s (review_mode)", post_id)
            return True

        # Live submission
        reddit = self._get_praw()
        submission = reddit.submission(id=post_id)
        submission.reply(reply_text)
        logger.info("Replied to post %s", post_id)
        return True

    def make_post(
        self,
        subreddit_name: str,
        title: str,
        body: str,
    ) -> str | None:
        """
        Create a new text post.

        Returns:
            URL of created post, or None in dry_run/review_mode.
        """
        if self.dry_run:
            print("\n" + "=" * 60)
            print(f"[DRY-RUN] Would create post in r/{subreddit_name}:")
            print(f"TITLE: {title}")
            print("-" * 60)
            print(body)
            print("=" * 60 + "\n")
            return None

        if self.review_mode:
            self._queue_item(
                "post",
                subreddit=subreddit_name,
                title=title,
                text=body,
            )
            logger.info("Queued post for r/%s (review_mode)", subreddit_name)
            return None

        # Live submission
        reddit = self._get_praw()
        sub = reddit.subreddit(subreddit_name)
        submission = sub.submit(title=title, selftext=body)
        url = f"https://www.reddit.com{submission.permalink}"
        logger.info("Posted to r/%s: %s", subreddit_name, url)
        return url

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_praw(self):
        """Lazily build the PRAW client (only needed for write operations)."""
        if self._reddit is not None:
            return self._reddit
        if not _PRAW_AVAILABLE:
            raise RuntimeError(
                "praw is not installed. Install it to enable write operations."
            )
        missing = [v for v in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET",
                               "REDDIT_USERNAME", "REDDIT_PASSWORD")
                   if not os.getenv(v)]
        if missing:
            raise RuntimeError(
                f"Reddit write operations require credentials. "
                f"Missing env vars: {', '.join(missing)}\n"
                "Apply for API access at: "
                "https://support.reddithelp.com/hc/en-us/requests/new"
                "?ticket_form_id=14868593862164"
            )
        self._reddit = praw.Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            username=os.environ["REDDIT_USERNAME"],
            password=os.environ["REDDIT_PASSWORD"],
            user_agent=self._user_agent,
        )
        return self._reddit

    def _queue_item(self, action: str, **kwargs) -> None:
        REVIEW_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if REVIEW_QUEUE_PATH.exists():
            queue = json.loads(REVIEW_QUEUE_PATH.read_text())
        else:
            queue = []

        # Serialize any RedditPost objects so json.dumps doesn't choke
        serializable = {
            k: (v.to_dict() if isinstance(v, RedditPost) else v)
            for k, v in kwargs.items()
        }

        entry = {
            "id": str(uuid.uuid4()),
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
            **serializable,
        }
        queue.append(entry)
        REVIEW_QUEUE_PATH.write_text(json.dumps(queue, indent=2))


def _env_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key, "").lower()
    if val in ("true", "1", "yes"):
        return True
    if val in ("false", "0", "no"):
        return False
    return default
