"""Shared test fixtures. pytest loads this file automatically."""

import math
import re
import zlib
from pathlib import Path

import pytest

from testgen.ingestion.vector_store import ChunkStore

DIMENSIONS = 256


class FakeEmbedder:
    """Bag-of-words vectors: texts sharing words score as similar. Fast, offline, deterministic."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        vector = [0.0] * DIMENSIONS
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            # crc32, not hash(): Python's hash() of a string changes between runs.
            vector[zlib.crc32(word.encode()) % DIMENSIONS] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def store(tmp_path: Path, fake_embedder: FakeEmbedder) -> ChunkStore:
    return ChunkStore(fake_embedder, tmp_path / "chroma")
