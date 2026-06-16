"""
Memory retrievers.

One retriever = one ranking signal. Plug into MemoryTools via
`get_relevant_memories(..., retriever="hybrid")` or via the eval runner
which iterates over all registered retrievers for multi-mode metrics.

Each retriever returns the same dict shape that MemoryTools._row_to_dict
emits, so callers downstream don't care which ranking produced the row.

Add a new retriever:
  1. Subclass MemoryRetriever, set `name`
  2. Implement retrieve() with your SQL/ranking
  3. Add to REGISTRY

Adding a retriever does not change the production default (hybrid).
"""
from __future__ import annotations

import logging
import math
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.embedding_service import embed_text_sync, vec_literal

logger = logging.getLogger(__name__)


def _safe_float_or_none(val: Any) -> Optional[float]:
    """Convert to float, returning None for None or NaN.

    BUG-20260615-01: pgvector's `<=>` returns NaN (not NULL) when the
    query embedding is a zero vector — e.g., Ollama is down. NaN doesn't
    satisfy `is not None`, so it slips through the COALESCE / null-check
    and ends up as a literal NaN in the API response, which crashes JSON
    consumers that don't expect it. Convert NaN to None at the
    serialization boundary.
    """
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    return float(val)


def _row_to_dict(r: Any) -> Dict[str, Any]:
    """Same shape MemoryTools._row_to_dict emits."""
    sim = r.get("similarity")
    score = r.get("score")
    return {
        "id": r["id"],
        "user_id": r.get("user_id"),
        "memory_type": r["memory_type"],
        "content": r["content"],
        "importance_score": r["importance_score"],
        "confidence_score": float(r["confidence_score"]) if r.get("confidence_score") is not None else 0.8,
        "source": r["source"],
        "source_message_id": r.get("source_message_id"),
        "status": r["status"],
        "last_used_at": r["last_used_at"].isoformat() if r.get("last_used_at") else None,
        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
        "updated_at": r["updated_at"].isoformat() if r.get("updated_at") else None,
        "metadata": r.get("metadata_json"),
        "embedding_status": r.get("embedding_status"),
        "similarity": _safe_float_or_none(sim),
        "score": _safe_float_or_none(score),
    }


class MemoryRetriever(ABC):
    """Pluggable memory retriever. `name` is the registry key."""

    name: str = "base"

    @abstractmethod
    def retrieve(
        self,
        db: Session,
        user_id: int,
        query_text: str,
        memory_types: Optional[List[str]],
        limit: int,
    ) -> List[Dict[str, Any]]:
        ...


# ---------------------------------------------------------------------------
# Vector-only: cos distance against pgvector embedding
# ---------------------------------------------------------------------------

class VectorRetriever(MemoryRetriever):
    """Pure vector recall. Same embedding flow as hybrid but importance=0."""

    name = "vector"

    def retrieve(self, db, user_id, query_text, memory_types, limit):
        try:
            vec = embed_text_sync(query_text)
            vec_str = vec_literal(vec)
            sql = f"""
                SELECT id, user_id, memory_type, content, importance_score, confidence_score,
                       source, source_message_id, status, last_used_at, created_at, updated_at,
                       metadata_json, embedding_status, embedding_updated_at,
                       COALESCE(1 - (embedding <=> CAST(:qvec AS vector)), 0.0) AS similarity
                FROM memory_items
                WHERE user_id = :uid AND status = 'active'
                  {'AND memory_type = ANY(:mtypes)' if memory_types else ''}
                ORDER BY similarity DESC, importance_score DESC, created_at DESC
                LIMIT :lim
            """
            params = {"uid": user_id, "qvec": vec_str, "lim": limit}
            if memory_types:
                params["mtypes"] = memory_types
            rows = db.execute(text(sql), params).mappings().all()
            return [_row_to_dict(r) for r in rows]
        except Exception as e:
            logger.warning("vector retriever failed: %s", e)
            return []


# ---------------------------------------------------------------------------
# Importance-only: pure ORM, no embedding, no SQL ranking beyond importance
# ---------------------------------------------------------------------------

class ImportanceRetriever(MemoryRetriever):
    """Recall ranked purely by importance_score. No embedding cost, no Ollama."""

    name = "importance"

    def retrieve(self, db, user_id, query_text, memory_types, limit):
        sql = f"""
            SELECT id, user_id, memory_type, content, importance_score, confidence_score,
                   source, source_message_id, status, last_used_at, created_at, updated_at,
                   metadata_json, embedding_status, embedding_updated_at
            FROM memory_items
            WHERE user_id = :uid AND status = 'active'
              {'AND memory_type = ANY(:mtypes)' if memory_types else ''}
            ORDER BY importance_score DESC, created_at DESC
            LIMIT :lim
        """
        params = {"uid": user_id, "lim": limit}
        if memory_types:
            params["mtypes"] = memory_types
        rows = db.execute(text(sql), params).mappings().all()
        return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Hybrid: weighted blend of vector similarity + importance (production default)
# ---------------------------------------------------------------------------

class HybridRetriever(MemoryRetriever):
    """v0.6 * (1 - cos_dist) + v0.4 * (importance/10). The shipped default.

    Pass vector_weight / importance_weight to make a tuned instance — useful
    for the vw/iw sweep runner. If weights are omitted, falls back to the
    settings.MEMORY_VECTOR_WEIGHT / MEMORY_IMPORTANCE_WEIGHT env defaults.

    The `name` is computed from the weights so sweep instances can be told
    apart in the report (e.g., "hybrid_0.8_0.2").
    """

    def __init__(self, vector_weight: float = None, importance_weight: float = None):
        self.vw = vector_weight if vector_weight is not None else settings.MEMORY_VECTOR_WEIGHT
        self.iw = importance_weight if importance_weight is not None else settings.MEMORY_IMPORTANCE_WEIGHT
        # Per-instance name: makes the sweep runner's per-instance columns distinguishable.
        self.name = f"hybrid_{self.vw:.2f}_{self.iw:.2f}"

    def retrieve(self, db, user_id, query_text, memory_types, limit):
        try:
            vec = embed_text_sync(query_text)
            vec_str = vec_literal(vec)
            score_expr = (
                f"({self.vw} * (1 - COALESCE(embedding <=> CAST(:qvec AS vector), 1.0)))"
                f" + ({self.iw} * (importance_score::float / 10.0))"
            )
            sql = f"""
                SELECT id, user_id, memory_type, content, importance_score, confidence_score,
                       source, source_message_id, status, last_used_at, created_at, updated_at,
                       metadata_json, embedding_status, embedding_updated_at,
                       {score_expr} AS score,
                       COALESCE(1 - (embedding <=> CAST(:qvec AS vector)), 0.0) AS similarity
                FROM memory_items
                WHERE user_id = :uid AND status = 'active'
                  {'AND memory_type = ANY(:mtypes)' if memory_types else ''}
                ORDER BY score DESC, importance_score DESC, created_at DESC
                LIMIT :lim
            """
            params = {"uid": user_id, "qvec": vec_str, "lim": limit}
            if memory_types:
                params["mtypes"] = memory_types
            rows = db.execute(text(sql), params).mappings().all()
            return [_row_to_dict(r) for r in rows]
        except Exception as e:
            logger.warning("hybrid retriever failed: %s", e)
            return []


# ---------------------------------------------------------------------------
# Full-text: pg_trgm / tsvector + ts_rank
# Requires migration 008 (content_zh + content_tsv + GIN index).
# ---------------------------------------------------------------------------

class FullTextRetriever(MemoryRetriever):
    """Recall ranked by ts_rank on content_tsv. Chinese via jieba (Python side).

    Design notes — Chinese full-text is hard:

    1. We tokenize the query in Python with jieba so the query lexemes
       match what the trigger put in content_tsv ('simple' tsvector doesn't
       segment CJK on its own).
    2. We use OR (`|`) not AND (`&`) because most queries are paraphrases,
       not literal keyword matches (e.g. "刚喝了奶茶，胃不舒服" / "乳糖不耐受"
       share zero jieba tokens — AND would always miss).
    3. We deliberately drop the `@@` hard filter. ts_rank returns ~0 for
       non-matches, so they sort to the bottom and importance_score breaks
       ties. Result: full-text becomes a soft relevance signal that nudges
       matching memories up the ranking, not a gate that hides them.
    """

    name = "fulltext"

    def retrieve(self, db, user_id, query_text, memory_types, limit):
        try:
            from app.tools.memory_tools import tokenize_zh
            tokens = [t for t in tokenize_zh(query_text).split() if t]
            if not tokens:
                return []
            # Escape single quotes inside tokens (defensive — jieba shouldn't emit them).
            tsquery_expr = " | ".join(
                f"'{t.replace(chr(39), chr(39)+chr(39))}'" for t in tokens
            )

            sql = f"""
                SELECT id, user_id, memory_type, content, importance_score, confidence_score,
                       source, source_message_id, status, last_used_at, created_at, updated_at,
                       metadata_json, embedding_status, embedding_updated_at,
                       ts_rank(content_tsv, to_tsquery('simple', :qts)) AS similarity
                FROM memory_items
                WHERE user_id = :uid AND status = 'active'
                  {'AND memory_type = ANY(:mtypes)' if memory_types else ''}
                ORDER BY similarity DESC, importance_score DESC, created_at DESC
                LIMIT :lim
            """
            params = {"uid": user_id, "qts": tsquery_expr, "lim": limit}
            if memory_types:
                params["mtypes"] = memory_types
            rows = db.execute(text(sql), params).mappings().all()
            return [_row_to_dict(r) for r in rows]
        except Exception as e:
            logger.warning("fulltext retriever failed: %s", e)
            return []


# ---------------------------------------------------------------------------
# RRF (Reciprocal Rank Fusion): vector + fulltext rank-based blend
# ---------------------------------------------------------------------------

class RRFRetriever(MemoryRetriever):
    """Reciprocal Rank Fusion over vector + fulltext.

    Why these two bases (and not importance / hybrid)?
    - vector:   query-aware semantic similarity (embedding cos distance)
    - fulltext: query-aware lexical overlap (jieba + tsvector + ts_rank)
    Both are query-dependent relevance signals; RRF fuses them RANK-BASED so
    cosine distances and ts_ranks (totally different scales) don't need
    normalization. That's the practical benefit over score blending.

    importance is excluded because it's a static per-memory field — same
    ranking for every query, so RRF-ing it would degenerate to a weighted
    hybrid. We already have HybridRetriever for that.

    k=60 is the standard from Cormack et al. 2009 ("Reciprocal Rank Fusion
    outperforms Condorcet and individual Rank Learning Methods"). Smaller k
    weights top ranks more; larger k spreads credit more evenly.
    """

    name = "rrf"

    def __init__(self, k: int = 60, fetch_factor: int = 2,
                 base_retrievers: list = None):
        # Reuse the singleton base instances so RRF stays in sync with eval
        # runs of vector/fulltext alone.
        from app.tools.retrievers import VectorRetriever, FullTextRetriever  # noqa: F401
        self.k = k
        self.fetch_factor = fetch_factor
        if base_retrievers is not None:
            self.base = base_retrievers
        else:
            self.base = [VectorRetriever(), FullTextRetriever()]

    def retrieve(self, db, user_id, query_text, memory_types, limit):
        fetch_n = limit * self.fetch_factor
        rrf_scores: Dict[int, float] = {}
        rows_by_id: Dict[int, Dict[str, Any]] = {}

        for retriever in self.base:
            try:
                rows = retriever.retrieve(db, user_id, query_text, memory_types, fetch_n)
            except Exception as e:
                logger.warning("RRF base %s failed: %s", retriever.name, e)
                continue
            for rank, row in enumerate(rows, start=1):
                rid = row["id"]
                rrf_scores[rid] = rrf_scores.get(rid, 0.0) + 1.0 / (self.k + rank)
                if rid not in rows_by_id:
                    rows_by_id[rid] = dict(row)

        ranked_ids = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)[:limit]
        out = []
        for rid in ranked_ids:
            row = rows_by_id[rid]
            row["rrf_score"] = rrf_scores[rid]
            out.append(row)
        return out


REGISTRY = {
    r.name: r for r in [
        VectorRetriever(),
        ImportanceRetriever(),
        HybridRetriever(),
        FullTextRetriever(),
        RRFRetriever(),
    ]
}

# Alias so `runner --retrievers hybrid` still works after we made HybridRetriever's
# name per-instance. New callers should reference the explicit `hybrid_<vw>_<iw>` form.
REGISTRY["hybrid"] = REGISTRY[f"hybrid_{settings.MEMORY_VECTOR_WEIGHT:.2f}_{settings.MEMORY_IMPORTANCE_WEIGHT:.2f}"]


def make_hybrid_sweep(weights: list = None) -> list:
    """Build extra HybridRetriever instances for vw/iw sweep runs.

    `weights` is a list of (vw, iw) tuples. None uses the standard sweep grid.
    Returns a list of (name, instance) pairs, excluding the default weights
    (which are already in REGISTRY).
    """
    if weights is None:
        weights = [
            (1.0, 0.0),
            (0.8, 0.2),
            (0.6, 0.4),  # the production default
            (0.4, 0.6),
            (0.2, 0.8),
            (0.0, 1.0),
        ]
    out = []
    default_vw = round(settings.MEMORY_VECTOR_WEIGHT, 2)
    default_iw = round(settings.MEMORY_IMPORTANCE_WEIGHT, 2)
    for vw, iw in weights:
        if round(vw, 2) == default_vw and round(iw, 2) == default_iw:
            continue  # already in REGISTRY as "hybrid"
        r = HybridRetriever(vector_weight=vw, importance_weight=iw)
        out.append((r.name, r))
    return out
