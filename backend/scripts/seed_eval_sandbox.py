"""
Seed a sandbox user with broad memory coverage for eval.

Creates user `eval_sandbox_<timestamp>` and seeds 10 preference + 8
allergy_intolerance memories. Embeddings are generated via Ollama
(synchronous — needs ollama running). Idempotent: drops any prior
eval_sandbox_* users before recreating.

The seed content is intentionally **literal and unambiguous** so that
LLM-generated eval cases can match reliably and so the retriever's
semantic match is unambiguous too. Avoid paraphrases in the seeds —
those should come from generated queries.

Usage:
    cd backend
    PYTHONPATH=. python scripts/seed_eval_sandbox.py
    PYTHONPATH=. python scripts/seed_eval_sandbox.py --keep-existing   # don't reset
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from typing import List

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import User
from app.tools.memory_tools import MemoryTools

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("eatfit.seed_eval")


# Seed content — (memory_type, content, importance_score)
# Designed to be **literal and unambiguous** so:
#   - LLM-generated queries have unambiguous ground truth
#   - The retriever's vector match is well-defined (no paraphrase inside content)
SEED_MEMORIES: List[tuple] = [
    # --- preference (10) ---
    ("preference", "不吃香菜", 8),
    ("preference", "不吃苦瓜", 7),
    ("preference", "不吃肥肠", 7),
    ("preference", "不吃动物内脏", 6),
    ("preference", "不吃辣", 7),
    ("preference", "不喝含糖饮料", 6),
    ("preference", "饮食偏好清淡口味", 7),
    ("preference", "健身增肌期，需要高蛋白", 8),
    ("preference", "预算每餐 30 元以内", 5),
    ("preference", "晚上 8 点后不吃主食", 6),
    # --- allergy_intolerance (8) ---
    ("allergy_intolerance", "乳糖不耐受", 9),
    ("allergy_intolerance", "海鲜过敏", 9),
    ("allergy_intolerance", "花生过敏", 9),
    ("allergy_intolerance", "鸡蛋过敏", 8),
    ("allergy_intolerance", "麸质过敏", 7),
    ("allergy_intolerance", "芒果过敏", 7),
    ("allergy_intolerance", "坚果过敏", 9),
    ("allergy_intolerance", "酒精过敏", 8),
]


def _reset_sandbox_users(db) -> None:
    """Delete any prior eval_sandbox_* users (and cascade memories)."""
    rows = db.execute(
        text("SELECT id, username FROM users WHERE username LIKE 'eval_sandbox_%'")
    ).mappings().all()
    for r in rows:
        logger.info("Resetting prior sandbox user %s (id=%s)", r["username"], r["id"])
        db.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": r["id"]})
    db.commit()


def _create_user(db, username: str) -> User:
    """Create a fresh user with a known bcrypt-hashed password."""
    from passlib.hash import bcrypt
    user = User(
        username=username,
        email=f"{username}@eatfit-test.local",
        password_hash=bcrypt.hash("eval-sandbox-no-real-password"),
        auto_memory_enabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed eval sandbox user")
    parser.add_argument("--keep-existing", action="store_true",
                        help="Skip the reset step (only add to an existing sandbox)")
    parser.add_argument("--no-embed", action="store_true",
                        help="Skip Ollama embedding generation (faster, but content_tsv is fine; "
                             "embedding_status will be 'failed' and retrievers that need vectors will be empty)")
    args = parser.parse_args()

    engine = create_engine(settings.DATABASE_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    username = f"eval_sandbox_{int(time.time())}"
    user_id_holder = {"id": None}
    seeded_count = {"n": 0}
    with SessionLocal() as db:
        if not args.keep_existing:
            _reset_sandbox_users(db)
        user = _create_user(db, username)
        user_id_holder["id"] = user.id
        logger.info("Created sandbox user: id=%s username=%s", user.id, username)

        mem_tools = MemoryTools(db)
        created_ids = []
        for mem_type, content, importance in SEED_MEMORIES:
            try:
                if args.no_embed:
                    # Direct insert without going through MemoryTools.create_memory
                    # (which would try to embed via Ollama).
                    from app.models.memory import MemoryItem
                    mem = MemoryItem(
                        user_id=user.id, memory_type=mem_type, content=content,
                        importance_score=importance, source="manual", status="active",
                        embedding_status="failed",  # will be backfilled later if desired
                    )
                    from app.tools.memory_tools import tokenize_zh
                    mem.content_zh = tokenize_zh(content)
                    db.add(mem)
                    db.commit()
                    db.refresh(mem)
                    created_ids.append(mem.id)
                else:
                    mem = mem_tools.create_memory(
                        user_id=user.id, memory_type=mem_type, content=content,
                        importance_score=importance, source="manual",
                    )
                    created_ids.append(mem.id)
            except Exception as e:
                logger.error("Failed to seed '%s': %s", content, e)
                db.rollback()
        seeded_count["n"] = len(created_ids)

    print("\n" + "=" * 60)
    print(f"  Sandbox user created: {username} (id={user_id_holder['id']})")
    print(f"  Seeded {seeded_count['n']} memories")
    print(f"  Use --user-id {user_id_holder['id']} when running eval:")
    print(f"     python -m app.eval.runner --user-id {user_id_holder['id']}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
