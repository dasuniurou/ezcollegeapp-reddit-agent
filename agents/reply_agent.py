"""
Reply Agent: crafts a helpful Reddit reply from the perspective of a student
who used EZCollegeApp, sharing personal experience and advice.
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
from tools.reddit_tool import RedditPost, RedditTool

logger = logging.getLogger(__name__)

_SELF_CRITIQUE_SYSTEM = """
You are a Reddit quality reviewer. Given a draft reply to a Reddit post,
decide whether it is good enough to post and return ONLY a JSON object:
{
  "approved": true or false,
  "feedback": "one-sentence reason if rejected"
}

Approve if:
- The reply genuinely addresses the poster's question or concern with real advice
- The tone is friendly and peer-like, as if written by a fellow student
- Any mention of EZCollegeApp is brief (1-2 sentences), comes AFTER the real advice,
  and reads like casual personal experience ("I used it for X") not a recommendation

Reject ONLY if:
- The reply is mostly an advertisement with little real advice
- The reply ignores what the poster actually asked
- The reply opens with a product mention instead of leading with advice
- The reply makes false claims (e.g. guarantees admission)

When in doubt, approve — a helpful student reply with a soft personal mention is fine.
"""

_SELF_CRITIQUE_USER = """
Original post title: {post_title}
Draft reply:
{reply}

Approve or reject?
"""


class ReplyAgent:
    """
    Generates a reply to a Reddit post using the LLM,
    runs a self-critique pass, and submits if approved.
    """

    def __init__(
        self,
        llm: LLMClient,
        reddit: RedditTool,
        memory: MemoryTool,
        max_daily_replies: int = 10,
    ):
        self.llm = llm
        self.reddit = reddit
        self.memory = memory
        self.max_daily_replies = max_daily_replies
        self._prompts = load_yaml_prompt("reply_prompt.yaml")
        self._product_context = load_md("product_context.md")
        self._brand_voice = load_md("brand_voice.md")

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def reply(self, post: RedditPost) -> str | None:
        """
        Generate and submit a reply to the given post.

        Returns:
            The reply text if submitted, None if skipped.
        """
        if self.memory.daily_reply_count() >= self.max_daily_replies:
            logger.warning("Daily reply limit reached (%d). Skipping.", self.max_daily_replies)
            return None

        subreddit_guide = load_subreddit_guide(post.subreddit)

        system = render(
            self._prompts["system_prompt"],
            subreddit=post.subreddit,
            product_context=self._product_context,
            brand_voice=self._brand_voice,
            subreddit_guide=subreddit_guide or "No specific guide available.",
        )
        user = render(
            self._prompts["user_prompt"],
            subreddit=post.subreddit,
            post_title=post.title,
            post_body=post.body[:800],
        )

        reply_text = self.llm.chat(system=system, user=user)
        logger.debug("Generated reply for %s:\n%s", post.id, reply_text[:200])

        if not self._self_critique(post.title, reply_text):
            logger.info("Reply for %s rejected by self-critique. Skipping.", post.id)
            return None

        success = self.reddit.reply_to_post(post.id, reply_text, post=post)
        if success:
            self.memory.mark_replied(post.id)
            self.memory.log_reply(
                {
                    "post_id": post.id,
                    "post_title": post.title,
                    "subreddit": post.subreddit,
                    "reply": reply_text,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        return reply_text if success else None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _self_critique(self, post_title: str, reply: str) -> bool:
        import json as _json

        user_msg = _SELF_CRITIQUE_USER.format(post_title=post_title, reply=reply)
        try:
            raw = self.llm.chat(system=_SELF_CRITIQUE_SYSTEM, user=user_msg)
            raw = raw.strip().strip("```json").strip("```").strip()
            result = _json.loads(raw)
            approved = result.get("approved", False)
            feedback = result.get("feedback", "")
            if not approved:
                logger.debug("Self-critique rejected reply: %s", feedback)
            return bool(approved)
        except Exception as exc:
            logger.warning("Self-critique failed: %s — approving by default.", exc)
            return True
