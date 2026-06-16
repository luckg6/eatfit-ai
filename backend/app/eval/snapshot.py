"""
Snapshot/restore of last_used_at for the memory-recall eval.

MemoryTools._hybrid_search bulk-updates last_used_at = NOW() for every
memory it surfaces. To keep eval runs side-effect free, we wrap each
case with a snapshot (taken right before recall) and a restore (taken
right after metrics are computed).

The DB-level BEFORE UPDATE trigger memory_items_touch_updated_at will
auto-bump updated_at when we write last_used_at — that's fine, updated_at
is supposed to track the last touch; the metric we care about preserving
is the last_used_at timestamp itself.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session


def snapshot_last_used(db: Session, user_id: int) -> Dict[int, object]:
    """Return {memory_id: last_used_at_or_None} for every memory of the user."""
    rows = db.execute(
        text("SELECT id, last_used_at FROM memory_items WHERE user_id = :uid"),
        {"uid": user_id},
    ).all()
    return {r[0]: r[1] for r in rows}


def restore_last_used(
    db: Session,
    snapshot: Dict[int, object],
) -> None:
    """Restore the snapshot. None values translate to NULL (never used)."""
    for mem_id, ts in snapshot.items():
        db.execute(
            text("UPDATE memory_items SET last_used_at = :ts WHERE id = :id"),
            {"ts": ts, "id": mem_id},
        )
    db.commit()
