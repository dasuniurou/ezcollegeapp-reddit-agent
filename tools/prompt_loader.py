"""
Utility for loading prompt templates and context files.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_yaml_prompt(filename: str) -> dict[str, str]:
    """Load a YAML prompt file and return its contents as a dict."""
    path = _PROMPTS_DIR / filename
    with path.open() as f:
        return yaml.safe_load(f)


def load_md(filename: str) -> str:
    """Load a markdown context file."""
    path = _PROMPTS_DIR / filename
    return path.read_text()


def load_subreddit_guide(subreddit_name: str) -> str:
    """Load a subreddit-specific guide if available, else return empty string."""
    path = _PROMPTS_DIR / f"subreddit_{subreddit_name}.md"
    if path.exists():
        return path.read_text()
    return ""


def render(template: str, **kwargs: Any) -> str:
    """Simple {key} substitution in a template string."""
    return template.format(**kwargs)
