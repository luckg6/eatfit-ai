"""
Generate candidate eval cases from a sandbox user's memories.

For each memory in the user's memory_items table, the LLM generates
3 positive candidate queries (queries that should recall this memory)
and 2 negative candidate queries (queries that look topically related
but should NOT recall it). Output is printed to stdout as YAML-appendable
blocks — **the script never modifies cases/*.yaml automatically**.

The human reviewer reads the output, picks the good ones, and pastes
them into memory_recall.yaml. This is the **review gate** that prevents
LLM-generated junk cases from polluting the eval set.

Usage:
    cd backend
    PYTHONPATH=. python scripts/generate_eval_cases.py --user-id 10
    PYTHONPATH=. python scripts/generate_eval_cases.py --user-id 10 --only-types preference
    PYTHONPATH=. python scripts/generate_eval_cases.py --user-id 10 --mem-ids 42,46
    PYTHONPATH=. python scripts/generate_eval_cases.py --user-id 10 --fallback   # no LLM, use templates

Without LLM_API_KEY (or with --fallback), uses deterministic templates
instead of LLM-generated queries. Useful for fast iteration but lower
quality.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.llm_service import get_llm_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("eatfit.generate_eval_cases")


# ---------------------------------------------------------------------------
# LLM prompts
# ---------------------------------------------------------------------------

POSITIVE_GEN_SYSTEM = """你是评测集构造助手。根据给定的一条用户记忆，生成 3 条**用户原话风格**的查询语句。

要求：
1. 三条查询**角度不同**：一条直接表达、一条 paraphrase（描述症状或场景）、一条是具体场景的提问
2. 必须是真实用户会说的话，不能有"请帮我..."这种 AI 套话
3. 每条独立成行，**只输出 3 条 query**，每行一条，不要编号、引号或其他任何字符"""

POSITIVE_GEN_USER_TEMPLATE = """用户记忆 (id={mem_id}, type={mem_type}, importance={importance}, content={content})：

请生成 3 条用户原话风格的 query，每条独立一行。
- 第 1 条直接表达，例如"我对 X 过敏"或"我不吃 X"
- 第 2 条 paraphrase，描述症状或具体场景
- 第 3 条提问式，例如"附近有什么能吃的"或"中午推荐什么"
"""


NEGATIVE_GEN_SYSTEM = """你是评测集构造助手。根据给定的一条用户记忆，生成 2 条**看起来相关但实际不该召回该记忆**的查询。

要求：
1. 两条 query 必须是**和原记忆同一类别（饮食相关）但措辞/语义不会命中**
2. 例如：记忆是"不吃香菜"，负例可以是"我很喜欢吃辣"或"今天天气不错"
3. 不要输出空 query 或跟原记忆完全一样的内容
4. 每条独立成行，**只输出 2 条 query**"""

NEGATIVE_GEN_USER_TEMPLATE = """用户记忆 (id={mem_id}, type={mem_type}, content={content})：

请生成 2 条查询，看起来跟这条记忆相关但实际不该召回它。
"""


# ---------------------------------------------------------------------------
# Fallback templates (no LLM available)
# ---------------------------------------------------------------------------

POSITIVE_FALLBACK_BY_TYPE = {
    "preference": [
        "我{neg}{content}",                  # "我不吃香菜"
        "推荐点{topic_hint}，不要{content}",   # "推荐点外卖，不要香菜"
        "中午吃什么好？",                     # generic recommendation
    ],
    "allergy_intolerance": [
        "我{allergy_verb}{content}，能吃什么",
        "刚吃了含{trigger}的东西，不舒服",
        "我{allergy_verb}{content}，附近有什么推荐",
    ],
}

NEGATIVE_FALLBACK = [
    "今天天气怎么样",
    "我最近心情不太好",
]


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------

async def _llm_generate_candidates(system: str, user: str, n_expected: int) -> List[str]:
    if not settings.LLM_API_KEY:
        return []
    llm = get_llm_service()
    try:
        raw = await llm.generate(system, user)
        lines = [l.strip().strip("\"'`").strip() for l in raw.splitlines() if l.strip()]
        # Strip leading numbering like "1. " or "- "
        cleaned = []
        for l in lines:
            if l[:2] in ("1.", "2.", "3.", "4.", "- ") or (len(l) > 2 and l[1:3] == ". "):
                l = l.split(" ", 1)[1] if " " in l else l
            cleaned.append(l)
        return [c for c in cleaned if c][:n_expected]
    except Exception as e:
        logger.warning("LLM generation failed: %s", e)
        return []


def _fallback_positive(mem: Dict[str, Any]) -> List[str]:
    """Deterministic positive templates. Last-resort when no LLM is available."""
    content = mem["content"]
    mem_type = mem["memory_type"]
    if mem_type == "preference":
        if "不吃" in content or "不喝" in content:
            topic_hint = "清淡的"
            return [
                f"我{content}",
                f"推荐点{topic_hint}，不要{content[2:]}",
                "中午吃什么好",
            ]
        if "预算" in content:
            return [
                f"{content}",
                "午饭吃什么好",
                "附近推荐一下",
            ]
        if "晚上" in content or "中午" in content:
            return [
                content,
                "晚上吃什么",
                "有什么推荐",
            ]
        return [content, "中午推荐", "附近有什么"]
    # allergy_intolerance
    return [
        f"我{content}，能吃什么",
        f"刚吃了含{content[1:3]}的东西不舒服",
        f"我{content}，附近有什么推荐",
    ]


def _fallback_negative() -> List[str]:
    return list(NEGATIVE_FALLBACK)


async def generate_for_memory(mem: Dict[str, Any], use_llm: bool) -> Dict[str, List[str]]:
    """Return {'positive': [...], 'negative': [...]} candidates."""
    # Template placeholders use mem_id/mem_type/importance/content; SQL rows give id/type/...
    fmt = {
        "mem_id": mem["id"],
        "mem_type": mem["memory_type"],
        "importance": mem["importance_score"],
        "content": mem["content"],
    }
    out = {"positive": [], "negative": []}
    if use_llm:
        out["positive"] = await _llm_generate_candidates(
            POSITIVE_GEN_SYSTEM,
            POSITIVE_GEN_USER_TEMPLATE.format(**fmt),
            n_expected=3,
        )
        out["negative"] = await _llm_generate_candidates(
            NEGATIVE_GEN_SYSTEM,
            NEGATIVE_GEN_USER_TEMPLATE.format(**fmt),
            n_expected=2,
        )
    if not out["positive"]:
        out["positive"] = _fallback_positive(mem)
    if not out["negative"]:
        out["negative"] = _fallback_negative()
    return out


# ---------------------------------------------------------------------------
# YAML printer (manual review gate)
# ---------------------------------------------------------------------------

def print_yaml_block(mem: Dict[str, Any], candidates: Dict[str, List[str]]) -> None:
    print(f"\n--- memory id={mem['id']} type={mem['memory_type']} imp={mem['importance_score']}: \"{mem['content']}\" ---")
    for kind in ("positive", "negative"):
        for i, q in enumerate(candidates[kind], 1):
            print(f"  # {kind} #{i}")
            print(f"  - case_id: {mem['memory_type']}_{mem['id']}_{kind[0]}{i}")
            print(f"    user_id: {mem['user_id']}")
            print(f"    intent: diet_advice")
            print(f"    query: \"{q}\"")
            if kind == "positive":
                print(f"    relevant_memory_ids: [{mem['id']}]")
                print(f"    relevant_types: [{mem['memory_type']}]")
                print(f"    notes: \"auto-gen: should recall {mem['content']}\"")
            else:
                # Negative: ground truth is "don't recall this"
                print(f"    relevant_memory_ids: []")
                print(f"    relevant_types: []")
                print(f"    notes: \"auto-gen: should NOT recall {mem['content']}\"")
            print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> int:
    parser = argparse.ArgumentParser(description="Generate eval case candidates")
    parser.add_argument("--user-id", type=int, required=True, help="Sandbox user id")
    parser.add_argument("--only-types", type=str, default=None,
                        help="Comma-separated memory types to process (default: all)")
    parser.add_argument("--mem-ids", type=str, default=None,
                        help="Comma-separated specific memory ids (default: all active)")
    parser.add_argument("--fallback", action="store_true",
                        help="Use deterministic templates instead of LLM")
    parser.add_argument("--output", type=str, default=None,
                        help="Write YAML to this file instead of stdout (still does NOT modify cases/*.yaml)")
    args = parser.parse_args()

    use_llm = bool(settings.LLM_API_KEY) and not args.fallback
    logger.info("LLM generation: %s", "ON" if use_llm else "OFF (fallback templates)")

    engine = create_engine(settings.DATABASE_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionLocal() as db:
        sql = """
            SELECT id, user_id, memory_type, content, importance_score
            FROM memory_items
            WHERE user_id = :uid AND status = 'active'
        """
        params: Dict[str, Any] = {"uid": args.user_id}
        if args.only_types:
            types = [t.strip() for t in args.only_types.split(",")]
            sql += " AND memory_type = ANY(:mtypes)"
            params["mtypes"] = types
        if args.mem_ids:
            ids = [int(i) for i in args.mem_ids.split(",")]
            sql += " AND id = ANY(:ids)"
            params["ids"] = ids
        sql += " ORDER BY memory_type, id"
        rows = db.execute(text(sql), params).mappings().all()

    if not rows:
        logger.error("No memories found for user_id=%s (with given filters)", args.user_id)
        return 1

    logger.info("Generating candidates for %d memories...", len(rows))

    # Build output
    header = (
        "# Auto-generated candidate eval cases\n"
        "# Pipeline: scripts/generate_eval_cases.py\n"
        "# \n"
        "# Review gate: each block below is a CANDIDATE — paste the good ones into\n"
        "# backend/app/eval/cases/memory_recall.yaml under the `cases:` list.\n"
        "# Discard candidates that are:\n"
        "#   - too easy (memory content is literally in the query)\n"
        "#   - too noisy (no reasonable retriever would match)\n"
        "#   - semantically wrong (the candidate doesn't actually mean what notes claim)\n"
        "# \n"
        "# YAML structure reminder:\n"
        "#   - case_id:           unique string\n"
        "#   - user_id:           sandbox user id (passed via --user-id)\n"
        "#   - intent:            diet_advice / meal_log / profile_update / dashboard_query\n"
        "#   - query:             the user message (Chinese natural language)\n"
        "#   - relevant_memory_ids: list[int]  — exact IDs that should appear in top-K\n"
        "#   - relevant_types:    list[str]   — accepted memory_type values\n"
        "#   - notes:             string       — why this case is interesting\n"
        "# \n"
        f"# user_id: {args.user_id}\n"
        f"# generated: {len(rows)} memories × ~5 candidates each\n"
        "\n"
    )

    blocks = [header]
    for mem in rows:
        cands = await generate_for_memory(dict(mem), use_llm=use_llm)
        # Capture the print into the buffer
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_yaml_block(dict(mem), cands)
        blocks.append(buf.getvalue())

    output = "".join(blocks)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        logger.info("Wrote candidates to %s", args.output)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
