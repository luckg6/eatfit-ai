"""
Backfill embeddings for existing memory_items rows in PG eatfit_ai.

Reads all rows where embedding IS NULL or embedding_status != 'ready',
calls ollama /api/embeddings (qwen3-embedding:0.6b, 1024-dim) for each,
and writes the vector back.
"""
import sys
import time
import psycopg2
import httpx

PG = dict(host='localhost', port=5432, user='postgres', password='root', dbname='eatfit_ai')
OLLAMA = "http://localhost:11434"
MODEL = "qwen3-embedding:0.6b"
DIM = 1024


def embed_sync(client: httpx.Client, text: str) -> list[float]:
    text = (text or "").strip() or " "
    r = client.post("/api/embeddings", json={"model": MODEL, "prompt": text}, timeout=60.0)
    r.raise_for_status()
    v = r.json().get("embedding", [])
    if len(v) != DIM:
        v = (v + [0.0] * DIM)[:DIM]
    return v


def vec_literal(v: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def main():
    conn = psycopg2.connect(**PG)
    conn.autocommit = False
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, content FROM memory_items
            WHERE embedding IS NULL OR embedding_status != 'ready'
            ORDER BY id
        """)
        rows = cur.fetchall()
    print(f"待回填：{len(rows)} 条")

    if not rows:
        conn.close()
        return

    with httpx.Client(base_url=OLLAMA, timeout=httpx.Timeout(60.0, connect=10.0)) as client:
        t0 = time.time()
        for mid, content in rows:
            try:
                vec = embed_sync(client, content)
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE memory_items
                        SET embedding = CAST(%s AS vector),
                            embedding_status = 'ready',
                            embedding_updated_at = NOW()
                        WHERE id = %s
                    """, (vec_literal(vec), mid))
                conn.commit()
                print(f"  id={mid:>4d}  dim={len(vec):>4d}  preview={content[:30]}")
            except Exception as e:
                with conn.cursor() as cur:
                    cur.execute("UPDATE memory_items SET embedding_status='failed' WHERE id=%s", (mid,))
                conn.commit()
                print(f"  id={mid:>4d}  FAILED: {e}")
        print(f"--- 全部完成，耗时 {time.time()-t0:.1f}s ---")

    # 验证
    with conn.cursor() as cur:
        cur.execute("SELECT id, memory_type, content, embedding_status, vector_dims(embedding) FROM memory_items ORDER BY id")
        print("\n=== 回填后状态 ===")
        for r in cur.fetchall():
            print(f"  id={r[0]:>3d}  {r[3]:>7s}  dim={r[4]}  {r[2][:25]}")
    conn.close()


if __name__ == "__main__":
    main()
