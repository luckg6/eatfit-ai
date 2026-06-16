"""
Backfill content_zh for existing memory_items.

Run once after migration 008 to populate the jieba-segmented text column.
The trigger (trg_memory_items_refresh_tsv) reads content_zh to rebuild
content_tsv, so this single column backfill also refreshes the tsvector.

Idempotent: re-running is safe; every row is rewritten with fresh tokens.

Usage:
    cd backend
    PYTHONPATH=. python sql/pg/backfill_content_zh.py
"""
from __future__ import annotations

import logging
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.tools.memory_tools import tokenize_zh

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("eatfit.backfill_zh")


def main() -> int:
    engine = create_engine(settings.DATABASE_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionLocal() as db:
        rows = db.execute(
            text("SELECT id, content FROM memory_items ORDER BY id")
        ).mappings().all()

        if not rows:
            logger.info("No rows to backfill.")
            return 0

        logger.info("Backfilling content_zh for %d memory rows...", len(rows))
        for r in rows:
            zh = tokenize_zh(r["content"])
            db.execute(
                text("UPDATE memory_items SET content_zh = :zh WHERE id = :id"),
                {"zh": zh, "id": r["id"]},
            )
        db.commit()

        # Verify a sample
        samples = db.execute(
            text("""
                SELECT id, content, content_zh, length(content_tsv::text) AS tsv_len
                FROM memory_items
                WHERE user_id = 1
                ORDER BY id
                LIMIT 5
            """)
        ).mappings().all()
        print("\nSample after backfill:")
        print(f"  {'id':>3}  {'content':<20}  {'content_zh':<40}  tsv_len")
        for s in samples:
            print(f"  {s['id']:>3}  {(s['content'] or '')[:18]:<20}  "
                  f"{(s['content_zh'] or '')[:38]:<40}  {s['tsv_len']}")

    logger.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
