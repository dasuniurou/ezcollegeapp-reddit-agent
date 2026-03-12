"""
Layer 1 Tests: Dry-Run Mode
============================
Verify that DRY_RUN=true prevents any real Reddit API calls.
The full LLM → reply/post pipeline runs; only the PRAW submission is blocked.
All tests use a mock LLM so no real API key is needed.
"""
from __future__ import annotations

import os
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from tools.reddit_tool import RedditPost, RedditTool


# ---------------------------------------------------------------------------
# RedditTool dry-run behaviour
# ---------------------------------------------------------------------------

class TestRedditToolDryRun:
    """RedditTool should never build a PRAW client or submit when dry_run=True."""

    def test_dry_run_no_praw_client(self):
        """No praw.Reddit instance should be created in dry-run mode."""
        with patch("tools.reddit_tool.praw.Reddit") as mock_praw:
            tool = RedditTool(dry_run=True)
            mock_praw.assert_not_called()

    def test_dry_run_reply_prints_and_returns_true(self, capsys):
        tool = RedditTool(dry_run=True)
        result = tool.reply_to_post("abc123", "This is my reply text.")
        captured = capsys.readouterr()
        assert result is True
        assert "DRY-RUN" in captured.out
        assert "abc123" in captured.out
        assert "This is my reply text." in captured.out

    def test_dry_run_make_post_prints_and_returns_none(self, capsys):
        tool = RedditTool(dry_run=True)
        result = tool.make_post("ApplyingToCollege", "My Title", "My body text.")
        captured = capsys.readouterr()
        assert result is None
        assert "DRY-RUN" in captured.out
        assert "My Title" in captured.out
        assert "My body text." in captured.out

    def test_dry_run_scan_uses_public_api(self):
        """scan_subreddit uses the public JSON API even in dry-run mode."""
        fake_response = {
            "data": {
                "children": [
                    {
                        "data": {
                            "id": "abc123",
                            "title": "Test post",
                            "selftext": "body text",
                            "permalink": "/r/ApplyingToCollege/comments/abc123/test_post/",
                        }
                    }
                ]
            }
        }
        with patch("tools.reddit_tool.requests.get") as mock_get:
            mock_get.return_value.json.return_value = fake_response
            mock_get.return_value.raise_for_status = lambda: None
            tool = RedditTool(dry_run=True)
            posts = list(tool.scan_subreddit("ApplyingToCollege"))

        assert len(posts) == 1
        assert posts[0].id == "abc123"
        assert posts[0].title == "Test post"

    def test_dry_run_does_not_write_review_queue(self, tmp_path):
        """Dry-run should NOT write to the review queue."""
        with patch("tools.reddit_tool.REVIEW_QUEUE_PATH", tmp_path / "review_queue.json"):
            tool = RedditTool(dry_run=True, review_mode=False)
            tool.reply_to_post("post1", "reply text")
            assert not (tmp_path / "review_queue.json").exists()


# ---------------------------------------------------------------------------
# ReplyAgent dry-run: full pipeline, no Reddit submission
# ---------------------------------------------------------------------------

class TestReplyAgentDryRun:
    """ReplyAgent should generate a reply and 'submit' it via dry-run (print only)."""

    def test_reply_agent_calls_llm_and_dry_runs(
        self, capsys, mock_llm_approved_reply, tmp_memory_dir
    ):
        from agents.reply_agent import ReplyAgent

        reddit = RedditTool(dry_run=True)
        agent = ReplyAgent(
            llm=mock_llm_approved_reply,
            reddit=reddit,
            memory=tmp_memory_dir,
        )
        post = RedditPost(
            post_id="abc123",
            title="How do I write a Common App essay?",
            body="I need help with my personal statement.",
            subreddit="ApplyingToCollege",
            url="",
        )
        reply = agent.reply(post)

        # LLM was called (at least twice: once for reply, once for self-critique)
        assert mock_llm_approved_reply.chat.call_count >= 2

        # Reply was returned
        assert reply is not None
        assert len(reply) > 0

        # Dry-run output was printed
        captured = capsys.readouterr()
        assert "DRY-RUN" in captured.out

    def test_reply_agent_marks_post_replied_even_in_dry_run(
        self, mock_llm_approved_reply, tmp_memory_dir
    ):
        from agents.reply_agent import ReplyAgent

        reddit = RedditTool(dry_run=True)
        agent = ReplyAgent(
            llm=mock_llm_approved_reply,
            reddit=reddit,
            memory=tmp_memory_dir,
        )
        post = RedditPost("post999", "College essay help", "body text", "ApplyingToCollege", "")

        assert not tmp_memory_dir.has_replied("post999")
        agent.reply(post)
        assert tmp_memory_dir.has_replied("post999")

    def test_reply_agent_respects_daily_limit(
        self, mock_llm_approved_reply, tmp_memory_dir, capsys
    ):
        from agents.reply_agent import ReplyAgent

        reddit = RedditTool(dry_run=True)
        agent = ReplyAgent(
            llm=mock_llm_approved_reply,
            reddit=reddit,
            memory=tmp_memory_dir,
            max_daily_replies=1,
        )

        post1 = RedditPost("id1", "Essay help 1", "body", "ApplyingToCollege", "")
        post2 = RedditPost("id2", "Essay help 2", "body", "ApplyingToCollege", "")

        r1 = agent.reply(post1)
        r2 = agent.reply(post2)

        assert r1 is not None    # first reply goes through
        assert r2 is None        # second reply is blocked by limit


# ---------------------------------------------------------------------------
# PostAgent dry-run
# ---------------------------------------------------------------------------

class TestPostAgentDryRun:
    """PostAgent should generate a post and dry-run it without any PRAW call."""

    def test_post_agent_generates_and_dry_runs(
        self, capsys, mock_llm_post, tmp_memory_dir
    ):
        from agents.post_agent import PostAgent

        reddit = RedditTool(dry_run=True)
        agent = PostAgent(
            llm=mock_llm_post,
            reddit=reddit,
            memory=tmp_memory_dir,
        )
        title, body = agent.post(subreddit="ApplyingToCollege", post_format="story")

        assert title is not None
        assert body is not None
        assert "Common App" in title or len(title) > 5

        captured = capsys.readouterr()
        assert "DRY-RUN" in captured.out

    def test_post_agent_respects_daily_limit(self, mock_llm_post, tmp_memory_dir):
        from agents.post_agent import PostAgent

        reddit = RedditTool(dry_run=True)
        agent = PostAgent(
            llm=mock_llm_post,
            reddit=reddit,
            memory=tmp_memory_dir,
            max_daily_posts=1,
        )
        t1, b1 = agent.post("ApplyingToCollege", "story")
        t2, b2 = agent.post("ApplyingToCollege", "resource")

        assert t1 is not None
        assert t2 is None   # blocked by limit
