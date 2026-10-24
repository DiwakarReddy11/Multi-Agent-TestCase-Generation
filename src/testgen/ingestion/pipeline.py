"""Ingestion pipeline: SRS file -> text blocks -> chunks -> embeddings in the vector store."""

import logging
import time
from pathlib import Path

from pydantic import BaseModel

from testgen.ingestion.chunking import chunk_document
from testgen.ingestion.parsers import parse_document
from testgen.ingestion.vector_store import ChunkStore

logger = logging.getLogger(__name__)


class IngestReport(BaseModel):
    document: str
    blocks: int
    chunks: int
    seconds: float


def ingest_file(
    path: Path, store: ChunkStore, chunk_size: int = 800, chunk_overlap: int = 100
) -> IngestReport:
    start = time.perf_counter()
    doc = parse_document(path)
    chunks = chunk_document(doc, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    # Replace rather than merge: an edited SRS gets new chunk IDs, so old chunks must go.
    store.delete_document(doc.name)
    store.upsert(chunks)
    report = IngestReport(
        document=doc.name,
        blocks=len(doc.blocks),
        chunks=len(chunks),
        seconds=time.perf_counter() - start,
    )
    logger.info(
        "ingested %s: %d blocks, %d chunks in %.1fs",
        report.document,
        report.blocks,
        report.chunks,
        report.seconds,
    )
    return report
