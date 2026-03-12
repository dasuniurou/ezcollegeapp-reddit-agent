"""
Post Agent: on-demand creation of personal experience Reddit posts
from the perspective of a student who used EZCollegeApp.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from tools.llm_client import LLMClient
from tools.memory_tool import MemoryTool
from tools.prompt_loader import (
    load_md,
    load_subreddit_guide,
    load_yaml_prompt,
    render,
)
from tools.reddit_tool import RedditTool

logger = logging.getLogger(__name__)

POST_FORMATS = ("story", "tips", "question")


class PostAgent:
    """
    Generates and publishes a new Reddit post sharing a student's personal
    experience using EZCollegeApp during the college application process.
    Called on-demand (not by the scheduler).
    """

    def __init__(
        self,
        llm: LLMClient,
        reddit: RedditTool,
        memory: MemoryTool,
        max_daily_posts: int = 2,
    ):
        self.llm = llm
        self.reddit = reddit
        self.memory = memory
        self.max_daily_posts = max_daily_posts
        self._prompts = load_yaml_prompt("post_prompt.yaml")
        self._product_context = load_md("product_context.md")
        self._brand_voice = load_md("brand_voice.md")

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def post(
        self,
        subreddit: str,
        post_format: str = "story",
        extra_context: str = "",
    ) -> tuple[str | None, str | None]:
        """
        Generate and submit a post.

        Args:
            subreddit:    Target subreddit name (without r/).
            post_format:  "story" | "resource" | "question"
            extra_context: Optional angle or talking point hint.

        Returns:
            (title, body) — body is None if skipped.
        """
        if post_format not in POST_FORMATS:
            raise ValueError(f"post_format must be one of {POST_FORMATS} — note: 'resource' has been replaced by 'tips'")

        if self.memory.daily_post_count() >= self.max_daily_posts:
            logger.warning("Daily post limit reached (%d). Skipping.", self.max_daily_posts)
            return None, None

        subreddit_guide = load_subreddit_guide(subreddit)

        system = render(
            self._prompts["system_prompt"],
            subreddit=subreddit,
            product_context=self._product_context,
            brand_voice=self._brand_voice,
            subreddit_guide=subreddit_guide or "No specific guide available.",
        )
        user = render(
            self._prompts["user_prompt"],
            subreddit=subreddit,
            post_format=post_format,
            extra_context=extra_context or "No additional context provided.",
        )

        raw = self.llm.chat(system=system, user=user)
        title, body = self._parse_output(raw)

        if not title or not body:
            logger.error("Failed to parse post output:\n%s", raw)
            return None, None

        url = self.reddit.make_post(subreddit, title, body)
        self.memory.increment_post_count()
        self.memory.log_reply(
            {
                "type": "post",
                "subreddit": subreddit,
                "title": title,
                "body": body,
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        logger.info("Post created in r/%s: %s", subreddit, title)
        return title, body

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _parse_output(self, raw: str) -> tuple[str | None, str | None]:
        """
        Parse LLM output into (title, body).
        Expected format:
            TITLE: <title>
            BODY:
            <body>
        """
        lines = raw.strip().splitlines()
        title = None
        body_lines: list[str] = []
        in_body = False

        for line in lines:
            if line.startswith("TITLE:") and not title:
                title = line[len("TITLE:"):].strip()
            elif line.startswith("BODY:"):
                in_body = True
            elif in_body:
                body_lines.append(line)

        body = "\n".join(body_lines).strip() or None
        return title, body
