from pathlib import Path

import pytest

from testgen.ingestion.chunking import chunk_document
from testgen.ingestion.embeddings import Embedder, get_embedder
from testgen.ingestion.vector_store import ChunkStore
from testgen.schemas import Chunk, ParsedDocument, TextBlock

LIBRARY_SRS = ParsedDocument(
    name="library.pdf",
    blocks=[
        TextBlock(
            text="The system shall lock an account after 5 failed login attempts.",
            page=2,
            section="2.1 Account Management",
        ),
        TextBlock(
            text="A member shall be able to borrow at most 5 books at the same time.",
            page=3,
            section="2.3 Borrowing",
        ),
        TextBlock(text="Search results shall load within 2 seconds.", section="3.1 Performance"),
    ],
)


def library_chunks() -> list[Chunk]:
    return chunk_document(LIBRARY_SRS)


def test_upsert_twice_does_not_duplicate(store: ChunkStore) -> None:
    store.upsert(library_chunks())
    store.upsert(library_chunks())
    assert store.count() == 3


def test_search_ranks_the_matching_chunk_first(store: ChunkStore) -> None:
    store.upsert(library_chunks())
    [best, *_] = store.search("how many books can a member borrow", k=3)
    assert best.chunk.section == "2.3 Borrowing"
    assert best.score > 0


def test_search_returns_full_chunk_with_metadata(store: ChunkStore) -> None:
    chunks = library_chunks()
    store.upsert(chunks)
    results = store.search("search results load seconds", k=1)
    assert results[0].chunk == chunks[2]  # page=None survives the round trip


def test_search_can_be_limited_to_one_document(store: ChunkStore) -> None:
    store.upsert(library_chunks())
    other = ParsedDocument(name="bank.pdf", blocks=[TextBlock(text="Lock account after 3 tries.")])
    store.upsert(chunk_document(other))

    results = store.search("lock account", k=5, document="bank.pdf")
    assert {r.chunk.document for r in results} == {"bank.pdf"}


def test_delete_document_removes_only_its_chunks(store: ChunkStore) -> None:
    store.upsert(library_chunks())
    store.upsert(chunk_document(ParsedDocument(name="bank.pdf", blocks=[TextBlock(text="x y")])))
    store.delete_document("library.pdf")
    assert store.count() == 1


def test_empty_store_returns_no_results(store: ChunkStore) -> None:
    assert store.search("anything") == []


def test_data_persists_on_disk(tmp_path: Path, fake_embedder: Embedder) -> None:
    ChunkStore(fake_embedder, tmp_path / "db").upsert(library_chunks())
    reopened = ChunkStore(fake_embedder, tmp_path / "db")
    assert reopened.count() == 3


@pytest.mark.integration
def test_real_model_matches_by_meaning_not_keywords(tmp_path: Path) -> None:
    store = ChunkStore(get_embedder(), tmp_path / "chroma")
    store.upsert(library_chunks())
    # Shares no meaningful words with "lock an account after 5 failed login attempts".
    [best, *_] = store.search("what happens when someone keeps typing the wrong password?")
    assert best.chunk.section == "2.1 Account Management"
