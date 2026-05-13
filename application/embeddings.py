"""Embedding provider wrapper.
Currently backed by a local sentence-transformers
model (Snowflake/snowflake-arctic-embed-s, 384 dims).
"""

import hashlib
from functools import lru_cache

from flask import current_app


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(current_app.config["EMBEDDING_MODEL"])


def embed(text: str) -> list[float]:
    vector = _model().encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = _model().encode(
        texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vectors]


def content_hash(title: str, body: str) -> str:
    """Hash used to enable skip re-embed unchanged rows."""
    h = hashlib.sha256()
    content = embedding_input(title, body)
    h.update(content.encode("utf-8"))
    return h.hexdigest()


def embedding_input(title: str, body: str) -> str:
    return f"{title}\n{body}"
