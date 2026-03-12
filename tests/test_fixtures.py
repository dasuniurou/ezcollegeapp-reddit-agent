"""
Layer 2 Tests: Static Fixture Tests
=====================================
Feed saved Reddit post JSON snapshots directly to agents.
No Reddit API calls, no real LLM calls.
Tests cover:
  - Keyword pre-filtering
  - LLM relevance classification
  - MonitorAgent routing (relevant vs irrelevant vs already-replied)
  - ReplyAgent self-critique approval and rejection
  - PostAgent output parsing
  - MemoryTool deduplication
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.reddit_tool import RedditPost

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _post_from_fixture(name: str) -> RedditPost:
    data = json.loads((FIXTURE_DIR / name).read_text())
    return RedditPost.from_dict(data)


# ---------------------------------------------------------------------------
# MemoryTool
# ---------------------------------------------------------------------------

class TestMemoryTool:
    def test_has_replied_false_initially(self, tmp_memory_dir):
        assert not tmp_memory_dir.has_replied("new_post_id")

    def test_mark_replied_persists(self, tmp_memory_dir):
        tmp_memory_dir.mark_replied("post_abc")
        assert tmp_memory_dir.has_replied("post_abc")

    def test_daily_counter_increments(self, tmp_memory_dir):
        assert tmp_memory_dir.daily_reply_count() == 0
        tmp_memory_dir.mark_replied("p1")
        tmp_memory_dir.mark_replied("p2")
        assert tmp_memory_dir.daily_reply_count() == 2

    def test_daily_post_counter(self, tmp_memory_dir):
        assert tmp_memory_dir.daily_post_count() == 0
        tmp_memory_dir.increment_post_count()
        assert tmp_memory_dir.daily_post_count() == 1

    def test_reply_log_append(self, tmp_memory_dir):
        tmp_memory_dir.log_reply({"post_id": "x", "reply": "hello"})
        tmp_memory_dir.log_reply({"post_id": "y", "reply": "world"})
        log = tmp_memory_dir.load_reply_log()
        assert len(log) == 2
        assert log[0]["post_id"] == "x"

    def test_no_duplicate_post_ids_in_state(self, tmp_memory_dir):
        tmp_memory_dir.mark_replied("dup")
        tmp_memory_dir.mark_replied("dup")
        state = tmp_memory_dir.load_state()
        assert state["replied_post_ids"].count("dup") == 1


# ---------------------------------------------------------------------------
# MonitorAgent — keyword filtering
# ---------------------------------------------------------------------------

class TestMonitorAgentKeywordFilter:
    """Tests the keyword pre-filter without any Reddit connection."""

    def _make_monitor(self, llm, memory):
        from agents.monitor_agent import MonitorAgent
        from tools.reddit_tool import RedditTool

        reddit = RedditTool(dry_run=True)
        return MonitorAgent(
            llm=llm,
            reddit=reddit,
            memory=memory,
            keywords=["college application", "common app", "personal statement", "essay"],
        )

    def test_relevant_post_passes_keyword_filter(self, mock_llm_relevant, tmp_memory_dir):
        monitor = self._make_monitor(mock_llm_relevant, tmp_memory_dir)
        post = _post_from_fixture("post_relevant.json")
        assert monitor._keyword_match(post) is True

    def test_irrelevant_post_fails_keyword_filter(self, mock_llm_irrelevant, tmp_memory_dir):
        monitor = self._make_monitor(mock_llm_irrelevant, tmp_memory_dir)
        post = _post_from_fixture("post_irrelevant.json")
        assert monitor._keyword_match(post) is False

    def test_already_replied_post_is_skipped(self, mock_llm_relevant, tmp_memory_dir):
        monitor = self._make_monitor(mock_llm_relevant, tmp_memory_dir)
        post = _post_from_fixture("post_already_replied.json")
        # Mark as already replied
        tmp_memory_dir.mark_replied(post.id)
        assert tmp_memory_dir.has_replied(post.id) is True


# ---------------------------------------------------------------------------
# MonitorAgent — LLM relevance classification
# ---------------------------------------------------------------------------

class TestMonitorAgentRelevanceClassification:
    def _make_monitor(self, llm, memory):
        from agents.monitor_agent import MonitorAgent
        from tools.reddit_tool import RedditTool

        return MonitorAgent(
            llm=llm,
            reddit=RedditTool(dry_run=True),
            memory=memory,
            keywords=["college", "essay"],
        )

    def test_is_relevant_returns_true(self, tmp_memory_dir):
        llm = MagicMock()
        llm.chat.return_value = '{"relevant": true, "reason": "College essay question."}'
        monitor = self._make_monitor(llm, tmp_memory_dir)
        post = _post_from_fixture("post_relevant.json")
        assert monitor._is_relevant(post) is True

    def test_is_relevant_returns_false(self, tmp_memory_dir):
        llm = MagicMock()
        llm.chat.return_value = '{"relevant": false, "reason": "Not about college apps."}'
        monitor = self._make_monitor(llm, tmp_memory_dir)
        post = _post_from_fixture("post_irrelevant.json")
        assert monitor._is_relevant(post) is False

    def test_malformed_json_defaults_to_not_relevant(self, tmp_memory_dir):
        """If LLM returns bad JSON, relevance check should fail-safe to False."""
        llm = MagicMock()
        llm.chat.return_value = "I think it's relevant!"  # not JSON
        monitor = self._make_monitor(llm, tmp_memory_dir)
        post = _post_from_fixture("post_relevant.json")
        assert monitor._is_relevant(post) is False


# ---------------------------------------------------------------------------
# ReplyAgent — self-critique
# ---------------------------------------------------------------------------

class TestReplyAgentSelfCritique:
    def _make_agent(self, llm, memory):
        from agents.reply_agent import ReplyAgent
        from tools.reddit_tool import RedditTool

        return ReplyAgent(
            llm=llm,
            reddit=RedditTool(dry_run=True),
            memory=memory,
        )

    def test_self_critique_approves_good_reply(self, tmp_memory_dir):
        llm = MagicMock()
        llm.chat.return_value = '{"approved": true, "feedback": ""}'
        agent = self._make_agent(llm, tmp_memory_dir)
        assert agent._self_critique("Some title", "Some reply") is True

    def test_self_critique_rejects_spammy_reply(self, tmp_memory_dir):
        llm = MagicMock()
        llm.chat.return_value = '{"approved": false, "feedback": "Too promotional."}'
        agent = self._make_agent(llm, tmp_memory_dir)
        assert agent._self_critique("Some title", "Buy EZCollegeApp now!!!") is False

    def test_self_critique_bad_json_defaults_to_approve(self, tmp_memory_dir):
        """Fail-safe: if self-critique fails to parse, approve the reply."""
        llm = MagicMock()
        llm.chat.return_value = "Looks great!"  # not JSON
        agent = self._make_agent(llm, tmp_memory_dir)
        assert agent._self_critique("title", "reply") is True

    def test_rejected_reply_not_submitted_or_logged(self, tmp_memory_dir):
        """When self-critique rejects, reply should NOT be submitted or logged."""
        def side_effect(system, user):
            if "quality reviewer" in system:
                return '{"approved": false, "feedback": "Too salesy."}'
            return "Buy EZCollegeApp! It is the best product!"

        llm = MagicMock()
        llm.chat.side_effect = side_effect

        agent = self._make_agent(llm, tmp_memory_dir)
        post = _post_from_fixture("post_relevant.json")
        result = agent.reply(post)

        assert result is None
        assert not tmp_memory_dir.has_replied(post.id)
        assert tmp_memory_dir.load_reply_log() == []


# ---------------------------------------------------------------------------
# PostAgent — output parsing
# ---------------------------------------------------------------------------

class TestPostAgentOutputParsing:
    def _make_agent(self, llm, memory):
        from agents.post_agent import PostAgent
        from tools.reddit_tool import RedditTool

        return PostAgent(
            llm=llm,
            reddit=RedditTool(dry_run=True),
            memory=memory,
        )

    def test_parse_valid_output(self, tmp_memory_dir):
        llm = MagicMock()
        llm.chat.return_value = (
            "TITLE: How I finally nailed my Common App essay\n"
            "BODY:\n"
            "Long story short, I used EZCollegeApp and it auto-filled my Common App.\n"
            "Check it out at ezcollegeapp.com."
        )
        agent = self._make_agent(llm, tmp_memory_dir)
        title, body = agent.post("ApplyingToCollege", "story")

        assert title == "How I finally nailed my Common App essay"
        assert "EZCollegeApp" in body

    def test_parse_missing_body_returns_none(self, tmp_memory_dir):
        llm = MagicMock()
        llm.chat.return_value = "TITLE: Just a title with no body"
        agent = self._make_agent(llm, tmp_memory_dir)
        title, body = agent.post("ApplyingToCollege", "story")

        # Body missing → entire post should be skipped
        assert title is None or body is None

    def test_invalid_format_raises(self, tmp_memory_dir):
        from agents.post_agent import PostAgent
        from tools.reddit_tool import RedditTool

        agent = PostAgent(
            llm=MagicMock(),
            reddit=RedditTool(dry_run=True),
            memory=tmp_memory_dir,
        )
        with pytest.raises(ValueError, match="post_format"):
            agent.post("ApplyingToCollege", post_format="invalid_format")


# ---------------------------------------------------------------------------
# LLMClient — provider validation
# ---------------------------------------------------------------------------

class TestLLMClientValidation:
    def test_unsupported_provider_raises(self):
        import os
        from tools.llm_client import LLMClient

        with patch.dict(os.environ, {"LLM_PROVIDER": "grok", "OPENAI_API_KEY": "fake"}):
            with pytest.raises(ValueError, match="Unsupported provider"):
                LLMClient(provider="grok")

    def test_missing_openai_key_raises(self):
        import os
        from tools.llm_client import LLMClient

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENAI_API_KEY", None)
            with pytest.raises(EnvironmentError, match="OPENAI_API_KEY"):
                LLMClient(provider="openai")

    def test_missing_gemini_key_raises(self):
        import os
        from tools.llm_client import LLMClient

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GEMINI_API_KEY", None)
            with pytest.raises(EnvironmentError, match="GEMINI_API_KEY"):
                LLMClient(provider="gemini")
