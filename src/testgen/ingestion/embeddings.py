"""Text embeddings computed locally on the CPU: free, private, and no API quota."""

from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from fastembed import TextEmbedding

from testgen.config import get_settings


class Embedder(Protocol):
    """Anything that turns text into vectors. Tests pass a fake; the app uses FastEmbedEmbedder."""

    def embed_documents(self, texts: list[str]) -> list[Sequence[float]]: ...

    def embed_query(self, text: str) -> Sequence[float]: ...


class FastEmbedEmbedder:
    """ONNX-based embeddings: no PyTorch, a ~70 MB model, fast enough on a laptop CPU."""

    def __init__(self, model_name: str, cache_dir: Path) -> None:
        self._model = TextEmbedding(model_name=model_name, cache_dir=str(cache_dir))

    def embed_documents(self, texts: list[str]) -> list[Sequence[float]]:
        return [vector.tolist() for vector in self._model.embed(texts)]

    def embed_query(self, text: str) -> Sequence[float]:
        return next(iter(self._model.query_embed(text))).tolist()


@lru_cache
def get_embedder() -> FastEmbedEmbedder:
    """Load the model once per process; loading takes seconds, embedding takes milliseconds."""
    s = get_settings()
    return FastEmbedEmbedder(s.embedding_model, Path(s.models_cache_dir))
