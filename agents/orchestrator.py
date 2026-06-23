"""
Orchestrator: wires together Monitor → Reply pipeline and exposes
the on-demand post interface.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import yaml  # type: ignore
from dotenv import load_dotenv  # type: ignore

from agents.monitor_agent import MonitorAgent
from agents.post_agent import PostAgent
from agents.reply_agent import ReplyAgent
from tools.llm_client import LLMClient
from tools.memory_tool import MemoryTool
from tools.rag_tool import RAGTool
from tools.reddit_tool import RedditTool

load_dotenv()
logger = logging.getLogger(__name__)

_SETTINGS_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"


class Orchestrator:
    """
    Central coordinator.  Two entry-points:
      - run_monitor_cycle(): scan subreddits → classify → reply
      - make_post():         on-demand personal experience post
    """

    def __init__(self, settings_path: Path = _SETTINGS_PATH):
        self.cfg = self._load_settings(settings_path)

        dry_run = _resolve_bool("DRY_RUN", self.cfg.get("dry_run", True))
        review_mode = _resolve_bool("REVIEW_MODE", self.cfg.get("review_mode", False))
        provider = os.getenv("LLM_PROVIDER") or self.cfg["llm"]["provider"]
        model = self._resolve_model(provider)
        embed_model = self.cfg.get("llm", {}).get("openai_embed_model", "text-embedding-3-small")

        self.llm = LLMClient(provider=provider, model=model, embed_model=embed_model)
        self.reddit = RedditTool(dry_run=dry_run, review_mode=review_mode)
        self.memory = MemoryTool()
        self.rag = self._build_rag(embed_model)

        rate = self.cfg["rate_limits"]
        self.monitor = MonitorAgent(
            llm=self.llm,
            reddit=self.reddit,
            memory=self.memory,
            keywords=self.cfg["keywords"],
            post_limit=self.cfg["reddit"]["post_limit"],
        )
        self.reply_agent = ReplyAgent(
            llm=self.llm,
            reddit=self.reddit,
            memory=self.memory,
            max_daily_replies=rate["max_replies_per_day"],
            rag=self.rag,
        )
        self.post_agent = PostAgent(
            llm=self.llm,
            reddit=self.reddit,
            memory=self.memory,
            max_daily_posts=rate["max_posts_per_day"],
        )

        logger.info(
            "Orchestrator ready | provider=%s model=%s dry_run=%s review_mode=%s rag=%s",
            provider, model, dry_run, review_mode, self.rag is not None,
        )

    # ------------------------------------------------------------------
    # Public entry-points
    # ------------------------------------------------------------------

    def run_monitor_cycle(self) -> int:
        """
        Scan all configured subreddits and reply to relevant posts.

        Returns:
            Number of posts replied to.
        """
        subreddits = self.cfg["subreddits"]
        delay = self.cfg["rate_limits"]["min_delay_between_replies_seconds"]
        replied = 0

        for post in self.monitor.scan(subreddits):
            result = self.reply_agent.reply(post)
            if result:
                replied += 1
                logger.info("Replied to post %s (%d total this cycle)", post.id, replied)
                if replied > 1 and not self.reddit.dry_run and not self.reddit.review_mode:
                    logger.debug("Sleeping %ds between replies ...", delay)
                    time.sleep(delay)

        logger.info("Monitor cycle complete. Replied to %d post(s).", replied)
        return replied

    def make_post(
        self,
        subreddit: str | None = None,
        post_format: str = "story",
        extra_context: str = "",
    ) -> tuple[str | None, str | None]:
        """
        Create an on-demand personal experience post.

        Args:
            subreddit:    Target subreddit. Defaults to first in config.
            post_format:  "story" | "tips" | "question"
            extra_context: Optional angle hint.

        Returns:
            (title, body)
        """
        target = subreddit or self.cfg["subreddits"][0]
        return self.post_agent.post(
            subreddit=target,
            post_format=post_format,
            extra_context=extra_context,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _load_settings(path: Path) -> dict:
        with path.open() as f:
            return yaml.safe_load(f)

    def _resolve_model(self, provider: str) -> str:
        llm_cfg = self.cfg.get("llm", {})
        if provider == "openai":
            return llm_cfg.get("openai_model", "gpt-4o")
        if provider == "gemini":
            return llm_cfg.get("gemini_model", "gemini-1.5-pro")
        return ""

    def _build_rag(self, embed_model: str) -> RAGTool | None:
        """Build the RAG tool from config, or None when disabled / on failure (fail-open)."""
        rag_cfg = self.cfg.get("rag", {})
        if not rag_cfg.get("enabled", False):
            logger.info("RAG disabled in config — replies will run ungrounded.")
            return None

        root = _SETTINGS_PATH.parent.parent
        kwargs: dict = {"llm": self.llm, "top_k": rag_cfg.get("top_k", 3), "embed_model": embed_model}
        kb_path = self._resolve_path(root, rag_cfg.get("kb_file"))
        cache_path = self._resolve_path(root, rag_cfg.get("cache_file"))
        if kb_path is not None:
            kwargs["kb_path"] = kb_path
        if cache_path is not None:
            kwargs["cache_path"] = cache_path
        try:
            return RAGTool(**kwargs)
        except Exception as exc:  # noqa: BLE001 — fail open
            logger.warning("Could not initialize RAGTool: %s — replies run ungrounded.", exc)
            return None

    @staticmethod
    def _resolve_path(root: Path, value: str | None) -> Path | None:
        if not value:
            return None
        p = Path(value)
        return p if p.is_absolute() else root / p


def _resolve_bool(env_key: str, config_default: bool) -> bool:
    val = os.getenv(env_key, "").lower()
    if val in ("true", "1", "yes"):
        return True
    if val in ("false", "0", "no"):
        return False
    return config_default
