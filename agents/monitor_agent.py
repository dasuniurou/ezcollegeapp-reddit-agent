"""
Monitor Agent: scans subreddits for relevant posts and filters out already-replied ones.
"""
from __future__ import annotations

import logging
import re
from typing import Generator

from tools.llm_client import LLMClient
from tools.memory_tool import MemoryTool
from tools.reddit_tool import RedditPost, RedditTool

logger = logging.getLogger(__name__)

_RELEVANCE_SYSTEM = """
You are a filter agent. Your job is to determine if a Reddit post is relevant
to college applications — specifically, if it's a question, request for help,
or discussion where advice about the application process would be genuinely useful.

Return ONLY a JSON object with two keys:
  "relevant": true or false
  "reason": a one-sentence explanation

Do not include anything else in your response.
"""

_RELEVANCE_USER = """
Subreddit: r/{subreddit}
Title: {title}
Body: {body}

Is this post relevant to college applications?
"""


class MonitorAgent:
    """
    Scans configured subreddits, classifies post relevance using an LLM,
    and yields posts that should be replied to.
    """

    def __init__(
        self,
        llm: LLMClient,
        reddit: RedditTool,
        memory: MemoryTool,
        keywords: list[str],
        post_limit: int = 25,
    ):
        self.llm = llm
        self.reddit = reddit
        self.memory = memory
        self.keywords = [kw.lower() for kw in keywords]
        self.post_limit = post_limit
        self._keyword_re = self._compile_keywords(self.keywords)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def scan(self, subreddits: list[str]) -> Generator[RedditPost, None, None]:
        """
        Scan subreddits and yield posts that are:
          1. Not already replied to
          2. Contain at least one keyword (pre-filter)
          3. Classified as relevant by the LLM
        """
        for sub in subreddits:
            logger.info("Scanning r/%s ...", sub)
            for post in self.reddit.scan_subreddit(sub, self.post_limit):
                if self.memory.has_replied(post.id):
                    logger.debug("Skipping already-replied post %s", post.id)
                    continue

                if not self._keyword_match(post):
                    continue

                if self._is_relevant(post):
                    logger.info("Relevant post found: %s [%s]", post.id, post.title[:60])
                    yield post

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _compile_keywords(keywords: list[str]) -> re.Pattern | None:
        """Build one word-boundary regex from the keyword list.

        Word boundaries prevent false positives that plain substring matching
        causes (e.g. "sat" matching "Saturday", "ed" matching "edited"), so short
        abbreviations like "ED", "EA", "GPA" are safe to include as keywords.
        """
        if not keywords:
            return None
        # Longest-first so multi-word phrases win over their sub-tokens.
        alts = "|".join(re.escape(kw) for kw in sorted(keywords, key=len, reverse=True))
        return re.compile(rf"\b(?:{alts})\b", re.IGNORECASE)

    def _keyword_match(self, post: RedditPost) -> bool:
        if self._keyword_re is None:
            return False
        text = f"{post.title} {post.body}"
        return self._keyword_re.search(text) is not None

    def _is_relevant(self, post: RedditPost) -> bool:
        import json as _json

        user_msg = _RELEVANCE_USER.format(
            subreddit=post.subreddit,
            title=post.title,
            body=post.body[:500],  # truncate long bodies
        )
        try:
            raw = self.llm.chat(system=_RELEVANCE_SYSTEM, user=user_msg)
            # Strip markdown code fences if present
            raw = raw.strip().strip("```json").strip("```").strip()
            result = _json.loads(raw)
            relevant = result.get("relevant", False)
            reason = result.get("reason", "")
            logger.debug("Relevance [%s]: %s — %s", post.id, relevant, reason)
            return bool(relevant)
        except Exception as exc:
            logger.warning("Relevance check failed for %s: %s", post.id, exc)
            return False
