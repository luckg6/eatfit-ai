"""
LLM-as-judge for memory recall evaluation.

For each (query, retrieved_memory) pair, ask a separate LLM to judge
semantic relevance. This catches matches that exact-id ground truth
misses (e.g., the retriever surfaces id=7 "海鲜过敏" for a query about
"花生过敏" — irrelevant by id but the same category, which id-based
recall counts as 0).

Behavior:
  - LLM_API_KEY set: calls RealLLMService and parses the JSON verdict.
  - LLM_API_KEY empty: skips the judge. The runner marks the metric as
    None so the aggregate table shows `--` instead of misleading numbers.

The judge prompt is intentionally short and the verdict is a hard 0/1.
We don't ask for a 1-5 score — those are noisy, hard to align across
runs, and the binary call is enough to add the missing signal.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.services.llm_service import get_llm_service

logger = logging.getLogger("eatfit.eval.judge")


# Bound concurrent LLM judge requests to avoid 429 on free-tier endpoints.
# Tune via env if needed.
import os
JUDGE_CONCURRENCY = int(os.environ.get("EVAL_JUDGE_CONCURRENCY", "4"))


JUDGE_SYSTEM = """你是记忆召回评估助手。
判断给定的 memory 是否与用户 query 语义相关（不是字面匹配）。
如果 memory 含有对回答 query 有用的信息（即使措辞不同），判 1；否则 0。
仅返回 JSON，格式：{"relevant": 0|1, "reason": "不超过20字的理由"}"""


def judge_user_prompt(query: str, memory: Dict[str, Any]) -> str:
    return (
        f"用户 query: {query}\n\n"
        f"召回的 memory:\n"
        f"  id={memory.get('id')}\n"
        f"  type={memory.get('memory_type')}\n"
        f"  importance={memory.get('importance_score')}\n"
        f"  content={memory.get('content')}\n\n"
        f"请判断该 memory 是否与 query 语义相关。"
    )


@dataclass
class JudgeVerdict:
    relevant: int  # 0 or 1
    reason: str
    skipped: bool = False  # True when LLM_API_KEY was empty


def is_judge_enabled() -> bool:
    return bool(settings.LLM_API_KEY)


async def judge_one(query: str, memory: Dict[str, Any]) -> JudgeVerdict:
    """Judge a single (query, memory) pair. Async — call via gather for batches."""
    if not is_judge_enabled():
        return JudgeVerdict(relevant=0, reason="mock-mode: judge skipped", skipped=True)

    llm = get_llm_service()
    prompt = judge_user_prompt(query, memory)
    try:
        raw = await llm.generate(JUDGE_SYSTEM, prompt)
        parsed = json.loads(raw)
        return JudgeVerdict(
            relevant=int(parsed.get("relevant", 0)),
            reason=str(parsed.get("reason", ""))[:80],
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        logger.warning("judge parse failed: %s | raw=%r", e, (raw or "")[:200])
        return JudgeVerdict(relevant=0, reason=f"parse_error: {e}", skipped=False)


async def judge_batch(query: str, memories: List[Dict[str, Any]]) -> List[JudgeVerdict]:
    """Judge a batch with bounded concurrency.

    Free-tier LLM endpoints commonly 429 when you fire 30 calls in parallel
    (which is what `asyncio.gather` would do for a top-30 retrieval). We
    cap at JUDGE_CONCURRENCY in-flight requests.
    """
    if not is_judge_enabled():
        return [JudgeVerdict(relevant=0, reason="mock-mode: judge skipped", skipped=True) for _ in memories]

    sem = asyncio.Semaphore(JUDGE_CONCURRENCY)

    async def _bounded(m: Dict[str, Any]) -> JudgeVerdict:
        async with sem:
            return await judge_one(query, m)

    return await asyncio.gather(*[_bounded(m) for m in memories])
