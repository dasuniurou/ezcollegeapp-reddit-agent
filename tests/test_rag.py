"""
Tests for tools/rag_tool.py — embedding cache, retrieval ranking, and fail-open.
All tests use a fake keyword-based embedder so no API key or network is needed.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from tools.rag_tool import RAGTool
from tools.reddit_tool import RedditPost

# Keyword "embedding" space — each dimension is a topic keyword. A text's vector
# has 1.0 where the keyword appears, so cosine similarity ranks by keyword overlap.
_VOCAB = ["essay", "school", "list", "scholarship", "deadline", "form"]


def _keyword_embed(texts):
    vectors = []
    for t in texts:
        low = t.lower()
        vectors.append([1.0 if kw in low else 0.0 for kw in _VOCAB])
    return vectors


@pytest.fixture()
def kb_file(tmp_path):
    entries = [
        {"topic_id": "T1", "title": "Writing your college essay",
         "content": "How to approach the personal statement essay.", "tags": ["essay"]},
        {"topic_id": "T2", "title": "Building a balanced school list",
         "content": "Reach target safety school list strategy.", "tags": ["school-list"]},
        {"topic_id": "T3", "title": "Scholarship deadlines",
         "content": "Track each scholarship deadline carefully.", "tags": ["scholarship"]},
    ]
    path = tmp_path / "kb.json"
    path.write_text(json.dumps(entries))
    return path


@pytest.fixture()
def fake_llm():
    llm = MagicMock()
    llm.embed.side_effect = _keyword_embed
    return llm


def test_cache_is_written_then_reused(kb_file, fake_llm, tmp_path):
    cache = tmp_path / "cache.npz"

    rag1 = RAGTool(llm=fake_llm, kb_path=kb_file, cache_path=cache)
    assert cache.exists()
    build_calls = fake_llm.embed.call_count  # one batched call to embed all entries
    assert build_calls == 1

    # A second instance with the same KB + cache must NOT re-embed during init.
    RAGTool(llm=fake_llm, kb_path=kb_file, cache_path=cache)
    assert fake_llm.embed.call_count == build_calls  # no extra embed call


def test_retrieve_ranks_matching_entry_first(kb_file, fake_llm, tmp_path):
    rag = RAGTool(llm=fake_llm, kb_path=kb_file, cache_path=tmp_path / "cache.npz", top_k=3)
    post = RedditPost("p1", "Help with my college essay", "How do I start my essay?",
                      "ApplyingToCollege", "")
    results = rag.retrieve(post)
    assert results
    assert results[0]["title"] == "Writing your college essay"


def test_retrieval_fails_open(kb_file, fake_llm, tmp_path):
    rag = RAGTool(llm=fake_llm, kb_path=kb_file, cache_path=tmp_path / "cache.npz")
    # Force an embedding error at query time → retrieve returns [] (no raise).
    fake_llm.embed.side_effect = RuntimeError("embedding API down")
    post = RedditPost("p2", "School list help", "body", "college", "")
    assert rag.retrieve(post) == []
    assert "No specific knowledge-base" in RAGTool.format_context([])


def test_reply_pipeline_completes_when_rag_fails(kb_file, fake_llm, tmp_path,
                                                 mock_llm_approved_reply, tmp_memory_dir, capsys):
    """A failing RAG retrieval must not break the reply pipeline (dry-run)."""
    from agents.reply_agent import ReplyAgent
    from tools.reddit_tool import RedditTool

    rag = RAGTool(llm=fake_llm, kb_path=kb_file, cache_path=tmp_path / "cache.npz")
    fake_llm.embed.side_effect = RuntimeError("embedding API down")

    agent = ReplyAgent(
        llm=mock_llm_approved_reply,
        reddit=RedditTool(dry_run=True),
        memory=tmp_memory_dir,
        rag=rag,
    )
    post = RedditPost("p3", "College essay help", "body text", "ApplyingToCollege", "")
    reply = agent.reply(post)

    assert reply is not None
    assert "DRY-RUN" in capsys.readouterr().out
