"""
Embedding service backed by a local Ollama instance.

Default model: qwen3-embedding:0.6b (1024-dim, Q8_0 quant).
Calls POST /api/embeddings. Falls back to a zero-vector on hard failure
(so callers can mark embedding_status='failed' and retry later).
"""
import logging
from typing import List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_async_client: Optional[httpx.AsyncClient] = None


def get_async_client() -> httpx.AsyncClient:
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
    return _async_client


def _format_vec(v: List[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


async def embed_text(text: str) -> List[float]:
    """Async: call ollama /api/embeddings and return a 1024-dim vector."""
    text = (text or "").strip()
    if not text:
        return [0.0] * settings.EMBEDDING_DIM

    client = get_async_client()
    try:
        resp = await client.post(
            "/api/embeddings",
            json={"model": settings.EMBEDDING_MODEL, "prompt": text},
        )
        resp.raise_for_status()
        vec = resp.json().get("embedding", [])
    except Exception as e:
        logger.error("Ollama embed failed: %s", e)
        return [0.0] * settings.EMBEDDING_DIM

    if len(vec) != settings.EMBEDDING_DIM:
        logger.warning(
            "Embedding dim mismatch: got %d, expected %d. Padding/truncating.",
            len(vec), settings.EMBEDDING_DIM,
        )
        vec = (vec + [0.0] * settings.EMBEDDING_DIM)[: settings.EMBEDDING_DIM]
    return vec


def embed_text_sync(text: str) -> List[float]:
    """Sync: same as embed_text, for use in scripts / sync contexts."""
    text = (text or "").strip()
    if not text:
        return [0.0] * settings.EMBEDDING_DIM
    try:
        with httpx.Client(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=httpx.Timeout(60.0, connect=10.0),
        ) as client:
            resp = client.post(
                "/api/embeddings",
                json={"model": settings.EMBEDDING_MODEL, "prompt": text},
            )
            resp.raise_for_status()
            vec = resp.json().get("embedding", [])
    except Exception as e:
        logger.error("Ollama embed failed: %s", e)
        return [0.0] * settings.EMBEDDING_DIM
    if len(vec) != settings.EMBEDDING_DIM:
        vec = (vec + [0.0] * settings.EMBEDDING_DIM)[: settings.EMBEDDING_DIM]
    return vec


def vec_literal(v: List[float]) -> str:
    """Build a pgvector literal '[x,y,z,...]' for raw SQL."""
    return _format_vec(v)
