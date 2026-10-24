"""Find the SRS text relevant to a question and format it for an LLM prompt, with citations."""

from testgen.ingestion.vector_store import ChunkStore
from testgen.schemas import RetrievedChunk

# bge-small rates even unrelated text around 0.5 and real matches above ~0.6 (measured on the
# sample SRS). Phase 7's retrieval evals will tune this with data.
DEFAULT_MIN_SCORE = 0.6


def retrieve(
    store: ChunkStore,
    query: str,
    document: str | None = None,
    k: int = 5,
    min_score: float = DEFAULT_MIN_SCORE,
) -> list[RetrievedChunk]:
    """Top-k chunks for the query, dropping weak matches that would only add noise."""
    return [r for r in store.search(query, k=k, document=document) if r.score >= min_score]


def format_context(results: list[RetrievedChunk]) -> str:
    """Number each chunk and say where it came from, so the LLM can cite its sources."""
    parts = []
    for number, result in enumerate(results, start=1):
        chunk = result.chunk
        page = f"page {chunk.page}" if chunk.page else None
        location = ", ".join(p for p in (chunk.document, page, chunk.section) if p)
        parts.append(f"[{number}] ({location})\n{chunk.text}")
    return "\n\n".join(parts)
