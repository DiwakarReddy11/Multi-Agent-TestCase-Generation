"""Split a parsed SRS into chunks small enough for embedding and LLM context."""

import hashlib

from langchain_text_splitters import RecursiveCharacterTextSplitter

from testgen.schemas import Chunk, ParsedDocument

# SRS requirements are usually one per line, so split on lines before sentences or words.
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def _chunk_id(document: str, index: int, text: str) -> str:
    """Same input, same ID: re-ingesting a document updates its chunks instead of duplicating."""
    return hashlib.sha256(f"{document}|{index}|{text}".encode()).hexdigest()[:16]


def chunk_document(
    doc: ParsedDocument, chunk_size: int = 800, chunk_overlap: int = 100
) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=SEPARATORS
    )
    chunks: list[Chunk] = []
    # Split each block on its own, so a chunk never mixes two sections or two pages.
    for block in doc.blocks:
        for piece in splitter.split_text(block.text):
            index = len(chunks)
            chunks.append(
                Chunk(
                    id=_chunk_id(doc.name, index, piece),
                    document=doc.name,
                    index=index,
                    text=piece,
                    page=block.page,
                    section=block.section,
                )
            )
    return chunks
