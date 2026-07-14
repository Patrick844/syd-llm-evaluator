"""Semantic retrieval over the preventive-health knowledge base.

Embeds each KB entry once at startup with OpenAI embeddings and answers queries
with cosine-similarity search. In-memory and dependency-light (pure-Python
cosine) — the KB is small; swap in pgvector/FAISS when it grows.
"""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")


def _client() -> OpenAI:
    return OpenAI(base_url=os.getenv("OPENAI_BASE_URL") or None, api_key=os.getenv("OPENAI_API_KEY"))


def _embed(texts: list[str]) -> list[list[float]]:
    resp = _client().embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in resp.data]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


class KBRetriever:
    """Embeds the KB at construction; `.search()` returns the top-k entries."""

    def __init__(self, kb: list[dict[str, Any]]) -> None:
        self.kb = kb or []
        self._embeddings: list[list[float]] = []
        if self.kb:
            self._embeddings = _embed([self._entry_text(e) for e in self.kb])

    @staticmethod
    def _entry_text(entry: dict[str, Any]) -> str:
        return (
            f"{entry.get('topic', '')}. {entry.get('guideline', '')} "
            f"Population: {entry.get('population', '')}. Notes: {entry.get('notes', '')}"
        )

    def search(self, query: str, k: int = 3, min_score: float = 0.2) -> list[dict[str, Any]]:
        if not self.kb:
            return []
        qv = _embed([query])[0]
        scored = sorted(
            ((_cosine(qv, emb), i) for i, emb in enumerate(self._embeddings)),
            reverse=True,
        )
        results: list[dict[str, Any]] = []
        for score, idx in scored[:k]:
            if score < min_score:
                continue
            results.append({**self.kb[idx], "score": round(score, 3)})
        return results
