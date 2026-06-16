"""
Memory-recall eval runner — multi-retriever mode.

Loads cases from cases/memory_recall.yaml, runs each through every
registered retriever (vector / importance / hybrid / fulltext),
computes per-case and per-retriever metrics, and prints a comparison
report.

Usage:
    cd backend
    PYTHONPATH=. python -m app.eval.runner
    PYTHONPATH=. python -m app.eval.runner --retrievers vector,hybrid,fulltext
    PYTHONPATH=. python -m app.eval.runner --user-id 1 --k 3,5,10

Per case × retriever we:
  1. Snapshot (memory_id -> last_used_at) for the case's user
  2. Run the retriever
  3. Compute Recall@K / Hit@K / Type-Precision@K / MRR
  4. Restore the snapshot, commit
  5. Move on; DB state is unchanged after the run

If Ollama is down, vector / hybrid return []; importance / fulltext keep working.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.eval.judge import JudgeVerdict, is_judge_enabled, judge_batch
from app.eval.metrics import aggregate, compute_case_metrics
from app.eval.snapshot import restore_last_used, snapshot_last_used
from app.tools.memory_tools import MemoryTools
from app.tools.retrievers import REGISTRY as RETRIEVER_REGISTRY, make_hybrid_sweep

logger = logging.getLogger("eatfit.eval.memory_recall")


# ---------------------------------------------------------------------------
# Case loading
# ---------------------------------------------------------------------------

DEFAULT_CASES_PATH = Path(__file__).parent / "cases" / "memory_recall.yaml"


def load_cases(path: Path) -> List[Dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    if not cases:
        raise ValueError(f"No cases found in {path}")
    for c in cases:
        for required in ("case_id", "user_id", "intent", "query"):
            if required not in c:
                raise ValueError(f"Case {c.get('case_id', '<no id>')} missing field: {required}")
        c.setdefault("relevant_memory_ids", [])
        c.setdefault("relevant_types", [])
        c.setdefault("notes", "")
    return cases


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def _format_metric(value: Any) -> str:
    if value is None:
        return "  -- "
    return f"{value:.3f}"


def print_case_report(case: Dict[str, Any],
                      per_retriever: Dict[str, Dict[str, Any]],
                      show_judge: bool = False) -> None:
    print(f"\n--- {case['case_id']} ---")
    print(f"  query:    {case['query']}")
    print(f"  intent:   {case['intent']}")
    print(f"  notes:    {case['notes'] or '-'}")
    rel_ids = case.get("relevant_memory_ids") or []
    rel_types = case.get("relevant_types") or []
    empty_marker = "(empty)"
    print(f"  expected: ids={rel_ids or empty_marker}  types={rel_types or empty_marker}")

    for retriever_name, payload in per_retriever.items():
        if payload.get("error"):
            print(f"  [{retriever_name}] ERROR: {payload['error']}")
            continue
        retrieved = payload["retrieved"]
        metrics = payload["metrics"]
        verdicts = payload.get("verdicts") or []
        print(f"  [{retriever_name}] top {len(retrieved)}:")
        for i, r in enumerate(retrieved[:5]):
            sim = r.get("similarity")
            score = r.get("score")
            sim_str = ""
            if sim is not None and not (isinstance(sim, float) and sim != sim):
                sim_str = f" sim={sim:.3f}"
            elif sim is not None:
                sim_str = " sim=NaN"
            score_str = ""
            if score is not None and not (isinstance(score, float) and score != score):
                score_str = f" score={score:.3f}"
            elif score is not None:
                score_str = " score=NaN"
            judge_str = ""
            if show_judge and i < len(verdicts):
                v = verdicts[i]
                tag = "J1" if v.relevant == 1 and not v.skipped else ("J0" if not v.skipped else "J-")
                judge_str = f" {tag}({v.reason[:25]})"
            print(f"      #{r['id']:>3} {r['memory_type']:<20} imp={r['importance_score']:<2}{sim_str}{score_str}{judge_str} | {r['content']}")
        metric_strs = "  ".join(f"{k}={_format_metric(v)}" for k, v in metrics.items())
        print(f"    metrics: {metric_strs}")


def print_aggregate(per_retriever_agg: Dict[str, Dict[str, float]]) -> None:
    print("\n" + "=" * 72)
    print(f"  AGGREGATE  (per retriever)")
    print("=" * 72)

    # Collect all metric keys (preserve insertion order via dict)
    all_keys: List[str] = []
    for agg in per_retriever_agg.values():
        for k in agg.keys():
            if k != "n_cases" and k not in all_keys:
                all_keys.append(k)

    header = "  " + "metric".ljust(22) + "".join(name.ljust(13) for name in per_retriever_agg.keys())
    print(header)
    print("  " + "-" * (22 + 13 * len(per_retriever_agg)))

    n_cases = next(iter(per_retriever_agg.values())).get("n_cases", 0) if per_retriever_agg else 0
    print(f"  {'n_cases':<22}" + f"{n_cases:<13}" * len(per_retriever_agg))

    for k in all_keys:
        row = f"  {k:<22}"
        for name in per_retriever_agg.keys():
            v = per_retriever_agg[name].get(k)
            row += _format_metric(v).ljust(13)
        print(row)


# ---------------------------------------------------------------------------
# Per-case execution (multi-retriever)
# ---------------------------------------------------------------------------

async def run_case(db: Session, case: Dict[str, Any],
                   retrievers: List[str], k_values: List[int],
                   run_judge: bool) -> Dict[str, Any]:
    snap = snapshot_last_used(db, case["user_id"])
    mem_tools = MemoryTools(db)
    per_retriever: Dict[str, Dict[str, Any]] = {}

    for retriever_name in retrievers:
        t0 = time.perf_counter()
        try:
            retrieved = mem_tools.get_relevant_memories(
                user_id=case["user_id"],
                intent=case["intent"],
                limit=max(k_values),
                query_text=case["query"],
                retriever=retriever_name,
            )
        except Exception as e:
            logger.error("[case %s / retriever %s] recall failed: %s",
                         case["case_id"], retriever_name, e, exc_info=True)
            per_retriever[retriever_name] = {"retrieved": [], "metrics": {}, "error": str(e)}
            continue

        # LLM-as-judge (skipped in mock mode)
        if run_judge and retrieved:
            verdicts = await judge_batch(case["query"], retrieved)
        else:
            verdicts = []

        elapsed_ms = (time.perf_counter() - t0) * 1000

        metrics = compute_case_metrics(
            retrieved=retrieved,
            relevant_ids=case["relevant_memory_ids"],
            relevant_types=case["relevant_types"],
            k_values=k_values,
            verdicts=verdicts if run_judge else None,
        )
        per_retriever[retriever_name] = {
            "retrieved": retrieved,
            "verdicts": verdicts,
            "metrics": metrics,
            "elapsed_ms": elapsed_ms,
        }

    restore_last_used(db, snap)
    return {"case_id": case["case_id"], "per_retriever": per_retriever}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_k_values(raw: str) -> List[int]:
    out = []
    for piece in raw.split(","):
        piece = piece.strip()
        if not piece:
            continue
        out.append(int(piece))
    if not out:
        raise ValueError("--k must list at least one K, e.g. --k 3,5,10")
    return out


def parse_retrievers(raw: str) -> List[str]:
    out = []
    for piece in raw.split(","):
        piece = piece.strip()
        if not piece:
            continue
        if piece not in RETRIEVER_REGISTRY:
            raise ValueError(f"Unknown retriever {piece!r}. Available: {list(RETRIEVER_REGISTRY)}")
        out.append(piece)
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser(description="Run memory-recall eval (multi-retriever)")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH,
                        help=f"Path to cases YAML (default: {DEFAULT_CASES_PATH})")
    parser.add_argument("--user-id", type=int, default=None,
                        help="Override all cases' user_id (useful for sandbox users)")
    parser.add_argument("--k", type=parse_k_values, default=[3, 5, 10],
                        help="Comma-separated K values (default: 3,5,10)")
    parser.add_argument("--retrievers", type=parse_retrievers,
                        default=list(RETRIEVER_REGISTRY.keys()),
                        help=f"Comma-separated retriever names (default: all "
                             f"{list(RETRIEVER_REGISTRY.keys())})")
    parser.add_argument("--vw-iw-sweep", action="store_true",
                        help="Replace 'hybrid' with a 6-point vw/iw sweep grid "
                             "(1.0/0.0, 0.8/0.2, 0.6/0.4, 0.4/0.6, 0.2/0.8, 0.0/1.0). "
                             "Useful for picking the best weight combo from data.")
    parser.add_argument("--no-judge", action="store_true",
                        help="Skip LLM-as-judge even if LLM_API_KEY is set")
    parser.add_argument("--show-judge", action="store_true",
                        help="Print per-memory judge verdicts inline (J1/J0/J-)")
    parser.add_argument("--json", action="store_true",
                        help="Also dump the full result as JSON to stdout at the end")
    parser.add_argument("--log-level", default="WARNING",
                        help="Logging level for app.* (default: WARNING — keeps the report clean)")
    args = parser.parse_args()

    run_judge = is_judge_enabled() and not args.no_judge
    if run_judge:
        logger.warning("LLM judge enabled (LLM_API_KEY set); this will call the LLM API for every retrieved memory.")
    else:
        logger.warning("LLM judge disabled (no LLM_API_KEY or --no-judge); llm_relevance_rate@K will be skipped.")

    logging.getLogger("eatfit").setLevel(getattr(logging, args.log_level.upper(), logging.WARNING))
    logging.getLogger("app").setLevel(getattr(logging, args.log_level.upper(), logging.WARNING))
    logging.getLogger("httpx").setLevel(logging.WARNING)

    cases = load_cases(args.cases)
    if args.user_id is not None:
        for c in cases:
            c["user_id"] = args.user_id

    # Build the retriever list for this run. In sweep mode, replace `hybrid`
    # with the full grid; vector/importance/fulltext remain unchanged so we
    # can compare "pure" signals against each blend.
    if args.vw_iw_sweep:
        sweep_retrievers = [r for _, r in make_hybrid_sweep()]
        # drop the default 'hybrid' from args.retrievers, then add the grid
        active_retrievers = [r for r in args.retrievers if r != "hybrid"]
        for r in sweep_retrievers:
            active_retrievers.append(r.name)
        logger.warning(f"vw/iw sweep enabled: running hybrid at {len(sweep_retrievers)} weight combos")
        # Validate they exist in our merged view (memory_tools expects names)
        for name in active_retrievers:
            if name not in RETRIEVER_REGISTRY and name not in {r.name for r in sweep_retrievers}:
                logger.error(f"Unknown retriever in sweep: {name}")
        # The run_case function looks up by name via REGISTRY, so we need to
        # add the sweep instances to a temporary expanded registry.
        from app.tools import retrievers as _r
        expanded = dict(_r.REGISTRY)
        for r in sweep_retrievers:
            expanded[r.name] = r
        # Monkey-patch the registry inside memory_tools.get_relevant_memories
        # via this simple substitution: temporarily expose the same name.
        # Easiest: pass through a custom retriever map. The run_case function
        # uses MemoryTools.get_relevant_memories(retriever=name) which calls
        # RETRIEVER_REGISTRY.get(name). We can't easily inject; simplest fix:
        # rebuild REGISTRY entries for the sweep names by mapping to instances.
        # Since REGISTRY is shared, we mutate it in place — but we restore at end.
        original = dict(_r.REGISTRY)
        _r.REGISTRY.update(expanded)
    else:
        active_retrievers = args.retrievers
        original = None

    engine = create_engine(settings.DATABASE_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    full_results: List[Dict[str, Any]] = []
    try:
        with SessionLocal() as db:
            for case in cases:
                result = asyncio.run(run_case(db, case, active_retrievers, args.k, run_judge))
                full_results.append(result)
                print_case_report(case, result["per_retriever"], show_judge=args.show_judge)
    finally:
        if original is not None:
            from app.tools import retrievers as _r
            _r.REGISTRY.clear()
            _r.REGISTRY.update(original)

    # Aggregate per-retriever
    per_retriever_agg: Dict[str, Dict[str, float]] = {}
    for retriever_name in active_retrievers:
        per_case_metrics = []
        for r in full_results:
            pr = r["per_retriever"].get(retriever_name, {})
            per_case_metrics.append(pr.get("metrics", {}))
        per_retriever_agg[retriever_name] = aggregate(per_case_metrics)

    print_aggregate(per_retriever_agg)

    if args.json:
        print("\n----- JSON -----")
        out = {
            "retrievers": args.retrievers,
            "k_values": args.k,
            "aggregate": per_retriever_agg,
            "cases": [
                {
                    "case_id": r["case_id"],
                    "per_retriever": {
                        name: {
                            "metrics": pr.get("metrics", {}),
                            "elapsed_ms": pr.get("elapsed_ms"),
                            "retrieved_ids": [m["id"] for m in pr.get("retrieved", [])],
                            "error": pr.get("error"),
                        }
                        for name, pr in r["per_retriever"].items()
                    },
                }
                for r in full_results
            ],
        }
        if run_judge:
            out["judge_verdicts"] = [
                {
                    "case_id": r["case_id"],
                    "per_retriever": {
                        name: [
                            {"memory_id": pr.get("retrieved", [{}])[i].get("id") if i < len(pr.get("retrieved", [])) else None,
                             "relevant": v.relevant, "reason": v.reason, "skipped": v.skipped}
                            for i, v in enumerate(pr.get("verdicts", []))
                        ]
                        for name, pr in r["per_retriever"].items()
                    },
                }
                for r in full_results
            ]
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))

    return 0


if __name__ == "__main__":
    sys.exit(main())
