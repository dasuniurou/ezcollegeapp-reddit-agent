"""
RAG tool: semantic retrieval over the college-admissions knowledge base.

Embeds each knowledge entry once (via OpenAI), caches the vectors to disk, and
retrieves the most relevant entries for a given Reddit post using cosine
similarity. The cache is committed to git so every account clone reuses the same
vectors with no re-embedding cost — it auto-rebuilds only if the knowledge base
file or embedding model changes.
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import numpy as np  # type: ignore

from tools.llm_client import LLMClient
from tools.reddit_tool import RedditPost

logger = logging.getLogger(__name__)

_BASE = Path(__file__).parent.parent
_DEFAULT_KB = _BASE / "knowledge_base" / "general-all-merged.json"
_DEFAULT_CACHE = _BASE / "knowledge_base" / "embeddings_cache.npz"


class RAGTool:
    """Embeds the knowledge base, caches vectors, and retrieves top-k entries."""

    def __init__(
        self,
        llm: LLMClient,
        kb_path: Path = _DEFAULT_KB,
        cache_path: Path = _DEFAULT_CACHE,
        top_k: int = 3,
        embed_model: str = "text-embedding-3-small",
    ):
        self.llm = llm
        self.kb_path = Path(kb_path)
        self.cache_path = Path(cache_path)
        self.top_k = top_k
        self.embed_model = embed_model

        self._entries: list[dict] = json.loads(self.kb_path.read_text())
        self._matrix: np.ndarray | None = None  # (N, dim), L2-normalized
        self._load_or_build_cache()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def retrieve(self, post: RedditPost) -> list[dict]:
        """
        Return the top-k knowledge entries most relevant to the post.

        Fails open: on any error (or if embeddings are unavailable) returns an
        empty list so the reply pipeline still runs ungrounded.
        """
        if self._matrix is None:
            return []
        try:
            query = f"{post.title}\n{post.body[:800]}"
            qvec = self.llm.embed([query])[0]
            qvec = _normalize(np.asarray(qvec, dtype=np.float32))
            scores = self._matrix @ qvec  # cosine similarity (both normalized)
            top_idx = np.argsort(scores)[::-1][: self.top_k]

            results = []
            for i in top_idx:
                entry = self._entries[int(i)]
                results.append(
                    {
                        "title": entry.get("title", ""),
                        "content": entry.get("content", ""),
                        "tags": entry.get("tags", []),
                        "score": float(scores[int(i)]),
                    }
                )
            logger.debug(
                "RAG retrieved %d entries for post %s (top score %.3f)",
                len(results), post.id, results[0]["score"] if results else 0.0,
            )
            return results
        except Exception as exc:  # noqa: BLE001 — fail open
            logger.warning("RAG retrieval failed for %s: %s", post.id, exc)
            return []

    @staticmethod
    def format_context(entries: list[dict]) -> str:
        """Render retrieved entries into a compact text block for prompt injection.

        Sources/URLs are intentionally dropped so no links leak into replies.
        """
        if not entries:
            return "No specific knowledge-base entries retrieved."
        blocks = []
        for i, entry in enumerate(entries, 1):
            blocks.append(f"### KB Entry {i}: {entry['title']}\n{entry['content']}")
        return "\n\n".join(blocks)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fingerprint(self) -> str:
        """sha256 of (knowledge base bytes + embed model) — cache invalidation key."""
        h = hashlib.sha256()
        h.update(self.kb_path.read_bytes())
        h.update(self.embed_model.encode("utf-8"))
        return h.hexdigest()

    def _load_or_build_cache(self) -> None:
        fingerprint = self._fingerprint()

        if self.cache_path.exists():
            try:
                cached = np.load(self.cache_path, allow_pickle=False)
                if str(cached["fingerprint"]) == fingerprint:
                    self._matrix = cached["matrix"].astype(np.float32)
                    logger.info(
                        "Loaded %d cached embeddings from %s",
                        self._matrix.shape[0], self.cache_path.name,
                    )
                    return
                logger.info("Embedding cache stale (fingerprint changed) — rebuilding.")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not read embedding cache (%s) — rebuilding.", exc)

        self._build_cache(fingerprint)

    def _build_cache(self, fingerprint: str) -> None:
        try:
            texts = [
                f"{e.get('title', '')}\n{e.get('content', '')}" for e in self._entries
            ]
            logger.info("Embedding %d knowledge-base entries ...", len(texts))
            vectors = self.llm.embed(texts)
            matrix = _normalize_rows(np.asarray(vectors, dtype=np.float32))

            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            np.savez(
                self.cache_path,
                matrix=matrix,
                fingerprint=np.array(fingerprint),
                ids=np.array([e.get("topic_id", "") for e in self._entries]),
            )
            self._matrix = matrix
            logger.info("Built and cached %d embeddings -> %s", len(texts), self.cache_path.name)
        except Exception as exc:  # noqa: BLE001 — fail open
            logger.warning("Failed to build embedding cache: %s — RAG disabled.", exc)
            self._matrix = None


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _normalize(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    return vec / norm if norm else vec


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms
