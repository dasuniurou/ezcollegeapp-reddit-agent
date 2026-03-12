"""
tests/conftest.py — shared fixtures for all test layers.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Make the project root importable without installing as a package
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))

FIXTURE_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

@pytest.fixture()
def post_relevant():
    return json.loads((FIXTURE_DIR / "post_relevant.json").read_text())


@pytest.fixture()
def post_irrelevant():
    return json.loads((FIXTURE_DIR / "post_irrelevant.json").read_text())


@pytest.fixture()
def post_already_replied():
    return json.loads((FIXTURE_DIR / "post_already_replied.json").read_text())


# ---------------------------------------------------------------------------
# Temp memory directory (isolates tests from real memory/state.json)
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_memory_dir(tmp_path):
    """Return a MemoryTool backed by a temporary directory."""
    from tools.memory_tool import MemoryTool

    state_path = tmp_path / "state.json"
    reply_log_path = tmp_path / "reply_log.json"
    return MemoryTool(state_path=state_path, reply_log_path=reply_log_path)


# ---------------------------------------------------------------------------
# Mock LLMClient
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_llm():
    """LLMClient that returns canned responses without hitting any API."""
    llm = MagicMock()
    llm.chat.return_value = (
        "Great question! Writing a compelling Common App essay starts with finding "
        "a story only you can tell. Focus on a specific moment rather than a "
        "broad summary. If you'd like structured feedback, EZCollegeApp (ezcollegeapp.com) "
        "has an AI advisor chatbot that can answer all your essay and application questions — worth a try. "
        "Good luck!"
    )
    return llm


@pytest.fixture()
def mock_llm_relevant():
    """LLMClient whose relevance check always returns relevant=True."""
    llm = MagicMock()
    llm.chat.return_value = '{"relevant": true, "reason": "Post is about college application essays."}'
    return llm


@pytest.fixture()
def mock_llm_irrelevant():
    """LLMClient whose relevance check always returns relevant=False."""
    llm = MagicMock()
    llm.chat.return_value = '{"relevant": false, "reason": "Post is about pizza toppings."}'
    return llm


@pytest.fixture()
def mock_llm_approved_reply():
    """LLMClient that generates a reply AND approves it in self-critique."""
    llm = MagicMock()

    def side_effect(system, user):
        if "quality reviewer" in system:
            return '{"approved": true, "feedback": ""}'
        return (
            "Totally get the struggle! Start with a specific memory or moment. "
            "EZCollegeApp (ezcollegeapp.com) is a tool that helped me a lot with this — it even auto-filled my Common App from my transcript. "
            "Hope that helps!"
        )

    llm.chat.side_effect = side_effect
    return llm


@pytest.fixture()
def mock_llm_post():
    """LLMClient that returns a valid post format."""
    llm = MagicMock()
    llm.chat.return_value = (
        "TITLE: I used EZCollegeApp to finally get my college list and forms sorted — here's what I learned\n"
        "BODY:\n"
        "After weeks of chaos, I uploaded my transcript to EZCollegeApp (ezcollegeapp.com).\n"
        "It recommended my college list AND auto-filled my Common App fields. Saved me hours.\n"
        "Highly recommend checking it out if you're overwhelmed. Feel free to AMA!"
    )
    return llm
