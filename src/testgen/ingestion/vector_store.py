"""Persistent store of SRS chunks and their embeddings, backed by a local Chroma database."""

from functools import lru_cache
from pathlib import Path

import chromadb
from chromadb.api.types import Metadata
from chromadb.config import Settings as ChromaSettings

from testgen.config import get_settings
from testgen.ingestion.embeddings import Embedder, get_embedder
from testgen.schemas import Chunk, RetrievedChunk

DEFAULT_COLLECTION = "srs_chunks"


def _to_metadata(chunk: Chunk) -> Metadata:
    # Chroma metadata values can't be None, so leave out fields that are missing.
    meta: dict[str, str | int] = {"document": chunk.document, "index": chunk.index}
    if chunk.page is not None:
        meta["page"] = chunk.page
    if chunk.section is not None:
        meta["section"] = chunk.section
    return meta


def _to_chunk(chunk_id: str, text: str, meta: Metadata) -> Chunk:
    return Chunk.model_validate({"id": chunk_id, "text": text, **meta})


class ChunkStore:
    def __init__(
        self, embedder: Embedder, path: Path, collection: str = DEFAULT_COLLECTION
    ) -> None:
        self._embedder = embedder
        client = chromadb.PersistentClient(
            path=str(path), settings=ChromaSettings(anonymized_telemetry=False)
        )
        # Cosine distance suits normalised sentence embeddings such as bge.
        self._collection = client.get_or_create_collection(
            collection, metadata={"hnsw:space": "cosine"}
        )

    def count(self) -> int:
        return self._collection.count()

    def upsert(self, chunks: list[Chunk]) -> None:
        """Insert new chunks and overwrite existing ones with the same ID."""
        if not chunks:
            return
        self._collection.upsert(
            ids=[c.id for c in chunks],
            embeddings=self._embedder.embed_documents([c.text_for_embedding for c in chunks]),
            documents=[c.text for c in chunks],
            metadatas=[_to_metadata(c) for c in chunks],
        )

    def delete_document(self, document: str) -> None:
        self._collection.delete(where={"document": document})

    def search(self, query: str, k: int = 5, document: str | None = None) -> list[RetrievedChunk]:
        """Return the k chunks most similar in meaning to the query, best first."""
        if self.count() == 0:
            return []
        result = self._collection.query(
            query_embeddings=[self._embedder.embed_query(query)],
            n_results=min(k, self.count()),
            where={"document": document} if document else None,
        )
        ids = result["ids"][0]
        texts = (result["documents"] or [[]])[0]
        metas = (result["metadatas"] or [[]])[0]
        distances = (result["distances"] or [[]])[0]
        return [
            RetrievedChunk(chunk=_to_chunk(i, t, m), score=1 - d)
            for i, t, m, d in zip(ids, texts, metas, distances, strict=True)
        ]


@lru_cache
def get_chunk_store() -> ChunkStore:
    """The app's store: the local embedding model plus the Chroma folder from settings."""
    return ChunkStore(get_embedder(), Path(get_settings().chroma_path))
