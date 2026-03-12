"""
Memory tool: manages operational state (seen posts, rate limits) and reply logs.

Files:
    memory/state.json    — replied post IDs, daily counters
    memory/reply_log.json — full history of all generated replies
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_BASE = Path(__file__).parent.parent / "memory"
STATE_PATH = _BASE / "state.json"
REPLY_LOG_PATH = _BASE / "reply_log.json"

_DEFAULT_STATE = {
    "replied_post_ids": [],
    "daily_reply_count": 0,
    "daily_post_count": 0,
    "last_reset_date": "",
}


class MemoryTool:
    """Read/write wrapper for state.json and reply_log.json."""

    def __init__(
        self,
        state_path: Path = STATE_PATH,
        reply_log_path: Path = REPLY_LOG_PATH,
    ):
        self._state_path = state_path
        self._reply_log_path = reply_log_path
        _BASE.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def load_state(self) -> dict:
        state = _read_json(self._state_path, _DEFAULT_STATE.copy())
        state = self._maybe_reset_daily_counters(state)
        return state

    def save_state(self, state: dict) -> None:
        _write_json(self._state_path, state)

    def has_replied(self, post_id: str) -> bool:
        state = self.load_state()
        return post_id in state.get("replied_post_ids", [])

    def mark_replied(self, post_id: str) -> None:
        state = self.load_state()
        if post_id not in state["replied_post_ids"]:
            state["replied_post_ids"].append(post_id)
        state["daily_reply_count"] = state.get("daily_reply_count", 0) + 1
        self.save_state(state)

    def increment_post_count(self) -> None:
        state = self.load_state()
        state["daily_post_count"] = state.get("daily_post_count", 0) + 1
        self.save_state(state)

    def daily_reply_count(self) -> int:
        return self.load_state().get("daily_reply_count", 0)

    def daily_post_count(self) -> int:
        return self.load_state().get("daily_post_count", 0)

    # ------------------------------------------------------------------
    # Reply log helpers
    # ------------------------------------------------------------------

    def log_reply(self, entry: dict[str, Any]) -> None:
        """Append a reply record to reply_log.json."""
        log = _read_json(self._reply_log_path, [])
        entry.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        log.append(entry)
        _write_json(self._reply_log_path, log)

    def load_reply_log(self) -> list[dict]:
        return _read_json(self._reply_log_path, [])

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _maybe_reset_daily_counters(self, state: dict) -> dict:
        today = date.today().isoformat()
        if state.get("last_reset_date") != today:
            state["daily_reply_count"] = 0
            state["daily_post_count"] = 0
            state["last_reset_date"] = today
            self.save_state(state)
        return state


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        logger.warning("Could not read %s, using default.", path)
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
