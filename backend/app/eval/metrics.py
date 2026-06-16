"""
Metrics for memory-recall evaluation.

All metrics are computed against the top-K retrieved memory IDs returned by
MemoryTools.get_relevant_memories. Each case carries:
  - relevant_memory_ids: list[int]  — exact IDs that should appear in top-K
  - relevant_types:       list[str]  — accepted memory_type values for
                                       type-precision (a coarser signal that
                                       catches "wrong specific ID but right
                                       category")

LLM-as-judge adds a third signal:
  - llm_relevance_rate@K: fraction of top-K that the judge marked relevant
    (semantic precision — catches "right category, wrong specific ID"
    matches that id-based recall scores as 0)

A metric returns None when it cannot be computed (e.g., recall@K with no
relevant ids, or judge disabled in mock mode) so the aggregator can skip
without poisoning averages.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence


def recall_at_k(
    retrieved_ids: Sequence[int],
    relevant_ids: Iterable[int],
    k: int,
) -> Optional[float]:
    """Fraction of relevant_ids appearing in the top-K retrieved list.

    Returns None if relevant_ids is empty (no ground truth → undefined).
    """
    relevant_set = set(relevant_ids)
    if not relevant_set:
        return None
    top_k = list(retrieved_ids[:k])
    if not top_k:
        return 0.0
    hits = sum(1 for rid in top_k if rid in relevant_set)
    return hits / len(relevant_set)


def hit_rate_at_k(
    retrieved_ids: Sequence[int],
    relevant_ids: Iterable[int],
    k: int,
) -> Optional[float]:
    """1 if at least one relevant id appears in top-K, else 0.

    Returns None if relevant_ids is empty.
    """
    relevant_set = set(relevant_ids)
    if not relevant_set:
        return None
    top_k = list(retrieved_ids[:k])
    return 1.0 if any(rid in relevant_set for rid in top_k) else 0.0


def mrr(
    retrieved_ids: Sequence[int],
    relevant_ids: Iterable[int],
) -> float:
    """Mean Reciprocal Rank: 1/rank of the first relevant id, 0 if none.

    Unlike recall/HR, MRR is well-defined even when relevant_ids is empty
    (returns 0.0), so the aggregator can average it across all cases.
    """
    relevant_set = set(relevant_ids)
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in relevant_set:
            return 1.0 / rank
    return 0.0


def type_precision_at_k(
    retrieved_types: Sequence[str],
    relevant_types: Iterable[str],
    k: int,
) -> Optional[float]:
    """Fraction of top-K results whose memory_type is in the relevant set."""
    relevant_set = set(relevant_types)
    if not relevant_set:
        return None
    top_k = list(retrieved_types[:k])
    if not top_k:
        return 0.0
    return sum(1 for t in top_k if t in relevant_set) / len(top_k)


def llm_relevance_rate_at_k(
    verdicts: Sequence,  # sequence of JudgeVerdict (or anything with .relevant)
    k: int,
) -> Optional[float]:
    """Fraction of top-K judged semantically relevant by the LLM judge.

    Returns None if no verdicts (e.g., retrieval returned empty, or judge
    disabled in mock mode).
    """
    if not verdicts:
        return None
    top_k = list(verdicts[:k])
    if not top_k:
        return 0.0
    n_relevant = sum(1 for v in top_k if v.relevant == 1)
    return n_relevant / len(top_k)


def compute_case_metrics(
    retrieved: List[Dict],
    relevant_ids: List[int],
    relevant_types: List[str],
    k_values: Sequence[int] = (3, 5, 10),
    verdicts: Optional[Sequence] = None,
) -> Dict[str, Optional[float]]:
    """Compute the full metric bundle for one case.

    `verdicts` is an optional sequence of JudgeVerdict objects, one per
    retrieved memory. If provided, llm_relevance_rate@K is added.
    """
    retrieved_ids = [m["id"] for m in retrieved]
    retrieved_types = [m["memory_type"] for m in retrieved]

    out: Dict[str, Optional[float]] = {}
    for k in k_values:
        out[f"recall@{k}"] = recall_at_k(retrieved_ids, relevant_ids, k)
        out[f"hit@{k}"] = hit_rate_at_k(retrieved_ids, relevant_ids, k)
        out[f"type_precision@{k}"] = type_precision_at_k(retrieved_types, relevant_types, k)
        if verdicts is not None:
            out[f"llm_relevance_rate@{k}"] = llm_relevance_rate_at_k(verdicts, k)
    out["mrr"] = mrr(retrieved_ids, relevant_ids)
    return out


def aggregate(per_case: List[Dict[str, Optional[float]]]) -> Dict[str, float]:
    """Average each metric across cases. Skip None entries (undefined cases)."""
    keys = set()
    for row in per_case:
        keys.update(row.keys())
    agg: Dict[str, float] = {}
    for k in sorted(keys):
        values = [row[k] for row in per_case if row.get(k) is not None]
        agg[k] = sum(values) / len(values) if values else 0.0
    agg["n_cases"] = len(per_case)
    return agg
